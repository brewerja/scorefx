#!/usr/bin/python
#Scrape all player info from 2009 into a csv

from datetime import date, timedelta
from urllib import urlopen
from xml.sax import make_parser, saxutils
from xml.sax.handler import feature_namespaces

import re
import sys

playerIDs = set()
outfil = None

class Player :
    def __init__(self, pid, first, last) :
        self.pid = pid
        self.first = first
        self.last = last
        
class PlayerParser(saxutils.handler.ContentHandler) :
  
    def startElement(self, name, attrs) :
        if (name == "Player") :
            outfil.write(attrs.get('id') + "," + attrs.get('first_name') + "," + attrs.get('last_name') + '\n')

if __name__ == '__main__':
    base = 'http://gd2.mlb.com/components/game/mlb/year_2009/'

    outfil = open("playerIDs.csv", "w")
    # Create a parser
    parser = make_parser()
    # Tell the parser we are not interested in XML namespaces
    parser.setFeature(feature_namespaces, 0)

    p = PlayerParser()

    parser.setContentHandler(p)

    d = date(2009, 4, 1)
    while d.month < 11 :
        print d
        dayURL = base + "month_0" + str(d.month) + "/day_"
        if d.day < 10 :
            dayURL += "0"
        dayURL += str(d.day) + "/"
        f = urlopen(dayURL)
        s = f.read()
        f.close()

        for u in re.findall('href="(gid.*)/"', s) :
            batURL = dayURL + u + "/batters"
            f = urlopen(batURL)
            s = f.read()
            f.close()

            for batterID in re.findall('href="(\d+)\.xml"', s) :
                if batterID in playerIDs :
                    continue
                tmp = batURL + '/' + batterID + '.xml'
                f = urlopen(tmp)
                parser.parse(f)
                f.close()
                playerIDs.add(batterID)
                
        d += timedelta(1)
        outfil.flush()
    outfil.close()
    #for player in players :
    #    print player.id + "," + player.first + "," + player.last
