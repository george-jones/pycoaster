import direct.directbase.DirectStart
from direct.showbase import DirectObject
from panda3d.core import *
from direct.interval.IntervalGlobal import *
from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from math import pi, sin, cos, atan2
import random

def ballmaker(n, inverted):
    node = GeomNode('ball')
    #gf = GeomVertexFormat.getV3n3() # vertex and normal
    gf = GeomVertexFormat.getV3n3t2() # vertex, normal, texture    
    vdata = GeomVertexData('ball', gf, Geom.UHStatic)
    vwrite = GeomVertexWriter(vdata, 'vertex')
    nwrite = GeomVertexWriter(vdata, 'normal')
    twrite = GeomVertexWriter(vdata, 'texcoord')
    geom = Geom(vdata)    
    
    def tesselate(faces):
        a = [ ]
        for f in faces:            
            m0 = (f[0] + f[1]) / 2
            m1 = (f[1] + f[2]) / 2
            m2 = (f[2] + f[0]) / 2
            a.append([ f[0], m0, m2 ])
            a.append([ m0, f[1], m1 ])
            a.append([ m2, m1, f[2] ])
            a.append([ m0, m1, m2 ])
        return a
    
    faces = [ ]
    # top pyramid
    faces.append([ Point3(-0.5, -0.5, 0), Point3(0.5, -0.5, 0), Point3(0, 0, 0.5) ])
    faces.append([ Point3(0.5, -0.5, 0), Point3(0.5, 0.5, 0), Point3(0, 0, 0.5) ])
    faces.append([ Point3(0.5, 0.5, 0), Point3(-0.5, 0.5, 0), Point3(0, 0, 0.5) ])
    faces.append([ Point3(-0.5, 0.5, 0), Point3(-0.5, -0.5, 0), Point3(0, 0, 0.5) ])
    # bottom pyramid
    faces.append([ Point3(-0.5, -0.5, 0), Point3(0, 0, -0.5), Point3(0.5, -0.5, 0) ])
    faces.append([ Point3(0.5, -0.5, 0), Point3(0, 0, -0.5), Point3(0.5, 0.5, 0) ])
    faces.append([ Point3(0.5, 0.5, 0), Point3(0, 0, -0.5), Point3(-0.5, 0.5, 0) ])
    faces.append([ Point3(-0.5, 0.5, 0), Point3(0, 0, -0.5), Point3(-0.5, -0.5, 0) ])
    
    for i in range(0, n):
        faces = tesselate(faces)
    
    prim = GeomTriangles(Geom.UHStatic)    
    
    for f in faces:
        if inverted:
            # rearrange vertices
            v1 = f[1]
            v2 = f[2]
            f[1] = v2
            f[2] = v1            
        for p in f:
            v = Vec3(p[0], p[1], p[2])
            v.normalize()
            p = Point3(v[0], v[1], v[2])
            vwrite.addData3f(p)
            nwrite.addData3f(p)
            # something weird here.  fix it later.
            twrite.addData2f(atan2(p[1], p[0]) / (2*pi), 0.5+p[2]/2)
    
    k = 0
    for i in range(0, len(faces)):
        for j in range(0, len(f)):            
            prim.addVertex(k)
            k += 1
    prim.closePrimitive()
    geom.addPrimitive(prim)    
    node.addGeom(geom)
    return node    

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

def collisionPlane():    
    cp = CollisionPlane(Plane(Vec3(0, -1, 0), Point3(0, 0, 0)))
    cn = CollisionNode('pickingplane')
    cn.addSolid(cp)
    pn = render.attachNewNode(cn)    
    pn.setTag('plane', 'main')
    pn.show()
    return pn, cp    

class MyMouseApp(DirectObject):
    def __init__(self):
        
        base.disableMouse() # Disable mouse-based camera control
        taskMgr.remove("mouseTask")
        self.mainLoop = taskMgr.add(self.mouseTask, "mouseTask")
        self.mousePos = None
        self.mouse1ing = False
        self.mouse3ing = False
        
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
                
        self.collPlane = collisionPlane()
        self.sky("gradmetal.png")                
        self.targetBalls(10)
        self.remText = TextNode('remaining')
        self.remText.setText('Balls remaining: ')
        tnp = render2d.attachNewNode(self.remText) #aspect2d.attachNewNode(self.remText)
        tnp.setScale(0.07)
        tnp.setPos(-1, 0, 0.95)
        self.start()
        
    def start(self):     
        self.cam = CamInfo(Point3(0, 0, 0), -pi/2, pi/2, 200)
        self.reCamera()            
        self.ballsRemaining = 0
        self.pickaBalls(2)
        self.heldBall = None
        self.reNormalPlane = False
        
    def sky(self, texName):
        b = ballmaker(3, True)
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
            b = ballmaker(3, False)
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
            p = Point3(random.random()*60 - 30, random.random()*60 - 30, random.random()*60 - 30)
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
            b = ballmaker(2, False)
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
                        print "Excellent"
                    else:
                        print "Bogus"
                    self.ballTrav.removeCollider(entry.getFromNodePath())
                    self.setBallsRemaining(self.ballsRemaining - 1)
                    f.detachNode()                    
                    break
                
    def setPlane(self, pos, reNormal):
        curpn, cplane = self.collPlane
        if pos is not None:
            curpn.setPos(pos)
        else:
            pos = curpn.getPos()            
        if reNormal:
            plane2cam = Vec3(self.cam.getPos() - pos)
            cplane.setPlane(Plane(plane2cam, pos))                
        
    def mouse1Down(self):
        if base.mouseWatcherNode.hasMouse():
            self.mouse1ing = True
            self.heldBall, e = self.mouseFindTagged('pickaBall', None)                        
            if self.heldBall is not None:                
                self.setPlane(self.heldBall.getPos(), False)
                
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
            self.setPlane(pos, True)
                                
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
        try:
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
                        if self.heldBall is not None:
                            pos = self.heldBall.getPos()
                        else:
                            pos = self.cam.poi
                        self.setPlane(pos, True)
                    elif self.mouse1ing:
                        if self.heldBall is not None:
                            planeNode, e = self.mouseFindTagged('plane', 'main')
                            sp = e.getSurfacePoint(render)
                            self.heldBall.setPos(sp) 
                            self.setPlane(sp, False)
                self.mousePos = mp
        except Exception, ex:
            print ex
            
        if self.ballsRemaining == 0:
            self.start()
        return Task.cont
    
    def reCamera(self):        
        hpr = self.cam.getHpr()
        pos = self.cam.getPos()
        camera.setHpr(hpr)
        camera.setPos(pos)        
        
app = MyMouseApp()
run()