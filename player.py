import logging
import mpd
import os
import osax
import select
import time

from datetime import datetime
from threading import Thread, Lock


class LockableMPDClient(mpd.MPDClient):
  def __init__(self, use_unicode=False):
    super(LockableMPDClient, self).__init__()
    self.use_unicode = use_unicode
    self._lock = Lock()
  def acquire(self):
    self._lock.acquire()
  def release(self):
    self._lock.release()
  def __enter__(self):
    self.acquire()
  def __exit__(self, type, value, traceback):
    self.release()


class Player:
  MPD_ROOT = "/Users/corradio/Music/"

  mpc = LockableMPDClient()
  server = None
  check_for_track_played = False
  dt_newtrack_played = None

  # Apple Script for controlling volume
  appscript = None

  def clear_queue(self):
    with self.mpc:
      self.mpc.clear()

  def enqueue(self, track, start=0, length=100):
    if isinstance(track, list):
      track = track[0:min(length,len(track))]
      for t in track:
        self.enqueue(t)
    else:
      with self.mpc:
        try:
          self.mpc.add("%s" % track.replace(self.MPD_ROOT, ''))
        except mpd.CommandError as e:
          print '[PLAYER] MPD error: %s for track %s' % (e, track)

  def get_queue(self):
    with self.mpc:
      queue = self.mpc.playlist()
    status = self.get_status()
    indexOfCurrentlyPlaying = int(status['song']) if 'song' in status else -1
    return {
      'Tracks': [self.parse_mpd_track(track) for track in queue],
      'TrackInfos': [self.server.library.map_track_info[self.parse_mpd_track(track)] for track in queue],
      'QueueIndexOfCurrentlyPlaying': indexOfCurrentlyPlaying,
    }
    """
    return {
      'Tracks': [self.parse_mpd_track(track) for track in queue],
      'QueueIndexOfCurrentlyPlaying': indexOfCurrentlyPlaying,
    }
    """

  def get_status(self):
    with self.mpc:
      status = self.mpc.status()
    return status
    # status.keys gives ['songid', 'playlistlength', 'playlist', 'repeat', 'consume', 'mixrampdb', 'random', 'state', 'xfade', 'volume', 'single', 'mixrampdelay', 'time', 'song', 'elapsed', 'bitrate', 'audio']

  def get_track_info(self, track):
    return self.server.library.map_track_info[track]

  def init(self, server):
    self.server = server

    os.system('mpd')

    #logging.basicConfig(level=logging.DEBUG)

    with self.mpc:
      self.mpc.connect("localhost", 6600)
      self.mpc.consume(0)
      self.mpc.crossfade(20)
      self.mpc.replay_gain_mode('track')
      # Sets the threshold at which songs will be overlapped (no fading)
      self.mpc.mixrampdb(-15)
      # Additional overlap
      self.mpc.mixrampdelay(0.5)

    thread_mpd_fetch_idle = Thread(target=self.mpd_fetch_idle, args=())
    thread_mpd_fetch_idle.setDaemon(True)
    thread_mpd_fetch_idle.start()

    thread_mpd_detect_track_played = Thread(target=self.mpd_detect_track_played, args=())
    thread_mpd_detect_track_played.setDaemon(True)
    thread_mpd_detect_track_played.start()

    self.appscript = osax.OSAX()

  def mpd_detect_track_played(self):

    while True:
      if self.check_for_track_played:
        status = self.get_status()
        if 'time' in status.keys():
          time_played, unused, time_total = status['time'].partition(':')
          time_played = float(time_played)
          time_total = float(time_total)
          if time_played/time_total > 0.5:
            queue = self.get_queue()
            track = queue['Tracks'][queue['QueueIndexOfCurrentlyPlaying']]
            print '[PLAYER] Marking track as played: %s' % track
            self.server.library.mark_track_played(track)
            self.check_for_track_played = False
      time.sleep(1)

  def mpd_fetch_idle(self):
    idlempc = mpd.MPDClient()
    idlempc.connect("localhost", 6600)
    songid = -1 # Keep track of the songid currently being played
    while True:
      idlempc.send_idle()
      select.select([idlempc], [], [])
      response = idlempc.fetch_idle()

      print '[PLAYER] MPD event raised: %s' % response

      for event in response:
        if event == 'playlist':
          self.server.raise_client_event('queue_changed', self.get_queue())

        elif event == 'player':
          status = self.get_status()
          self.server.raise_client_event(
            'player_changed',
            {
              'State': status['state'],
              'QueueIndexOfCurrentlyPlaying': int(status['song']) if 'song' in status else '',
            }
          )
          newsongid = int(status['songid']) if 'songid' in status else -1
          if songid != -1 and newsongid != songid:
            # The player automatically transitioned to a new song
            self.set_current_track_as_new()
          songid = newsongid

  def next(self):
    with self.mpc:
      self.mpc.next()

  def parse_mpd_track(self, track):
    return '%s%s' % (self.MPD_ROOT, unicode(track.replace('file: ', ''), 'utf8'))

  def playpausetoogle(self):
    if (self.get_status()['state'] == 'play'):
      self.pause()
    else:
      self.play()

  def pause(self):
    with self.mpc:
      self.mpc.pause()

  def play(self, index=None):
    # If playback has been resumed, then don't force making
    # this track eligible for 'played'
    if (index or self.get_status()['state'] in 'stop'):
      self.set_current_track_as_new()
    with self.mpc:
      if index:
        self.mpc.play(index)
      else:
        self.mpc.play()

  """
  This will make this track eligible for being marked as played.
  """
  def set_current_track_as_new(self):
    self.check_for_track_played = True
    self.dt_newtrack_played = datetime.now()

  def set_volume(self, value):
    # Note that input is in range [0, 10]
    sa.set_volume(value/10.0)

  def stop(self):
    with self.mpc:
      self.mpc.stop()

  def remove_from_queue(self, index):
    with self.mpc:
      self.mpc.delete(index)

  def update_library(self):
    with self.mpc:
      self.mpc.update()

  def quit(self):
    os.system('mpd --kill')
