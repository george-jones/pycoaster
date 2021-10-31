from xml.etree import ElementTree
from panda3d.core import *
from coaster import *
import unittest

def xmlToCoaster(xml, render):
    t = ElementTree.XML(xml)
    return elementToCoaster(t, render)

def xyzToPoint(el):
    return Point3(float(el.get('x')), float(el.get('y')), float(el.get('z')))
    
def xyzToVec(el):
    return Vec3(float(el.get('x')), float(el.get('y')), float(el.get('z')))

def elementToCoaster(t, render):
    c = Coaster(render)
    inf = t.find('info')
    if inf is not None:
        n = inf.find('name')
        if n is not None:
            c.name = n.text
        n = inf.find('creator')
        if n is not None:
            c.creator = n.text
        n = inf.find('color')
        if n is not None:
            red = float(n.get('red'))
            green = float(n.get('green'))
            blue = float(n.get('blue'))
            c.setColor(VBase4(red, green, blue, 1))
    track = t.find('track')
    if track is not None:
        for seg in track.findall('segment'):
            d = { }
            # segment start
            n = seg.find('p0')
            if n is not None:
                d['p0'] = xyzToPoint(n)
            n = seg.find('n0')
            if n is not None:
                d['n0'] = xyzToVec(n)
            n = seg.find('a0')
            if n is not None:
                d['a0'] = float(n.text)
            # segment end
            n = seg.find('p1')
            if n is not None:
                d['p1'] = xyzToPoint(n)
            n = seg.find('a1')
            if n is not None:
                d['a1'] = float(n.text)                    
            c.addSegment(d)
    return c
