import direct.directbase.DirectStart
from direct.showbase import DirectObject
from panda3d.core import *
from direct.interval.IntervalGlobal import *
from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from math import pi, sin, cos, atan2
import random
import gsjutil

class MyMouseApp(DirectObject):
    def __init__(self):        
        base.disableMouse() # Disable mouse-based camera control
        taskMgr.remove("mouseTask")
        self.mainLoop = taskMgr.add(self.mouseTask, "mouseTask")
        self.mousePos = None
        self.mouse1ing = False
        self.mouse3ing = False
        
        bgSound = loader.loadSfx("sound/boro_64kb.mp3")        
        bgSound.setVolume(0.15)
        bgSound.setLoop(True)
        bgSound.play()
        
        self.goodSound = loader.loadSfx("sound/good.ogg")
        self.goodSound.setLoop(False)
        self.goodSound.setVolume(0.5)
        self.badSound = loader.loadSfx("sound/bad.ogg")
        self.badSound.setLoop(False)
        
        self.accept("mouse1", self.mouse1Down)
        self.accept("mouse1-up", self.mouse1Up)
        self.accept("mouse2-up", self.mouse2Up)
        self.accept("mouse3", self.mouse3Down)
        self.accept("mouse3-up", self.mouse3Up)
        self.accept("wheel_up", self.wheelUp)
        self.accept("wheel_down", self.wheelDown)
                
        pickerNode = CollisionNode('mouseRay')
        pickerNP = camera.attachNewNode(pickerNode)
        # only detect collisions with CollisionNodes, not other geometry
        pickerNode.setFromCollideMask(BitMask32.bit(0))
        pickerNode.setIntoCollideMask(BitMask32.allOff())        
        self.pickerRay = CollisionRay()
        pickerNode.addSolid(self.pickerRay)
        
        self.mouseTrav = CollisionTraverser('mouseTrav')
        self.mouseQ = CollisionHandlerQueue()
        self.mouseTrav.addCollider(pickerNP, self.mouseQ)
        
        self.ballTrav = CollisionTraverser('ballTrav')
        self.ballQ = CollisionHandlerQueue()        
        
        alight = AmbientLight('alight')
        alight.setColor(VBase4(0.3, 0.3, 0.3, 1))
        alnp = render.attachNewNode(alight)
        render.setLight(alnp)
        
        dlight = DirectionalLight('dlight')
        dlight.setColor(VBase4(0.98, 0.98, 0.97, 1))
        dlnp = render.attachNewNode(dlight)        
        dlnp.setHpr(0, -90, 0)
        render.setLight(dlnp)
        
        self.cam = gsjutil.CamInfo(Point3(0, 0, 0), -pi/2, pi/2, 200)
        self.collPlane = self.collisionPlane(self.cam.r)
        self.sky("img/gradmetal.png")                
        self.targetBalls(10)
        self.remText = TextNode('remaining')
        self.remText.setText('Balls remaining: ')
        tnp = render2d.attachNewNode(self.remText)
        tnp.setScale(0.07)
        tnp.setPos(-1, 0, 0.95)
        self.start()
        
    def spinCameraTask(self, task):
        dt = task.time - self.spinCameraPrev        
        self.spinCameraPrev = task.time        
        self.cam.phi += dt
        a = task.time / (2 * pi)
        b = 1 - a        
        self.cam.theta = a * pi/2 + b * self.startCamTheta
        self.cam.r = a * 200 + b * self.startCamR        
        if task.time >= 2 * pi: # once all the way around
            self.pickable = True
            return Task.done
        else:            
            self.reCamera()
            return Task.cont
        
    def start(self): 
        self.cam.poi = Point3(0, 0, 0)
        self.reCamera()

        self.ballsRemaining = 0
        self.pickaBalls(2)
        self.heldBall = None        
        
        self.pickable = False # non-interactive until after one full spin
        self.spinCameraPrev = 0
        self.startCamTheta = self.cam.theta
        self.startCamR = self.cam.r        
        taskMgr.add(self.spinCameraTask, "SpinCameraTask")
        
    def collisionPlane(self, r):
        cp = CollisionPlane(Plane(Vec3(0, -1, 0), Point3(0, r, 0)))
        cn = CollisionNode('pickingplane')
        cn.addSolid(cp)
        pn = camera.attachNewNode(cn)    
        pn.setTag('plane', 'main')        
        return pn, cp        
        
    def sky(self, texName):
        b = gsjutil.ballmaker(3, True)
        bp = render.attachNewNode(b)
        bp.setPos(Point3(0, 0, 0))
        bp.setScale(1500, 1500, 1500)    
        tex = loader.loadTexture(texName)
        bp.setTexture(tex)
        mat = Material()
        mat.setEmission(VBase4(0.5, 0.5, 0.5, 1))        
        bp.setMaterial(mat)
        
    def targetBalls(self, size):
        bdefs = [
            { 'pos': Point3(30, 30, 30), 'color': VBase4(1, 0, 0, 1), 'name': 'red' },
            { 'pos': Point3(-30, -30, 30), 'color': VBase4(0, 1, 0, 1), 'name': 'green' },
            { 'pos': Point3(30, -30, -30), 'color': VBase4(0, 0, 1, 1), 'name': 'blue' },
            { 'pos': Point3(-30, 30, -30), 'color': VBase4(0, 0, 0, 1), 'name': 'black' }
            ]
        for d in bdefs:
            mat = Material()
            mat.setShininess(100)
            mat.setAmbient(d['color'])
            mat.setDiffuse(d['color'])
            mat.setSpecular(VBase4(1, 1, 1, 1.0))            
            b = gsjutil.ballmaker(3, False)
            bp = render.attachNewNode(b)
            bp.setPos(d['pos'])
            bp.setScale(size, size, size)
            bp.setMaterial(mat)
            bp.setTag('targetBall', d['name'])
            cs = CollisionSphere(0, 0, 0, 1)
            cnp = bp.attachNewNode(CollisionNode('cnode'))
            cnp.node().addSolid(cs)            
    
    def setBallsRemaining(self, n):
        self.ballsRemaining = n
        self.remText.setText('Balls remaining: %d' % (n))
            
    def pickaBalls(self, size):
        n = 8
        self.setBallsRemaining(n)        
        for i in range(0, n):
            p = Point3(random.random()*40 - 20, random.random()*40 - 20, random.random()*40 - 20)
            if i < 2:
                tagval = 'red'
                c = VBase4(1, 0, 0, 1)
            elif i < 4:
                tagval = 'green'
                c = VBase4(0, 1, 0, 1)
            elif i < 6:
                tagval = 'blue'
                c = VBase4(0, 0, 1, 1)            
            else:
                tagval = 'black'
                c = VBase4(0, 0, 0, 1)
            mat = Material()
            mat.setShininess(100)
            mat.setAmbient(c)
            mat.setDiffuse(c)
            mat.setSpecular(VBase4(1, 1, 1, 1.0))            
            b = gsjutil.ballmaker(2, False)
            bp = render.attachNewNode(b)
            bp.setPos(p)
            bp.setScale(size, size, size)
            bp.setMaterial(mat)
            bp.setTag('pickaBall', tagval)
            cs = CollisionSphere(0, 0, 0, 1)
            cnp = bp.attachNewNode(CollisionNode('cnode'))
            cnp.node().addSolid(cs)
            self.ballTrav.addCollider(cnp, self.ballQ)

    def mouseFindTagged(self, tag, tagval):
        mpos = base.mouseWatcherNode.getMouse()
        # This makes the ray's origin the camera and makes the ray point 
        # to the screen coordinates of the mouse.
        self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())            
        self.mouseTrav.traverse(render)
        if self.mouseQ.getNumEntries() > 0:
            self.mouseQ.sortEntries()
            # find first entry that matches the desired tag, and tag value if desired
            for i in range(self.mouseQ.getNumEntries()):              
                entry = self.mouseQ.getEntry(i)
                p = entry.getIntoNodePath().findNetTag(tag)
                if not p.isEmpty() and (tagval is None or p.getTag(tag) == tagval):
                    return p, entry
        return None, None
    
    def ballCollisionFinder(self):
        self.ballTrav.traverse(render)
        for i in range(self.ballQ.getNumEntries()):
            entry = self.ballQ.getEntry(i)
            p = entry.getIntoNodePath().findNetTag('targetBall')          
            if not p.isEmpty():
                f = entry.getFromNodePath().findNetTag('pickaBall')
                if not f.isEmpty():
                    if f.getTag('pickaBall') == p.getTag('targetBall'):
                        self.goodSound.play()
                    else:
                        self.badSound.play()
                    self.ballTrav.removeCollider(entry.getFromNodePath())
                    self.setBallsRemaining(self.ballsRemaining - 1)
                    f.detachNode()                    
                    break
                
    def mouse1Down(self):
        if not self.pickable:
            # no ball picking during preview rotation
            return
        try:
            if base.mouseWatcherNode.hasMouse():
                self.mouse1ing = True
                self.heldBall, e = self.mouseFindTagged('pickaBall', None)
                if self.heldBall is not None:
                    self.collPlaneSet(self.heldBall.getPos())
        except Exception, ex:
            print ex
                
    def mouse1Up(self):
        self.letGo()                
                    
    def mouse2Up(self):
        """ move camera on middle-click
        """
        if base.mouseWatcherNode.hasMouse():
            b, e = self.mouseFindTagged('pickaBall', None)                        
            if b is not None:                
                pos = b.getPos()
            else:
                pos = Point3(0, 0, 0)            
            d = (self.cam.getPos() - pos).length()
            self.cam.r = d
            self.cam.poi = pos
            self.reCamera()
                                
    def letGo(self):
        self.mouse1ing = False
        self.heldBall = None
    
    def mouse3Down(self):
        self.letGo()
        self.mouse3ing = True   
        
    def mouse3Up(self):        
        self.mouse3ing = False
        
    def wheelDown(self):
        self.letGo()
        self.cam.r *= 1.1
        self.reCamera()
    
    def wheelUp(self):
        self.mouse1ing = False
        self.cam.r *= 0.9
        if self.cam.r < 2:
            self.cam.r = 2
        self.reCamera()
        
    def mouseTask(self, task):
        if base.mouseWatcherNode.hasMouse():                            
            
            # getMouse doesn't return a copy - it returns the same object every time.
            mp = Point2(base.mouseWatcherNode.getMouse())
            if self.mousePos is not None and (mp[0] != self.mousePos[0] or mp[1] != self.mousePos[1]):
                self.ballCollisionFinder()
                diff = mp - self.mousePos
                if self.mouse3ing:
                    self.cam.phi -= diff[0]
                    self.cam.theta += diff[1]
                    self.reCamera()
                elif self.mouse1ing:
                    if self.heldBall is not None:
                        planeNode, e = self.mouseFindTagged('plane', 'main')
                        sp = e.getSurfacePoint(render)
                        self.heldBall.setPos(sp)
            self.mousePos = mp
            
        if self.ballsRemaining == 0:
            self.start()
        return Task.cont
    
    def reCamera(self):        
        hpr = self.cam.getHpr()
        pos = self.cam.getPos()
        camera.setHpr(hpr)
        camera.setPos(pos)
        self.collPlaneSetDist(self.cam.r)
    
    def collPlaneSetDist(self, d):
        curpn, cplane = self.collPlane
        cplane.setPlane(Plane(Vec3(0, -1, 0), Point3(0, d, 0)))
        
    def collPlaneSet(self, pos):
        vpoi = Vec3(self.cam.poi - self.cam.getPos())
        dpoi = vpoi.length()
        vpoi.normalize()
        d = dpoi + vpoi.dot(Vec3(pos - self.cam.poi))
        self.collPlaneSetDist(d)        
try:
    app = MyMouseApp()
except Exception, ex:
    print ex
run()

    