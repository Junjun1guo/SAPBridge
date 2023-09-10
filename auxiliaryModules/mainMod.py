#-*-coding: UTF-8-*-
#####Units: Length-m, Force-kN, mass-ton, Stress-kpa(10e-3MPa), g=9.81m/s2
#####Units: Length-mm, Force-N, mass-ton, Stress-Mpa, g=9810mm/s2 pho=ton/mm3
########################################################################################################################
#  Author: Junjun Guo,Tongji University. https://github.com/Junjun1guo
#  E-mail: guojj@tongji.edu.cn/guojj_ce@163.com
#  Environemet: Successfully executed in python 3.8
#  Date: 2022-01-29
########################################################################################################################
########################---import modules---#################################
import os
import numpy as np
import math
from scipy.stats import norm
from scipy import signal
from scipy.signal import argrelextrema
import matplotlib.pyplot as plt
from PIL import Image
import comtypes.client
import comtypes.client
########################################################################################################################
########################################################################################################################
class SectionFiberDivide():
    """
    --------------------------------------------------------------------------------------------------------------------
    A class for section fiber divide
    --------------------------------------------------------------------------------------------------------------------
    ** **********************************************************************  **
    ** (C) Copyright 2023, Department of Bridge Engineering,Tongji University  **
    ** All Rights Reserved.                                                    **
    **                                                                         **
    ** Commercial use of this program is strictly prohibited.                  **
    **                                                                         **
    ** Developed by:                                                           **
    **   Junjun Guo,Tongji University. https://github.com/Junjun1guo           **
    **   guojj@tongji.edu.cn/guojj_ce@163.com                                  **
    ** *********************************************************************   **
    --------------------------------------------------------------------------------------------------------------------
    """
    def __init__(self,saveFold="fiberDivideInformation"):


        path=os.getcwd()
        self.saveFold=path+"\\"+saveFold
        # try:
        #     shutil.rmtree(self.saveFold)
        # except:
        #     pass
        if not os.path.exists(self.saveFold):
            os.mkdir(saveFold)

    def circleSection(self,name,outD, coverThick, outbarD, outbarDist, coreSize, coverSize,autoBarMesh=True,
        userBarInfoList=None,inD=None,inBarD=None,inBarDist=None,lineWidth=1,markerSize=2):
        """
        ----------------------------------------------------------------------------------------------------------------
        Inputs:
            name# the name of the fiber
            outD # the diameter of the outside circle
            coverThick # the thinckness of the cover concrete
            outbarD # outside bar diameter
            outbarDist # outside bar space
            coreSize # the size of core concrete fiber
            coverSize # the size of cover concrete fiber
            autoBarMesh(bool)#generate the bar fiber automatically, otherwise manually provide the bar divide information
            userBarInfoList(list)#[[outSideDist1,barD1,barDist1],[outSideDist2,barD2,barDist2],...]
            ---here the outsideDist means the distance between the center of the bar and the outside of the cirder
            inD # the diameter of the inner circle,if not inD=None
            inBarD # inside bar diameter, if not inBarD=None
            inBarDist # inside bar space,if not inBarDist=None
            lineWidth #the line widht of the plot
            markerSize #the size of the discrete fiber point
        Output:
        ---coreFiber,coverFiber,barFiber #core concrete, cover concrete anb bar fibers information
        for eaxample coreFiber=[(y1,z1,area1),(y2,y2,area2),...], y1,z1 is the fiber coordinate values in loacal y-z plane
       area1 is the fiber area
       -----------------------------------------------------------------------------------------------------------------
       ###---example 1:
       #######################---solid circle example---#####################
       fiberDivideInstance=SectionFiberDivide()
        name = "circle"  # section name
        outD = 2  # the diameter of the outside circle
        coverThick = 0.05  # the thinckness of the cover concrete
        outbarD = 0.03  # outside bar diameter
        outbarDist = 0.15  # outside bar space
        coreSize = 0.1  # the size of core concrete fiber
        coverSize = 0.1  # the size of cover concrete fiber
        autoBarMesh=False
        userBarInfoList=[[0.065,outbarD,outbarDist],[0.115,outbarD,outbarDist]]
        inD=1
        inBarD=outbarD
        inBarDist=outbarDist
        lineWidth=0.5
        markerSize=2
        fiberDivideInstance.circleSection(name, outD, coverThick, outbarD, outbarDist,
        coreSize, coverSize,autoBarMesh,userBarInfoList,inD,inBarD,inBarDist,lineWidth,markerSize)
        fiberDivideInstance.plotFibers(name)
        ######################################################################
        ######################################################################

       -----------------------------------------------------------------------------------------------------------------
        """
        from .sectionFiberDivide.sectionFiberMain import circleSection
        coreFiber, coverFiber, barFiber = circleSection(name, outD, coverThick, outbarD, outbarDist,
        coreSize, coverSize,self.saveFold,autoBarMesh,userBarInfoList,inD,inBarD,inBarDist,lineWidth,markerSize)
        np.savetxt(self.saveFold+"/"+name+"_coreFiber.txt",coreFiber,fmt="%.6f %.6f %.6f")
        np.savetxt(self.saveFold+"/"+name+"_coverFiber.txt", coverFiber,fmt="%.6f %.6f %.6f")
        np.savetxt(self.saveFold+"/"+name+"_barFiber.txt", barFiber,fmt="%.6f %.6f %.6f")
        return coreFiber, coverFiber, barFiber

    def polygonSection(self,sectionName, outSideNode, outSideEle, coverThick, coreSize, coverSize, \
        outBarD, outBarDist,autoBarMesh=True,userBarNodeDict = None, userBarEleDict = None, inSideNode = None, \
        inSideEle = None, inBarD = None, inBarDist = None, lineWidth = 1, markerSize = 2):
        """
        ----------------------------------------------------------------------------------------------------------------
        Input:
            ---outSideNode # the outside vertexes consecutively numbering and coordinate values in local y-z plane in dict container
            ---outSideEle  # the outside vertexes loop consecutively numbering in dict container
            ---coverThick  # the thinck of the cover concrete
            ---coreSize  # the size of the core concrete fiber elements
            ---coverSize   # the size of the cover concrete fiber elements
            ---outBarD  # outside bar diameter
            ---outBarDist  # outside bar space
            ---savedFolder #the directory to save the fibers information
            ---autoBarMesh=True # generate the bar fiber automatically, otherwise manually provide the bar divide information
            ---userBarNodeDict=None# {1:(y1,z1),2:(y2,z2),...}
            ---userBarEleDict=None #{1:(nodeI,nodeJ,barD,barDist)}
            ---inSideNode #the inside vertexes consecutively numbering and coordinate values in local y-z plane in list container
            ---inSideEle # the inside vertexes loop consecutively numbering in list container
            ---inBarD #inside bar diameter
            ---inBarDist #inside bar space
            ---lineWidth #the line widht of the plot
            ---markerSize #the size of the discrete fiber point
            Output:
            ---coreFiber,coverFiber,barFiber #core concrete, cover concrete anb bar fibers information
               for eaxample coreFiber=[(y1,z1,area1),(y2,y2,area2),...], y1,z1 is the fiber coordinate values in loacal y-z plane
               area1 is the fiber area
        ----------------------------------------------------------------------------------------------------------------
        ###---example 1:
        fiberDivideInstance = SectionFiberDivide()
        name = "polygon"  # section  name
        the outside vertexes consecutively numbering and coordinate values in local y-z plane in dict container
        outSideNode = {1: (3.5, 3), 2: (1.5, 5), 3: (-1.5, 5), 4: (-3.5, 3), 5: (-3.5, -3), 6: (-1.5, -5), 7: (1.5, -5),
                       8: (3.5, -3)}  # anti-clockwise numbering
        the outside vertexes loop consecutively numbering in dict container
        outSideEle = {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 5), 5: (5, 6), 6: (6, 7), 7: (7, 8), 8: (8, 1)}
        coverThick = 0.06  # the thinck of the cover concrete
        coreSize = 0.2  # the size of the core concrete fiber elements
        coverSize = 0.3  # the size of the cover concrete fiber elements
        outBarD = 0.032  # outside bar diameter
        outBarDist = 0.2  # outside bar space
        autoBarMesh = True  # if false provide the barControlNodeDict and barEleDict
        userBarNodeDict = None  # {1:(y1,z1),2:(y2,z2),...} bar line end nodes
        userBarEleDict = None  # {1:(nodeI,nodeJ,barD,barDist),...}  bar line end nodes number and diameter and distance
        fiberDivideInstance.polygonSection(name, outSideNode, outSideEle, coverThick,coreSize, coverSize,outBarD,
                                          outBarDist,autoBarMesh,lineWidth=0.5,markerSize=0.5)
        fiberDivideInstance.plotFibers(name)
       -----------------------------------------------------------------------------------------------------------------
       ###---example 2:
        fiberDivideInstance = SectionFiberDivide()
        name = "polygonWithThreeHoles"
        outSideNode = {1: (0, 0), 2: (7, 0), 3: (7, 3), 4: (0, 3)}  # anti-clockwise numbering
        the outside vertexes loop consecutively numbering in dict container
        outSideEle = {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 1)}
        ## the inside vertexes consecutively numbering and coordinate values in local y-z plane in list container
        inSideNode = [
          {1: (1, 1), 2: (2, 1), 3: (2, 2), 4: (1, 2)},
          {1: (3, 1), 2: (4, 1), 3: (4, 2), 4: (3, 2)},
          {1: (5, 1), 2: (6, 1), 3: (6, 2), 4: (5, 2)}]  # anti-clockwise numbering
        # # the inside vertexes loop consecutively numbering in dict container
        inSideEle = [{1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 1)},
                     {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 1)},
                     {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 1)}]
        coverThick = 0.06  # the thinck of the cover concrete
        coreSize = 0.2  # the size of the core concrete fiber elements
        coverSize = 0.3  # the size of the cover concrete fiber elements
        outBarD = 0.032  # outside bar diameter
        outBarDist = 0.2  # outside bar space
        autoBarMesh = True  # if false provide the barControlNodeDict and barEleDict
        userBarNodeDict = None
        userBarEleDict = None
        inBarD = 0.032  # inside bar diameter (None)
        inBarDist = 0.2  # inside bar space (None)
        fiberDivideInstance.polygonSection(name, outSideNode, outSideEle, coverThick, coreSize, coverSize, outBarD,
                                          outBarDist, autoBarMesh,userBarNodeDict,userBarEleDict,inSideNode,inSideEle,
        inBarD,inBarDist,lineWidth=0.5, markerSize=0.5)
       -----------------------------------------------------------------------------------------------------------------
       ###---example 3:
        fiberDivideInstance = SectionFiberDivide()
        name = "polygonWithHole"
        # # the outside vertexes consecutively numbering and coordinate values in local y-z plane in dict container
        outSideNode = {1: (2.559, 2.1), 2: (-2.559, 2.1), 3: (-2.559, 1.6), 4: (-3.059, 1.6), 5: (-3.059, -1.6),
                       6: (-2.559, -1.6), 7: (-2.559, -2.1), 8: (2.559, -2.1), 9: (2.559, -1.6), 10: (3.059, -1.6),
                       11: (3.059, 1.6),
                       12: (2.559, 1.6)}  # anti-clockwise numbering
        # # the outside vertexes loop consecutively numbering in dict container
        outSideEle = {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 5), 5: (5, 6), 6: (6, 7), 7: (7, 8), 8: (8, 9), 9: (9, 10), \
                    10: (10, 11), 11: (11, 12), 12: (12, 1)}
        # # the inside vertexes consecutively numbering and coordinate values in local y-z plane in list container
        inSideNode = [{1: (1.809, 1.35), 2: (-1.809, 1.35), 3: (-2.309, 0.85), 4: (-2.309, -0.85), 5: (-1.809, -1.35), \
                    6: (1.809, -1.35), 7: (2.309, -0.85), 8: (2.309, 0.85)}]  ##(None)   # anti-clockwise numbering
        # # the inside vertexes loop consecutively numbering in dict container
        inSideEle = [{1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 5), 5: (5, 6), 6: (6, 7), 7: (7, 8), 8: (8, 1)}]
        coverThick = 0.06  # the thinck of the cover concrete
        coreSize = 0.2  # the size of the core concrete fiber elements
        coverSize = 0.3  # the size of the cover concrete fiber elements
        outBarD = 0.032  # outside bar diameter(None)
        outBarDist = 0.2  # outside bar space (None)
        plotState = True  # plot the fiber or not plot=True or False
        autoBarMesh = False  # if false provide the barControlNodeDict and barEleDict
        userBarNodeDict = {1: (2.975, 1.516), 2: (2.475, 1.516), 3: (2.475, 2.016), 4: (-2.475, 2.016), 5: (-2.475, 1.516),
                         6: (-2.975, 1.516), 7: (-2.975, -1.516), 8: (-2.475, -1.516), 9: (-2.475, -2.016),
                          10: (2.475, -2.016),
                          11: (2.475, -1.516), 12: (2.975, -1.516)}  # {1:(y1,z1),2:(y2,z2),...} （None)
        userBarEleDict = {1: (1, 2, 0.01, 0.2), 2: (2, 3, 0.01, 0.2), 3: (3, 4, 0.01, 0.2), 4: (4, 5, 0.01, 0.2), \
                          5: (6, 5, 0.01, 0.2), 6: (5, 2, 0.01, 0.2), 7: (7, 8, 0.01, 0.2), 8: (8, 9, 0.01, 0.2),
                         9: (9, 10, 0.01, 0.2),
                          10: (10, 11, 0.01, 0.2), 11: (12, 11, 0.01, 0.2), 12: (11, 8, 0.01, 0.2), \
                         }  # {1:(nodeI,nodeJ,barD,barDist)}（None)
        inBarD = 0.032  # inside bar diameter (None)
        inBarDist = 0.2  # inside bar space (None)
        fiberDivideInstance.polygonSection(name, outSideNode, outSideEle, coverThick, coreSize, coverSize, outBarD,
                                           outBarDist, autoBarMesh, userBarNodeDict, userBarEleDict, inSideNode, inSideEle,
                                         inBarD, inBarDist, lineWidth=0.5, markerSize=0.5)
        ----------------------------------------------------------------------------------------------------------------
        """
        from .sectionFiberDivide.sectionFiberMain import polygonSection

        coreFiber, coverFiber, barFiber =polygonSection(sectionName, outSideNode, outSideEle, coverThick, coreSize,
        coverSize,outBarD, outBarDist,self.saveFold,autoBarMesh,userBarNodeDict, userBarEleDict, inSideNode, \
        inSideEle, inBarD, inBarDist, lineWidth, markerSize)
        np.savetxt(self.saveFold + "/" + sectionName + "_coreFiber.txt", coreFiber, fmt="%.6f %.6f %.6f")
        np.savetxt(self.saveFold + "/" + sectionName + "_coverFiber.txt", coverFiber, fmt="%.6f %.6f %.6f")
        np.savetxt(self.saveFold + "/" + sectionName + "_barFiber.txt", barFiber, fmt="%.6f %.6f %.6f")
        return coreFiber, coverFiber, barFiber

    def plotFibers(self,fiberName):
        """
        Plot the divided fibers
        -----------------------------
        Inputs:
            fiberName(str)-the saved fiber figure name
        """
        sectionImage = Image.open(self.saveFold+"/"+fiberName+".jpg")
        sectionImage.show()
