#!/usr/bin/python

"""Parse an MLB play-by-play XML file and build a scorecard."""

import re
import logging
from urllib2 import urlopen, HTTPError
from xml.sax import saxutils

from google.appengine.ext import db

import const
from models import InningState

WORDS = ["ground",
        "grounds",
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
PLAYS = { "strikeout": "K",
          "strikeout_looking": "Kl",
          "walk": "BB",
          "ground": "G",
          "fly": "F",
          "line": "L",
          "home run": "HR",
          "error": "E",
          "sac fly": "SF",
          "sac bunt": "SH",
          "fielder's choice": "FC",
          "hit by pitch": "HB",
          "catcher interference": "CI"}
POSITIONS = {"pitcher": "1",
             "catcher": "2",
             "first": "3",
             "second": "4",
             "third": "5",
             "shortstop": "6",
             "left": "7",
             "center": "8",
             "right": "9"}
         
class procMLB(saxutils.handler.ContentHandler):
    def __init__(self, box, url):
        self.box = box
        self.url = url # URL for the game directory
        self.curTeam = None # Keep track of which team is at bat
        self.desc = ''
        self.inningState = InningState()
        self.homePitchers = []
        self.awayPitchers = []
        self.reliefNoOutsFlag = False
        self.pinchRunnerID = None
        self.noBatterRunner = True   
        self.batters = dict()
        self.pitchers = dict()
        self.offline = False
        self.pitcher = ''
        self.outs = '0'
        self.batterObj = None
        
    def startElement(self, name, attrs):
        if (name == 'top'):
            self.curTeam = "A"
            
        elif (name == 'bottom'):
            self.curTeam = "H"
            
        elif (name == 'action'):
            self.desc += attrs.get('des')
            
            e = attrs.get('event')
            if e == 'Pitching Substitution':
                self.updatePitcher(attrs.get('player'))
            if e == 'Relief with No Outs':
                self.reliefNoOutsFlag = True
            if e == 'Offensive sub':
                action = attrs.get('des')
                mtch = re.search('Pinch runner .* replaces .*', action)
                if mtch:
                    self.pinchRunnerID = attrs.get('player')
                
        elif (name == 'atbat'):
            # Get the SP or a RP who hasn't put anyone out.
            if self.reliefNoOutsFlag == True or \
               (not self.homePitchers and self.curTeam == "A") or \
               (not self.awayPitchers and self.curTeam == "H"):
                self.updatePitcher(attrs.get('pitcher'))
                self.reliefNoOutsFlag = False                    

            self.outs = int(attrs.get('o'))
            self.desc += attrs.get('des')
            (code, result) = self.parsePlay(attrs.get('des'))
            if attrs.get('event') == 'Runner Out':
                code = '--'
            
            batterID = attrs.get('batter')
            self.desc = self.desc.strip().replace('.    ', '. ').replace('.  ', '. ')
            # Create a Batter object to be added at the end of the <atbat> tag.
            self.batterObj = self.inningState.createBatter(batterID, code, result, self.desc)
            # look up batterID
            self.updateBatter(batterID)
        
        elif (name == 'pitch' and self.inningState.runnerStack):
            self.inningState.advRunners(duringAB = True)
            
        elif (name == 'runner'):
            # Handle a runner advancing
            fromBase = attrs.get('start')
            toBase = attrs.get('end')
            event = attrs.get('event')
            out = False
            code = ''

            # Handling end is tougher.
            # "" doesn't mean the same thing all the time.
            # If the runner scores end will be "" and score will be "T".
            # At the end of the inning, stranded runners will be = "".
            # If a runner is out, end will be also be "".
            willScore = False
            if attrs.get('score') == "T":
                willScore = True
                toBase = "4B"
            # stranded at the end of an inning, or out!?
            elif toBase == '' and self.outs == 3:
                toBase = fromBase
            elif toBase == '':
                toBase = str(int(fromBase[0])+1)+'B'
                out = True
            
            mtch = re.search('Caught Stealing', event)
            if mtch:
                code = 'CS'
                if attrs.get('end') == '':
                    out = True
                    if self.outs == 3:
                        toBase = str(int(fromBase[0])+1)+'B'
            mtch = re.search('Defensive Indiff', event)
            if mtch:
                code = 'DI'
            mtch = re.search('Error', event)
            if mtch:
                code = 'E' 
            mtch = re.search('Passed Ball', event)
            if mtch:
                code = 'PB'
            mtch = re.search('Picked off stealing', event)
            if mtch or event in ['Pickoff 1B', 'Pickoff 2B', 'Pickoff 3B']:
                code = 'PO'
                if attrs.get('end') == '':
                    out = True
                    if self.outs == 3:
                        toBase = str(int(fromBase[0])+1)+'B'
            #mtch = re.search('Pickoff', event)
            #if mtch:
            #    code = 'PO'
            #    if attrs.get('end') == '':
            #        out = True
            mtch = re.search('Pickoff Error', event)
            if mtch:
                code = 'E'
                out = False
            #mtch = re.search('Pickoff Attempt', event)
            #if mtch:
            #    code = ''
            #    out = False                                                                           
            mtch = re.search('Stolen Base', event)
            if mtch:
                code = 'SB'
            mtch = re.search('Wild Pitch', event)
            if mtch:
                code = 'WP'                 
            
            pid = attrs.get('id')
            
            if pid == self.pinchRunnerID:
                self.inningState.pinchRunner(fromBase, self.pinchRunnerID)
            
            # If this runner is also the batter, then add the batter here.
            if pid == self.batterObj.pid:
                self.noBatterRunner = False
                self.inningState.addBatter(self.batterObj, toBase, out, willScore)
                self.inningState.advRunners()                
            else: # otherwise, it's a runner already on base, so advance him.
                runnerObj = self.inningState.onBase[pid]
                self.inningState.addRunner(runnerObj, toBase, code, out)
                
    def endElement(self, name):
        if name == 'atbat':
            self.desc = ''
            # If there is not a runner tag for the batter, 
            # then you don't need the extra stuff.
            if self.noBatterRunner == True:
                self.inningState.addBatter(self.batterObj)
                if self.batterObj.code == '--':
                    self.inningState.advRunners(duringAB = True, endAB = True)
                else:
                    self.inningState.advRunners()
            self.noBatterRunner = True
              
        if name == 'top' or name == 'bottom':
            self.inningState.team = self.curTeam
            self.box.drawInning(self.inningState)
            self.inningState = InningState()
          
   
    def parsePlay(self, des):
        code = "XX"
        result = const.OTHER
        found = False
        i = 0
        # Split into sentences and strip trailing periods
        lines = des.split(".    ")
        action = re.sub("\.\s*$", "", lines[0])
        words = action.split()
        word = ""
        for word in words:
            word = word.split('.')[0]
            # Until we find the type of play, we have the batter's name
            if word in WORDS:
                found = True
                break
            else:
                i += 1
                
        if not found:
            return (code, result)
        
        if word == "strikes":
            # "strikes out swinging"
            # "strikes out on foul tip"
            code = PLAYS["strikeout"]
            result = const.OUT
        elif word == "called":
            # "called out on strikes"
            code = PLAYS["strikeout_looking"]
            result = const.OUT
        elif word == "walks":
            code = PLAYS["walk"]
            result = const.HIT
        elif word == "ground":
            mtch = re.search("ground bunts into a force out.*?, (\w*)", action)
            if mtch:
                code = PLAYS["ground"] + POSITIONS[mtch.group(1)]
                result = const.OUT
        elif word == "grounds":
            mtch = re.search("grounds out.*?, (\w*)", action)
            if mtch:
                code = PLAYS["ground"] + POSITIONS[mtch.group(1)]
                result = const.OUT
            elif (words[i + 1] == "out" and words[i + 2] == "to"):
                code = PLAYS["ground"] + POSITIONS[words[i + 3]]
                result = const.OUT
            elif (words[i + 1] == "out" and words[i + 3] == "to"):
                code = PLAYS["ground"] + POSITIONS[words[i + 4]]
                result = const.OUT
            elif ''.join(words[i + 1:i + 4]) == "intodoubleplay,":
                code = "DP"
                result = const.OUT
            elif ''.join(words[i + 1:i + 5]) == "intoaforceout,":
                # description is "grounds into a force out, (pos) to (pos)"
                # or "grounds into a force out, fielded by (pos)."
                code = PLAYS["ground"]
                tmp = action.split(",")[1]
                mtch = re.search("fielded by (\w*)", tmp)
                if mtch:
                    code += POSITIONS[mtch.group(1)]
                else:
                    code += POSITIONS[tmp.split()[0]]
                result = const.OUT
        elif word == "flies" or word == "pops":
            mtch = re.search("out.*? to (\w*)", action)
            if mtch:
                code = PLAYS["fly"] + POSITIONS[mtch.group(1)]
                result = const.OUT
            mtch = re.search("into.*? double play, (\w*)", action)
            if mtch:
                code = PLAYS["fly"] + POSITIONS[mtch.group(1)]
                result = const.OUT
        elif word == "lines":
            mtch = re.search("out.*? to (\w*)", action)
            if mtch:
                code = PLAYS["line"] + POSITIONS[mtch.group(1)]
                result = const.OUT
            mtch = re.search("into.*? double play, (\w*)", action)
            if mtch:
                code = PLAYS["line"] + POSITIONS[mtch.group(1)]
                result = const.OUT
            mtch = re.search("into.*? triple play, (\w*)", action)
            if mtch:
                code = 'TP' #PLAYS["line"] + positions[mtch.group(1)]
                result = const.OUT                
        elif word == "singles" or word == "doubles" or word == "triples":
            # Description is "on a (fly ball|ground ball|line drive|pop up)
            # to (position)" there is sometimes an adjective (soft, hard) after "on a"
            mtch = re.search("on a.*? (fly|ground|line|pop|bunt) .*? to (\w*)", action)
            tmp = mtch.group(1)
            if tmp == "pop" or tmp == "bunt":
                tmp = "fly"
            code = PLAYS[tmp] + POSITIONS[mtch.group(2)]
            result = const.HIT
        elif word == "reaches":
            if re.search("reaches on .* error", action):
                mtch = re.search("error by (\w*)", action)
                code = PLAYS["error"] + POSITIONS[mtch.group(1)]
                result = const.ERROR                
            if re.search("reaches on a fielder's choice", action):
                mtch = re.search("fielded by (\w*)", action)
                if mtch == None:
                    mtch = re.search("reaches on a fielder's choice out, (\w*)", action)
                code = PLAYS["fielder's choice"] + POSITIONS[mtch.group(1)]
                result = const.OTHER
            if re.search("reaches on catcher interference", action):
                code = PLAYS["catcher interference"]
                result = const.OTHER                
        elif word == "homers":
            code = PLAYS["home run"]
            result = const.HIT
        elif word == "out":
            mtch = re.search("on a sacrifice (\w*)(,| to) (\w*)", action)
            if mtch:
                if mtch.group(1) == "fly":
                    code = PLAYS["sac fly"] + POSITIONS[mtch.group(3)]
                    result = const.OUT
                elif mtch.group(1) == "bunt":
                    code = PLAYS["sac bunt"] + POSITIONS[mtch.group(3)]
                    result = const.OUT
        elif word == "hits":
            mtch = re.search("ground-rule double", action)
            if mtch:
                action = action[6:len(action)].split('.')[0] # [6:end] Handles B. J. Upton
                mtch = re.search("ground-rule double .* on a (\w*) .*? to (\w*)", action)
                if mtch:
                    code = PLAYS[mtch.group(1)] + POSITIONS[mtch.group(2)]
                    result = const.HIT
                mtch = re.search("ground-rule double .* on a (\w*) .*? down the (\w*)", action)
                if mtch:
                    code = PLAYS[mtch.group(1)] + POSITIONS[mtch.group(2)]
                    result = const.HIT                
            elif ''.join(words[i + 1:i + 4]) == "agrandslam":
                code = PLAYS["home run"]
                result = const.HIT
            elif ''.join(words[i + 1:i + 4]) == "asacrificebunt":
                code = PLAYS["sac bunt"]
                result = const.OUT
            elif ''.join(words[i + 1:i + 5]) == "aninside-the-parkhomerun":
                code = PLAYS["home run"]
                result = const.HIT                
        elif word == "hit":
            if re.search("hit by pitch", action):
                code = PLAYS["hit by pitch"]
                result = const.HIT
        return (code, result)

    def updatePitcher(self, pitcherID):
        if pitcherID == '0':
            logging.error("Pitcher ID was '0'. Handled with a bogus name for now.")
        if self.offline:
            self.pitcher = pitcherID
        elif pitcherID in self.pitchers:
            p = self.pitchers[pitcherID]
        else:
            # We haven't seen the pitcher in this game yet, query the db
            pchrs = Player.gql("WHERE pid=:1", pitcherID)
            if pchrs.count() == 0:
                try:
                    # Not in the db, look him up and add him
                    f = urlopen(self.url + "/pitchers/" + pitcherID + ".xml")
                    s = f.read()
                    f.close()
                    p = Player()
                    p.pid = pitcherID
                    p.first = re.search('first_name="(.*?)"', s).group(1)
                    p.last = re.search('last_name="(.*?)"', s).group(1)
                    p.put()
                except HTTPError:
                    # TODO: Handle this by figuring out the name. Usually lands here b/c player ID is '0'
                    p = Player()
                    p.pid = '0'
                    p.first = "First"
                    p.last = "Last"
                    p.put()
                    logging.error("Pitcher ID was not valid. Handled with a bogus name for now.")
            else:
                p = pchrs.fetch(1)[0]
            # Cache the pitcher to save future trips to the db
            self.pitchers[pitcherID] = p
        if not self.offline:
            self.pitcher = p.first[0] + ". " + p.last

        batters = len(self.inningState.batters)
        if self.curTeam == "A":
            if not self.homePitchers or self.pitcher != self.homePitchers[-1][0]:
                self.homePitchers.append([self.pitcher, self.box.getCurBatter("A", batters)])
        elif self.curTeam == "H":
            if (not self.awayPitchers or self.pitcher != self.awayPitchers[-1][0]):
                self.awayPitchers.append([self.pitcher, self.box.getCurBatter("H", batters)])            
            
    def updateBatter(self, batterID):
        if not self.offline:
            if batterID in self.batters:
                btr = self.batters[batterID]
            else:
                # We haven't seen the batter in this game yet, query the db
                btrs = Player.gql("WHERE pid=:1", batterID)
                if btrs.count() == 0:
                    # Not in the db, look him up and add him
                    f = urlopen(self.url + "/batters/" + batterID + ".xml")
                    s = f.read()
                    f.close()
                    btr = Player()
                    btr.pid = batterID
                    btr.first = re.search('first_name="(.*?)"', s).group(1)
                    btr.last = re.search('last_name="(.*?)"', s).group(1)
                    btr.put()
                else:
                    btr = btrs.fetch(1)[0]
                # Cache the batter to save future trips to the db
                self.batters[batterID] = btr
            
            self.batterObj.name = btr.first[0] + ". " + btr.last

class Player(db.Model):
    """App engine db objects."""
    pid = db.StringProperty()
    first = db.StringProperty()
    last = db.StringProperty()
