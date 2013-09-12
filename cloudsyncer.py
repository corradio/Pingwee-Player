"""EXPERIMENTAL: Sync a given tag with the cloud"""

import json
import os
import shutil

from dropbox import client, rest, session

class CloudSyncer:

  # TODO: Put this in a configuration file
  #DROPBOX_PATH = '/Users/corradio/Dropbox/Apps/pingweeplayer/'
  DROPBOX_PATH = '/Users/corradio/Music/BTSync_music'

  server = None
  tags_to_sync = ["Hot"]

  def init(self, server):
    self.server = server

    self.sync()

    

  def sync(self):
    # TODO: Here do a sync and not only an add

    for tag in self.tags_to_sync:
      for filepath in self.server.library.map_tag_tracks[tag]:
        filename = os.path.basename(filepath)
        dst = '%s/%s' % (self.DROPBOX_PATH, filename)
        if True:
          shutil.copy(filepath, dst)
        #if not os.path.islink(dst):
        #  os.symlink(filepath, dst)
