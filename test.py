from models import Batter, Base, InningState
import const

def onBaseState():
    baseState = [None, None, None]
    for key, b in innS.onBase.items():
        bb = b.onBase
        if bb == Base.FIRST:
            baseState[0] = b.id
        elif bb == Base.SECOND:
            baseState[1] = b.id
        elif bb == Base.THIRD:
            baseState[2] = b.id
    print '1B: ' + str(baseState[0])
    print '2B: ' + str(baseState[1])
    print '3B: ' + str(baseState[2])
    print '---'


innS = InningState()
onBaseState()
b1 = innS.addBatter(innS.createBatter(111, 'F6', const.HIT), Base.FIRST, out=False)
onBaseState()
innS.advRunner(b1, Base.SECOND, 'SB')
onBaseState()
b2 = innS.addBatter(innS.createBatter(222, 'K', const.OUT))
onBaseState()
b3 = innS.addBatter(innS.createBatter(333, 'F7', const.HIT), Base.SECOND, out=False)
innS.advRunner(b1, Base.HOME, out=False)
onBaseState()
innS.pinchRunner(Base.SECOND, 'newid')
onBaseState()
innS.advRunner(b3, Base.THIRD, 'CS', out=True)
onBaseState()
innS.pinchRunner

print '----------'
for b in innS.batters:
    for e in b.events:
        if e == None:
            print 'None'
        else:
            print e.code + ':' + e.type + ', ' + e.fromBase + '-->' + e.toBase + ' out? ' + str(e.out)
    print '----------'

for i in range(0, innS.actionCount+1):
    string = str(i) + ': '
    for b in innS.batters:
        e = b.eventAt(i)
        if e != None:
            string += e.type + ' '
    print string
    string = ''

for i in range(0, innS.actionCount+1):
    if b1.eventAt(i):
        print str(b1.eventAt(i).willScore)
