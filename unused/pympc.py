import mpd
mpc = mpd.MPDClient()
mpc.connect('localhost', 6600)
print 'mpc is available'