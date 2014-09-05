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



clients = []
games = {}

class GameObject(object):
    host = None
    guest = None
    state = ''
    q_num = 0
    questions = []

    def get_op(self, player):
        return self.host if player == self.guest else self.guest

    def __init__(self, model, host):
        self.model = model
        self.host = host

    def __repr__(self):
        return '<Game %r %r %r>' % (self.model, self.host, self.guest)

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
        facts = Fact.query.filter_by(deck_id=deck_id).all()
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

    def cheated(self):
        if self.role == 'host' and self.guest_socket:
            self.guest_socket.write_message(json.dumps({
                'msg': 'cheated',
                'gid': self.gif,
            }))
        elif self.role == 'guest' and self.host_socket:
            self.host_socket.write_message(json.dumps({
                'msg': 'cheated',
                'gid': self.gif,
            }))

    def send_update(self, correct, target):
        target.socket.write_message(json.dumps({
            'msg': 'result',
            'correct': 'true' if correct else 'false',
            'gid': self.model.id,
            'hp': self.host.point,
            'gp': self.guest.point,
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
            game = Game.query.get(int(data['gid']))
            if not game or game.status != 'created':
                return
            if games.has_key(game.id):
                return
            host = User.query.get(int(data['clid']))
            new_game = GameObject(game, PlayerObject(host, self))
            new_game.state = 'created'
            games[new_game.model.id] = new_game
            for client in clients:
                if client is not self:
                    client.write_message(json.dumps({
                        'msg': 'new_game',
                        'gid': new_game.model.id,
                        'name': new_game.host.model.name,
                        'clid': new_game.host.model.id
                    }))
        if msg_type == 'joined':
            gid = int(data['gid'])
            if not games.has_key(gid):
                return
            game = games[gid]
            guest_id = int(data['clid'])
            game.model = Game.query.get(gid)
            if game.model.guest_id != guest_id:
                return
            guest = User.query.get(int(data['clid']))
            game.guest = PlayerObject(guest, self)
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
                game.cheated()
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
