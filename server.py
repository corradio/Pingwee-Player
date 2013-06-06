#!/usr/bin/python

import library
import player
import os

import tornado.gen
import tornado.ioloop
import tornado.web
import tornado.websocket

from threading import Thread


class Server(tornado.web.Application):

  clients = []
  player = player.Player()
  library = library.Library()

  def __init__(self):
    handlers =[
        (r"/", self.MainHandler),
        (r"/websocket", self.SocketHandler),
      ]
    settings = dict(
      static_path=os.path.join(os.path.dirname(__file__), "static"),
    )
    tornado.web.Application.__init__(self, handlers, **settings)

  def hdl_enqueue(self, socket, data):
    self.player.enqueue(data['track'])

  def hdl_list_queue(self, socket, data):
    self.raise_client_event('queue_changed', self.player.get_queue())

  def hdl_list_tags(self, socket, data):
    map_tag_tracks = self.library.map_tag_tracks
    obj = {
      'Tags': sorted(map_tag_tracks.keys())
    }
    self.raise_client_event('list_tags', obj)

  def hdl_list_tracks(self, socket, data):
    tag = data['tag']
    map_tag_tracks = self.library.map_tag_tracks
    map_track_info = self.library.map_track_info
    tracks = map_tag_tracks[tag]
    obj = {
      'Tag': tag,
      'Tracks': map_tag_tracks[tag],
      'TrackInfos': [map_track_info[track] for track in tracks]
    }
    self.raise_client_event('list_tracks', obj)

  def hdl_next(self, socket, data):
    self.player.next()

  def hdl_play(self, socket, data):
    self.player.play(data['track'])

  def hdl_scan_library(self, socket, data):
    self.raise_client_event('scan_library_started')
    thread_scan_library = Thread(target=self.scan_library, args=([socket]))
    thread_scan_library.setDaemon(True)
    thread_scan_library.start()

  def hdl_stop(self, socket, data):
    self.player.stop()

  def init(self):
    self.player.init(self)
    self.library.init()

  def raise_client_event(self, message, data=''):
    obj = {
      'message': message,
      'data': data,
    }
    print '[WS] -> Sending raw message: %s' % str(obj)
    for client in self.clients:
      client.write_message(obj)

  def run(self):
    self.listen(8088)
    try:
      tornado.ioloop.IOLoop.instance().start()
    finally:
      self.player.quit()

  def scan_library(self, client):
    self.library.scan_library()
    self.player.update_library()
    self.raise_client_event('scan_library_finished')

  class MainHandler(tornado.web.RequestHandler):
    def get(self):
      self.render("static/musiclibrary.html")

  class SocketHandler(tornado.websocket.WebSocketHandler):

    def __init__(self, application, request):
      tornado.websocket.WebSocketHandler.__init__(self, application, request)
      self.MESSAGE_HANDLERS = {
        'enqueue': self.application.hdl_enqueue,
        'list_queue': self.application.hdl_list_queue,
        'list_tags': self.application.hdl_list_tags,
        'list_tracks': self.application.hdl_list_tracks,
        'next': self.application.hdl_next,
        'play': self.application.hdl_play,
        'scan_library': self.application.hdl_scan_library,
        'stop': self.application.hdl_stop,
      }

    def open(self):
      print "[WS] WebSocket opened"
      self.application.clients += [self]

    @tornado.web.asynchronous
    @tornado.gen.engine
    def on_message(self, message):
      print '[WS] <- Received raw message: %s' % message
      obj = tornado.escape.json_decode(message)
      message = obj['message']
      data = obj['data']
      if not data and data != '':
        data = tornado.escape.json_decode(data)

      if message in self.MESSAGE_HANDLERS.keys():
        self.MESSAGE_HANDLERS[message](self, data)
      else:
        print "[WS] Unknown message received: %s" % message

    def on_close(self):
      print "[WS] WebSocket closed"
      self.application.clients.remove(self)


def main():
  server = Server()
  server.init()
  server.run()

if __name__ == "__main__":
    main()