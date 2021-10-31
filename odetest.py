import numpy as np
from scipy import interpolate
from panda3d.core import *
import xml.etree.ElementTree as ET

loadPrcFile("config/Config.prc")

import direct.directbase.DirectStart
from direct.interval.IntervalGlobal import *
from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from math import pi
import os
import random
import gsjutil
import design

class ODEApp(DirectObject):
    def __init__(self):
        b = gsjutil.ballmaker(2, False)
        bp = render.attachNewNode(b)
        bp.setPos((0, 30, 5))
        self.bp = bp
        
        self.deltaTimeAccumulator = 0
        self.stepSize = 1.0 / 90.0 # 90 fps
        taskMgr.doMethodLater(1.0, self.simTask, "Physics Sim")
    
    def sim(self):        
        bp = self.bp
        pos = bp.getPos()
        pos[2] -= 0.01
        bp.setPos(pos)
        #print pos
        
    def simTask(self, task):
        self.deltaTimeAccumulator += globalClock.getDt()        
        while self.deltaTimeAccumulator > self.stepSize:
            self.deltaTimeAccumulator -= self.stepSize            
            self.sim()
        return task.cont
        
    
        

app = ODEApp()
run()