"""Everything that has to do with the file system"""

import json
import os
import mutagen.id3
from datetime import datetime
from mutagen.id3 import ID3, TXXX, ID3NoHeaderError
from mutagen.flac import FLAC


class Library:

  MAP_ID3_FIELDS = {
    'tags': 'TXXX:TAG',
    'album': 'TALB',
    'artist': 'TPE2',
    'title': 'TIT2',
    'date': 'TDRC',
    'tracknumber': 'TRCK',
    'first_played': 'TXXX:FIRST_PLAYED',
    'first_added': 'TXXX:FIRST_ADDED',
    'last_played': 'TXXX:LAST_PLAYED',
    'play_counter': 'TXXX:PLAY_COUNTER',
    'replaygain_track_gain': 'TXXX:replaygain_track_gain',
    'replaygain_album_gain': 'TXXX:replaygain_album_gain',
    'bpm': 'bpm',
    'lyrics': 'TXXX:LYRICS',
  }

  MAP_FLAC_FIELDS = {
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
    'bpm': 'bpm',
    'lyrics': 'lyrics',
  }

  MULTILINE_FIELDS = [
    'tags',
  ]

  DATETIME_TAG_FORMAT = '%Y-%m-%d %H:%M:%S'
  DATABASE_FILENAME = 'database.json'

  LIBRAIRIES = [
    "/Users/corradio/Music/iTunes/iTunes Media/",
    "/Users/corradio/Music/Logic",
    "/Users/corradio/Music/Library",
    "/Users/corradio/Downloads",
  ]

  EXTENSIONS = ['.MP3', '.FLAC']

  map_tag_tracks = {}
  map_track_info = {}

  def get_track_info(self, file):
    filename, extension = os.path.splitext(file)
    info = {}

    try:
      if extension.upper() == '.MP3':
        audio = ID3(file)
        MAP_FIELDS = self.MAP_ID3_FIELDS
      elif extension.upper() == '.FLAC':
        audio = FLAC(file)
        MAP_FIELDS = self.MAP_FLAC_FIELDS

      for field in MAP_FIELDS.keys():
        if MAP_FIELDS[field] in audio.keys():
          if extension.upper() == '.MP3':
            data = UTF8Encode(audio[MAP_FIELDS[field]].text)
          elif extension.upper() == '.FLAC':
            data = UTF8Encode(audio[MAP_FIELDS[field]])
          if field not in self.MULTILINE_FIELDS:
            info[field] = ';'.join(data)
          else:
            if not isinstance(data, list):
              data = [data]
            info[field] = data
    except mutagen.id3.ID3NoHeaderError:
      print 'Warning: No ID3 header found in file %s' % file
    return info

  def init(self):
    try:
      f = open(self.DATABASE_FILENAME, 'r')
      data = json.loads(f.read())
      f.close()
      self.map_tag_tracks = data['map_tag_tracks']
      self.map_track_info = data['map_track_info']
      data = None
    except IOError:
      pass

  def scan_library(self):
    self.map_tag_tracks = {'!RecentlyAdded': [], '!Untagged': []}
    self.map_track_info = {}

    print 'Library scan started'
    for library in self.LIBRAIRIES:
      for dirname, dirnames, filenames in os.walk(library):
        print 'Scanning %s' % dirname
        for filename in filenames:
          file = os.path.join(dirname, filename)
          unused, ext = os.path.splitext(filename)
          if ext.upper() in self.EXTENSIONS:
            try:
              self.map_track_info[file] = self.get_track_info(file)
              if 'tags' in self.map_track_info[file].keys():
                tags = self.map_track_info[file]['tags']
                if len(tags) == 0:
                  self.map_tag_tracks['!Untagged'] += [file]
                for tag in tags:
                  if tag in self.map_tag_tracks.keys():
                    self.map_tag_tracks[tag] += [file]
                  else:
                    self.map_tag_tracks[tag] = [file]
              else:
                self.map_tag_tracks['!Untagged'] += [file]

              # Special tags
              if 'first_added' in self.map_track_info[file].keys():
                if (datetime.now() - datetime.strptime(self.map_track_info[file]['first_added'], self.DATETIME_TAG_FORMAT)).days <= 30:
                  self.map_tag_tracks['!RecentlyAdded'] += [file]
              else:
                print 'Welcome to the library %s' % file
                self.write_tag(file, 'first_added', datetime.now().strftime(self.DATETIME_TAG_FORMAT))
            except Exception as e:
              print str(e)
          elif ext.upper() in ['.WAV', '.OGG']:
            print 'Unsupported %s format %s' % (ext.upper(), file)

    print 'Library scan finished'
    data = json.dumps(
      {
        'map_tag_tracks': self.map_tag_tracks,
        'map_track_info': self.map_track_info
      }
    )
    f = open(self.DATABASE_FILENAME, 'w')
    f.write(data)
    f.close()

  def mark_track_played(self, file):
    self.write_tag(file, 'last_played', datetime.now().strftime(self.DATETIME_TAG_FORMAT))
    info = self.get_track_info(file)
    if 'play_counter' in info.keys():
      counter = int(info['play_counter']) + 1
    else:
      counter = 0
    self.write_field(file, 'play_counter', str(counter))

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
      # Commit on file and memory
      self.map_track_info[track]['tags'] = tags
      self.write_field(track, 'tags', tags)
      # Update the taglist
      self.map_tag_tracks[new].append(track)
    # Delete old tag  
    self.map_tag_tracks.pop(old)

  def tag_track(self, track, tag):
    tags = self.map_track_info[track]['tags']
    tags.append(tag)
    self.write_field(track, 'tags', tags)
    self.map_track_info[track]['tags'] = tags
    # Declare new tag if needed
    if not new in self.map_tag_tracks.keys():
      self.map_tag_tracks[tag] = []
    # Append
    self.map_tag_tracks[tag].append(track)

  def untag_track(self, track, tag):
    tags = self.map_track_info[track]['tags']
    tags.remove(tag)
    self.write_field(self, track, 'tags', tags)
    self.map_track_info[track]['tags'] = tags
    # Remove track from tag list
    self.map_tag_tracks[tag].remove(track)
    # Remove tag if empty
    if len(self.map_tag_tracks[tag]) == 0:
      self.map_tag_tracks.pop(tag)

  def write_fields(self, file, dictkeyvalues):
    for key in dictkeyvalues.keys():
      self.write_field(file, key, dictkeyvalues[key])

  def write_field(self, file, field, value):
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
      audio[MAP_FLAC_FIELDS[field]] = value
    audio.save(file)

def UTF8Encode(obj):
  if isinstance(obj, list):
    return [s.encode('utf8') for s in obj]
  else:
    return obj.encode('utf8')
