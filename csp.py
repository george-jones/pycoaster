from __future__ import division
from math import pi, sin, cos, pow
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence
from panda3d.core import *
from pandac.PandaModules import Material
from time import clock

class LinearInterp():
    def __init__(self, p0, p1):
        # Pass in Poin3 or Vec3 for ctor
        self.p0 = p0
        self.p1 = p1
        if isinstance(p0, Point3):
            self.ctor = Point3
        elif isinstance(p0, Vec3):
            self.ctor = Vec3
        else:            
            raise Exception, "Expected Point3 or Vec3"            
        
    def evalat(self, t):
        """ Get Point3 or Vec3 at a given position.        
        """
        vals = [ ]
        for i in range(0, 3):
            vals.append(self.p0[i] * (1 - t) + self.p1[i] * t)
        return self.ctor(vals[0], vals[1], vals[2])

class HermiteSpline():
    def __init__(self, p0, p1, t0, t1):
        self.p0 = p0
        self.p1 = p1
        self.t0 = t0
        self.t1 = t1
        
    # returns tuple (Point3, Vec3) for position, tangent
    def evalat(self, t):
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
    c = v.cross(mv)
    d = mv.cross(c)
    r = v.project(mv) - v.project(d)
    return r

# gets normal vector at t1 along a spline, given normal vector n0 at t0
def normfinder(sp, n0, t0, t1, steps):    
    n = Vec3(n0[0], n0[1], n0[2])
    n.normalize()
    for i in range(0, steps+1):
        t = t0 + i * (t1 - t0) / steps        
        p, v = sp.evalat(t)
        n = v.cross(n).cross(v)        
        n.normalize()
        
    return n

def nftest():
    p0 = Point3(0, 0, 0)
    p1 = Point3(5, 10, 20)
    v0 = Vec3(2, 2, 0)
    n0 = Vec3(0, 0, 1)
    v1 = vec3mirror(v0, (p1-p0))
    #p0 = Point3(0, 50, 0)
    #p1 = Point3(10, 50, 0)
    #v0 = Vec3(0, 0, 20) # magnitude maybe should depend on distance between points
    #v1 = vec3mirror(v0, (p1-p0))
    #n0 = Vec3(0, 0, 1)
    steps = 100    
    s = HermiteSpline(p0, p1, v0, v1)
    n1 = normfinder(s, n0, 0.0, 1.0, steps)
    
    print n1

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        p0 = Point3(0, 50, 0)
        p1 = Point3(0, 100, 50)
        v0 = Vec3(0, 0, 50) # magnitude maybe should depend on distance between points
        v1 = vec3mirror(v0, (p1-p0))
        n0 = Vec3(0, -1, 0)        
        s = HermiteSpline(p0, p1, v0, v1)
                
        #gf = GeomVertexFormat.getV3n3() # vertex, normal
        gf = GeomVertexFormat.getV3() # vertex
        vdata = GeomVertexData('tube', gf, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, 'vertex')
        #normal = GeomVertexWriter(vdata, 'normal')
        num = 30       
        for i in range(0, num):
            p,v = s.evalat(i / num)
            vertex.addData3f(p[0], p[1], p[2])
            print p
        
        for i in range(0, num):            
            p,v = s.evalat(i / num)
            if i == 0:
                n = n0
            else:
                n = normfinder(s, n, (i-1) / num, i / num, 10)            
            vertex.addData3f(p[0] + n[0], p[1] + n[1], p[2] + n[2])
            
        # true path
        prim = GeomLinestrips(Geom.UHStatic)            
        prim.addConsecutiveVertices(0, num)
        prim.closePrimitive()
        geom = Geom(vdata)
        geom.addPrimitive(prim)
        node = GeomNode('TheLine')
        node.addGeom(geom)
        nodePath = self.render.attachNewNode(node)

        # normal path
        prim = GeomLinestrips(Geom.UHStatic)            
        prim.addConsecutiveVertices(num, num)
        prim.closePrimitive()
        geom = Geom(vdata)
        geom.addPrimitive(prim)
        node = GeomNode('TheNormalLine')
        node.addGeom(geom)
        nodePath = self.render.attachNewNode(node)
        
        
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
        