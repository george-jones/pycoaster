from math import pi, sin, cos
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence
from panda3d.core import Point3

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.disableMouse()
        
        self.environ = self.loader.loadModel("models/environment")
        self.environ.reparentTo(self.render)
        self.environ.setScale(0.25, 0.25, 0.25)
        self.environ.setPos(-8, 42, 0)
        
        self.taskMgr.add(self.spinCameraTask, "SpinCameraTask")
        
        self.panda = Actor("models/panda-model",
                           { "walk": "models/panda-walk4"})
        self.panda.setScale(0.005, 0.005, 0.005)
        self.panda.reparentTo(self.render)
        self.panda.loop("walk")
        
        pandaPosInt1 = self.panda.posInterval(13,
                                              Point3(0, -10, 0),
                                              startPos=Point3(0, 10, 0))
        pandaPosInt2 = self.panda.posInterval(13,
                                              Point3(0, 10, 0),
                                              startPos=Point3(0, -10, 0))
        pandaHprInt1 = self.panda.hprInterval(3,
                                              Point3(180, 0, 0),
                                              startHpr=Point3(0, 0, 0))
        pandaHprInt2 = self.panda.hprInterval(3,
                                             Point3(0, 0, 0),
                                             startHpr=Point3(180, 0, 0))
        self.pandaPace = Sequence(pandaPosInt1,
                                  pandaHprInt1,
                                  pandaPosInt2,
                                  pandaHprInt2,
                                  name="pandaPace")
        self.pandaPace.loop()
                                  
        
    def spinCameraTask(self, task):
        angleDegrees = task.time * 6.0
        angleRadians = angleDegrees * (pi / 180.0)
        #r = task.time * 5
        r = 20
        c = self.camera
        c.setPos(r * sin(angleRadians), -1.0 * r * cos(angleRadians), 3)
        c.setHpr(angleDegrees, 0, 0)
        return Task.cont
        
app = MyApp()
app.run()
        