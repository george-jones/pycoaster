#import sys
import os

exe = 'C:\\Panda3D-1.7.0\\bin\\egg-texture-cards.exe'
imgdir = 'E:\\george\\p3d\\coaster\\img\\buttons\\'
eggdir = 'E:\\george\\p3d\\coaster\\img\\buttons\\'
size = (86, 26)
states = [ 'active', 'click', 'hover', 'disabled' ]
for b in [ 'open', 'save', 'saveas', 'new', 'design', 'test', 'build', 'ride',
           'des_curve', 'des_linear', 'des_remove', 'des_rotate', 'des_tunnelon', 'des_tunneloff',
           'des_liftoff', 'des_lifton' ]:
    cmd = exe + ' -o %s%s.egg -p %d,%d ' % (eggdir, b, size[0], size[1])
    for s in states:
        cmd += ' %s%s_%s.png ' % (imgdir, b, s)
    os.system(cmd)