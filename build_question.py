#!venv/bin/python
# -*- coding: utf-8 -*-

import tornado
import tornado.websocket
import tornado.wsgi
import logging
import time
import json
import random
from app import app, db
from app.models import User, Game, Fact, Deck, ROLE_USER, ROLE_ADMIN, get_object_or_404

"""
d = Deck('hiragana', 'test')
db.session.add(d)
db.session.commit()
a = Fact('あ', 'a', deck=d)
db.session.add(a)
db.session.commit()
a = Fact('い', 'i', deck=d)
db.session.add(a)
db.session.commit()
a = Fact('う', 'u', deck=d)
db.session.add(a)
db.session.commit()
a = Fact('え', 'e', deck=d)
db.session.add(a)
db.session.commit()
a = Fact('お', 'o', deck=d)
db.session.add(a)
db.session.commit()
"""
questions = []
facts = Fact.query.filter_by(deck_id=1).all()
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
print questions

