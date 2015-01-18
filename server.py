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
hosts = {}
guests = {}

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

    @asynchronous
    @gen.engine
    def send_question(self, game, sockets, sec=0):
        print 'send questions'
        if sec:
            yield gen.Task(IOLoop.instance().add_timeout, time.time() + sec)
        for socket in sockets:
            socket.write_message(json.dumps({
                'msg': 'question',
                'gid': game.gid,
                'q': game.questions[game.q_num]['q'],
                'a': game.questions[game.q_num]['a'],
                'q_num': game.q_num
            }))

    def send_update(self, game, correct, my_socket, op_socket):
        my_socket.write_message(json.dumps({
            'msg': 'result',
            'correct': 'true' if correct else 'false',
            'gid': game.gid,
            'hp': game.host_point,
            'gp': game.guest_point,
            'aid': game.questions[game.q_num]['i'] + 1
        }))
        op_socket.write_message(json.dumps({
            'msg': 'update',
            'gid': game.gid,
            'hp': game.host_point,
            'gp': game.guest_point,
        }))

        for client in clients:
            client.write_message(json.dumps({
                'msg': 'status_scored',
                'gid': game.gid,
                'hp': game.host_point,
                'gp': game.guest_point
            }))

    def send_unknown_error(self, game, sockets):
        for socket in sockets:
            socket.write_message(json.dumps({
                'msg': 'unknown_error',
                'gid': game.gid,
            }))

    def send_end_game(self, game, sockets):
        for socket in sockets:
            socket.write_message(json.dumps({
                'msg': 'end',
                'gid': game.gid,
                'hp': game.host_point,
                'gp': game.guest_point,
            }))

    def check_origin(self, origin):
        return True

    def on_message(self, message):
        print "INFO Got message %s" % (message)
        data = json.loads(message)
        msg_type = data['msg'];

        if msg_type == 'created':
            game = redis_client.get("g%d" % int(data['gid']))
            if not game:
                return
            new_game = GameObject().from_json_string(game)
            if not new_game or new_game.status != 'created':
                return
            hosts[new_game.gid] = self
            for client in clients:
                if client is not self:
                    client.write_message(json.dumps({
                        'msg': 'new_game',
                        'gid': new_game.gid,
                        'name': new_game.host_name,
                        'd': new_game.deck_name,
                        'avt': new_game.host_avatar,
                        'clid': new_game.host_id
                    }))

        if msg_type == 'joined':
            gid = int(data['gid'])
            cached = redis_client.get("g%d" % gid)
            if not cached:
                return
            game = GameObject().from_json_string(cached)
            guest_id_id = int(data['clid'])
            if game.guest_id != guest_id_id:
                return
            print "[INFO] Player %s ready game %s" % (game.guest_name, game.gid)
            guests[game.gid] = self
            hosts[game.gid].write_message(json.dumps({
                'msg': 'ready',
                'gid': game.gid,
                'name': game.guest_name
            }))
            for client in clients:
                if client is not self:
                    client.write_message(json.dumps({
                        'msg': 'status_joined',
                        'gid': game.gid,
                        'name': game.guest_name,
                        'avt': game.guest_avatar,
                        'clid': game.guest_id
                    }))
            redis_client.set("g%d" % gid, game.to_json())

        if msg_type == 'start':
            gid = int(data['gid'])
            cached = redis_client.get("g%d" % gid)
            if not cached:
                return
            game = GameObject().from_json_string(cached)
            if not game or self != hosts[game.gid] or game.status != 'joined':
                return
            game.status = 'started'
            print "INFO game %d started " % (game.gid)
            for client in clients:
                if client is not self:
                    client.write_message(json.dumps({
                        'msg': 'status_started',
                        'gid': game.gid,
                    }))
            game.q_num = 0
            self.send_question(game, [hosts[gid], guests[gid]])
            redis_client.set("g%d" % gid, game.to_json())

        if msg_type == 'answer':
            gid = int(data['gid'])
            cached = redis_client.get("g%d" % gid)
            if not cached:
                return
            game = GameObject().from_json_string(cached)
            if not game.status == 'started':
                return
            if game.gid != gid:
                self.send_unknown_error(game, [hosts[gid], guests[gid]])
            socket = hosts[gid] if self == hosts[gid] else guests
            print "INFO Checking questions %d" % game.q_num
            print "INFO Correct is %d" % game.questions[game.q_num]['i']
            if self == hosts[gid]:
                if game.host_id == int(data['clid']) and game.q_num == int(data['q_num']) and game.gid == gid:
                    if game.questions[game.q_num]['i'] + 1 == int(data['aid']) and not game.host_answered:
                        game.host_point += 10 + data['t']
                        self.send_update(game, True, hosts[gid], guests[gid])
                    else:
                        self.send_update(game, False, hosts[gid], guests[gid])
                    game.host_answered = True
            else:
                if game.guest_id == int(data['clid']) and game.q_num == int(data['q_num']) and game.gid == gid:
                    if game.questions[game.q_num]['i'] + 1 == int(data['aid']) and not game.guest_answered:
                        game.guest_point += 10 + data['t']
                        self.send_update(game, True, guests[gid], hosts[gid])
                    else:
                        self.send_update(game, False, guests[gid], hosts[gid])
                    game.guest_answered = True
            #print "INFO answered %r %r" % (game.host_id.answered, game.guest_id.answered)

            if all([game.host_answered, game.guest_answered]):
                game.host_answered = False
                game.guest_answered = False
                game.q_num += 1
                if game.q_num == len(game.questions):
                    print "INFO game %d ended " % (game.gid)
                    model = Game.query.get(gid)
                    model.status = 'ended'
                    model.host_point = game.host_point if game.host_id else 0
                    model.guest_point = game.guest_point if game.guest_id else 0
                    db.session.add(model)
                    db.session.commit()
                    self.send_end_game(game, [hosts[gid], guests[gid]])
                    for client in clients:
                        client.write_message(json.dumps({
                            'msg': 'status_ended',
                            'gid': game.gid,
                        }))
                    redis_client.delete("g%d" % gid)
                    del hosts[gid]
                    del guests[gid]
                else:
                    print 'send questions 1'
                    redis_client.set("g%d" % gid, game.to_json())
                    self.send_question(game, [hosts[gid], guests[gid]], sec=3)
            redis_client.set("g%d" % gid, game.to_json())

    def on_close(self):
        print "clients", clients
        print "hosts", hosts
        print "guests", guests
        print "INFO client %r leave" % (self)
        clients.remove(self)
        gid = None
        for target_id, socket in hosts.iteritems():
            if self == socket:
                gid = target_id
                break
        if not gid:
            for target_id, socket in guests.iteritems():
                if self == socket:
                    gid = target_id
                    break
        print "gid", gid
        if gid:
            print "INFO client %r quit game %d" % (self, gid)
            cached = redis_client.get("g%d" % gid)
            if not cached:
                return
            game = GameObject().from_json_string(cached)
            if not game or game.status == 'canceled':
                return
            if game.status == 'ended':
                redis_client.delete("g%d" % gid)
                del hosts[gid]
                del guests[gid]
                return
            model = Game.query.get(gid)
            model.status = 'canceled'
            model.host_point = game.host_point if game.host_id else 0
            model.guest_point = game.guest_point if game.guest_id else 0
            db.session.add(model)
            db.session.commit()
            sockets = [hosts[gid]]
            if guests.get(gid):
                sockets.append(guests[gid])
            for socket in sockets:
                try:
                    socket.write_message(json.dumps({
                        'msg': 'quited',
                        'gid': game.gid,
                    }))
                except:
                    pass
            for client in clients:
                if client is not self:
                    client.write_message(json.dumps({
                        'msg': 'status_canceled',
                        'gid': game.gid,
                    }))

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
