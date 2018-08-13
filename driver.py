#!/usr/bin/python

import os
import re
import json

from datetime import datetime, timedelta
from urllib2 import urlopen
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces

import webapp2
import jinja2

from buildBox import BoxScore
from proc import procMLB, Player
from constants import TEAMS, LOGOS

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)


class Game:
    def __init__(self, url, away, home):
        self.url = url
        self.home = home
        self.away = away


def getGames(date):
    url = ('http://gd2.mlb.com/components/game/mlb/year_%04d/month_%02d/'
           'day_%02d') % (date.year, date.month, date.day)

    data = urlopen(url).read()

    games = []
    for game in re.findall('href="day_%02d/(gid_%04d_%02d_%02d.*?)"' %
                           (date.day, date.year, date.month, date.day), data):
        away = game.split('_')[4][:3]
        home = game.split('_')[5][:3]
        if away in TEAMS and home in TEAMS:
            games.append(Game(game.rstrip('/'), TEAMS[away], TEAMS[home]))

    return games


class GameLister(webapp2.RequestHandler):
    def get(self):
        """Given a year, month, day, return JSON listing of games."""
        try:
            year = int(self.request.get('year'))
            month = int(self.request.get('month'))
            day = int(self.request.get('day'))
            date = datetime(year, month, day)
        except (TypeError, ValueError):
            self.abort(400)

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(
            json.dumps([g.__dict__ for g in getGames(date)]))


class PageBuilder(webapp2.RequestHandler):
    def get(self):
        # Figure out at which day to set the calendar.
        # If no game has started today, use yesterday.
        # Timezones are screwy in Python, so for now just get UTC and adjust
        # manually.
        date = datetime.utcnow() - timedelta(hours=4)
        url = ('http://gd2.mlb.com/components/game/mlb/year_%04d/month_%02d/'
               'day_%02d/master_scoreboard.xml' %
               (date.year, date.month, date.day))
        data = urlopen(url).read()

        # We don't bother with parsing XML since we know exactly what we're
        # looking for.
        times = re.finditer(' time="([0-9:]+)".*?ampm="([AP]M)"', data,
                            re.DOTALL)
        curTime = date.time()
        started = False
        for mtch in times:
            t = datetime.strptime(mtch.group(1) + mtch.group(2),
                                  '%I:%M%p').time()
            if (t < curTime):
                started = True
                break
        if not started:
            date -= timedelta(days=1)

        # Now that we've settled on a date,
        # figure out what games are being played
        games = getGames(date)
        dte = ('new Date(%d, %d, %d)' % (date.year, date.month - 1, date.day))
        template_values = {'games': games, 'dte': dte}
        t = jinja_env.get_template('index.html')
        self.response.out.write(t.render(template_values))


class PlayerLookup(webapp2.RequestHandler):
    def get(self):
        pid = self.request.get('batterID')
        players = Player.gql('WHERE pid = :1', pid)
        for p in players:
            self.response.out.write(p.pid + ' - ' + p.first[0] + '. ' + p.last)


class BuildScorecard(webapp2.RequestHandler):
    def get(self):
        try:
            year = int(self.request.get('year'))
            month = int(self.request.get('month'))
            day = int(self.request.get('day'))
            datetime(year, month, day)  # Validation
            gid = self.request.get('gameID')
        except (TypeError, ValueError):
            self.abort(400)

        url = ('http://gd2.mlb.com/components/game/mlb/year_%04d/month_%02d/'
               'day_%02d/%s') % (year, month, day, gid)

        self.response.headers['Content-Type'] = 'image/svg+xml'

        # Figure out which teams are playing.  MLB uses inconsistent codes
        # to represent teams (i.e. nya & nyy for the Yanks) so translate
        # from the code in the gid to the code for the logo PNG
        away_code = LOGOS.get(gid.split('_')[4][:3], None)
        home_code = LOGOS.get(gid.split('_')[5][:3], None)
        box = BoxScore(away_code, home_code, self.response.out)

        # Create a parser
        parser = make_parser()
        # Tell the parser we are not interested in XML namespaces
        parser.setFeature(feature_namespaces, 0)

        p = procMLB(box, url)

        parser.setContentHandler(p)

        # Read the inning directory and process each inning
        s = urlopen(url + '/inning/').read()

        for i in range(1, len(re.findall('"inning_\d+\.xml"', s)) + 1):
            parser.parse(urlopen(url + '/inning/inning_' + str(i) + '.xml'))
            if i == len(re.findall('"inning_\d+\.xml"', s)):
                box.endInning(gameOver=True)
            else:
                box.endInning()
        box.endBox(p.homePitchers, p.awayPitchers, p.away_score, p.home_score)


app = webapp2.WSGIApplication([
    ('/', PageBuilder),
    ('/getgames', GameLister),
    ('/scorecard', BuildScorecard),
    ('/player', PlayerLookup)
], debug=True)
