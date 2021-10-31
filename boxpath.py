from __future__ import division
from math import pi, sin, cos, pow
from time import clock
from numbers import Number
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence
from panda3d.core import *
from pandac.PandaModules import Material
import random

class LinearInterp():
    def __init__(self, p0, p1):
        # works with numbers, Point3, Vec3
        self.p0 = p0
        self.p1 = p1        
        if (isinstance(p0, Number) == False and 
            isinstance(p0, Point3) == False and 
            isinstance(p0, Vec3) == False):
            raise Exception, "Expected Point3 or Vec3"
        
    def evalat(self, t):
        """ Get value at a given position
        """        
        return self.p0 * (1 - t) + self.p1 * t

class HermiteSpline():
    def __init__(self, p0, p1, t0, t1):
        self.p0 = p0
        self.p1 = p1
        self.t0 = t0
        self.t1 = t1
            
    def evalat(self, t):
        """ returns tuple (Point3, Vec3) for position, tangent
        """
        tcb = pow(t, 3.0)
        tsq = pow(t, 2.0)
        
        pvals = [ ]    
        tvals = [ ]        
        for i in range(0, 3):
            a = self.p0[i]
            b = self.p1[i]
            c = self.t0[i]
            d = self.t1[i]
            pvals.append(a*(2*tcb - 3*tsq + 1) + 
                         b*(-2*tcb + 3*tsq) +
                         c*(tcb - 2*tsq + t) +
                         d*(tcb - tsq))
            tvals.append(a*(6*tsq - 6*t) + 
                         b*(-6*tsq + 6*t) +
                         c*(3*tsq - 4*t + 1) +
                         d*(3*tsq - 2*t))
        p = Point3(pvals[0], pvals[1], pvals[2])
        v = Vec3(tvals[0], tvals[1], tvals[2])        
        return (p, v)

def vec3mirror(v, mv):
    """ get a vector that is mirrored about another. some work to do still here
    to make it safe for vectors that are perpendicular or collinear
    """    
    c = v.cross(mv)
    d = mv.cross(c)
    r = v.project(mv) - v.project(d)
    return r

def normfinder(sp, n0, t0, t1, steps): 
    """ gets normal vector at t1 along a spline, given normal vector n0 at t0
    """
    n = Vec3(n0[0], n0[1], n0[2])
    n.normalize()
    for i in range(0, steps+1):
        t = t0 + i * (t1 - t0) / steps        
        p, v = sp.evalat(t)
        n = v.cross(n).cross(v)
        n.normalize()        
    return n

def rotateaxis(v, v_axis, angle):
    """ rotate vector v clockwise about axis
    """
    axis = Vec3(v_axis)
    axis.normalize()
    s_angle = -1 * sin(angle)
    c_angle = cos(angle)
    r1 = v * c_angle
    r2 = axis.cross(v) * s_angle
    r3 = axis * axis.dot(v) * (1 - c_angle)
    return r1 + r2 + r3

def tubenode(p0, p1, v0, n0, a0, a1, r, num, perseg):
    node = GeomNode('TheTube')    
    gf = GeomVertexFormat.getV3n3() # vertex
    vdata = GeomVertexData('tube', gf, Geom.UHStatic)    
    vwrite = GeomVertexWriter(vdata, 'vertex')
    nwrite = GeomVertexWriter(vdata, "normal")
    geom = Geom(vdata)
    # number of segments -> number of points
    if num % 2 == 1:
        num += 1
    v1 = vec3mirror(v0, (p1-p0))
    s = HermiteSpline(p0, p1, v0, v1)
    aint = LinearInterp(a0, a1)
    
    # get values using interpolation
    vals = [ ]
    k = 0
    for i in range(0, num+1):
        t = i / num
        p, tg = s.evalat(t)
        if i == 0:
            n = n0
        else:
            tprev = (i - 1) / num
            n = normfinder(s, n, tprev, t, 5)
        ang = aint.evalat(t)        
        vals.append([ p, tg, n, ang ])        
        # get vertices        
        for j in range(0, perseg):
            a = ang + (j / perseg) * (2 * pi)
            na = rotateaxis(n, tg, a)
            pj = p + na*r
            vwrite.addData3f(pj)
            nwrite.addData3f(na)
            #nwrite.addData3f(j/4, j/2, j)
    # make tristrips from added vertices    
    for i in range(0, num):
        prim = GeomTristrips(Geom.UHStatic)
        for j in range(0, perseg+1):
            if j == perseg:
                j = 0
            prim.addVertices(i*perseg + j, (i+1)*perseg + j)            
        prim.closePrimitive()
        geom.addPrimitive(prim)
    node.addGeom(geom)
    return node
        
