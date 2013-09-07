import json
import os
import shutil

from dropbox import client, rest, session

class CloudSyncer:

  """ACCESS_TYPE = 'app_folder'
  APP_KEY = '1bdx396ea146xyl'
  APP_SECRET = 'wljhuyq1mtria1y'
  TOKEN_FILE = 'dropbox.json'"""

  #DROPBOX_PATH = '/Users/corradio/Dropbox/Apps/pingweeplayer/'
  DROPBOX_PATH = '/Users/corradio/Music/BTSync_music'

  server = None
  tags_to_sync = ["Hot"]

  def init(self, server):
    self.server = server

    self.sync()

    """client = self.authorize()
    print "linked account:", client.account_info()

    #self.upload(client, '/Users/corradio/Documents/Dev/stringencoder.py')

    #return
    for track in server.library.map_tag_tracks[self.tags_to_sync[0]]:
      self.upload(client, track)

      folder_metadata = client.metadata('/')
      print "metadata:", folder_metadata"""

  """def authorize(self):
    sess = session.DropboxSession(self.APP_KEY, self.APP_SECRET, self.ACCESS_TYPE)

    try:
      f = open(self.TOKEN_FILE, 'r')
      data = json.loads(f.read())
      f.close()
    except IOError:
      request_token = sess.obtain_request_token()
      url = sess.build_authorize_url(request_token)
      print "url:", url
      print "Please authorize in the browser. After you're done, press enter."
      raw_input()
      access_token = sess.obtain_access_token(request_token)
      data = {
        'token_key': access_token.key,
        'token_secret': access_token.secret
      }
      f = open(self.TOKEN_FILE, 'w')
      f.write(json.dumps(data))
      f.close()

    sess.set_token(data['token_key'], data['token_secret'])
    return client.DropboxClient(sess)

  def upload(self, client, filepath):
    BUFFER_SIZE = 1024*1024
    print filepath

    f = open(filepath, 'rb')
    size = os.stat(filepath).st_size # THIS MIGHT BE WRONG
    filename = os.path.basename(filepath)
    uploader = client.get_chunked_uploader(f, size)
    print "uploading: ", size
    while uploader.offset < size:
      #try:
      upload = uploader.upload_chunked(chunk_size=BUFFER_SIZE)
      print "uploaded: ", offset
      #except rest.ErrorResponse, e:
        # perform error handling and retry logic
      #  print e
    uploader.finish('/%s' % filename)
    print "finished"

    f.close()"""

  def sync(self):
    # TODO: Here do a deletion thing

    for tag in self.tags_to_sync:
      for filepath in self.server.library.map_tag_tracks[tag]:
        filename = os.path.basename(filepath)
        dst = '%s/%s' % (self.DROPBOX_PATH, filename)
        if True:
          shutil.copy(filepath, dst)
        #if not os.path.islink(dst):
        #  os.symlink(filepath, dst)
