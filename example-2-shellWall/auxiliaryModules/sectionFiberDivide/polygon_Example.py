######################################################################################
#  Author: Junjun Guo
#  E-mail: guojj@tongji.edu.cn/guojj_ce@163.com
#    Date: 1/16/2021
#  Environemet: Successfully excucted in python 3.8
######################################################################################
from sectionFiberMain import polygonSection
name="polygon" #section  name
# the outside vertexes consecutively numbering and coordinate values in local y-z plane in dict container
outSideNode = {1: (3.5, 3), 2: (1.5, 5), 3: (-1.5, 5), 4: (-3.5, 3), 5: (-3.5, -3), 6: (-1.5, -5), 7: (1.5, -5),
    8: (3.5, -3)} # anti-clockwise numbering
# the outside vertexes loop consecutively numbering in dict container
outSideEle = {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 5), 5: (5, 6), 6: (6, 7), 7: (7, 8), 8: (8, 1)}
coverThick = 0.06  # the thinck of the cover concrete
coreSize = 0.2  # the size of the core concrete fiber elements
coverSize = 0.3  # the size of the cover concrete fiber elements
outBarD = 0.032  # outside bar diameter
outBarDist = 0.2  # outside bar space
plotState=True  # plot the fiber or not plot=True or False
autoBarMesh=True #if false provide the barControlNodeDict and barEleDict
userBarNodeDict=None # {1:(y1,z1),2:(y2,z2),...} bar line end nodes
userBarEleDict=None # {1:(nodeI,nodeJ,barD,barDist),...}  bar line end nodes number and diameter and distance
coreFiber,coverFiber,barFiber=polygonSection(name,outSideNode, outSideEle, coverThick, coreSize, coverSize,\
                                   outBarD, outBarDist,plotState,autoBarMesh)