from __future__ import division
from math import pi, sin, cos, pow
from panda3d.core import *
import geomutil

def tubenode(name, p0, p1, v0, v1, n0, a0, a1, r, num, perseg):
    a0 = a0 + pi/8
    a1 = a1 + pi/8
    node = GeomNode(name)    
    gf = GeomVertexFormat.getV3n3() # vertex
    vdata = GeomVertexData('tube', gf, Geom.UHStatic)    
    vwrite = GeomVertexWriter(vdata, 'vertex')
    nwrite = GeomVertexWriter(vdata, "normal")
    geom = Geom(vdata)
    # number of segments -> number of points
    if num % 2 == 1:
        num += 1    
    s = geomutil.HermiteSpline(p0, p1, v0, v1)
    aint = geomutil.LinearInterp(a0, a1)
    
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
            n = geomutil.normfinder(s, n, tprev, t, 5)
        ang = aint.evalat(t)        
        vals.append([ p, tg, n, ang ])        
        # get vertices        
        for j in range(0, perseg):
            a = ang + (j / perseg) * (2 * pi)
            na = geomutil.rotateaxis(n, tg, a)
            pj = p + na*r
            vwrite.addData3f(pj)
            nwrite.addData3f(na)            
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