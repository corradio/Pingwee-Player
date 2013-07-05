#!/usr/bin/python

import coverart
import base64
import json
import library
import player
import os
import random

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
    handlers = [
      (r"/", self.MainHandler),
      (r"/websocket", self.SocketHandler),
    ]
    settings = dict(
      static_path=os.path.join(os.path.dirname(__file__), "static"),
    )
    tornado.web.Application.__init__(self, handlers, **settings)

  def hdl_delete(self, socket, data):
    if 'track' in data:
      track = data['track']
    elif 'QueueIndex' in data:
      track = self.player.get_queue()['Tracks'][data['QueueIndex']]
      self.player.remove_from_queue(data['QueueIndex'])
    self.library.delete(track)

  def hdl_enqueue(self, socket, data):
    self.player.enqueue(data['track'])

  def hdl_get_coverart(self, socket, data):
    if 'track' in data:
      track = data['track']
    elif 'QueueIndex' in data:
      track = self.player.get_queue()['Tracks'][data['QueueIndex']]

    cover = self.library.get_track_coverart(track)
    if not cover:
      print '[SERVER] Cover Art is not available in library: fetching from web.'
      query = '%s %s %s cover' % (
        self.library.map_track_info[track]['artist'],
        self.library.map_track_info[track]['album'],
        self.library.map_track_info[track]['title']
      )
      cover = coverart.getbase64image(query)
    else:
      cover = base64.b64encode(cover['data'])
    obj = {
      'data': cover,
      'Track': track,
    }
    self.raise_client_event('get_coverart', obj, socket)

  def hdl_list_queue(self, socket, data):
    self.raise_client_event('queue_changed', self.player.get_queue(), socket)

  def hdl_list_tags(self, socket, data):
    map_tag_tracks = self.library.map_tag_tracks
    obj = {
      'Tags': sorted(map_tag_tracks.keys())
    }
    self.raise_client_event('list_tags', obj, socket)

  def hdl_list_tracks(self, socket, data):
    tag = data['tag']
    map_tag_tracks = self.library.map_tag_tracks
    map_track_info = self.library.map_track_info
    tracks = map_tag_tracks[tag]
    trackinfos = [map_track_info[track] for track in tracks]
    obj = {
      'Tag': tag,
      'Tracks': tracks,
      'TrackInfos': trackinfos,
    }
    self.raise_client_event('list_tracks', obj, socket)

  def hdl_next(self, socket, data):
    self.player.next()

  def hdl_play(self, socket, data):
    if 'QueueIndex' in data:
      self.player.play(int(data['QueueIndex']))
    elif 'Track' in data:
      self.player.play(data['Track'])
    else:
      self.player.play()

  def hdl_play_pause_toogle(self, socket, data):
    self.player.playpausetoogle()

  def hdl_play_tag(self, socket, data):
    tracks = self.library.map_tag_tracks[data['tag']]
    shuffle = bool(data['shuffle']) if 'shuffle' in data else False
    if shuffle:
      random.shuffle(tracks)
    self.player.clear_queue()
    self.player.enqueue(tracks)
    self.player.play()

  def hdl_rename_tag(self, socket, data):
    self.library.rename_tag(data['old'], data['new'])

  def hdl_scan_library(self, socket, data):
    self.raise_client_event('scan_library_started')
    thread_scan_library = Thread(target=self.scan_library, args=())
    thread_scan_library.setDaemon(True)
    thread_scan_library.start()

  def hdl_stop(self, socket, data):
    self.player.stop()

  def hdl_remove_from_queue(self, socket, data):
    self.player.remove_from_queue(int(data['QueueIndex']))

  def hdl_tag_track(self, socket, data):
    self.library.tag_track(data['track'], data['tag'])
    # Broadcast to all clients that the taglist has changed
    self.hdl_list_tags(None, None)
    # Broadcast to all clients that the queue has changed
    self.hdl_list_queue(None, None)

  def hdl_untag_track(self, socket, data):
    self.library.untag_track(data['track'], data['tag'])
    # Broadcast to all clients that the taglist has changed
    self.hdl_list_tags(None, None)
    # Broadcast to all clients that the queue has changed
    self.hdl_list_queue(None, None)

  def init(self):
    self.player.init(self)
    self.library.init()

  def raise_client_event(self, message, data='', client=None):
    obj = {
      'message': message,
      'data': data,
    }
    if client:
      print '[WS] -> Sending message to a specific client: %s' % (message)
      client.write_message(obj)
    else:
      #print '[WS] -> Broadcasting raw message to %s clients: %s' % (len(self.clients), obj)
      print '[WS] -> Broadcasting message to %s clients: %s' % (len(self.clients), message)
      for client in self.clients:
        client.write_message(obj)

  def run(self):
    port = 8088
    self.listen(port)
    print '[SERVER] Listening on port %d' % port
    try:
      tornado.ioloop.IOLoop.instance().start()
    finally:
      self.player.quit()

  def scan_library(self):
    self.player.update_library()
    self.library.scan_library()
    self.raise_client_event('scan_library_finished')

  class MainHandler(tornado.web.RequestHandler):
    def get(self):
      self.redirect("static/musiclibrary.html")

  class SocketHandler(tornado.websocket.WebSocketHandler):

    def __init__(self, application, request):
      tornado.websocket.WebSocketHandler.__init__(self, application, request)
      self.MESSAGE_HANDLERS = {
        'delete': self.application.hdl_delete,
        'get_coverart': self.application.hdl_get_coverart,
        'enqueue': self.application.hdl_enqueue,
        'list_queue': self.application.hdl_list_queue,
        'list_tags': self.application.hdl_list_tags,
        'list_tracks': self.application.hdl_list_tracks,
        'next': self.application.hdl_next,
        'play': self.application.hdl_play,
        'play_pause_toogle': self.application.hdl_play_pause_toogle,
        'play_tag': self.application.hdl_play_tag,
        'rename_tag': self.application.hdl_rename_tag,
        'scan_library': self.application.hdl_scan_library,
        'stop': self.application.hdl_stop,
        'remove_from_queue': self.application.hdl_remove_from_queue,
        'tag_track': self.application.hdl_tag_track,
        'untag_track': self.application.hdl_untag_track,
      }

    def open(self):
      self.application.clients += [self]
      print "[WS] WebSocket opened from %s. Now we have %s clients!" % (str(self.request.remote_ip), len(self.application.clients))

    @tornado.web.asynchronous
    @tornado.gen.engine
    def on_message(self, message):
      try:
        print '[WS] <- Received raw message: %s' % message
        obj = json.loads(message)
        message = obj['message']
        data = None
        if 'data' in obj.keys():
          data = obj['data']

        if message in self.MESSAGE_HANDLERS.keys():
          self.MESSAGE_HANDLERS[message](self, data)
        else:
          print "[WS] Unknown message received: %s" % message
      except Exception as e:
        print "[WS] Exception %s" % e

    def on_close(self):
      print "[WS] WebSocket closed, now down to %s clients" % len(self.application.clients)
      self.application.clients.remove(self)


def main():
  server = Server()
  server.init()
  server.run()

if __name__ == "__main__":
    main()