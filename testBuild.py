#!/usr/bin/env python

import re
import sys
from urllib2 import urlopen
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces

from constants import LOGOS
from buildBox import BoxScore
from proc import procMLB

if __name__ == '__main__':
    MONTH = sys.argv[1]
    DAY = sys.argv[2]
    YEAR = sys.argv[3]
    TEAM = sys.argv[4].lower()

    url = 'http://gd2.mlb.com/components/game/mlb/year_' + \
           YEAR + '/month_' + MONTH + '/day_' + DAY

    f = urlopen(url)
    DATA = f.read()
    f.close()

    for game in re.findall('href="day_%s/(gid.*?)"' % DAY, DATA):
        if game.find(TEAM + "mlb") > 0:
            url += '/' + game
            break

    IMG = open("test.svg", "w")
    gid = url.split('/')[-2]
    away_code = LOGOS.get(gid.split('_')[4][:3], None)
    home_code = LOGOS.get(gid.split('_')[5][:3], None)
    BOX = BoxScore(away_code, home_code, IMG)

    PARSER = make_parser()
    PARSER.setFeature(feature_namespaces, 0)
    p = procMLB(BOX, url)
    p.offline = True
    PARSER.setContentHandler(p)

    f = urlopen(url + 'inning/')
    s = f.read()
    f.close()
    for i in range(1, len(re.findall('"inning_\d+\.xml"', s)) + 1):
        print 'Inning: ' + str(i)
        f = urlopen(url + 'inning/inning_' + str(i) + '.xml')
        PARSER.parse(f)
        f.close()
        if i == len(re.findall('"inning_\d+\.xml"', s)):
            BOX.endInning(gameOver=True)
        else:
            BOX.endInning()
    BOX.endBox(p.homePitchers, p.awayPitchers, p.away_score, p.home_score)
    print p.homePitchers
    print p.awayPitchers

    IMG.close()
