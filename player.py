import mpd
import os
import select

from threading import Thread


class Player:
  MPD_ROOT = "/Users/corradio/Music/"

  mpc = mpd.MPDClient()
  server = None

  def clear_queue(self):
    self.mpc.clear()

  def enqueue(self, track):
    self.mpc.add("%s" % track.replace(self.MPD_ROOT, ''))

  def get_queue(self):
    queue = self.mpc.playlist()
    return {
      'Tracks': [self.server.library.map_track_info['%s%s' % (self.MPD_ROOT, track.replace('file: ', '').encode('utf8'))] for track in queue],
      'TrackInfos': [self.server.library.map_track_info['%s%s' % (self.MPD_ROOT, track.replace('file: ', '').encode('utf8'))] for track in queue],
    }

  def init(self, server):
    self.server = server

    os.system('mpd')

    self.mpc.connect("localhost", 6600)
    self.mpc.crossfade(2)
    self.mpc.replay_gain_mode('track')

    thread_mpd_fetch_idle = Thread(target=self.mpd_fetch_idle, args=())
    thread_mpd_fetch_idle.setDaemon(True)
    thread_mpd_fetch_idle.start()

  def mpd_fetch_idle(self):
    mpc = mpd.MPDClient()
    mpc.connect("localhost", 6600)
    while True:
      mpc.send_idle()
      select.select([mpc], [], [])
      response = mpc.fetch_idle()
      for event in response:
        message = None
        data = None

        if event == 'playlist':
          message = 'queue_changed'
          data = self.get_queue()

        elif event == 'player':
          message = 'player_changed'
          data = None

        else:
          message = event

        print '[PLAYER] Event raised: %s' % message
        self.server.raise_client_event(message, data)

  def playpausetoogle(self):
    pass

  def play(self, track):
    self.clear_queue()
    self.enqueue(track)
    self.mpc.play()

  def stop(self):
    self.mpc.stop()

  def update_library(self):
    self.mpc.update()

  def quit(self):
    os.system('mpd --kill')
