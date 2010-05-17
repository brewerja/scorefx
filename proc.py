#!/usr/bin/python

# Parse an MLB play-by-play XML file and build a scorecard

import const
from models import Player, InningState, Base
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
        self.batters = dict()
        self.pitchers = dict()
        self.offline = False
        self.desc = ''
        self.homePitchers = []
        self.awayPitchers = []
        self.reliefNoOutsFlag = False
        self.batterEvent = ''
        self.noBatterRunner = True
        self.pinchRunnerID = None
        self.inningState = InningState()
        
    def startElement(self, name, attrs):
        if (name == 'top'):
            self.curTeam = "A"
        elif (name == 'bottom'):
            self.curTeam = "H"
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
            if e == 'Offensive sub':
                action = attrs.get('des')
                mtch = re.search('Pinch runner .* replaces .*', action)
                if mtch:
                    self.pinchRunnerID = attrs.get('player')
                
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

            self.outs = int(attrs.get('o'))
            self.desc = self.desc + attrs.get('des')
            (code, result) = self.parsePlay(attrs.get('des'))
            self.batterEvent = attrs.get('event')
            
            # look up batterID
            batterID = attrs.get('batter')
            if self.offline :
                pass
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
                self.batterName = btr.first[0] + ". " + btr.last
            
            # Create a Batter object to be added at the end of the <atbat> tag.
            self.batterObj = self.inningState.createBatter(batterID, code, result, self.desc)
        
        elif (name == 'pitch' and self.inningState.runnerStack != {}):
              self.inningState.actionCount += 1
              self.inningState.advRunners(duringAB = True)
            
        elif (name == 'runner'):
            # Handle a runner advancing
            fromBase = attrs.get('start')
            toBase = attrs.get('end')
            event = attrs.get('event')
            out = False
            code = ''

            # handling end is tougher
            # "" doesn't mean the same thing all the time
            # if the runner scores end will be "" and score will be "T"
            # at the end of the inning, stranded runners have end = ""
            # other places?
            willScore = False
            if attrs.get('score') == "T":
                willScore = True
                toBase = Base.HOME
            elif toBase == '' and self.outs == 3: #stranded at the end of an inning, or out!?
                toBase = fromBase
            elif toBase == '':
                toBase = str(bases[fromBase]+1)+'B'
                out = True
            
            mtch = re.search('Caught Stealing', event)
            if mtch:
                code = 'CS'
                if attrs.get('end') == '':
                    out = True
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
            if mtch:
                code = 'POCS'
                if attrs.get('end') == '':
                    out = True      
            mtch = re.search('Pickoff', event)
            if mtch:
                code = 'PO'
                if attrs.get('end') == '':
                    out = True
            mtch = re.search('Pickoff Error', event)
            if mtch:
                code = 'E'
            mtch = re.search('Pickoff Attempt', event)
            if mtch:
                code = ''                                                                           
            mtch = re.search('Stolen Base', event)
            if mtch:
                code = 'SB'
            mtch = re.search('Wild Pitch', event)
            if mtch:
                code = 'WP'                 
            
            pid = attrs.get('id')
            
            if pid == self.pinchRunnerID:
                self.inningState.pinchRunner(fromBase, self.pinchRunnerID)
            
            # If this runner is also the batter, then go ahead and add the batter here.
            if pid == self.batterObj.id:
                self.noBatterRunner = False
                self.inningState.addBatter(self.batterObj, toBase, out, willScore)
                self.inningState.advRunners()                
            else: # otherwise, it's a runner already on base, so advance him accordingly.
                runnerObj = self.inningState.onBase[pid]
                self.inningState.addRunner(runnerObj, toBase, code, out)
                
    def endElement(self, name):
        if name == 'atbat':
            self.desc = ''
            # if there is not a runner tag for the batter, then you don't need the extra stuff
            if self.noBatterRunner == True:
                self.inningState.addBatter(self.batterObj)
                self.inningState.advRunners()
            self.noBatterRunner = True
              
        if name == 'top' or name == 'bottom':
     #       for i in range(0, self.inningState.actionCount+1):
     #           if i in self.inningState.atbats:
     #               string = str(i) + '*:'
     #           else:
     #               string = str(i) + ':'
     #           for b in self.inningState.batters:
     #               e = b.eventAt(i)
     #               if e != None:
     #                   if e.out == True:
     #                       end = '*'
     #                   else:
     #                       end = ''
     #                   string += e.fromBase + '->' + e.toBase + end + ' '
     #           print string
     #           string = ''
     #       print '--'
      #      for b in self.inningState.batters:
      #          for i in range(0,len(b.events)):
      #              e = b.events[i]
      #              if e == None:
      #                  print None
      #              else:
      #                  print e.fromBase + '->' + e.toBase
      #          print self.inningState.atbats
      #          print '--'
            self.inningState.team = self.curTeam      
            self.box.drawInning(self.inningState)
            self.inningState = InningState()
          
   
    def parsePlay(self, des):
        name = ""
        code = "XXX"
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
            return (code, result)
        
        if word == "strikes" :
            # "strikes out swinging"
            # "strikes out on foul tip"
            code = plays["strikeout"]
            result = const.OUT
        elif word == "called" :
            # "called out on strikes"
            code = plays["strikeout_looking"]
            result = const.OUT
        elif word == "walks" :
            code = plays["walk"]
            result = const.HIT
        elif word == "grounds" :
            mtch = re.search("grounds out.*?, (\w*)", action)
            if mtch :
                code = plays["ground"] + positions[mtch.group(1)]
                result = const.OUT
            elif (words[i + 1] == "out" and words[i + 2] == "to") :
                code = plays["ground"] + positions[words[i + 3]]
                result = const.OUT
            elif (words[i + 1] == "out" and words[i + 3] == "to") :
                code = plays["ground"] + positions[words[i + 4]]
                result = const.OUT
            elif ''.join(words[i + 1:i + 4]) == "intodoubleplay," :
                code = "DP"
                result = const.OUT
            elif ''.join(words[i + 1:i + 5]) == "intoaforceout," :
                # description is "grounds into a force out, (pos) to (pos)"
                # or "grounds into a force out, fielded by (pos)."
                code = plays["ground"]
                tmp = action.split(",")[1]
                mtch = re.search("fielded by (\w*)", tmp)
                if mtch :
                    code += positions[mtch.group(1)]
                else :
                    code += positions[tmp.split()[0]]
                result = const.OUT
        elif word == "flies" or word == "pops" :
            mtch = re.search("out.*? to (\w*)", action)
            if mtch :
                code = plays["fly"] + positions[mtch.group(1)]
                result = const.OUT
            mtch = re.search("into.*? double play, (\w*)", action)
            if mtch :
                code = plays["fly"] + positions[mtch.group(1)]
                result = const.OUT
        elif word == "lines" :
            mtch = re.search("out.*? to (\w*)", action)
            if mtch :
                code = plays["line"] + positions[mtch.group(1)]
                result = const.OUT
            mtch = re.search("into.*? double play, (\w*)", action)
            if mtch :
                code = plays["line"] + positions[mtch.group(1)]
                result = const.OUT
        elif word == "singles" or word == "doubles" or word == "triples" :
            # description is "on a (fly ball|ground ball|line drive|pop up) to (position)"
            # there is sometimes an adjective (soft, hard) after "on a"
            mtch = re.search("on a.*? (fly|ground|line|pop) .*? to (\w*)", action)
            tmp = mtch.group(1)
            if tmp == "pop" :
                tmp = "fly"
            code = plays[tmp] + positions[mtch.group(2)]
            result = const.HIT
        elif word == "reaches" :
            if re.search("reaches on \w* error", action) :
                mtch = re.search("error by (\w*)", action)
                code = plays["error"] + positions[mtch.group(1)]
                result = const.ERROR
            if re.search("reaches on a fielder's choice", action) :
                mtch = re.search("fielded by (\w*)", action)
                if mtch == None:
                    mtch = re.search("reaches on a fielder's choice out, (\w*)", action)
                code = plays["fielder's choice"] + positions[mtch.group(1)]
                result = const.OTHER
        elif word == "homers" :
            code = plays["home run"]
            result = const.HIT
        elif word == "out" :
            mtch = re.search("on a sacrifice (\w*)(,| to) (\w*)", action)
            if mtch :
                if mtch.group(1) == "fly" :
                    code = plays["sac fly"] + positions[mtch.group(3)]
                    result = const.OUT
                elif mtch.group(1) == "bunt" :
                    code = plays["sac bunt"] + positions[mtch.group(3)]
                    result = const.OUT
        elif word == "hits" :
            mtch = re.search("ground-rule double", action)
            if mtch:
                action = action.split('.')[0]
                mtch = re.search("ground-rule double .* on a (\w*) .*? to (\w*)", action)
                if mtch:
                    code = plays[mtch.group(1)] + positions[mtch.group(2)]
                    result = const.HIT
                mtch = re.search("ground-rule double .* on a (\w*) .*? down the (\w*)", action)
                if mtch:
                    code = plays[mtch.group(1)] + positions[mtch.group(2)]
                    result = const.HIT                
            elif ''.join(words[i + 1:i + 4]) == "agrandslam" :
                code = plays["home run"]
                result = const.HIT
        elif word == "hit" :
            if re.search("hit by pitch", action) :
                code = plays["hit by pitch"]
                result = const.HIT
        return (code, result)

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
