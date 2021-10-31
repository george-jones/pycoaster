from pandac.PandaModules import Material
from panda3d.core import *
import geomutil
import geommaker
import numpy as np
from scipy import interpolate

class Coaster():
    def __init__(self, render):
        self.name = None
        self.creator = None
        self.color = None
        self.segments = [ ]
        self.mat = None
        self.render = render
        
    def addSegment(self, d):        
        segnum = len(self.segments)
        if segnum == 0:
            # the very first track segment
            d['n0'] = Vec3(0, 0, 1)
            d['v0'] = Vec3(0, 25, 0.25)
        else:
            # copy initial details from previous segment's endpoint
            prev = self.segments[segnum-1]
            d['p0'] = prev.getP1()
            d['v0'] = prev.getV1()
            d['n0'] = prev.getN1()
            d['a0'] = prev.getA1()
            
        d['v1'] = geomutil.vec3mirror(d['v0'], (d['p1']-d['p0']))            
                    
        s = CoasterSeg(d, self.render)
        s.setMaterial(self.mat)
        self.segments.append(s)
        
    def removeSegment(self):
        s = self.segments.pop()
        s.kill()
        
    def setColor(self, c):
        self.color = c
        self.mat = Material()
        self.mat.setShininess(15.0)
        self.mat.setAmbient(VBase4(c[0]/3, c[1]/3, c[2]/3, 1))
        self.mat.setDiffuse(c)
        self.mat.setSpecular(VBase4(1.0, 1.0, 1.0, 1))        
        
class CoasterSeg():
    def __init__(self, pt, prevseg, render):
        self.pt = pt
        self.ps = prevseg
        self.render = render
        self.points = None # points along curve
        self.ders = None # first derivative vectors
        self.endangle = 0.0
        if self.prevseg is not None:
            self.endangle = self.prevseg.getEndAngle()
        
    def setEndAngle(self, a):
        self.endangle = a
        
    def getEndAngle(self):
        return self.endangle        
    
    def makeSpline(self):
        ufull = np.arange(0, 1.01, 0.01)
        if self.ps is not None:
            pts = self.ps.getLastNPts(3).append(self.pt)
        else:
            # for initial segment, pretend that there was a prior segment from
            # y=-1 to y=0, with x=0, z=0
            pts = [ Point3(0, -0.02, 0), Point3(0, -0.01, 0), Point3(0, 0, 0), self.pt ]
        x = [ None, None, None ]
        
        # pull out individual components from Point3
        for i in range(0, 3):
            x[i] = np.array([ p[i] for p in pts ])
        tck, u = interpolate.splprep(x, s=0, k=3)
        pos = interpolate.splev(ufull, tck, der=0)
        der = interpolate.splev(ufull, tck, der=1)
        
        # make points and vectors from evaluated spline
        spts = [ ]
        for i in range(0, len(pos[0])):
            spts.append(Point3(pos[0][i], pos[1][i], pos[2][i]))
        self.points = spts
        sder = [ ]
        for i in range(0, len(der[0])):
            sder.append(Vec3(der[0][i], der[1][i], der[2][i]))
        self.ders = sder
        
    def getLastNPts(self, n):
        return self.points[-n:]
    
    def setMaterial(self, m):
        self.mat = m
        #self.tubeNodePath.setMaterial(mat)
        
    def build(self):
        pass
        #self.spline = geomutil.HermiteSpline(self.p0, self.p1, self.v0, self.v1)
        #self.n1 = geomutil.normfinder(self.spline, self.n0, 0.0, 1.0, 100)
        #tn = geommaker.tubenode('segment', self.p0, self.p1, self.v0, self.v1, self.n0, self.a0, self.a1, 1, 15, 4)
        #tnp = self.render.attachNewNode(tn)
        #tnp.setPos(self.origin)
        
    def kill(self):
        pass
        
        
# returns (node, normal at p1) 
def trackSection(seg):
    p_orig = p0
    # translate to origin.  The node itself will be positioned at the final location
    p0 = Point3(0, 0, 0)
    p1 = p1 - p_orig    

def testmakesegs():
    pts = [ Point3(5, 5, 0), Point3(10, 15, 0), Point3(15, 20, 0) ]
    prevseg = None
    segs = [ ]
    for p in pts:
        seg = CoasterSeg(p, prevseg, None)
        segs.append(seg)
        prevseg = seg
    

testmakesegs()
    
#tube = tubenode(p0, p1, v0*random.random()*2, n0, 0, pi/2, 0.25, 15, 10)
#tubeNodePath = self.render.attachNewNode(tube)
#tubeNodePath.setPos(Point3(0, 15, -5))
#mat = Material()
#mat.setShininess(15.0)
#mat.setAmbient(VBase4(random.random(), random.random(), random.random(), 1))
#mat.setDiffuse(VBase4(random.random(), random.random(), random.random(), 1))
#mat.setSpecular(VBase4(random.random(), random.random(), random.random(), 1))
#tubeNodePath.setMaterial(mat)
    