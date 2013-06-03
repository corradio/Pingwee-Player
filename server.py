#!/usr/bin/python

import library
import player
import os

import tornado.gen
import tornado.ioloop
import tornado.web
import tornado.websocket


class Server(tornado.web.Application):

  clients = []
  player = player.Player()
  library = library.Library()

  def __init__(self):
    handlers =[
        (r"/", self.MainHandler),
        (r"/websocket", self.sock),
      ]
    settings = dict(
      static_path=os.path.join(os.path.dirname(__file__), "static"),
    )
    tornado.web.Application.__init__(self, handlers, **settings)

  def init(self):
    self.player.init(self)
    self.library.init()

  def list_queue(self):
    queue = player.get_queue()
    obj = {
      'Tracks': [map_track_info[track] for track in queue],
      'TrackInfos': [map_track_info[track] for track in queue]
    }
    return obj

  def list_tags(self):
    map_tag_tracks = self.library.map_tag_tracks
    obj = {
      'Tags': sorted(map_tag_tracks.keys())
    }
    return obj

  def list_tracks(self, tag):
    map_tag_tracks = self.library.map_tag_tracks
    map_track_info = self.library.map_track_info
    tracks = map_tag_tracks[tag]
    obj = {
      'Tag': tag,
      'Tracks': map_tag_tracks[tag],
      'TrackInfos': [map_track_info[track] for track in tracks]
    }
    return obj

  def raise_client_event(self, message, data):
    for client in self.clients:
      client.write_message(
        {
          'message': message,
          'data': data,
        }
      )

  def run(self):
    self.listen(8080)
    try:
      tornado.ioloop.IOLoop.instance().start()
    finally:
      self.player.quit()

  def start_scan_library(self, client):
    # TODO: make non-blocking
    self.library.scan_library()
    self.player.update_library()
    client.write_message('scan_library_finished')

  class MainHandler(tornado.web.RequestHandler):
    def get(self):
      self.render("static/musiclibrary.html")

  class sock(tornado.websocket.WebSocketHandler):
    def open(self):
      print "[WS] WebSocket opened"
      self.application.clients += [self]

    @tornado.web.asynchronous
    @tornado.gen.engine
    def on_message(self, message):
      print '[WS] Raw message: %s' % message
      obj = tornado.escape.json_decode(message)
      message = obj['message']
      data = obj['data']
      if not data and data != '':
        data = tornado.escape.json_decode(data)

      if message == 'enqueue':
        self.application.player.enqueue(data['track'])

      elif message == 'list_queue':
        self.application.raise_client_event('queue', self.application.list_queue())

      elif message == 'list_tags':
        self.application.raise_client_event('list_tags', self.application.list_tags())

      elif message == 'list_tracks':
        self.application.raise_client_event('list_tracks', self.application.list_tracks(data['tag']))

      elif message == 'play':
        self.application.player.play(data['track'])

      elif message == 'scan_library':
        self.application.raise_client_event('scan_library_started', '')
        self.application.start_scan_library(self)

    def on_close(self):
      print "[WS] WebSocket closed"
      self.application.clients.remove(self)


def main():
  server = Server()
  server.init()
  server.run()

if __name__ == "__main__":
    main()