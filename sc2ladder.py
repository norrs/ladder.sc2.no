#!/usr/bin/python

import simplejson
import httplib2
import psycopg2
import time
import os
import codecs
from datetime import datetime,date
from pprint import pprint
from urllib import FancyURLopener
from psycopg2 import IntegrityError
SEARCH_BASE = 'http://sc2ranks.com/api/char/eu/'

os.umask(000)

class SC2RanksError(Exception):
  pass

class SC2NOError(Exception):
  pass

class SC2NO:

  def __init__(self):
    self.database = "sc2no"
    self.dbhost = "localhost"
    self.dbuser = "sc2no"
    self.dbpassword = "abba2006"

    self.api = "http://sc2ranks.com/api/char/teams/eu/"
    self.nick = None
   
    self.hc = httplib2.Http("/local/home/dotkom/norangsh/sc2ladder/.cache")
    self.hcheaders = "sc2.no/%s (StarCraft Norway)" % self.version
    self.version = "0.2"

  def crawl(self, url):
    try:
      (response, content) = self.hc.request(url, headers={"User-agent":self.hcheaders})
    except Exception,e:
      self.log(e)
      sys.exit(0)
    return (int(response['status']), content)

  def search_uc(self ,username, charactercode, team):
    #url = SEARCH_BASE + '?' + urllib.urlencode(kwargs)
    url = self.api + "%s$%s/%s/0.json?appKey=ladder.sc2.no" % (username.decode('utf8'), charactercode, team)
    self.log("[%s] search_uc : url : %s" % (datetime.now(), url))
    self.nick = username
    (status, content) = self.crawl(url)
    if (status==200):
      result = simplejson.loads(content.decode('utf-8'))
      if 'error' in result:
        # An error occured; raise an exception
        self.log("[%s] search_bnet : Error trying fetching %s (%s) : %s" % (datetime.now(), username, bnet, result['error']))
        return None
        #raise SC2RanksError, result['error']
    elif (status==304):
      self.log("[%s] search_bnet : no new data %s (%s)" % (datetime.now(), username,bnet))
      self.update_cronjob(username,bnet)
      return None
    else:
      self.log("[%s] search_bnet : error crawling : %s -> %s (%s)" % (datetime.now(), status, username, bnet))
      self.update_cronjob(username,bnet)
      return None
    return result

  def search_bnet(self, username, bnet, team):
    #url = SEARCH_BASE + '?' + urllib.urlencode(kwargs)
    url = self.api + "%s!%s/%s/0.json?appKey=ladder.sc2.no" % (username, bnet, team)
    self.log("[%s] search_bnet : url : %s" % (datetime.now(), url))
    self.nick = username
    (status, content) = self.crawl(url)
    if (status==200):
      result = simplejson.loads(content.decode('utf-8'))
      if 'error' in result:
        # An error occured; raise an exception
        self.log("[%s] search_bnet : Error trying fetching %s (%s) : %s" % (datetime.now(), username, bnet, result['error']))
        return None
        #raise SC2RanksError, result['error']
    elif (status==304):
      self.log("[%s] search_bnet : no new data %s (%s)" % (datetime.now(), username,bnet))
      self.update_cronjob(username,bnet)
      return None
    else:
      self.log("[%s] search_bnet : error crawling : %s -> %s (%s)" % (datetime.now(), status, username, bnet))
      self.update_cronjob(username,bnet)
      return None
    return result


  def is_player_added_uc(self, username, charactercode ):
    db_con = psycopg2.connect(database = self.database, host = self.dbhost, user = self.dbuser, password = self.dbpassword)
    cursor = db_con.cursor()

    if (username and charactercode):
      query = "SELECT bnet_id,nick FROM player WHERE nick = '%s' AND character_code = %s" % (username, charactercode)
      cursor.execute(query)
      result = cursor.fetchone()
      cursor.close()
      db_con.close()
      if result:
        return (result[0],result[1])
      return (None,None)
        
  
  def is_player_added_bnet(self,bnet_id):
    db_con = psycopg2.connect(database = self.database, host = self.dbhost, user = self.dbuser, password = self.dbpassword)
    cursor = db_con.cursor()
    query = "SELECT bnet_id,nick FROM player WHERE bnet_id = %i" % bnet_id
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    db_con.close()
    if result:
      return (result[0],result[1])
    return (None,None)

  def add_player(self, bnet_id, username, charactercode, playerid, last_updated, scanned, country=None, ap=None):
    try:
      db_con = psycopg2.connect(database = self.database, host = self.dbhost, user = self.dbuser, password = self.dbpassword)
      cursor = db_con.cursor()
      if not charactercode:
        charactercode = 0
      if not ap:
        ap = 0
      #print bnet_id,username,charactercode,playerid,last_updated
      if (scanned):
        if not country:
          query = "INSERT INTO player (bnet_id, nick, character_code, playerid, last_updated, cronjob, country, ap) VALUES (%i, '%s', %i, %i, '%s', '%s', NULL, %i)" % (bnet_id,username,charactercode,playerid,last_updated, datetime.now(), ap)
        else:
          query = "INSERT INTO player (bnet_id, nick, character_code, playerid, last_updated, cronjob, country, ap) VALUES (%i, '%s', %i, %i, '%s', '%s', '%s', %i)" % (bnet_id,username,charactercode,playerid,last_updated, datetime.now(), country, ap)
      else:
        if not country:
          query = "INSERT INTO player (bnet_id, nick, character_code, playerid, last_updated, cronjob, country, ap) VALUES (%i, '%s', %i, %i, '%s', '%s', NULL, %i)" % (bnet_id,username,charactercode,playerid,last_updated, '1973-01-01 13:37:10', ap)
        else:
          query = "INSERT INTO player (bnet_id, nick, character_code, playerid, last_updated, cronjob, country, ap) VALUES (%i, '%s', %i, %i, '%s', '%s', '%s', %i)" % (bnet_id,username,charactercode,playerid,last_updated, '1973-01-01 13:37:10', country, ap)
      cursor.execute(query)
      db_con.commit()
      cursor.close()
      db_con.close()
      return (bnet_id,username)
    except IntegrityError:
      self.log("[%s] add_player : %s (%s) already exists" % (datetime.now(), username, bnet_id))
      return (None,None)

  def fetch_player_uc(self, username, charactercode, team):
    (bnet_id, nick) = self.is_player_added_uc(username, charactercode)
    if bnet_id and nick:
      return self.parse_sc2ranks_data(self.search_bnet(nick, bnet_id, team))
    else:
      return self.parse_sc2ranks_data(self.search_uc(username, charactercode, team))
  
  def fetch_player_bnet(self, username, bnet, team):
    (bnet_id, nick) = self.is_player_added_bnet(bnet)
    if bnet_id and nick:
      return self.parse_sc2ranks_data(self.search_bnet(nick, bnet_id, team))
    else:
      return self.parse_sc2ranks_data(self.search_bnet(username, bnet, team))

  def update_sc2ranks_ts(self, cursor, playerid, updated_at, teamid=None):
    if not teamid:
      query = "UPDATE player set last_updated = '%s' WHERE playerid = %i" % (updated_at, playerid)
      cursor.execute(query)

  def parse_sc2ranks_data(self, data):
    if data:
      #self.log(data)
      db_con = psycopg2.connect(database = self.database, host = self.dbhost, user = self.dbuser, password = self.dbpassword)
      cursor = db_con.cursor()
  
      (bnet, nick) = self.is_player_added_bnet(data['bnet_id'])
      if bnet and nick:
        if "character_code" in data and data['character_code'] != 'null':
          query = "UPDATE player SET character_code = %i, cronjob = '%s', ap = %i WHERE playerid = %i" % (data['character_code'], datetime.now(), data['achievement_points'], data['id'])
          cursor.execute(query)
        else:
          query = "UPDATE player SET cronjob = '%s', ap = %i WHERE playerid = %i" % (datetime.now(), data['achievement_points'], data['id'])
          cursor.execute(query)
      else:
        if "character_code" in data:
          self.add_player(data['bnet_id'], self.nick, data['character_code'], data['id'], data['updated_at'], True, data['achievement_points'])
        else:
          self.add_player(data['bnet_id'], self.nick, None, data['id'], data['updated_at'], True, data['achievement_points'])
  
      if (len(data['teams'])>0):
        for team in data['teams']:
          if (team['is_random'] == False):
            query = "SELECT points FROM team where teamid = %s" % team['id']
            cursor.execute(query)
            result = cursor.fetchone()
            if result:
              points_h = team['points']-result[0]
            else:
              points_h = 0

            if (self.is_team_added(team['id'])):
              query = "INSERT INTO history (teamid,points,delta) (select teamid,points,now() from team where teamid = %i)" % team['id']
              cursor.execute(query)
              region_rank = 0
              world_rank = 0
              if "region_rank" in team and team['region_rank']:
                region_rank = team['region_rank']
              if "world_rank" in team and team['world_rank']:
                world_rank = team['world_rank']
              self.log("WORLD_RANK: %s" % (world_rank))
              self.log("WORLD_RANK: %s , %s" % (world_rank, team['world_rank']))
              query = "UPDATE team SET bracket = %s, division_id = %s, division_rank = %s, is_random = %s, league = %s, losses = %s, wins = %s, points = %s, region_rank = %s, world_rank = %s, points_adj = %s WHERE teamid = %s" % (
                team['bracket'],
                team['division_id'],  
                team['division_rank'],  
                team['is_random'],  
                self.league_to_int(team['league']),  
                team['losses'],  
                team['wins'],  
                team['points'],  
                region_rank,
                world_rank,
                points_h,
                team['id'] )
              cursor.execute(query)
              if "updated_at" in team and team['updated_at'] != 'null':
                self.log("TEAM UPDATED AT %s" % team['updated_at'])
                self.update_sc2ranks_ts(cursor, data['id'], team['updated_at'])
              if (team['bracket'] != 1):
                for teamplayer in team['members']:
                  (bnet, nick) = self.is_player_added_bnet(teamplayer['bnet_id'])
                  if not bnet or not nick:
                    if 'character_code' in teamplayer and teamplayer['character_code'] != 'null':
                      self.add_player(teamplayer['bnet_id'], teamplayer['name'], teamplayer['character_code'], teamplayer['id'], '1972-01-01', False)
                    else:
                      self.add_player(teamplayer['bnet_id'], teamplayer['name'], 0, teamplayer['id'], '1972-01-01', False)
                  self.update_teamplayer(cursor, team['id'], teamplayer['id'], teamplayer['fav_race'])
              self.update_teamplayer(cursor, team['id'], data['id'], team['fav_race'])
                  
            else:
              region_rank = 0
              world_rank = 0
              if "region_rank" in team and team['region_rank']:
                region_rank = team['region_rank'] 
              if "world_rank" in team and team['world_rank']:
                world_rank = team['world_rank'] 
              self.log("CREATE WORLD_RANK: %s , %s" % (world_rank, team['world_rank']))
              self.log("22")
              query = """INSERT INTO team (teamid, bracket, division_id, division_rank , is_random, league, losses, wins, points, region_rank, world_rank, points_adj) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
              cursor.execute(query,(
                team['id'],
                team['bracket'],
                team['division_id'],  
                team['division_rank'],  
                team['is_random'],  
                self.league_to_int(team['league']),  
                team['losses'],  
                team['wins'],  
                team['points'],  
                region_rank,
                world_rank,
                points_h ))
              if "updated_at" in team and team['updated_at'] != 'null':
                self.update_sc2ranks_ts(cursor, data['id'], team['updated_at'])
              self.log("WTFF2") 
  
              query = "INSERT INTO history (teamid,points,delta) VALUES (%i, %i, now())" % (team['id'], team['points'])
              cursor.execute(query)
              if (team['bracket'] != 1):
                for teamplayer in team['members']:
                  (bnet, nick) = self.is_player_added_bnet(teamplayer['bnet_id'])
                  if not bnet or not nick:
                    if 'character_code' in teamplayer and teamplayer['character_code'] != 'null':
                      self.add_player(teamplayer['bnet_id'], teamplayer['name'], teamplayer['character_code'], teamplayer['id'], '1972-01-01', False)
                    else:
                      self.add_player(teamplayer['bnet_id'], teamplayer['name'], 0, teamplayer['id'], '1972-01-01', False)
                  self.add_teamplayer(cursor, team['id'], teamplayer['id'], teamplayer['fav_race'])
              self.add_teamplayer(cursor, team['id'], data['id'], team['fav_race'])
          else: 
            self.log("[%s] Crawler : %s : Ignoring teamid %i , it is random." % (datetime.now(), self.nick, team['id']))
      else:
        self.log("[%s] No teams here yet.." % datetime.now())
      db_con.commit()
      cursor.close()
      db_con.close()
      self.log("[%s] Crawler : Updated %s (%s) and it's teams" % (datetime.now(),self.nick,data['bnet_id']))
      self.nick = None
      
      return data
  
  def league_to_int(self, league):
    if (league=='diamond'):
      return 1
    elif (league=='platinum'):
      return 2
    elif (league=='gold'):
      return 3
    elif (league=='silver'):
      return 4
    elif (league=='bronze'):
      return 5
    elif (league=='master'):
      return 0
    else:
      return 7

  def league_from_int(self, league):
    if (league==1):
      return 'diamond'
    elif (league==2):
      return 'platinum'
    elif (league==3):
      return 'gold'
    elif (league==4):
      return 'silver'
    elif (league==5):
      return 'bronze'
    elif (league==0):
      return 'master'
    elif (league==6):
      return 'master'
  

  def add_teamplayer(self, cursor, teamid, playerid, favrace):
    if (favrace == 0):
      fav_race = 'zerg'
    elif (favrace == 1):
      fav_race = 'protoss'
    elif (favrace == 2):
      fav_race = 'terran'
    elif (favrace == 3):
      fav_race = 'random'
    else:
      fav_race = favrace

    query = "INSERT INTO teamplayer (teamid, playerid, fav_race) VALUES (%i,%i,'%s')" % (teamid, playerid, fav_race)
    cursor.execute(query)

  def cup(self,nick,uc):
      db_con = psycopg2.connect(database = self.database, host = self.dbhost, user = self.dbuser, password = self.dbpassword)
      cursor = db_con.cursor()
  
      if (nick and uc):
        uc = int(uc)
        query = "INSERT INTO cup (nick, uc, delta) VALUES ('%s' , %i , current_timestamp)" % (nick,uc)
        cursor.execute(query)
        res = db_con.commit()
        cursor.close()
        db_con.close()
        return True
      return False

  def cupshow(self):
    db_con = psycopg2.connect(database = self.database, host = self.dbhost, user = self.dbuser, password = self.dbpassword)
    cursor = db_con.cursor()
    query = "SELECT * FROM cup ORDER BY delta";
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    db_con.close()
    return result

  def update_teamplayer(self, cursor, teamid, playerid, favrace):
    if (favrace == 0):
      fav_race = 'zerg'
    elif (favrace == 1):
      fav_race = 'protoss'
    elif (favrace == 2):
      fav_race = 'terran'
    elif (favrace == 3):
      fav_race = 'random'
    else:
      fav_race = favrace

    query = "UPDATE teamplayer SET fav_race = '%s' WHERE teamid = %i AND playerid = %i" % (fav_race, teamid, playerid)
    cursor.execute(query)
    
    

  def is_team_added(self, teamid):
    db_con = psycopg2.connect(database = self.database, host = self.dbhost, user = self.dbuser, password = self.dbpassword)
    cursor = db_con.cursor()

    if (teamid):
      query = "SELECT teamid FROM team WHERE teamid = %i" % teamid
      cursor.execute(query)
      result = cursor.fetchone()
      cursor.close()
      db_con.close()
      if result:
        return True
      return False
    
  def cronjob(self):
    db_con = psycopg2.connect(database = self.database, host = self.dbhost, user = self.dbuser, password = self.dbpassword)
    cursor = db_con.cursor()
    query = "select bnet_id,nick,last_updated from player p where current_timestamp-cronjob>interval '6 hours' AND country IS NOT NULL order by cronjob asc limit 50;"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    db_con.close()
    if result:
      for row in result:
        (bnet, nick, last_updated) = (row[0], row[1], row[2])
        self.log("[%s] Polling SC2Ranks for %s, %s (%s)" % (datetime.now(),nick,bnet, last_updated))
        for team in range(1,5):
          self.fetch_player_bnet(nick, bnet, team)
        time.sleep(0.2)
      
  def version(self):
    return self.version

  def log(self,msg):
    fileHandle = codecs.open('/local/home/dotkom/norangsh/sc2ladder/log.txt', 'a', 'utf-8' )
    try:
      fileHandle.write ( "%s\n" % msg.decode('utf-8') ) 
    except UnicodeEncodeError:
      fileHandle.write ( "%s\n" % unicode(msg,'utf-8') )
    fileHandle.close() 
  

  def update_cronjob(self, nick, bnetid):
    db_con = psycopg2.connect(database = self.database, host = self.dbhost, user = self.dbuser, password = self.dbpassword)
    cursor = db_con.cursor()
    query = "UPDATE player SET cronjob='%s' WHERE nick='%s' and bnet_id=%i" % (datetime.now(),nick,bnetid)
    cursor.execute(query)
    db_con.commit()
    cursor.close()
    db_con.close()
    
  def update_country(self, nick,bnetid,country):
    db_con = psycopg2.connect(database = self.database, host = self.dbhost, user = self.dbuser, password = self.dbpassword)
    cursor = db_con.cursor()
    query = "UPDATE player SET country='%s' WHERE nick='%s' and bnet_id=%i" % (country,nick,bnetid)
    cursor.execute(query)
    db_con.commit()
    cursor.close()
    db_con.close()

  def add(self, nick, bnetid, country):
    bnetid = int(bnetid)
    (bnet, n2) = self.is_player_added_bnet(bnetid)
    if bnet and nick:
      self.log("[%s] WEB : ALREADY : Fixing nation to %s (%i) to nation [%s]" % (datetime.now(), n2, bnetid, country))
      self.update_country(n2, bnet, country)
      return True
    self.log("[%s] WEB : NEW : Trying to add %s (%i) to nation [%s]" % (datetime.now(), nick, bnetid, country))
    for team in range(1,5):
      self.fetch_player_bnet(nick, bnetid, team)
    (bnet, nick) = self.is_player_added_bnet(bnetid)
    if bnet and nick:
      self.update_country(nick,bnetid,country)
      return True
    return False

  def achievement_ladder(self, country):
    db_con = psycopg2.connect(database = self.database, host = self.dbhost, user = self.dbuser, password = self.dbpassword)
    cursor = db_con.cursor()
    query = "SELECT rank() OVER(ORDER BY ap desc) AS nrank, nick, ap FROM player WHERE country='%s' ORDER BY ap desc" % country;
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    db_con.close()
    return result
    
  def graph_top10(self, bracket, country):
    db_con = psycopg2.connect(database = self.database, host = self.dbhost, user = self.dbuser, password = self.dbpassword)
    cursor = db_con.cursor()
    bracket = int(bracket)
    #h.teamid, h.points, round(date_part('epoch', h.delta))::integer, array_to_string(array_agg(p.nick),',') \
    query = "SELECT \
 	h.teamid, h.points, date_part('epoch', h.delta::timestamp)*1000, array_to_string(array_agg(p.nick),',') \
 FROM \
 	history h \
 JOIN teamplayer tp ON (h.teamid = tp.teamid) JOIN player p ON (tp.playerid = p.playerid) \
 WHERE \
 	h.teamid IN \
 ( \
 	select \
 	      s2.teamid \
 	  FROM \
 	  ( \
 	      SELECT \
 		  rank() OVER(ORDER BY t.league,t.points desc) AS national_rank, t.bracket,t.division_id, t.division_rank, t.is_random, t.league, t.losses, t.wins, t.points, t.region_rank, t.teamid, t.historypoints \
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
 	      JOIN  \
 		  teamplayer tp  \
 			ON (t.teamid = tp.teamid AND t.bracket=%i)  \
 	      JOIN  \
 		  player p  \
 			ON (tp.playerid = p.playerid)  \
 	      GROUP BY \
 		  t.teamid,p.country,t.bracket,t.division_id, t.division_rank, t.is_random, t.league, t.losses, t.wins, t.points, t.region_rank, t.historypoints  \
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
 	      s2.wins, s2.losses, s2.points, s2.national_rank, s2.region_rank, s2.bracket, s2.teamid, s2.division_id, s2.division_rank, s2.is_random, s2.league, s2.historypoints \
 	  ORDER BY \
 	      national_rank asc limit 10 \
 ) \
 GROUP BY h.teamid, h.points, h.delta \
 ORDER BY h.teamid,h.delta" % (bracket,bracket,country, bracket, bracket, country)

    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    db_con.close()
    return result
     
    
#program = SC2NO()
#program.add('Rockj',174823,'no')
#print program.is_player_added_uc('Rockj',234)
#print program.is_player_added_bnet(174823)

#print program.add_player(174823,'Rockj',234,202098, datetime.now())

#print program.fetch_player_bnet('Rockj',174823)
#print program.fetch_player_uc('Kjartan',155)
#print program.fetch_player_uc('InvalidCola',893)

#program.cronjob()

#print program.version

#f = open("/home/rockj/sc2ladder/data.txt","r")
#text = simplejson.load("file:///home/rockj/sc2ladder/data.txt")
#print program.parse_sc2ranks_data(text)
#pp
