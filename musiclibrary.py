#!/usr/bin/python

import os
import sys
import urllib2
from bottle import route, run, template, request, static_file
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
  'last_played': 'last_played',
  'play_counter': 'play_counter',
  'replaygain_track_gain': 'replaygain_track_gain',
  'replaygain_album_gain': 'replaygain_album_gain',
  'bpm': 'bpm',
  'lyrics': 'lyrics',
}

FIELDS_TO_LOAD_AT_SCAN = [
  'tags',
  'album',
  'artist',
  'title',
  'date',
  'tracknumber',
  'play_counter',
  'bpm',
]

MULTILINE_FIELDS = [
  'tags',
]

def get_track_info(file):
  filename, extension = os.path.splitext(file)
  info = {}
  if extension.upper() == '.MP3':
    audio = ID3(file)
    for field in FIELDS_TO_LOAD_AT_SCAN:
      if MAP_ID3_FIELDS[field] in audio.keys():
        data = UTF8Encode(audio[MAP_ID3_FIELDS[field]].text)
        if field not in MULTILINE_FIELDS and isinstance(field, list):
          info[field] = ';'.join(data)
        else:
          info[field] = data
  elif extension.upper() == '.FLAC':
    audio = FLAC(file)
    for field in FIELDS_TO_LOAD_AT_SCAN:
      if MAP_FLAC_FIELDS[field] in audio.keys():
        data = UTF8Encode(audio[MAP_FLAC_FIELDS[field]])
        if field not in MULTILINE_FIELDS and isinstance(field, list):
          info[field] = ';'.join(data)
        else:
          info[field] = data
  return info

def write_tags(file, tags):
  filename, extension = os.path.splitext(file)
  if extension.upper() == '.MP3':
    # Try to open the ID3 tags
    try:
      audio = ID3(file)
    except mutagen.id3.ID3NoHeaderError:
      # Save a blank ID3 header first
      audio = ID3()
      audio.save(file)
    audio['TXXX:TAG'] = TXXX(encoding=3, desc=u'TAG', text=tags)
    audio.save()
  elif extension.upper() == '.FLAC':
    audio = FLAC(file)
    audio['tag'] = tags

def print_fields(file):
  audio = ID3(file)
  print audio.keys()

def HTMLDecode(s):
  return urllib2.unquote(urllib2.quote(s.encode("utf8")))

LIBRAIRIES = ["/Users/corradio/Music/iTunes/iTunes Media/",
              "/Users/corradio/Music/Logic"
              "/Users/corradio/Downloads"]
MPD_ROOT = "/Users/corradio/Music/"
EXTENSIONS = ['.MP3', '.FLAC'] # take care of WAV!
MAP_TAG_TRACKS = {}
MAP_TRACK_INFO = {}

def UTF8Encode(obj):
  if isinstance(obj, list):
    return [s.encode('utf8') for s in obj]
  else:
    return obj.encode('uft8')

def scan_library():
  global MAP_TAG_TRACKS, MAP_TRACK_INFO
  MAP_TAG_TRACKS = {}
  MAP_TRACK_INFO = {}
  for library in LIBRAIRIES:
    for dirname, dirnames, filenames in os.walk(library):
      #for subdirname in dirnames:
      #  print os.path.join(dirname, subdirname)
      for filename in filenames:
        unused, ext = os.path.splitext(filename)
        if ext.upper() in EXTENSIONS:
          try:
            file = os.path.join(dirname, filename)
            MAP_TRACK_INFO[file] = get_track_info(file)
            if 'tags' in MAP_TRACK_INFO[file].keys():
              tags = MAP_TRACK_INFO[file]['tags']
              for tag in tags:
                if tag in MAP_TAG_TRACKS.keys():
                  MAP_TAG_TRACKS[tag] += [file]
                else:
                  MAP_TAG_TRACKS[tag] = [file]
          except Exception,e: print str(e)

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

  run(host='0.0.0.0', port=8080, reloader=True)

  os.system('mpd --kill')

if __name__ == "__main__":
    main()

# IDEA: Start mpd, add symlink to library, then we have everything. Just remember to lock mpd to 127.0.0.1
# IDEA: Use Node.js for playing music and receiving messages, and this for handling the library (like a db system)?
