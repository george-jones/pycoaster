import direct.directbase.DirectStart
from direct.showbase import DirectObject
from panda3d.core import *
from direct.interval.IntervalGlobal import *
from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from math import pi, sin, cos
import random

PLANE_XY = 0
PLANE_YZ = 1
PLANE_XZ = 2

def ballmaker(n):
    node = GeomNode('ball')
    gf = GeomVertexFormat.getV3n3() # vertex and normal
    vdata = GeomVertexData('ball', gf, Geom.UHStatic)    
    vwrite = GeomVertexWriter(vdata, 'vertex')
    nwrite = GeomVertexWriter(vdata, "normal")
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
        for p in f:
            v = Vec3(p[0], p[1], p[2])
            v.normalize()
            p = Point3(v[0], v[1], v[2])
            vwrite.addData3f(p)
            nwrite.addData3f(p)            
    
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

def axialPlane(plane):    
    node = GeomNode('plane')
    gf = GeomVertexFormat.getV3()
    vdata = GeomVertexData('plane', gf, Geom.UHStatic)    
    vwrite = GeomVertexWriter(vdata, 'vertex')    
    geom = Geom(vdata)
    prim = GeomTriangles(Geom.UHStatic)    
    
    if plane == PLANE_XY:
        c = VBase4(0, 0, 1, 1)
        vwrite.addData3f(-1, -1, 0)
        vwrite.addData3f( 1, -1, 0)
        vwrite.addData3f( 1,  1, 0)
        vwrite.addData3f(-1,  1, 0)                   
    elif plane == PLANE_YZ:
        c = VBase4(1, 0, 0, 1)
        vwrite.addData3f(0, -1, -1)
        vwrite.addData3f(0,  1, -1)
        vwrite.addData3f(0,  1,  1)
        vwrite.addData3f(0, -1,  1)
    elif plane == PLANE_XZ:
        c = VBase4(0, 1, 0, 1)
        vwrite.addData3f(-1, 0, -1)
        vwrite.addData3f( 1, 0, -1)
        vwrite.addData3f( 1, 0,  1)
        vwrite.addData3f(-1, 0,  1)    
    
    prim.addVertex(0)
    prim.addVertex(1)
    prim.addVertex(3)
    prim.addVertex(3)
    prim.addVertex(1)
    prim.addVertex(2)    
    prim.closePrimitive()
    geom.addPrimitive(prim)    
    node.addGeom(geom)
    
    np = render.attachNewNode(node)
    np.hide()
    mat = Material()
    mat.setShininess(100)
    mat.setAmbient(c)
    mat.setDiffuse(c)
    mat.setSpecular(VBase4(1, 1, 1, 1.0))
    np.setTwoSided(True)
    np.setAlphaScale(0.1)            
    np.setTransparency(TransparencyAttrib.MAlpha)    
    np.setMaterial(mat)    
    return np
    
def axes():
    pts = [ ]
    xballs = [ ]
    yballs = [ ]
    zballs = [ ]
    for i in range(0, 10):
        pts.append(Point3(i*2, 0, 0))
    for i in range(0, 10):
        pts.append(Point3(0, i*2, 0))
    for i in range(0, 10):
        pts.append(Point3(0, 0, i*2))
        
    for p in pts:
        b = ballmaker(2)
        bp = render.attachNewNode(b)
        mat = Material()
        mat.setShininess(100)
        if p[0] != 0:
            c = VBase4(0, 0, 1, 1)
            xballs.append(bp)
        elif p[1] != 0:
            c = VBase4(1, 0, 0, 1)
            yballs.append(bp)
        elif p[2] != 0:
            c = VBase4(0, 1, 0, 1)
            zballs.append(bp)
        else:
            c = VBase4(1, 1, 1, 1)                
        mat.setAmbient(c)
        mat.setDiffuse(c)
        mat.setSpecular(VBase4(1, 1, 1, 1.0))
        #mat.setEmission(VBase4(1, 1, 0.75, 0.01))
        #mat.setTwoside(1)
        #bp.setAlphaScale(0.25)            
        #bp.setTransparency(TransparencyAttrib.MAlpha)
        bp.setPos(p)
        bp.setMaterial(mat)
    return [ xballs, yballs, zballs ]
    
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
        self.accept("mouse3", self.mouse3Down)
        self.accept("mouse3-up", self.mouse3Up)
        self.accept("wheel_up", self.wheelUp)
        self.accept("wheel_down", self.wheelDown)
        
        #self.cam = CamInfo(Point3(0, 0, 0), -pi/2, pi/4, 200)
        self.cam = CamInfo(Point3(0, 0, 0), -pi/2, pi/2, 200)
        self.reCamera()
        
        pickerNode = CollisionNode('mouseRay')
        pickerNP = camera.attachNewNode(pickerNode)
        pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        pickerNode.addSolid(self.pickerRay)
        
        self.mouseTrav = CollisionTraverser('mouseTrav')        
        self.mouseQ = CollisionHandlerQueue()
        self.mouseTrav.addCollider(pickerNP, self.mouseQ)            
        
        alight = AmbientLight('alight')
        alight.setColor(VBase4(0.3, 0.3, 0.3, 1))
        alnp = render.attachNewNode(alight)
        render.setLight(alnp)
        
        dlight = DirectionalLight('dlight')
        dlight.setColor(VBase4(0.98, 0.98, 0.97, 1))
        dlnp = render.attachNewNode(dlight)
        dlnp.setHpr(90, 315, 0)        
        render.setLight(dlnp)
        
        self.axes = axes()
        self.axPlanes = [ axialPlane(plane) for plane in range(0, 3) ]

    def planeShow(self, plane):
        for i in range(0, 3):
            p = self.axPlanes[i]
            if i != plane:
                p.hide()
            else:
                s = 0.2 * self.cam.r
                p.setScale(s, s, s)
                p.setPos(self.cam.poi)
                p.show()
    
    def getCurrPlane(self):
        phi = self.cam.phi
        theta = self.cam.theta
        if phi < 0:
            phi += 2*pi
        if theta < 0:
            theta += 2*pi
        plane = 0
        if (theta > pi/4 and theta < 3*pi/4) or (theta > 5*pi/4 and theta < 7*pi/4):
            if (phi > pi/4 and phi < 3*pi/4) or (phi > 5*pi/4 and phi < 7*pi/4):                    
                plane = PLANE_XZ
            else:
                plane = PLANE_YZ
        else:
            plane = PLANE_XY
        return plane
                
    def mouse1Down(self):
        if base.mouseWatcherNode.hasMouse():
            self.mouse1ing = True
            
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
                    p = entry.getIntoNodePath().findNetTag('trackball')
                    if not p.isEmpty():
                        p.hide()
                        break
            
    def mouse1Up(self):
        self.mouse1ing = False
    
    def mouse3Down(self):
        self.mouse1ing = False
        self.mouse3ing = True   
        
    def mouse3Up(self):        
        self.mouse3ing = False
        
    def wheelDown(self):
        self.mouse1ing = False
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
            
            if self.mouse1ing:
                self.planeShow(self.getCurrPlane())
            else:
                self.planeShow(-1)
            
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