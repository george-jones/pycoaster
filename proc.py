from math import pi, sin, cos
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence
from panda3d.core import Point3
from panda3d.core import AmbientLight, DirectionalLight
from panda3d.core import VBase4
from panda3d.core import Fog
from pandac.PandaModules import Material


class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        f = Fog("Foggy")
        f.setColor(0.5, 0.5, 0.5)
        f.setExpDensity(0.05)
        self.render.setFog(f)
        
        mat = Material()
        mat.setShininess(5.0)
        mat.setAmbient(VBase4(1, 0, 0, 1))
        mat.setDiffuse(VBase4(0, 0, 1, 1))
        mat.setSpecular(VBase4(0, 1, 0, 1))
        #mat.setEmission(VBase4(0.25, 0.25, 0.25, 1.0))

        #mr = self.render.attachNewNode("someroot")
        m = self.loader.loadModel("panda")
        m.setScale(0.02, 0.02, 0.02)
        m.setPos(0, 2, -0.2)
        #m.reparentTo(mr)
        m.reparentTo(self.render)
        m.setMaterial(mat)
        
        alight = AmbientLight('alight')
        alight.setColor(VBase4(0.2, 0.2, 0.2, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)
        
        dlight = DirectionalLight('dlight')
        dlight.setColor(VBase4(0.98, 0.98, 0.97, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(90, 315, 0)
        self.render.setLight(dlnp)
        
        # Use a 512x512 resolution shadow map
        #light.setShadowCaster(True, 512, 512)
        # Enable the shader generator for the receiving nodes
        #render.setShaderAuto()
        
        
        
app = MyApp()
app.run()
        