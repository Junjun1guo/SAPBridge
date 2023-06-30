##########################################################################    
Author: Junjun Guo([HomePage](https://github.com/Junjun1guo))    
E-mail: guojj@tongji.edu.cn/guojj_ce@163.com    
Environemet: Successfully excucted in python 3.8    
##########################################################################
______
## Tutorials      
1. download the zip file.
2. download gmsh.exe ([download gmsh](https://gmsh.info/)) that satifies your operation system,and put gmsh.exe to your unzip file in step 1.     
## Note: If you encount AttributeError: module 'pygmsh' has no attribute 'opencascade', please uninstall current pygmsh module and install pygmsh with version 6.1.1
# sectionFiberDivide
Generate sectional fibers based on python programming

The followings are some basic examples, and you can also find them in the download files.

## Circle section fiber generate
<img src="https://github.com/Junjun1guo/sectionFiberDivide/raw/main/circle.jpg" width =40% height =40% div align="center">

```python
from sectionFiberMain import circleSection
name="circle"#section name
outD=2  # the diameter of the outside circle
coverThick=0.05  # the thinckness of the cover concrete
outbarD=0.03  # outside bar diameter
outbarDist=0.15  # outside bar space
coreSize=0.1  # the size of core concrete fiber
coverSize=0.1  # the size of cover concrete fiber
plotState=True  # plot the fiber or not plot=True or False
corFiber,coverFiber,barFiber=circleSection(name,outD, coverThick, outbarD, outbarDist, coreSize, coverSize,plotState)
```

##  CircleHole section fiber generate
<img src="https://github.com/Junjun1guo/sectionFiberDivide/raw/main/circleHole.jpg" width =40% height =40% div align="center">

```python
from sectionFiberMain import circleSection
name="circleHole" #section name
outD = 2  # the diameter of the outside circle
coverThick = 0.06  # the thinckness of the cover concrete
outbarD = 0.03  # outside bar diameter
outbarDist = 0.15  # outside bar space
coreSize = 0.1  # the size of core concrete fiber
coverSize = 0.1  # the size of cover concrete fiber
plotState = True  # plot the fiber or not plot=True or False
inD =1 # the diameter of the inside circle
inBarD=0.03 # inside bar diameter
inBarDist=0.15 # inside bar space
corFiber, coverFiber, barFiber = circleSection(name,outD, coverThick, outbarD, outbarDist, coreSize, coverSize,
                                                   plotState,inD,inBarD,inBarDist)
```

## Polygen section fiber generate
<img src="https://github.com/Junjun1guo/sectionFiberDivide/raw/main/polygon.jpg" width =40% height =40% div align="center">

```python
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
```

## PolygenThreeHole section fiber generate
<img src="https://github.com/Junjun1guo/sectionFiberDivide/raw/main/polygonWithThreeHoles.jpg" width =40% height =40% div align="center">

```python
from sectionFiberMain import polygonSection
name="polygonWithThreeHoles"
outSideNode = {1: (0, 0), 2: (7, 0), 3: (7,3), 4: (0, 3)} # anti-clockwise numbering
# the outside vertexes loop consecutively numbering in dict container
outSideEle = {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4,1)}
# the inside vertexes consecutively numbering and coordinate values in local y-z plane in list container
inSideNode = [
   {1: (1, 1), 2: (2, 1), 3: (2, 2), 4: (1, 2)},
   {1: (3, 1), 2: (4, 1), 3: (4, 2), 4: (3, 2)},
   {1: (5, 1), 2: (6, 1), 3: (6, 2), 4: (5, 2)}] # anti-clockwise numbering
# the inside vertexes loop consecutively numbering in dict container
inSideEle = [{1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 1)},
            {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 1)},
            {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 1)}]
coverThick = 0.06  # the thinck of the cover concrete
coreSize = 0.2  # the size of the core concrete fiber elements
coverSize = 0.3  # the size of the cover concrete fiber elements
outBarD = 0.032  # outside bar diameter
outBarDist = 0.2  # outside bar space
plotState = True  # plot the fiber or not plot=True or False
autoBarMesh=True #if false provide the barControlNodeDict and barEleDict
userBarNodeDict=None
userBarEleDict=None
inBarD=0.032  # inside bar diameter (None)
inBarDist=0.2  # inside bar space (None)
coreFiber,coverFiber,barFiber=polygonSection(name,outSideNode, outSideEle, coverThick, coreSize, coverSize,\
                                   outBarD, outBarDist,plotState,autoBarMesh,userBarNodeDict,userBarEleDict,\
       inSideNode,inSideEle,inBarD,inBarDist)
         
```

## polygon with one hole section user bar mesh example
<img src="https://github.com/Junjun1guo/sectionFiberDivide/raw/main/polygonWithHole.jpg" width =40% height =40% div align="center">

```python
from sectionFiberMain import polygonSection
name="polygonWithHole"
# the outside vertexes consecutively numbering and coordinate values in local y-z plane in dict container
outSideNode = {1: (2.559, 2.1), 2: (-2.559, 2.1), 3: (-2.559, 1.6), 4: (-3.059, 1.6), 5: (-3.059, -1.6),
              6: (-2.559, -1.6), 7: (-2.559, -2.1), 8: (2.559, -2.1), 9: (2.559, -1.6), 10: (3.059, -1.6), 11: (3.059, 1.6),
              12: (2.559, 1.6)} # anti-clockwise numbering
# the outside vertexes loop consecutively numbering in dict container
outSideEle = {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 5), 5: (5, 6), 6: (6, 7), 7: (7, 8), 8: (8, 9), 9: (9, 10),\
             10: (10, 11), 11: (11, 12), 12: (12, 1)}
# the inside vertexes consecutively numbering and coordinate values in local y-z plane in list container
inSideNode = [{1: (1.809, 1.35), 2: (-1.809, 1.35), 3: (-2.309, 0.85), 4: (-2.309, -0.85), 5: (-1.809, -1.35), \
              6: (1.809, -1.35), 7: (2.309, -0.85), 8: (2.309, 0.85)}] ##(None)   # anti-clockwise numbering
# the inside vertexes loop consecutively numbering in dict container
inSideEle = [{1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 5), 5: (5, 6), 6: (6, 7), 7: (7, 8), 8: (8, 1)}]
coverThick = 0.06  # the thinck of the cover concrete
coreSize = 0.2  # the size of the core concrete fiber elements
coverSize = 0.3  # the size of the cover concrete fiber elements
outBarD = 0.032  # outside bar diameter(None)
outBarDist = 0.2  # outside bar space (None)
plotState=True  # plot the fiber or not plot=True or False
autoBarMesh=False #if false provide the barControlNodeDict and barEleDict
userBarNodeDict={1: (2.975, 1.516), 2: (2.475, 1.516), 3: (2.475, 2.016), 4: (-2.475, 2.016), 5: (-2.475, 1.516),
              6: (-2.975, 1.516),7: (-2.975, -1.516), 8: (-2.475, -1.516), 9: (-2.475, -2.016), 10: (2.475, -2.016),
              11: (2.475, -1.516), 12: (2.975, -1.516)} #{1:(y1,z1),2:(y2,z2),...} （None)
userBarEleDict={1: (1, 2,0.01,0.2), 2: (2, 3,0.01,0.2), 3: (3, 4,0.01,0.2), 4: (4, 5,0.01,0.2),\
               5: (6, 5,0.01,0.2), 6: (5, 2,0.01,0.2), 7: (7, 8,0.01,0.2), 8: (8, 9,0.01,0.2), 9: (9, 10,0.01,0.2),
             10: (10, 11,0.01,0.2), 11: (12, 11,0.01,0.2), 12: (11, 8,0.01,0.2),\
               }  #{1:(nodeI,nodeJ,barD,barDist)}（None)
inBarD=0.032  # inside bar diameter (None)
inBarDist=0.2  # inside bar space (None)
coreFiber,coverFiber,barFiber=polygonSection(name,outSideNode, outSideEle, coverThick, coreSize, coverSize,\
                                   outBarD, outBarDist,plotState,autoBarMesh,userBarNodeDict,userBarEleDict,\
       inSideNode,inSideEle,inBarD,inBarDist)
```
