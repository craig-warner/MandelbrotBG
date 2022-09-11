#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
PUMA Perf
author: Craig Warner
"""

import os
import platform
import sys
import argparse
import random
from PyQt5 import QtCore, QtGui, QtWidgets
import json
from pprint import pprint
import helpform
#import qrc_resources
from array import *
from time import sleep
from struct import pack
# import libc
from ctypes import CDLL


# Issue:
#
# Enhancements:

# Input File Format
#
#

#
# Functions
#

def HTMLColorNumber(colorNum):
    colorTable = [0x000000, 0xFFFFFF, 0x1ABC9C, 0xA3E4D7,
#                     MVMU0->MVMU3
                      0xE8DAEF, 0xBB8FCE, 0x884EA0, 0x633974,
#                     VU,SU,
                      0xB9770E, 0xB7950B,
#                     LD,LDW,ST,STW->MVMU3
                      0x717D7E, 0xD5DBDB, 0xF39C12, 0xF5CBA7,
#                     Even Interval,Odd Interval
                      0xDC7633,0x3498DB]

    return(colorTable[colorNum])


class MandelCalc:
  threshold = 1000.0
  MaxA = 2.0
  MinA = -1.0
  MaxDi = 1.5
  MinDi = -1.5
  AperDot = 1.0
  DiperDot = 1.0
  def SetRange(self,MinX,MinY,MaxX,MaxY,XDots,YDots):
    self.MinA = MinX
    self.MaxA = MaxX
    self.MinDi = MinY
    self.MaxDi = MaxY
    self.AperDot = (MaxX-MinX)/XDots
    self.DiperDot = (MaxY-MinY)/YDots
  def GetColor(self,c,di,numIters):
    for i in range(0,numIters):
      if i == 0:
        a=c
        bi=di
      else:
        newA=a*a-bi*bi-c
        newBi=2*a*bi-di
        a=newA
        bi=newBi
      if a>self.threshold:
        return i
    return 0
  def GetA(self,xDot):
    a = self.AperDot*xDot + self.MinA
    return a
  def GetDi(self,yDot):
    di = self.MaxDi - self.DiperDot*yDot
    return di
  def Inter2Color(self,numBits,i):
    if numBits == 4:
      str = "#%03x" % (i&0xfff)
      return str
    if numBits == 5:
      str = "#%04x" % (i&0x7fff)
      return str
    if numBits == 6:
      str = "#%05x" % (i&0x3ffff)
      return str
    elif numBits == 8:
      str = "#%06x" % (i&0xffffff)
      return str
    elif numBits == 12:
      str = "#%09x" & (i&0xfffffffff)
      return str
    else:
      print ("Error 1")
      raise Exception("Not a Valid Color Width")

  def ColorDot(self,numBits,x,y):
    a = self.GetA(x)
    di = self.GetDi(y)
    numIters = 1<<(numBits*3)
    colorI = self.GetColor(a,di,numIters)
    colorStr = self.Inter2Color(numBits,colorI)
    return(colorStr)

class Bitmap():
  def __init__(s, width, height):
    s._bfType = 19778 # Bitmap signature
    s._bfReserved1 = 0
    s._bfReserved2 = 0
    s._bcPlanes = 1
    s._bcSize = 12
    s._bcBitCount = 24
    s._bfOffBits = 26
    s._bcWidth = width
    s._bcHeight = height
    s._bfSize = 26+s._bcWidth*3*s._bcHeight
    s.clear()


  def clear(s):
    s._graphics = [(0,0,0)]*s._bcWidth*s._bcHeight


  def setPixel(s, x, y, color):
    if isinstance(color, tuple):
      if x<0 or y<0 or x>s._bcWidth-1 or y>s._bcHeight-1:
        raise ValueError('Coords out of range')
      if len(color) != 3:
        raise ValueError('Color must be a tuple of 3 elems')
      s._graphics[y*s._bcWidth+x] = (color[2], color[1], color[0])
    else:
      raise ValueError('Color must be a tuple of 3 elems')


  def write(s, file):
    with open(file, 'wb') as f:
      f.write(pack('<HLHHL',
                   s._bfType,
                   s._bfSize,
                   s._bfReserved1,
                   s._bfReserved2,
                   s._bfOffBits)) # Writing BITMAPFILEHEADER
      f.write(pack('<LHHHH',
                   s._bcSize,
                   s._bcWidth,
                   s._bcHeight,
                   s._bcPlanes,
                   s._bcBitCount)) # Writing BITMAPINFO
      for px in s._graphics:
        f.write(pack('<BBB', *px))
      for i in range((4 - ((s._bcWidth*3) % 4)) % 4):
        f.write(pack('B', 0))



#
# Functions
#
class MandelbrotBackground(QtWidgets.QMainWindow):

    def __init__(self):
        super(MandelbrotBackground, self).__init__()
        self.dirty = True
        self.border= 10

#        self.positionerData = []
#        for y in range(0,40):
#            row = []
#            for x in range(0,40):
#                row.append(0x000000)
#            self.positionerData.append(row)

#       Arrangement Settings
#        self.bg_arrangement = json.load(open("eight.json"))
#        self.bg_arrangement = json.load(open("eight_r.json"))
#        self.bg_arrangement = json.load(open("eleven.json"))
        self.bg_arrangement = json.load(open("fourteen.json"))
#        self.bg_arrangement = json.load(open("story.json"))

        self.initUI()
        fileOpenAction = self.createAction("&Open...", self.fileOpen,
                                           QtGui.QKeySequence.Open, "fileopen",
                                           "Open an existing file")
        fileQuitAction = self.createAction( "&Quit", self.fileClose,
                 "Ctrl+Q", "filequit", "Close the application")
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenuActions = (fileOpenAction,None,fileQuitAction)
        #self.fileQuitActions(self.fileMenu, (fileQuitAction, fileQuitAction))
        #self.connect(self.fileMenu, QtCore.SIGNAL("aboutToShow()"),
        #             self.updateFileMenu)

        helpAboutAction = self.createAction(
            "&About Mandelbrot Background Drawer", self.helpAbout)
        helpHelpAction = self.createAction(
            "&Help", self.helpHelp, QtGui.QKeySequence.HelpContents)
        helpMenu = self.menuBar().addMenu("&Help")
        self.addActions(helpMenu, (helpAboutAction, helpHelpAction))

        fileToolbar = self.addToolBar("File")
        fileToolbar.setObjectName("FileToolBar")
        self.addActions(fileToolbar, (fileOpenAction,fileQuitAction))

        settings = QtCore.QSettings()
        self.filename = None
        self.recentFiles = settings.value("RecentFiles") or []

        self.updateFileMenu()
        self.listWidget = QtWidgets.QListWidget()

        self.BoardWidth = 1024
        self.BoardHeight = 768
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.isLoaded = False

        self.settingPath = False
        self.settingPathPos = 1


    def createAction(self, text, slot=None, shortcut=None, icon=None, tip=None,
                     checkable=False, signal="triggered()"):
        action = QtWidgets.QAction(text, self)
        if icon is not None:
            action.setIcon(QtGui.QIcon("images/{}.png".format(icon)))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        #if slot is not None:
        #    self.connect(action, QtCore.SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action

    def addActions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def fileOpen(self):
        dir = (os.path.dirname(self.filename)
               if self.filename is not None else ".")
        formats = (["*.json"])
        fname = QtGui.QFileDialog.getOpenFileName(self,
                        "Mandelbackground ", dir,
                        "JSON files ({})".format(" ".join(formats)))
        if fname:
            print (fname)
            self.loadFile(fname)

    def fileClose(self):
        QtCore.QCoreApplication.instance().quit()

    def loadFile(self, fname=None):
        if fname is None:
            action = self.sender()
            if isinstance(action, QtGui.QAction):
                fname = action.data()
            else:
                return
        if fname:
            self.filename = None
            self.loadData(fname)
        self.drawBackGround()

    def loadInitialFile(self):
        settings = QtCore.QSettings()
        fname = settings.value("LastFile")
        if fname and QtCore.QFile.exists(fname):
            self.loadFile(fname)

    def updateFileMenu(self):
        self.fileMenu.clear()
        self.addActions(self.fileMenu, self.fileMenuActions[:-1])
        current = self.filename
        self.recentFiles = []
        for fname in self.recentFiles:
            if fname != current and QtCore.QFile.exists(fname):
                recentFiles.append(fname)
        if self.recentFiles:
            self.fileMenu.addSeparator()
            for i, fname in enumerate(recentFiles):
                action = QtGui.QAction(QtGui.QIcon(":/icon.png"),
                                       "&{} {}".format(i + 1, QtCore.QFileInfo(
                                           fname).fileName()), self)
                action.setData(fname)
                self.connect(action, QtCore.SIGNAL("triggered()"),
                             self.loadFile)
                self.fileMenu.addAction(action)
                self.fileMenu.addSeparator()
                self.fileMenu.addAction(self.fileMenuActions[-1])

    def addRecentFile(self, fname):
        if fname is None:
            return
        if fname not in self.recentFiles:
            self.recentFiles = [fname] + self.recentFiles[:8]

    def helpAbout(self):
        QtGui.QMessageBox.about(self, "Mandelbrot Background Drawer",
          """<b>Mandelbrot Background Drawer</b> v{1.0}
      <p>Copyright &copy; 2022 Craig Warner
      All rights reserved.
      <p>This application can be used to display
      Create Mandelbrot backgrounds.  </p>""")

    def helpHelp(self):
        form = helpform.HelpForm("help/index.html", self)
        form.show()

    def loadData(self,fname):
        self.settings_json = json.load(open(fname))

    def initUI(self):
        self.wid = QtWidgets.QWidget(self)
        self.setCentralWidget(self.wid)
        self.setGeometry(0,100,1024,768)
        self.setWindowTitle('Mandelbrot Background Drawer')
        self.addBody()
        self.show()

    def center(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

    def updateStatus(self, message):
        self.statusBar().showMessage(message, 5000)
        self.listWidget.addItem(message)
        if self.filename:
            self.setWindowTitle(
                "Mandelbrot Background - {}[*]".format(os.path.basename(str(self.filename))))
        elif not self.image.isNull():
            self.setWindowTitle("Mandelbrot Background - Unnamed[*]")
        else:
            self.setWindowTitle("Mandelbrot Background [*]")
        self.grid.reDraw()


    def addBody(self):
        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.setGeometry(QtCore.QRect(0, 0, 800, 400))
        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.setGeometry(QtCore.QRect(0, 0, 200, 200))
        vbox = QtWidgets.QVBoxLayout()

        # Positioner
        self.positionerWidget = PositionerWidget(self.bg_arrangement["zoom"])

        title= QtWidgets.QLabel()
        title.setText("Positioner")
        title.setFont(QtGui.QFont('SansSerif', 10))

        scroll = QtWidgets.QScrollArea()
        scroll.setGeometry(QtCore.QRect(0, 0, 400, 400))
        scroll.setWidget(self.positionerWidget)
        #scroll.setWidgetResizable(True)
        scroll.setFixedWidth(425)
        scroll.setFixedHeight(425)
        scroll.ensureVisible(0,0,100,100)

        vbox_positioner = QtWidgets.QVBoxLayout()
        vbox_positioner.setGeometry(QtCore.QRect(0, 0, 400, 400))
        vbox_positioner.addWidget(title)
        vbox_positioner.addWidget(scroll)
#        vbox_positioner.addWidget(self.positionerWidget)

        hbox1.addLayout(vbox_positioner)

        # Settings
        self.settings_vbox = QtWidgets.QVBoxLayout()
        self.settings_vbox.setGeometry(QtCore.QRect(0, 0, 400, 400))

        title= QtWidgets.QLabel()
        title.setText("Zoom Settings")
        title.setFont(QtGui.QFont('SansSerif', 10))

        self.pathWidget = PathWidget(self.bg_arrangement["num_images"])

        self.scroll2 = QtWidgets.QScrollArea()
        self.scroll2.setGeometry(QtCore.QRect(0, 0, 400, 300))
        self.scroll2.setWidget(self.pathWidget)
        self.scroll2.ensureVisible(0,0,100,100)

        reset_path_button = QtWidgets.QPushButton('Reset Path', self)
        reset_path_button.setCheckable(True)
        reset_path_button.clicked[bool].connect(self.resetPath)
        set_path_button = QtWidgets.QPushButton('Set Path', self)
        set_path_button.setCheckable(True)
        set_path_button.clicked[bool].connect(self.setPath)

        self.settings_vbox.addWidget(title)
        self.settings_vbox.addWidget(self.scroll2)
        self.settings_vbox.addWidget(reset_path_button)
        self.settings_vbox.addWidget(set_path_button)
        hbox1.addLayout(self.settings_vbox)

        # Preview
        self.bg = BGWidget(
            self.bg_arrangement["width"],
            self.bg_arrangement["height"],
            self.bg_arrangement["bits_per_color"])

        title= QtWidgets.QLabel()
        title.setText("Preview")
        title.setFont(QtGui.QFont('SansSerif', 10))

        scroll = QtWidgets.QScrollArea()
        #scroll.setGeometry(QtCore.QRect(0, 0, 400, 400))
        scroll.setWidget(self.bg)
        #scroll.setWidgetResizable(True)
        scroll.setFixedWidth(800)
        scroll.setFixedHeight(200)
        scroll.ensureVisible(0,0,100,100)

        vboxPreview = QtWidgets.QVBoxLayout()
        vboxPreview.addWidget(title)

        draw_button = QtWidgets.QPushButton('Draw', self)
        draw_button.setCheckable(True)
        draw_button.clicked[bool].connect(self.drawBackground)

        vboxPreview.addWidget(draw_button)

        hbox2.addLayout(vboxPreview)
        hbox2.addWidget(scroll)

        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)

        self.wid.setLayout(vbox)

    def clearPositioner(self):
        for x in range(0,40):
            for y in range(0,40):
                self.postionerData[x][y] = "#000000"


    def center(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

    def updateStatus(self, message):
        self.statusBar().showMessage(message, 5000)
        self.listWidget.addItem(message)
        if self.filename:
            self.setWindowTitle(
                "PUMA Performace Viewer - {}[*]".format(os.path.basename(str(self.filename))))
        elif not self.image.isNull():
            self.setWindowTitle("Mandelbrot Background - Unnamed[*]")
        else:
            self.setWindowTitle("Mandelbrot Background [*]")
        self.grid.reDraw()

    def closeEvent(self, event):
        QtCore.QCoreApplication.instance().quit()

    def hSliderChange(self,value):
        print("H:",value)

    def vSliderChange(self,value):
        print("V:",value)

    def drawBackground(self):
        print("Coloring BG")
    # "num_images": 8,
    # "pixels_per_unit": 120,
    # "zoom": 0.1,
    # "images": [
    #   {
    #    "side_size": 2,
    #    "bg_x": 0,
    #    "bg_y": 0,
    #   }
        for i in range(0,self.bg_arrangement["num_images"]):
            px_per_side = self.bg_arrangement["images"][i]["side_size"] * self.bg_arrangement["pixels_per_unit"]
            self.bg.color(
                self.pathWidget.getMinX(i),
                self.pathWidget.getMaxX(i),
                self.pathWidget.getMinY(i),
                self.pathWidget.getMaxY(i),
                self.bg_arrangement["images"][i]["bg_x"],
                self.bg_arrangement["images"][i]["bg_y"],
                px_per_side)
            print("Image %d colored: x: %d y %d" % (i,
                self.bg_arrangement["images"][i]["bg_x"],
                self.bg_arrangement["images"][i]["bg_y"]))
        self.bg.save(self.bg_arrangement["filename"],self.bg_arrangement["rgb"],self.bg_arrangement["bits_per_color"],
                self.bg_arrangement["brightness_shift"])

    def resetPath(self):
        self.pathWidget.resetFrame()
        self.settingPathPos = 1
        print("Reset Path")
        self.pathWidget.repaint()
        self.repaint()

    def setPath(self):
        self.pathWidget.resetFrame()
        if(self.positionerWidget.isSetPoint() == True):
            new_min_x =self.positionerWidget.getSetPointX()
            new_min_y =self.positionerWidget.getSetPointY()
            new_len =self.positionerWidget.getSetPointLength()
            new_max_x = new_min_x + new_len
            new_max_y = new_min_y + new_len
            self.pathWidget.setFrame(self.settingPathPos,new_min_x,new_max_x,new_min_y,new_max_y)
            self.settingPathPos = self.settingPathPos + 1
        print("Set Path : %d" % self.settingPathPos)
        self.pathWidget.repaint()
        self.repaint()

class PositionerWidget(QtWidgets.QWidget):
    def __init__(self,zoom):
        super(PositionerWidget, self).__init__()
        self.MyMandelCalc = MandelCalc()
        self.MyMandelCalc.SetRange(-1.0,-1.5,2.0,1.5,400,400)
        self.min_real_x = -1.0
        self.max_real_x = 2.0
        self.min_real_y = -1.5
        self.max_real_y = 1.5
        self.real_len = 3.0
        self.real_zoom = zoom

        self.setGeometry(QtCore.QRect(0, 0, 400, 400))

        self.positionerData = []
        for y in range(0,40):
            row = []
            for x in range(0,40):
                row.append(0x000000)
            self.positionerData.append(row)

        self.color()

        self.point_set = False
        self.point_set_x = 0
        self.point_set_y = 0
        print("Positioner Widget")

    def paintEvent(self, e):
        self.color()
        qp = QtGui.QPainter()
        qp.begin(self)
        for x in range(0,40):
            for y in range(0,40):
                x1 = x*10 + 10
                y1 = y*10 + 10
                self.drawRect(qp,x1,y1,10,10,self.positionerData[x][y])
        print ("positioner paint event")

    def drawRect(self,painter,x,y,width,height,colornum):
        color = QtGui.QColor(colornum)
        painter.fillRect(x , y , width, height, color)

    def color(self):
        for x in range(0,40):
            for y in range(0,40):
                x1 = x*10 + 10
                y1 = y*10 + 10
                colorNum = self.MyMandelCalc.ColorDot(4,x1,y1)
                self.positionerData[x][y] = colorNum

    def mousePressEvent(self,event):
        self.point_set = True
        self.point_set_x = event.pos().x()
        self.point_set_y = event.pos().y()
        print("x: %d y: %d " % (event.pos().x(),event.pos().y()))
        center_x = (self.min_real_x + (float(self.point_set_x)/400.0) * self.real_len)
        center_y  = (self.max_real_y - (float(self.point_set_y)/400.0) * self.real_len)
        self.real_len = self.real_len * self.real_zoom
        self.min_real_x = center_x - self.real_len/2.0
        self.max_real_y = center_y + self.real_len/2.0
        self.max_real_x = self.min_real_x + self.real_len
        self.min_real_y = self.max_real_y - self.real_len
        self.MyMandelCalc.SetRange(self.min_real_x,self.min_real_y,self.max_real_x,self.max_real_y,400,400)
        self.repaint()

    def isSetPoint(self):
        if(self.point_set == True):
            self.point_set = False
            return(True)
        else:
            return(False)

    def getSetPointX(self):
    #    self.min_real_x = (self.min_real_x + (self.point_set_x/400) * self.real_len)
        print ("getSetPointX %5.3f" % self.min_real_x)
        return(self.min_real_x)

    def getSetPointY(self):
    #    self.min_real_y  = (self.min_real_y + (self.point_set_y/400) * self.real_len)
        return (self.min_real_y)

    def getSetPointLength(self):
    #    self.real_len = self.real_len * self.real_zoom
        return(self.real_len)


class PathWidget(QtWidgets.QWidget):
    def __init__(self,num_images):
        super(PathWidget, self).__init__()
        self.num_images = num_images
        self.setGeometry(QtCore.QRect(0, 0, 800, 400))
        self.minx = []
        self.maxx = []
        self.miny = []
        self.maxy = []
        self.text = ""
        for x in range(0,num_images):
            self.minx.append(0)
            self.maxx.append(0)
            self.miny.append(0)
            self.maxy.append(0)
        self.resetFrame()
        print("Path Widget")

    def resetFrame(self):
        self.minx[0]  = -1.0
        self.maxx[0]  = 2.0
        self.miny[0]  = -1.5
        self.maxy[0]  = 1.5
        self.numPaths = 1
        self.setText()

    def setFrame(self,frame,minx,maxx,miny,maxy):
        self.minx[frame] = minx
        self.maxx[frame] = maxx
        self.miny[frame] = miny
        self.maxy[frame] = maxy
        self.numPaths = frame + 1
        self.setText()

    def setText(self):
        self.text = ""
        s=("Number of Frames Needed: %8s\n" % (str(self.num_images)))
        self.text = self.text + s
        s=("|%8s|%8s|%8s|%8s|%8s|\n" % ("Frame","Min X", "Max X", "Min Y", "Max Y"))
        self.text = self.text + s
        for i in range(0,self.numPaths):
            s=("|%8s| %6.3f | %6.3f | %6.3f | %6.3f |\n" % (str(i), self.minx[i], self.maxx[i], self.miny[i], self.maxy[i]))
            self.text = self.text + s

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawText(event, qp)
        qp.end()

    def drawText(self, event, qp):
        qp.setPen(QtGui.QColor(168, 34, 3))
        qp.setFont(QtGui.QFont('Decorative', 10))
        qp.drawText(event.rect(), QtCore.Qt.AlignCenter, self.text)

    def getMinX(self,i):
        return(self.minx[i])

    def getMaxX(self,i):
        return(self.maxx[i])

    def getMinY(self,i):
        return(self.miny[i])

    def getMaxY(self,i):
        return(self.maxy[i])

class BGWidget(QtWidgets.QWidget):
    def __init__(self,width,height,bits_per_color):
        super(BGWidget, self).__init__()
        self.width = width
        self.height = height
        self.bits_per_color = bits_per_color
        self.MyMandelCalc = MandelCalc()
        self.MyMandelCalc.SetRange(-1.0,-1.5,2.0,1.5,400,400)
        self.setGeometry(QtCore.QRect(0, 0, width, height))
        self.BGData = []
        for y in range(0,self.height):
            row = []
            for x in range(0,self.width):
                row.append("#000")
            self.BGData.append(row)
        print("BG Widget")

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        for y in range(0,self.height,10):
            for x in range(0,self.width,10):
                self.drawRect(qp,x,y,10,10,self.BGData[y][x])

    def drawRect(self,painter,x,y,width,height,colornum):
        color = QtGui.QColor(colornum)
        painter.fillRect(x , y , width, height, color)

    def color(self,minx,maxx,miny,maxy,pos_x,pos_y,side):
        self.MyMandelCalc.SetRange(minx,miny,maxx,maxy,side,side)
        for x in range(0,side):
            for y in range(0,side):
                colorNum = self.MyMandelCalc.ColorDot(self.bits_per_color,x,y)
                self.BGData[pos_y + y][ pos_x + x] = colorNum

    def save(self,filename,rgb,bits_per_color,bright_shift):
        b = Bitmap(self.width, self.height)
        for y in range(0,self.height):
            for x in range(0,self.width):
                val_str = self.BGData[y][x]
                print (val_str)
                val_str2 = val_str[1:]
                val = int(val_str2,16)
                if(bits_per_color == 6):
                    val_low = ((val & 0x3f) << bright_shift)
                    val_mid = (((val>>6) & 0x3f) << bright_shift)
                    val_high = (((val>>12) & 0x3f) << bright_shift)
                elif (bits_per_color == 5):
                    val_low = ((val & 0x1f) << bright_shift)
                    val_mid = (((val>>5) & 0x1f) << bright_shift)
                    val_high = (((val>>10) & 0x1f) << bright_shift)
                elif (bits_per_color == 4):
                    val_low = ((val & 0xf) << bright_shift)
                    val_mid = (((val>>4) & 0xf) << bright_shift)
                    val_high = (((val>>8) & 0xf) << bright_shift)
                else:
                    #Enhance die
                    val_low = (val & 0xf)
                    val_mid = ((val>>4) & 0xf)
                    val_high = ((val>>8) & 0xf)
                # val low
                if(rgb[0].lower() == "r"):
                    val_red = val_low;
                elif(rgb[0].lower() == "g"):
                    val_green = val_low;
                else:
                    val_blue = val_low;
                # val mid
                if(rgb[1].lower() == "r"):
                    val_red = val_mid;
                elif(rgb[1].lower() == "g"):
                    val_green = val_mid;
                else:
                    val_blue = val_mid;
                # val high
                if(rgb[2].lower() == "r"):
                    val_red = val_high;
                elif(rgb[2].lower() == "g"):
                    val_green = val_high;
                else:
                    val_blue = val_high;
                # RGB
                b.setPixel(x,y,(val_red,val_green,val_blue))
        b.write(filename)




def main():

    parser = argparse.ArgumentParser(description='Draw Mandoelbrot Banckgrounds')
    args = parser.parse_args()
    app = QtWidgets.QApplication([])
    mBack = MandelbrotBackground()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

