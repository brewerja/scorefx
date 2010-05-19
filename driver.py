#!/usr/bin/python

from buildBox import BoxScore
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from models import Player
from proc import procMLB
from urllib2 import urlopen
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces

import os
import re
import sys

teams = {"ana" : "LAA",
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
        path = os.path.join(os.path.dirname(__file__), 'templates/datechooser.html')
        self.response.out.write(template.render(path, None))

class GameChooser(webapp.RequestHandler) :
    def get(self) :
        y = self.request.get("year")
        m = self.request.get("month")
        d = self.request.get("day")
        url = 'http://gd2.mlb.com/components/game/mlb/year_' + y + '/month_' + m + '/day_' + d + '/'

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
            if away in teams and home in teams:
                games.append(Game(game.rstrip('/'), teams[away], teams[home]))

        template_values = {'games' : games,
                           'year' : y,
                           'month' : m,
                           'day' : d}
        path = os.path.join(os.path.dirname(__file__), 'templates/gamechooser.html')
        self.response.out.write(template.render(path, template_values))

class PlayerLookup(webapp.RequestHandler) :
    def get(self) :
        pid = self.request.get("batterID")
        players = Player.gql("WHERE pid = :1", pid)
        for p in players :
            self.response.out.write(p.pid + " - " + p.first[0] + ". " + p.last)            
        
class BuildScorecard(webapp.RequestHandler) :
    def get(self) :
        y = self.request.get("year")
        m = self.request.get("month")
        d = self.request.get("day")
        gid = self.request.get("gameID")
        url = 'http://gd2.mlb.com/components/game/mlb/year_' + y + '/month_' + m + '/day_' + d + '/' + gid

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
            box.endInning()
        box.endBox(p.homePitchers, p.awayPitchers)

        
application = webapp.WSGIApplication([('/', DateChooser),
                                      ('/choosegame', GameChooser),
                                      ('/scorecard', BuildScorecard),
                                      ('/player', PlayerLookup)],
                                     debug=True)

def main() :
    run_wsgi_app(application)
    
if __name__ == '__main__':
    main()
