#!/usr/bin/env python
 
import sys, time
import sc2ladder
import os
from daemon import Daemon

os.umask(000)

class Service():
	sc2 = sc2ladder.SC2NO()
	while True:
		sc2.cronjob()
		time.sleep(300)
 
if __name__ == "__main__":
	Service()
	print "Starting sc2ladder service"
