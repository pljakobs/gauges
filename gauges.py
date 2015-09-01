#!/usr/bin/python
########################################################
#
# Implement gauges that are automatically updated with
# values read from callback functions. This is part of
# a RaspberyPi project and thus specifically tuned to
# small scree displays
#
# I was unable to find a similar library that didn't
# require a browser to display gauges.
#
########################################################

import random
import math
import sys
import pygame
from pygame.locals import Color
import os
import time
import threading
from threading import Timer

def deg2rad(deg):
	return deg/180.0*math.pi


class simpleGauge:
  def __init__(self, screen, rect, alpha, valMin, valMax, valYellow, valRed, bgColor):
    self.screen    = screen
    self.rect      = rect
    self.alpha     = float(alpha)
    self.valMin    = valMin
    self.valMax    = valMax
    self.valYellow = valYellow
    self.valRed    = valRed
    self.val       = valMin
    self.bgColor   = bgColor
    self.value_old = 0

    ((self.x0, self.y0), (self.width, self.height)) = self.rect

    self.factor    = alpha/float(valMax-valMin)
    self.backup    = pygame.Surface((self.width, self.height),0,self.screen)

    self.redraw    = True

    # calculate the arc and radius (radius will be increased to use more space
    # when the actual arc is less
    self.startDeg=180-self.alpha/2
    self.endDeg=180+self.alpha/2
    if self.alpha>180:
      self.arc_r=self.width/2
    elif self.alpha<30:
      self.arc_r=selfwidth/2
    else:
      self.arc_r=self.width/(2*abs(math.cos(deg2rad(90-self.alpha/2))))
    self.arc_r*=0.95
    self.center=(self.width/2, self.arc_r*1.2)
    # draw the actual scale
    self.doRedraw()

  def enableText(self):
    self.text=True

  def disableText(self):
    self.text=False

  def setTextPosition(self, position):
    (x,y)=position
    self.TextPosition=position

  def doRedraw(self):
    self.drawScale()
    self.drawNeedle(self.val)

  def setbgColor(self, bgColor):
    self.bgColor = bgColor
    self.redraw  = True
    self.doRedraw()

  def setDamping(self, damping=0.75,damping_down=0):
    self.damping_up=damping
    if damping_down==0:
      self.damping_down=damping
    else:
      self.damping_down=damping_down

  def update(self):
    v=self.callback()
    diff=v-self.value_old

    if diff>0:
      value=round(self.value_old+diff*self.damping_up,3)
    else:
      value=round(self.value_old+diff*self.damping_down,3)

    if value<self.valMin:
      self.val=self.valMin
    elif value>self.valMax:
      self.val=self.valMax
    else:
      self.val = value
    self.doRedraw()
    self.value_old=self.val

  def SetCallback(self, callback):
    self.callback=callback

  def autoupdate(self, interval=1, flag=False):
    self.interval=interval
    self.updateflag=flag
    if self.updateflag==True:
      self.update_t=updateThread(self, self.interval)
      self.update_t.stop_event=threading.Event()
      self.update_t.start()
    else:
      self.update_t.stop()

  def getValue(self):
    return self.val

  def drawCircleArc(self, color, center, radius, startDeg, endDeg, thickness):
    (x,y) = center
    startRad = deg2rad(270-startDeg)
    endRad = deg2rad(270-endDeg)
    rect = (x-radius,y-radius,radius*2,radius*2)
    pygame.draw.arc(self.backup, color, rect, endRad, startRad, thickness-1)
    rect = (x-radius,y-radius+1,radius*2,radius*2)
    pygame.draw.arc(self.backup, color, rect, endRad, startRad, thickness-1)

  def drawScale(self):
    ((top_x, top_y),(width, height))=self.rect
    if self.redraw:
      pygame.draw.rect(self.backup, self.bgColor, ((0,0),(width, height)))
      pygame.draw.rect(self.backup, Color("Black"), ((0,0),(width, height)),1)
      pygame.draw.rect(self.backup, Color("white"), (self.center,(4,4)))

      self.drawCircleArc(Color("black"),  self.center, self.arc_r,   180-self.alpha/2-2,                       180+self.alpha/2+2,                        16)
      self.drawCircleArc(Color("green"),  self.center, self.arc_r-2, 180-self.alpha/2,                         180-self.alpha/2 + self.alpha * self.valYellow / 100, 12)
      self.drawCircleArc(Color("yellow"), self.center, self.arc_r-2, 180-self.alpha/2+self.alpha*self.valYellow/100, 180-self.alpha/2 + self.alpha * self.valRed / 100,    12)
      self.drawCircleArc(Color("red"),    self.center, self.arc_r-2, 180-self.alpha/2+self.alpha*self.valRed/100,    180+self.alpha/2,                          12)

    self.screen.blit(self.backup, self.rect,)
    pygame.display.update(self.rect)
    self.redraw=False;

  def drawNeedle(self, value):
    (x, y)=self.center
    beta_r=deg2rad(270+(value-self.valMin)*self.factor-self.alpha/2)

    self.drawScale()
    pygame.draw.line(self.screen, Color("red"), (x+self.x0+2,y+self.y0+2), (x+self.x0+self.arc_r*math.cos(beta_r)+2, y+self.y0+self.arc_r*math.sin(beta_r)+2), 4)
    pygame.display.update(self.rect)

