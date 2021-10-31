from panda3d.core import *
import numpy as np
from scipy import interpolate
import matplotlib.pyplot as plt

def simple():
    x = np.arange(0, 10)
    y = np.exp(-x/3.0)
    f = interpolate.interp1d(x, y)
    
    xnew = np.arange(0, 9, 0.1)
    plt.plot(x, y, 'o', xnew, f(xnew), '-')
    plt.show()
    
def paramspline():
    x = np.arange(0,2*np.pi+np.pi/4,2*np.pi/8)
    y = np.sin(x)
    tck = interpolate.splrep(x,y,s=0)
    xnew = np.arange(0,2*np.pi,np.pi/50)
    ynew = interpolate.splev(xnew,tck,der=0)
    
    plt.figure()
    plt.plot(xnew, ynew, 'b')
    plt.axis([-0.05,6.33,-1.05,1.05])
    plt.title('Cubic-spline interpolation')
    plt.show()

def t():
    plt.plot([1,2,3,4], [1,4,9,16], 'ro')
    plt.show()    
    
def sp2():    
    x = np.array([ 0,  0, 0,  2])
    y = np.array([-2, -1, 0, 10])
        
    tck, u = interpolate.splprep([x, y], s=0)
    #print interpolate.splev([0.8], tck, der=0)
    unew = np.arange(0, 1.01, 0.01)
    out = interpolate.splev(unew, tck, der=0)    
    
    x2 = np.array([ out[0][-3], out[0][-2], 2, 8])
    y2 = np.array([ out[1][-3], out[1][-2], 10, 12])    
    
    tck2, u2 = interpolate.splprep([x2, y2], s=0)    
    unew2 = np.arange(0, 1.01, 0.01)
    out2 = interpolate.splev(unew2, tck2, der=0)
    
    plt.figure()
    plt.plot(out[0], out[1], 'b', out2[0], out2[1], 'r')
    plt.show()
        
def vecspline(a):
    s = [ ]
    for i in range(1, len(a)):
        x = [ None, None, None ]
        ufull = np.arange(0, 1.01, 0.01)
        if i == 1:
            for j in range(0, 3):
                x[j] = np.array([ a[0][j], a[1][j] ])  
            tck, u = interpolate.splprep(x, s=0, k=1)
            out = interpolate.splev(ufull, tck, der=0)            
        else:
            for j in range(0, 3):
                x[j] = np.array([ out[j][-3], out[j][-2], out[j][-1], a[i][j] ])
            tck, u = interpolate.splprep(x, s=0, k=3)
            out = interpolate.splev(ufull, tck, der=0)
            s.append(out[0])
            s.append(out[1])
    plt.plot(s[0], s[1], 'r', s[2], s[3], 'b', s[4], s[5], 'g')
    plt.show()    
    
def vecsplineplot(a):
    pts, d = vecspline(a)
        
#vecspline([ Vec3(0, -10, 0), Vec3(0, 0, 0), Vec3(2, 10, 0), Vec3(8, 12, 0), Vec3(14, 16, 0) ])
#vecspline([ Vec3(0, -10, 0), Vec3(0, 0, 0), Vec3(5, 5, 0), Vec3(5, 15, 0), Vec3(-5, 20, 0) ])
#vecspline([ Vec3(0, -10, 0), Vec3(0, 0, 0), Vec3(5, 5, 0), Vec3(10, 15, 0), Vec3(15, 20, 0) ])
vecspline([ Point3(0, -10, 0), Point3(0, 0, 0), Point3(5, 5, 0), Point3(10, 15, 0), Point3(15, 20, 0) ])

