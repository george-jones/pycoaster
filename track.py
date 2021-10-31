from __future__ import division
from time import clock
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence
from panda3d.core import *
from coasterload import xmlToCoaster
        
class MyApp(ShowBase):    
    def __init__(self):
        ShowBase.__init__(self)        
        
        self.setlights()
        #self.render = None
        f = open('first.xml')
        c = xmlToCoaster(f.read(), self.render)        
        f.close()
        
    def setlights(self):
        alight = AmbientLight('alight')
        alight.setColor(VBase4(0.2, 0.2, 0.2, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)
        
        dlight = DirectionalLight('dlight')
        dlight.setColor(VBase4(0.98, 0.98, 0.97, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(90, 315, 0)        
        self.render.setLight(dlnp)                
        
app = MyApp()
app.run()
