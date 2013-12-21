# -*- coding: utf-8 -*-
#!/usr/bin/python
import cherrypy
import re
import psycopg2
#import json
import simplejson as json
import os
from os import getcwd
from datetime import datetime,date

from mako.template import Template
from mako.lookup import TemplateLookup
import sys, traceback
sys.stdout = sys.stderr

import atexit
import threading

import site
site.addsitedir('/usr/lib/python2.6/site-packages')
site.addsitedir('/local/home/dotkom/norangsh/sc2ladder')
import sc2ladder
import pretty
import dateutil.parser

os.umask(000)
mylookup = TemplateLookup(directories=['frontend'])

class SC2LadderService():
    _cp_config = {'tools.staticdir.on' : True,
                  'tools.staticdir.dir' : "%s/frontend" % "/local/home/dotkom/norangsh/sc2ladder",
                  'tools.encode.encoding': 'utf8', 
                 }

    def __init__(self):
        self.database = "sc2no"
        self.dbhost = "localhost"
        self.dbuser = "sc2no"
        self.dbpassword = "woopwooppwoop"
        self.base = "/local/home/dotkom/norangsh/sc2ladder"
        #self.bnetregex = re.compile("^http://eu.battle.net/sc2/en/profile/(\d+)/1/([\d\w]+)/")
        self.bnetregex = re.compile("^http://eu.battle.net/sc2/en/profile/(\d+)/1/([^/]*)/")
        self.sc2 = sc2ladder.SC2NO()

    def default(self, country='no', bracket=1, arg3=None,arg4=None, **kwargs):
	try:
            if (country == 'admin'):
              #return self.admin(bracket,arg3,arg4)
              return self.admin(bracket,arg3,arg4,**kwargs)
            elif (country == 'faq'):
              mytemplate = Template(filename="%s/frontend/faq.html" % self.base, input_encoding='utf-8',
        output_encoding='utf-8')
              return mytemplate.render()
            elif (bracket == 'achievements'):
              rows = self.sc2.achievement_ladder(country)
              data = []
              for row in rows:
                (nrank, player, ap) = (row[0], row[1], row[2])
                aPlayer = {
                 'nrank' : nrank,
                 'player' : player,
                 'ap' : ap
                }
                data.append(aPlayer)
               
              mytemplate = Template(filename="%s/frontend/achievement.html" % self.base, input_encoding='utf-8',
        output_encoding='utf-8', default_filters=['decode.utf8'])
              return mytemplate.render(data=data, crawling=os.path.isfile("/tmp/daemon-sc2ladder.pid"))
            elif (country == 'graphs'):
              return self.graphs(bracket,arg3, **kwargs)
            elif (country == 'cup'):
              return self.cup(**kwargs)
            else:
              try:
                bracket = int(bracket)
              except ValueError:
                return None
              if(bracket<1 or bracket>4):
                return None
              
              query = "select \
          array_to_string(array_agg(p.nick), ',') as players, array_to_string(array_agg(p.bnet_id), ',') as playerids, array_to_string(array_agg(tp.fav_race), ',') as fav_race,array_to_string(array_agg(p.last_updated), ',') as last_updated, array_to_string(array_agg(p.cronjob), ',') as cronjob, s2.wins, s2.losses, s2.points, s2.national_rank, s2.region_rank, s2.bracket, s2.teamid, s2.division_id, s2.division_rank, s2.is_random, s2.league, s2.points_adj, s2.world_rank \
      FROM \
      ( \
          SELECT \
              rank() OVER(ORDER BY t.league,t.points desc) AS national_rank, t.bracket,t.division_id, t.division_rank, t.is_random, t.league, t.losses, t.wins, t.points, t.region_rank, t.world_rank, t.teamid, t.points_adj \
          FROM \
          ( \
                    select \
                    distinct on (t.teamid) \
                        t.teamid, t.bracket,t.division_id, t.division_rank, t.is_random, t.league, t.losses, t.wins, t.points, t.region_rank,t.world_rank, t.points_adj  \
                    FROM \
                        team t \
                    ORDER BY \
                         t.teamid \
          ) as t \
          JOIN  \
              teamplayer tp  \
                    ON (t.teamid = tp.teamid AND t.bracket=%i)  \
          JOIN  \
              player p  \
                    ON (tp.playerid = p.playerid)  \
          GROUP BY \
              t.teamid,p.country,t.bracket,t.division_id, t.division_rank, t.is_random, t.league, t.losses, t.wins, t.points, t.region_rank,t.world_rank, t.points_adj  \
          HAVING \
              count(p.country) = %i AND p.country = '%s' \
      ) as s2 \
      JOIN \
          teamplayer tp \
              ON (s2.teamid = tp.teamid) \
      JOIN \
          player p \
              ON (tp.playerid = p.playerid) \
      WHERE \
          s2.teamid in \
          ( \
              select \
                  t.teamid \
              from \
                  team t \
              JOIN \
                  teamplayer tp \
                      ON (t.teamid = tp.teamid AND t.bracket=%i) \
              JOIN \
                  player p \
                      ON (tp.playerid = p.playerid) \
              GROUP BY \
                  t.teamid,p.country \
              HAVING \
                  count(p.country) = %i AND p.country = '%s' \
          ) \
      GROUP by \
          s2.wins, s2.losses, s2.points, s2.national_rank, s2.region_rank,s2.world_rank, s2.bracket, s2.teamid, s2.division_id, s2.division_rank, s2.is_random, s2.league, s2.points_adj \
      ORDER BY \
          national_rank asc" % (bracket, bracket, country , bracket, bracket, country)    

              db_con = psycopg2.connect(database = self.database, host = self.dbhost, user = self.dbuser, password = self.dbpassword)
              cursor = db_con.cursor()
              cursor.execute(query)
              rows = cursor.fetchall()
              cursor.close()
              db_con.close()
              teams = []
              for row in rows:
                #players     | wins | losses | points | national_rank | region_rank | bracket | teamid
                (players, playerids, favteams, last_updated, cronjob, wins, losses, points, nrank, eurank, bracket, teamid, divisionid, divisionrank, israndom, league, pointsadj, wrank) = (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17])
                #lu = [datetime.strptime(x.split(".")[0] , '%Y-%m-%d %H:%M:%S') for x in last_updated.split(",")]
                lu = [dateutil.parser.parse("%s %s" % (x.split(".")[0], "Z")) for x in last_updated.split(",")]
                cronjoblu = [dateutil.parser.parse("%s %s" % (x.split(".")[0], " CEST")) for x in cronjob.split(",")]
                #print lu
                if not pointsadj:
                  pointsadj = 0
                if not points:
                  points = 0
                newest = datetime(1970,1,1,tzinfo=dateutil.tz.tzutc())
                for y in lu:
                  if y > newest:
                    newest = y
                newestcj = datetime(1970,1,1,tzinfo=dateutil.tz.gettz("Europe/Oslo"))
                for y in cronjoblu:
                  if y > newestcj:
                    newestcj = y
                #print lu
                #test =  zip([pretty.date(datetime.strptime(x.split(".")[0], '%Y-%m-%d %H:%M:%S')) for x in lu], [pretty.date(datetime.strptime(y.split(".")[0], '%Y-%m-%d %H:%M:%S')) for y in cronjob.split(",")])
                #print test
                aTeam = {
                 'teamid' : teamid,
                 'bracket' : bracket,
                 'nrank' : nrank,
                 'eurank' : eurank,
                 'worldrank' : wrank,
                 'points' : points,
                 'wins' : wins,
                 'losses' : losses,
                 'divisionid' : divisionid,
                 'divisionrank' : divisionrank,
                 'israndom' : israndom,
                 'league' : self.sc2.league_from_int(league),
                 'players' : zip(players.split(","),playerids.split(","), favteams.split(",")),
                 'lastupdated' : zip(lu, cronjoblu),
                 'cronjoblastupdated' : pretty.date(newestcj),
                 'humanlastupdated' : pretty.date(newest.astimezone(dateutil.tz.gettz("Europe/Oslo"))),
                 'helper' : len(lu),
                 'historypoints' : points-pointsadj,
                 'pointsadj' : pointsadj
                 }
                #'humanlastupdated' : zip([pretty.date(datetime.strptime(x.split(".")[0], '%Y-%m-%d %H:%M:%S')) for x in lu], [pretty.date(datetime.strptime(y.split(".")[0], '%Y-%m-%d %H:%M:%S')) for y in cronjob.split(",")]),
                teams.append(aTeam)
              #print teams
              mytemplate = Template(filename="%s/frontend/index.html" % self.base, input_encoding='UTF-8', output_encoding='UTF-8', default_filters=['decode.utf8'])
              return mytemplate.render(data=teams, bracket=bracket, crawling=os.path.isfile("/tmp/daemon-sc2ladder.pid"))
              #return json.dumps({"teams" : teams})
        except Exception,e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.sc2.log("[%s] Broken: %s \n  %s" % (datetime.now(), e, repr(traceback.extract_tb(exc_traceback))))
            mytemplate = Template(filename="%s/frontend/broken.html" % self.base, input_encoding='utf-8', output_encoding='utf-8')
            return mytemplate.render()

    def graphs(self, country="no", bracket=1, **kwargs):
      query = "SELECT \
  history.teamid, \
  array_agg(history.points) as points, \
  array_agg(history.delta) as delta \
FROM \
  public.history, \
  public.player, \
  public.teamplayer, \
  public.team \
WHERE \
  teamplayer.teamid = team.teamid AND \
  teamplayer.playerid = player.playerid AND \
  teamplayer.teamid = history.teamid AND history.teamid IN \
  ( \
     SELECT \
           t.teamid \
      FROM \
      ( \
                select \
                distinct on (t.teamid) \
                    t.teamid, t.bracket,t.division_id, t.division_rank, t.is_random, t.league, t.losses, t.wins, t.points, t.region_rank, h.points as historypoints \
                FROM \
                    team t \
                LEFT JOIN \
                    history h \
                ON \
                    (t.teamid = h.teamid) \
                ORDER BY \
                     t.teamid, delta desc \
      ) as t \
      ORDER BY rank() OVER(ORDER BY t.league,t.points desc) \
      limit 10 \
  ) \
\
GROUP BY \
  history.teamid" 
      data = self.sc2.graph_top10(bracket, country)
      mytemplate = Template(filename="%s/frontend/graphs-top.html" % self.base, input_encoding='utf-8',
    output_encoding='utf-8')
      return mytemplate.render(data=data, bracket=bracket, country=country)

    def cup(self, nick=None, uc=None,status=None, **kwargs):
        request = cherrypy.serving.request
        if (request.method == 'POST'):
          nick = nick.strip()
          uc = uc.strip()

          if (nick and uc):
            result = self.sc2.cup(nick,uc)
            if (result):
              raise cherrypy.HTTPRedirect("/cup/?status=Saved %s.%s : %s" % (nick,uc,result))
            else:
              raise cherrypy.HTTPRedirect("/cup/?status=Fail, try again")
          else:
            raise cherrypy.HTTPRedirect("/cup/?status=%s" % "Mangler enten nick eller character code...")
              
        else:
          mytemplate = Template(filename="%s/frontend/cup.html" % self.base, input_encoding='utf-8',
    output_encoding='utf-8')
          data = self.sc2.cupshow()
          if status:
            return mytemplate.render(data=data,status=status)
          else:
            return mytemplate.render(data=data)
        return "woops"
        

    def admin(self, mode="main", module=None, csv=None, blizzardurl=None, remote=None,status=None, **kwargs):
        request = cherrypy.serving.request
	'''raise cherrypy.HTTPRedirect("http://sc2.no", 307)'''
        if (request.method == 'POST'):
          blizzardurl = blizzardurl.strip()
          #print "post data: %s" % blizzardurl
          match = self.bnetregex.search(blizzardurl)
          if match:
            (bnetid, nick) = match.groups()
            if bnetid and nick:
              result = self.sc2.add(nick.decode('utf8'),bnetid,"no")
              raise cherrypy.HTTPRedirect("/admin/add/player/?status=Saved %s,%s : %s" % (bnetid,nick,result))
          else:
            raise cherrypy.HTTPRedirect("/admin/add/player/?status=%s" % "Not matching eu.battle.net url...")
        else:
          if (mode=="add" and module=="player" and remote):
            (bnet,nick) = remote.split(",")
            self.sc2.log("[%s] WEB : SC2.NO : Adding %s (%s)" % (datetime.now(),nick,bnet))
            result = self.sc2.add(nick,bnet,"no")
            return "%s" % result
              
          elif (mode=="add" and module=="player"):
            mytemplate = Template(filename="%s/frontend/admin/player/add.html" % self.base, input_encoding='utf-8',
    output_encoding='utf-8')
            if status:
              return mytemplate.render(data=csv,status=status)
            else:
              return mytemplate.render(data=csv)
          return "woops"

    

    def json_lookup(self, bracket = 2):
        query = "select p.nick,s1.wins,s1.losses,s1.points,s1.national_rank,s1.region_rank,s1.bracket,s1.teamid from (select rank() OVER(ORDER BY t.region_rank asc) AS national_rank,t.bracket,t.teamid,t.wins,t.losses,t.points,t.region_rank FROM team t WHERE t.bracket=2) as s1 join teamplayer tp ON (s1.teamid = tp.teamid) JOIN player p ON (tp.playerid = p.playerid) ORDER BY national_rank asc" 
        db_con = psycopg2.connect(database = self.database, host = self.dbhost, user = self.dbuser, password = self.dbpassword)
        cursor = db_con.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        db_con.close()
        result = []
        counter=0
        teams = []
        players = []
        for row in rows:
          (nick, wins, losses, points, nrank, eurank, bracket, team) = (row[0], row[1], row[2] , row[3], row[4], row[5], row[6], row[7])
          players.append({"player" : nick})
          if (counter % 2 != 0):
            teams.append({"team" : team, "bracket" : bracket, "nrank" : nrank, "eurank" : eurank, "points" : points, "wins" : wins, "losses" : losses, "players" : players})
            players = []
          counter = counter + 1
        return json.dumps({"teams" : teams})
       

    @cherrypy.expose
    def languages(self):
        languages = ("NO-UK", "UK-NO", "NO-NO", "UK-UK", "NO-DE", "DE-NO", "UK-SE", "SE-UK", "UK-FR", "FR-UK", "UK-ES", "ES-UK", "NO-ME")
        result = []
        for language in languages:
            result.append({"language" : language})
        return json.dumps({"languages" : result})

    default.exposed = True
    admin.exposed = True
    graphs.exposed = True
    #languages._cp_config = {'tools.staticdir.on': False}
    #languages.exposed = True


cherrypy.config.update({'environment': 'embedded', 'log.error_file': '/local/home/dotkom/norangsh/sc2ladder/site.log'})
'''
if cherrypy.version.startswith('3.0') and cherrypy.engine.state == 0:
    cherrypy.engine.start(blocking=False)
    atexit.register(cherrypy.engine.stop)
'''

application = cherrypy.Application(SC2LadderService(),None)

'''
cherrypy.config.update({'server.socket_host': '0.0.0.0',
                        'server.socket_port': 8081,})
cherrypy.quickstart(Dict())
'''
