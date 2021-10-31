import numpy as np
from scipy import interpolate
from panda3d.core import *
import xml.etree.ElementTree as ET

loadPrcFile("config/Config.prc")

import direct.directbase.DirectStart
#from direct.showbase import DirectObject
from direct.interval.IntervalGlobal import *
from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from math import pi
import os
import random
import gsjutil
import design

# TODO
# DONE 1. Removable segments
# DONE 2. Sticky end, with proper incoming direction
# DONE 3. Angle setting
# DONE 4. Save
# DONE 5. Open
# 6. Open Dialog
# 7. Save As Dialog

# menu (see base.a2dTopLeft and base.a2dTopRight
# Save Open | Design Test Build Ride
#| Erase Sky Colors Roll

class CoasterSeg():
    def __init__(self, pos, ang, n, prev, initialUp):
        self.pos = pos
        self.ang = ang
        self.n = n
        self.prev = prev
        self.positions = None
        self.derivatives = None
        self.ups = None
        self.angles = None
        self.startParam = 0.0
        self.isLinear = False
        self.isTunnel = False
        self.isLift = False
        self.nextPos = None
        self.initialUp = initialUp        
        self.lastRails = [ None, None, None ]

    def __interpolate(self, der, stparam, endparam):
        a = [ ]
        ufull = np.arange(stparam, endparam, (endparam - stparam) / self.n)
        x = [ None, None, None ]
        prev = self.prev
        
        if self.isLinear and isinstance(prev, Point3) == False:
            prev = self.prev.pos
        
        if self.isLinear:
            # linear interpolation
            prevPos = prev
            for i in range(0, 3):
                x[i] = np.array([ prev[i], self.pos[i] ])
            self.splineInfo, u = interpolate.splprep(x, s=0, k=1)
            out = interpolate.splev(ufull, self.splineInfo, der=der)
        else:
            # cubic spline
            allPrev = prev.getPositions()
            prevPos = prev.pos
            if self.nextPos is not None:
                # invent a phony point very near the true last point that will make the
                # derivative at least be pointing the right way
                v = self.nextPos - self.pos
                v.normalize()
                v *= 0.01
                nextPos = self.pos + v
                for i in range(0, 3):
                    x[i] = np.array([ allPrev[-3][i], allPrev[-2][i], prevPos[i], self.pos[i], nextPos[i] ])
            else:
                for i in range(0, 3):
                    x[i] = np.array([ allPrev[-3][i], allPrev[-2][i], prevPos[i], self.pos[i] ])
            self.splineInfo, u = interpolate.splprep(x, s=0, k=3)
            out = interpolate.splev(ufull, self.splineInfo, der=der)
        for i in range(0, len(out[0])):
            if der == 0:
                p = Point3(out[0][i], out[1][i], out[2][i])
            else:
                p = Vec3(out[0][i], out[1][i], out[2][i])
            a.append(p)
        return a
        
    def setPositions(self):
        self.positions = self.__interpolate(0, 0.0, 1.0)
        self.derivatives = None
        self.angles = None
        
        # find the node just after the one closest to the true starting node.
        # That's where we start this segment, as far as the outside world is concerned.        
        mindist = None
        self.startParam = 0.0
        if not self.isLinear:
            prevPos = self.prev.pos
            for i in range(0, len(self.positions)):
                d = (self.positions[i] - prevPos).lengthSquared()
                if i == 0 or d < mindist:
                    mindist = d                
                else:
                    self.startParam = i * 1.0 / self.n
                    break
                if i == len(self.positions)-1:
                    self.startParam = (i-1) * 1.0 / self.n    
            # reinterpolate on new interval
            self.positions = self.__interpolate(0, self.startParam, 1.0)
        
    def setAngles(self):
        if isinstance(self.prev, Point3) or self.prev.ang == self.ang:
            self.angles = [ self.ang for i in range(0, self.n+1) ]
        else:            
            a0 = self.prev.ang
            a1 = self.ang
            x = [ np.array([ a0, a1 ]) ]
            ufull = np.arange(self.startParam, 1.0, (1.0 - self.startParam) / self.n)
            lineInfo, u = interpolate.splprep(x, s=0, k=1)
            out = interpolate.splev(ufull, lineInfo)
            self.angles = out[0]
    
    def setDerivatives(self):
        self.derivatives = self.__interpolate(1, self.startParam, 1.0)
        self.ups = None
        
    def setUps(self):
        self.ups = [ ]
        if self.initialUp is None:
            if isinstance(self.prev, Point3) == False:
                if self.prev.isLinear:
                    self.initialUp = self.prev.initialUp
                else:
                    pups = self.prev.getUps()
                    self.initialUp = pups[-1]
            else:
                raise Exception, "Can't get initialUp from fake seg"
        u = self.initialUp
        for d in self.derivatives:
            self.ups.append(u)
            s = d.cross(u)
            s.normalize()
            u = s.cross(d)
            u.normalize()
    
    def getPositions(self):
        if self.positions is None:
            self.setPositions()
        return self.positions
    
    def getAngles(self):
        if self.angles is None:
            self.setAngles()
        return self.angles
    
    def getDerivatives(self):
        if self.derivatives is None:
            self.setDerivatives()
        return self.derivatives

    def getUps(self):
        if self.derivatives is None:
            self.setDerivatives()
        if self.ups is None:
            self.setUps()
        return self.ups
    
    def toXML(self, parent):
        atts = { }
        atts['ang'] = str(self.ang)
        atts['isLinear'] = str(self.isLinear)
        atts['isTunnel'] = str(self.isTunnel)
        atts['isLift'] = str(self.isLift)
        seg = ET.SubElement(parent, "segment", attrib=atts)
        posatts = { }
        posatts['x'] = str(self.pos[0])
        posatts['y'] = str(self.pos[1])
        posatts['z'] = str(self.pos[2])
        p = ET.SubElement(seg, "pos", attrib=posatts)
        return seg
    
    def __boolattr(self, atts, attname):
        if atts[attname] == 'True':
            return True
        else:
            return False        
    
    def updateFromXML(self, x):
        a = x.attrib
        self.ang = float(a['ang'])
        self.isLinear = self.__boolattr(a, 'isLinear')
        self.isLift = self.__boolattr(a, 'isLift')
        self.isTunnel = self.__boolattr(a, 'isTunnel')

