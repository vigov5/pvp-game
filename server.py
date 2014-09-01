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
class GameWebSocket(tornado.websocket.WebSocketHandler):
    name = ''
    host_id = None
    guest_id = None
    gid = None
    role = ''
    state = ''
    host_point = 0
    guest_point = 0
    host_socket = None
    guest_socket = None
    q_num = 0
    questions = []
    
    def open(self):
        clients.append(self)
        """
        self.nick = "client%s" % (int(time.time()))
        print self
        for client in GameWebSocket.clients:
            if client is not self:
                client.write_message(json.dumps({
                    'msg': 'online',
                    'client': self.nick
                }))
        self.write_message(json.dumps({
            'msg': 'connected',
            'client': self.nick
        }))
        self.write_message(json.dumps({
            'msg': 'list_clients',
            'clients': [cl.nick for cl in GameWebSocket.clients if cl.nick is not self.nick]
        }))
        """
        pass

    def __repr__(self):
        return '<Socket %s %s %s %s %s>' % (self.name, self.gid, self.host_id, self.guest_id, self.state)

    def on_message(self, message):
        print "[INFO] Player %s got message %s" % (self.name, message)
        #print GameWebSocket.clients
        data = json.loads(message)
        msg_type = data['msg'];
        if msg_type == 'created':
            game = Game.query.get(int(data['gid']))
            if not game or game.status != 'created':
                return
            self.name = data['name']
            self.host_id = int(data['clid'])
            self.gid = int(data['gid'])
            self.role = 'host'
            self.state = 'created'
            self.host_point = 0
            self.guest_point = 0
            self.host_socket = self
            for client in clients:
                if client is not self:
                    print client
                    client.write_message(json.dumps({
                        'msg': 'new_game',
                        'gid': self.gid,
                        'name': self.name,
                        'clid': self.host_id
                    }))
        if msg_type == 'joined':
            gid = int(data['gid'])
            guest_id = int(data['clid'])
            game = Game.query.get(gid)
            if not game or game.status != 'joined' or guest_id != game.guest_id:
                return
            self.gid = gid
            self.role = 'guest'
            self.name = data['name']
            for client in clients:
                print client
                if client.gid == gid and client.role == 'host':
                    # TODO check client valid
                    client.guest_id = guest_id
                    client.state = 'joined'
                    client.guest_socket = self
                    self.host_socket = client
                    self.guest_socket = self
                    print "[INFO] Player %s ready game %s" % (data['name'], client.gid)
                    print data['clid']
                    client.write_message(json.dumps({
                        'msg': 'ready',
                        'gid': client.gid,
                        'name': data['name']
                    }))
                    break
        if msg_type == 'start':
            gid = int(data['gid'])
            for client in clients:
                if client.gid == gid and client.role == 'host':
                    game = Game.query.get(gid)
                    if not game or game.status != 'joined':
                        break
                    game.status = 'started'
                    db.session.add(game)
                    db.session.commit()
                    print "[INFO] game %d started " % (client.gid)
                    client.questions = client.create_questions()
                    print client
                    client.q_num = 0
                    client.send_question(gid)
                    break
        if msg_type == 'answer':
            gid = int(data['gid'])
            if self.gid != gid:
                self.cheated()
            if self.role == 'host' and self.host_id == int(data['clid']) and \
                self.host_socket.q_num == int(data['q_num']) and self.gid == int(data['gid']):
                if self.host_socket.questions[self.host_socket.q_num] == int(data['aid']):
                    self.host_socket.host_point += 10
                    self.send_correct(self.host_point)
            elif self.role == 'guest' and self.guest_id == int(data['clid']) and \
                self.host_socket.q_num == int(data['q_num']) and self.gid == int(data['gid']):
                if self.host_socket.questions[self.host_socket.q_num] == int(data['aid']):
                    self.host_socket.guest_point += 10
                    self.send_correct(self.guest_point)
            else:
                self.cheated()
                

    def send_correct(self, point):
        self.write_message(json.dumps({
            'msg': 'correct',
            'gid': self.gid,
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
            questions.append({
                'q': fact.front,
                'a': a,
                'i': a.index(fact.back)
            })
        return questions


    def send_question(self, gid):
        print "[INFO] User %s close connection " % (self.gid)
        print self.questions
        self.host_socket.write_message(json.dumps({
            'msg': 'question',
            'gid': self.gid,
            'q': self.questions[self.q_num]['q'],
            'a': self.questions[self.q_num]['a'],
            'q_num': self.q_num
        }))
        self.guest_socket.write_message(json.dumps({
            'msg': 'question',
            'gid': self.gid,
            'q': self.questions[self.q_num]['q'],
            'a': self.questions[self.q_num]['a'],
            'q_num': self.q_num
        }))


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
     
    def on_close(self):
        clients.remove(self)
        if self.gid == None:
            return
        game = Game.query.get(self.gid)
        if not game or game.status == 'canceled':
            return
        game.status = 'canceled'
        db.session.add(game)
        db.session.commit()
        if self.role == 'host' and self.guest_socket:
            self.guest_socket.write_message(json.dumps({
                'msg': 'quited',
                'gid': self.gid,
            }))
        elif self.role == 'guest' and self.host_socket:
            self.host_socket.write_message(json.dumps({
                'msg': 'quited',
                'gid': self.gid,
            }))
        print 'done'
 
logging.getLogger().setLevel(logging.DEBUG)
tornado_app = tornado.web.Application([
        (r'/websocket', GameWebSocket),
        (r'.*', tornado.web.FallbackHandler, {'fallback': tornado.wsgi.WSGIContainer(app)})
    ],
    debug=True,
)
 
tornado_app.listen(5000)
tornado.ioloop.IOLoop.instance().start()
