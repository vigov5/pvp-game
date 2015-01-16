import json
import random
from tornado import gen
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, asynchronous
from app import app, db
from app.models import User, Game, Deck

class GameObject(RequestHandler):

    def __init__(self):
        self.q_num = 0
        pass

    def from_game(self, game):
        self.gid = game.id
        self.host_id = game.host_id
        self.guest_id = game.guest_id
        self.host_point = game.host_point
        self.guest_point = game.guest_point
        self.status = game.status
        self.reversed = game.reversed
        self.deck_id = game.deck_id
        self.questions = self.create_questions(game.deck)
        return self

    def __repr__(self):
        pass

    def __str__(self):
        return 'game %d' % self.gid

    def to_json(self):
        return json.dumps({
            'id': self.gid,
            'host_id': self.host_id,
            'guest_id': self.guest_id,
            'host_point': self.host_point,
            'guest_point': self.guest_point,
            'status': self.status,
            'reversed': self.reversed,
            'deck_id': self.deck_id,
            'questions': self.questions,
            'q_num': self.q_num,
        })

    def from_json_string(self, data):
        values = json.loads(data)
        self.gid = values['id']
        self.host_id = values['host_id']
        self.guest_id = values['guest_id']
        self.host_point = values['host_point']
        self.guest_point = values['guest_point']
        self.status = values['status']
        self.reversed = values['reversed']
        self.deck_id = values['deck_id']
        self.questions = values['questions']
        return self

    @asynchronous
    @gen.engine
    def send_question(self, sec=0):
        if sec:
            yield gen.Task(IOLoop.instance().add_timeout, time.time() + sec)
        for socket in [self.host_id.socket, self.guest_id.socket]:
            socket.write_message(json.dumps({
                'msg': 'question',
                'gid': self.model.id,
                'q': self.questions[self.q_num]['q'],
                'a': self.questions[self.q_num]['a'],
                'q_num': self.q_num
            }))

    def create_questions(self, deck, reversed=False):
        questions = []
        print deck
        facts = random.sample(deck.facts, min(30, len(deck.facts)))
        random.shuffle(facts)
        for fact in facts:
            tmp = list(facts)
            tmp.remove(fact)
            a = []
            for decoy in random.sample(tmp, 3):
                a.append(decoy.front) if reversed else a.append(decoy.back)
            a.append(fact.front) if reversed else a.append(fact.back)
            random.shuffle(a)
            questions.append({
                'q': fact.back if reversed else fact.front,
                'a': a,
                'i': a.index(fact.front if reversed else fact.back)
            })
        return questions

    def send_unknown_error(self):
        for socket in [self.host_id.socket, self.guest_id.socket]:
            socket.write_message(json.dumps({
                'msg': 'unknown_error',
                'gid': self.model.id,
            }))

    def send_update(self, correct, target):
        target.socket.write_message(json.dumps({
            'msg': 'result',
            'correct': 'true' if correct else 'false',
            'gid': self.model.id,
            'hp': self.host_id.point,
            'gp': self.guest_id.point,
            'aid': self.questions[self.q_num]['i'] + 1
        }))
        self.get_op(target).socket.write_message(json.dumps({
            'msg': 'update',
            'gid': self.model.id,
            'hp': self.host_id.point,
            'gp': self.guest_id.point,
        }))

        for client in clients:
            client.write_message(json.dumps({
                'msg': 'status_scored',
                'gid': self.model.id,
                'hp': self.host_id.point,
                'gp': self.guest_id.point
            }))

    def send_end_game(self):
        for socket in [self.host_id.socket, self.guest_id.socket]:
            socket.write_message(json.dumps({
                'msg': 'end',
                'gid': self.model.id,
                'hp': self.host_id.point,
                'gp': self.guest_id.point,
            }))

    def keep_undetached(self):
        #print self
        models = [player.model for player in [self.host_id, self.guest_id] if player]
        if self.model:
            models.append(self.model)
        for model in models:
            if inspect(model).detached:
                try:
                    db.session.add(model)
                except Exception, e:
                    print str(e)