class Coaster():
    def __init__(self):
        self.segs = [ ]

    def addSeg(self, pos, ang, prev, initialUp):
        if pos is None:
            # figure out a point from the previous ones
            prevPos = prev.pos
            d = prev.getDerivatives()
            v = Vec3(d[-1])
            v.normalize()
            pos = prevPos + v * 10
            # can't be below the ground
            if pos[2] < 0:
                pos[2] = 0
        seg = CoasterSeg(pos, ang, 15, prev, initialUp)
        self.segs.append(seg)
        return seg
    
    def removeSeg(self, i):
        seg = self.segs[i]
        if i+1 < len(self.segs):
            prev = seg.prev
            nseg = self.segs[i+1]
            nseg.prev = prev
        del self.segs[i]
    
    def save(self, filename):
        root = ET.Element("coaster")
        segs = ET.SubElement(root, "segments")
        for seg in self.segs:
            seg.toXML(segs)
        tree = ET.ElementTree(root)
        tree.write(filename)
        
    def load(self, filename):
        tree = ET.parse(filename)
        root = tree.getroot()
        self.segs = [ ]
        for i,x in enumerate(root.findall('segments/segment')):
            if i == 0:
                prev = Point3(0, -10, 10)
                initialUp = Vec3(0, 0, 1)
            else:
                prev = self.segs[i-1]
                initialUp = None
            pos = self.__segXMLgetpos(x)
            cs = CoasterSeg(pos, 0.0, 15, prev, initialUp)
            cs.updateFromXML(x)
            self.segs.append(cs)
        
    def __segXMLgetpos(self, x):
        p = x.find('pos')
        pos = Point3(float(p.attrib['x']), float(p.attrib['y']), float(p.attrib['z']))
        return pos
         
