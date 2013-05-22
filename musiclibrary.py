#!/usr/bin/python

import os
import sys
import urllib2
from bottle import route, run, template, request, static_file
from mutagen.id3 import ID3, TXXX, ID3NoHeaderError
from mutagen.flac import FLAC

def get_tags(file):
  filename, extension = os.path.splitext(file)
  if extension.upper() == '.MP3':
    audio = ID3(file)
    if 'TXXX:TAG' in audio.keys():
      return audio['TXXX:TAG'].text
    else:
      return []
  elif extension.upper() == '.FLAC':
    audio = FLAC(file)
    if 'tag' in audio.keys():
      return audio['tag']
    else:
      return []

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

LIBRAIRIES = ["/Users/corradio/Music/iTunes/iTunes Media/Dance"]
MPD_ROOT = "/Users/corradio/Music/"
EXTENSIONS = ['.MP3', '.FLAC'] # take care of WAV!
MAP_TAG_TRACKS = {}
MAP_TRACK_INFO = {}

def scan_library():
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
            tags = get_tags(file)
            MAP_TRACK_INFO[file] = {'Tags':tags,
                                    'Artist':'',
                                    'Title':''}
            for tag in tags:
              if tag in MAP_TAG_TRACKS.keys():
                MAP_TAG_TRACKS[tag] += [file]
              else:
                MAP_TAG_TRACKS[tag] = [file]
          except Exception as e:
            print e
  return MAP_TAG_TRACKS, MAP_TRACK_INFO

@route('/list_tags')
def list_tags():
  return {'Tags':MAP_TAG_TRACKS.keys()}

@route('/list_tracks')
def list_tracks(tag=None):
  tag = HTMLDecode(request.query['tag'])
  return {'Tag':tag, 'Tracks':MAP_TAG_TRACKS[tag]}

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

  global MAP_TAG_TRACKS, MAP_TRACK_INFO
  MAP_TAG_TRACKS, MAP_TRACK_INFO = scan_library()

  run(host='0.0.0.0', port=8080, reloader=True)

  os.system('mpd --kill')

if __name__ == "__main__":
    main()

# IDEA: Start mpd, add symlink to library, then we have everything. Just remember to lock mpd to 127.0.0.1
# IDEA: Use Node.js for playing music and receiving messages, and this for handling the library (like a db system)?