class MyApp(ShowBase):
    #def run(self): pass
    def __init__(self):
        ShowBase.__init__(self)
        
        p0 = Point3(0, 0, 0)
        p1 = Point3(7, 0, 10)
        v0 = Point3(-8, 0.2, 10)
        n0 = Vec3(0, -1, 0)
        
        for i in range(0, 1):
            for j in range(0, 1):        
                tube = tubenode(p0, p1, v0, n0, 0, pi/2, 0.25, 15, 10)
                tubeNodePath = self.render.attachNewNode(tube)
                tubeNodePath.setPos(Point3(i-15, j+30, -5))
                a = random.randrange(-180, 180)
                b = random.randrange(-180, 180)
                c = random.randrange(-180, 180)
                hprInt1 = tubeNodePath.hprInterval(5, Point3(a, b, c), startHpr=Point3(0, 0, 0))
                hprInt2 = tubeNodePath.hprInterval(10, Point3(360, 360, 360), startHpr=Point3(a, b, c))
                Sequence(hprInt1, hprInt2).loop()        
                mat = Material()
                mat.setShininess(15.0)
                mat.setAmbient(VBase4(random.random(), random.random(), random.random(), 1))
                mat.setDiffuse(VBase4(random.random(), random.random(), random.random(), 1))
                mat.setSpecular(VBase4(random.random(), random.random(), random.random(), 1))
                tubeNodePath.setMaterial(mat)
        
        alight = AmbientLight('alight')
        alight.setColor(VBase4(0.2, 0.2, 0.2, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)
        
        dlight = DirectionalLight('dlight')
        dlight.setColor(VBase4(0.98, 0.98, 0.97, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(90, 315, 0)
        #dlnp.setHpr(90, 315, 0)
        self.render.setLight(dlnp)        
        
        #p0 = Point3(0, 50, 0)
        #p1 = Point3(0, 100, 50)
        #v0 = Vec3(0, 0, 50) # magnitude maybe should depend on distance between points
        #v1 = vec3mirror(v0, (p1-p0))
        #n0 = Vec3(0, -1, 0)        
        #s = HermiteSpline(p0, p1, v0, v1)       
                
        ##gf = GeomVertexFormat.getV3n3() # vertex, normal
        #gf = GeomVertexFormat.getV3() # vertex
        #vdata = GeomVertexData('tube', gf, Geom.UHStatic)
        #vertex = GeomVertexWriter(vdata, 'vertex')
        ##normal = GeomVertexWriter(vdata, 'normal')
        #num = 30       
        #for i in range(0, num):
            #p,v = s.evalat(i / num)
            #vertex.addData3f(p[0], p[1], p[2])
        
#        for i in range(0, num):            
            #p,v = s.evalat(i / num)
            #if i == 0:
                #n = n0
            #else:
             #   n = normfinder(s, n, (i-1) / num, i / num, 10)            
            #vertex.addData3f(p[0] + n[0], p[1] + n[1], p[2] + n[2])
            
        # true path
        #prim = GeomLinestrips(Geom.UHStatic)            
        #prim.addConsecutiveVertices(0, num)
        #prim.closePrimitive()
        #geom = Geom(vdata)
        #geom.addPrimitive(prim)
        #node = GeomNode('TheLine')
        #node.addGeom(geom)
        #nodePath = self.render.attachNewNode(node)

        # normal path
        #prim = GeomLinestrips(Geom.UHStatic)            
        #prim.addConsecutiveVertices(num, num)
        #prim.closePrimitive()
        #geom = Geom(vdata)
        #geom.addPrimitive(prim)
        #node = GeomNode('TheNormalLine')
        #node.addGeom(geom)
        #nodePath = self.render.attachNewNode(node)
        
        
            #d = 16
            #for j in range(0, d+2):
                #if j >= d:
                    #j -= d
                
            #for 
            #print i/n
#        print "%f\t%f\t%f\t%f\t%f\t%f" % (p[0], p[1], p[2], v[0], v[1], v[2])        

    
    # GeomVertexFormat.getV3n3() vertex, normal
#    GeomVertexFormat.getV3n3()
        
    # GeomNode
    #  Geom
    #   GeomVertexData
    #   GeomTriangles, GeomLines, GeomTristrips, GeomLinestrips, etc
        
app = MyApp()
app.run()

        