########################################################################################################################
########################################################################################################################
def OpenSeesPyX(dataBaseName="resultDB"):
    """
    --------------------------------------------------------------------------------------------------------------------
    A function for openSeesPy visualization and structural model analysis (version:0.4.0)
    Environemet: Successfully executed in python 3.8
    Date: 2023-04-07
    --------------------------------------------------------------------------------------------------------------------
    Units: Length-m, Force-kN, mass-ton, Stress-kpa(10e-3MPa), g=9.81m/s2
    --------------------------------------------------------------------------------------------------------------------
        ** **********************************************************************  **
        ** (C) Copyright 2023, Department of Bridge Engineering,Tongji University  **
        ** All Rights Reserved.                                                    **
        **                                                                         **
        ** Commercial use of this program is strictly prohibited.                  **
        **                                                                         **
        ** Developed by:                                                           **
        **   Junjun Guo,Tongji University. https://github.com/Junjun1guo           **
        **   guojj@tongji.edu.cn/guojj_ce@163.com                                  **
        ** *********************************************************************   **
    """
    from .OpenSeesPyX.OpenSeesPyX import OpenSeesPyX
    return OpenSeesPyX(dataBaseName=dataBaseName)
########################################################################################################################
########################################################################################################################
class SectionPropertyCalculate():
    """
    --------------------------------------------------------------------------------------------------------------------
    A class for calculating cross-sectional properties using sectionproperties module.
    --------------------------------------------------------------------------------------------------------------------
    Insplired by :A python package for the analysis of arbitrary cross-sections using the finite element method written by
    Robbie van Leeuwen. sectionproperties can be used to determine section properties to be used in structural
    design and visualise cross-sectional stresses resulting from combinations of applied forces and bending moments.
    --------------------------------------------------------------------------------------------------------------------
    ** **********************************************************************  **
    ** (C) Copyright 2023, Department of Bridge Engineering,Tongji University  **
    ** All Rights Reserved.                                                    **
    **                                                                         **
    ** Commercial use of this program is strictly prohibited.                  **
    **                                                                         **
    ** Developed by:                                                           **
    **   Junjun Guo,Tongji University. https://github.com/Junjun1guo           **
    **   guojj@tongji.edu.cn/guojj_ce@163.com                                  **
    ** *********************************************************************   **
    --------------------------------------------------------------------------------------------------------------------
    """
    def __init__(self):
        """
        """
        pass

    def dxf_sectionproperties(self,dxfFileName,layerName,scaleFactor=50,meshSize=0.05,numCircleSeg=50, numArcSeg=10,
        numEllipseSeg=20,numSplineSeg=20):
        """
        ----------------------------------------------------------------------------------------------------------------
        ---Cross sectional properties calculation based on dxf file class---
                            ^z
                            *
                            *
                *************************
                *           *           *
                *           *           *
             ********************************> y
                *           *           *
                *           *           *
                *************************
            (minY,minZ)     *
                            *
        -----------------------------
        Inputs:
            dxfFileName(str)-the path of the dxf file,for example-"pythonInteractSAP2000\circle.dxf"
            layerName(str)-the layer name that the line objects ploted
            scaleFactor(float)-the sacle factor equals to the length in CAD divides (measure scaling factor and the converted size)
            meshSize(float)-the maximum size of the meshed element
            numCircleSeg(int)-the total number of lines approximate a circle
            numArcSeg(int)-the total number of lines approximate an arc
            numEllipseSeg(int)-the total number of lines approximate an ellipse
            numSplineSeg(int)-the total number of lines approximate an ellipse arc
        Outputs:
            [A, Iyy, Izz, J, Cy, Cz],outSideNode,outSideEle,inSideNode,inSideEle
            A-Cross-sectional area
            Iyy-Second moments of area about the global y axis
            Izz-Second moments of area about the global z axis
            J-Torsion constant
            Cy,Cz-the relative distance between elastic centroid and (ymin,zmin)
            outSideNode-# the outside vertexes loop consecutively numbering in dict container(anti-clockwise)
            outSideEle-
            inSideNode-# the inside vertexes loop consecutively numbering in dict container
        ----------------------------------------------------------------------------------------------------------------
        ###---Example:
        sectionPropertyInstance=SectionPropertyCalculate()
        A, Iyy, Izz, J, Cy, Cz,outSideNode,outSideEle,inSideNode,inSideEle= sectionPropertyInstance.dxf_sectionproperties\
            ("ellipse.dxf","粗实线",scaleFactor=1000,meshSize=0.005)
        print("A=", A, " Iyy=", Iyy, " Izz=", Izz, " J=", J, " Cy=", Cy, " Cz=",Cz)
        ----------------------------------------------------------------------------------------------------------------
        """
        from .SecPropertyCalDxfPy.SecPropertyCalDxfPy import SecPropertyCalDxfPy

        dxfInstance = SecPropertyCalDxfPy(dxfFileName, numCircleSeg, numArcSeg, numEllipseSeg,numSplineSeg)
        A, Iyy, Izz, J, Cy, Cz,sortNodes,outAntiNodes,innerAntiNodes= dxfInstance.getSectionProperty(layerName,
        scaleFactor, meshSize)
        outSideNode={}
        outSideEle={}
        inSideNode=[]
        inSideEle=[]
        nodesDict={i1:(sortNodes[i1][0],sortNodes[i1][1])  for i1 in range(len(sortNodes))}
        for i1 in range(len(outAntiNodes)):
            outSideNode[i1+1]=nodesDict[outAntiNodes[i1]]
            outSideEle[i1+1]=(i1+1,i1+2)
        outSideEle[len(outAntiNodes)]=(len(outAntiNodes),1)
        for i1 in range(len(innerAntiNodes)):
            inNodesDict={}
            inEleDict={}
            inNodes=innerAntiNodes[i1]
            for j1 in range(len(inNodes)):
                inNodesDict[j1+1]=nodesDict[inNodes[j1]]
                inEleDict[j1+1]=(j1+1,j1+2)
            inEleDict[len(inNodes)]=(len(inNodes),1)
            inSideNode.append(inNodesDict)
            inSideEle.append(inEleDict)
        return A, Iyy, Izz, J, Cy, Cz,outSideNode,outSideEle,inSideNode,inSideEle
