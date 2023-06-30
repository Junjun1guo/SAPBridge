######################################################################################
#  Author: Junjun Guo
#  E-mail: guojj@tongji.edu.cn/guojj_ce@163.com
#    Date: 1/16/2021
#  Environemet: Successfully excucted in python 3.8
######################################################################################
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