class updateThread(threading.Thread):
  def __init__(self, parent, interval):
    self.parent=parent
    self.interval=interval
    threading.Thread.__init__(self)

  def run(self):
    while not self.stop_event.isSet():
      self.parent.update()
      self.stop_event.wait(self.interval)

  def stop(self):
    self.stop_event.set()


########################################################
#
# a callback function that returns 0
# used to let a gauge fall off to 0
#
########################################################
def getZero():
  return float(0)

########################################################
#
# those only make sense on the RasPi
# they're also the reason, why you need to start the
# demo code with root rights
#
########################################################
def getCPUtemperature():
 res = os.popen('/opt/vc/bin/vcgencmd measure_temp').readline()
 return float(res.replace("temp=","").replace("'C\n",""))

def getCPUfrequency():
 res = os.popen('/opt/vc/bin/vcgencmd measure_clock arm').readline()
 return float(res.replace("frequency(45)=",""))/1000000

########################################################
#
# if there's no $DISPLAY, we're on a fb-only device
# you'll have to configure the framebuffer according
# to your requirements
#
# this demo was written for the adafruit 2.8" 320x480
# display on a RaspberryPi
#
########################################################

if os.getenv('DISPLAY')==None:
  os.putenv('SDL_FBDEV', '/dev/fb1')
  os.putenv('SDL_VIDEODRIVER', 'fbcon')
  os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
  os.putenv('SDL_MOUSEDRV', 'TSLIB')
  #os.putenv('SDL_NOMOUSE', '1')

pygame.init()

pi=math.pi

window = pygame.display.set_mode((240, 320))

########################################################
#
# create two gauges
#
########################################################

CPUTemp = simpleGauge(window, ((0,0),(120,106)), 160, 0, 60, 80, 90, Color("Navy"))
CPUFreq = simpleGauge(window, ((120,0),(120,106)), 300, 500, 1000, 85,95, Color("Navy"))

CPUTemp.SetCallback(getCPUtemperature)
CPUTemp.setDamping(0.75,0.75)

CPUFreq.SetCallback(getCPUfrequency)
CPUFreq.setDamping(0.75,0.5)

CPUFreq.autoupdate(0.01,True)
time.sleep(2)
CPUTemp.autoupdate(0.2,True)

time.sleep(5)
CPUTemp.SetCallback(getZero)
CPUTemp.setbgColor(Color('grey'))
for i in range(1,100):
  #print CPUTemp.getValue()
  time.sleep(0.1)

CPUFreq.SetCallback(getZero)
CPUFreq.setbgColor(Color('grey'))
time.sleep(10)
CPUTemp.autoupdate(False)
CPUFreq.autoupdate(False)
time.sleep(6)


CPUTemp.SetCallback(getCPUtemperature)
CPUTemp.setbgColor(Color('black'))
CPUFreq.SetCallback(getCPUfrequency)
CPUFreq.setbgColor(Color('black'))

CPUFreq.autoupdate(0.01,True)
CPUTemp.autoupdate(0.02,True)

time.sleep(5)
CPUTemp.SetCallback(getZero)
CPUTemp.setbgColor(Color('grey'))
time.sleep(2)

CPUFreq.SetCallback(getZero)
CPUFreq.setbgColor(Color('grey'))
time.sleep(10)
CPUTemp.autoupdate(False)
CPUFreq.autoupdate(False)

