#!/usr/bin/python

import tempfile

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
    space = 100
    # awayX is the top left corner of away's box
    # homeX is the top right corner of home's box
    # this lets us lay out the boxes the same, only changing from + to -
    awayX = 50
    awayY = boxBuffer
    homeX = awayX + boxWidth + space + boxWidth
    homeY = awayY
    pitcherBuf = 10
    batterHeight = 17
    curHomeBatter = homeY
    curAwayBatter = awayY

    def __init__(self, outfile) :
        self.imgFile = outfile
        self.imgFileTmp = tempfile.TemporaryFile()
        
    def writeLine(self, x1, y1, x2, y2) :
        f = self.imgFileTmp
        f.write('<line x1="' + str(x1) + '" y1="' + str(y1) + '" x2="' + str(x2) + '" y2="' + str(y2) + '"/>\n')

    def writeText(self, txt, x, y, rot=0, rx=-1, ry=-1, anchor=None, size=10) :
        f = self.imgFileTmp
        f.write('<text x="' + str(x) + '" y="' + str(y) + '"')
        if (rot > 0) :
            if rx == -1 :
                rx = x
            if ry == -1 :
                ry = y
            f.write(' transform="rotate(' + str(rot) + ',' + str(rx) + ',' + str(ry) + ')"')
        if anchor :
            f.write(' text-anchor="' + anchor + '"')
        f.write(' style="font-family:Arial; font-size: ' + str(size) + 'pt;">' + txt + '</text>\n')

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
        
    def endBox(self) :
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
        f.write('</svg>\n')

        # Now that we know the image's height, we can write the SVG header
        img = self.imgFile
        img.write('''<?xml version="1.0" standalone="no"?>

<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">

<svg width="''' + str(self.homeX) + '" height="' + str(h + 2*self.boxBuffer) + '''" version="1.1"
xmlns="http://www.w3.org/2000/svg">
''')
        img.write('\n\n')
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
    
    def writeBatter(self, team, name, play, base=0, error=False) :
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
        self.writeText(play, x, y, anchor="middle")

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
        
    def tmp(self) :
        f = self.imgFileTmp

#        f.write('<!-- Away Box -->\n')
#        self.writeBox("A")
#        f.write('<!-- Home Box -->\n')
#        self.writeBox("H")

#        f.write('<!-- Home Pitcher -->\n')
#        self.writePitcher("H", "CC Sabbathia")
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
