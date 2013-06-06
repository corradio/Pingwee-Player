import mpd
import os
import select
import time

from datetime import datetime
from threading import Thread


class Player:
  MPD_ROOT = "/Users/corradio/Music/"

  mpc = mpd.MPDClient()
  server = None
  check_for_track_played = False
  dt_newtrack_played = None

  def clear_queue(self):
    self.mpc.clear()

  def enqueue(self, track):
    self.mpc.add("%s" % track.replace(self.MPD_ROOT, ''))

  def get_queue(self):
    queue = self.mpc.playlist()
    print queue
    return {
      'Tracks': [self.parse_mpd_track(track) for track in queue],
      'TrackInfos': [self.server.library.map_track_info[self.parse_mpd_track(track)] for track in queue],
    }

  def get_status(self):
    return self.mpc.status()
    # status.keys gives ['songid', 'playlistlength', 'playlist', 'repeat', 'consume', 'mixrampdb', 'random', 'state', 'xfade', 'volume', 'single', 'mixrampdelay', 'time', 'song', 'elapsed', 'bitrate', 'audio']

  def init(self, server):
    self.server = server

    os.system('mpd')

    self.mpc.connect("localhost", 6600)
    self.mpc.consume(1)
    self.mpc.crossfade(2)
    self.mpc.replay_gain_mode('track')

    thread_mpd_fetch_idle = Thread(target=self.mpd_fetch_idle, args=())
    thread_mpd_fetch_idle.setDaemon(True)
    thread_mpd_fetch_idle.start()

    thread_mpd_detect_track_played = Thread(target=self.mpd_detect_track_played, args=())
    thread_mpd_detect_track_played.setDaemon(True)
    thread_mpd_detect_track_played.start()

  def mpd_detect_track_played(self):
    while True:
      if self.check_for_track_played:
        status = self.get_status()
        if 'time' in status.keys():
          time_played, unused, time_total = status['time'].partition(':')
          time_played = float(time_played)
          time_total = float(time_total)
          if time_played/time_total > 0.5:
            track = self.get_queue()['Tracks'][0]
            self.server.library.mark_track_played(track)
            self.check_for_track_played = False
            print '[PLAYER] Track marked as played: %s' % track
      time.sleep(1)

  def mpd_fetch_idle(self):
    mpc = mpd.MPDClient()
    mpc.connect("localhost", 6600)
    while True:
      mpc.send_idle()
      select.select([mpc], [], [])
      response = mpc.fetch_idle()

      print '[PLAYER] Event raised: %s' % response

      if len(response) == 2:
        if 'playlist' in response and 'player' in response:
          # This is a next song event [we might have reached the end of the queue]
          self.set_current_track_as_new()
          self.server.raise_client_event('queue_changed', self.get_queue())
          self.server.raise_client_event('player_changed', self.get_status()['state'])
      elif len(response) == 1:
        event = response[0]

        if event == 'playlist':
          self.server.raise_client_event('queue_changed', self.get_queue())

        elif event == 'player':
          self.server.raise_client_event('player_changed', self.get_status()['state'])

  def next():
    self.mpc.next()

  def parse_mpd_track(self, track):
    return '%s%s' % (self.MPD_ROOT, track.replace('file: ', '').encode('utf8'))

  def playpausetoogle(self):
    if (self.get_status()['state'] == 'play'):
      self.pause()
    else:
      self.play()

  def pause(self):
    self.mpc.pause()

  def play(self, tracks=None):
    if isinstance(tracks, list):
      self.clear_queue()
      self.set_current_track_as_new()
      for track in tracks:
        self.enqueue(track)
      self.play()
    elif tracks and tracks != '':
      self.play([tracks])
    else:
      # If player is at the start of a song, then it is
      # eligible for being marked as played later on
      status = self.get_status()
      if status['state'] == 'stop':
        self.set_current_track_as_new()
      self.mpc.play()

  """
  This will make this track eligible for being marked as played.
  """
  def set_current_track_as_new(self):
    self.check_for_track_played = True
    self.dt_newtrack_played = datetime.now()

  def stop(self):
    self.mpc.stop()

  def update_library(self):
    self.mpc.update()

  def quit(self):
    os.system('mpd --kill')
