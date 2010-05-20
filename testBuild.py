#!/usr/bin/env python

import re
import sys
from urllib2 import urlopen
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces

from buildBox import BoxScore
from proc import procMLB

if __name__ == '__main__':
    MONTH = sys.argv[1]
    DAY = sys.argv[2]
    YEAR = sys.argv[3]
    TEAM = sys.argv[4].lower()

    url = 'http://gd2.mlb.com/components/game/mlb/year_' + \
           YEAR + '/month_' + MONTH + '/day_' + DAY + '/'

    f = urlopen(url)
    DATA = f.read()
    f.close()

    for game in re.findall('href="(gid.*?)"', DATA) :
        if game.find(TEAM + "mlb") > 0 :
            url += game
            break
    
    IMG = open("test.svg", "w")
    BOX = BoxScore(IMG)
    
    PARSER = make_parser()
    PARSER.setFeature(feature_namespaces, 0)
    p = procMLB(BOX, url)
    p.offline = True
    PARSER.setContentHandler(p)

    f = urlopen(url + '/inning')
    s = f.read()
    f.close()
    for i in range(1, len(re.findall('"inning_\d+\.xml"', s)) + 1) :
        print 'Inning: ' + str(i)
        f = urlopen(url + '/inning/inning_' + str(i) + '.xml')
        PARSER.parse(f)
        f.close()
        if i == len(re.findall('"inning_\d+\.xml"', s)):
            BOX.endInning(gameOver=True)
        else:
            BOX.endInning()                
    BOX.endBox(p.homePitchers, p.awayPitchers)
    print p.homePitchers
    print p.awayPitchers

    IMG.close()
