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