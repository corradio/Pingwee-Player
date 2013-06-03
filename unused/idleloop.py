import mpd
import select

if __name__ == "__main__":
  mpc = mpd.MPDClient()
  mpc.connect("localhost", 6600)
  while True:
    mpc.send_idle()
    select.select([mpc], [], [])
    response = mpc.fetch_idle()
    print 'R: %s' % response
    #for client in clients:
    #  client.write_message(response)
