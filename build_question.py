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


a = {'あ':'a',
'い':'i',
'う':'u',
'え':'e',
'お':'o',
'か':'ka',
'き':'ki',
'く':'ku',
'け':'ke',
'こ':'ko',
'さ':'sa',
'し':'shi',
'す':'su',
'せ':'se',
'そ':'so',
'た':'ta',
'ち':'chi',
'つ':'tsu',
'て':'te',
'と':'to',
'な':'na',
'に':'ni',
'ぬ':'nu',
'ね':'ne',
'の':'no',
'は':'ha',
'ひ':'hi',
'ふ':'hu',
'へ':'he',
'ほ':'ho',
'ま':'ma',
'み':'mi',
'む':'mu',
'め':'me',
'も':'mo',
'や':'ya',
'ゆ':'yu',
'よ':'yo',
'ら':'ra',
'り':'ri',
'る':'ru',
'れ':'re',
'ろ':'ro',
'わ':'wa',
'を':'wo',
'ん':'n'}

d = Deck.query.get(1)
for k,v in a.items():
	z = Fact(k, v, deck=d)
	db.session.add(z)
	db.session.commit()
