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
        print game
        self.gid = game.id
        self.host_id = game.host_id
        self.guest_id = game.guest_id
        self.host_point = game.host_point
        self.guest_point = game.guest_point
        self.host_avatar = game.host_player.getAvatar(24)
        self.guest_avatar = game.guest_player.getAvatar(24) if game.guest_player else None
        self.host_name = game.host_player.name
        self.guest_name = game.guest_player.name if game.guest_player else None
        self.status = game.status
        self.reversed = game.reversed
        self.host_answered = False
        self.guest_answered = False
        self.deck_id = game.deck_id
        self.deck_name = game.deck.name
        self.questions = self.create_questions(game.deck, game.reversed)
        return self

    def __repr__(self):
        return 'game %d' % self.gid

    def __str__(self):
        return 'game %d' % self.gid

    def to_json(self):
        return json.dumps({
            'id': self.gid,
            'host_id': self.host_id,
            'guest_id': self.guest_id,
            'host_point': self.host_point,
            'guest_point': self.guest_point,
            'host_avatar': self.host_avatar,
            'guest_avatar': self.guest_avatar,
            'host_name': self.host_name,
            'guest_name': self.guest_name,
            'host_answered': self.host_answered,
            'guest_answered': self.guest_answered,
            'status': self.status,
            'reversed': self.reversed,
            'deck_id': self.deck_id,
            'deck_name': self.deck_name,
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
        self.host_avatar = values['host_avatar']
        self.guest_avatar = values['guest_avatar']
        self.host_name = values['host_name']
        self.guest_name = values['guest_name']
        self.host_answered = values['host_answered']
        self.guest_answered = values['guest_answered']
        self.status = values['status']
        self.reversed = values['reversed']
        self.deck_id = values['deck_id']
        self.deck_name = values['deck_name']
        self.questions = values['questions']
        self.q_num = values['q_num']
        return self

    def create_questions(self, deck, reversed=False):
        questions = []
        print deck
        facts = random.sample(deck.facts, min(10, len(deck.facts)))
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
