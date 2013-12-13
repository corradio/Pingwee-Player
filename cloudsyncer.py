"""EXPERIMENTAL: Sync a given tag with the cloud"""

import json
import os
import shutil

class CloudSyncer:

  # TODO: Put this in a configuration file
  CLOUD_PATH = '/Users/olc/Music/BTSync/pingweeplayer'
  DB_FILE = os.path.join(CLOUD_PATH, 'db.json')

  server = None
  TAG_TO_SYNC = "Hot"

  def init(self, server):
    self.server = server
    self.sync()

  def get_watched_tags(self):
    return [self.TAG_TO_SYNC]

  def remove_file(self, file):
    filename = os.path.basename(file)
    dst = os.path.join(self.CLOUD_PATH, filename)
    os.path.remove(file)

  def sync(self):
    # TODO(olc)The idea here is to read a changelog.json file, and then taking action on playcounts...
    print "[CLOUDSYNCER] Warning: file names must be uniques. Use some method to check that it holds."
    
    # Read the db file to see if any file has been deleted
    if os.path.exists(self.DB_FILE):
      f = open(self.DB_FILE, 'r')
      local_db = json.loads(f.read())
      f.close()
      for dirname, dirnames, filenames in os.walk(self.CLOUD_PATH):
        # Convert to unicode
        filenames = [unicode(filename, 'utf8') for filename in filenames]
        # Check that each track of the local db is still there
        for track in local_db['Tracks']:
          filename = os.path.basename(track)
          if not filename in filenames:
            print "[CLOUDSYNCER] %s was removed from cloud. Untagging this one." % filename
            self.server.library.untag_track(track, self.TAG_TO_SYNC)

    # Extract server db
    if not os.path.exists(self.CLOUD_PATH):
      os.mkdir(self.CLOUD_PATH)
    if not self.TAG_TO_SYNC in self.server.library.map_tag_tracks:
      return
    tracks = self.server.library.map_tag_tracks[self.TAG_TO_SYNC]
    db = {
      'Tracks': tracks,
      'TrackInfos': [self.server.library.map_track_info[track] for track in tracks],
      'GeneratedAt': '[TOBEIMPLEMENTED]'
    }
    
    # Copy files
    for filepath in tracks:
      filename = os.path.basename(filepath)
      dst = os.path.join(self.CLOUD_PATH, filename)
      if not os.path.exists(filepath):
        print "[CLOUDSYNCER] Skipping %s as it does not exist. Please update library." % filepath
        continue
      if not os.path.exists(dst):
        shutil.copy(filepath, dst)

    # Also copy the db
    data = json.dumps(db)
    f = open(self.DB_FILE, 'w')
    f.write(data)
    f.close()

    print "[CLOUDSYNCER] Files synced."