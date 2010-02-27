#!/usr/bin/python
#given a game url, build a boxscore locally

from buildBox import BoxScore
from proc import procMLB
from urllib import urlopen
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces

import re
import sys

if __name__ == '__main__':
    if (len(sys.argv) != 2):
        print "USAGE: ", sys.argv[0], " <GAMEURL>"
        sys.exit(1)

    url = sys.argv[1]
    img = open("box.svg", "w")
    box = BoxScore(img)
    box.startBox()
    
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
    box.endBox()
    img.close()