########################################################################################################################
########################################################################################################################
class CalculateGroundMotionIMs():
    """
    --------------------------------------------------------------------------------------------------------------------
    A class for calculating ground motion intensity measures (IMs)
    --------------------------
    The detail meaning of each IM can be found at the paper:
        Guo J, Alam MS, Wang J, Li S, Yuan W. Optimal intensity measures for probabilistic seismic demand models of a
        cable-stayed bridge based on generalized linear regression models. Soil Dynamics and Earthquake Engineering.
        2020 Apr 1;131:106024.
    --------------------------------------------------------------------------------------------------------------------
    ** **********************************************************************  **
    ** (C) Copyright 2023, Department of Bridge Engineering,Tongji University  **
    ** All Rights Reserved.                                                    **
    **                                                                         **
    ** Commercial use of this program is strictly prohibited.                  **
    **                                                                         **
    ** Developed by:                                                           **
    **   Junjun Guo,Tongji University. https://github.com/Junjun1guo           **
    **   guojj@tongji.edu.cn/guojj_ce@163.com                                  **
    ** *********************************************************************   **
    --------------------------------------------------------------------------------------------------------------------
    ###---Example
    acc=np.loadtxt("1.txt")
    imInstance=CalculateGroundMotionIMs(acc,0.01)
    IMcal=imInstance.calIMs() ###---return the instance of the class IMs()
    print(help(IMcal))
    print(IMcal.PGA())
    --------------------------------------------------------------------------------------------------------------------
    """
    def __init__(self,acc,dt):
        """
        ----------------------------------------------------------------------------------------------------------------
        acc(list,g)-acceleration time history with unit g
        dt(float)-time interval for the acc
        ----------------------------------------------------------------------------------------------------------------
        """
        self.acc=acc
        self.dt=dt

    def calIMs(self):
        """
        ----------------------------------------------------------------------------------------------------------------
        This method will return the instance of the class IMs
        ----------------------------------------------------------------------------------------------------------------
        """
        from .CalculateIMs.IMs import  IMs
        return IMs(self.acc,self.dt)
########################################################################################################################
########################################################################################################################
class GroundMotionProcess():
    """
    --------------------------------------------------------------------------------------------------------------------
    A class for ground motion process
    --------------------------------------------------------------------------------------------------------------------
    ** **********************************************************************  **
    ** (C) Copyright 2023, Department of Bridge Engineering,Tongji University  **
    ** All Rights Reserved.                                                    **
    **                                                                         **
    ** Commercial use of this program is strictly prohibited.                  **
    **                                                                         **
    ** Developed by:                                                           **
    **   Junjun Guo,Tongji University. https://github.com/Junjun1guo           **
    **   guojj@tongji.edu.cn/guojj_ce@163.com                                  **
    ** *********************************************************************   **
    --------------------------------------------------------------------------------------------------------------------
    """
    def __init__(self):
        pass
    def responseSpectra_Cal(self,acc,dt,Tarray,beta):
        """
        ----------------------------------------------------------------------------------------------------------------
        acceleration,velocity and displacement response spectra calculation
        ----------------------------------------------------------------------------------------------------------------
        Inputs:
            acc(g)-acceleration time history
            dt(s)-time interval
            T(list)-periods list
            beta(float)-damping ratio
        Outputs:
            Sa(g),Sv(cm/s),Sd(cm)
        ----------------------------------------------------------------------------------------------------------------
        ###---Example
        groundMotionProcessInstance=GroundMotionProcess()
        logP = [0.05 * x for x in range(-40, 27, 1)]
        Tarray = [10 ** y for y in logP]
        beta = 0.05
        dt1 = np.loadtxt("pulseMotions/dt.txt")
        length1 = np.loadtxt("pulseMotions/length.txt")
        saPulse = []
        svPulse = []
        sdPulse=[]
        for i1 in range(10):
            acc1 = np.loadtxt("pulseMotions/FN/" + str(i1 + 1) + ".txt")
            sa1, sv1, sd1 = groundMotionProcessInstance.responseSpectra_Cal(acc1, dt1[i1], Tarray, beta)
            saPulse.append(sa1)
            svPulse.append(sv1)
            sdPulse.append(sd1)
        #####################################################
        percentileValue=[0.025,0.975]
        groundMotionProcessInstance.responseSpectra_Plot(Tarray,saPulse, svPulse,sdPulse,[Tarray[0],Tarray[-1]],
                                                         percentileValue,saveFig=True)
        ----------------------------------------------------------------------------------------------------------------
        """
        from .responseSpectCalculate.responseSpectMain import SaSvSd

        sa1, sv1, sd1 = SaSvSd(acc, dt, Tarray, beta)
        return sa1,sv1,sd1

    def responseSpectra_Plot(self,Tarray,saList,svList,sdList,xlimValue,percentileValue,saveFig=True):
        """
        ----------------------------------------------------------------------------------------------------------------
        Response spectra plot method
        ----------------------------------------------------------------------------------------------------------------
        Inputs:
            Tarray(list)-period List,[0.001,0.05,...,20]
            saList(list)-acceleration response spectra values for multiple motions, [[a1_1,a1_2,...],[a2_1,a2_2,...]]
            svList(list)-velocity response spectra values for multiple motions, [[v1_1,v1_2,...],[v2_1,v2_2,...]]
            sdList(list)-displacement response spectra values for multiple motions, [[d1_1,d1_2,...],[d2_1,d2_2,...]]
            xlimValue(list)-the x limit value list,[0.01,20]
            percentileValue(list)-percentile response spectra,[0.025,0.975]
            saveFig(bool)-save figure to .eps format
        ----------------------------------------------------------------------------------------------------------------
        """
        fig, ((ax1, ax2),(ax3,ax4)) = plt.subplots(2, 2)
        ax1.set_xscale("log")
        ax1.set_yscale("log")
        ax1.grid(which="both")
        ax1.set_xlim(xlimValue[0],xlimValue[1])
        ax2.set_xscale("log")
        ax2.set_yscale("log")
        ax2.grid(which="both")
        ax2.set_xlim(xlimValue[0], xlimValue[1])
        ax3.set_xscale("log")
        ax3.set_yscale("log")
        ax3.grid(which="both")
        ax3.set_xlim(xlimValue[0], xlimValue[1])

        logSa=np.log10(saList)
        mean1 = np.mean(np.mat(logSa), axis=0).tolist()[0]
        mean1real = [10 ** x for x in mean1]
        var1 = np.var(np.mat(logSa), axis=0).tolist()[0]
        std1 = [x ** 0.5 for x in var1]
        var1real = [10 ** y for y in std1]
        upper1 = []
        lower1 = []
        for i1 in range(len(mean1real)):
            inorm = norm.ppf(percentileValue[1], loc=mean1[i1], scale=var1[i1])
            upper1.append(inorm)
            lnorm = norm.ppf(percentileValue[0], loc=mean1[i1], scale=var1[i1])
            lower1.append(lnorm)
        upperReal1 = [10 ** x for x in upper1]
        lowerReal1 = [10 ** x for x in lower1]
        for i1 in range(len(saList)):
            ax1.plot(Tarray, saList[i1], "k")
        ax1.plot(Tarray, mean1real, "r", linewidth=2)
        ax1.plot(Tarray, upperReal1, "b", linewidth=2)
        ax1.plot(Tarray, lowerReal1, "b", linewidth=2)

        logSv = np.log10(svList)
        mean1 = np.mean(np.mat(logSv), axis=0).tolist()[0]
        mean1real = [10 ** x for x in mean1]
        var1 = np.var(np.mat(logSv), axis=0).tolist()[0]
        std1 = [x ** 0.5 for x in var1]
        var1real = [10 ** y for y in std1]
        upper1 = []
        lower1 = []
        for i1 in range(len(mean1real)):
            inorm = norm.ppf(percentileValue[1], loc=mean1[i1], scale=var1[i1])
            upper1.append(inorm)
            lnorm = norm.ppf(percentileValue[0], loc=mean1[i1], scale=var1[i1])
            lower1.append(lnorm)
        upperReal1 = [10 ** x for x in upper1]
        lowerReal1 = [10 ** x for x in lower1]
        for i1 in range(len(svList)):
            ax2.plot(Tarray, svList[i1], "k")
        ax2.plot(Tarray, mean1real, "r", linewidth=2)
        ax2.plot(Tarray, upperReal1, "b", linewidth=2)
        ax2.plot(Tarray, lowerReal1, "b", linewidth=2)

        logSd = np.log10(sdList)
        mean1 = np.mean(np.mat(logSd), axis=0).tolist()[0]
        mean1real = [10 ** x for x in mean1]
        var1 = np.var(np.mat(logSd), axis=0).tolist()[0]
        std1 = [x ** 0.5 for x in var1]
        var1real = [10 ** y for y in std1]
        upper1 = []
        lower1 = []
        for i1 in range(len(mean1real)):
            inorm = norm.ppf(percentileValue[1], loc=mean1[i1], scale=var1[i1])
            upper1.append(inorm)
            lnorm = norm.ppf(percentileValue[0], loc=mean1[i1], scale=var1[i1])
            lower1.append(lnorm)
        upperReal1 = [10 ** x for x in upper1]
        lowerReal1 = [10 ** x for x in lower1]
        for i1 in range(len(sdList)):
            ax3.plot(Tarray, sdList[i1], "k")
        ax3.plot(Tarray, mean1real, "r", linewidth=2)
        ax3.plot(Tarray, upperReal1, "b", linewidth=2)
        ax3.plot(Tarray, lowerReal1, "b", linewidth=2)
        if saveFig==True:
            plt.savefig("responseSpect.eps")
        plt.show()

    def accToVelocity(self,dt,acc):
        """
        ----------------------------------------------------------------------------------------------------------------
        from acceleration (g) to velocity (cm/s)
        ----------------------------------------------------------------------------------------------------------------
        Inputs:
            dt:time interval (s)
            acc: acceleration time history (g/s2)
        output:
            vel-velocity time history (cm/s)
        """
        from .baseLineCorrectionAndFiltering.BaseLineCorrectionAndFiltering import AccToVelocity
        return AccToVelocity(dt,acc)

    def velToDisplacement(self,dt, vel):
        """
        ----------------------------------------------------------------------------------------------------------------
        from velocity (cm/s) to displacement (cm)
        ----------------------------------------------------------------------------------------------------------------
        Inputs:
            dt:time interval (s)
            vel-velocity time history(cm/s)
        output:
            disp-displacement time history(cm)
        """
        from .baseLineCorrectionAndFiltering.BaseLineCorrectionAndFiltering import VelToDisplacement
        return VelToDisplacement(dt,vel)

    def dispToVelocity(self,dt, disp):
        """
        ----------------------------------------------------------------------------------------------------------------
        from displacement (cm) to velocity (cm/s)
        ----------------------------------------------------------------------------------------------------------------
        Inputs:
            dt:time interval (s)
            disp-displacement time history (cm)
        output:
            velocity time history(cm/s)
        """
        from .baseLineCorrectionAndFiltering.BaseLineCorrectionAndFiltering import DispToVelocity
        return DispToVelocity((dt,disp))

    def velToAccele(self,dt, vel):
        """
        ----------------------------------------------------------------------------------------------------------------
        from velocity (cm/s) to acceleration (g)
        ----------------------------------------------------------------------------------------------------------------
        Inputs:
            dt:time interval (s)
            vel-velocity time history(cm/s)
        output:
            acceleration time history(g)
        """
        from .baseLineCorrectionAndFiltering.BaseLineCorrectionAndFiltering import VelToAccele
        return VelToAccele(dt,vel)

    def polynomialBaseLineCorrect(self,acc, dt):
        """
        ----------------------------------------------------------------------------------------------------------------
        3th order polynomial baseline correction
        ----------------------------------------------------------------------------------------------------------------
        Inputs:
            acc-acceleration time history (g)
            dt:time interval (s)
        output:
            corretAcc,corretVel,corretDisp-the filted acceleration (g)
            velocity (cm/s) and displacement (cm)
        """
        from .baseLineCorrectionAndFiltering.BaseLineCorrectionAndFiltering import polynomialBaseLineCorrect
        return polynomialBaseLineCorrect(acc,dt)

    def improvedWuBseLineCorrect(self,accFilePath, velFilePath, dispFilePath, t, fileNamei, nIterate, saveAccPath, \
                   saveVelPath, saveDispPath, T3, T1Self=None, T2=None):
        """
        ----------------------------------------------------------------------------------------------------------------
        improved Wu et al method for basedline correction
        Wu Y-M, Wu C-F. Approximate recovery of coseismic deformation from Taiwan strong-motion records.
	    Journal of Seismology. 2007;11(2):159-70.
        ----------------------------------------------------------------------------------------------------------------
        Inputs:
            :param accFilePath: the file path of acceleration
            :param velFilePath: the file path of velocity
            :param dispFilePath: the file path of displacement
            :param t: time interval of motion (s)
            :param fileNamei: fileName of the processed ground motion
            :param nIterate: sample numbers for t2 values
            :param saveAccPath: the save path of processed acceleration
            :param saveVelPath: the save path of processed velocity
            :param saveDispPath: the save path of processed displacement
            :param T3: T3 position in the motion
            :param T1Self: T1 position in the motion, if T1self is none,the program will automatically determine it
        OutPuts:
            T1, T2Index, T3, maxfValue
        ----------------------------------------------------------------------------------------------------------------
        ###---Example
        ###provide the acceleration, velocity and displacement paths of the unprocessed motion
        accFilePath='ChiChiEarthquakeAccg/N'
        velFilePath='ChiChiEarthquakeVel/N'
        dispFilePath='ChiChiEarthquakeDisp/N'
        ###provide the save paths for the processed acceleration, velocity and displacement
        saveAccPath='accBaselineCorre/N'
        saveVelPath='velBaselineCorre/N'
        saveDispPath='dispBaselineCorre/N'
        dt=0.005 #time interval (s)
        nIterate=100 # sample size for T2 position from T3 to the end
        fileNamei='TCU084' #file name of unprocessed motion
        # #########################################################################
        # #########################################################################
        #automatically determine T1 and T3,T1=(4500,5500),T3=(5000,7000)
        bounds = [(5000,7000),(5000,9000)]
        NIter=10 #iterate number for T1 and T3
        instance = Sample(bounds, NIter)
        samples =instance.LHSample()
        T1sample=samples[:,0]
        T3sample=samples[:,1]
        T1List=[]
        T2List=[]
        T3List=[]
        fvalueList=[]
        for j1 in range(NIter):
            print(j1)
            ###call the improved Wu et al. method to conduct baseline correction
            T11,T22,T33,fvalue=improvedMethod (accFilePath,velFilePath,dispFilePath,dt,\
                                           fileNamei,nIterate,saveAccPath,saveVelPath,saveDispPath,T3sample[j1],T1sample[j1])
            T1List.append(T11)
            T2List.append(T22)
            T3List.append(T33)
            fvalueList.append(fvalue)
        maxIndex=fvalueList.index(max(fvalueList))
        finalT1=T1List[maxIndex]
        finalT2=T2List[maxIndex]
        finalT3=T3List[maxIndex]
        print("finalT1,T2,T3",finalT1,finalT2,finalT3)
        #########################################################################
        #########################################################################
        T1=finalT1 #T1 position in the motion, if T1=None the program will automatically determine T1
        T3=finalT3 # T3 position in the motion
        T2=finalT2 # T2 position in the motion
        T11,T22,T33,fvalue=improvedMethod (accFilePath,velFilePath,dispFilePath,dt,\
                                               fileNamei,nIterate,saveAccPath,saveVelPath,saveDispPath,T3,T1,T2)
        """
        from .baseLineCorrectionAndFiltering.BaseLineCorrectionAndFiltering import improvedWuBaseLineCorrect
        return improvedWuBaseLineCorrect(accFilePath, velFilePath, dispFilePath, t, fileNamei, nIterate, saveAccPath, \
                   saveVelPath, saveDispPath, T3, T1Self, T2)

    def highPassFilter(self,acc,dt,freq_corner,filter_order=4):
        """
        ----------------------------------------------------------------------------------------------------------------
        High pass acceleration filter based on FFT
        --------------------------------------------------------------------------------------------------------------------
        Inputs:
            acc(g)-acceleration time history
            dt(float)-acc time interval
            freq_corner (Hz)-the cut frequency, (Empirical approach，freq_corner=10.0**(1.4071 - 0.3452 * momentMag)  ##In Hz)
            filter_order-butterworth filter order (default value=4)
        """
        from .baseLineCorrectionAndFiltering.BaseLineCorrectionAndFiltering import accFilter
        fliteredAcc,num_pads=accFilter(acc,dt,freq_corner,filter_order)
        filterVel=self.accToVelocity(dt,fliteredAcc)
        filteredDisp=self.velToDisplacement(dt,filterVel)
        maxdisp = 0.01  ##单位cm
        index1 = next((n1 for n1, v1 in enumerate(filteredDisp) if abs(v1) >= maxdisp))  ##---生成器式查找
        returnAcc=fliteredAcc[index1:-num_pads]
        return returnAcc
