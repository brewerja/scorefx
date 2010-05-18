from google.appengine.ext import db

class Player(db.Model) :
    pid = db.StringProperty()
    first = db.StringProperty()
    last = db.StringProperty()
    
class Batter():
    def __init__(self, id, code, result, desc, willScore=False):
        self.id = id # from MLB XML
        self.name = id
        self.code = code # F7, L8, G6, etc.
        self.result = result # ERROR, HIT, OTHER, OUT (const.py)
        self.desc = desc
        self.events = [] # list of events, indexed by actionCount.  if no event @ an index, use None
        self.willScore = willScore
 
    def advance(self, actionCount, code, toBase, out):
        # update onBase and add an event to events at index actionCount
        fromBase = self.onBase
        self.onBase = toBase
        while len(self.events) < actionCount:
            self.events.append(None)
        if (toBase == '4B' or toBase == '4X') and out == False:
            self.willScore = True
        e = Event("RunnerAdvance", code, fromBase, toBase, out)            
        self.events.append(e)
    
    def eventAt(self, actionCount):
        if len(self.events) > actionCount:
            ret = self.events[actionCount]
            if ret:
                ret.willScore = self.willScore
        else:
            ret = None
        return ret
class Event:
    def __init__(self, type, code, fromBase, toBase, out):
        self.type = type # this is either "AtBat" (really a plate appearance) or "RunnerAdvance"
        self.code = code # this is, for example, "K" or "L7" or "WP"
        self.fromBase = fromBase # the base where the player starts, we'll have a Base object defining "constant" values
        self.toBase = toBase # the base where the player ends, we'll have a Base object defining "constant" values
        self.out = out # whether the player reaches toBase successfully
        self.willScore = False

class InningState:
    def __init__(self):
        self.actionCount = -1
        self.batters = [] # Ordered list of the batters appearing in the inning.
        self.onBase = {} # Dict of id:Batter pairs of who is on base at a given time.
        self.runnerStack = {} # Dict of id:Batter pairs of runners to be advanced after the batter.
        self.atbats = {} # Dict of actionCount:index in self.batters.

    def createBatter(self, id, code, result, desc):
        return Batter(id, code, result, desc)

    def addBatter(self, batterObj, toBase='', out=True, willScore=False):
        self.batters.append(batterObj)
        self.actionCount += 1
        while len(batterObj.events) < self.actionCount:
            batterObj.events.append(None)
        fromBase = ''
        batterObj.events.append(Event("AtBat", batterObj.code, fromBase, toBase, out))
        self.atbats[self.actionCount] = len(self.batters)-1
        batterObj.willScore = willScore # whether a player will eventually score.  will need to refine this to handle batting around
        batterObj.onBase = toBase # the base where the player is currently.  use the advance() function to change

        events = batterObj.events
        if out == False and toBase != Base.HOME:
            self.onBase[batterObj.id] = batterObj
        return batterObj
    
    def advRunners(self, duringAB=False, endAB=False): 
        if duringAB == False:
            # Hold runners who are already on base, but who did not move.
            for key, runnerObj in self.onBase.items():
                if key not in self.runnerStack and self.batters[-1].id != key:
                    fromBase = runnerObj.onBase
                    if fromBase == Base.FIRST:
                        toBase = Base.FIRST
                    elif fromBase == Base.SECOND or fromBase == Base.SECOND_M:
                        toBase = Base.SECOND
                    elif fromBase == Base.THIRD or fromBase == Base.THIRD_M:
                        toBase = Base.THIRD
                    self.addRunner(runnerObj, toBase)        
        
        if duringAB == True:
            if not endAB:
                self.actionCount += 1
            for key, r in self.runnerStack.items():
                toBase = r.toBase
                if toBase == Base.SECOND:
                    r.toBase = Base.SECOND_M
                elif toBase == Base.THIRD:
                    r.toBase = Base.THIRD_M
                elif toBase == Base.HOME:
                    r.toBase = Base.HOME_M
        
        for key, r in self.runnerStack.items():
            runnerObj = self.onBase[key]
            runnerObj.advance(self.actionCount, r.code, r.toBase, r.out)
            # If a runners scores or is out on the play, take him off the bases.
            if r.toBase == '4B' or r.toBase == '4X' or r.out == True:
                self.onBase.pop(key)
        self.runnerStack = {}
            
    def addRunner(self, runnerObj, toBase, code='', out=False):
        self.runnerStack[runnerObj.id] = Runner(toBase, code, out)
    
    def pinchRunner(self, base, newID):
        for key, runnerObj in self.onBase.items():
            if self.onBase[key].onBase == base:
                self.onBase[key].id = newID
                self.onBase[newID] = self.onBase.pop(key)
class Runner:
    def __init__(self, toBase, code, out):
        self.toBase = toBase
        self.code = code
        self.out = out

class Base:
    FIRST = "1B"
    SECOND = "2B"
    THIRD = "3B"
    HOME = "4B"
    SECOND_M = "2X" # 2nd base in the "middle" of a plate appearance i.e. from a stolen base
    THIRD_M = "3X" # ditto
    HOME_M = "4X"        
