#!/usr/bin/python

import tempfile
import const

class BoxScore :
    nameWidth = 110
    playWidth = 20
    baseWidth = 20
    runnersWidth = 4 * baseWidth
    boxWidth = nameWidth + playWidth + runnersWidth
    boxBuffer = 50
    # offset of each base from the end of the name box
    bases = [0,
             playWidth + baseWidth,
             playWidth + 2 * baseWidth,
             playWidth + 3 * baseWidth,
             playWidth + 4 * baseWidth]
    boxHeight = 500
    space = 200
    # awayX is the top left corner of away's box
    # homeX is the top right corner of home's box
    # this lets us lay out the boxes the same, only changing from + to -
    awayX = 50
    awayY = boxBuffer
    homeX = awayX + boxWidth + space + boxWidth
    homeY = awayY
    pitcherBuf = 20
    batterHeight = 17
    curHomeBatter = homeY
    curAwayBatter = awayY
    inning = 1
    lastInningY = awayY

    def __init__(self, outfile) :
        self.imgFile = outfile
        self.imgFileTmp = tempfile.TemporaryFile()
        
    def drawInning(self, inningState):
        f = self.imgFileTmp
        runnersAlready = False
        for i in range(0, inningState.actionCount+1):             
            if i in inningState.atbats:
                batter_num = inningState.atbats[i]
                b = inningState.batters[batter_num]
                e = b.eventAt(i)
                if e.toBase != '':
                    toBase = int(e.toBase[0])
                else:
                    toBase = 0        
                      
                if not runnersAlready:
                    f.write('<g onmouseover="highlight(this)" onmouseout="unhighlight(this)">\n')
                    f.write(' <title>' + b.desc + '</title>')
                runnersAlready = False
                self.writeBatter(inningState.team, b, toBase)
                
                # This is an inning ending 'Runner Out'.
                if b.code == '--':
                    duringAB = True
                    if inningState.team == 'A':
                        self.curAwayBatter -= self.batterHeight
                    elif inningState.team == 'H':
                        self.curHomeBatter -= self.batterHeight
                else:
                    duringAB = False

                for b in inningState.batters:
                    e = b.eventAt(i)
                    if e != None:                                               
                        if e.type_ == 'RunnerAdvance':
                            self.advanceRunner(inningState.team, e, duringAB=duringAB)
                            if duringAB:
                                if inningState.team == 'A':
                                    self.curAwayBatter += self.batterHeight
                                elif inningState.team == 'H':
                                    self.curHomeBatter += self.batterHeight
                f.write('</g>\n')
            else:
                for j in range(i+1, inningState.actionCount+1):
                    if j in inningState.atbats:
                        batter_num = inningState.atbats[j]
                        b = inningState.batters[batter_num]
                        break
                if not runnersAlready:
                    f.write('<g onmouseover="highlight(this)" onmouseout="unhighlight(this)">\n')
                    f.write(' <title>' + b.desc + '</title>')
                runnersAlready = True                    
                for b in inningState.batters:
                    e = b.eventAt(i)
                    if e != None:                                               
                        if e.type_ == 'RunnerAdvance':
                            self.advanceRunner(inningState.team, e, duringAB=True)
        f.write('\n')

        
    def writeLine(self, x1, y1, x2, y2, color='black', sw='1') :
        f = self.imgFileTmp
        f.write(' <line x1="' + str(x1) + '" y1="' + str(y1) + '" x2="' + str(x2) + '" y2="' + str(y2) + '" style="stroke:' + color + '; stroke-width:' + sw + ';"/>\n')

    def writeText(self, txt, x, y, rot=0, rx= -1, ry= -1, anchor=None, size=10, color="black", weight="normal", flip=False, id_=None) :
        f = self.imgFileTmp
        if (flip == True):
            f.write(' <text x="0" y="0" transform="matrix(-1 0 0 1 ' + str(x) + ' ' + str(y) + ')" ')
        else:
            f.write(' <text x="' + str(x) + '" y="' + str(y) + '"')
        if (rot > 0) :
            if rx == -1 :
                rx = x
            if ry == -1 :
                ry = y
            f.write(' transform="rotate(' + str(rot) + ',' + str(rx) + ',' + str(ry) + ')"')
        if anchor :
            f.write(' text-anchor="' + anchor + '"')
        f.write(' fill="' + color + '"')
        f.write(' style="font-family:Arial; font-size: ' + str(size) + 'pt; font-weight:' + weight + ';"')
        if id_ != None:
            f.write(' id="' + id_ + '"')
        f.write('>' + txt + '</text>\n')

    def writeCircle(self, x, y, r, color='black') :
        f = self.imgFileTmp
        f.write(' <circle cx="' + str(x) + '" cy="' + str(y) + '" r="' + str(r) + '" style="stroke:' + color + '; fill:' + color + ';"/>\n')

    def writeX(self, x, y) :
        # Write an X centered at x, y
        x1 = x - 3
        x2 = x + 3
        y1 = y - 3
        y2 = y + 3
        self.writeLine(x1, y1, x2, y2, 'gray')
        self.writeLine(x1, y2, x2, y1, 'gray')

    def startBox(self) :
        f = self.imgFileTmp

        # Start the away box
        x = self.awayX
        y = self.awayY
        w = self.boxWidth
        self.writeLine(x, y, x + w, y, 'gray', '.4')

        # Start the home box
        x = self.homeX
        y = self.homeY
        self.writeLine(x, y, x - w, y, 'gray', '.4')
        
    def endBox(self, homePitchers, awayPitchers) :
        f = self.imgFileTmp
        h = self.curHomeBatter - self.homeY + 2
        
        # Draw Pitchers
        f.write('<g id="hashMarks" style="stroke:black; stroke-width:1;">\n')
        
        # Draw away side hash marks
        x = self.awayX + self.boxWidth + self.pitcherBuf       
        for i, p in enumerate(homePitchers):
            if i == 0:
                self.writeLine(x - 5, self.awayY, x + 5, self.awayY)
            else:
                self.writeLine(x - 5, p[1] + 2, x + 5, p[1] + 2)
        self.writeLine(x - 5, self.awayY + h, x + 5, self.awayY + h)
        
        # Draw home side hash marks
        x = self.homeX - self.boxWidth - self.pitcherBuf
        for i, p in enumerate(awayPitchers):
            if i == 0:
                self.writeLine(x - 5, self.homeY, x + 5, self.homeY)
            else:
                self.writeLine(x - 5, p[1] + 2, x + 5, p[1] + 2)
        #self.writeLine(x - 5, self.homeY + h, x + 5, self.homeY + h)
        self.writeLine(x - 5, self.homeHash, x + 5, self.homeHash)
        
        f.write('</g>\n\n')  
        
        # Draw in the names of the pitchers, homePitchers first
        x = self.awayX + self.boxWidth + self.pitcherBuf
        for i in range(0, len(homePitchers) - 1):
            y = (homePitchers[i][1] + homePitchers[i + 1][1]) / 2
            if i == 0:
                self.writeText(str(homePitchers[i][0]), x - 5, y + 1, rot=90, anchor="middle", id_="homeP" + str(i))
            else:
                self.writeText(str(homePitchers[i][0]), x - 5, y + 2, rot=90, anchor="middle", id_="homeP" + str(i))
        y = (homePitchers[-1][1] + self.awayY + h) / 2
        self.writeText(str(homePitchers[-1][0]), x - 5, y + 1, rot=90, anchor="middle", id_="homeP" + str(len(homePitchers) - 1))            

        # awayPitchers second
        x = self.homeX - self.boxWidth - self.pitcherBuf
        for i in range(0, len(awayPitchers) - 1):
            y = (awayPitchers[i][1] + awayPitchers[i + 1][1]) / 2
            if i == 0:
                self.writeText(str(awayPitchers[i][0]), x + 5, y + 1, rot=270, anchor="middle", id_="awayP" + str(i))
            else:
                self.writeText(str(awayPitchers[i][0]), x + 5, y + 2, rot=270, anchor="middle", id_="awayP" + str(i))
        y = (awayPitchers[-1][1] + self.homeHash) / 2
        self.writeText(str(awayPitchers[-1][0]), x + 5, y + 1, rot=270, anchor="middle", id_="awayP" + str(len(awayPitchers) - 1))      

        f.write('\n</svg>\n')

        # Now that we know the image's height, we can write the SVG header
        img = self.imgFile
        img.write('''<?xml version="1.0" standalone="no"?>

<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">

<svg width="''' + str(self.homeX + 1) + '" height="' + str(h + 2 * self.boxBuffer) + '''" version="1.1"
xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" onload="init(evt)">
''')
        img.write('\n')
        
        # Begin the JavaScript portion of the file
        img.write('<script type="text/ecmascript"><![CDATA[\n')
        # Create the initialization function
        img.write('function init(evt) {\n\n')
        img.write('    // Store the widths of each pitcher\'s name\n')
        img.write('    h_nameWidths = new Array()\n')
        img.write('    for (i=0; i<' + str(len(homePitchers)) + '; i++) {\n')
        img.write('        pText = document.getElementById("homeP"+(i))\n')
        img.write('        h_nameWidths[i] = pText.getComputedTextLength()\n')
        img.write('        //pText.setAttribute("fill","red")\n')        
        img.write('    }\n\n')
        img.write('    a_nameWidths = new Array()\n')
        img.write('    for (i=0; i<' + str(len(awayPitchers)) + '; i++) {\n')
        img.write('        pText = document.getElementById("awayP"+(i))\n')
        img.write('        a_nameWidths[i] = pText.getComputedTextLength()\n')
        img.write('        //pText.setAttribute("fill","red")\n')        
        img.write('    }\n\n')        

        # Create explicit arrays to move data from Python to JS.
        storeString1 = '    h_hashWidths = ['
        storeString2 = '    h_yName = ['
        storeString3 = '    h_yHash = ['
        for i in range(0, len(homePitchers)):
            if i != (len(homePitchers) - 1):
                hashwidth = homePitchers[i + 1][1] - homePitchers[i][1]
                y = (homePitchers[i][1] + homePitchers[i + 1][1]) / 2
                postfix = ', '
            else:
                hashwidth = (self.awayY + h) - homePitchers[i][1]
                y = (homePitchers[-1][1] + self.awayY + h) / 2
                postfix = ']\n'
            storeString1 = storeString1 + str(hashwidth) + postfix
            storeString2 = storeString2 + str(y) + postfix
            storeString3 = storeString3 + str(homePitchers[i][1]) + postfix
        storeString4 = '    a_hashWidths = ['
        storeString5 = '    a_yName = ['
        storeString6 = '    a_yHash = ['
        for i in range(0, len(awayPitchers)):
            if i != (len(awayPitchers) - 1):
                hashwidth = awayPitchers[i + 1][1] - awayPitchers[i][1]
                y = (awayPitchers[i][1] + awayPitchers[i + 1][1]) / 2
                postfix = ', '
            else:
                hashwidth = (self.homeHash) - awayPitchers[i][1]
                y = (awayPitchers[-1][1] + self.homeHash) / 2
                postfix = ']\n'
            storeString4 = storeString4 + str(hashwidth) + postfix
            storeString5 = storeString5 + str(y) + postfix
            storeString6 = storeString6 + str(awayPitchers[i][1]) + postfix
        img.write('    // Create explicit arrays to move data from Python to JS.\n')
        img.write(storeString1 + storeString2 + storeString3 + storeString4 + storeString5 + storeString6)
        
        img.write('\n    drawPitchers(h_nameWidths, h_hashWidths, h_yName, h_yHash, ' + str(len(homePitchers)) + ', "homeP", ' + str(self.awayX + self.boxWidth + self.pitcherBuf) + ', ' + str(self.awayY + h) + ')')
        img.write('\n    drawPitchers(a_nameWidths, a_hashWidths, a_yName, a_yHash, ' + str(len(awayPitchers)) + ', "awayP", ' + str(self.homeX - self.boxWidth - self.pitcherBuf) + ', ' + str(self.homeHash) + ')\n')        
        img.write('}\n\n')
        
        img.write('function drawPitchers(nameWidths, hashWidths, yName, yHash, numP, tagPrefix, xLoc, yBottom) {\n')
        img.write('    levelHeight = 12\n')
        img.write('    curLevel = new Array()\n')
        img.write('    curLevelWidths = new Array()\n\n')
        
        img.write('    // For each pitcher, compare name width and space between the hashes.\n')        
        img.write('    for (i=0; i<numP; i++){\n\n')
        img.write('        // If the name is too long, move it up a level\n')        
        img.write('        if (nameWidths[i]+5 >= hashWidths[i]) {\n')
        img.write('            pText = document.getElementById(tagPrefix+i)\n')
        img.write('            pText.setAttribute("y", yName[i]-levelHeight)\n')
        img.write('            curLevel.push(tagPrefix+i)\n')
        img.write('            curLevelWidths.push(nameWidths[i])\n        }\n\n')
        img.write('        // Otherwise, check to see if the pitcher was in the game a long time.\n')
        img.write('        else if (nameWidths[i]+70 < hashWidths[i]) {\n')
        img.write('            // If he was, draw lines from the top hash to the name and from the bottom.\n')
        img.write('            currentP = document.getElementById(tagPrefix+i)\n')
        img.write('            cY1 = currentP.getAttribute("y") - .5*nameWidths[i]\n')
        img.write('            cY2 = cY1 + nameWidths[i]\n')
        img.write('            svg="http://www.w3.org/2000/svg"\n\n')
        
        img.write('            // Create top or left line.\n')
        img.write('            topLine = document.createElementNS(svg,"line")\n')
        img.write('            topLine.setAttribute("x1", xLoc)\n')
        img.write('            if (i==0)\n')
        img.write('                topLine.setAttribute("y1", yHash[i])\n')
        img.write('            else\n')
        img.write('                topLine.setAttribute("y1", yHash[i]+2)\n')
        img.write('            topLine.setAttribute("x2", xLoc)\n')
        img.write('            topLine.setAttribute("y2", cY1-10)\n\n')
        
        img.write('            // Create bottom or right line.\n')
        img.write('            bottomLine = document.createElementNS(svg,"line")\n')
        img.write('            bottomLine.setAttribute("x1", xLoc)\n')
        img.write('            bottomLine.setAttribute("y1", cY2+10)\n')       
        img.write('            bottomLine.setAttribute("x2", xLoc)\n')
        img.write('            if (i==numP-1)\n')
        img.write('                bottomLine.setAttribute("y2", yBottom)\n')
        img.write('            else\n')
        img.write('                bottomLine.setAttribute("y2", yHash[i+1]+2)\n\n') 
         
        img.write('            // Add both lines to the SVG document.\n')       
        img.write('            hash = document.getElementById("hashMarks")\n')
        img.write('            hash.appendChild(topLine)\n')
        img.write('            hash.appendChild(bottomLine)\n')
        img.write('        }\n')
        img.write('    }\n')   
        
        img.write('''
    // Correct any overlapping pitchers names
    nextLevel = []
    nextLevelWidths = []
    while (curLevel.length > 0) {
        //alert("curLevel.length="+curLevel.length)
        // Copy arrays, to create active or final versions.
        curLevel_f = curLevel.slice(0);
        curLevelWidths_f = curLevelWidths.slice(0);
        // Check for overlapping names in curLevel, skip first name.
        for (i=1; i<curLevel.length; i++){
            currentP = document.getElementById(curLevel[i])
            cY1 = parseFloat(currentP.getAttribute("y")) - .5*curLevelWidths[i]
            // Check only prior pitchers in curLevel for overlap.
            for (j=0; j<i-nextLevel.length; j++){               
                otherP = document.getElementById(curLevel_f[j])
                oY2 = parseFloat(otherP.getAttribute("y")) + .5*curLevelWidths_f[j];
                // Does the left side of the name overlap the right side of the other name?
                if (cY1 <= oY2){
                    // If it does, physically move the name up a level.
                    y = currentP.getAttribute("y")
                    currentP.setAttribute("y", y-levelHeight)
                    // Then remove it from current level array and add to the next level array.
                    nextLevel.push(curLevel_f.splice(i-nextLevel.length,1))
                }
            }
        }
        curLevel = nextLevel.slice(0)
        curLevel_Widths = nextLevelWidths.slice(0)
        nextLevel = []; nextLevelWidths = []
    }
}

lineStyle = []
circleStyle = []

function highlight(src) {
    lineArray = src.getElementsByTagName('line')
    for (i=0; i<lineArray.length; i++){
        lineStyle[i] = lineArray[i].getAttribute("style")
        lineArray[i].setAttribute("style", "stroke:orange; stroke-width:3;")
    }
    circleArray = src.getElementsByTagName('circle')
    for (i=0; i<circleArray.length; i++){
        circleStyle[i] = circleArray[i].getAttribute("style")
        circleArray[i].setAttribute("style", "stroke:orange; fill:orange;")
    }
}

function unhighlight(src) {
    lineArray = src.getElementsByTagName('line')
    for (i=0; i<lineArray.length; i++)
        lineArray[i].setAttribute("style", lineStyle[i])
    circleArray = src.getElementsByTagName('circle')
    for (i=0; i<circleArray.length; i++)
        circleArray[i].setAttribute("style", circleStyle[i])
}

function moveToBottom(src)
{
   src.parentNode.insertBefore(src, src.parentNode.firstChild)
}\n''')

        img.write('\n]]></script>\n\n')
        
        #SWITCH!
        saveTmp = self.imgFileTmp
        self.imgFileTmp = img
        f = img
        
        f.write('<g id="boxOutline">\n')
        
        self.startBox()
        h = self.curHomeBatter - self.homeY + 2

        # End the away box
        x = self.awayX
        y = self.awayY
        m = 1
        w = m * self.boxWidth
        self.writeLine(x, y + h, x + w, y + h, 'gray', '.4')
        self.writeLine(x, y, x, y + h, 'gray', '.4')
        self.writeLine(x + m * self.nameWidth, y, x + m * self.nameWidth, y + h, 'gray', '.4')
        self.writeLine(x + m * (self.nameWidth + self.playWidth), y, x + m * (self.nameWidth + self.playWidth), y + h, 'gray', '.4')
        self.writeLine(x + w, y, x + w, y + h, 'gray', '.4')
        
        x = self.homeX
        y = self.homeY
        m = -1
        w = m * self.boxWidth
        self.writeLine(x, y + h, x + w, y + h, 'gray', '.4')
        self.writeLine(x, y, x, y + h, 'gray', '.4')
        self.writeLine(x + m * self.nameWidth, y, x + m * self.nameWidth, y + h, 'gray', '.4')
        self.writeLine(x + m * (self.nameWidth + self.playWidth), y, x + m * (self.nameWidth + self.playWidth), y + h, 'gray', '.4')
        self.writeLine(x + w, y, x + w, y + h, 'gray', '.4')

        f.write('</g>\n\n')
        
        # SWITCH BACK!
        self.imgFileTmp = saveTmp
        f = self.imgFileTmp        

        # Then we back up to the start of the tempfile and write it's contents to the image file
        f.seek(0)
        img.write(f.read())
        f.close()
    
    def writeBatter(self, team, b, base=0, error=False):
        
        name = b.name
        play = b.code
        result = b.result
        willScore = b.willScore

        if team == "A" :
            x = self.awayX
            m = 1
            self.curAwayBatter += self.batterHeight
            y = self.curAwayBatter
            anchor = "end"
        else :
            x = self.homeX
            m = -1
            self.curHomeBatter += self.batterHeight
            y = self.curHomeBatter
            anchor = "start"

        x += m * self.nameWidth
        if base > 0 :
            x2 = x + m * self.bases[base]

            if willScore == True:
                color = 'black'
                sw = '2'
            else:
                color = 'gray'
                sw = '1'

            if error :
                xmid = (x + x2) / 2
                self.writeLine(x, y + 2, xmid - m * 4, y + 2, color, sw)
                self.writeLine(xmid + m * 4, y + 2, x2, y + 2, color, sw)
            else :
                self.writeLine(x, y + 2, x2, y + 2, color, sw)
                
            if base == 4:
                self.writeCircle(x2, y + 2, 3, color)
            else:
                self.writeCircle(x2, y + 2, 2, color)

            if error :
                self.writeText("E", xmid, y + 4, anchor="middle", size="8")
                
        x += m * (-5)
        self.writeText(name, x, y, anchor=anchor)

        x += m * 15
        weight = "normal"
        if result == const.OUT :
            color = "red"
        elif result == const.HIT :
            color = "green"
            weight = "bold"
        elif result == const.ERROR :
            color = "orange"
        else :
            color = "black"
            
        flip = False
        if play == "Kl":
            play = "K"
            flip = True
            
        self.writeText(play, x, y, anchor="middle", color=color, weight=weight, flip=flip)

    def advanceRunner(self, team, e, error=False, duringAB=False):
        
        fromBase_in = e.fromBase
        toBase_in = e.toBase
        safe = not e.out
        willScore = e.willScore        
        
        toBase = int(toBase_in[0])
        fromBase = int(fromBase_in[0])
        
        if team == "A" :
            x = self.awayX
            y2 = self.curAwayBatter + 2
            m = 1
        else :
            x = self.homeX
            y2 = self.curHomeBatter + 2
            m = -1
        x += m * self.nameWidth

        x1 = x + m * self.bases[fromBase]
        x2 = x + m * self.bases[toBase]
        y1 = y2 - self.batterHeight
        
        if duringAB == True:
            if toBase_in[1] == 'X':
                y1 = y2
                y2 = y1 + self.batterHeight / 2
            if fromBase_in[1] == 'X':
                y1 = y2
        else:
            if fromBase_in[1] == 'X':
                y1 += self.batterHeight / 2
                
        
        if willScore == True:
            color = 'black'
            sw = '2'
        else:
            color = 'gray'
            sw = '1'
        

        if safe :
            if not error :
                self.writeLine(x1, y1, x2, y2, color, sw)
            else :
                xmid = (x1 + x2) / 2
                ymid = (y1 + y2) / 2
                self.writeLine(x1, y1, xmid - m * 3, ymid + 3, color, sw)
                self.writeLine(xmid + m * 3, ymid - 3, x2, y2, color, sw)            
            if toBase == 4:
                self.writeCircle(x2, y2, 3)
            else:
                if willScore == True:
                    self.writeCircle(x2, y2, 2)
                else:
                    self.writeCircle(x2, y2, 2, 'gray')
        else :
            slope = m*float(y2 - y1)/float(x2 - x1)
            if not error :
                if slope != 0:
                    self.writeLine(x1, y1, x2 - m*4/slope, y2 - 4, color, sw)
                else:
                    self.writeLine(x1, y1, x2 - m*4, y2, color, sw)
            else :
                xmid = (x1 + x2) / 2
                ymid = (y1 + y2) / 2
                self.writeLine(x1, y1, xmid - m * 3, ymid + 3, color, sw)
                self.writeLine(xmid + m * 3, ymid - 3, x2, y2, color, sw)
            if slope != 0:             
                self.writeX(x2 - m*4/slope, y2 - 4)
            else:
                self.writeX(x2 - m*4, y2)

        if error :
            self.writeText("E", xmid, ymid + 4, anchor="middle", size=8)
        
    def endInning(self, gameOver=False):
        f = self.imgFileTmp
        self.homeHash = self.curHomeBatter + 2
        if self.curHomeBatter > self.curAwayBatter :
            self.curAwayBatter = self.curHomeBatter
        else :
            self.curHomeBatter = self.curAwayBatter
        y = self.curHomeBatter + 2
        
        f.write('<g onload="moveToBottom(this)">\n')
        if not gameOver:
            self.writeLine(self.awayX + self.nameWidth, y, self.awayX + self.boxWidth, y, 'gray', '.4')
            self.writeLine(self.homeX - self.nameWidth, y, self.homeX - self.boxWidth, y, 'gray', '.4')

        self.writeText(str(self.inning), (self.awayX + self.homeX)/2, (y + self.lastInningY)/2+2.5, anchor="middle", color="blue", weight="bold")
        f.write('</g>\n')
        self.inning = self.inning + 1
        self.lastInningY = y
        f.write('\n')
        
    def getCurBatter(self, team, batters=0):
        if team == "A":
            return self.curAwayBatter + self.batterHeight*batters
        elif team == "H":
            return self.curHomeBatter + self.batterHeight*batters
