from google.appengine.ext import db

class Player(db.Model) :
    pid = db.StringProperty()
    first = db.StringProperty()
    last = db.StringProperty()
    
class Batter():
    def __init__(self, id, code, toBase, out, willScore):
        self.id = id # from MLB XML
        self.events = [] # list of events, indexed by actionCount.  if no event @ an index, use None
        fromBase = ''
        self.events.append(Event("AtBat", code, fromBase, toBase, out))
        self.willScore = willScore # whether a player will eventually score.  will need to refine this to handle batting around
        self.onBase = toBase # the base where the player is currently.  use the advance() function to change
 
    def advance(self, actionCount, code, toBase, out):
        # update onBase and add an event to events at index actionCount
        fromBase = self.onBase
        e = Event("RunnerAdvance", code, fromBase, toBase, out)
        self.onBase = toBase
        while len(self.events) < actionCount :
            self.events.append(None)
        self.events.append(e)
        if toBase == '4B' and out == False:
            self.willScore = True
    
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

class Base:
    FIRST = "1B"
    SECOND = "2B"
    THIRD = "3B"
    HOME = "4B"
    SECOND_M = "2X" # 2nd base in the "middle" of a plate appearance i.e. from a stolen base
    THIRD_M = "3X" # ditto

class InningState:
    def __init__(self):
        self.actionCount = -1
        self.batters = []
        self.onBase = {}

    def addBatter(self, id, code, toBase='', out=True, willScore=False):
        batterObj = Batter(id, code, toBase, out, willScore)
        self.batters.append(batterObj)
        self.actionCount += 1
        while len(batterObj.events) <= self.actionCount:
            batterObj.events.insert(0,None)
        if out == False:
            self.onBase[batterObj.id] = batterObj
        return batterObj
    
    def advRunner(self, runnerObj, toBase, code='', out=False):
        if code != '':
            self.actionCount += 1
        runnerObj.advance(self.actionCount, code, toBase, out)
        # If the runner is out on the basepaths or scores, he's no longer on base.
        if out == True or (out == False and toBase == '4B'):
            self.onBase.pop(runnerObj.id)
    
    def pinchRunner(self, base, newID):
        for key, runnerObj in self.onBase.items():
            if self.onBase[key] == base:
                self.onBase[key].id = newID
                self.onBase[newID] = self.onBase.pop(key)
        
