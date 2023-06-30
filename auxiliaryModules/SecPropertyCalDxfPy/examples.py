# -*-coding: UTF-8-*-
#  Author: Junjun Guo
#  E-mail: guojj@tongji.edu.cn/guojj_ce@163.com/guojj01@gmail.com
#  Environemet: Successfully excucted in python 3.8
#  Date: 2021.04.27
# import necessary modules
from SecPropertyCalDxfPy import SecPropertyCalDxfPy

###---circle section test---####
# dxfInstance = SecPropertyCalDxfPy("circle.dxf",numCircleSeg=50,numArcSeg=10,numEllipseSeg=20,numSplineSeg=20)
# A, Iyy, Izz, J, Cy, Cz = dxfInstance.getSectionProperty("粗实线",scaleFactor=1000, meshSize=0.005)
# print(A,Iyy,Izz,J,Cy,Cz)
###---ellipse section test---####
# dxfInstance = SecPropertyCalDxfPy("ellipse.dxf", numCircleSeg=50, numArcSeg=10, numEllipseSeg=20, numSplineSeg=20)
# A, Iyy, Izz, J, Cy, Cz = dxfInstance.getSectionProperty("粗实线", scaleFactor=1000, meshSize=0.01)
# print(A, Iyy, Izz, J, Cy, Cz)
###---splines section test---####
# dxfInstance = SecPropertyCalDxfPy("splines.dxf", numCircleSeg=50, numArcSeg=10, numEllipseSeg=20, numSplineSeg=20)
# A, Iyy, Izz, J, Cy, Cz = dxfInstance.getSectionProperty("粗实线", scaleFactor=100, meshSize=0.1)
# print(A, Iyy, Izz, J, Cy, Cz)
###---tower section section test---####
dxfInstance = SecPropertyCalDxfPy("towerSection.dxf", numCircleSeg=50, numArcSeg=10, numEllipseSeg=20, numSplineSeg=20)
A, Iyy, Izz, J, Cy, Cz = dxfInstance.getSectionProperty("粗实线", scaleFactor=50, meshSize=0.05)
print("A=",A, " Iyy=",Iyy, " Izz=",Izz, " J=",J, " Cy=",Cy, " Cz=",Cz)

