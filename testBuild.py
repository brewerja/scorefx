#!/usr/bin/env python

from buildBox import BoxScore
from proc import procMLB
from urllib2 import urlopen
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces

import re
import sys

if __name__ == '__main__' :
    m = sys.argv[1]
    d = sys.argv[2]
    y = sys.argv[3]
    team = sys.argv[4].lower()

    url = 'http://gd2.mlb.com/components/game/mlb/year_' + y + '/month_' + m + '/day_' + d + '/'

    f = urlopen(url)
    data = f.read()
    f.close()

    for game in re.findall('href="(gid.*?)"', data) :
        if game.find(team + "mlb") > 0 :
            break
    url += game

    img = open("test.svg", "w")
    box = BoxScore(img)
    box.startBox()
    
    parser = make_parser()
    parser.setFeature(feature_namespaces, 0)
    p = procMLB(box, url)
    p.offline = True
    parser.setContentHandler(p)

    f = urlopen(url + '/inning')
    s = f.read()
    f.close()
    for i in range(1, len(re.findall('"inning_\d+\.xml"', s)) + 1) :
        print i
        f = urlopen(url + '/inning/inning_' + str(i) + '.xml')
        parser.parse(f)
        f.close()
        box.endInning()                
    box.endBox(p.homePitchers, p.awayPitchers)
    print p.homePitchers
    print p.awayPitchers

    img.close()
