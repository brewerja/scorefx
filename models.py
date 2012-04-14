"""Container for the InningState class and the classes it uses."""


class InningState:
    """The class handling all the stored data for each inning."""
    def __init__(self):
        self.actionCount = -1
        # Ordered list of the batters appearing in the inning.
        self.batters = []
        # Dict of pid:Batter pairs of who is on base at a given time.
        self.onBase = {}
        # Dict of pid:Batter pairs of runners to be advanced after the batter.
        self.runnerStack = {}
         # Dict of actionCount:index in self.batters.
        self.atbats = {}

    @staticmethod
    def createBatter(pid, code, result, desc):
        """Serves as the Batter __init__ function interface."""
        return _Batter(pid, code, result, desc)

    def addBatter(self, batterObj, toBase='', out=True, willScore=False):
        """This adds the Batter object to the list of batters in the inning.
           As a result, the actionCount is increased, and an AtBat Event
           object is created and added to the Batter's events list."""
        self.batters.append(batterObj)
        self.actionCount += 1
        while len(batterObj.events) < self.actionCount:
            batterObj.events.append(None)
        fromBase = ''
        e = _Event("AtBat", batterObj.code, fromBase, toBase, out)
        batterObj.events.append(e)
        self.atbats[self.actionCount] = len(self.batters) - 1
        # Whether a player will eventually score.
        batterObj.willScore = willScore
        # The base where the player is currently.
        batterObj.onBase = toBase

        if out == False and toBase != HOME:
            self.onBase[batterObj.pid] = batterObj
        return batterObj

    def advRunners(self, duringAB=False, endAB=False):
        """Once all the runners have been parsed, they can then be advanced.
           It depends whether the runners are advancing during an AB (SB, etc.)
           or as a result of the AB, how they are processed. It also matters
           if the runner's actions end the AB (CS to end inning, etc.)."""
        if duringAB == False:
            # Hold runners who are already on base, but who did not move.
            for key, runnerObj in self.onBase.items():
                if key not in self.runnerStack and self.batters[-1].pid != key:
                    fromBase = runnerObj.onBase
                    if fromBase == FIRST:
                        toBase = FIRST
                    elif fromBase == SECOND or fromBase == SECOND_M:
                        toBase = SECOND
                    elif fromBase == THIRD or fromBase == THIRD_M:
                        toBase = THIRD
                    self.addRunner(runnerObj, toBase)

        if duringAB == True:
            if not endAB:
                self.actionCount += 1
            for key, r in self.runnerStack.items():
                toBase = r.toBase
                if toBase == SECOND:
                    r.toBase = SECOND_M
                elif toBase == THIRD:
                    r.toBase = THIRD_M
                elif toBase == HOME:
                    r.toBase = HOME_M

        for key, r in self.runnerStack.items():
            runnerObj = self.onBase[key]
            runnerObj.advance(self.actionCount, r.code, r.toBase, r.out)
            # If a runner scores or is out on the play, take him off the bases.
            if r.toBase == HOME or r.toBase == HOME_M or \
               r.out == True:
                self.onBase.pop(key)
        self.runnerStack = {}

    def addRunner(self, runnerObj, toBase, code='', out=False):
        """Adds a Runner object for holding until advRunners is called."""
        self.runnerStack[runnerObj.pid] = _Runner(toBase, code, out)

    def pinchRunner(self, base, newID):
        """Replaces the runner on a given base with the id."""
        for pid in self.onBase:
            if self.onBase[pid].onBase == base:
                self.onBase[pid].pid = newID
                self.onBase[newID] = self.onBase.pop(pid)


class _Runner:
    """Simple class to hold runner tag info until the runners are advanced."""
    def __init__(self, toBase, code, out):
        self.toBase = toBase
        self.code = code
        self.out = out


class _Batter():
    """This class is private, accessible only by the InningState class.
       A Batter object is created for all batters in an inning and
       maintains the event information for tracking a batter-runner
       throughout the inning."""
    def __init__(self, pid, code, result, desc, willScore=False):
        self.pid = pid  # from MLB XML
        self.name = pid
        self.code = code  # F7, L8, G6, etc.
        self.result = result  # ERROR, HIT, OTHER, OUT (const.py)
        self.desc = desc  # Description text used for the tooltips.
        # List of events, indexed by actionCount.
        # If no event at an index, use None.
        self.events = []
        self.willScore = willScore
        self.onBase = ''

    def advance(self, actionCount, code, toBase, out):
        """Updates the Batter object of one who has reached base.
           An Event is added to the events list at the actionCount index."""
        fromBase = self.onBase
        self.onBase = toBase
        while len(self.events) < actionCount:
            self.events.append(None)
        if (toBase == HOME or toBase == HOME_M) and out == False:
            self.willScore = True
        e = _Event("RunnerAdvance", code, fromBase, toBase, out)
        self.events.append(e)

    def eventAt(self, actionCount):
        """Returns the Event (if one exists) at the requested actionCount
           index. It will also mark an event's willScore variable True if the
           Batter's willScore is True."""
        if len(self.events) > actionCount:
            ret = self.events[actionCount]
            if ret:
                ret.willScore = self.willScore
        else:
            ret = None
        return ret


class _Event:
    """All outs and on base advancement by a runner are captured for each
       individual Batter. Each Event records the necessary information
       (bases, if an out is made, etc.) for recreating a runner's progress."""
    def __init__(self, type_, code, fromBase, toBase, out):
        # Either "AtBat" (really a plate appearance) or "RunnerAdvance".
        self.type_ = type_
        self.code = code  # this is, for example, "K" or "L7" or "WP"
        self.fromBase = fromBase  # The base where the player starts.
        self.toBase = toBase  # The base where the player ends.
        self.out = out  # whether the player reaches toBase successfully
        self.willScore = False

FIRST = "1B"
SECOND = "2B"
THIRD = "3B"
HOME = "4B"
SECOND_M = "2X"  # 2nd base in the "middle" of a plate appearance.
THIRD_M = "3X"  # ditto
HOME_M = "4X"
