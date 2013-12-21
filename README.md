ladder.sc2.no
=============

This is the original source code that was used as a ladder for sc2.no back in the early days of the release of SC2. 

The fun part of this project is the main SQL query running at https://github.com/norrs/ladder.sc2.no/blob/master/backend.py#L82 which does the main functionality for the ladder :') 

NB: do not run this code in production, the crawler requires some modifications to not drain down sc2ranks resources. Running this crawler will likley get you banned.

We (sc2.no admins in 2010) never got the ban lifted, hence I abondened the project even tho we fixed the errors and tried to get feedback from the admins at sc2ranks for why we got banned. 

Yawn. 

Lession from this project; don't code it like this :') harr harr. 

Archives
========

It looked like this:

http://sc2ladder.norrs.no/
http://web.archive.org/web/20100831110001/http://ladder.sc2.no/


And the site is horrible slow, the SQL query should really have been memcached ;) 
