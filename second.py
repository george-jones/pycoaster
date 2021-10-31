from math import pi, sin, cos
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence
from panda3d.core import Point3
from panda3d.core import AmbientLight, DirectionalLight
from panda3d.core import VBase4

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
                
        self.panda = Actor("models/panda-model",
                           { "walk": "models/panda-walk4"})
        self.panda.setScale(0.005, 0.005, 0.005)
        self.panda.setPos(0, 20, -2)
        
        self.panda.reparentTo(self.render)
        
        alight = AmbientLight('alight')
        alight.setColor(VBase4(0.2, 0.2, 0.2, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)
        
        dlight = DirectionalLight('dlight')
        dlight.setColor(VBase4(0.98, 0.98, 0.97, 1))
        dlnp = render.attachNewNode(dlight)
        dlnp.setHpr(90, 315, 0)
        self.render.setLight(dlnp)
        

        
app = MyApp()
app.run()
        