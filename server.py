#!venv/bin/python

import tornado
import tornado.websocket
import tornado.wsgi
import logging
import time
import random
import json
from app import app, db
from app.models import User, Game, Fact, ROLE_USER, ROLE_ADMIN, get_object_or_404
from flask import url_for
from sqlalchemy.inspection import inspect

clients = []
games = {}

def object_state(obj):
    try:
        insp = inspect(obj)
        return "%r transient %r pending %r persistent %r detached %r" % (obj, insp.transient, insp.pending, insp.persistent, insp.detached)
    except Exception, e:
        return str(e)

class GameObject(object):
    host = None
    guest = None
    model = None
    q_num = 0
    questions = []

    def get_op(self, player):
        return self.host if player == self.guest else self.guest

    def __init__(self, model, host):
        self.model = model
        self.host = host

    def __repr__(self):
        for obj in db.session:
            print obj
        txt = ''
        txt += "<Game %r %r %r >\n" % (self.model, self.host, self.guest)
        try:
            txt += "Game " + object_state(self.model) + "\n"
            if self.host.model:
                txt += "Host " + object_state(self.host.model) + "\n"
            if self.guest and self.guest.model:
                txt += "Guest " + object_state(self.guest.model) + "\n"
            return txt
        except Exception, e:
            return str(e)

    def send_question(self):
        for socket in [self.host.socket, self.guest.socket]:
            socket.write_message(json.dumps({
                'msg': 'question',
                'gid': self.model.id,
                'q': self.questions[self.q_num]['q'],
                'a': self.questions[self.q_num]['a'],
                'q_num': self.q_num
            }))

    def create_questions(self, deck_id=1):
        questions = []
        facts = db.session.query(Fact).filter_by(deck_id=deck_id).all()
        random.shuffle(facts)
        for fact in facts:
            tmp = list(facts)
            tmp.remove(fact)
            a = []
            for decoy in random.sample(tmp, 3):
                a.append(decoy.back)
            a.append(fact.back)
            random.shuffle(a)
            questions.append({
                'q': fact.front,
                'a': a,
                'i': a.index(fact.back)
            })
        return questions

    def send_unknown_error(self):
        for socket in [self.host.socket, self.guest.socket]:
            socket.write_message(json.dumps({
                'msg': 'unknown_error',
                'gid': self.model.id,
            }))

    def send_update(self, correct, target):
        target.socket.write_message(json.dumps({
            'msg': 'result',
            'correct': 'true' if correct else 'false',
            'gid': self.model.id,
            'hp': self.host.point,
            'gp': self.guest.point,
            'aid': self.questions[self.q_num]['i'] + 1
        }))
        self.get_op(target).socket.write_message(json.dumps({
            'msg': 'update',
            'gid': self.model.id,
            'hp': self.host.point,
            'gp': self.guest.point,
        }))

    def send_end_game(self):
        for socket in [self.host.socket, self.guest.socket]:
            socket.write_message(json.dumps({
                'msg': 'end',
                'gid': self.model.id,
                'hp': self.host.point,
                'gp': self.guest.point,
            }))

class PlayerObject(object):

    socket = None
    model = None
    point = 0
    answered = False

    def __init__(self, model, socket):
        self.socket = socket
        self.model = model
        self.point = 0
        self.answered = False

class GameWebSocket(tornado.websocket.WebSocketHandler):

    def open(self):
        clients.append(self)
        pass


    def on_message(self, message):
        print "INFO Got message %s" % (message)
        data = json.loads(message)
        msg_type = data['msg'];

        if msg_type == 'created':
            game = db.session.query(Game).get(int(data['gid']))
            if not game or game.status != 'created':
                return
            if games.has_key(game.id):
                return
            host_model = db.session.query(User).get(int(data['clid']))
            new_game = GameObject(game, PlayerObject(host_model, self))
            games[new_game.model.id] = new_game
            db.session.add(new_game.model)
            for client in clients:
                if client is not self:
                    client.write_message(json.dumps({
                        'msg': 'new_game',
                        'gid': new_game.model.id,
                        'name': new_game.host.model.name,
                        'd': 'Hiragana',
                        'avt': new_game.host.model.getAvatar(24),
                        'clid': new_game.host.model.id
                    }))

        if msg_type == 'joined':
            gid = int(data['gid'])
            if not games.has_key(gid):
                return
            game = games[gid]
            guest_id = int(data['clid'])
            game.model = db.session.query(Game).get(gid)
            if game.model.guest_id != guest_id:
                return
            guest_model = db.session.query(User).get(int(data['clid']))
            game.guest = PlayerObject(guest_model, self)
            # mysteriously host got detached, we need to add host model once again
            db.session.add(game.guest.model)
            db.session.add(game.host.model)
            # TODO check client valid
            print "[INFO] Player %s ready game %s" % (game.guest.model.name, game.model.id)
            game.host.socket.write_message(json.dumps({
                'msg': 'ready',
                'gid': game.model.id,
                'name': game.guest.model.name
            }))

        if msg_type == 'start':
            gid = int(data['gid'])
            game = games.get(gid)
            if not game or self != game.host.socket or game.model.status != 'joined':
                return
            game.model.status = 'started'
            db.session.add(game.model)
            db.session.commit()
            print "INFO game %d started " % (game.model.id)
            game.questions = game.create_questions()
            game.q_num = 0
            game.send_question()

        if msg_type == 'answer':
            gid = int(data['gid'])
            game = games.get(gid)
            if not game or game.model.status != 'started':
                return
            if game.model.id != gid:
                game.send_unknown_error()
            for player in [game.host, game.guest]:
                print "INFO Checking questions %d" % game.q_num
                print "INFO Correct is %d" % game.questions[game.q_num]['i']
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
            print "INFO answered %r %r" % (game.host.answered, game.guest.answered)
            if all([game.host.answered, game.guest.answered]):
                game.host.answered = False
                game.guest.answered = False
                game.q_num += 1
                if game.q_num == len(game.questions):
                    game.model.status = 'ended'
                    game.host_point = game.host.point
                    game.guest_point = game.guest.point
                    db.session.add(game.model)
                    db.session.commit()
                    game.send_end_game()
                else:
                    time.sleep(3)
                    game.send_question()

    def on_close(self):
        print "INFO client %r leave" % (self)
        clients.remove(self)
        for gid, game in games.items():
            if self in [a.socket for a in [game.host, game.guest] if a]:
                print "INFO client %r quit game" % (self)
                if not game or game.model.status == 'canceled':
                    return
                game.model.status = 'canceled'
                game.model.host_point = game.host.point if game.host else 0
                game.model.guest_point = game.guest.point if game.guest else 0
                db.session.add(game.model)
                db.session.commit()
                sockets = [a.socket for a in [game.host, game.guest] if a]
                for socket in sockets:
                    try:
                        socket.write_message(json.dumps({
                            'msg': 'quited',
                            'gid': game.model.id,
                        }))
                    except:
                        pass
                del games[gid]
                break
 
logging.getLogger().setLevel(logging.DEBUG)
tornado_app = tornado.web.Application([
        (r'/websocket', GameWebSocket),
        (r'.*', tornado.web.FallbackHandler, {'fallback': tornado.wsgi.WSGIContainer(app)})
    ],
    debug=True,
)
 
tornado_app.listen(5000)
tornado.ioloop.IOLoop.instance().start()
