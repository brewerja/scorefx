#!/usr/bin/python

from models import Batter
import re
from urllib2 import urlopen
from xml.sax import saxutils

bases = {"1B" : 1, "2B" : 2, "3B" : 3, "" : 4}
plays = {"Strikeout" : "K",
         "Batter Interference" : "BI",
         "Fly Out" : "F",
         "Sac Fly" : "F",
         "Grounded Into DP" : "G",
         "Ground Out" : "G",
         "Home Run" : "F",
         "Force Out" : "XXX",
         "Double" : "XXX",
         "Runner Out" : "XXX",
         "Field Error" : "XXX",
         "Fielders Choice Out" : "XXX",
         "Hit By Pitch" : "HBP",
         "Bunt Ground Out" : "XXX",
         "Double Play" : "XXX",
         "Line Out" : "L",
         "Strikeout - DP" : "K",
         "Pop Out" : "F",
         "Fan interference" : "INT",
         "Bunt Pop Out" : "B",
         "Fielders Choice" : "XXX",
         "Walk" : "BB",
         "Intent Walk" : "IBB",
         "Single" : "XXX",
         "Triple" : "XXX",
         "Sac Bunt" : "B"}
         
class procMLB(saxutils.handler.ContentHandler):
    def __init__(self, box, url):
        self.box = box
        self.url = url
        self.curTeam = None
        self.onBase = [None, None, None, None]
        
    def startElement(self, name, attrs):
        if (name == 'top'):
            self.curTeam = "A"
            self.onBase = [None, None, None, None]
        elif (name == 'bottom'):
            self.curTeam = "H"
            self.onBase = [None, None, None, None]
        elif (name == 'atbat'):
            # Adjust baserunners
            tmp = list(self.onBase)
            self.onBase = [None, None, None, None]
            for t in tmp :
                if t and t < 4 :
                    self.onBase[t] = t
            self.scored = []
            self.play = attrs.get('event')
            if self.play in plays :
                self.play = plays[self.play]
            batterID = attrs.get('batter')
            btrs = Batter.gql("WHERE pid=:1", batterID)
            if btrs.count() == 0 :
                f = urlopen(self.url + "/batters/" + batterID + ".xml")
                s = f.read()
                f.close()
                btr = Batter()
                btr.pid = batterID
                btr.first = re.search('first_name="(.*?)"', s).group(1)
                btr.last = re.search('last_name="(.*?)"', s).group(1)
                btr.put()
            else :
                btr = btrs.fetch(1)[0]
            self.batter = btr.first[0] + ". " + btr.last
        elif (name == 'runner'):
            start = attrs.get('start')
            end = attrs.get('end')

            if start == "" :
                fromBase = 0
            else :
                fromBase = bases[start]
            toBase = bases[end]

            if attrs.get('score') == "T" :
                self.scored.append(fromBase)
            elif toBase == 4 :
                toBase = fromBase
            self.onBase[fromBase] = toBase
                
    def endElement(self, name):
        if (name == 'inning'):
            return
        elif name == 'atbat' :
            #print self.curTeam + " " + self.batter + " " + self.play
            self.box.writeBatter(self.curTeam, self.batter, self.play, self.onBase[0])
            for fromBase, toBase in enumerate(self.onBase) :
                if toBase and fromBase > 0 :
                    #print "  " + str(fromBase) + " -> " + str(toBase)
                    self.box.advanceRunner(self.curTeam, fromBase, toBase)
    

