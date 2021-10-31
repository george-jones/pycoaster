from panda3d.core import *
import math

class CoasterSim():
    def __init__(self, numcars, carsep, course, v0, gravity):
        self.__course = course
        self.__numcars = numcars
        self.__carsep = carsep        
        self.__v = v0        
        self.__g = gravity        
        
        self.__cpos = [ None for x in range(0, numcars) ]
        self.__currseg = 0
        self.__cpos[0] = self.__course[self.__currseg]
        self.__getNextPos(0)
        self.__e = self.__getPE() + self.__getKE()
        if self.__e < 0:
            self.__e = 0

    # potential energy, depends entirely on distance from ground of cars
    # and the mass of each car (assumed to be 1)
    def __getPE(self):
        pe = 0
        for c in self.__cpos:
            pe += c[1] # y pos is distance from ground
        pe *= self.__g
        return pe
        
    def __getKE(self):
        return self.__numcars * (self.__v ** 2) / 2
    
    def __getNextPos(self, ds):
        if self.__currseg >= len(self.__course)-1:
            raise Exception("Off the end of the course")
        cs = self.__currseg
        seg = { }        
        prevpos = self.__cpos[0]
        def getseg():
            seg['p1'] = self.__course[cs]
            seg['p2'] = self.__course[cs+1]
            seg['d'] = seg['p2'] - seg['p1']
            seg['dlen'] = seg['d'].length()
            seg['ud'] = Vec3(seg['d'])
            seg['ud'].normalize()
        getseg()
        for x in range(0, self.__numcars):
            if x == 0:
                tosep = ds
            else:
                tosep = self.__carsep            
            while tosep > 0:
                p = prevpos + seg['ud'] * tosep
                trav = (p - prevpos).length()
                segd = (p - seg['p1']).length()
                if segd <= seg['dlen']:
                    tosep = 0 # done, move to next car
                    self.__cpos[x] = p
                    prevpos = p
                else:
                    # have to move to next segment
                    trav = (seg['p2'] - prevpos).length()
                    tosep -= trav
                    cs += 1
                    if cs >= len(self.__course)-1:
                        return False
                    if x == 0:
                        self.__currseg = cs                    
                    getseg()
                    prevpos = seg['p1']
        return True
    
    def __advance(self, dt):        
        ds = self.__v * dt
        if self.__getNextPos(ds) == False:
            return False
        pe = self.__getPE()
        ke = self.__e - pe
        if ke <= 0:
            return False
        self.__v = math.sqrt(2 * ke / self.__numcars)        
        return True
    
    def evaluate(self, dt):
        a = [ ]        
        a.append([ p for p in self.__cpos ])
        while self.__advance(dt) == True:
            a.append([ p for p in self.__cpos ])
        return a