import direct.directbase.DirectStart
from direct.showbase import DirectObject
from panda3d.core import *
from direct.interval.IntervalGlobal import *
from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from math import pi, sin, cos

class CamInfo():
    def __init__(self, poi, phi, theta, r):        
        self.poi = poi # point of interest - what the camera is looking at
        self.phi = phi # angle in XY plane
        self.theta = theta # angle in XZ plane
        self.r = r # distance from poi
        
    def getHpr(self):
        """ returns heading, pitch, roll.  in degrees.
        """
        h = (180 / pi) * self.phi + 90
        p = (180 / pi) * self.theta - 90
        return Vec3(h, p, 0)
    
    def getPos(self):
        """ get position of camera
        """
        # keep angles within bounds
        if self.phi < -pi:
            self.phi += 2 * pi
        elif self.phi > pi:
            self.phi -= 2 *pi
        if self.theta < -pi:
            self.theta += 2 * pi
        elif self.theta > pi:
            self.theta -= 2 *pi        
        return self.poi + Point3(self.r * sin(self.theta) * cos(self.phi),
                                 self.r * sin(self.theta) * sin(self.phi),
                                 self.r * cos(self.theta))    

class MyMouseApp(DirectObject):
    def __init__(self):
        
        base.disableMouse() # Disable mouse-based camera control
        taskMgr.remove("mouseTask")
        self.mainLoop = taskMgr.add(self.mouseTask, "mouseTask")
        self.mousePos = None
        self.mouse3ing = False
        
        self.accept("mouse1", self.mouse1Down)
        self.accept("mouse1-up", self.mouse1Up)
        self.accept("mouse3", self.mouse3Down)
        self.accept("mouse3-up", self.mouse3Up)
        self.accept("wheel_up", self.wheelUp)
        self.accept("wheel_down", self.wheelDown)
        
        self.environ = loader.loadModel("models/environment")
        self.environ.reparentTo(render)
        self.environ.setScale(0.25, 0.25, 0.25)
        self.environ.setPos(0, 0, 0)        
        
        self.pandaA = loader.loadModel("models/panda")
        self.pandaA.reparentTo(render)
        self.pandaA.setScale(2, 2, 2)
        self.pandaA.setPos(0, 0, 0)
        self.pandaA.setTag('pandaTag', 'A')

        self.pandaB = loader.loadModel("models/panda")
        self.pandaB.reparentTo(render)
        self.pandaB.setScale(1.5, 1.5, 1.5)
        self.pandaB.setPos(40, 40, 0)
        self.pandaB.setTag('pandaTag', 'B')

        self.pandaC = loader.loadModel("models/panda")
        self.pandaC.reparentTo(render)
        self.pandaC.setScale(2.5, 2.5, 2.5)
        self.pandaC.setPos(-40, -40, 0)
        self.pandaC.setTag('pandaTag', 'C')
        
        self.cam = CamInfo(Point3(0, 0, 0), -pi/2, pi/4, 200)
        self.reCamera()        
        
        pickerNode = CollisionNode('mouseRay')
        pickerNP = camera.attachNewNode(pickerNode)
        pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        pickerNode.addSolid(self.pickerRay)
        
        self.mouseTrav = CollisionTraverser('mouseTrav')        
        self.mouseQ = CollisionHandlerQueue()
        self.mouseTrav.addCollider(pickerNP, self.mouseQ)        

    def mouse1Down(self):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            # This makes the ray's origin the camera and makes the ray point 
            # to the screen coordinates of the mouse.
            self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())            
            self.mouseTrav.traverse(render)            
            if self.mouseQ.getNumEntries() > 0:                
                self.mouseQ.sortEntries()
                # find first entry that is a panda (or a child of a panda)
                for i in range(self.mouseQ.getNumEntries()):
                    entry = self.mouseQ.getEntry(i)
                    p = entry.getIntoNodePath().findNetTag('pandaTag')                    
                    if not p.isEmpty():
                        p.hide()
                        break
            
    def mouse1Up(self):
        pass
    
    def mouse3Down(self):
        self.mouse3ing = True     
        
    def mouse3Up(self):        
        self.mouse3ing = False
        
    def wheelDown(self):
        self.cam.r *= 1.1
        self.reCamera()
    
    def wheelUp(self):
        self.cam.r *= 0.9
        if self.cam.r < 2:
            self.cam.r = 2
        self.reCamera()        
        
    def mouseTask(self, task):
        if base.mouseWatcherNode.hasMouse():
            # getMouse doesn't return a copy - it returns the same object every time.
            mp = Point2(base.mouseWatcherNode.getMouse())
            if self.mousePos is not None and (mp[0] != self.mousePos[0] or mp[1] != self.mousePos[1]):
                diff = mp - self.mousePos
                if self.mouse3ing:
                    self.cam.phi -= diff[0]
                    self.cam.theta += diff[1]
                    self.reCamera()
            self.mousePos = mp
        return Task.cont
    
    def reCamera(self):        
        hpr = self.cam.getHpr()
        pos = self.cam.getPos()
        camera.setHpr(hpr)
        camera.setPos(pos)        

app = MyMouseApp()

run()