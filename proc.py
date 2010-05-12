#!/usr/bin/python

# Parse an MLB play-by-play XML file and build a scorecard

import const
from models import Player
import re
from urllib2 import urlopen
from xml.sax import saxutils

bases = {"1B" : 1, "2B" : 2, "3B" : 3, "" : 4}
wrds = ["grounds",
        "walks",
        "flies",
        "hits",
        "strikes",
        "singles",
        "doubles",
        "triples",
        "homers",
        "lines",
        "called",
        "hit",
        "hits",
        "pops",
        "reaches",
        "out"]
plays = { "strikeout" : "K",
          "strikeout_looking" : "Kl",
          "walk" : "BB",
          "ground" : "G",
          "fly" : "F",
          "line" : "L",
          "home run" : "HR",
          "error" : "E",
          "sac fly" : "SF",
          "sac bunt" : "SH",
          "fielder's choice" : "FC",
          "hit by pitch" : "HB"}
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
        self.pitchers = dict()
        self.offline = False
        self.desc = ''
        self.homePitchers = []
        self.awayPitchers = []
        self.reliefNoOutsFlag = False
        
    def startElement(self, name, attrs):
        if (name == 'top'):
            self.curTeam = "A"
            self.onBase = [None, None, None, None]
        elif (name == 'bottom'):
            self.curTeam = "H"
            self.onBase = [None, None, None, None]
        elif (name == 'action'):
            self.desc = self.desc + attrs.get('des')
            e = attrs.get('event')
            if e == 'Pitching Substitution':                  
                # look up pitcherID
                self.updatePitcher(attrs.get('player'))
                if self.curTeam == "A":
                    self.homePitchers.append([self.pitcher, self.box.getCurBatter("A")])
                elif self.curTeam == "H":
                    self.awayPitchers.append([self.pitcher, self.box.getCurBatter("H")])
            if e == 'Relief with No Outs':
                self.reliefNoOutsFlag = True
                
        elif (name == 'atbat'):
            # Inefficient IF's, should just get the starting pitcher somewhere else
            if self.homePitchers == [] and self.curTeam == "A":
                self.updatePitcher(attrs.get('pitcher'))
                self.homePitchers.append([self.pitcher, self.box.getCurBatter("A")])
            elif self.awayPitchers == [] and self.curTeam == "H":
                self.updatePitcher(attrs.get('pitcher'))
                self.awayPitchers.append([self.pitcher, self.box.getCurBatter("H")])
            if self.reliefNoOutsFlag == True:
                self.reliefNoOutsFlag = False
                if self.curTeam == "A":
                    self.updatePitcher(attrs.get('pitcher'))
                    self.homePitchers.append([self.pitcher, self.box.getCurBatter("A")])
                elif self.curTeam == "H":
                    self.updatePitcher(attrs.get('pitcher'))
                    self.awayPitchers.append([self.pitcher, self.box.getCurBatter("H")])                    
                
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
            self.desc = self.desc + attrs.get('des')
            (self.play, self.result) = self.parsePlay(attrs.get('des'))
            
            # look up batterID
            batterID = attrs.get('batter')
            if self.offline :
                self.batter = batterID
            elif batterID in self.batters :
                btr = self.batters[batterID]
            else :
                # We haven't seen the batter in this game yet, query the db
                btrs = Player.gql("WHERE pid=:1", batterID)
                if btrs.count() == 0 :
                    # Not in the db, look him up and add him
                    f = urlopen(self.url + "/batters/" + batterID + ".xml")
                    s = f.read()
                    f.close()
                    btr = Player()
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
            self.box.writeBatter(self.curTeam, self.batter, self.play, self.result, self.desc, self.onBase[0])
            self.desc = ''
            for fromBase, toBase in enumerate(self.onBase) :
                # toBase == None means no runner on fromBase
                # fromBase == 0 is the batter, we handle that in writeBatter
                if toBase and fromBase > 0 :
                    self.box.advanceRunner(self.curTeam, fromBase, toBase)
    
    def parsePlay(self, des) :
        name = ""
        play = "XXX"
        result = const.OTHER
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
            return (play, result)
        
        if word == "strikes" :
            # "strikes out swinging"
            # "strikes out on foul tip"
            play = plays["strikeout"]
            result = const.OUT
        elif word == "called" :
            # "called out on strikes"
            play = plays["strikeout_looking"]
            result = const.OUT
        elif word == "walks" :
            play = plays["walk"]
            result = const.HIT
        elif word == "grounds" :
            mtch = re.search("grounds out.*?, (\w*)", action)
            if mtch :
                play = plays["ground"] + positions[mtch.group(1)]
                result = const.OUT
            elif (words[i + 1] == "out" and words[i + 2] == "to") :
                play = plays["ground"] + positions[words[i + 3]]
                result = const.OUT
            elif (words[i + 1] == "out" and words[i + 3] == "to") :
                play = plays["ground"] + positions[words[i + 4]]
                result = const.OUT
            elif ''.join(words[i + 1:i + 4]) == "intodoubleplay," :
                play = "DP"
                result = const.OUT
            elif ''.join(words[i + 1:i + 5]) == "intoaforceout," :
                # description is "grounds into a force out, (pos) to (pos)"
                # or "grounds into a force out, fielded by (pos)."
                play = plays["ground"]
                tmp = action.split(",")[1]
                mtch = re.search("fielded by (\w*)", tmp)
                if mtch :
                    play += positions[mtch.group(1)]
                else :
                    play += positions[tmp.split()[0]]
                result = const.OUT
        elif word == "flies" or word == "pops" :
            mtch = re.search("out.*? to (\w*)", action)
            if mtch :
                play = plays["fly"] + positions[mtch.group(1)]
                result = const.OUT
            mtch = re.search("into.*? double play, (\w*)", action)
            if mtch :
                play = plays["fly"] + positions[mtch.group(1)]
                result = const.OUT
        elif word == "lines" :
            mtch = re.search("out.*? to (\w*)", action)
            if mtch :
                play = plays["line"] + positions[mtch.group(1)]
                result = const.OUT
            mtch = re.search("into.*? double play, (\w*)", action)
            if mtch :
                play = plays["line"] + positions[mtch.group(1)]
                result = const.OUT
        elif word == "singles" or word == "doubles" or word == "triples" :
            # description is "on a (fly ball|ground ball|line drive|pop up) to (position)"
            # there is sometimes an adjective (soft, hard) after "on a"
            mtch = re.search("on a.*? (fly|ground|line|pop) .*? to (\w*)", action)
            tmp = mtch.group(1)
            if tmp == "pop" :
                tmp = "fly"
            play = plays[tmp] + positions[mtch.group(2)]
            result = const.HIT
        elif word == "reaches" :
            if re.search("reaches on \w* error", action) :
                mtch = re.search("error by (\w*)", action)
                play = plays["error"] + positions[mtch.group(1)]
                result = const.ERROR
            if re.search("reaches on a fielder's choice", action) :
                mtch = re.search("fielded by (\w*)", action)
                if mtch == None:
                    mtch = re.search("reaches on a fielder's choice out, (\w*)", action)
                play = plays["fielder's choice"] + positions[mtch.group(1)]
                result = const.OTHER
        elif word == "homers" :
            play = plays["home run"]
            result = const.HIT
        elif word == "out" :
            mtch = re.search("on a sacrifice (\w*)(,| to) (\w*)", action)
            if mtch :
                if mtch.group(1) == "fly" :
                    play = plays["sac fly"] + positions[mtch.group(3)]
                    result = const.OUT
                elif mtch.group(1) == "bunt" :
                    play = plays["sac bunt"] + positions[mtch.group(3)]
                    result = const.OUT
        elif word == "hits" :
            mtch = re.search("ground-rule double", action)
            if mtch:
                action = action.split('.')[0]
                mtch = re.search("ground-rule double .* on a (\w*) .*? to (\w*)", action)
                if mtch:
                    play = plays[mtch.group(1)] + positions[mtch.group(2)]
                    result = const.HIT
                mtch = re.search("ground-rule double .* on a (\w*) .*? down the (\w*)", action)
                if mtch:
                    play = plays[mtch.group(1)] + positions[mtch.group(2)]
                    result = const.HIT                
            elif ''.join(words[i + 1:i + 4]) == "agrandslam" :
                play = plays["home run"]
                result = const.HIT
        elif word == "hit" :
            if re.search("hit by pitch", action) :
                play = plays["hit by pitch"]
                result = const.HIT
        return (play, result)

    def updatePitcher(self, pitcherID):
        if self.offline :
            self.pitcher = pitcherID
        elif pitcherID in self.pitchers :
            p = self.pitchers[pitcherID]
        else :
            # We haven't seen the pitcher in this game yet, query the db
            pchrs = Player.gql("WHERE pid=:1", pitcherID)
            if pchrs.count() == 0 :
                # Not in the db, look him up and add him
                f = urlopen(self.url + "/pitchers/" + pitcherID + ".xml")
                s = f.read()
                f.close()
                p = Player()
                p.pid = pitcherID
                p.first = re.search('first_name="(.*?)"', s).group(1)
                p.last = re.search('last_name="(.*?)"', s).group(1)
                p.put()
            else :
                p = pchrs.fetch(1)[0]
            # Cache the pitcher to save future trips to the db
            self.pitchers[pitcherID] = p
        if not self.offline:
            self.pitcher = p.first[0] + ". " + p.last 
