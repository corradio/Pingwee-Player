"""Everything that has to do with the file system"""

import json
import os
import mutagen.id3
import sys
import time
import traceback

from datetime import datetime
from dirtools import Dir, DirState
from mutagen.apev2 import APEv2
from mutagen.flac import FLAC
from mutagen.id3 import ID3, TXXX, ID3NoHeaderError
from mutagen.mp3 import MP3
from subprocess import call
from threading import Thread

class Library:

  MAP_ID3_FIELDS = {
    'bpm': 'TBPM',
    'tags': 'TXXX:TAG',
    'album': 'TALB',
    'artist': 'TPE1',
    'title': 'TIT2',
    'date': 'TDRC',
    'key': 'TKEY',
    'tracknumber': 'TRCK',
    'first_played': 'TXXX:FIRST_PLAYED',
    'first_added': 'TXXX:FIRST_ADDED',
    'last_played': 'TXXX:LAST_PLAYED',
    'play_counter': 'TXXX:PLAY_COUNTER',
    'replaygain_track_gain': 'TXXX:replaygain_track_gain',
    'replaygain_album_gain': 'TXXX:replaygain_album_gain',
    'mp3gain': 'TXXX:MP3GAIN_MINMAX',
    'lyrics': 'TXXX:LYRICS',
  }

  MAP_FLAC_FIELDS = {
    'bpm': 'bpm',
    'tags': 'tag',
    'album': 'album',
    'artist': 'artist',
    'title': 'title',
    'date': 'date',
    'tracknumber': 'tracknumber',
    'first_played': 'first_played',
    'first_added': 'first_added',
    'last_played': 'last_played',
    'play_counter': 'play_counter',
    'replaygain_track_gain': 'replaygain_track_gain',
    'replaygain_album_gain': 'replaygain_album_gain',
    'lyrics': 'lyrics',
  }

  MAP_REPLAYGAIN_BIN = {
    '.FLAC': 'metaflac --add-replay-gain',
    '.MP3': '%s %s' % (os.path.join(os.path.dirname(__file__), 'bin/mp3gain'), '-p -q -s i'),
  }

  MULTILINE_FIELDS = [
    'tags',
  ]

  DATETIME_TAG_FORMAT = '%Y-%m-%d %H:%M:%S'
  DATABASE_FILENAME = os.path.join(os.path.dirname(__file__), 'database.json')

  EXTENSIONS = ['.MP3', '.FLAC']

  LIBRAIRIES = [
    "/Users/olc/Music/iTunes/iTunes Media",
    "/Users/olc/Music/Logic",
    "/Users/olc/Music/Library",
    "/Users/olc/Downloads",
  ]

  PODCAST_DIRECTORIES = [
    "/Users/olc/Music/iTunes/iTunes Media/Podcasts",
    "/Users/olc/Music/iTunes/iTunes Media/Recordings",
    "/Users/olc/Music/iTunes/iTunes Media/Mixes",
    "/Users/olc/Music/Library/TOU",
  ]

  SPECIAL_TAGS = [
    '!NeverPlayed',
    '!Podcast',
    '!RecentlyAdded',
    '!Untagged',
  ]

  TRASH_PATH = '/Users/olc/.Trash'

  WATCHDOG_POLL_PERIOD_SECONDS = 60

  map_tag_tracks = {}
  map_track_info = {}

  def delete(self, track):
    # Library removal
    if 'tags' in self.map_track_info[track]:
      for tag in self.map_track_info[track]['tags']:
        self.map_tag_tracks[tag].remove(track)
        if len(self.map_tag_tracks[tag]) == 0:
          del self.map_tag_tracks[tag]
    del self.map_track_info[track]
    # IO removal
    #os.remove(track)
    os.rename(track, os.path.join(self.TRASH_PATH, os.path.basename(track)))
    # Save
    self.save_database()
    print "[LIBRARY] Track moved to trash: %s" % track

  def get_track_coverart(self, file):
    def try_fetch_from_filesystem():
      path = os.path.join(os.path.dirname(file), 'folder.jpg')
      try:
        f = open(path, 'r')
        data = f.read()
        f.close()
        return {
          'data': data,
          'mime': 'image/jpeg',
          'source': 'folder.jpg',
        }
      except:
        return None

    filename, extension = os.path.splitext(file)
    if extension.upper() == '.MP3':
      audio = MP3(file)
      if 'APIC:' in audio.tags:
        return {
          'data': audio.tags['APIC:'].data,
          'mime': audio.tags['APIC:'].mime,
          'source': 'metadata',
        }
      else:
        return try_fetch_from_filesystem()
    elif extension.upper() == '.FLAC':
      audio = FLAC(file)
      if len(audio.pictures) > 0:
        return {
          'data': audio.pictures[0].data,
          'mime': audio.pictures[0].mime,
          'source': 'metadata',
        }
      else:
        return try_fetch_from_filesystem()

  def set_track_coverart(self, file, data, mime):
    filename, extension = os.path.splitext(file)
    if extension.upper() == '.MP3':
      audio = MP3(file)
      apic = mutagen.id3.APIC(
        desc     = u'',
        encoding = 3,
        data     = data,
        mime     = mime,
        type     = 3, # Front Cover is 3
      )
      audio.tags.add(apic)
    elif extension.upper() == '.FLAC':
      audio = mutagen.File(file)
      image = mutagen.flac.Picture()
      image.desc = u''
      image.data = data
      image.type = 3
      image.mime = mime
      audio.add_picture(image)
    audio.save()
    print "[LIBRARY] Coverart written in file %s" % os.path.basename(file)


  def get_track_info(self, file):
    filename, extension = os.path.splitext(file)
    info = {}

    def read_info(audio, MAP_FIELDS):
      for field in MAP_FIELDS.keys():
        if MAP_FIELDS[field] in audio.keys():
          if audio.__class__ == mutagen.id3.ID3:
            data = UTF8Encode(audio[MAP_FIELDS[field]].text)
          elif audio.__class__ == mutagen.flac.FLAC:
            data = UTF8Encode(audio[MAP_FIELDS[field]])
          # Flatten everything which is not multiline
          if field in self.MULTILINE_FIELDS:
            if not isinstance(data, list):
              data = [data]
          elif isinstance(data, list):
            data = ';'.join(data)
          info[field] = data

    if extension.upper() == '.MP3':
      try:
        audio = ID3(file)
        read_info(audio, self.MAP_ID3_FIELDS)
      except mutagen.id3.ID3NoHeaderError:
        print 'Warning: No ID3 header found in file %s' % file
    elif extension.upper() == '.FLAC':
      audio = FLAC(file)
      read_info(audio, self.MAP_FLAC_FIELDS)

    return info

  def init(self):
    try:
      f = open(self.DATABASE_FILENAME, 'r')
      data = json.loads(f.read())
      f.close()
      self.map_tag_tracks = data['map_tag_tracks']
      self.map_track_info = data['map_track_info']
      data = None
      print '[LIBRARY] Database read from file'
    except IOError:
      pass
    # Start watchdog
    for library in self.LIBRAIRIES:
      watchdog = Thread(target=self.watch_library, args=(library))
      watchdog.setDaemon(True)
      watchdog.start()

  def mark_track_played(self, file):
    info = self.map_track_info[file]
    if 'play_counter' in info.keys():
      counter = int(info['play_counter']) + 1
    else:
      # This track was never played before, but now it has been.
      self.map_tag_tracks['!NeverPlayed'].remove(file)
      counter = 1
    # Remember that this will trigger a database save
    self.write_fields(file,
      {
        'play_counter': str(counter),
        'last_played': datetime.now().strftime(self.DATETIME_TAG_FORMAT),
      }
    )

  def scan_file(self, temp_map_tag_tracks, temp_map_track_info, dirname, filename):
    file = unicode(os.path.join(dirname, filename), 'utf8')
    unused, ext = os.path.splitext(filename)
    if ext.upper() in self.EXTENSIONS:
      try:
        temp_map_track_info[file] = self.get_track_info(file)
        if 'tags' in temp_map_track_info[file]:
          tags = temp_map_track_info[file]['tags']
          if len(tags) == 0:
            temp_map_tag_tracks['!Untagged'] += [file]
          for tag in tags:
            if tag in temp_map_tag_tracks:
              temp_map_tag_tracks[tag] += [file]
            else:
              temp_map_tag_tracks[tag] = [file]
        else:
          temp_map_tag_tracks['!Untagged'] += [file]
          temp_map_track_info[file]['tags'] = []

        # !RecentlyAdded
        if not 'first_added' in temp_map_track_info[file]:
          first_added = datetime.now().strftime(self.DATETIME_TAG_FORMAT)
          self.write_field(file, 'first_added', first_added, True)
          # Remember that writing here will update the current DB, but not the temporary one we are creating here
          temp_map_track_info[file]['first_added'] = first_added
          print 'Welcome to the library %s' % file
        if (datetime.now() - datetime.strptime(temp_map_track_info[file]['first_added'],
                                               self.DATETIME_TAG_FORMAT)).days <= 90:
            temp_map_tag_tracks['!RecentlyAdded'] += [file]

        # !NeverPlayed
        if not 'play_counter' in temp_map_track_info[file]:
          temp_map_tag_tracks['!NeverPlayed'] += [file]

        # !Podcast
        if any([x in os.path.join(dirname, '') for x in self.PODCAST_DIRECTORIES]):
          temp_map_tag_tracks['!Podcast'] += [file]

        # ReplayGain support
        if (not 'replaygain_track_gain' in temp_map_track_info[file] 
          and not 'mp3gain' in temp_map_track_info[file]
          and not file in temp_map_tag_tracks['!Podcast']):
          call('%s "%s"' % (self.MAP_REPLAYGAIN_BIN[ext.upper()], file), shell=True)
          # Re-read tags
          temp_map_track_info[file] = self.get_track_info(file)

      except Exception, e:
        traceback.print_exc()
    elif ext.upper() in ['.WAV', '.OGG']:
      print '[LIBRARY] Unsupported %s format %s' % (ext.upper(), file)

  def scan_library(self):
    temp_map_tag_tracks = {}
    temp_map_track_info = {}
    for tag in self.SPECIAL_TAGS:
      temp_map_tag_tracks[tag] = []

    print '[LIBRARY] Library scan started'
    for library in self.LIBRAIRIES:
      for dirname, dirnames, filenames in os.walk(library):
        #print 'Scanning %s' % dirname
        for filename in filenames:
          scan_file(temp_map_tag_tracks, temp_map_track_info, dirname, filename)

    # Postprocessing begins

    # Sort !RecentlyAdded by first_added
    temp_map_tag_tracks['!RecentlyAdded'] = sorted(
      temp_map_tag_tracks['!RecentlyAdded'],
      key=lambda track: temp_map_track_info[track]['first_added'],
      reverse=True,
    )

    print '[LIBRARY] Library scan finished'
    # Commit to memory and disk
    self.map_tag_tracks = temp_map_tag_tracks
    self.map_track_info = temp_map_track_info
    self.save_database()

  def rename_tag(self, old, new):
    # Declare new tag
    if not new in self.map_tag_tracks.keys():
      self.map_tag_tracks[new] = []
    # Fetch tracks to modify
    tracks = self.map_tag_tracks[old]
    # Loop through them
    for track in tracks:
      # Fetch a track's tags
      tags = self.map_track_info[track]['tags']
      # Modify
      tags.remove(old)
      tags.append(new)
      # Commit on file and db
      self.write_field(track, 'tags', tags, bypassdbwrite=True)
      # Update the taglist
      self.map_tag_tracks[new].append(track)
    # Delete old tag
    del self.map_tag_tracks[old]
    # Save
    self.save_database()

  def save_database(self):
    data = json.dumps(
      {
        'map_tag_tracks': self.map_tag_tracks,
        'map_track_info': self.map_track_info
      }
    )
    f = open(self.DATABASE_FILENAME, 'w')
    f.write(data)
    f.close()
    print '[LIBRARY] Database written.'

  def tag_track(self, track, tag):
    if 'tags' not in self.map_track_info[track]:
      self.map_track_info[track]['tags'] = []
    tags = self.map_track_info[track]['tags']
    if tag in tags:
      # It's already there
      return False
    tags.append(tag)
    self.write_field(track, 'tags', tags, bypassdbwrite=True)
    # Declare new tag if needed
    if not tag in self.map_tag_tracks.keys():
      self.map_tag_tracks[tag] = []
    # Append
    self.map_tag_tracks[tag].append(track)
    # Save
    self.save_database()
    return True

  def untag_track(self, track, tag):
    tags = self.map_track_info[track]['tags']
    tags.remove(tag)
    self.write_field(track, 'tags', tags, bypassdbwrite=True)
    # Remove track from tag list
    self.map_tag_tracks[tag].remove(track)
    # Remove tag if empty
    if len(self.map_tag_tracks[tag]) == 0:
      del self.map_tag_tracks[tag]
    # Save
    self.save_database()

  def watch_library(self, library):
    d = Dir(library)
    ref = DirState(d)
    while (True):
      time.sleep(WATCHDOG_POLL_PERIOD_SECONDS)
      new = DirState(d)
      diff = new - ref
      for file_added in diff['created']:
        print '[LIBRARY] Watchdog detected a new file: %s' % file_added
        self.scan_file(map_tag_tracks, map_track_info, library, file_added)
      ref = new


  def write_fields(self, file, dictkeyvalues, bypassdbwrite=False):
    for key in dictkeyvalues.keys():
      self.write_field(file, key, dictkeyvalues[key], bypassdbwrite=True)
    if not bypassdbwrite:
      self.save_database()

  def write_field(self, file, field, value, bypassdbwrite=False):
    filename, extension = os.path.splitext(file)
    if extension.upper() == '.MP3':
      # Try to open the ID3 tags
      try:
        audio = ID3(file)
      except mutagen.id3.ID3NoHeaderError:
        # Save a blank ID3 header first
        audio = ID3()
      id3field = self.MAP_ID3_FIELDS[field]
      fieldtype, unused, fieldname = id3field.partition(':')
      gentag = getattr(mutagen.id3, fieldtype)
      audio[id3field] = gentag(encoding=3, desc=u'%s' % fieldname, text=value)
      #audio['TXXX:TAG'] = TXXX(encoding=3, desc=u'TAG', text=tags)
    elif extension.upper() == '.FLAC':
      audio = FLAC(file)
      audio[self.MAP_FLAC_FIELDS[field]] = value
    audio.save(file)
    print "[LIBRARY] Field '%s' written in file %s" % (field, os.path.basename(file))

    # Update DB if needed
    if file in self.map_track_info:
      self.map_track_info[file][field] = value
      if not bypassdbwrite:
        self.save_database()

def UTF8Encode(obj):
  if isinstance(obj, list):
    return [s.encode('utf8') for s in obj]
  else:
    return obj.encode('utf8')
