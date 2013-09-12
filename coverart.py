#!/usr/bin/python
"""EXPERIMENTAL: Auto-fetching covers from the web"""

import base64
import urllib2

def getimageurl(query):
  url = 'https://www.google.com/search?q=%s&start=0&filter=1&biw=1599&bih=1079&sei=ZYLWUdXfLo3y0gXdu4GIAg&tbm=isch' % query.replace(' ', '+')
  #url = 'http://http://www.junodownload.com/search/?q%5Ball%5D%5B%5D=' % query.replace(' ', '+')
  opener = urllib2.build_opener()
  opener.addheaders = [('User-agent', 'Mozilla/5.0')]
  f = opener.open(url)
  htmldata = f.read()
  f.close()

  # Store it in file
  #f = open('coverart_queryresult.html', 'w')
  #try:
  #  f.write(htmldata)
  #finally:
  #  f.close()

  """buf = ''
  isRecording = False
  found = False
  results = []

  imageurl = ''
  isScanningForURL = False
  for char in htmldata:
    if char == '<':
      isRecording = True
    # Record
    if isRecording:
      buf += char
      # Process
      if buf == '<div id="product_list_controller_container_top">':
        found = True
        isScanningForURL = False
        imageurl = ''
      elif found and buf = '<div id="item-"'
        isScanningForURL = True
      elif buf[-1] == " " and not getlastbufchars(buf, 3) == "<a " and not found:
        isRecording = False
      elif getlastbufchars(buf, 2) == "</" and not found:
        isRecording = False
      elif char == ">" and not found:
        isRecording = False
      elif char == ">" and found:
        if getlastbufchars(buf, 4) == "</a>":
          results.append(buf)
          isRecording = False
          found = False
      elif isScanningForURL:
        imageurl += buf[-1]
        if getlastbufchars(buf, 1) == '"':
          isScanningForURL = False
          # FOUND
          tmp = imageurl.split('-')
          return "http://images.junostatic.com/full/CS%s-%02dA-BIG.jpg" % (tmp[0], int(tmp[1]))"""

  
  buf = ''
  isRecording = False
  found = False
  results = []

  imageurl = ''
  isScanningForURL = False
  for char in htmldata:
    if char == '<':
      isRecording = True
      if not found:
        buf = ''
    # Record
    if isRecording:
      buf += char
      # Process
      if buf == '<a href="http://www.google.com/imgres?imgurl=':
        found = True
        isScanningForURL = True
        imageurl = ''
      elif buf[-1] == " " and not getlastbufchars(buf, 3) == "<a " and not found:
        isRecording = False
      elif getlastbufchars(buf, 2) == "</" and not found:
        isRecording = False
      elif char == ">" and not found:
        isRecording = False
      elif char == ">" and found:
        if getlastbufchars(buf, 4) == "</a>":
          results.append(buf)
          isRecording = False
          found = False
      elif isScanningForURL:
        imageurl += buf[-1]
        if getlastbufchars(buf, 4) in ['.jpg', '.png'] or getlastbufchars(buf, 4) in ['.jpeg']:
          isScanningForURL = False
          results.append(imageurl)

  return results[0]

def getbase64image(query):
  url = getimageurl(query)
  opener = urllib2.build_opener()
  opener.addheaders = [('User-agent', 'Mozilla/5.0')]
  f = opener.open(url)
  data = f.read()
  f.close()
  return base64.b64encode(data)

def getlastbufchars(string, length):
  return string[len(string)-length:len(string)]

def main():
  query = 'Gareth Emery Meet her in Miami'
  print getimageurl(query)  


if __name__ == "__main__":
  main()