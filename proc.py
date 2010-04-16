#!/usr/bin/python

# Parse an MLB play-by-play XML file and build a scorecard

from models import Batter
import re
from urllib2 import urlopen
from xml.sax import saxutils

bases = {"1B" : 1, "2B" : 2, "3B" : 3, "" : 4}
# Map event attributes to scoring codes
wrds = ["grounds",
        "walks",
        "flies",
        "hits",
        "strikes",
        "doubles",
        "lines",
        "singles",
        "called",
        "hit",
        "pops",
        "homers",
        "reaches",
        "out"]
plays = { "strikeout" : "K",
          "walk" : "BB",
          "ground" : "G",
          "fly" : "F",
          "line" : "L",
          "home run" : "HR",
          "error" : "E",
          "sac fly" : "SF"}
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
        self.offline = False
        
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
            (self.play, self.out) = self.parsePlay(attrs.get('des'))
            # look up batterId
            batterID = attrs.get('batter')
            if self.offline :
                self.batter = batterID
            elif batterID in self.batters :
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
            if not self.offline :
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
            self.box.writeBatter(self.curTeam, self.batter, self.play, self.out, self.onBase[0])
            for fromBase, toBase in enumerate(self.onBase) :
                # toBase == None means no runner on fromBase
                # fromBase == 0 is the batter, we handle that in writeBatter
                if toBase and fromBase > 0 :
                    self.box.advanceRunner(self.curTeam, fromBase, toBase)
    
    def parsePlay(self, des) :
        name = ""
        play = "XXX"
        out = False
        found = False
        i = 0
        # Split into sentences and strip trailing periods
        lines = des.split(".    ")
        action = re.sub("\.\s*$", "", lines[0])
        words = action.split()
        for word in words :
            # Until we find the type of play, we have the batter's name
            if word in wrds :
                found = True
                break
            else :
                name += word
                i += 1
                
        if not found :
            return (play, out)
        
        if word == "strikes" or word == "called" :
            # "strikes out swinging"
            # "strikes out on foul tip"
            # "called out on strikes"
            play = plays["strikeout"]
            out = True
        elif word == "walks" :
            play = plays["walk"]
            out = False
        elif word == "grounds" :
            if words[i+1] == "out," :
                play = plays["ground"] + positions[words[i+2]]
                out = True
            elif ''.join(words[i+1:i+3]) == "outto" :
                play = plays["ground"] + positions[words[i+3]]
                out = True
            elif ''.join(words[i+1:i+4]) == "intodoubleplay," :
                play = "DP"
                out = True
            elif ''.join(words[i+1:i+5]) == "intoaforceout," :
                play = plays["ground"] + positions[words[i+5]]
                out = True
        elif word == "flies" or word == "pops" :
            play = plays["fly"] + positions[words[i+3]]
            out = True
        elif word == "lines" :
            play = plays["line"] + positions[words[i+3]]
            out = True
        elif word == "singles" or word == "doubles" or word == "triples" :
            # description is "on a (fly ball|ground ball|line drive) to (position)"
            # there is sometimes an adjective (soft, hard) after "on a"
            mtch = re.search("on a.* (fly|ground|line) .* to (\w*)", action)
            play = plays[mtch.group(1)] + positions[mtch.group(2)]
            out = False
        elif word == "reaches" :
            if re.search("reaches on \w* error", action) :
                mtch = re.search("error by (\w*)", action)
                play = plays["error"] + positions[mtch.group(1)]
                out = False
        elif word == "homers" :
            play = plays["home run"]
            out = False
        elif word == "out" :
            mtch = re.search("on a sacrifice fly to (\w*)", action)
            if mtch :
                play = plays["sac fly"] + positions[mtch.group(1)]
                out = True
                
        return (play, out)
