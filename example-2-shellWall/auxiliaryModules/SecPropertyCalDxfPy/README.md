# SecPropertyCalDxfPy
Calculate the sectional properties of arbitray dxf format drawing with python programming

##########################################################################    
Author: Junjun Guo([HomePage](https://github.com/Junjun1guo))    
E-mail: guojj@tongji.edu.cn/guojj_ce@163.com    
Environemet: Successfully excucted in python 3.8    
##########################################################################
______
## Tutorials      
1. download the zip file.
2. install associated python packages via pip(MeshPy and ezdxf)    
3. (notes: Before install MeshPy, make sure VS C++ has been installed in your computer, C++ workload and win10SDK should be included when install VS C++)    

## The calculation results interpretation
<img src="https://github.com/Junjun1guo/SecPropertyCalDxfPy/raw/main/resultsExplanation-01.jpg" width =80% height =80% div align="center">

## Example-1
<img src="https://github.com/Junjun1guo/SecPropertyCalDxfPy/raw/main/geometry-1.png" width =50% height =50% div align="center"><img src="https://github.com/Junjun1guo/SecPropertyCalDxfPy/raw/main/finiteElementPlot-1.png" width =50% height =50% div align="center">

```python
from SecPropertyCalDxfPy import SecPropertyCalDxfPy

dxfInstance = SecPropertyCalDxfPy("towerSection.dxf", numCircleSeg=50, numArcSeg=10, numEllipseSeg=20, numSplineSeg=20)
A, Iyy, Izz, J, Cy, Cz = dxfInstance.getSectionProperty("粗实线", scaleFactor=50, meshSize=0.05)
print("A=",A, " Iyy=",Iyy, " Izz=",Izz, " J=",J, " Cy=",Cy, " Cz=",Cz)
```

## Example-2
<img src="https://github.com/Junjun1guo/SecPropertyCalDxfPy/raw/main/geometry-2.png" width =50% height =50% div align="center"><img src="https://github.com/Junjun1guo/SecPropertyCalDxfPy/raw/main/finiteElementPlot-2.png" width =50% height =50% div align="center">

```python
from SecPropertyCalDxfPy import SecPropertyCalDxfPy

dxfInstance = SecPropertyCalDxfPy("splines.dxf", numCircleSeg=50, numArcSeg=10, numEllipseSeg=20, numSplineSeg=20)
A, Iyy, Izz, J, Cy, Cz = dxfInstance.getSectionProperty("粗实线", scaleFactor=100, meshSize=0.1)
print("A=",A, " Iyy=",Iyy, " Izz=",Izz, " J=",J, " Cy=",Cy, " Cz=",Cz)
```
