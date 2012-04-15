#!/usr/bin/python

import os
import re

from datetime import date, datetime, time, timedelta
from urllib2 import urlopen
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from buildBox import BoxScore
from proc import procMLB, Player

TEAMS = {'ana': 'LAA',
         'ari': 'ARI',
         'atl': 'ATL',
         'bal': 'BAL',
         'bos': 'BOS',
         'cha': 'CWS',
         'chn': 'CHC',
         'cin': 'CIN',
         'cle': 'CLE',
         'col': 'COL',
         'det': 'DET',
         'flo': 'FLA',
         'hou': 'HOU',
         'kca': 'KC',
         'lan': 'LAD',
         'mia': 'MIA',
         'mil': 'MIL',
         'min': 'MIN',
         'nya': 'NYY',
         'nyn': 'NYM',
         'oak': 'OAK',
         'phi': 'PHI',
         'pit': 'PIT',
         'sea': 'SEA',
         'sfn': 'SF',
         'sln': 'STL',
         'sdn': 'SD',
         'tba': 'TB',
         'tex': 'TEX',
         'tor': 'TOR',
         'was': 'WAS'}

LOGOS = {'ana' : 'ana',
         'ari' : 'ari',
         'atl' : 'atl',
         'bal' : 'bal',
         'bos' : 'bos',
         'cha' : 'cws',
         'chn' : 'chc',
         'cin' : 'cin',
         'cle' : 'cle',
         'flo' : 'fla',
         'hou' : 'hou',
         'kca' : 'kc',
         'lan' : 'la',
         'mia' : 'mia',
         'mil' : 'mil',
         'min' : 'min',
         'nya' : 'nyy',
         'nyn' : 'nym',
         'oak' : 'oak',
         'phi' : 'phi',
         'pit' : 'pit',
         'sea' : 'sea',
         'sfn' : 'sf',
         'sln' : 'stl',
         'sdn' : 'sd',
         'tba' : 'tb',
         'tex' : 'tex',
         'tor' : 'tor',
         'was' : 'was'}

class Game:
    def __init__(self, url, away, home):
        self.url = url
        self.home = home
        self.away = away

    def jsonString(self):
        ret = '{"url": "%s", "home": "%s", away: "%s"}' % (self.url, self.home,
                                                           self.away)
        return ret


def getGames(gameDate):
        year = gameDate.strftime('%Y')
        month = gameDate.strftime('%m')
        date = gameDate.strftime('%d')

        url = ('http://gd2.mlb.com/components/game/mlb/year_%s/month_%s/'
               'day_%s/') % (year, month, date)

        data = urlopen(url).read()

        games = []
        for game in re.findall('href="(gid_%s_%s_%s.*?)"' % (year, month,
                                                             date), data):
            away = game.split('_')[4][:3]
            if 'mlb' in away:
                away = away[0:3]
            home = game.split('_')[5][:3]
            if 'mlb' in home:
                home = home[0:3]
            if away in TEAMS and home in TEAMS:
                games.append(Game(game.rstrip('/'), TEAMS[away], TEAMS[home]))

        return games


class GameLister(webapp.RequestHandler):
    def get(self):
        # Translate the passed-in args to a datetime object
        year = self.request.get('year')
        month = self.request.get('month')
        day = self.request.get('day')
        gameDate = datetime.strptime(year + month + day, '%Y%m%d')

        # Get the games for the requested day
        games = getGames(gameDate)

        # Translate the list of games to JSON
        gamesJSON = '[\n'
        for game in games:
            gamesJSON += game.jsonString()
            gamesJSON += ',\n'
        gamesJSON = gamesJSON.strip(',\n')
        gamesJSON += '\n]\n'

        # Return the JSON
        self.response.headers['Content-Type'] = 'text/javascript'
        self.response.out.write(gamesJSON)


class PageBuilder(webapp.RequestHandler):
    def get(self):
        # Figure out at which day to set the calendar.
        # If no game has started today, use yesterday.
        # Timezones are screwy in Python, so for now just get UTC and adjust
        # manually.
        gameDate = datetime.utcnow()
        gameDate -= timedelta(hours=4)
        url = ('http://gd2.mlb.com/components/game/mlb/year_%s/month_%s/'
               'day_%s/master_scoreboard.xml') % (gameDate.strftime('%Y'),
                                                  gameDate.strftime('%m'),
                                                  gameDate.strftime('%d'))
        data = urlopen(url).read()

        # We don't bother with parsing XML since we know exactly what we're
        # looking for.
        times = re.finditer(' time="([0-9:]+)".*?ampm="([AP]M)"', data,
                            re.DOTALL)
        curTime = gameDate.time()
        started = False
        for mtch in times:
            t = datetime.strptime(mtch.group(1) + mtch.group(2),
                                  '%I:%M%p').time()
            if (t < curTime):
                started = True
                break
        if not started:
            gameDate -= timedelta(days=1)

        # Now that we've settled on a date,
        # figure out what games are being played
        games = getGames(gameDate)
        dte = ('new Date(%d, %d, %d)' %
               (gameDate.year, gameDate.month - 1, gameDate.day))
        template_values = {'games': games,
                           'dte': dte}
        path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
        self.response.out.write(template.render(path, template_values))


class PlayerLookup(webapp.RequestHandler):
    def get(self):
        pid = self.request.get('batterID')
        players = Player.gql('WHERE pid = :1', pid)
        for p in players:
            self.response.out.write(p.pid + ' - ' + p.first[0] + '. ' + p.last)


class BuildScorecard(webapp.RequestHandler):
    def get(self):
        year = self.request.get('year')
        month = self.request.get('month')
        day = self.request.get('day')
        gid = self.request.get('gameID')

        url = ('http://gd2.mlb.com/components/game/mlb/year_%s/month_%s/'
               'day_%s/%s') % (year, month, day, gid)

        self.response.headers['Content-type'] = 'image/svg+xml'

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
        s = urlopen(url + '/inning').read()

        for i in range(1, len(re.findall('"inning_\d+\.xml"', s)) + 1):
            parser.parse(urlopen(url + '/inning/inning_' + str(i) + '.xml'))
            if i == len(re.findall('"inning_\d+\.xml"', s)):
                box.endInning(gameOver=True)
            else:
                box.endInning()
        box.endBox(p.homePitchers, p.awayPitchers, p.away_score, p.home_score)


APPLICATION = webapp.WSGIApplication([('/', PageBuilder),
                                      ('/getgames', GameLister),
                                      ('/scorecard', BuildScorecard),
                                      ('/player', PlayerLookup)],
                                     debug=True)


def main():
    run_wsgi_app(APPLICATION)

if __name__ == '__main__':
    main()
