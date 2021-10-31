from __future__ import division
from math import pi, sin, cos, pow
from numbers import Number
from panda3d.core import *

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