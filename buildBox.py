#!/usr/bin/python

import tempfile
import const

class BoxScore :
    nameWidth = 100
    playWidth = 20
    baseWidth = 20
    runnersWidth = 4 * baseWidth
    boxWidth = nameWidth + playWidth + runnersWidth
    boxBuffer = 50
    # offset of each base from the end of the name box
    bases = [0,
             playWidth + baseWidth,
             playWidth + 2*baseWidth,
             playWidth + 3*baseWidth,
             playWidth + 4*baseWidth]
    boxHeight = 500
    space = 175
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

    def __init__(self, outfile) :
        self.imgFile = outfile
        self.imgFileTmp = tempfile.TemporaryFile()
        
    def writeLine(self, x1, y1, x2, y2) :
        f = self.imgFileTmp
        f.write('<line x1="' + str(x1) + '" y1="' + str(y1) + '" x2="' + str(x2) + '" y2="' + str(y2) + '"/>\n')

    def writeText(self, txt, x, y, rot=0, rx=-1, ry=-1, anchor=None, size=10, color="black", weight="normal", desc=None, flip=False, id=None) :
        f = self.imgFileTmp
        if (flip == True):
            f.write('<text x="0" y="0" transform="matrix(-1 0 0 1 ' + str(x) + ' ' + str(y) + ')" ')
        else:
            f.write('<text x="' + str(x) + '" y="' + str(y) + '"')
        if (rot > 0) :
            if rx == -1 :
                rx = x
            if ry == -1 :
                ry = y
            f.write(' transform="rotate(' + str(rot) + ',' + str(rx) + ',' + str(ry) + ')"')
        if anchor :
            f.write(' text-anchor="' + anchor + '"')
        f.write(' fill="' + color + '"')
        f.write(' style="font-family:Arial; font-size: ' + str(size) + 'pt; font-weight:' + weight +';"')
        if desc != None:
            f.write(' xlink:title="' + desc + '"')
        if id != None:
            f.write(' id="' + id + '"')
        f.write('>' + txt + '</text>\n')

    def writeCircle(self, x, y, r) :
        f = self.imgFileTmp
        f.write('<circle cx="' + str(x) + '" cy="' + str(y) + '" r="' + str(r) + '"/>\n')

    def writeX(self, x, y) :
        # Write an X centered at x, y
        x1 = x - 2
        x2 = x + 2
        y1 = y - 2
        y2 = y + 2
        self.writeLine(x-2, y-2, x+2, y+2)
        self.writeLine(x-2, y+2, x+2, y-2)

    def startBox(self) :
        f = self.imgFileTmp
        f.write('<g stroke="gray" stroke-width="0.1">\n')

        # Start the away box
        x = self.awayX
        y = self.awayY
        w = self.boxWidth
        self.writeLine(x, y, x + w, y)

        # Start the home box
        x = self.homeX
        y = self.homeY
        self.writeLine(x, y, x - w, y)

        f.write('</g>\n\n')
        
    def endBox(self, homePitchers, awayPitchers) :
        f = self.imgFileTmp
        f.write('<g stroke="gray" stroke-width="0.1">\n')

        h = self.curHomeBatter - self.homeY + 2

        # End the away box
        x = self.awayX
        y = self.awayY
        m = 1
        w = m*self.boxWidth
        self.writeLine(x, y + h, x + w, y + h)
        self.writeLine(x, y, x, y + h)
        self.writeLine(x + m*self.nameWidth, y, x + m*self.nameWidth, y + h)
        self.writeLine(x + m*(self.nameWidth + self.playWidth), y, x + m*(self.nameWidth + self.playWidth), y + h)
        self.writeLine(x + w, y, x + w, y + h)
        
        x = self.homeX
        y = self.homeY
        m = -1
        w = m*self.boxWidth
        self.writeLine(x, y + h, x + w, y + h)
        self.writeLine(x, y, x, y + h)
        self.writeLine(x + m*self.nameWidth, y, x + m*self.nameWidth, y + h)
        self.writeLine(x + m*(self.nameWidth + self.playWidth), y, x + m*(self.nameWidth + self.playWidth), y + h)
        self.writeLine(x + w, y, x + w, y + h)
        
        f.write('</g>\n\n')
        
        # Draw Pitchers
        f.write('<g id="hashMarks" stroke="black">\n')
        
        # Draw away side hash marks
        x = self.awayX + self.boxWidth + self.pitcherBuf       
        for i, p in enumerate(homePitchers):
            if i == 0:
                self.writeLine(x-5, self.awayY, x+5, self.awayY)
            else:
                self.writeLine(x-5, p[1]+2, x+5, p[1]+2)
        self.writeLine(x-5, self.awayY+h, x+5, self.awayY+h)
        
        # Draw home side hash marks
        x = self.homeX - self.boxWidth - self.pitcherBuf
        for i, p in enumerate(awayPitchers):
            if i == 0:
                self.writeLine(x-5, self.homeY, x+5, self.homeY)
            else:
                self.writeLine(x-5, p[1]+2, x+5, p[1]+2)
        self.writeLine(x-5, self.homeY+h, x+5, self.homeY+h)
        
        f.write('</g>\n')  
        
        # Draw in the names of the pitchers, homePitchers first
        x = self.awayX + self.boxWidth + self.pitcherBuf
        for i in range(0, len(homePitchers)-1):
            y = (homePitchers[i][1] + homePitchers[i+1][1])/2
            if i == 0:
                self.writeText(str(homePitchers[i][0]), x-5, y+1, rot=90, anchor="middle", id="homeP"+str(i))
            else:
                self.writeText(str(homePitchers[i][0]), x-5, y+2, rot=90, anchor="middle", id="homeP"+str(i))
        y = (homePitchers[-1][1] + self.awayY+h)/2
        self.writeText(str(homePitchers[-1][0]), x-5, y+1, rot=90, anchor="middle", id="homeP"+str(len(homePitchers)-1))            

        # awayPitchers second
        x = self.homeX - self.boxWidth - self.pitcherBuf
        for i in range(0, len(awayPitchers)-1):
            y = (awayPitchers[i][1] + awayPitchers[i+1][1])/2
            if i == 0:
                self.writeText(str(awayPitchers[i][0]), x+5, y+1, rot=270, anchor="middle", id="awayP"+str(i))
            else:
                self.writeText(str(awayPitchers[i][0]), x+5, y+2, rot=270, anchor="middle", id="awayP"+str(i))
        y = (awayPitchers[-1][1] + self.homeY+h)/2
        self.writeText(str(awayPitchers[-1][0]), x+5, y+1, rot=270, anchor="middle", id="awayP"+str(len(awayPitchers)-1))      

        f.write('</svg>\n')

        # Now that we know the image's height, we can write the SVG header
        img = self.imgFile
        img.write('''<?xml version="1.0" standalone="no"?>

<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">

<svg width="''' + str(self.homeX) + '" height="' + str(h + 2*self.boxBuffer) + '''" version="1.1"
xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" onload="init(evt)">
''')
        img.write('\n\n')
        
        # Begin the JavaScript portion of the file
        img.write('<script type="text/ecmascript"><![CDATA[\n')
        # Create the initialization function
        img.write('function init(evt) {\n\n')
        img.write('    // Store the widths of each pitcher\'s name\n')
        img.write('    nameWidths = new Array()\n')
        img.write('    for (i=0; i<'+str(len(homePitchers))+'; i++) {\n')
        img.write('        pText = document.getElementById("homeP"+(i))\n')
        img.write('        nameWidths[i] = pText.getComputedTextLength()\n')
        img.write('        //pText.setAttribute("fill","red")\n')        
        img.write('    }\n\n')

        # Create explicit arrays to move data from Python to JS.
        storeString1 = '    hashWidths = ['
        storeString2 = '    yName = ['
        storeString3 = '    yHash = ['
        for i in range(0, len(homePitchers)):
            if i != (len(homePitchers)-1):
                hashwidth = homePitchers[i+1][1] - homePitchers[i][1]
                y = (homePitchers[i][1] + homePitchers[i+1][1])/2
                postfix = ', '
            else:
                hashwidth = (self.awayY + h) - homePitchers[i][1]
                y = (homePitchers[-1][1] + self.awayY+h)/2
                postfix = ']\n'
            storeString1 = storeString1 + str(hashwidth) + postfix
            storeString2 = storeString2 + str(y) + postfix
            storeString3 = storeString3 + str(homePitchers[i][1]) + postfix
        img.write('    // Create explicit arrays to move data from Python to JS.\n')
        img.write(storeString1)
        img.write(storeString2)
        img.write(storeString3)
        img.write('    curLevel = new Array()\n')
        img.write('    curLevelWidths = new Array()\n\n')
        
        img.write('    // For each pitcher, compare name width and space between the hashes.\n')        
        img.write('    for (i=0; i<'+str(len(homePitchers))+'; i++){\n\n')
        img.write('        // If the name is too long, move it up a level\n')        
        img.write('        if (nameWidths[i]+5 >= hashWidths[i]) {\n')
        img.write('            pText = document.getElementById("homeP"+i)\n')
        img.write('            pText.setAttribute("y", yName[i]-10)\n')
        img.write('            curLevel.push("homeP"+i)\n')
        img.write('            curLevelWidths.push(nameWidths[i])\n        }\n\n')
        img.write('        // Otherwise, check to see if the pitcher was in the game a long time.\n')
        img.write('        else if (nameWidths[i]+75 < hashWidths[i]) {\n')
        
        x = self.awayX + self.boxWidth + self.pitcherBuf
        
        img.write('            // If he was, draw lines from the top hash to the name and from the bottom.\n')
        img.write('            currentP = document.getElementById("homeP"+i)\n')
        img.write('            cY1 = currentP.getAttribute("y") - .5*nameWidths[i]\n')
        img.write('            cY2 = cY1 + nameWidths[i]\n')
        img.write('            svg="http://www.w3.org/2000/svg"\n\n')
        
        img.write('            // Create top or left line.\n')
        img.write('            topLine = document.createElementNS(svg,"line")\n')
        img.write('            topLine.setAttribute("x1",'+str(x)+')\n')
        img.write('            if (i==0)\n')
        img.write('                topLine.setAttribute("y1", yHash[i])\n')
        img.write('            else\n')
        img.write('                topLine.setAttribute("y1", yHash[i]+2)\n')
        img.write('            topLine.setAttribute("x2",'+str(x)+')\n')
        img.write('            topLine.setAttribute("y2", cY1-10)\n\n')
        
        img.write('            // Create bottom or right line.\n')
        img.write('            bottomLine = document.createElementNS(svg,"line")\n')
        img.write('            bottomLine.setAttribute("x1",'+str(x)+')\n')
        img.write('            bottomLine.setAttribute("y1", cY2+10)\n')       
        img.write('            bottomLine.setAttribute("x2",'+str(x)+')\n')
        img.write('            if (i=='+str(len(homePitchers)-1)+')\n')
        img.write('                bottomLine.setAttribute("y2", '+str(self.awayY+h)+')\n')
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
        r=0 // Number of names promoted to the next level.
        // Check for overlapping names in curLevel, skip first name.
        for (i=1; i<curLevel.length; i++){
            currentP = document.getElementById(curLevel[i])
            cY1 = parseFloat(currentP.getAttribute("y")) - .5*curLevelWidths[i]
            // Check only prior pitchers in curLevel for overlap.
            for (j=0; j<i-r; j++){               
                otherP = document.getElementById(curLevel_f[j])
                oY2 = parseFloat(otherP.getAttribute("y")) + .5*curLevelWidths_f[j];
                // Does the left side of the name overlap the right side of the other name?
                if (cY1 <= oY2){
                    // If it does, physically move the name up a level.
                    y = currentP.getAttribute("y")
                    currentP.setAttribute("y", y-10)
                    // Then remove it from current level array and add to the next level array.
                    nextLevel.push(curLevel_f.splice(i-r,1))
                    r++
                }
            }
        }
        curLevel = nextLevel.slice(0)
        curLevel_Widths = nextLevelWidths.slice(0)
        nextLevel = []; nextLevelWidths = []
    }\n''')

        img.write('}\n]]></script>')

        # Then we back up to the start of the tempfile and write it's contents to the image file
        f.seek(0)
        img.write(f.read())
        f.close()

    def writeBox(self, team) :
        f = self.imgFileTmp
        if team == "A" :
            x = self.awayX
            y = self.awayY
            m = 1
        else :
            x = self.homeX
            y = self.homeY
            m = -1

        w = m*self.boxWidth
        h = self.boxHeight
            
        f.write('<g stroke="gray" stroke-width="0.1">\n')
        self.writeLine(x, y, x + w, y)
        self.writeLine(x, y + h, x + w, y + h)
        self.writeLine(x, y, x, y + h)
        self.writeLine(x + m*self.nameWidth, y, x + m*self.nameWidth, y + h)
        self.writeLine(x + m*(self.nameWidth + self.playWidth), y, x + m*(self.nameWidth + self.playWidth), y + h)
        self.writeLine(x + w, y, x + w, y + h)
        f.write('</g>\n\n')

    def writePitcher(self, team, name) :
        f = self.imgFileTmp
        f.write('<g stroke="black">\n')
        w = self.boxWidth
        h = self.boxHeight

        # A team's pitcher abuts the other team's box
        if team == "A" :
            x = self.homeX - self.boxWidth - self.pitcherBuf
            y = self.homeY
            rot = 270
        else :
            x = self.awayX + self.boxWidth + self.pitcherBuf
            y = self.awayY
            rot = 90
        
        self.writeLine(x - 5, y, x + 5, y)
        self.writeLine(x - 5, y + h, x + 5, y + h)
        self.writeLine(x, y, x, y + (h - 100) / 2)
        self.writeLine(x, y + 100 + (h - 100) / 2, x, y + h)
        f.write('</g>\n\n')
        if team == "A" :
            x = x + 5
        else :
            x = x - 5
        self.writeText(name, x, y + h / 2, rot=rot, anchor="middle")
    
    def writeBatter(self, team, name, play, result, desc, base=0, error=False) :
        if not base :
            base = 0
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

        x += m*self.nameWidth
        if base > 0 :
            x2 = x + m * self.bases[base]
            self.imgFileTmp.write('<g stroke="black">\n')
            if error :
                xmid = (x+x2)/2
                self.writeLine(x, y+2, xmid - m*4, y+2)
                self.writeLine(xmid + m*4, y+2, x2, y+2)
            else :
                self.writeLine(x, y+2, x2, y+2)
            self.writeCircle(x2, y+2, 3)
            self.imgFileTmp.write('</g>\n')
            if error :
                self.writeText("E", xmid, y+4, anchor="middle", size="8")
                
        x += m*(-5)
        self.writeText(name, x, y, anchor=anchor)

        x += m*15
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
            
        self.writeText(play, x, y, anchor="middle", color=color, weight=weight, desc=desc, flip=flip)

    def advanceRunner(self, team, fromBase, toBase, safe=True, error=False) :
        if team == "A" :
            x = self.awayX
            y2 = self.curAwayBatter + 2
            m = 1
        else :
            x = self.homeX
            y2 = self.curHomeBatter + 2
            m = -1
        x += m*self.nameWidth
        self.imgFileTmp.write('<g stroke="black">\n')
        x1 = x + m*self.bases[fromBase]
        x2 = x + m*self.bases[toBase]
        y1 = y2 - self.batterHeight
        if not safe :
            x2 -= m*self.baseWidth / 2
            y2 -= self.batterHeight / 2
        if not error :
            self.writeLine(x1, y1, x2, y2)
        else :
            xmid = (x1+x2) / 2
            ymid = (y1+y2) / 2
            self.writeLine(x1, y1, xmid-m*3, ymid+3)
            self.writeLine(xmid+m*3, ymid-3, x2, y2)
        if safe :
            self.writeCircle(x2, y2, 3)
        else :
            self.writeX(x2, y2)
        self.imgFileTmp.write('</g>\n')
        if error :
            self.writeText("E", xmid, ymid+4, anchor="middle", size=8)
            
    def steal(self, team, fromBase, toBase, safe=True) :
        if team == "A" :
            x = self.awayX
            y2 = self.curAwayBatter + 2
            m = 1
        else :
            x = self.homeX
            y2 = self.curHomeBatter + 2
            m = -1
        x += m*self.nameWidth
        self.imgFileTmp.write('<g stroke="black">\n')
        x1 = x + m*self.bases[fromBase]
        x2 = x + m*self.bases[toBase]
        y1 = y2 - self.batterHeight
        if not safe :
            x2 -= m*self.baseWidth / 2
            y2 -= self.batterHeight / 2
        self.writeLine(x1, y1, x1, y1 + self.batterHeight / 2)
        self.writeLine(x2, y2, x2, y1 + self.batterHeight / 2)
        if safe :
            self.writeCircle(x2, y2, 3)
        else :
            self.writeX(x2, y2)
        self.imgFileTmp.write('</g>\n')
        self.writeText("S", (x1+x2)/2, ((y1+y2)/2)+4, anchor="middle", size=8)
        
    def endInning(self) :
        if self.curHomeBatter > self.curAwayBatter :
            self.curAwayBatter = self.curHomeBatter
        else :
            self.curHomeBatter = self.curAwayBatter
        y = self.curHomeBatter + 2
        self.imgFileTmp.write('<g stroke="gray" stroke-width="0.1">\n')
        self.writeLine(self.awayX + self.nameWidth, y, self.awayX + self.boxWidth, y)
        self.writeLine(self.homeX - self.nameWidth, y, self.homeX - self.boxWidth, y)
        self.imgFileTmp.write('</g>\n\n')
    
    def getCurBatter(self, team):
        if team == "A":
            return self.curAwayBatter
        elif team == "H":
            return self.curHomeBatter
        
    def tmp(self) :
        f = self.imgFileTmp

#        f.write('<!-- Away Box -->\n')
#        self.writeBox("A")
#        f.write('<!-- Home Box -->\n')
#        self.writeBox("H")

#        f.write('<!-- Home Pitcher -->\n')
#        self.writePitcher("H", "C.C. Sabathia")
#        f.write('<!-- Away Pitcher -->\n')
#        self.writePitcher("A", "Cliff Lee")

        self.startBox()
        
        self.writeBatter("A", "J. Rollins", "B3")
        self.writeBatter("A", "S. Victorino", "P4")
        self.writeBatter("A", "C. Utley", "W", 1)
        self.writeBatter("A", "R. Howard", "L9", 2)
        self.advanceRunner("A", 1, 3)
        self.writeBatter("A", "J. Werth", "W", 1)
        self.advanceRunner("A", 2, 2)
        self.advanceRunner("A", 3, 3)
        self.writeBatter("A", "R. Ibanez", "G4")

        self.writeBatter("H", "D. Jeter", "K")
        self.writeBatter("H", "J. Damon", "B1")
        self.writeBatter("H", "M. Teixeira", "K")

        self.endInning()

        self.writeBatter("A", "B. Francisco", "G5")
        self.writeBatter("A", "P. Feliz", "G6")
        self.writeBatter("A", "C. Ruiz", "G4")

        self.writeBatter("H", "A. Rodriguez", "K")
        self.writeBatter("H", "J. Posada", "F9", 1)
        self.writeBatter("H", "H. Matsui", "K")
        self.advanceRunner("H", 1, 1)
        self.writeBatter("H", "R. Cano", "F8")
        self.advanceRunner("H", 1, 1)

        self.endInning()

        self.writeBatter("A", "J. Rollins", "F8")
        self.writeBatter("A", "S. Victorino", "G6")
        self.writeBatter("A", "C. Utley", "F", 4)
        self.writeBatter("A", "R. Howard", "K")
        
        self.writeBatter("H", "N. Swisher", "F3")
        self.writeBatter("H", "M. Cabrera", "F4")
        self.writeBatter("H", "D. Jeter", "L9", 2)
        self.writeBatter("H", "J. Damon", "G5")
        self.advanceRunner("H", 2, 2)

        self.endInning()
        
        self.writeBatter("A", "J. Werth", "K")
        self.writeBatter("A", "R. Ibanez", "K")
        self.writeBatter("A", "B. Francisco", "F8")

        self.writeBatter("H", "M. Teixeira", "K")
        self.writeBatter("H", "A. Rodriguez", "K")
        self.writeBatter("H", "J. Posada", "K")

        self.endInning()
        
        self.writeBatter("A", "P. Feliz", "K")
        self.writeBatter("A", "C. Ruiz", "G6")
        self.writeBatter("A", "J. Rollins", "F5")

        self.writeBatter("H", "H. Matsui", "G8", 1)
        self.writeBatter("H", "R. Cano", "L6")
        self.advanceRunner("H", 1, 2, safe=False)
        self.writeBatter("H", "N. Swisher", "F9")

        self.endInning()
        
        self.writeBatter("A", "S. Victorino", "F6")
        self.writeBatter("A", "C. Utley", "F", 4)
        self.writeBatter("A", "R. Howard", "K")
        self.writeBatter("A", "J. Werth", "G9", 1)
        self.writeBatter("A", "R. Ibanez", "K")
        self.advanceRunner("A", 1, 1)

        self.writeBatter("H", "M. Cabrera", "F9")
        self.writeBatter("H", "D. Jeter", "G8", 1)
        self.writeBatter("H", "J. Damon", "F1")
        self.advanceRunner("H", 1, 1)
        self.writeBatter("H", "M. Teixeira", "G4")      
        self.advanceRunner("H", 1, 2, safe=False)

        self.endInning()
        
        self.writeBatter("A", "B. Francisco", "W", 1)
        self.writeBatter("A", "P. Feliz", "G5")
        self.advanceRunner("A", 1, 2, safe=False)
        self.writeBatter("A", "C. Ruiz", "G5")

        self.writeBatter("H", "A. Rodriguez", "K")
        self.writeBatter("H", "J. Posada", "K")
        self.writeBatter("H", "H. Matsui", "G8", 1)

        self.endInning()
        
        self.writeBatter("A", "J. Rollins", "W", 1)
        self.writeBatter("A", "S. Victorino", "W", 1)
        self.steal("A", 1, 2)
        self.writeBatter("A", "C. Utley", "K")
        self.advanceRunner("A", 1, 1)
        self.advanceRunner("A", 2, 2)
        self.writeBatter("A", "R. Howard", "F9")
        self.advanceRunner("A", 1, 1)
        self.advanceRunner("A", 2, 2)
        self.writeBatter("A", "J. Werth", "W", 1)
        self.advanceRunner("A", 1, 2)
        self.advanceRunner("A", 2, 3)
        self.writeBatter("A", "R. Ibanez", "G8", 1)
        self.advanceRunner("A", 2, 4)
        self.advanceRunner("A", 3, 4)
        self.advanceRunner("A", 1, 2)
        self.writeBatter("A", "B. Francisco", "G5")
        self.advanceRunner("A", 1, 1)
        self.advanceRunner("A", 2, 2)

        self.writeBatter("H", "R. Cano", "G1")
        self.writeBatter("H", "N. Swisher", "K")
        self.writeBatter("H", "M. Cabrera", "F8")

        self.endInning()
        
        self.writeBatter("A", "P. Feliz", "F4")
        self.writeBatter("A", "C. Ruiz", "F8", 2)
        self.writeBatter("A", "J. Rollins", "G5", 1)
        self.advanceRunner("A", 2, 3)
        self.writeBatter("A", "S. Victorino", "G9", 1)
        self.advanceRunner("A", 1, 2)
        self.advanceRunner("A", 3, 4)
        self.writeBatter("A", "C. Utley", "F8")
        self.advanceRunner("A", 1, 1)
        self.advanceRunner("A", 2, 3)
        self.writeBatter("A", "R. Howard", "F9")
        self.advanceRunner("A", 3, 4)
        self.advanceRunner("A", 1, 3, safe=False)
        
        self.writeBatter("H", "D. Jeter", "F8", 1)
        self.writeBatter("H", "J. Damon", "L9", 1)
        self.advanceRunner("H", 1, 2)
        self.writeBatter("H", "M. Teixeira", "G4", 2, error=True)      
        self.advanceRunner("H", 1, 2, safe=False)
        self.advanceRunner("H", 2, 4, error=True)
        self.writeBatter("H", "A. Rodriguez", "K")
        self.advanceRunner("H", 2, 2)
        self.writeBatter("H", "J. Posada", "K")
        self.advanceRunner("H", 2, 2)

        self.endInning()

        self.endBox()


if __name__ == "__main__" :
    f = open("box.svg", "w")
    t = BoxScore(f)
    t.tmp()
    f.close()