########################################################################################################################
########################################################################################################################
class SectMCAnalysis():
    """
    --------------------------------------------------------------------------------------------------------------------
    A class for section moment curvature analysis
    --------------------------------------------------------------------------------------------------------------------
    ** **********************************************************************  **
    ** (C) Copyright 2023, Department of Bridge Engineering,Tongji University  **
    ** All Rights Reserved.                                                    **
    **                                                                         **
    ** Commercial use of this program is strictly prohibited.                  **
    **                                                                         **
    ** Developed by:                                                           **
    **  1. Penghui Zhang, Tongji University, https://github.com/Penghui0616    **
    **     penghui@tongji.edu.cn                                               **
    **  2. Junjun Guo,Tongji University. https://github.com/Junjun1guo         **
    **     guojj@tongji.edu.cn/guojj_ce@163.com                                **
    ** *********************************************************************   **

    --------------------------------------------------------------------------------------------------------------------
    """
    def __init__(self,saveFolderName,fiberFolderName,fiberSectName,coverFiber,coreFiber,barFiber,barMaterial,
                 concreteMaterial,loadDirection,maxMu=30,numIncr=100):
        """
        --------------------------------------------------------------------------------------------------------------------
        Inputs:
            saveFolderName(str)-the saved file folder name,eg."sectionMomentCurvatureFolder"
            fiberFolderName(str)-the fiber saved folder name, eg. "fiberDivide"
            fiberSectName(str)-the name of the fiber section
            coverFiber,coreFiber,barFiber-the section fibers get from SectionFiberDivide module
            barMaterial(str)-the material tag for section bars,eg. "HRB400",must include yield stress (Mpa)
            concreteMaterial(str)-the material of for section concrete,eg. "C40",must include concrete standard stress (Mpa)
            loadDirection(str)-the load direction, "X" or "Y"
            maxMu(int)-target ductility coefficient for analysis
            numIncr(int)-total steps for moment curvature analysis
        --------------------------------------------------------------------------------------------------------------------
        """
        self.folderName=saveFolderName
        self.fiberFolderName=fiberFolderName
        self.fiberSectName=fiberSectName
        self.coverFiber=coverFiber
        self.coreFiber=coreFiber
        self.barFiber=barFiber
        self.barMaterial=barMaterial
        self.concreteMaterial=concreteMaterial
        self.loadDirection=loadDirection
        self.maxMu=maxMu
        self.numIncr=numIncr

        self.path = os.getcwd()
        print("currentPath=",self.path)

    def circularSect(self,hoopType,outD,coverThick,s,Dhoop,fyHoop,axialLoad,otherMoment=0):
        """
        ----------------------------------------------------------------------------------------------------------------
        circular section moment curvature analysis
        ----------------------------------------------------------------------------------------------------------------
        Inputs:
            hoopType(str)-stirrup type,'Circular' or 'Spiral'
            outD(float)-the outside diameter of the circular section (m)
            coverThick(float)-cover concrete depth of the section (m)
            s(float)-longitudinal space of adjancent stirrups (m)
            Dhoop(float)-the diameter of the stirrup  (m)
            fyHoop(float)-the yield stress of the stirrup (Mpa)
            axialLoad(float)-axial load,eg,200 (kN)
            otherMoment(float)-moment in the other direction (KN.m)
        ----------------------------------------------------------------------------------------------------------------
        ###---Example 1
        ##############################----circular section example-----#################################################
        fiberDivideInstance=SectionFiberDivide("fiberDivideInformation")
        name = "circularPier"  # section name
        outD = 2  # the diameter of the outside circle
        coverThick = 0.06  # the thinckness of the cover concrete
        outbarD = 0.032  # outside bar diameter
        outbarDist = 0.119  # outside bar space
        coreSize = 0.1  # the size of core concrete fiber
        coverSize = 0.1  # the size of cover concrete fiber
        autoBarMesh=True
        userBarInfoList=[[0.065,outbarD,outbarDist],[0.115,outbarD,outbarDist]]
        inD=None
        inBarD=outbarD
        inBarDist=outbarDist
        lineWidth=0.5
        markerSize=2
        coreFiber, coverFiber, barFiber=fiberDivideInstance.circleSection(name, outD, coverThick, outbarD, outbarDist,
            coreSize, coverSize,autoBarMesh)
        sectMCInstance=SectMCAnalysis(saveFolderName="sectionMomentCurvatureFolder",fiberFolderName="fiberDivideInformation",
        fiberSectName="circularPier",coverFiber=coverFiber,coreFiber=coreFiber,barFiber=barFiber,barMaterial="HRB400",
        concreteMaterial="C40",loadDirection="Y",maxMu = 40,numIncr = 200)
        sectMCInstance.circularSect(hoopType="Spiral",outD=outD,coverThick=coverThick,s=0.1,Dhoop=0.014,fyHoop=400,
                                    axialLoad=200)
        ----------------------------------------------------------------------------------------------------------------
        """
        from .MCAnalysis.Material import Material
        from .MCAnalysis.MCAnalysis import MC
        # Define material
        ###roucc-纵向配筋率
        roucc = np.sum(self.barFiber, axis=0)[2] / (np.sum(self.coverFiber, axis=0)[2] + np.sum(self.coreFiber, axis=0)[2])
        material = Material(self.folderName,self.fiberSectName)
        barParameter = material.barParameter(self.barMaterial)
        coverParameter = material.coverParameter(self.concreteMaterial)
        coreParameter = material.coreParameterCircular(self.concreteMaterial,hoopType, outD, coverThick, roucc,s,Dhoop,fyHoop)
        # Estimate the yield curvature of circular section
        D =outD# length of the outer section in x direction
        kx = 2.213 * barParameter[0] / barParameter[2] / D
        ky = kx
        np.savetxt(self.folderName+"/"+self.fiberSectName+"/yieldCurvature.txt", [kx, ky], fmt="%0.6f")
        # Moment curvature analysis
        mcInstance = MC(self.folderName,self.fiberFolderName,self.fiberSectName,self.loadDirection)
        mcInstance.MCAnalysis(axialLoad,otherMoment,self.maxMu,self.numIncr)
        momEff = mcInstance.MCCurve()

    def rectangularSect(self,coverThick,lx,ly,outBarDist,outBarD,roux,rouy,s,Dhoop,fyHoop,axialLoad,otherMoment=0):
        """
        ----------------------------------------------------------------------------------------------------------------
        rectangular section moment curvature analysis
        ----------------------------------------------------------------------------------------------------------------
        Inputs:
            coverThick(float)-cover concrete depth of the section (m)
            lx(float)-length of the outer section in x direction (m)
            ly(float)-length of the outer section in y direction (m)
            outbarDist(float)--the longitudinal bar space (m)
            outBarD(float)-longitudinal bar diameter (m)
            roux,rouy(float)-stirrup volume reinforcement ratio in x,y direction, respectively
            参考范立础院士延性抗震设计专著中的计算方法，对于所求方向配箍率的计算，对于不同约束肢的区间分别计算，并乘以对应的比例，最后加权求和，
            对于有斜肢的可以先投影到对应方向再计算
            s(float)-transverse bar space (m)
            Dhoop(float)-transverse bar diameter (m)
            fyHoop(float)-transverse bar yield stress (Mpa)
            axialLoad(float)-axial load,eg,200 (kN)
            otherMoment(float)-moment in the other direction (KN.m)
        ----------------------------------------------------------------------------------------------------------------
        ###---Example
        ##############################----rectangular section example-----##############################################
        fiberDivideInstance = SectionFiberDivide("fiberDivideInformation")
        sectName = "RectangularPier"
        outSideNode = {1: (3.5, 3), 2: (1.5, 5), 3: (-1.5, 5), 4: (-3.5, 3), 5: (-3.5, -3), 6: (-1.5, -5), 7: (1.5, -5),
                       8: (3.5, -3)}
        outSideEle = {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 5), 5: (5, 6), 6: (6, 7), 7: (7, 8), 8: (8, 1)}
        coverThick = 0.06  # the thinckness of the cover concrete(m)
        coreSize = 0.2  # the size of core concrete fiber
        coverSize = 0.3  # the size of cover concrete fiber
        outBarDist = 0.2  # bar space(m)
        outBarD = 0.032  # bar diameter(m)
        autoBarMesh = True  # if false provide the barControlNodeDict and barEleDict
        userBarNodeDict = None  # {1:(y1,z1),2:(y2,z2),...} bar line end nodes
        userBarEleDict = None  # {1:(nodeI,nodeJ,barD,barDist),...}  bar line end nodes number and diameter and distance
        fiberDivideInstance = SectionFiberDivide()
        coreFiber, coverFiber, barFiber = fiberDivideInstance.polygonSection(sectName, outSideNode, outSideEle,
        coverThick, coreSize, coverSize, outBarD,outBarDist, autoBarMesh, lineWidth=0.5,markerSize=0.5)
        sectMCInstance = SectMCAnalysis(saveFolderName="sectionMomentCurvatureFolder",fiberFolderName="fiberDivideInformation",
        fiberSectName="RectangularPier", coverFiber=coverFiber,coreFiber=coreFiber, barFiber=barFiber, barMaterial="HRB400",
                                        concreteMaterial="C40", loadDirection="X", maxMu=100,numIncr=500)
        ######参考Prestly或者范院士延性抗震设计专著中的计算方法，对于所求方向配箍率的计算，对于不同约束肢的区间分别计算，并乘以对应的比例，
        ######最后加权求和，对于有斜肢的可以先投影到对应方向再计算
        sectMCInstance.rectangularSect(coverThick=coverThick, lx=1.6, ly=3.2, outBarDist=outBarDist, outBarD=outBarD,
                                       roux=0.005, rouy=0.005, s=0.15, Dhoop=0.012, fyHoop=400, axialLoad=23000,
                                       otherMoment=0)
        ----------------------------------------------------------------------------------------------------------------
        """
        from .MCAnalysis.Material import Material
        from .MCAnalysis.MCAnalysis import MC
        # Define material
        roucc = np.sum(self.barFiber, axis=0)[2] / np.sum(self.coreFiber, axis=0)[2]
        material = Material(self.folderName,self.fiberSectName)
        barParameter = material.barParameter(self.barMaterial)
        coverParameter = material.coverParameter(self.concreteMaterial)
        coreParameter = material.coreParameterRectangular(self.concreteMaterial, lx, ly, coverThick, roucc,outBarDist,
                                outBarD, roux, rouy, s,Dhoop, fyHoop)

        # Estimate the yield curvature of rectangular section
        kx = 1.957 * barParameter[0] / barParameter[2] / lx
        ky = 1.957 * barParameter[0] / barParameter[2] / ly
        np.savetxt(self.folderName+"/"+self.fiberSectName+"/yieldCurvature.txt", [kx, ky], fmt="%0.6f")

        # Moment curvature analysis
        mcInstance = MC(self.folderName,self.fiberFolderName,self.fiberSectName,self.loadDirection)
        mcInstance.MCAnalysis(axialLoad,otherMoment,self.maxMu,self.numIncr)
        momEff = mcInstance.MCCurve()