class CoasterApp(DirectObject):
    def __init__(self):
        try:            
            base.disableMouse() # Disable mouse-based camera control            
            
            taskMgr.remove("mouseTask")
            self.coaster = None
            self.mainLoop = taskMgr.add(self.mouseTask, "mouseTask")
            self.mousePos = None
            self.mouse1ing = False
            self.mouse3ing = False
            self.dialoging = False
            self.currFileName = None
            
            #bgSound = loader.loadSfx("sound/boro_64kb.mp3")
            #bgSound.setVolume(0.15)
            #bgSound.play()
                    
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
                    
            alight = AmbientLight('alight')
            alight.setColor(VBase4(0.3, 0.3, 0.3, 1))
            alnp = render.attachNewNode(alight)
            render.setLight(alnp)
            
            dlight = DirectionalLight('dlight')
            dlight.setColor(VBase4(0.98, 0.98, 0.97, 1))
            dlnp = render.attachNewNode(dlight)
            dlnp.setHpr(0, -90, 0)
            render.setLight(dlnp)
                        
            actFrame = DirectFrame(parent=base.a2dTopLeft,
                              frameColor=(0.3, 0.3, 0.3, 0.35),
                              frameSize=(0.0, 1.25, -0.1, 0.0)) # left, right, bottom, top
            optFrame = DirectFrame(parent=base.a2dTopLeft,
                                   frameColor=(0.7, 0.0, 0.0, 0.35),
                                   frameSize=(0.0, 1.6, -0.1, 0.0))
            optFrame.setPos(1.25, 0, 0)
             
            btnScale = (0.2, 1.0, 0.061)
            actButtonDef = [
                { 'name': 'open', 'pos': 0.15, 'f': self.open, 'disabled': False, 'hidden': False },
                { 'name': 'save', 'pos': 0.45, 'f': self.save, 'disabled': True, 'hidden': False },
                { 'name': 'saveas', 'pos': 0.75, 'f': self.saveas, 'disabled': False, 'hidden': False },
                { 'name': 'new', 'pos': 1.05, 'f': self.newcoaster, 'disabled': False, 'hidden': False }
            ]
            optButtonDef = [
                { 'name': 'design', 'pos': 0.15, 'f': self.design, 'disabled': False, 'hidden': False },
                { 'name': 'test', 'pos': 0.55, 'f': self.noop, 'disabled': True, 'hidden': False },
                { 'name': 'build', 'pos': 0.95, 'f': self.noop, 'disabled': True, 'hidden': False },
                { 'name': 'ride', 'pos': 1.35, 'f': self.noop, 'disabled': True, 'hidden': False }
            ]
            
            self.buttons = { }
            
            frameDef = [
                { 'frame': actFrame, 'def': actButtonDef, 'btnY': -0.05 },
                { 'frame': optFrame, 'def': optButtonDef, 'btnY': -0.05 }
            ]
    
            for fd in frameDef:
                for bd in fd['def']:
                    n = bd['name']
                    maps = loader.loadModel('img/buttons/%s.egg' % (n))
                    b = DirectButton(parent=fd['frame'],
                        geom=(maps.find('**/%s_active' % (n)),
                                           maps.find('**/%s_click' % (n)),
                                           maps.find('**/%s_hover' % (n)),
                                           maps.find('**/%s_disabled' % (n))),
                                     command=gsjutil.opfuncmaker(bd['f'], self))
                    #b.reparentTo(fd['frame'])
                    b['frameVisibleScale'] = (0, 0)
                    b.setScale(btnScale)
                    b.setPos((bd['pos'], 0, fd['btnY']))
                    if bd['disabled']:
                        b['state'] = DGG.DISABLED
                    if bd['hidden']:                        
                        b.hide()
                    self.buttons[n] = b
                        
            self.cam = gsjutil.CamInfo(Point3(0, 0, 0), -pi/2, pi/2, 200)
            self.collPlane = self.collisionPlane(self.cam.r)
            self.linearMode = False
            self.cursky = None
            self.curfloor = None
            self.curHandler = None
            self.ignoreUp = False
            self.design()
        except Exception, e:
            gsjutil.exceptprint(e)
    
    def noop(self):
        pass
        
    def handlerSwitch(self):
        if self.curHandler is not None:
            self.curHandler.done()
            self.curHandler = None            
    
    def newcoaster(self):
        if self.dialoging == True:
            return
        self.handlerSwitch()
        self.coaster = None
        self.design()
    
    def save(self):
        if self.dialoging == True:
            return        
        self.coaster.save(self.currFileName)
        
    def saveas(self):
        if self.dialoging == True:
            return
        self.file_saveas_dialog()        
        
    def open(self):
        if self.dialoging == True:
            return        
        self.file_open_dialog()
        
    def design(self):
        if self.dialoging == True:
            return        
        try:
            self.handlerSwitch()
            if self.coaster is None:
                self.coaster = Coaster()
                pts = [ Point3(0, -10, 10),
                        Point3(0, 0, 10)
                        ]
                prev = pts[0]
                for i, p in enumerate(pts):
                    if i > 0:
                        prev = self.coaster.addSeg(p, 0, prev, Vec3(0, 0, 1))
                        if i == 1:
                            prev.isLinear = True
            self.curHandler = design.Design(self, self.coaster)
        except Exception, e:
            gsjutil.exceptprint(e)
        
    def collisionPlane(self, r):
        try:
            cp = CollisionPlane(Plane(Vec3(0, -1, 0), Point3(0, r, 0)))
            cn = CollisionNode('pickingplane')
            cn.addSolid(cp)
            pn = camera.attachNewNode(cn)
            pn.setTag('plane', 'main')
            return pn, cp
        except Exception, e:
            gsjutil.exceptprint(e)
    
    def unsky(self):
        try:
            if self.cursky is not None:
                self.cursky.remove()
                self.cursky = None        
        except Exception, e:
            gsjutil.exceptprint(e)
            
    def sky(self, texName):
        try:
            self.unsky()
            b = gsjutil.ballmaker(4, True)
            bp = render.attachNewNode(b)
            bp.setPos(Point3(0, 0, 0))
            bp.setScale(1500, 1500, 1500)
            tex = loader.loadTexture(texName)
            bp.setTexture(tex)
            mat = Material()
            mat.setEmission(VBase4(0.5, 0.5, 0.5, 1))
            bp.setMaterial(mat)
            self.cursky = bp
        except Exception, e:
            gsjutil.exceptprint(e)

    def unfloor(self):
        try:
            if self.curfloor is not None:
                self.curfloor.remove()
                self.curfloor = None        
        except Exception, e:
            gsjutil.exceptprint(e)
            
    def floor(self, texName):
        try:
            self.unfloor()
            f = gsjutil.floormaker(50)
            fp = render.attachNewNode(f)
            # slightly below z=0 so that stuff that skims the surface will not cause z-fighting
            fp.setPos(Point3(0, 0, -0.01))
            fp.setScale(3000, 3000, 1)
            tex = loader.loadTexture(texName)
            fp.setTexture(tex)
            mat = Material()
            fp.setMaterial(mat)
            self.curfloor = fp
            
        except Exception, e:
            gsjutil.exceptprint(e)
        
    def mouseFindTagged(self, tag, tagval):
        try:
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
        except Exception, e:
            gsjutil.exceptprint(e)
                    
    def mouse1Down(self):        
        try:
            if self.dialoging == True:
                return
            if self.curHandler is not None and base.mouseWatcherNode.hasMouse():
                self.curHandler.mouse1Down()
        except Exception, e:
            gsjutil.exceptprint(e)
                
    def mouse1Up(self):
        try:
            if self.dialoging == True:
                return            
            if self.ignoreUp:
                self.ignoreUp = False
                return
            if self.curHandler is not None and base.mouseWatcherNode.hasMouse():
                self.curHandler.mouse1Up()
        except Exception, e:
            gsjutil.exceptprint(e)
                    
    def mouse2Up(self):
        try:
            if self.dialoging == True:
                return            
            if self.curHandler is not None and base.mouseWatcherNode.hasMouse():
                self.curHandler.mouse2Up()
        except Exception, e:
            gsjutil.exceptprint(e)
    
    def mouse3Down(self):
        try:
            if self.dialoging == True:
                return            
            if self.curHandler is not None:
                self.curHandler.release()
            self.mouse3ing = True
        except Exception, e:
            gsjutil.exceptprint(e)
        
    def mouse3Up(self):
        try:
            if self.dialoging == True:
                return            
            self.mouse3ing = False
        except Exception, e:
            gsjutil.exceptprint(e)
        
    def wheelDown(self):
        try:
            if self.dialoging == True:
                return            
            if self.curHandler is not None:
                self.curHandler.release()
            self.cam.r *= 1.1
            self.reCamera()
        except Exception, e:
            gsjutil.exceptprint(e)
    
    def wheelUp(self):
        try:
            if self.dialoging == True:
                return            
            self.mouse1ing = False
            self.cam.r *= 0.9
            if self.cam.r < 2:
                self.cam.r = 2
            self.reCamera()
        except Exception, e:
            gsjutil.exceptprint(e)
        
    def mouseTask(self, task):
        try:
            #if self.dialoging == True:
             #   return            
            if base.mouseWatcherNode.hasMouse():
                # getMouse doesn't return a copy - it returns the same object every time.            
                mp = Point2(base.mouseWatcherNode.getMouse())
                if self.mousePos is not None and (mp[0] != self.mousePos[0] or mp[1] != self.mousePos[1]):                
                    diff = mp - self.mousePos
                    if self.mouse3ing:
                        self.cam.phi -= diff[0]
                        self.cam.theta += diff[1]
                        self.reCamera()
                    elif self.curHandler is not None:
                        self.curHandler.mouseMove()
                self.mousePos = mp            
            return Task.cont
        except Exception, e:
            gsjutil.exceptprint(e)
    
    def reCamera(self):
        try:           
            hpr = self.cam.getHpr()
            pos = self.cam.getPos()
            # no looking under the floor
            if pos[2] < 1:
                pos[2] = 1    
            camera.setHpr(hpr)
            camera.setPos(pos)
            self.collPlaneSetDist(self.cam.r)
        except Exception, e:
            gsjutil.exceptprint(e)
    
    def collPlaneSetDist(self, d):
        try:
            curpn, cplane = self.collPlane
            cplane.setPlane(Plane(Vec3(0, -1, 0), Point3(0, d, 0)))
        except Exception, e:
            gsjutil.exceptprint(e)
        
    def collPlaneSet(self, pos):
        try:
            vpoi = Vec3(self.cam.poi - self.cam.getPos())
            dpoi = vpoi.length()
            vpoi.normalize()
            d = dpoi + vpoi.dot(Vec3(pos - self.cam.poi))
            self.collPlaneSetDist(d)
        except Exception, e:
            gsjutil.exceptprint(e)

    def file_open_dialog(self):
        self.dialoging = True
        try:
            all_frames = [ ]
            for i in range(0, 4):
                d = 0.005 * i
                f = DirectFrame(parent=base.a2dTopCenter,
                                frameColor=(1.0, 1.0, 1.0, 0.35),
                                frameSize=(-1.0 + d, 1.0 - d, -2.0 + d, -0.1 - d),
                                pos=(0, i, 0))
                all_frames.append(f)
            
            openLabel = DirectLabel(f, text="Open Coaster", text_scale=0.1, pad=(0.02, 0.02), frameColor=(0.0, 0.0, 0.0, 0.0))
            openLabel.setPos((-0.6, 0, -0.25))
                    
            def cleanup():
                for frm in all_frames:
                    frm.destroy()                        
                self.dialoging = False

            cancelButton = DirectButton(f,
                                        text = 'Cancel',
                                        relief = DGG.FLAT,
                                        frameSize = (0.0, 0.5, 0.0, -0.15),
                                        text_scale = 0.08,
                                        text_pos = (0.25, -0.1),
                                        color = (1.0, 0.7, 0.7, 0.8),
                                        command = cleanup)
            cancelButton.setPos((0.0, 0, -0.16))
                
            def makeButton(itemName, itemNum, *extraArgs):            
                def buttonCommand():
                    try:
                        cleanup()
                        self.coaster = Coaster()
                        self.currFileName = 'saved/' + itemName + '.xml'
                        self.coaster.load(self.currFileName)
                        self.design()
                        self.buttons['save']['state'] = DGG.NORMAL
                    except Exception, ex:
                        gsjutil.exceptprint(ex)
                return DirectButton(text = itemName,
                                    relief = DGG.FLAT,
                                    frameSize = (0.0, 1.4, 0.0, -0.15),
                                    text_scale = 0.08,
                                    text_pos=(0.7, -0.1),
                                    color=(1.0, 1.0, 0.8, 0.8),
                                    command = buttonCommand)
            
            items = [ ]
            for fn in os.listdir("saved"):
                if len(fn) > 4:
                    if fn[-4:] == '.xml':
                        name = fn[:-4]
                        items.append(name)
            
            sl = DirectScrolledList(f, pos=(-0.75, 0, -0.4), frameSize=(0, 1.5, 0.0, -1.5),
                                        decButton_pos=(1.475, 0, -0.025),
                                        decButton_scale = 0.25,
                                        incButton_pos=(1.475, 0, -1.475),
                                        incButton_scale = 0.25,
                                        numItemsVisible=7,
                                        forceHeight=0.20,
                                        frameColor=(0.0, 0.0, 0.0, 0.15),
                                        itemFrame_frameSize=(0.0, 1.4, 0.0, -1.4),
                                        itemFrame_pos=(0.05, 0, -0.05),
                                        itemFrame_color=(1.0, 1.0, 1.0, 0.5),
                                        items=items,
                                        itemMakeFunction = makeButton)
        except Exception, ex:
            gsjutil.exceptprint(ex)        

    def file_saveas_dialog(self):
        self.dialoging = True
        try:
            all_frames = [ ]
            for i in range(0, 4):
                d = 0.005 * i
                f = DirectFrame(parent=base.a2dTopCenter,
                                frameColor=(1.0, 1.0, 1.0, 0.35),
                                frameSize=(-1.0 + d, 1.0 - d, -2.0 + d, -0.1 - d),
                                pos=(0, i, 0))
                all_frames.append(f)
            
            saveLabel = DirectLabel(f, text="Save Coaster", text_scale=0.1, pad=(0.02, 0.02), frameColor=(0.0, 0.0, 0.0, 0.0))
            saveLabel.setPos((-0.6, 0, -0.25))
            
            nameLabel = DirectLabel(f, text="Coaster Name", text_scale=0.08, pad=(0.02, 0.02), frameColor=(0.0, 0.0, 0.0, 0.0))
            nameLabel.setPos((-0.6, 0, -0.45))
            
            def cleanup():
                for frm in all_frames:
                    frm.destroy()
                self.dialoging = False
            
            entry = None            
            def entrydo(text):
                if len(text) > 0:
                    self.currFileName = 'saved/' + text + '.xml'
                    cleanup()
                    self.save()
                    self.buttons['save']['state'] = DGG.NORMAL
                
            def savebuttoned():
                entrydo(entry.get())
            
            entry = DirectEntry(f, command=entrydo, width=15, focus=1, text_scale=0.08)
            entry.setPos((-0.6, 0, -0.75))        

            saveButton = DirectButton(f,
                                        text = 'Save',
                                        relief = DGG.FLAT,
                                        frameSize = (0.0, 0.5, 0.0, -0.15),
                                        text_scale = 0.08,
                                        text_pos = (0.25, -0.1),
                                        color = (1.0, 1.0, 0.7, 0.8),
                                        command = savebuttoned)
            saveButton.setPos((-0.75, 0, -1.0))                
                
            cancelButton = DirectButton(f,
                                        text = 'Cancel',
                                        relief = DGG.FLAT,
                                        frameSize = (0.0, 0.5, 0.0, -0.15),
                                        text_scale = 0.08,
                                        text_pos = (0.25, -0.1),
                                        color = (1.0, 0.7, 0.7, 0.8),
                                        command = cleanup)
            cancelButton.setPos((0.0, 0, -1.0))
                
        except Exception, ex:
            gsjutil.exceptprint(ex)            
        
app = CoasterApp()
run()