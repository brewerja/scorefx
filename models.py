from google.appengine.ext import db

class Player(db.Model) :
    pid = db.StringProperty()
    first = db.StringProperty()
    last = db.StringProperty()
    
class Batter():
    def __init__(self, id, code, result):
        self.id = id # from MLB XML
        self.code = code
        self.result = result
        self.events = [] # list of events, indexed by actionCount.  if no event @ an index, use None
 
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

class Base:
    FIRST = "1B"
    SECOND = "2B"
    THIRD = "3B"
    HOME = "4B"
    SECOND_M = "2X" # 2nd base in the "middle" of a plate appearance i.e. from a stolen base
    THIRD_M = "3X" # ditto
    HOME_M = "4X"

class InningState:
    def __init__(self):
        self.actionCount = -1
        self.batters = []
        self.onBase = {}
        self.runnerStack = {}
        self.atbats = []

    def createBatter(self, id, code, result):
        return Batter(id, code, result)

    def addBatter(self, batterObj, toBase='', out=True, willScore=False):
        self.batters.append(batterObj)
        self.actionCount += 1
        while len(batterObj.events) < self.actionCount:
            batterObj.events.append(None)
        fromBase = ''
        batterObj.events.append(Event("AtBat", batterObj.code, fromBase, toBase, out))
        self.atbats.append(self.actionCount)
        batterObj.willScore = willScore # whether a player will eventually score.  will need to refine this to handle batting around
        batterObj.onBase = toBase # the base where the player is currently.  use the advance() function to change

        events = batterObj.events
        if events[len(events)-1].out == False:
            self.onBase[batterObj.id] = batterObj
        return batterObj
    
    def clearRunners(self, duringAB=False):
        if duringAB == True:
            for key, val in self.runnerStack.items():
                toBase = self.runnerStack[key][1]
                if toBase == Base.SECOND:
                    self.runnerStack[key][1] = Base.SECOND_M
                elif toBase == Base.THIRD:
                    self.runnerStack[key][1] = Base.THIRD_M
                elif toBase == Base.HOME:
                    self.runnerStack[key][1] = Base.HOME_M
        
        for key, val in self.runnerStack.items():
            code = val[0]
            toBase = val[1]
            out = val[2]
            self.advRunner(self.onBase[key], toBase, code, out, True)
        self.runnerStack = {}
    
    def advRunner(self, runnerObj, toBase, code='', out=False, clearStack=False):
        if clearStack == True:
            runnerObj.advance(self.actionCount, code, toBase, out)
            # If the runner is out on the basepaths or scores, he's no longer on base.
            if out == True or (out == False and toBase == '4B'):
                self.onBase.pop(runnerObj.id)
        else:
            self.runnerStack[runnerObj.id] = [code, toBase, out]
    
    def pinchRunner(self, base, newID):
        for key, runnerObj in self.onBase.items():
            if self.onBase[key].onBase == base:
                self.onBase[key].id = newID
                self.onBase[newID] = self.onBase.pop(key)
        