########################################################################################################################
########################################################################################################################
class ExciteAnyDirectionOpenSees():
    """
    --------------------------------------------------------------------------------------------------------------------
    A class for ground motion excite OpenSeesPy model in any direction
    --------------------------------------------------------------------------------------------------------------------
    ** (C) Copyright 2023, Department of Bridge Engineering,Tongji University  **
    ** All Rights Reserved.                                                    **
    **                                                                         **
    ** Commercial use of this program is strictly prohibited.                  **
    **                                                                         **
    ** Developed by:                                                           **
    **     Junjun Guo,Tongji University. https://github.com/Junjun1guo         **
    **     guojj@tongji.edu.cn/guojj_ce@163.com                                **
    ** *********************************************************************   **
    """
    def __init__(self,rotateAngle=0):
        """
        ----------------------------------------------------------------------------------------------------------------
        Inputs:
            rotateAngle(angle degrees)-a clockwise angle for ground motion exicte
        ----------------------------------------------------------------------------------------------------------------
        """
        self.rotateAngle=rotateAngle

    def PointsRotate (self,x,y):
        """
        ----------------------------------------------------------------------------------------------------------------
        Rotate a point with respect to the original point (0,0)
        ----------------------------------------------------------------------------------------------------------------
        Inputs:
            x,y(float)-points coordinate values in global X and Y axis, anticlockwise rotate
        Outputs:
            newx,newy(float)-point rotated coordinate values in global X and Y axis
        ----------------------------------------------------------------------------------------------------------------
        """
        alpha=self.rotateAngle/float(180.0)*math.pi
        if x == 0 and y == 0:
            newX = 0.0
            newY = 0.0
        elif x > 0.0 and y == 0:
            length1 = (x ** 2 + y ** 2) ** 0.5
            angle1 = 0.0
            newAngle = angle1 + alpha
            newX = (length1 * math.cos(newAngle))
            newY = (length1 * math.sin(newAngle))
        elif x == 0.0 and y > 0:
            length2 = (x ** 2 + y ** 2) ** 0.5
            angle2 = (90.0 / float(180.0)) * math.pi
            newAngle = angle2 + alpha
            newX = (length2 * math.cos(newAngle))
            newY = (length2 * math.sin(newAngle))
        elif x < 0.0 and y == 0:
            length3 = (x ** 2 + y ** 2) ** 0.5
            angle3 = (180.0 / float(180.0)) * math.pi
            newAngle = angle3 + alpha
            newX = (length3 * math.cos(newAngle))
            newY = (length3 * math.sin(newAngle))
        elif x == 0.0 and y < 0:
            length4 = (x ** 2 + y ** 2) ** 0.5
            angle4 = (270.0 / float(180.0)) * math.pi
            newAngle = angle4 + alpha
            newX = (length4 * math.cos(newAngle))
            newY = (length4 * math.sin(newAngle))
        elif x > 0.0 and y > 0:
            length5 = (x ** 2 + y ** 2) ** 0.5
            angle5 = math.atan(y / float(x))
            newAngle = angle5 + alpha
            newX = (length5 * math.cos(newAngle))
            newY = (length5 * math.sin(newAngle))
        elif x < 0.0 and y > 0:
            length6 = (x ** 2 + y ** 2) ** 0.5
            angle6 = math.atan(y / float(x)) + math.pi
            newAngle = angle6 + alpha
            newX = (length6 * math.cos(newAngle))
            newY = (length6 * math.sin(newAngle))
        elif x < 0.0 and y < 0:
            length7 = (x ** 2 + y ** 2) ** 0.5
            angle7 = math.atan(y / float(x)) + math.pi
            newAngle = angle7 + alpha
            newX = (length7 * math.cos(newAngle))
            newY = (length7 * math.sin(newAngle))
        else:
            length8 = (x ** 2 + y ** 2) ** 0.5
            angle8 = math.atan(y / float(x)) + 2 * math.pi
            newAngle = angle8 + alpha
            newX = (length8 * math.cos(newAngle))
            newY = (length8 * math.sin(newAngle))
        return newX, newY

    def localZvector(self,eleVector,refVector):
        """
        ----------------------------------------------------------------------------------------------------------------
        get local Z vector that perperticular to two vetors in a plane,one is a vector based on element (from I to J),
        and the other is easily specified,eg. 0,0,1
        -----------------------------
        Inputs:
            eleVector(list)-A element vector made up of I and J nodes, eg.(xj-xi,yj-ji,zj-zi)
            refVector(list)-A reference vector that in the same plane with eleVector, and perperticular to localZvector
        ----------------------------------------------------------------------------------------------------------------
        """
        a=np.array(eleVector)
        b=np.array(refVector)
        c=np.cross(a,b)
        vectorNorm=np.linalg.norm(c)
        localzVector=(c[0]/float(vectorNorm),c[1]/float(vectorNorm),c[2]/float(vectorNorm))
        return localzVector
########################################################################################################################
########################################################################################################################
def CableEqualStiffness (iNode,jNode,T,gamma=78.5,k=2,E=2.05e8,sigma=1770000):
    """
    --------------------------------------------------------------------------------------------------------------------
    Units: Length-m, Force-kN, mass-ton, Stress-kpa(10e-3MPa), g=9.81m/s2
		Function: This function calculates the equalStiffness of cable by Ernst formula
		inputs: inode,jnode--The end nodes of the cable((xi,yi,zi),(xj,yj,zj))
			T-tension force of cable(kN);
			gamma-Weight per m3,default is 78.5kN/m3
			k-safety factor of cable, default is 2
			E-Elastic stiffness of cable, default is 2.05e8kpa
			sigma-cable design stress, default is 1860000kPa
		outPuts: EqualE,mu,A,TensionSigma
			EqualE--The modified elastic stiffness (kPa)
			mu--Modified factor
			A--Area of the cable (m2)
			TensionSigma--Real stress in cable (kPa)
	--------------------------------------------------------------------------------------------------------------------
	"""
    A=float(T*k)/float(sigma)
    deltaX=jNode[0]-iNode[0]
    deltaY=jNode[1]-iNode[1]
    L=(deltaX**2+deltaY**2)**0.5
    TensionSigma=T/float(A)
    mu=1/float(1+gamma**2*L**2*E/float(12*TensionSigma**3))
    EqualE=E*mu
    return EqualE,mu,A,TensionSigma
