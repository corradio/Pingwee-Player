#!/usr/bin/python

# TODO: Move all HTTP handler files to a new file

import json
import os
import sys
import time
import urllib2
import mutagen.id3
from bottle import route, run, template, request, static_file
from datetime import datetime, timedelta
from mutagen.id3 import ID3, TXXX, ID3NoHeaderError
from mutagen.flac import FLAC
#from threading import Thread

MAP_ID3_FIELDS = {
  'tags': 'TXXX:TAG',
  'album': 'TALB',
  'artist': 'TPE1',
  'title': 'TIT2',
  'date': 'TDRC',
  'tracknumber': 'TRCK',
  'first_played': 'TXXX:FIRST_PLAYED',
  'first_added': 'TXXX:FIRST_ADDED',
  'last_played': 'TXXX:LAST_PLAYED',
  'play_counter': 'TXXX:LAST_PLAYED',
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

MPD_ROOT = "/Users/corradio/Music/"

EXTENSIONS = ['.MP3', '.FLAC'] # take care of WAV!?

# Globals
MAP_TAG_TRACKS = {}
MAP_TRACK_INFO = {}

def get_track_info(file):
  filename, extension = os.path.splitext(file)
  info = {}

  try:
    if extension.upper() == '.MP3':
      audio = ID3(file)
      MAP_FIELDS = MAP_ID3_FIELDS
    elif extension.upper() == '.FLAC':
      audio = FLAC(file)
      MAP_FIELDS = MAP_FLAC_FIELDS

    for field in MAP_FIELDS.keys():
      if MAP_FIELDS[field] in audio.keys():
        if extension.upper() == '.MP3':
          data = UTF8Encode(audio[MAP_FIELDS[field]].text)
        elif extension.upper() == '.FLAC':
          data = UTF8Encode(audio[MAP_FIELDS[field]])
        if field not in MULTILINE_FIELDS:
          info[field] = ';'.join(data)
        else:
          if not isinstance(data, list):
            data = [data]
          info[field] = data
  except mutagen.id3.ID3NoHeaderError:
    print 'Warning: No ID3 header found in file %s' % file
  return info

def write_tags(file, dictkeyvalues):
  for key in dictkeyvalues.keys():
    write_tag(file, key, dictkeyvalues[key])

def write_tag(file, field, value):
  filename, extension = os.path.splitext(file)
  if extension.upper() == '.MP3':
    # Try to open the ID3 tags
    try:
      audio = ID3(file)
    except mutagen.id3.ID3NoHeaderError:
      # Save a blank ID3 header first
      audio = ID3()
    id3field = MAP_ID3_FIELDS[field]
    fieldtype, unused, fieldname = id3field.partition(':')
    gentag = getattr(mutagen.id3, fieldtype)
    audio[id3field] = gentag(encoding=3, desc=u'%s' % fieldname, text=value)
    #audio['TXXX:TAG'] = TXXX(encoding=3, desc=u'TAG', text=tags)
  elif extension.upper() == '.FLAC':
    audio = FLAC(file)
    audio[MAP_FLAC_FIELDS[field]] = value
  audio.save(file)

def print_fields(file):
  audio = ID3(file)
  print audio.keys()

def HTMLDecode(s):
  return urllib2.unquote(urllib2.quote(s.encode("utf8")))

def UTF8Encode(obj):
  if isinstance(obj, list):
    return [s.encode('utf8') for s in obj]
  else:
    return obj.encode('utf8')

def scan_library():
  global MAP_TAG_TRACKS, MAP_TRACK_INFO
  MAP_TAG_TRACKS = {'!RecentlyAdded': [], '!Untagged': []}
  MAP_TRACK_INFO = {}

  print 'Sending update request to mpd'
  os.system('mpc update')

  print 'Library scan started'
  for library in LIBRAIRIES:
    for dirname, dirnames, filenames in os.walk(library):
      for filename in filenames:
        unused, ext = os.path.splitext(filename)
        if ext.upper() in EXTENSIONS:
          try:
            file = os.path.join(dirname, filename)
            MAP_TRACK_INFO[file] = get_track_info(file)
            if 'tags' in MAP_TRACK_INFO[file].keys():
              tags = MAP_TRACK_INFO[file]['tags']
              if len(tags) == 0:
                MAP_TAG_TRACKS['!Untagged'] += [file]
              for tag in tags:
                if tag in MAP_TAG_TRACKS.keys():
                  MAP_TAG_TRACKS[tag] += [file]
                else:
                  MAP_TAG_TRACKS[tag] = [file]
            else:
              MAP_TAG_TRACKS['!Untagged'] += [file]

            # Special tags
            if 'first_added' in MAP_TRACK_INFO[file].keys():
              if (datetime.now() - datetime.strptime(MAP_TRACK_INFO[file]['first_added'], DATETIME_TAG_FORMAT)).days <= 30:
                MAP_TAG_TRACKS['!RecentlyAdded'] += [file]
            else:
              print 'Welcome %s to the library!' % file
              write_tag('first_added', datetime.datetime.now().strftime(DATETIME_TAG_FORMAT))
          except Exception as e:
            print str(e)

  print 'Library scan finished'
  data = json.dumps({'MAP_TAG_TRACKS': MAP_TAG_TRACKS, 'MAP_TRACK_INFO': MAP_TRACK_INFO})
  f = open(DATABASE_FILENAME, 'w')
  f.write(data)
  f.close()
  print 'Database saved'

@route('/list_tags')
def list_tags():
  return {'Tags':sorted(MAP_TAG_TRACKS.keys())}

@route('/list_tracks')
def list_tracks(tag=None):
  tag = HTMLDecode(request.query['tag'])
  tracks = MAP_TAG_TRACKS[tag]
  return {
    'Tag': tag,
    'Tracks': MAP_TAG_TRACKS[tag],
    'TrackInfos': [MAP_TRACK_INFO[track] for track in tracks]
  }

@route('/play')
def play():
  track = HTMLDecode(request.query['track'])
  os.system('mpc clear')
  print 'mpc add "%s"' % track.replace(MPD_ROOT, '')
  os.system('mpc add "%s"' % track.replace(MPD_ROOT, ''))
  os.system('mpc play')

@route('/enqueue')
def enqueue(track=None):
  track = HTMLDecode(request.query['track'])
  os.system('mpc add "%s"' % track.replace(MPD_ROOT, ''))

@route('/rescan_library')
def rescan_library():
  scan_library()
  #thread = Thread(target=scan_library, args=())
  #thread.start()

#@route('/edit')
#def edit():
#  track = HTMLDecode(request.query['track'])
#  write_tags(tracks, tags)

@route('/stop')
def stop():
  os.system('mpc stop')

@route('/')
def index():
  return static_file('musiclibrary.html', root='static')

@route('/static/:filepath')
def server_static(filepath):
  return static_file(filepath, root='static')

#@route('/list_tags/:name')
#def index(name='World'):
#    return template('<b>Hello {{name}}</b>!', name=name)

def main():
  os.system('mpd')
  os.system('mpc crossfade 2')
  os.system('mpc replaygain track')

  # Load json data
  global MAP_TAG_TRACKS, MAP_TRACK_INFO
  f = open(DATABASE_FILENAME, 'r')
  data = json.loads(f.read())
  f.close()
  MAP_TAG_TRACKS = data['MAP_TAG_TRACKS']
  MAP_TRACK_INFO = data['MAP_TRACK_INFO']
  data = None

  run(host='0.0.0.0', port=8080, reloader=True)

  os.system('mpd --kill')

from ctypes import *

class struct_timespec(Structure):
    _fields_ = [('tv_sec', c_long), ('tv_nsec', c_long)]

class struct_stat64(Structure):
    _fields_ = [
        ('st_dev', c_int32),
        ('st_mode', c_uint16),
        ('st_nlink', c_uint16),
        ('st_ino', c_uint64),
        ('st_uid', c_uint32),
        ('st_gid', c_uint32), 
        ('st_rdev', c_int32),
        ('st_atimespec', struct_timespec),
        ('st_mtimespec', struct_timespec),
        ('st_ctimespec', struct_timespec),
        ('st_birthtimespec', struct_timespec),
        ('dont_care', c_uint64 * 8)
    ]

libc = CDLL('libc.dylib')
stat64 = libc.stat64
stat64.argtypes = [c_char_p, POINTER(struct_stat64)]

def get_creation_time(path):
    buf = struct_stat64()
    rv = stat64(path, pointer(buf))
    if rv != 0:
        raise OSError("Couldn't stat file %r" % path)
    return buf.st_birthtimespec.tv_sec

import subprocess

def get_creation_time(path):
    p = subprocess.Popen(['stat', '-f%B', path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.wait():
        raise OSError(p.stderr.read().rstrip())
    else:
        return int(p.stdout.read())

def fixdatetime():
  for library in LIBRAIRIES:
    for dirname, dirnames, filenames in os.walk(library):
      for filename in filenames:
        unused, ext = os.path.splitext(filename)
        if ext.upper() in EXTENSIONS:
          file = os.path.join(dirname, filename)
          #try:
          info = get_track_info(file)
          if 'first_added' in info.keys():
            continue
          first_played = None
          if 'first_played' in info.keys():
            first_played = datetime.strptime(info['first_played'], DATETIME_TAG_FORMAT)
          created = datetime.fromtimestamp(get_creation_time(file))

          first_added = None
          if first_played:
            if (created - first_played).days > 0:
              first_added = first_played
            else:
              first_added = created
          else:
            first_added = created


          print 'Writing %s' % file
          write_tag(file, 'first_added', first_added.strftime(DATETIME_TAG_FORMAT))
          #except Exception as e:
          #  print str(e)

if __name__ == "__main__":
    main()

# IDEA: Start mpd, add symlink to library, then we have everything. Just remember to lock mpd to 127.0.0.1
# IDEA: Use Node.js for playing music and receiving messages, and this for handling the library (like a db system)?
