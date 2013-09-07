#!/usr/bin/python

import cdburner
import cloudsyncer
import coverart
import base64
import json
import library
import player
import os
import random
import traceback
import urllib2

import tornado.gen
import tornado.ioloop
import tornado.web
import tornado.websocket

from threading import Thread


class Server(tornado.web.Application):

  clients = []

  cdburner = cdburner.CDBurner()
  cloudsyncer = cloudsyncer.CloudSyncer()
  library = library.Library()
  player = player.Player()

  def __init__(self):
    handlers = [
      (r"/", self.MainHandler),
      (r"/websocket", self.SocketHandler),
    ]
    settings = dict(
      static_path=os.path.join(os.path.dirname(__file__), "static"),
    )
    tornado.web.Application.__init__(self, handlers, **settings)

  def hdl_burn_cd(self, socket, data):
    tag = 'Burn'
    map_tag_tracks = self.library.map_tag_tracks
    map_track_info = self.library.map_track_info
    tracks = map_tag_tracks[tag]
    trackinfos = [map_track_info[track] for track in tracks]
    self.cdburner.burn_cd(tracks, trackinfos)

  def hdl_delete(self, socket, data):
    queue = self.player.get_queue()

    if 'track' in data:
      track = data['track']
    elif 'QueueIndex' in data:
      track = self.player.get_queue()['Tracks'][data['QueueIndex']]
    else:
      # Assume the currently playing track is targetted
      i = queue['QueueIndexOfCurrentlyPlaying']
      track = queue['Tracks'][i]

    # Is the current track being played? If yes, remove from playback
    try:
      i = queue['Tracks'].index(track)
      self.player.remove_from_queue(i)
      print "[SERVER] Track removed from queue index %d: %s" % (i, track)
    except ValueError:
      pass
    
    self.library.delete(track)

  def hdl_describe_currently_playing(self, socket, data):
    self.raise_client_event('describe_currently_playing', self.player.get_currently_playing(), socket)

  def hdl_enqueue(self, socket, data):
    self.player.enqueue(data['track'])

  def hdl_get_coverart(self, socket, data):
    if 'track' in data:
      track = data['track']
    elif 'QueueIndex' in data:
      track = self.player.get_queue()['Tracks'][data['QueueIndex']]

    obj = {
      'data': '',
      'Track': track,
    }

    cover = self.library.get_track_coverart(track)
    if cover:
      obj['data'] = "data:image/png;base64,%s" % base64.b64encode(cover['data'])
      obj['source'] = cover['source']
    else:
      obj['data'] = 'http://static.tumblr.com/jn9hrij/20Ul2zzsr/albumart.jpg'
      obj['source'] = None


    # Move all of this inside the library file
    """print '[SERVER] Cover Art is not available in library: fetching from web.'
    query = '%s %s %s cover' % (
      self.library.map_track_info[track]['artist'] if 'artist' in self.library.map_track_info[track] else '',
      self.library.map_track_info[track]['album'] if 'album' in self.library.map_track_info[track] else '',
      self.library.map_track_info[track]['title'] if 'title' in self.library.map_track_info[track] else ''
    )
    if query != '%s %s %s cover' % ('', '', ''):
      obj['data'] = "data:image/png;base64,%s" % coverart.getbase64image(query)
    """
    
    self.raise_client_event('get_coverart', obj, socket)

  def hdl_list_queue(self, socket, data):
    queue = self.player.get_queue()
    if data and 'index' in data:
      queue = [queue[data['index']]]
    self.raise_client_event('queue_changed', queue, socket)
    self.raise_client_event('describe_queue', queue, socket)

  def hdl_list_tags(self, socket, data):
    map_tag_tracks = self.library.map_tag_tracks
    obj = {
      'Tags': sorted(map_tag_tracks.keys(), key=lambda s: s.lower())
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
    if shuffle and not data['tag'] == '!RecentlyAdded':
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

  def hdl_set_track_coverart(self, socket, data):
    if 'track' not in data:
      # Assume the currently playing track is targetted
      queue = self.player.get_queue()
      i = queue['QueueIndexOfCurrentlyPlaying']
      track = queue['Tracks'][i]
    else:
      track = data['track']

    if 'url' in data.keys():
      # This is a URL, let's fetch from web
      request = urllib2.Request(data['url'])
      response = urllib2.urlopen(request)
      data = {
        'mime': response.info().getheader('Content-Type'),
        'data': response.read(),
      }
      response.close()
    else:
      data['data'] = base64.b64decode(data['data'])

    self.library.set_track_coverart(track, data['data'], data['mime'])
    self.hdl_get_coverart(socket=None, data={'track': track})

  def hdl_set_track_info(self, socket, data):
    if 'track' not in data:
      # Assume the currently playing track is targetted
      queue = self.player.get_queue()
      i = queue['QueueIndexOfCurrentlyPlaying']
      data['track'] = queue['Tracks'][i]
    for field in data.keys():
      if field == 'track':
        continue
      else:
        self.library.write_field(
          data['track'],
          field,
          data[field],
          True
        )
    self.library.save_database()

  def hdl_stop(self, socket, data):
    self.player.stop()

  def hdl_remove_from_queue(self, socket, data):
    self.player.remove_from_queue(int(data['QueueIndex']))

  def hdl_tag_track(self, socket, data):
    if 'track' not in data:
      # Assume the currently playing track is targetted
      queue = self.player.get_queue()
      i = queue['QueueIndexOfCurrentlyPlaying']
      data['track'] = queue['Tracks'][i]
    if (self.library.tag_track(data['track'], data['tag'])):
      # Broadcast to all clients that the taglist has changed
      self.hdl_list_tags(None, None)
      # Broadcast to all clients that the queue has changed
      self.hdl_list_queue(None, None)

  def hdl_untag_track(self, socket, data):
    if 'track' not in data:
      # Assume the currently playing track is targetted
      queue = self.player.get_queue()
      i = queue['QueueIndexOfCurrentlyPlaying']
      data['track'] = queue['Tracks'][i]
    self.library.untag_track(data['track'], data['tag'])
    # Broadcast to all clients that the taglist has changed
    self.hdl_list_tags(None, None)
    # Broadcast to all clients that the queue has changed
    self.hdl_list_queue(None, None)

  def init(self):
    self.player.init(self)
    self.library.init()
    self.cloudsyncer.init(self)
    self.cdburner.init(self)

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
      print '[WS] -> Broadcasting message to all (%s) clients: %s' % (len(self.clients), message)
      for client in self.clients:
        client.write_message(obj)

  def run(self):
    port = 8088
    self.listen(port)
    print "[SERVER] Listening on port %d.. we're now up and running!!" % port
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
        'burn_cd': self.application.hdl_burn_cd,
        'delete': self.application.hdl_delete,
        'describe_currently_playing': self.application.hdl_describe_currently_playing,
        'describe_queue': self.application.hdl_list_queue,
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
        'set_track_coverart': self.application.hdl_set_track_coverart,
        'set_track_info': self.application.hdl_set_track_info,
        'stop': self.application.hdl_stop,
        'remove_from_queue': self.application.hdl_remove_from_queue,
        'tag_track': self.application.hdl_tag_track,
        'untag_track': self.application.hdl_untag_track,
      }

    def open(self):
      self.application.clients += [self]
      print "[WS] WebSocket opened from %s. Now we have %s clients!" % (str(self.request.remote_ip), len(self.application.clients))

      self.application.raise_client_event(
        'describe_player_state',
        self.application.player.get_status(),
        self,
      )

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
        traceback.print_exc()

    def on_close(self):
      self.application.clients.remove(self)
      print "[WS] WebSocket closed, now down to %s clients" % len(self.application.clients)


def main():
  server = Server()
  server.init()
  server.run()

if __name__ == "__main__":
    main()