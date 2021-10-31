from panda3d.core import *
from direct.gui.DirectGui import *
from math import pi
import gsjutil

class Design():

    ballsize = 2
    endballsize = 1.5
    
    def __init__(self, m, coaster):        
        self.__mouse1ing = False
        self.__heldBall = None        
        self.__currBall = None
        self.__endball = None
        self.__ballNodes = [ ]
        self.__segSplines = [ ]
        self.__main = m
        self.__coaster = coaster
        self.__linearMode = False
        self.__tunnelMode = False
        self.__liftMode = False
        self.__buttonFrame = None
        self.__ballTrav = CollisionTraverser('ballTrav')
        self.__ballQ = CollisionHandlerQueue()
        self.__rotating = False
        self.__rotatingPrev = None
        
        cam = m.cam
        cam.phi = -pi/2
        cam.theta = 0
        cam.poi = Point3(0, 0, 0)
        cam.r = 200
        m.reCamera()            
            
        self.__mat = { }
                
        mat = Material()
        c = VBase4(0.0, 1.0, 0.0, 1)
        mat.setShininess(100)
        mat.setAmbient(c)
        mat.setDiffuse(c)
        mat.setSpecular(VBase4(1, 1, 1, 1.0))
        self.__mat['startball'] = mat
        
        mat = Material()
        c = VBase4(1.0, 0.0, 0.0, 1)
        mat.setShininess(100)
        mat.setAmbient(c)
        mat.setDiffuse(c)
        mat.setSpecular(VBase4(1, 1, 1, 1.0))
        self.__mat['endball'] = mat

        mat = Material()
        c = VBase4(1.0, 1.0, 0.75, 1)
        mat.setShininess(100)
        mat.setAmbient(c)
        mat.setDiffuse(c)
        mat.setSpecular(VBase4(1, 1, 1, 1.0))
        self.__mat['regularball'] = mat

        mat = Material()
        c = VBase4(0.75, 0.75, 0.0, 1)
        mat.setShininess(100)
        mat.setAmbient(c)
        mat.setDiffuse(c)
        mat.setSpecular(VBase4(1, 1, 1, 1.0))
        self.__mat['currentball'] = mat

        mat = Material()
        c = VBase4(0.0, 0.0, 0.0, 1)
        mat.setShininess(1)
        mat.setAmbient(c)
        mat.setDiffuse(c)        
        self.__mat['line'] = mat

        mat = Material()
        c = VBase4(0.0, 0.0, 1.0, 1)
        mat.setShininess(1)
        mat.setAmbient(c)
        mat.setDiffuse(c)        
        self.__mat['line_tunnel'] = mat

        mat = Material()
        c = VBase4(1.0, 0.0, 0.0, 1)
        mat.setShininess(1)
        mat.setAmbient(c)
        mat.setDiffuse(c)        
        self.__mat['line_lift'] = mat
        
        mat = Material()
        c = VBase4(0.49, 0.15, 0.5, 0.8)
        mat.setShininess(1)
        mat.setAmbient(c)
        mat.setDiffuse(c)        
        self.__mat['line_tunnellift'] = mat
        
        m.sky("img/designskylines.png")        
        m.floor("img/designfloor.png")                
        for i, seg in enumerate(self.__coaster.segs):
            self.__makeBalls(seg, i)
            self.__makeSegSplines(seg, i)
        
        desButtonDef = [
            { 'name': 'rotate', 'pos': -0.05, 'f': self.__rotate, 'disabled': False, 'hidden': False },
            { 'name': 'curve', 'pos': -0.125, 'f': self.__curvelinear, 'disabled': False, 'hidden': False },
            { 'name': 'linear', 'pos': -0.125, 'f': self.__curvelinear, 'disabled': False, 'hidden': True },
            { 'name': 'liftoff', 'pos': -0.2, 'f': self.__lifttoggle, 'disabled': False, 'hidden': False },
            { 'name': 'lifton', 'pos': -0.2, 'f': self.__lifttoggle, 'disabled': False, 'hidden': True },
            { 'name': 'tunneloff', 'pos': -0.275, 'f': self.__tunneltoggle, 'disabled': False, 'hidden': False },
            { 'name': 'tunnelon', 'pos': -0.275, 'f': self.__tunneltoggle, 'disabled': False, 'hidden': True },
            { 'name': 'remove', 'pos': -0.35, 'f': self.__remove, 'disabled': False, 'hidden': False }
        ]
        
        self.__buttons = { }
        
        btnY = 0.85

        desFrame = DirectFrame(parent=base.a2dTopLeft,
                               frameColor=(1.0, 0.78, 0.0, 0.35),
                               frameSize=(0.0, 0.1, -0.4, 0.0))
        desFrame.setPos(0.0, 0.0, -0.1)
        self.__buttonFrame = desFrame
        btnScale = (0.2, 1.0, 0.061)
        for bd in desButtonDef:
            n = bd['name']
            imgn = 'des_' + n
            maps = loader.loadModel('img/buttons/%s.egg' % (imgn))
            b = DirectButton(parent=desFrame,
                             geom=(maps.find('**/%s_active' % (imgn)),
                                   maps.find('**/%s_click' % (imgn)),
                                   maps.find('**/%s_hover' % (imgn)),
                                   maps.find('**/%s_disabled' % (imgn))),
                             command=gsjutil.opfuncmaker(bd['f'], self.__main))            
            b['frameVisibleScale'] = (0, 0)
            b.setScale(btnScale)
            b.setPos((0.05, 0, bd['pos']))
            if bd['disabled']:
                b['state'] = DGG.DISABLED
            if bd['hidden']:                        
                b.hide()
            self.__buttons[n] = b
        
    def __noop(self):
        pass
    
    def __remove(self):
        if self.__currBall is not None:
            n = int(self.__currBall.getTag('segNum'))
            self.__currBall.remove()
            self.__currBall = None
            del self.__ballNodes[n]
            for np in self.__segSplines[n]:
                np.remove()
            del self.__segSplines[n]
            self.__coaster.removeSeg(n)
            #renumber balls
            for i in range(n, len(self.__ballNodes)):                
                self.__ballNodes[i].setTag('segNum', str(i))
            self.__redrawRange(n, None, None)
    
    def __makeBalls(self, seg, i):
        if len(self.__ballNodes) > i:            
            bn = self.__ballNodes[i]
            if bn is not None:
                bn.remove()
                self.__ballNodes[i] = None
        else:
            for j in range(len(self.__ballNodes), i+1):                
                self.__ballNodes.append(None)
        points = [ ]
        nodes = [ ]
        if i == 0:
            points.append(seg.prev)
        points.append(seg.pos)
        for j, p in enumerate(points):
            if i == 0:
                if j == 0:
                    # final point
                    tagval = 'end'
                    mat = self.__mat['endball']
                    sz = self.endballsize
                else:
                    # starting point
                    tagval = 'start'
                    mat = self.__mat['startball']
                    sz = self.endballsize
            else:
                # real track points!
                tagval = 'real'
                mat = self.__mat['regularball']
                sz = self.ballsize
            b = gsjutil.ballmaker(2, False)
            bp = render.attachNewNode(b)
            bp.setPos(p)            
            bp.setScale(sz, sz, sz)
            bp.setMaterial(mat)
            bp.setTag('pickaBall', tagval)
            bp.setTag('segNum', str(i))
            cs = CollisionSphere(0, 0, 0, 1)
            cnp = bp.attachNewNode(CollisionNode('cnode'))
            cnp.node().addSolid(cs)            
            if i > 0 or j == 1:
                self.__ballNodes[i] = bp
            else:
                self.__endball = bp
                self.__ballTrav.addCollider(cnp, self.__ballQ)
            
    def __makeSegSplines(self, seg, i):
        # create splines segments between points
        if len(self.__segSplines) <= i:
            self.__segSplines.extend([[ ] for j in range(len(self.__segSplines)-1, i+1)])
        else:
            for np in self.__segSplines[i]:
                np.remove()
        sp = seg.getPositions()
        ders = seg.getDerivatives()
        ups = seg.getUps()
        angs = seg.getAngles()
        allpos = [ ]
        ss = [ ]
        
        if seg.isTunnel:
            if seg.isLift:
                m = self.__mat['line_tunnellift']
            else:
                m = self.__mat['line_tunnel']                
        else:
            if seg.isLift:
                m = self.__mat['line_lift']
            else:
                m = self.__mat['line']
            
        # add all points from current segment
        allpos.extend(sp)
        
        # plus the real endpoint
        allpos.append(seg.pos)
        
        r1prev = None
        r2prev = None
        # make sure none of the points go below the ground
        for p in allpos:
            if p[2] < 0:
                p[2] = 0
        for j in range(1, len(allpos)):
            p = allpos[j]
            der = ders[j - 1]
            u = ups[j - 1]
            a = angs[j - 1] # trouble here
            
            # current angle effects our opinion of what "up" is
            u = gsjutil.rotateAxis(u, der, a)
            
            n1 = der.cross(u)
            n1.normalize()
            n2 = u.cross(der)
            n2.normalize()  
            pn1 = p + n1
            pn2 = p + n2
            # horizontal bar
            b = gsjutil.linemaker(pn1, pn2)
            bp = render.attachNewNode(b)
            bp.setMaterial(m)
            ss.append(bp)
            r1 = pn1 + u/2
            r2 = pn2 + u/2
            # bar up to right rail
            b = gsjutil.linemaker(pn1, r1)
            bp = render.attachNewNode(b)
            bp.setMaterial(m)
            ss.append(bp)
            # bar up to left rail
            b = gsjutil.linemaker(pn2, r2)
            bp = render.attachNewNode(b)
            bp.setMaterial(m)
            ss.append(bp)            
            # rails
            if r1prev is None:
                if isinstance(seg.prev, Point3) == False:
                    r1prev = seg.prev.lastRails[0]
                    r2prev = seg.prev.lastRails[1]
                    r3prev = seg.prev.lastRails[2]
                
            if r1prev is not None:
                # right
                b = gsjutil.linemaker(r1prev, r1)
                bp = render.attachNewNode(b)
                bp.setMaterial(m)
                ss.append(bp)
                # left
                b = gsjutil.linemaker(r2prev, r2)
                bp = render.attachNewNode(b)
                bp.setMaterial(m)
                ss.append(bp)                    
                # middle
                b = gsjutil.linemaker(r3prev, p)
                bp = render.attachNewNode(b)
                bp.setMaterial(m)
                ss.append(bp)
                if j == len(allpos)-1:
                    seg.lastRails = [ r1, r2, p ]
            r1prev = r1
            r2prev = r2
            r3prev = p
        self.__segSplines[i] = ss
    
    def __setCurrBall(self, ball):
        # make sure it isn't the start or end node
        tag = ball.getTag('pickaBall')
        if tag == 'start' or tag == 'end':
            return
        if self.__currBall is not None:
            self.__currBall.setMaterial(self.__mat['regularball'])
        self.__currBall = ball
        self.__currBall.setMaterial(self.__mat['currentball'])
        segn = int(self.__currBall.getTag('segNum'))
        seg = self.__coaster.segs[segn]
        self.__linearMode = seg.isLinear        
        self.__button_set_linear()
        self.__tunnelMode = seg.isTunnel
        self.__button_set_tunnel()
        self.__liftMode = seg.isLift
        self.__button_set_lift()
    
    def __button_set_linear(self):        
        if self.__linearMode:
            self.__buttons['curve'].hide()
            self.__buttons['linear'].show()
        else:
            self.__buttons['linear'].hide()
            self.__buttons['curve'].show()
    
    def __curvelinear(self):
        try:
            if self.__linearMode:
                mode = False
            else:
                mode = True
            self.__linearMode = mode
            self.__button_set_linear()       
            if self.__currBall is not None:
                self.setLinear(mode)
        except Exception, e:
            gsjutil.exceptprint(e)
            
    def __rotate(self):
        self.__rotating = True
        self.__rotatingPrev = None

    def __button_set_tunnel(self):
        if self.__tunnelMode:
            self.__buttons['tunneloff'].hide()
            self.__buttons['tunnelon'].show()
        else:
            self.__buttons['tunnelon'].hide()
            self.__buttons['tunneloff'].show()
    
    def __tunneltoggle(self):
        try:
            if self.__tunnelMode:
                mode = False
            else:
                mode = True
            self.__tunnelMode = mode
            self.__button_set_tunnel()       
            if self.__currBall is not None:
                self.setTunnelMode(mode)
        except Exception, e:
            gsjutil.exceptprint(e)
            
    def __button_set_lift(self):
        if self.__liftMode:
            self.__buttons['liftoff'].hide()
            self.__buttons['lifton'].show()
        else:
            self.__buttons['lifton'].hide()
            self.__buttons['liftoff'].show()
    
    def __lifttoggle(self):
        try:
            if self.__liftMode:
                mode = False
            else:
                mode = True
            self.__liftMode = mode
            self.__button_set_lift()       
            if self.__currBall is not None:
                self.setLiftMode(mode)
        except Exception, e:
            gsjutil.exceptprint(e)              
            
    def mouse1Down(self):        
        self.__mouse1ing = True
        ball, e = self.__main.mouseFindTagged('pickaBall', 'real')
        if ball is not None:
            self.__heldBall = ball
            self.__setCurrBall(ball)
            self.__main.collPlaneSet(self.__heldBall.getPos())
        else:
            ball, e = self.__main.mouseFindTagged('pickaBall', 'start')
            if ball is not None:
                pass
            else:
                ball, e = self.__main.mouseFindTagged('pickaBall', 'end')
                if ball is not None:
                    pass
    
    def mouse1Up(self):
        if self.__rotating:            
            self.__rotating = False
            self.__rotatingPrev = None
        elif self.__heldBall is not None:
            self.release()
        else:
            # add another segment to the end
            seg = self.__coaster.segs[-1]
            isLinear = False            
            if len(self.__coaster.segs) > 1:
                isLinear = seg.isLinear
            isTunnel = seg.isTunnel
            isLift = seg.isLift            
            newseg = self.__coaster.addSeg(None, seg.ang, seg, None)
            newseg.isLinear = isLinear
            newseg.isTunnel = isTunnel
            newseg.isLift = isLift
            si = len(self.__coaster.segs)-1
            self.__makeBalls(newseg, si)
            self.__makeSegSplines(newseg, si)
            self.__setCurrBall(self.__ballNodes[-1])
            self.setLinear(isLinear)
            self.setTunnelMode(isTunnel)
            self.setLiftMode(isLift)
    
    def mouse2Down(self):
        pass
    
    def mouse2Up(self):
        """ move camera on middle-click
        """
        cam = self.__main.cam
        b, e = self.__main.mouseFindTagged('pickaBall', None)                        
        if b is not None:
            pos = b.getPos()
            self.__setCurrBall(b)
        else:
            pos = Point3(0, 0, 0)            
        d = (cam.getPos() - pos).length()
        cam.r = d
        cam.poi = pos
        self.release()
        self.__main.reCamera()
    

    def __redrawRange(self, idx0, idx1, repos):
        if idx1 is not None:
            nmax = idx1+1
            if nmax >= len(self.__coaster.segs):
                nmax = len(self.__coaster.segs)
        else:
            nmax = len(self.__coaster.segs)
        for i in range(idx0, nmax):
            seg = self.__coaster.segs[i]
            if i == idx0 and repos is not None:
                seg.pos = repos
            seg.setPositions()
            if i > 0:
                seg.initialUp = None
                seg.ups = None            
            self.__makeSegSplines(seg, i)        
    
    def __endBallCollider(self, ball, n):
        self.__ballTrav.traverse(render)
        for i in range(self.__ballQ.getNumEntries()):
            entry = self.__ballQ.getEntry(i)
            p = entry.getIntoNodePath().findNetTag('pickaBall')
            if not p.isEmpty() and p == ball:
                return self.__connectEnd(ball, n)        
        return None
    
    def __connectEnd(self, ball, n):
        p = self.__endball.getPos()
        ball.setPos(p)
        s = self.__coaster.segs[n]
        s.positions = None
        s.derivatives = None
        s.pos = p
        s.nextPos = self.__coaster.segs[0].pos
        return p
                
    def mouseMove(self):
        n = None
        if self.__rotating:
            if self.__currBall is not None:
                n = int(self.__currBall.getTag('segNum'))
                planeNode, e = self.__main.mouseFindTagged('plane', 'main')
                #curpn, cplane = self.__main.collPlane
                sp = e.getSurfacePoint(planeNode)
                #print sp
                #gsj
                seg = self.__coaster.segs[n]
                if self.__rotatingPrev is not None:                    
                    dx = sp[0] - self.__rotatingPrev[0]
                    dz = (sp[2] - self.__rotatingPrev[2])
                    d = gsjutil.absmax((dx, dz))
                    seg.ang += d / 50
                self.__rotatingPrev = sp
                sp = None # we don't want to move the ball
        else:
            if self.__heldBall is not None:
                n = int(self.__heldBall.getTag('segNum'))
                planeNode, e = self.__main.mouseFindTagged('plane', 'main')
                sp = e.getSurfacePoint(render)            
                # don't let points go under the floor
                if sp[2] < 0:
                    sp[2] = 0
                self.__heldBall.setPos(sp)                
                if n == len(self.__coaster.segs)-1:
                    t = self.__endBallCollider(self.__heldBall, n)
                    if t is not None:
                        sp = t
                    else:
                        self.__coaster.segs[n].nextPos = None
        if n is not None:
            self.__redrawRange(n, n+2, sp)
            
    def release(self):
        if self.__heldBall is not None:
            n = int(self.__heldBall.getTag('segNum'))            
            self.__redrawRange(n, None, None)
        self.__mouse1ing = False
        self.__heldBall = None
        
    def done(self):
        n = [ ]
        if self.__endball is not None:
            n.append(self.__endball)
        for a in self.__ballNodes:
            n.append(a)
        for a in self.__segSplines:
            n.extend(a)
        for pn in n:
            pn.remove()
        self.__buttonFrame.remove()
            
    def setLinear(self, linearMode):
        self.__linearMode = linearMode
        if self.__currBall is not None:
            n = int(self.__currBall.getTag('segNum'))
            self.__coaster.segs[n].isLinear = linearMode
            self.__redrawRange(n, n+6, None)
            
    def setTunnelMode(self, mode):
        self.__tunnelMode = mode
        if self.__currBall is not None:
            n = int(self.__currBall.getTag('segNum'))
            self.__coaster.segs[n].isTunnel = mode
            self.__redrawRange(n, n, None)

    def setLiftMode(self, mode):
        self.__liftMode = mode
        if self.__currBall is not None:
            n = int(self.__currBall.getTag('segNum'))
            self.__coaster.segs[n].isLift = mode
            self.__redrawRange(n, n, None)