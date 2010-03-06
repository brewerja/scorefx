#!/usr/bin/python

# Parse an MLB play-by-play XML file and build a scorecard

from models import Batter
import re
from urllib2 import urlopen
from xml.sax import saxutils

bases = {"1B" : 1, "2B" : 2, "3B" : 3, "" : 4}
# Map event attributes to scoring codes
plays = {"Strikeout" : "K",
         "Batter Interference" : "BI",
         "Fly Out" : "F",
         "Flyout" : "F",
         "Sac Fly" : "F",
         "Grounded Into DP" : "G",
         "Ground Out" : "G",
         "Groundout" : "G",
         "Home Run" : "F",
         "Force Out" : "XXX",
         "Runner Out" : "XXX",
         "Field Error" : "XXX",
         "Fielders Choice Out" : "XXX",
         "Hit By Pitch" : "HBP",
         "Bunt Ground Out" : "XXX",
         "Double Play" : "XXX",
         "Line Out" : "L",
         "Strikeout - DP" : "K",
         "Pop Out" : "P",
         "Fan interference" : "INT",
         "Bunt Pop Out" : "B",
         "Fielders Choice" : "XXX",
         "Walk" : "BB",
         "Intent Walk" : "IBB",
         "Sac Bunt" : "B"}
positions = {"pitcher" : "1",
             "catcher" : "2",
             "first" : "3",
             "second" : "4",
             "third" : "5",
             "shortstop" : "6",
             "left" : "7",
             "center" : "8",
             "right" : "9"}
         
class procMLB(saxutils.handler.ContentHandler):
    def __init__(self, box, url):
        self.box = box
        # URL for the game directory
        self.url = url
        # Keep track of which team is at bat
        self.curTeam = None
        # Keep track of where runners are and how they advance
        # 0=batter, 1=first, etc.
        # If there's a runner on base, the entry at the offset will indicate
        # which base the runner advanced to
        # Ex: [2, 3, 4, None] runners on first and second.  Batter doubles,
        # runner from first to third and runner from second scores
        self.onBase = [None, None, None, None]
        self.batters = dict()
        
    def startElement(self, name, attrs):
        if (name == 'top'):
            self.curTeam = "A"
            self.onBase = [None, None, None, None]
        elif (name == 'bottom'):
            self.curTeam = "H"
            self.onBase = [None, None, None, None]
        elif (name == 'atbat'):
            # Adjust baserunners.  onBase currently stores info on advancement
            # Make a copy, reset onBase and place baserunners
            # the default is runners don't advance
            tmp = list(self.onBase)
            self.onBase = [None, None, None, None]
            for t in tmp :
                if t and t < 4 :
                    self.onBase[t] = t
            self.scored = []
            #self.play = attrs.get('event')
            #if self.play in plays :
            #    self.play = plays[self.play]
            self.play = self.parsePlay(attrs.get('des'), attrs.get('event'))
            # look up batterId
            batterID = attrs.get('batter')
            if batterID in self.batters :
                btr = self.batters[batterID]
            else :
                # We haven't seen the batter in this game yet, query the db
                btrs = Batter.gql("WHERE pid=:1", batterID)
                if btrs.count() == 0 :
                    # Not in the db, look him up and add him
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
                # Cache the batter to save future trips to the db
                self.batters[batterID] = btr
            self.batter = btr.first[0] + ". " + btr.last
        elif (name == 'runner'):
            # Handle a runner advancing
            start = attrs.get('start')
            end = attrs.get('end')

            # parsing start is easy enough
            if start == "" :
                fromBase = 0
            else :
                fromBase = bases[start]

            # handling end is tougher
            # "" doesn't mean the same thing all the time
            # if the runner scores end will be "" and score will be "T"
            # at the end of the inning, stranded runners have end = ""
            # other places?
            toBase = bases[end]
            if attrs.get('score') == "T" :
                self.scored.append(fromBase)
            elif toBase == 4 :
                toBase = fromBase
            # update our runner tracking array
            self.onBase[fromBase] = toBase
                
    def endElement(self, name):
        if name == 'atbat' :
            # We're done with this atbat, write out the play and the runners
            self.box.writeBatter(self.curTeam, self.batter, self.play, self.onBase[0])
            for fromBase, toBase in enumerate(self.onBase) :
                # toBase == None means no runner on fromBase
                # fromBase == 0 is the batter, we handle that in writeBatter
                if toBase and fromBase > 0 :
                    self.box.advanceRunner(self.curTeam, fromBase, toBase)
    
    def parsePlay(self, des, event) :
        des = des.partition("    ")[0]
        if event in plays :
            play = plays[event]
        else :
            m = re.search("line|ground|fly", des)
            if m :
                if m.group(0) == "line" :
                    play = "L"
                elif m.group(0) == "ground" :
                    play = "G"
                elif m.group(0) == "fly" :
                    play = "F"
            else :
                play = "XXX"
        # Get the number of the position player who made the play, if needed
        if play in ("L", "G", "B", "F", "P") :
            m = re.search("left|right|center|first|second|third|shortstop|pitcher|catcher", des)
            if m :
                play += positions[m.group(0)]

        return play
