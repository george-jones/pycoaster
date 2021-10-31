from panda3d.core import *
from sim import CoasterSim

timeslice = 0.01
#pts = [ Point3(0, 120, 0), Point3(32, 78, 0), Point3(94, 41, 0), Point3(206, 49, 0), Point3(282, 4, 0), Point3(636, 130, 0) ] 
course = ( (Point3(0, 0, 0), True),
          (Point3(20, 12, 0), True),
          (Point3(80, 40, 0), True),
          (Point3(120, 10, 0), False),
          (Point3(200, 0, 0), False) )
sc = CoasterSim(5, 3, course, 0.1, 32)
positions = sc.evaluate(timeslice)
print "Ride time: %f" % (len(positions) * timeslice)
for p in positions:
    print "%f\t%f" % (p[0][0], p[0][1])    

print "%f,%f" % (positions[-1][-1][0], positions[-1][-1][1])

