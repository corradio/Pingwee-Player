import mpd
import os
import select

from threading import Thread


class Player:
  MPD_ROOT = "/Users/corradio/Music/"

  mpc = mpd.MPDClient()

  def init(self):
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
      print 'R: %s' % response

  def playpausetoogle(self):
    return

  def play(self, track):
    self.mpc.clear()
    self.mpc.add("%s" % track.replace(self.MPD_ROOT, ''))
    self.mpc.play()

  def enqueue(self, track):
    self.mpc.add("%s" % track.replace(self.MPD_ROOT, ''))

  def stop(self):
    self.mpc.stop()

  def quit(self):
    os.system('mpd --kill')
