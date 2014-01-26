"""Everything that has to do with burning a CD"""

import os
import shutil
import subprocess

from subprocess import call

class CDBurner:
  
  # TODO: Put this in a configuration file
  PATH_TO_CDRECORD = '/Users/olc/dev/pingweeplayer/bin/cdrecord'
  PATH_TO_MKISOFS = '/Users/olc/dev/pingweeplayer/bin/mkisofs'
  PATH_TO_LAME = '/Users/olc/dev/pingweeplayer/bin/lame'
  PATH_TO_MP3GAIN =  '%s %s' % (os.path.join(os.path.dirname(__file__), 'bin/mp3gain'), '-r -q')

  PATH_TO_TEMPFOLDER = '/Users/olc/dev/pingweeplayer/tempburn/'
  TEMPTEXTFILE = PATH_TO_TEMPFOLDER + 'tempburn.dat'

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

  def burn_mp3_cd(self, tracks, trackinfos):
    # TODO: Refactor to burn_data_cd

    if not os.path.exists(self.PATH_TO_TEMPFOLDER):
      os.makedirs(self.PATH_TO_TEMPFOLDER)

    # Copy and rename all tracks in the temp dir
    tmptracks = []
    for i in range(len(tracks)):
      track = tracks[i]
      info = trackinfos[i]
      if 'artist' in info and 'title' in info:
        unused, fileext = os.path.splitext(track)
        parent = os.path.dirname(track)
        filename = os.path.basename(track)
        if 'bpm' in info:
          newname = '%s %s - %s%s' % (info['bpm'], info['artist'], info['title'], fileext)
        else:
          newname = '%s - %s%s' % (info['artist'], info['title'], fileext)
        print 'Processing %s' % os.path.join(parent, newname)
        newtrack = os.path.join(self.PATH_TO_TEMPFOLDER, newname)
        if not os.path.exists(newtrack):
          shutil.copyfile(track, newtrack)
          cmd = '%s "%s"' % (self.PATH_TO_MP3GAIN, newtrack)
          call(cmd, shell=True)
        tmptracks.append(newtrack)

    # TODO: Can we order tracks by BPM without renaming them?

    # TODO: Check the file format is compatible
    # Remember to add the necessary flags to mkisofs
    #       Maybe make a folder by artist? or by BPM range?
    cmd = [
      self.PATH_TO_MKISOFS,
      "-J",
      "-R",
      "-joliet-long",
      "-o",
      self.PATH_TO_TEMPFOLDER + "temp.iso"
    ] + tmptracks

    if subprocess.call(cmd) != 0:
      print "[BURN] Error creating ISO"
      return False

    # TODO: Check here if an RW is inserted, and clear it, instead of assuming
    if not self.blank_cdrw():
      print "[BURN] Error blanking CDRW"
      return False

    cmd = [
      self.PATH_TO_CDRECORD,
      self.PATH_TO_TEMPFOLDER + "temp.iso"
    ]
    
    if subprocess.call(cmd) != 0:
      print "[BURN] Error burning CD"
      return False

    shutil.rmtree(self.PATH_TO_TEMPFOLDER)
    print "[BURN] Done!"

    return True

  """DEPRECATED
     There is a problem when burning from CUE files. Works fine if I burn without CUE.
     Still fails with CUE without TEXT
     Find a way to create a .dat cdtext file
  """
  def make_cue(self, tracks, trackinfos):
    """cmd = [
      self.PATH_TO_CDRECORD,
      "-audio",
      "-text",
      "-pad",
      "gracetime=0",
      "-dao",
      "textfile=%s" % self.TEMPTEXTFILE
    ]"""

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

      title = ''
      if 'title' in trackinfo:
        title = trackinfo['title']

      artist = ''
      if 'artist' in trackinfo:
        artist = trackinfo['artist']

      print '[BURN] Preparing %d/%d %s' % (tracknum, len(tracks), filename)

      if extension.upper() != '.WAV':
        # We need to convert this file first
        tmptrack = self.PATH_TO_TEMPFOLDER + os.path.basename(filename) + '.wav'
        #cmd = [self.PATH_TO_LAME, "--silent", "--decode", track, tmptrack]
        #if subprocess.call(cmd) != 0:
        #  print "[BURN] Error while using LAME to convert tracks to WAV: aborting."
        #  return False
        track = tmptrack

      cue = (cue + '\n' +
        'FILE "%s" %s\n' +
        '  TRACK %02d AUDIO\n' +
        '    TITLE "%s"\n' +
        '    PERFORMER "%s"\n' +
        '    INDEX 01 00:00:00') % (track, trackformat, tracknum, title, artist)

    # Write CUE
    f = open(self.TEMPCUEFILE, 'w')
    try:
      f.write(cue.encode('utf-8'))
    finally:
      f.close()

    return True

    