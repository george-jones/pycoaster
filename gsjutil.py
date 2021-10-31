import numpy as np
from scipy import interpolate
from math import pi, cos, sin, atan2
from panda3d.core import *
import inspect

def objectKeysDump(o):
    return '\n'.join([k for k in dir(o)])

def linemaker(p1, p2):
    """ makes line from p1 to p2
    """
    node = GeomNode('line')
    gf = GeomVertexFormat.getV3()
    vdata = GeomVertexData('line', gf, Geom.UHStatic)
    vwrite = GeomVertexWriter(vdata, 'vertex')    
    vwrite.addData3f(p1)
    vwrite.addData3f(p2)
    geom = Geom(vdata)
    prim = GeomLines(Geom.UHStatic)
    prim.addVertex(0)
    prim.addVertex(1)
    prim.closePrimitive()
    geom.addPrimitive(prim)    
    node.addGeom(geom)
    return node

def floormaker(numrepeat):
    node = GeomNode('floor')
    gf = GeomVertexFormat.getV3n3t2() # vertex, normal, texture    
    vdata = GeomVertexData('floor', gf, Geom.UHStatic)
    vwrite = GeomVertexWriter(vdata, 'vertex')
    nwrite = GeomVertexWriter(vdata, 'normal')
    twrite = GeomVertexWriter(vdata, 'texcoord')
    geom = Geom(vdata)
    prim = GeomTriangles(Geom.UHStatic)
    
    vwrite.addData3f(-0.5,  0.5, 0) # top-left
    vwrite.addData3f(-0.5, -0.5, 0) # bottom-left
    vwrite.addData3f( 0.5, -0.5, 0) # bottom-right
    vwrite.addData3f( 0.5,  0.5, 0) # top-right
    
    norm = Vec3(0, 0, 1)
    nwrite.addData3f(norm)
    nwrite.addData3f(norm)
    nwrite.addData3f(norm)
    nwrite.addData3f(norm)
    
    twrite.addData2f(0, 0)
    twrite.addData2f(0, numrepeat)
    twrite.addData2f(numrepeat, numrepeat)
    twrite.addData2f(numrepeat, 0)
    
    prim.addVertex(0)            
    prim.addVertex(1)
    prim.addVertex(3)
    
    prim.addVertex(3)
    prim.addVertex(1)
    prim.addVertex(2)
    
    prim.closePrimitive()
    geom.addPrimitive(prim)    
    node.addGeom(geom)
    return node

def ballmaker(n, inverted):
    node = GeomNode('ball')
    #gf = GeomVertexFormat.getV3n3() # vertex and normal
    gf = GeomVertexFormat.getV3n3t2() # vertex, normal, texture    
    vdata = GeomVertexData('ball', gf, Geom.UHStatic)
    vwrite = GeomVertexWriter(vdata, 'vertex')
    nwrite = GeomVertexWriter(vdata, 'normal')
    twrite = GeomVertexWriter(vdata, 'texcoord')
    geom = Geom(vdata)
    prim = GeomTriangles(Geom.UHStatic)
    
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
            #twrite.addData2f(atan2(p[1], p[0]) / (2*pi), 0.5+p[2]/2)
            twrite.addData2f(atan2(p[1], p[0]) / (2*pi), 0.5+p[2]/2.04)
    
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
            self.theta -= 2 * pi
        return self.poi + Point3(self.r * sin(self.theta) * cos(self.phi),
                                 self.r * sin(self.theta) * sin(self.phi),
                                 self.r * cos(self.theta))

def p3spline(a, n):
    s = [ [ ], [ ], [ ] ]
    for i in range(1, len(a)):
        x = [ None, None, None ]
        ufull = np.arange(0, 1.01, 1.0 / n)
        if i == 1:
            for j in range(0, 3):
                x[j] = np.array([ a[0][j], a[1][j] ])  
            tck, u = interpolate.splprep(x, s=0, k=1)
            out = interpolate.splev(ufull, tck, der=0)
            s[0].extend(out[0])
            s[1].extend(out[1])
            s[2].extend(out[2])
        else:
            for j in range(0, 3):
                x[j] = np.array([ out[j][-3], out[j][-2], out[j][-1], a[i][j] ])
            tck, u = interpolate.splprep(x, s=0, k=3)
            out = interpolate.splev(ufull, tck, der=0)
            s[0].extend(out[0])
            s[1].extend(out[1])
            s[2].extend(out[2])
    return s
    
#class MenuStrip(NodePath):
#    def __init__(self, height):
#        NodePath.__init__(self, 'menustrip')
#        b = ballmaker(3, False)
#        self.attachNewNode(b)            

def opfuncmaker(f, m):
    def f_inner():
        f()
        m.ignoreUp = True # don't send mouse1up event to handler mid-switch    
    return f_inner

def exceptprint(e):
    print "Exception: " + str(e)
    s = inspect.stack()
    print s[1][3]

def rotateAxis (v, v_axis, angle):
    axis = Vec3(v_axis) # copy
    axis.normalize()
    s_angle = sin(angle)
    c_angle = cos(angle)
    r1 = v * c_angle
    r2 = axis.cross(v) * s_angle
    r3 = axis * (axis.dot(v) * (1 - c_angle))
    return r1 + r2 + r3    

def absmax(a):
    m = None
    for x in a:
        if m is None or abs(x) > abs(m):
            m = x
    return m
