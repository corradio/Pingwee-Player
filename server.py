#!/usr/bin/python

import library
import player
import os
import urllib2

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
        (r"/list_tags", self.list_tags),
        (r"/list_tracks", self.list_tracks),
        (r"/enqueue", self.enqueue),
        (r"/play", self.play),
        (r"/websocket", self.sock),
      ]
    settings = dict(
      static_path=os.path.join(os.path.dirname(__file__), "static"),
    )
    tornado.web.Application.__init__(self, handlers, **settings)

  def init(self):
    self.player.init()
    self.library.init()

  def run(self):
    self.listen(8080)
    try:
      tornado.ioloop.IOLoop.instance().start()
    finally:
      self.player.quit()

  def start_library_scan(self, client):
    # TODO: make async
    self.library.scan_library()
    client.write_message('Library scan finished!')


  class enqueue(tornado.web.RequestHandler):
    def get(self):
      track = HTMLDecode(self.get_argument('track'))
      player.enqueue(track)

  class list_queue(tornado.web.RequestHandler):
    def get(self):
      track = HTMLDecode(self.get_argument('track'))

      global QUEUE
      obj = {
        'Tracks': [map_track_info[track] for track in QUEUE],
        'TrackInfos': [map_track_info[track] for track in QUEUE]
      }

      self.write(tornado.escape.json_encode(obj))

  class list_tags(tornado.web.RequestHandler):
    def get(self):
      map_tag_tracks = self.application.library.map_tag_tracks
      obj = {'Tags':sorted(map_tag_tracks.keys())}
      self.write(tornado.escape.json_encode(obj))

  class list_tracks(tornado.web.RequestHandler):
    def get(self):
      map_tag_tracks = self.application.library.map_tag_tracks
      map_track_info = self.application.library.map_track_info
      tag = HTMLDecode(self.get_argument('tag'))
      tracks = map_tag_tracks[tag]
      obj = {
        'Tag': tag,
        'Tracks': map_tag_tracks[tag],
        'TrackInfos': [map_track_info[track] for track in tracks]
      }
      self.write(tornado.escape.json_encode(obj))

  class MainHandler(tornado.web.RequestHandler):
    def get(self):
      self.render("static/musiclibrary.html")

  class play(tornado.web.RequestHandler):
    def get(self):
      track = HTMLDecode(self.get_argument('track'))
      self.application.player.play(track)

  class sock(tornado.websocket.WebSocketHandler):
    def open(self):
      print "WebSocket opened"
      self.application.clients += [self]

    @tornado.web.asynchronous
    @tornado.gen.engine
    def on_message(self, message):
      if message == 'scan_library':
        self.write_message('Library scan started..')
        self.application.start_library_scan(self)

    def on_close(self):
      print "WebSocket closed"
      self.application.clients.remove(self)


def HTMLDecode(s):
  return urllib2.unquote(urllib2.quote(s.encode("utf8")))

def main():
  server = Server()
  server.init()
  server.run()

if __name__ == "__main__":
    main()