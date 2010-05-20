#!/usr/bin/python

from buildBox import BoxScore
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from proc import procMLB, Player
from urllib2 import urlopen
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces

import os
import re

TEAMS = {"ana" : "LAA",
         "ari" : "ARI",
         "atl" : "ATL",
         "bal" : "BAL",
         "bos" : "BOS",
         "cha" : "CWS",
         "chn" : "CHC",
         "cin" : "CIN",
         "cle" : "CLE",
         "col" : "COL",
         "det" : "DET",
         "flo" : "FLA",
         "hou" : "HOU",
         "kca" : "KC",
         "lan" : "LAD",
         "mil" : "MIL",
         "min" : "MIN",
         "nya" : "NYY",
         "nyn" : "NYM",
         "oak" : "OAK",
         "phi" : "PHI",
         "pit" : "PIT",
         "sea" : "SEA",
         "sfn" : "SF",
         "sln" : "STL",
         "sdn" : "SD",
         "tba" : "TB",
         "tex" : "TEX",
         "tor" : "TOR",
         "was" : "WAS"}

class Game :
    def __init__(self, url, away, home) :
        self.url = url
        self.home = home
        self.away = away
    
class DateChooser(webapp.RequestHandler) :
    def get(self) :
        path = os.path.join(os.path.dirname(__file__), \
                            'templates/datechooser.html')
        self.response.out.write(template.render(path, None))

class GameChooser(webapp.RequestHandler) :
    def get(self) :
        year = self.request.get("year")
        month = self.request.get("month")
        day = self.request.get("day")
        url = 'http://gd2.mlb.com/components/game/mlb/year_' + \
              year + '/month_' + month + '/day_' + day + '/'

        f = urlopen(url)
        data = f.read()
        f.close()

        games = []
        for game in re.findall('href="(gid.*?)"', data) :
            away = game.split("_")[4][:3]
            if 'mlb' in away:
                away = away[0:3]
            home = game.split("_")[5][:3]
            if 'mlb' in home:
                home = home[0:3]
            if away in TEAMS and home in TEAMS:
                games.append(Game(game.rstrip('/'), TEAMS[away], TEAMS[home]))

        template_values = {'games' : games,
                           'year' : year,
                           'month' : month,
                           'day' : day}
        path = os.path.join(os.path.dirname(__file__), \
                            'templates/gamechooser.html')
        self.response.out.write(template.render(path, template_values))

class PlayerLookup(webapp.RequestHandler) :
    def get(self) :
        pid = self.request.get("batterID")
        players = Player.gql("WHERE pid = :1", pid)
        for p in players :
            self.response.out.write(p.pid + " - " + p.first[0] + ". " + p.last)
        
class BuildScorecard(webapp.RequestHandler) :
    def get(self) :
        year = self.request.get("year")
        month = self.request.get("month")
        day = self.request.get("day")
        gid = self.request.get("gameID")
        url = 'http://gd2.mlb.com/components/game/mlb/year_' + \
               year + '/month_' + month + '/day_' + day + '/' + gid

        self.response.headers['Content-type'] = 'image/svg+xml'
        box = BoxScore(self.response.out)
    
        # Create a parser
        parser = make_parser()
        # Tell the parser we are not interested in XML namespaces
        parser.setFeature(feature_namespaces, 0)

        p = procMLB(box, url)

        parser.setContentHandler(p)

        # Read the inning directory and process each inning
        f = urlopen(url + '/inning')
        s = f.read()
        f.close()
        for i in range(1, len(re.findall('"inning_\d+\.xml"', s)) + 1) :
            f = urlopen(url + '/inning/inning_' + str(i) + '.xml')
            parser.parse(f)
            f.close()
            if i == len(re.findall('"inning_\d+\.xml"', s)):
                box.endInning(gameOver=True)
            else:
                box.endInning()
        box.endBox(p.homePitchers, p.awayPitchers)

        
APPLICATION = webapp.WSGIApplication([('/', DateChooser),
                                      ('/choosegame', GameChooser),
                                      ('/scorecard', BuildScorecard),
                                      ('/player', PlayerLookup)],
                                     debug=True)

def main() :
    run_wsgi_app(APPLICATION)
    
if __name__ == '__main__':
    main()
