#!/usr/bin/env python
 
import sys, time
import sc2ladder
import os
from daemon import Daemon

os.umask(000)

class MyDaemon(Daemon):
	sc2 = sc2ladder.SC2NO()
        def run(self):
                while True:
			self.sc2.cronjob()
                        time.sleep(300)
 
if __name__ == "__main__":
        daemon = MyDaemon('/tmp/daemon-sc2ladder.pid')
        if len(sys.argv) == 2:
                if 'start' == sys.argv[1]:
                        daemon.start()
                elif 'stop' == sys.argv[1]:
                        daemon.stop()
                elif 'restart' == sys.argv[1]:
                        daemon.restart()
                else:
                        print "Unknown command"
                        sys.exit(2)
                sys.exit(0)
        else:
                print "usage: %s start|stop|restart" % sys.argv[0]
                sys.exit(2)