########################################################################################################################
########################################################################################################################
class PythonInteractSAP2000():
    """
    --------------------------------------------------------------------------------------------------------------------
    A class for python interact with SAP2000
    --------------------------------------------------------------------------------------------------------------------
    ** (C) Copyright 2023, Department of Bridge Engineering,Tongji University  **
    ** All Rights Reserved.                                                    **
    **                                                                         **
    ** Commercial use of this program is strictly prohibited.                  **
    **                                                                         **
    ** Developed by:                                                           **
    **     Junjun Guo,Tongji University. https://github.com/Junjun1guo         **
    **     guojj@tongji.edu.cn/guojj_ce@163.com                                **
    ** *********************************************************************   **
    --------------------------------------------------------------------------------------------------------------------
    ####---注意：需要首先打开软件，且确保只有一个软件在运行
    ####---查看任务管理器，详细信息里面查看是否有多个SAP2000程序在运行，关闭其他的
    ###---Example
    pySAPinit=PythonInteractSAP2000()
    sapInstance=pySAPinit.getSAP2000Instance()
    print(help(sapInstance)) ###---to get the description of each method defined in the class
    --------------------------------------------------------------------------------------------------------------------
    """
    def __init__(self):
        """
        """
        self.sapObject = comtypes.client.GetActiveObject('CSI.SAP2000.API.SapObject')  ##针对SAP2000
        self.sapModel = self.sapObject.SapModel
    def getSAP2000Instance(self):
        """
        ----------------------------------------------------------------------------------------------------------------
        To get the opended SAP2000 program object
        ----------------------------------------------------------------------------------------------------------------
        """
        from .pythonInteractSAP2000.SAP2000Py import SAP2000Py
        return SAP2000Py(self.sapObject,self.sapModel)
########################################################################################################################
########################################################################################################################
class ShakeTableTest():
    """
    --------------------------------------------------------------------------------------------------------------------
    A class for processing shake table test data
    --------------------------------------------------------------------------------------------------------------------
    ** (C) Copyright 2023, Department of Bridge Engineering,Tongji University  **
    ** All Rights Reserved.                                                    **
    **                                                                         **
    ** Commercial use of this program is strictly prohibited.                  **
    **                                                                         **
    ** Developed by:                                                           **
    **     Junjun Guo,Tongji University. https://github.com/Junjun1guo         **
    **     guojj@tongji.edu.cn/guojj_ce@163.com                                **
    ** *********************************************************************   **
    --------------------------------------------------------------------------------------------------------------------
    ###---Example
    --------------------------------------------------------------------------------------------------------------------

    """
    def __init__(self):
        """

        """
        pass

    def scaleRatio(self,lengthRatio,stressRatio,acceleratioRatio=1):
        """
        ----------------------------------------------------------------------------------------------------------------
        method for calculating the scale ratio (model to prototype)
        ----------------------------------------------------------------------------------------------------------------
        Inputs:
            lengthRatio(float)-length scale ratio, L
            stressRatio(float)-stress scale ratio, M-1T-2
            gravityRatio(float)-acceleration ratio, LT-2, default value 1
        ----------------------------------------------------------------------------------------------------------------
        ###---Example:
            shakeInstance=ShakeTableTest()
            scaleRatioDict = shakeInstance.scaleRatio(lengthRatio=0.2, stressRatio=0.3, acceleratioRatio=1)
        ----------------------------------------------------------------------------------------------------------------
        """
        ######-----材料性能
        stressRatio = stressRatio
        elasticModulusRatio = stressRatio
        strainRatio = stressRatio / float(elasticModulusRatio)
        possionRatio = 1
        massDensityRatio = stressRatio / float(acceleratioRatio * lengthRatio)
        massRatio = stressRatio * lengthRatio ** 2 / float(acceleratioRatio)
        ######-----几何特性
        lengthRatio = lengthRatio
        areaRatio = lengthRatio ** 2
        translationalDisp = lengthRatio
        rotationalAngle = stressRatio / float(elasticModulusRatio)
        ######-----荷载性能
        forceRatio = stressRatio * lengthRatio ** 2
        momentRatio = stressRatio * lengthRatio ** 3
        ######-----动力特性
        stiffnessRatio = stressRatio * lengthRatio
        timeRatio = lengthRatio ** 0.5 * acceleratioRatio ** (-0.5)
        freqencyRatio = 1.0 / float(timeRatio)
        dampingRatio = stressRatio * lengthRatio ** 1.5 * acceleratioRatio ** (-0.5)
        velocityRatio = (lengthRatio * acceleratioRatio) ** 0.5
        acceleratioRatio = acceleratioRatio
        gravityAccRatio = 1
        #######################
        scaleRatioDict = {"Sstrain": round(strainRatio, 10), "Sstress": round(stressRatio, 10),
                          "Selas": round(elasticModulusRatio, 10),
                          "Spossion": round(possionRatio, 10), "SmassDensity": round(massDensityRatio, 10),
                          "Smass": round(massRatio, 10), "Slength": round(lengthRatio, 10),
                          "Sarea": round(areaRatio, 10),
                          "StransDisp": round(translationalDisp, 10), "SrotDisp": round(rotationalAngle, 10),
                          "Sforce": round(forceRatio, 10), "Smoment": round(momentRatio, 10),
                          "Sstif": round(stiffnessRatio, 10),
                          "Stime": round(timeRatio, 10), "Sfreq": round(freqencyRatio, 10),
                          "Sdamp": round(dampingRatio, 10),
                          "Svel": round(velocityRatio, 10), "Sacc": round(acceleratioRatio, 10),
                          "SgravityAcc": round(1, 10)}
        return scaleRatioDict

    def plotAcc(self,timesList,accList,labelsList):
        """
        ----------------------------------------------------------------------------------------------------------------
        Inputs:
            times(list,list,second)-time sequence, eg.[[0,0.1,0.2,...],[]]
            accList(list,list,g)-acceleration list, and each item is also a acceleration list,eg.[[0.0,0.1,-0.2,...],[],...]
            labelsList(str list)-a list contains labels for each ground motion, eg.['acc1','acc2',...]
        Output:
            plt
        ----------------------------------------------------------------------------------------------------------------
        ###---Example:
            times=np.loadtxt("WN_Responses/1-WN-times.txt")
            acc_1_AX5=np.loadtxt("WN_Responses/1-WN-T1-5-AX.txt")
            acc_1_AX1 = np.loadtxt("WN_Responses/1-WN-T1-1-AX.txt")
            acc_1_AX3 = np.loadtxt("WN_Responses/1-WN-T1-3-AX.txt")
            acc_1_AX4 = np.loadtxt("WN_Responses/1-WN-T1-4-AX.txt")
            acc_1_GAX1=np.loadtxt("WN_Responses/1-WN-GAX-1.txt")
            pltHandle=shakeInstance.plotAcc([times,times,times,times],[acc_1_AX5,acc_1_AX4,acc_1_AX3,acc_1_AX1],
                                   labelsList=['T1-5-AX','T1-4-AX','T1-3-AX','T1-1-AX'])
            pltHandle.show()
        ----------------------------------------------------------------------------------------------------------------
        """
        numAcc=len(accList)
        plt.figure(figsize=(9.5, 2*numAcc))
        for i1 in range(numAcc):
            axi=plt.subplot(numAcc,1,i1+1)
            axi.plot(timesList[i1],accList[i1],label=labelsList[i1])
            axi.set_xlabel('Time(s)', fontsize=15)
            axi.set_ylabel('Acceleration(g)', fontsize=15)
            axi.legend()
            axi.grid(True)
            axi.set_xlim(timesList[i1][0],timesList[i1][-1])
            maxAcc=max(np.abs(accList[i1]))
            axi.set_ylim(-1.2*maxAcc,1.2*maxAcc)
        plt.tight_layout()
        return plt

    def freResFunc(self,dt,modeNum,accBase,accOtherPosList,labelStrList,maxXplot,maxYplot):
        """
        ----------------------------------------------------------------------------------------------------------------
        The acceleration frequency response function(FRF) can be computed by using the base acceleration as input
        and the acceleration at other positions as the output. FRF can tell you the scale factor between the input and
        output, and the phase of a structure at a given frequency. FRF can be used to calculate the periods and damping
        ratios of a structure.
        ----------------------------------------------------------------------------------------------------------------
        Inputs:
            dt(float)-time step of the time histories
            modeNum(int)-the total number of modes to be identified
            accBase(list)-the base acceleration time history,[0.0,-0.012,0.0234,...]
            accOtherPosList(list)-acceleration time histories in other positions, [[0,0.01,-0.04,...],[]]
            labelStrList(str,list)-the label of the acc in other positions ['acc1','acc2',...]
            maxXplot(float)-the maximum frequency display on the x axis (Hz).
            maxYplot(float)-the maximum Y value of the plot
        Output:
            plt
        ----------------------------------------------------------------------------------------------------------------
        ###---Example:
            times=np.loadtxt("WN_Responses/1-WN-times.txt")
            dt=times[1]-times[0]
            pltHandle=shakeInstance.freResFunc(dt,3,acc_1_AX5,[acc_1_AX1],['1'],10,90)
            pltHandle.show()
        ----------------------------------------------------------------------------------------------------------------
        """
        fs=1.0/float(dt) ###--采样频率(Hz)
        nfft=len(accBase) ###---FFT采用的长度
        ###---设置谱密度参数
        N_segments = 15  ###---段数
        overlapPercent = 50  ###---重叠比例
        seg_length = nfft / float(N_segments)  ###---确定每段的长度
        overlap = (nfft / float(N_segments)) * overlapPercent / float(100) ###---确定重叠的点数
        ####   compute the power spectral density (PSD) of the base acc. (input data for transfer function)
        fxx, Sxx = signal.csd(accBase,accBase, fs, 'hann', seg_length, overlap, nfft) ###---自功率谱
        plt.figure(figsize=(9,10))
        numAcc=len(accOtherPosList)
        color_names = ["black","red", "green", "blue", "yellow", "cyan", "magenta", "gray", "orange",
                       "brown", "pink", "purple", "turquoise", "silver", "gold", "navy", "olive", "maroon", "beige"]
        H1_3List=[]
        f3nList=[]
        fxy3List=[]
        Hv_abs_nfcn3List=[]
        peak_indexList=[]
        for i0 in range(numAcc):
            plt.subplot(2,1,1)
            ####   compute the PSD and cross spectral density (CSD) for accelerations in other position
            accOtherPos=accOtherPosList[i0]
            labelStr=labelStrList[i0]
            color0=color_names[i0%19]
            fyy3, Syy3 = signal.csd(accOtherPos,accOtherPos, fs, 'hann', seg_length, overlap, nfft)
            fxy3, Sxy3 = signal.csd(accBase,accOtherPos, fs, 'hann', seg_length, overlap, nfft)
            fxy3List.append(fxy3)
            ####   compute transfer function based on accs at base and other position
            H1_3 = Sxy3 / Sxx
            H1_3List.append(H1_3)
            H2_3 = Syy3 / Sxy3
            Hv_abs_nfcn3 = abs(H1_3) * abs(H2_3)
            Hv_abs_nfcn3List.append(Hv_abs_nfcn3)
            # find first modeNum peaks in magnitude plot
            peak_index = argrelextrema(20 * np.log10(Hv_abs_nfcn3)[15:], np.greater, axis=0, order=300)
            peak_indexList.append(peak_index)
            f3n=[fxy3[peak_index[0][j1] + 15] for j1 in range(modeNum)]
            f3nList.append(f3n)
            ###############################
            dampRatioList=[]
            #####################################################################
            ####---damping ratio=(f2-f1)/(2.0*fn) based on half-power bandwidth method
            for n1 in range(modeNum):
                realPeak_index1=peak_index[0][n1]+15
                maxAmp=Hv_abs_nfcn3[realPeak_index1]
                pwrpoint =maxAmp/ float(2 ** 0.5)
                lower0=next(i1 for i1 in range(realPeak_index1,0,-1) if Hv_abs_nfcn3[i1]<=pwrpoint)
                ratio1=(pwrpoint-Hv_abs_nfcn3[lower0])/float(Hv_abs_nfcn3[lower0+1]-Hv_abs_nfcn3[lower0])
                freq1=fxy3[lower0]+ratio1*(fxy3[lower0+1]-fxy3[lower0])
                upperIndex = next(i1 for i1 in range(realPeak_index1,len(Hv_abs_nfcn3),1) if Hv_abs_nfcn3[i1] <= pwrpoint)
                ratio2=(Hv_abs_nfcn3[upperIndex-1]-pwrpoint)/float(Hv_abs_nfcn3[upperIndex-1]-Hv_abs_nfcn3[upperIndex])
                freq2=fxy3[upperIndex-1]+ratio2*(fxy3[upperIndex]-fxy3[upperIndex-1])
                fn=fxy3[realPeak_index1]
                dampRatio1=(freq2-freq1)/float(2.0*fn)
                dampRatioList.append(dampRatio1)
                plt.axvline(x=freq1,c=color0,ls='--', alpha=1, lw=1.5)
                plt.axvline(x=freq2, c=color0, ls='--', alpha=1, lw=1.5)
                xvalues=fxy3[(lower0-20):(upperIndex+20)]
                yvalues=[pwrpoint for each in xvalues]
                plt.plot(xvalues,yvalues,ls='--', color=color0, lw=2)
            #############################################################################
            plt.plot(fxy3,Hv_abs_nfcn3,color=color0, lw=2, label=labelStr)
            [plt.axvline(x=f3n[j1], alpha=1,color=color0, lw=1.5, label=f"T-{j1+1}={format(1.0/f3n[j1],'.3f')} s--"
                                f"dampRatio={format(dampRatioList[j1]*100,'.3f')}%") for j1 in range(modeNum)]
        plt.xlabel('frequency [Hz]', fontsize=16)
        plt.ylabel('Amplitude', fontsize=16)
        plt.xlim(0, maxXplot)
        plt.ylim(0, maxYplot)
        plt.title(f'Magnitude of Transfer Function-{labelStr}', fontsize=20)
        plt.xticks(fontsize=16)
        plt.yticks(fontsize=16)
        plt.legend(fontsize=14)
        plt.grid(True)
        plt.subplot(2, 1, 2)
        for i1 in range(numAcc):
            labelStr = labelStrList[i1]
            color0 = color_names[i1 % 19]
            plt.plot(fxy3List[i1], np.angle(H1_3List[i1])*180/float(np.pi), color=color0, lw=2, label=labelStr)
            [plt.axvline(x=f3nList[i1][j1], alpha=1, color=color0, lw=1.5, label=f"T-{j1 + 1}={format(1.0 / f3n[j1], '.3f')} s")
             for j1 in range(modeNum)]
        plt.xlabel('frequency [Hz]', fontsize=16)
        plt.ylabel('Phase (degree)', fontsize=16)
        plt.xlim(0, maxXplot)
        plt.ylim(-180,180)
        plt.title(f'Phase of -{labelStr}', fontsize=20)
        plt.xticks(fontsize=16)
        plt.yticks(fontsize=16)
        plt.legend(fontsize=14)
        plt.grid(True)
        return plt
