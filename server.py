#!venv/bin/python

import tornado
import tornado.websocket
import tornado.wsgi
import logging
import time
import json
from app import app
  
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
            self.name = data['name']
            self.host_id = int(data['clid'])
            self.guest_id = 0
            self.gid = int(data['gid'])
            self.role = 'host'
            self.state = 'created'
            self.host_point = 0
            self.guest_point = 0
            print "[INFO] Player %s created game %s" % (self.name, self.gid)
        if msg_type == 'joined':
            for client in clients:
                print client
                if client.gid == int(data['gid']):
                    client.guest_id = int(data['clid'])
                    client.state = 'ready'
                    print "[INFO] Player %s ready game %s" % (data['name'], client.gid)
                    break

     
    def on_close(self):
        print 'on close'
        print 'before', clients
        clients.remove(self)
        print 'after', clients
 
logging.getLogger().setLevel(logging.DEBUG)
tornado_app = tornado.web.Application([
        (r'/websocket', GameWebSocket),
        (r'.*', tornado.web.FallbackHandler, {'fallback': tornado.wsgi.WSGIContainer(app)})
    ],
    debug=True,
)
 
tornado_app.listen(5000)
tornado.ioloop.IOLoop.instance().start()
