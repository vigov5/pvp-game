#!venv/bin/python

import tornado
import tornado.websocket
import tornado.wsgi
import logging
import time
import random
import json
import redis
from tornado import gen
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, asynchronous
from app import app, db
from app.models import User, Game, Deck
from sqlalchemy.inspection import inspect
from game_object import GameObject
from player_object import PlayerObject

clients = []
games = {}

redis_client = redis.Redis()

def object_state(obj):
    try:
        insp = inspect(obj)
        return "%r transient %r pending %r persistent %r detached %r" % (obj, insp.transient, insp.pending, insp.persistent, insp.detached)
    except Exception, e:
        return str(e)

class GameWebSocket(tornado.websocket.WebSocketHandler):

    def open(self):
        clients.append(self)
        print clients
        pass

    def check_origin(self, origin):
        return True

    def on_message(self, message):
        print "INFO Got message %s" % (message)
        data = json.loads(message)
        msg_type = data['msg'];

        if msg_type == 'created':
            game = redis_client.get("g%d" % int(data['gid']))
            print game
            if not game:
                return
            new_game = GameObject().from_json_string(game)
            print new_game
            print new_game.status
            if not new_game or new_game.status != 'created':
                return
            games[new_game.gid] = new_game
            for client in clients:
                if client is not self:
                    client.write_message(json.dumps({
                        'msg': 'new_game',
                        'gid': new_game.model.id,
                        'name': new_game.host_id.model.name,
                        'd': new_game.model.deck.name,
                        'avt': new_game.host_id.model.getAvatar(24),
                        'clid': new_game.host_id.model.id
                    }))
            print games

        if msg_type == 'joined':
            gid = int(data['gid'])
            if not games.has_key(gid):
                return
            game = games[gid]
            guest_id_id = int(data['clid'])
            game.model = db.session.query(Game).get(gid)
            if game.model.guest_id_id != guest_id_id:
                return
            guest_id_model = db.session.query(User).get(int(data['clid']))
            game.guest_id = PlayerObject(guest_id_model, self)
            # mysteriously host_id got detached, we need to add host_id model once again
            db.session.add(game.guest_id.model)
            db.session.add(game.host_id.model)
            # TODO check client valid
            #print "[INFO] Player %s ready game %s" % (game.guest_id.model.name, game.model.id)
            game.host_id.socket.write_message(json.dumps({
                'msg': 'ready',
                'gid': game.model.id,
                'name': game.guest_id.model.name
            }))
            for client in clients:
                if client is not self:
                    client.write_message(json.dumps({
                        'msg': 'status_joined',
                        'gid': game.model.id,
                        'name': game.guest_id.model.name,
                        'avt': game.guest_id.model.getAvatar(24),
                        'clid': game.guest_id.model.id
                    }))

        if msg_type == 'start':
            gid = int(data['gid'])
            game = games.get(gid)
            if not game or self != game.host_id.socket or game.model.status != 'joined':
                return
            game.keep_undetached()
            game.model.status = 'started'
            db.session.add(game.model)
            db.session.commit()
            #print "INFO game %d started " % (game.model.id)
            for client in clients:
                if client is not self:
                    client.write_message(json.dumps({
                        'msg': 'status_started',
                        'gid': game.model.id,
                    }))
            game.questions = game.create_questions(deck_id=game.model.deck.id,reversed=game.model.reversed)
            game.q_num = 0
            game.send_question()

        if msg_type == 'answer':
            gid = int(data['gid'])
            game = games.get(gid)
            game.keep_undetached()
            if not game or game.model.status != 'started':
                return
            if game.model.id != gid:
                game.send_unknown_error()
            for player in [game.host_id, game.guest_id]:
                #print "INFO Checking questions %d" % game.q_num
                #print "INFO Correct is %d" % game.questions[game.q_num]['i']
                if self == player.socket:
                    if player.model.id == int(data['clid']) and game.q_num == int(data['q_num']) \
                        and game.model.id == int(data['gid']):
                        if game.questions[game.q_num]['i'] + 1 == int(data['aid']) and not player.answered:
                            player.point += 10 + data['t']
                            game.send_update(True, player)
                        else:
                            game.send_update(False, player)
                        player.answered = True
                    break
            #print "INFO answered %r %r" % (game.host_id.answered, game.guest_id.answered)
            if all([game.host_id.answered, game.guest_id.answered]):
                game.host_id.answered = False
                game.guest_id.answered = False
                game.q_num += 1
                if game.q_num == len(game.questions):
                    #print "INFO game %d ended " % (game.model.id)
                    game.model.status = 'ended'
                    game.model.host_id_point = game.host_id.point
                    game.model.guest_id_point = game.guest_id.point
                    db.session.add(game.model)
                    db.session.commit()
                    game.send_end_game()
                    for client in clients:
                        client.write_message(json.dumps({
                            'msg': 'status_ended',
                            'gid': game.model.id,
                        }))
                else:
                    game.send_question(sec=3)

    def on_close(self):
        #print "INFO client %r leave" % (self)
        clients.remove(self)
        for gid, game in games.items():
            if self in [a.socket for a in [game.host_id, game.guest_id] if a]:
                #print "INFO client %r quit game" % (self)
                if not game or game.model.status == 'canceled':
                    return
                game.keep_undetached()
                if game.model.status == 'ended':
                    del games[gid]
                    return
                game.model.status = 'canceled'
                game.model.host_id_point = game.host_id.point if game.host_id else 0
                game.model.guest_id_point = game.guest_id.point if game.guest_id else 0
                db.session.add(game.model)
                db.session.commit()
                sockets = [a.socket for a in [game.host_id, game.guest_id] if a]
                for socket in sockets:
                    try:
                        socket.write_message(json.dumps({
                            'msg': 'quited',
                            'gid': game.model.id,
                        }))
                    except:
                        pass
                del games[gid]
                for client in clients:
                    if client is not self:
                        client.write_message(json.dumps({
                            'msg': 'status_canceled',
                            'gid': game.model.id,
                        }))
                break

logging.getLogger().setLevel(logging.DEBUG)
tornado_app = tornado.web.Application([
        (r'/websocket', GameWebSocket),
        (r'.*', tornado.web.FallbackHandler, {'fallback': tornado.wsgi.WSGIContainer(app)})
    ],
    debug=True,
)

if __name__ == '__main__':
    tornado_app.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