########################################################################################################################
########################################################################################################################
class HystereticResponseAnalyses():
    """
        --------------------------------------------------------------------------------------------------------------------
        A class for analyzing the force-displacement hysteretic loops
        --------------------------------------------------------------------------------------------------------------------
        ** (C) Copyright 2023, Department of Bridge Engineering,Tongji University  **
        ** All Rights Reserved.                                                    **
        **                                                                         **
        ** Commercial use of this program is strictly prohibited.                  **
        **                                                                         **
        ** Developed by:                                                           **
        **     Junjun Guo,Tongji University. https://github.com/Junjun1guo         **
        **     guojj@tongji.edu.cn/guojj_ce@163.com                                **
        ** *********************************************************************   **
        --------------------------------------------------------------------------------------------------------------------
        ###---Example
        --------------------------------------------------------------------------------------------------------------------
    """

########################################################################################################################
########################################################################################################################
class UniaxialMaterialTest():
    pass

########################################################################################################################
########################################################################################################################
if __name__ == "__main__":
    ###################
    # opsX=OpenSeesPyX(dataBaseName="testDataBase")
    # Bcol = 0.711
    # Hcol = Bcol
    #
    # c = 0.076  # cover
    #
    # y1col = Hcol / 2.0
    # z1col = Bcol / 2.0
    #
    # y2col = 0.5 * (Hcol - 2 * c) / 3.0
    #
    # nFibZ = 1
    # nFib = 20
    # nFibCover, nFibCore = 2, 16
    # As9 = 0.0006446
    #
    # fib_sec_2 = [['section', 'Fiber', 3, '-GJ', 1.0e6],
    #              ['patch', 'rect', 2, nFibCore, nFibZ, c - y1col, c - z1col, y1col - c, z1col - c],
    #              ['patch', 'rect', 3, nFib, nFibZ, -y1col, -z1col, y1col, c - z1col],
    #              ['patch', 'rect', 3, nFib, nFibZ, -y1col, z1col - c, y1col, z1col],
    #              ['patch', 'rect', 3, nFibCover, nFibZ, -y1col, c - z1col, c - y1col, z1col - c],
    #              ['patch', 'rect', 3, nFibCover, nFibZ, y1col - c, c - z1col, y1col, z1col - c],
    #              ['layer', 'straight', 4, 4, As9, y1col - c, z1col - c, y1col - c, c - z1col],
    #              ['layer', 'straight', 4, 2, As9, y2col, z1col - c, y2col, c - z1col],
    #              ['layer', 'straight', 4, 2, As9, -y2col, z1col - c, -y2col, c - z1col],
    #              ['layer', 'straight', 4, 4, As9, c - y1col, z1col - c, c - y1col, c - z1col]]
    # matcolor = ['r', 'lightgrey', 'gold', 'w', 'w', 'w']
    # opsX.auxiliary_fiberSectionPlot(saveFold='sectFiberPlot',fiberSectList=fib_sec_2,matColorList=matcolor)
    # print(opsX.nodeSetNameList)
    ###################
    ######################################-----------SectionFiberDivide------###########################################
    ###########################---sectionFiberDivide test
    # fiberDivideInstance=SectionFiberDivide()
    # # fiberDivideInstance.deleteDir()
    # name = "circle"  # section name
    # outD = 2  # the diameter of the outside circle
    # coverThick = 0.05  # the thinckness of the cover concrete
    # outbarD = 0.03  # outside bar diameter
    # outbarDist = 0.15  # outside bar space
    # coreSize = 0.1  # the size of core concrete fiber
    # coverSize = 0.1  # the size of cover concrete fiber
    # autoBarMesh=False
    # userBarInfoList=[[0.065,outbarD,outbarDist],[0.115,outbarD,outbarDist]]
    # inD=1
    # inBarD=outbarD
    # inBarDist=outbarDist
    # lineWidth=0.5
    # markerSize=2
    # fiberDivideInstance.circleSection(name, outD, coverThick, outbarD, outbarDist,
    #     coreSize, coverSize,autoBarMesh,userBarInfoList,inD,inBarD,inBarDist,lineWidth,markerSize)
    # fiberDivideInstance.plotFibers(name)
    ###################################################
    # fiberDivideInstance = SectionFiberDivide()
    # name = "polygon"  # section  name
    # # the outside vertexes consecutively numbering and coordinate values in local y-z plane in dict container
    # outSideNode = {1: (3.5, 3), 2: (1.5, 5), 3: (-1.5, 5), 4: (-3.5, 3), 5: (-3.5, -3), 6: (-1.5, -5), 7: (1.5, -5),
    #                8: (3.5, -3)}  # anti-clockwise numbering
    # # the outside vertexes loop consecutively numbering in dict container
    # outSideEle = {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 5), 5: (5, 6), 6: (6, 7), 7: (7, 8), 8: (8, 1)}
    # coverThick = 0.06  # the thinck of the cover concrete
    # coreSize = 0.2  # the size of the core concrete fiber elements
    # coverSize = 0.3  # the size of the cover concrete fiber elements
    # outBarD = 0.032  # outside bar diameter
    # outBarDist = 0.2  # outside bar space
    # autoBarMesh = True  # if false provide the barControlNodeDict and barEleDict
    # userBarNodeDict = None  # {1:(y1,z1),2:(y2,z2),...} bar line end nodes
    # userBarEleDict = None  # {1:(nodeI,nodeJ,barD,barDist),...}  bar line end nodes number and diameter and distance
    # fiberDivideInstance.polygonSection(name, outSideNode, outSideEle, coverThick,coreSize, coverSize,outBarD,
    #                                    outBarDist,autoBarMesh,lineWidth=0.5,markerSize=0.5)
    # fiberDivideInstance.plotFibers(name)
    ###################################################
    # fiberDivideInstance = SectionFiberDivide()
    # name = "polygonWithThreeHoles"
    # outSideNode = {1: (0, 0), 2: (7, 0), 3: (7, 3), 4: (0, 3)}  # anti-clockwise numbering
    # # the outside vertexes loop consecutively numbering in dict container
    # outSideEle = {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 1)}
    # # the inside vertexes consecutively numbering and coordinate values in local y-z plane in list container
    # inSideNode = [
    #     {1: (1, 1), 2: (2, 1), 3: (2, 2), 4: (1, 2)},
    #     {1: (3, 1), 2: (4, 1), 3: (4, 2), 4: (3, 2)},
    #     {1: (5, 1), 2: (6, 1), 3: (6, 2), 4: (5, 2)}]  # anti-clockwise numbering
    # # the inside vertexes loop consecutively numbering in dict container
    # inSideEle = [{1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 1)},
    #              {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 1)},
    #              {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 1)}]
    # coverThick = 0.06  # the thinck of the cover concrete
    # coreSize = 0.2  # the size of the core concrete fiber elements
    # coverSize = 0.3  # the size of the cover concrete fiber elements
    # outBarD = 0.032  # outside bar diameter
    # outBarDist = 0.2  # outside bar space
    # autoBarMesh = True  # if false provide the barControlNodeDict and barEleDict
    # userBarNodeDict = None
    # userBarEleDict = None
    # inBarD = 0.032  # inside bar diameter (None)
    # inBarDist = 0.2  # inside bar space (None)
    # fiberDivideInstance.polygonSection(name, outSideNode, outSideEle, coverThick, coreSize, coverSize, outBarD,
    #                                    outBarDist, autoBarMesh,userBarNodeDict,userBarEleDict,inSideNode,inSideEle,
    # inBarD,inBarDist,lineWidth=0.5, markerSize=0.5)
    #####################################################
    # fiberDivideInstance = SectionFiberDivide()
    # name = "polygonWithHole"
    # # the outside vertexes consecutively numbering and coordinate values in local y-z plane in dict container
    # outSideNode = {1: (2.559, 2.1), 2: (-2.559, 2.1), 3: (-2.559, 1.6), 4: (-3.059, 1.6), 5: (-3.059, -1.6),
    #                6: (-2.559, -1.6), 7: (-2.559, -2.1), 8: (2.559, -2.1), 9: (2.559, -1.6), 10: (3.059, -1.6),
    #                11: (3.059, 1.6),
    #                12: (2.559, 1.6)}  # anti-clockwise numbering
    # # the outside vertexes loop consecutively numbering in dict container
    # outSideEle = {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 5), 5: (5, 6), 6: (6, 7), 7: (7, 8), 8: (8, 9), 9: (9, 10), \
    #               10: (10, 11), 11: (11, 12), 12: (12, 1)}
    # # the inside vertexes consecutively numbering and coordinate values in local y-z plane in list container
    # inSideNode = [{1: (1.809, 1.35), 2: (-1.809, 1.35), 3: (-2.309, 0.85), 4: (-2.309, -0.85), 5: (-1.809, -1.35), \
    #                6: (1.809, -1.35), 7: (2.309, -0.85), 8: (2.309, 0.85)}]  ##(None)   # anti-clockwise numbering
    # # the inside vertexes loop consecutively numbering in dict container
    # inSideEle = [{1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 5), 5: (5, 6), 6: (6, 7), 7: (7, 8), 8: (8, 1)}]
    # coverThick = 0.06  # the thinck of the cover concrete
    # coreSize = 0.2  # the size of the core concrete fiber elements
    # coverSize = 0.3  # the size of the cover concrete fiber elements
    # outBarD = 0.032  # outside bar diameter(None)
    # outBarDist = 0.2  # outside bar space (None)
    # plotState = True  # plot the fiber or not plot=True or False
    # autoBarMesh = False  # if false provide the barControlNodeDict and barEleDict
    # userBarNodeDict = {1: (2.975, 1.516), 2: (2.475, 1.516), 3: (2.475, 2.016), 4: (-2.475, 2.016), 5: (-2.475, 1.516),
    #                    6: (-2.975, 1.516), 7: (-2.975, -1.516), 8: (-2.475, -1.516), 9: (-2.475, -2.016),
    #                    10: (2.475, -2.016),
    #                    11: (2.475, -1.516), 12: (2.975, -1.516)}  # {1:(y1,z1),2:(y2,z2),...} （None)
    # userBarEleDict = {1: (1, 2, 0.01, 0.2), 2: (2, 3, 0.01, 0.2), 3: (3, 4, 0.01, 0.2), 4: (4, 5, 0.01, 0.2), \
    #                   5: (6, 5, 0.01, 0.2), 6: (5, 2, 0.01, 0.2), 7: (7, 8, 0.01, 0.2), 8: (8, 9, 0.01, 0.2),
    #                   9: (9, 10, 0.01, 0.2),
    #                   10: (10, 11, 0.01, 0.2), 11: (12, 11, 0.01, 0.2), 12: (11, 8, 0.01, 0.2), \
    #                   }  # {1:(nodeI,nodeJ,barD,barDist)}（None)
    # inBarD = 0.032  # inside bar diameter (None)
    # inBarDist = 0.2  # inside bar space (None)
    # fiberDivideInstance.polygonSection(name, outSideNode, outSideEle, coverThick, coreSize, coverSize, outBarD,
    #                                    outBarDist, autoBarMesh, userBarNodeDict, userBarEleDict, inSideNode, inSideEle,
    #                                    inBarD, inBarDist, lineWidth=0.5, markerSize=0.5)
    ####################################################################################################################
    ##########################################--------SectionPropertyCalculate------####################################
    ###########################---sectionProperties Calculate
    # sectionPropertyInstance=SectionPropertyCalculate()
    # A, Iyy, Izz, J, Cy, Cz,outSideNode,outSideEle,inSideNode,inSideEle= sectionPropertyInstance.dxf_sectionproperties\
    #     ("ellipse.dxf","粗实线",scaleFactor=1000,meshSize=0.005)
    # print("A=", A, " Iyy=", Iyy, " Izz=", Izz, " J=", J, " Cy=", Cy, " Cz=",Cz)
    ####################################################################################################################
    ###########################---ground motion process
    # groundMotionProcessInstance=GroundMotionProcess()
    # logP = [0.05 * x for x in range(-40, 27, 1)]
    # Tarray = [10 ** y for y in logP]
    # beta = 0.05
    # dt1 = np.loadtxt("pulseMotions/dt.txt")
    # length1 = np.loadtxt("pulseMotions/length.txt")
    # saPulse = []
    # svPulse = []
    # sdPulse=[]
    # for i1 in range(10):
    #     acc1 = np.loadtxt("pulseMotions/FN/" + str(i1 + 1) + ".txt")
    #     sa1, sv1, sd1 = groundMotionProcessInstance.responseSpectra_Cal(acc1, dt1[i1], Tarray, beta)
    #     saPulse.append(sa1)
    #     svPulse.append(sv1)
    #     sdPulse.append(sd1)
    # #####################################################
    # percentileValue=[0.025,0.975]
    # groundMotionProcessInstance.responseSpectra_Plot(Tarray,saPulse, svPulse,sdPulse,[Tarray[0],Tarray[-1]],
    #                                                  percentileValue,saveFig=True)
    ####################################################################################################################
    ####圆形截面
    # fiberDivideInstance=SectionFiberDivide()
    # name = "circularPier"  # section name
    # outD = 2  # the diameter of the outside circle
    # coverThick = 0.06  # the thinckness of the cover concrete
    # outbarD = 0.032  # outside bar diameter
    # outbarDist = 0.119  # outside bar space
    # coreSize = 0.1  # the size of core concrete fiber
    # coverSize = 0.1  # the size of cover concrete fiber
    # autoBarMesh=True
    # userBarInfoList=[[0.065,outbarD,outbarDist],[0.115,outbarD,outbarDist]]
    # inD=None
    # inBarD=outbarD
    # inBarDist=outbarDist
    # lineWidth=0.5
    # markerSize=2
    # coreFiber, coverFiber, barFiber=fiberDivideInstance.circleSection(name, outD, coverThick, outbarD, outbarDist,
    #     coreSize, coverSize,autoBarMesh)
    # sectMCInstance=SectMCAnalysis(saveFolderName="sectionMomentCurvatureFolder",fiberFolderName="fiberDivideInformation",
    # fiberSectName="circularPier",coverFiber=coverFiber,coreFiber=coreFiber,barFiber=barFiber,barMaterial="HRB400",
    # concreteMaterial="C40",loadDirection="Y",maxMu = 40,numIncr = 200)
    # sectMCInstance.circularSect(hoopType="Spiral",outD=outD,coverThick=coverThick,s=0.1,Dhoop=0.014,fyHoop=400,
    #                             axialLoad=200)
    #####矩形截面
    # fiberDivideInstance = SectionFiberDivide("fiberDivideInformation")
    # sectName = "RectangularPier"
    # outSideNode = {1: (3.5, 3), 2: (1.5, 5), 3: (-1.5, 5), 4: (-3.5, 3), 5: (-3.5, -3), 6: (-1.5, -5), 7: (1.5, -5),
    #                8: (3.5, -3)}
    # outSideEle = {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 5), 5: (5, 6), 6: (6, 7), 7: (7, 8), 8: (8, 1)}
    # coverThick = 0.06  # the thinckness of the cover concrete(m)
    # coreSize = 0.2  # the size of core concrete fiber
    # coverSize = 0.3  # the size of cover concrete fiber
    # outBarDist = 0.2  # bar space(m)
    # outBarD = 0.032  # bar diameter(m)
    # autoBarMesh = True  # if false provide the barControlNodeDict and barEleDict
    # userBarNodeDict = None  # {1:(y1,z1),2:(y2,z2),...} bar line end nodes
    # userBarEleDict = None  # {1:(nodeI,nodeJ,barD,barDist),...}  bar line end nodes number and diameter and distance
    # fiberDivideInstance = SectionFiberDivide()
    # coreFiber, coverFiber, barFiber = fiberDivideInstance.polygonSection(sectName, outSideNode, outSideEle,
    # coverThick, coreSize, coverSize, outBarD,outBarDist, autoBarMesh, lineWidth=0.5,markerSize=0.5)
    # sectMCInstance = SectMCAnalysis(saveFolderName="sectionMomentCurvatureFolder",fiberFolderName="fiberDivideInformation",
    # fiberSectName="RectangularPier", coverFiber=coverFiber,coreFiber=coreFiber, barFiber=barFiber, barMaterial="HRB400",
    #                                 concreteMaterial="C40", loadDirection="X", maxMu=100,numIncr=500)
    # ######参考Prestly或者范院士延性抗震设计专著中的计算方法，对于所求方向配箍率的计算，对于不同约束肢的区间分别计算，并乘以对应的比例，
    # ######最后加权求和，对于有斜肢的可以先投影到对应方向再计算
    # sectMCInstance.rectangularSect(coverThick=coverThick, lx=1.6, ly=3.2, outBarDist=outBarDist, outBarD=outBarD,
    #                                roux=0.005, rouy=0.005, s=0.15, Dhoop=0.012, fyHoop=400, axialLoad=23000,
    #                                otherMoment=0)
    ####################################################################################################################
    ####----SAP2000
    # acc=np.loadtxt("1.txt")
    # dt=0.01
    # groundIns=GroundMotionProcess()
    # vel=groundIns.highPassFilter(acc,dt,0.5)
    # print(len(acc),len(vel))
    ###################################################################################################
    ###---shake table test
    # shakeInstance=ShakeTableTest()
    # scaleRatioDict = shakeInstance.scaleRatio(lengthRatio=0.2, stressRatio=0.3, acceleratioRatio=1)
    # print(scaleRatioDict)
    # times=np.loadtxt("WN_Responses/1-WN-times.txt")
    # acc_1_AX5=np.loadtxt("WN_Responses/1-WN-T1-5-AX.txt")
    # acc_1_AX1 = np.loadtxt("WN_Responses/1-WN-T1-1-AX.txt")
    # acc_1_AX3 = np.loadtxt("WN_Responses/1-WN-T1-3-AX.txt")
    # acc_1_AX4 = np.loadtxt("WN_Responses/1-WN-T1-4-AX.txt")
    # acc_1_GAX1=np.loadtxt("WN_Responses/1-WN-GAX-1.txt")
    # pltHandle=shakeInstance.plotAcc([times,times,times,times],[acc_1_AX5,acc_1_AX4,acc_1_AX3,acc_1_AX1],
    #                                 labelsList=['T1-5-AX','T1-4-AX','T1-3-AX','T1-1-AX'])
    # pltHandle.show()
    # dt=times[1]-times[0]
    # pltHandle=shakeInstance.freResFunc(dt,3,acc_1_AX5,[acc_1_AX1],['1'],10,90)
    # pltHandle.show()
    ####################################################################################################################
    ######---力与位移滞回响应分析
    hystereticInstance=HystereticResponseAnalyses()



















