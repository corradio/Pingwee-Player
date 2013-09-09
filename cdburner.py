import os
import shutil
import subprocess

class CDBurner:
  
  PATH_TO_CDRECORD = '/Users/corradio/Downloads/cdrtools-3.01/cdrecord/OBJ/i386-darwin-cc/cdrecord'
  PATH_TO_LAME = '/Users/corradio/Documents/Dev/lame'

  PATH_TO_TEMPFOLDER = '/Users/corradio/Documents/Dev/musiclibrary/tempburn/'
  TEMPCUEFILE = PATH_TO_TEMPFOLDER + 'tempburn.cue'

  server = None

  def init(self, server):
    self.server = server

  def blank_cdrw(self):
    cmd = [
      self.PATH_TO_CDRECORD,
      "gracetime=0",
      "blank=fast"
    ]
    if subprocess.call(cmd) != 0:
      print "[BURN] Error blanking CDRW"
      return False
    return True

  def burn_cd(self, tracks, trackinfos):
    # TODO: Save some time by cleaning the CD while making the cue

    if not os.path.exists(self.PATH_TO_TEMPFOLDER):
      os.makedirs(self.PATH_TO_TEMPFOLDER)

    # TODO: Check here if an RW is inserted, and clear it, instead of assuming
    if not self.blank_cdrw():
      return False

    if not self.make_cue(tracks, trackinfos):
      return False

    cmd = [
      self.PATH_TO_CDRECORD,
      "-audio",
      "-text",
      "-pad",
      "gracetime=0",
      "cuefile=%s" % self.TEMPCUEFILE
    ]
    
    if subprocess.call(cmd) != 0:
      print "[BURN] Error burning CD"
      return False

    shutil.rmtree(self.PATH_TO_TEMPFOLDER)
    print "[BURN] Done, and eject!"

    return True

  def make_cue(self, tracks, trackinfos):
    cdartist = "VA"
    cdtitle = "Pingwee Player Burn"
    cue = 'PERFORMER "%s"\nTITLE "%s"\n' % (cdartist, cdtitle)

    print "[BURN] Preparing tracks for burn (converting, arranging).."
    for i in range(len(tracks)):
      tracknum = i+1
      track = tracks[i]
      trackinfo = trackinfos[i]
      filepath = os.path.basename(track)
      filename, extension = os.path.splitext(filepath)
      trackformat = 'WAVE'
      if extension.upper() != '.WAV':
        # We need to convert this file first
        tmptrack = self.PATH_TO_TEMPFOLDER + os.path.basename(filename) + '.wav'
        cmd = [self.PATH_TO_LAME, "--silent", "--decode", track, tmptrack]
        if subprocess.call(cmd) != 0:
          print "[BURN] Error while using LAME to convert tracks to WAV: aborting."
          return False
        track = tmptrack

      cue = (cue + '\n' +
        'FILE "%s" %s\n' +
        '  TRACK %02d AUDIO\n' +
        '    TITLE "%s"\n' +
        '    PERFORMER "%s"\n' +
        '    INDEX 01 00:00:00') % (track, trackformat, tracknum, trackinfo['title'], trackinfo['artist'])

    # Write CUE
    f = open(self.TEMPCUEFILE, 'w')
    try:
      f.write(cue)
    finally:
      f.close()

    return True

    