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
import openseespy.opensees as ops
import time
import shutil
import math
from bidict import bidict
from scipy.stats import norm
from scipy import signal
from scipy.signal import argrelextrema
from scipy import interpolate
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Wedge
from PIL import Image
import comtypes.client
import sys
import datetime
import hashlib
from psutil import net_if_addrs
import requests
import comtypes.client
from SqliteDB import SqliteDB  ##sqlite database to store opensees results
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
        from auxiliaryModules.sectionFiberDivide.sectionFiberMain import circleSection
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
        from auxiliaryModules.sectionFiberDivide.sectionFiberMain import polygonSection

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
class OpenSeesPyX():
    """
    --------------------------------------------------------------------------------------------------------------------
    A class for openSeesPy visualization and structural model analysis (version:0.4.0)
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
    def __init__(self,dataBaseName):
        """
        ----------------------------------------------------------------------------------------------------------------
        Initialize the class
        ------------------------------------------
        Inputs:
            dataBaseName(str)-the name of the database
        ----------------------------------------------------------------------------------------------------------------
        """
        self.nodeSetNameList=[]
        self.eleSetNameList=[]
        self.modalNameList=[]
        self.specialEleTransfList = []
        self.EleLocalCoordSysSetNameList=[]
        self.localTransfNameList=[]
        self.materialNumberDict={}
        self.nodeLinkDict={}
        self.eleLinkDict={}
        self.nodeMassDict={}
        self.dbPath = dataBaseName+".db"
        self.saveInstance = SqliteDB(self.dbPath)
        SqliteDB.initDB(self.dbPath)
        #########----存储模型节点，单元等列表
        self.saveNodeList = []
        self.saveGeomfList=[]
        self.saveEleList=[]
        self.EleLocalCoordSys=[]
        #######----存储纤维截面信息
        self.currentSectTag=None
        self.fiberSectDict={}

    def auxiliary_localZvector(self,eleVector,refVector):
        """
        ----------------------------------------------------------------------------------------------------------------
        get local Z vector that perperticular to two vetors in a plane,one is a vector based on element(from I to J),
        and the other is easily specified,eg. 0,0,1
        -----------------------------
        Inputs:
            eleVector(list)-A element vector made up of I and J nodes, eg.(xj-xi,yj-yi,zj-zi)
            refVector(list)-A reference vector that in the same plane with eleVector, and perperticular to localZvector
        ----------------------------------------------------------------------------------------------------------------
        """
        a = np.array(eleVector)
        b = np.array(refVector)
        c = np.cross(a, b)
        vectorNorm = np.linalg.norm(c)
        localzVector = (c[0] / float(vectorNorm), c[1] / float(vectorNorm), c[2] / float(vectorNorm))
        return localzVector
    def auxiliary_materialReNumber(self,materialName):
        """
        ----------------------------------------------------------------------------------------------------------------
        Register a material name in the domain and return a unique number of the mateiral
        -----------------------------
        Inputs:
            materialName(str)-the name tag of the material
        ----------------------------------------------------------------------------------------------------------------
        """
        if materialName not in self.materialNumberDict.keys():
            self.materialNumberDict[materialName]=len(self.materialNumberDict.keys())+1000000
        return self.materialNumberDict[materialName]

    def auxiliary_nodeReNumber(self,nodeName):
        """
        ----------------------------------------------------------------------------------------------------------------
        Register a node name in the domain and return a unique number of the node
        -----------------------------
        Inputs:
            nodeName(str)-the name tag of the node
        ----------------------------------------------------------------------------------------------------------------
        """
        if nodeName not in self.nodeLinkDict.keys():
            self.nodeLinkDict[nodeName] = len(self.nodeLinkDict.keys()) + 1000000
        return self.nodeLinkDict[nodeName]

    def auxiliary_eleReNumber(self,eleName):
        """
        ----------------------------------------------------------------------------------------------------------------
        Register a element name in the domain and return a unique number of the element
        -----------------------------
        Inputs:
            eleName(str)-the name tag of the element
        ----------------------------------------------------------------------------------------------------------------
        """
        if eleName not in self.eleLinkDict.keys():
            self.eleLinkDict[eleName]=len(self.eleLinkDict.keys())+1000000
        return self.eleLinkDict[eleName]
    def auxiliary_nodeMassGenerate(self,nodeI,nodeJ,eleLength,massUnitLength):
        """
        ----------------------------------------------------------------------------------------------------------------
        node mass generate
        -----------------------------
        Inputs:
        nodeI,nodeJ(int)-girder end nodes
        eleLength(float)-girder element length
        massUnitLength(float)-mass per unit length
        Outputs:
        finally return the lumped node masses with call nodeMassDict
        ----------------------------------------------------------------------------------------------------------------
        """
        totalMass = eleLength * massUnitLength
        if nodeI not in self.nodeMassDict.keys():
            self.nodeMassDict[nodeI] = round(0.5 * totalMass, 6)
        else:
            self.nodeMassDict[nodeI] = round(self.nodeMassDict[nodeI] + 0.5 * totalMass, 6)
        if nodeJ not in self.nodeMassDict.keys():
            self.nodeMassDict[nodeJ] = round(0.5 * totalMass, 6)
        else:
            self.nodeMassDict[nodeJ] = round(self.nodeMassDict[nodeJ] + 0.5 * totalMass, 6)

    def auxiliary_concreteMaterialProperty_JTG2004(self,concreteTag="C40"):
        """
        ----------------------------------------------------------------------------------------------------------------
        ---the concrete material properties based on Chinese JTG standard (JTG D62-2004 C15)---
        concreteMatProDict=["concreteTag":[unitWeight(kN/m3),E,poission,coefficient of thermal expansion,G]]
        ----------------------------------------------------------------------------------------------------------------
        """
        concreteMatProDict = {"C15": [25, 22000000, 0.2, 1.000E-05, 9166667],
                              "C20": [25, 25500000, 0.2, 1.000E-05, 10625000],
                              "C25": [25, 28000000, 0.2, 1.000E-05, 11666667],
                              "C30": [25, 30000000, 0.2, 1.000E-05, 12500000],
                              "C35": [25, 31500000, 0.2, 1.000E-05, 13125000],
                              "C40": [25, 32500000, 0.2, 1.000E-05, 13541667],
                              "C45": [25, 33500000, 0.2, 1.000E-05, 13958333],
                              "C50": [25, 34500000, 0.2, 1.000E-05, 14375000],
                              "C55": [25, 35500000, 0.2, 1.000E-05, 14791667],
                              "C60": [25, 36000000, 0.2, 1.000E-05, 15000000],
                              "C65": [25, 36500000, 0.2, 1.000E-05, 15208333],
                              "C70": [25, 37000000, 0.2, 1.000E-05, 15416667],
                              "C75": [25, 37500000, 0.2, 1.000E-05, 15625000],
                              "C80": [25, 38000000, 0.2, 1.000E-05, 15833333]}
        return concreteMatProDict[concreteTag]

    def auxiliary_rebarMaterialProperty_GB(self,rebarTag="HRB400"):
        """
        ----------------------------------------------------------------------------------------------------------------
        ---the rebar material properties based on Chinese GB standard (GB50010)---
        reBarMatProDict={"rebarTag":[unitWeight,E,poission,coefficient of thermal expansion,G,Fy,Fu]}
        ----------------------------------------------------------------------------------------------------------------
        """
        reBarMatProDict = {"HPB300": [77, 2.100E+08, 0.3, 1.170E-05, 80769231, 300000, 420000],
                           "HRB335": [77, 2.000E+08, 0.3, 1.170E-05, 76923077, 335000, 455000],
                           "HRB400": [77, 2.000E+08, 0.3, 1.170E-05, 76923077, 400000, 540000],
                           "HRB500": [77, 2.000E+08, 0.3, 1.170E-05, 76923077, 500000, 630000]}
        return reBarMatProDict[rebarTag]

    def auxiliary_rebarMaterialProperty_JTG2004(self,rebarTag="R235"):
        """
        ----------------------------------------------------------------------------------------------------------------
        ---the rebar material properties based on Chinese JTG standard (JTG D62-2004)---
        reBarMatProDict={"rebarTag":[unitWeight,E,poission,coefficient of thermal expansion,G,Fy,Fu]}
        ----------------------------------------------------------------------------------------------------------------
        """
        reBarMatProDict = {"R235": [77, 2.100E+08, 0.3, 1.170E-05, 80769231,235000,290000],
                           "HRB335": [77, 2.000E+08, 0.3, 1.170E-05,76923077,335000,420000],
                           "HRB400": [77, 2.000E+08, 0.3, 1.170E-05, 76923077,400000,630000],
                           "KL400": [77, 2.000E+08, 0.3, 1.170E-05, 76923077, 400000, 630000]}
        return reBarMatProDict[rebarTag]

    def auxiliary_steelMaterialProperty_JTG2004(self,steelTag="Q235q"):
        """
        ----------------------------------------------------------------------------------------------------------------
        ---the steel material properties based on Chinese JTG standard (JTG D62-2004)---
        steelMatProDict={"rebarTag":[unitWeight,E,poission,coefficient of thermal expansion,G,Fy,Fu]}
        ----------------------------------------------------------------------------------------------------------------
        """
        steelMatProDict = {"Q235q": [77, 2.100E+08, 0.3, 1.170E-05, 80769231, 235000,400000],
                           "Q345q": [77, 2.100E+08, 0.3, 1.170E-05, 80769231, 345000,510000],
                           "Q370q": [77, 2.100E+08, 0.3, 1.170E-05, 80769231, 370000, 510000],
                           "Q420q": [77, 2.100E+08, 0.3, 1.170E-05, 80769231, 420000, 540000],
                           "Q460q": [77, 2.100E+08, 0.3, 1.170E-05, 80769231, 460000, 570000],
                           "Q500q": [77, 2.100E+08, 0.3, 1.170E-05, 80769231, 500000, 600000],
                           "Q550q": [77, 2.100E+08, 0.3, 1.170E-05, 80769231, 550000, 660000],
                           "Q620q": [77, 2.100E+08, 0.3, 1.170E-05, 80769231, 620000, 720000],
                           "Q690q": [77, 2.100E+08, 0.3, 1.170E-05, 80769231, 690000, 770000]}
        return steelMatProDict[steelTag]

    def auxiliary_tendonMaterialProperty_JTG2004(self,tendonTag="fpk1470"):
        """
        ----------------------------------------------------------------------------------------------------------------
        ---the tendon material properties based on Chinese JTG standard (JTG D62-2004)---
        tendonMatProDict={"tendonTag":[unitWeight,E,poission,coefficient of thermal expansion,G,Fy,Fu]}
        ----------------------------------------------------------------------------------------------------------------
        """
        tendonMatProDict = {"fpk1470": [77, 1.95E+08, 0.3, 1.170E-05,75000000,1470000,1690000],
                            "fpk1570": [77, 1.95E+08, 0.3, 1.170E-05, 75000000,1570000,1800000],
                            "fpk1720": [77, 1.95E+08, 0.3, 1.170E-05, 75000000,1720000,1980000],
                            "fpk1860": [77, 1.95E+08, 0.3, 1.170E-05, 75000000,1860000,2140000]}
        return tendonMatProDict[tendonTag]
    ####################################################################################################################
    def auxiliary_fiberSectionPlot(self,sectTag, fillFlag=1):
        """
        ----------------------------------------------------------------------------------------------------------------
        Used for plotting fiber sections,the commands are not added in the OpenSeesPy
        ----------------------------------------------------------------------------------------------------------------
        1. Inspired by plotSection matlab function written by D. Vamvatsikos available at
           http://users.ntua.gr/divamva/software.html (plotSection.zip)
        2. Inspired by the module opsvis developed by sewkokot available at
           https://github.com/sewkokot/opsvis
        ----------------------------------------------------------------------------------------------------------------
        Inputs:
            sectTag(int)-the tag of the fiber section to be plotted
            fillFlag (int): 1 - filled fibers with color specified in matcolor
                            0 - no color, only the outline of fibers
        Output:
            plt-plot handle
        ----------------------------------------------------------------------------------------------------------------
        ###---Example:
                pltHandle=opsX.auxiliary_fiberSectionPlot(sectTag=110001)
                pltHandle.show()
        ----------------------------------------------------------------------------------------------------------------
        """
        fiberSectList=self.fiberSectDict[sectTag]
        fig, ax = plt.subplots()
        ax.set_xlabel('y')
        ax.set_ylabel('z')
        ax.grid(False)
        matTag=list(set([item[2] for item in fiberSectList][1:]))
        color_names = ["silver","green","orange","brown", "gray", "red", "yellow", "cyan", "magenta", "blue",
                        "purple", "turquoise",  "gold", "navy", "olive", "maroon", "beige"]
        matColorDict={matTag[i1]:color_names[i1] for i1 in range(len(matTag))}
        for item in fiberSectList:
            if item[0] == 'layer':
                matTag = item[2]
                if item[1] == 'straight':
                    n_bars = item[3]
                    As = item[4]
                    Iy, Iz, Jy, Jz = item[5], item[6], item[7], item[8]
                    r = np.sqrt(As / np.pi)
                    Y = np.linspace(Iy, Jy, n_bars)
                    Z = np.linspace(Iz, Jz, n_bars)
                    for zi, yi in zip(Z, Y):
                        bar = Circle((yi,zi), r, ec='k', fc='k', zorder=10)
                        ax.add_patch(bar)
                if item[1] == 'circ':
                    n_bars, As = item[3], item[4]
                    yC, zC, arc_radius = item[5], item[6], item[7]
                    if len(item) > 8:
                        a0_deg, a1_deg = item[8], item[9]
                        if ((a1_deg - a0_deg) >= 360. and n_bars > 0):
                            a1_deg = a0_deg + 360. - 360. / n_bars
                    else:
                        a0_deg, a1_deg = 0., 360. - 360. / n_bars
                    a0_rad, a1_rad = np.pi * a0_deg / 180., np.pi * a1_deg / 180.
                    r_bar = np.sqrt(As / np.pi)
                    thetas = np.linspace(a0_rad, a1_rad, n_bars)
                    Y = yC + arc_radius * np.cos(thetas)
                    Z = zC + arc_radius * np.sin(thetas)
                    for zi, yi in zip(Z, Y):
                        bar = Circle((yi,zi), r_bar, ec='k', fc='k', zorder=10)
                        ax.add_patch(bar)
            if (item[0] == 'patch' and (item[1] == 'quad' or item[1] == 'quadr' or
                                        item[1] == 'rect')):
                matTag, nIJ, nJK = item[2], item[3], item[4]

                if item[1] == 'quad' or item[1] == 'quadr':
                    Iy, Iz, Jy, Jz = item[5], item[6], item[7], item[8]
                    Ky, Kz, Ly, Lz = item[9], item[10], item[11], item[12]

                if item[1] == 'rect':
                    Iy, Iz, Ky, Kz = item[5], item[6], item[7], item[8]
                    Jy, Jz, Ly, Lz = Ky, Iz, Iy, Kz
                # check for convexity (vector products)
                outIJxIK = (Jy - Iy) * (Kz - Iz) - (Ky - Iy) * (Jz - Iz)
                outIKxIL = (Ky - Iy) * (Lz - Iz) - (Ly - Iy) * (Kz - Iz)
                # check if I, J, L points are colinear
                outIJxIL = (Jy - Iy) * (Lz - Iz) - (Ly - Iy) * (Jz - Iz)
                # outJKxJL = (Ky-Jy)*(Lz-Jz) - (Ly-Jy)*(Kz-Jz)
                if outIJxIK <= 0 or outIKxIL <= 0 or outIJxIL <= 0:
                    print('Warning! Patch quad is non-convex or counter-clockwise defined or has at least 3 '
                          'colinear points in line')  # noqa: E501

                IJz, IJy = np.linspace(Iz, Jz, nIJ + 1), np.linspace(Iy, Jy, nIJ + 1)
                JKz, JKy = np.linspace(Jz, Kz, nJK + 1), np.linspace(Jy, Ky, nJK + 1)
                LKz, LKy = np.linspace(Lz, Kz, nIJ + 1), np.linspace(Ly, Ky, nIJ + 1)
                ILz, ILy = np.linspace(Iz, Lz, nJK + 1), np.linspace(Iy, Ly, nJK + 1)

                if fillFlag:
                    Z = np.zeros((nIJ + 1, nJK + 1))
                    Y = np.zeros((nIJ + 1, nJK + 1))
                    for j in range(nIJ + 1):
                        Z[j, :] = np.linspace(IJz[j], LKz[j], nJK + 1)
                        Y[j, :] = np.linspace(IJy[j], LKy[j], nJK + 1)
                    for j in range(nIJ):
                        for k in range(nJK):
                            zy = np.array([[Y[j, k],Z[j, k]],
                                           [Y[j, k + 1],Z[j, k + 1]],
                                           [Y[j + 1, k + 1],Z[j + 1, k + 1]],
                                           [Y[j + 1, k],Z[j + 1, k]]])
                            poly = Polygon(zy, closed=True, ec='k', fc=matColorDict[matTag])
                            ax.add_patch(poly)
                else:
                    # horizontal lines
                    for az, bz, ay, by in zip(IJz, LKz, IJy, LKy):
                        plt.plot([ay, by],[az, bz], 'b-', zorder=1)
                    # vertical lines
                    for az, bz, ay, by in zip(JKz, ILz, JKy, ILy):
                        plt.plot( [ay, by],[az, bz], 'b-', zorder=1)
            if item[0] == 'patch' and item[1] == 'circ':
                matTag, nc, nr = item[2], item[3], item[4]
                yC, zC, ri, re = item[5], item[6], item[7], item[8]
                a0, a1 = item[9], item[10]
                dr = (re - ri) / nr
                dth = (a1 - a0) / nc
                for j in range(nr):
                    rj = ri + j * dr
                    rj1 = rj + dr
                    for i in range(nc):
                        thi = a0 + i * dth
                        thi1 = thi + dth
                        wedge = Wedge((yC,zC), rj1, thi, thi1, width=dr, ec='k',
                                      lw=1, fc=matColorDict[matTag])
                        ax.add_patch(wedge)
                ax.axis('equal')
        plt.axis('equal')
        plt.title(f"Section fibers-{sectTag}")
        return plt
    ####################################################################################################################
    def auxiliary_writeModelInformationToDB(self):
        """
        When call this method all nodes,elements..., that need to be visualized by SAPBridge will be written to the
        result database
        """
        nodeDict={}
        for eachItem in self.saveNodeList:
            if eachItem[1] not in nodeDict.keys():
                nodeDict[eachItem[1]]=[]
                nodeDict[eachItem[1]].append(eachItem[0])
            else:
                nodeDict[eachItem[1]].append(eachItem[0])
        for eachKey in nodeDict.keys():
            self.saveInstance.saveNodes(nodesSaveName=eachKey, nodeList=nodeDict[eachKey])
        geomDict={}
        for eachItem in self.saveGeomfList:
            if eachItem[1] not in geomDict.keys():
                geomDict[eachItem[1]] = []
                geomDict[eachItem[1]].append(eachItem[0])
            else:
                geomDict[eachItem[1]].append(eachItem[0])
        for eachKey in geomDict.keys():
            self.saveInstance.saveGeomTransf(geomTransfSaveName=eachKey,geomfList=geomDict[eachKey])
        eleDict={}
        for eachItem in self.saveEleList:
            if eachItem[1] not in eleDict.keys():
                eleDict[eachItem[1]] = []
                eleDict[eachItem[1]].append(eachItem[0])
            else:
                eleDict[eachItem[1]].append(eachItem[0])
        for eachKey in eleDict.keys():
            self.saveInstance.saveEles(elesSaveName=eachKey, elesList=eleDict[eachKey])
        eleLocCoordDict={}
        for eachItem in self.EleLocalCoordSys:
            if eachItem[1] not in eleLocCoordDict.keys():
                eleLocCoordDict[eachItem[1]] = []
                eleLocCoordDict[eachItem[1]].append(eachItem[0])
            else:
                eleLocCoordDict[eachItem[1]].append(eachItem[0])
        for eachKey in eleLocCoordDict.keys():
            self.saveInstance.saveEleLocalCoordSys(SaveName=eachKey,EleLocalCoordSys=eleLocCoordDict[eachKey])

    def node(self,*args):
        """
        ----------------------------------------------------------------------------------------------------------------
        node(nodeTag, *crds, '-ndf', ndf, '-mass', *mass, '-disp', *disp, '-vel', *vel, '-accel', *accel)
        Create a OpenSees node.
        nodeTag (int)	node tag.
        crds (list (float))	nodal coordinates.
        ndf (float)	nodal ndf. (optional)
        mass (list (float))	nodal mass. (optional)
        vel (list (float))	nodal velocities. (optional)
        accel (list (float))	nodal accelerations. (optional)
        ----------------------------------------------------------------------------------------------------------------
        """
        eval(f"ops.node{args}") ###---create node in OpenSeesPy
        nodeArgsList=list(args)
        nodeTagValue=nodeArgsList[0]
        coords = ops.nodeCoord(nodeTagValue)
        if len(coords)==1:
            coords=coords+[0.0,0.0]
        elif len(coords)==2:
            coords=coords+[0.0]
        else:
            pass
        tipValue = 'node_node'
        self.saveNodeList.append([[nodeTagValue]+coords,tipValue])
        self.nodeSetNameList.append(tipValue)


    def geomTransf(self,*args):
        """
        ----------------------------------------------------------------------------------------------------------------
        geomTransf(transfType, transfTag, *transfArgs)
        ----------------------------------------------
        The geometric-transformation command is used to construct a coordinate-transformation (CrdTransf) object,
        which transforms beam element stiffness and resisting force from the basic system to the global-coordinate
        system. The command has at least one argument, the transformation type.
        ----------------------------------------------
        transfType (str)	geomTransf type
        transfTag (int)	geomTransf tag.
        transfArgs (list)	a list of geomTransf arguments, must be preceded with *.
        ----------------------------------------------
        The following contain information about available transfType:
        Linear Transformation
        PDelta Transformation
        Corotational Transformation
        ----------------------------------------------
        ----------------------------------------------------------------------------------------------------------------
        """
        eval(f"ops.geomTransf{args}")  ###---create node in OpenSeesPy
        geomTransfArgsList = list(args)
        geomTransfType = geomTransfArgsList[0]
        geomTransfTag = geomTransfArgsList[1]
        tipsString =geomTransfType
        geomVect=[0.0,0.0,0.0]
        if geomTransfType in ["Linear","linear"]:
            if "-jntOffset" in geomTransfArgsList:
                indexValue=geomTransfArgsList.index("-jntOffset")
                if indexValue-1<=1:
                    geomVect=[0,0,1]
                else:
                    for i1 in range(indexValue-2):
                        geomVect[i1]=geomTransfArgsList[2+i1]
            else:
                totalNum=len(geomTransfArgsList)
                if totalNum==2:
                    geomVect=[0,0,1]
                else:
                    for i1 in range(totalNum-2):
                        geomVect[i1]=geomTransfArgsList[2+i1]
        elif geomTransfType in ["PDelta","pDelta"]:
            if "-jntOffset" in geomTransfArgsList:
                indexValue=geomTransfArgsList.index("-jntOffset")
                if indexValue-1<=1:
                    geomVect=[0,0,1]
                else:
                    for i1 in range(indexValue-2):
                        geomVect[i1]=geomTransfArgsList[2+i1]
            else:
                totalNum=len(geomTransfArgsList)
                if totalNum==2:
                    geomVect=[0,0,1]
                else:
                    for i1 in range(totalNum-2):
                        geomVect[i1]=geomTransfArgsList[2+i1]
        else: ###---Corotational
            if "-jntOffset" in geomTransfArgsList:
                indexValue = geomTransfArgsList.index("-jntOffset")
                if indexValue - 1 <= 1:
                    geomVect = [0, 0, 1]
            else:
                totalNum = len(geomTransfArgsList)
                if totalNum == 2:
                    geomVect = [0, 0, 1]
                else:
                    for i1 in range(totalNum - 2):
                        geomVect[i1] = geomTransfArgsList[2 + i1]
        saveGeomfList = []
        self.saveGeomfList.append([[geomTransfTag, geomVect[0],geomVect[1],geomVect[2]],tipsString + "_geomTransf"])
        self.localTransfNameList.append(tipsString + "_geomTransf")


    def equalDOF(self,*args):
        """
        ----------------------------------------------------------------------------------------------------------------
        equalDOF(rNodeTag, cNodeTag, *dofs)
        ----------------------------------------------
        Create a multi-point constraint between nodes.
        ----------------------------------------------
        rNodeTag (int)	integer tag identifying the retained, or master node.
        cNodeTag (int)	integer tag identifying the constrained, or slave node.
        dofs (list (int))	nodal degrees-of-freedom that are constrained at the cNode to be the same as those at
        the rNode Valid range is from 1 through ndf, the number of nodal degrees-of-freedom.
        ----------------------------------------------
        ----------------------------------------------------------------------------------------------------------------
        """
        eval(f"ops.equalDOF{args}")
        equalDOFArgsList = list(args)
        nodeI,nodeJ=equalDOFArgsList[0],equalDOFArgsList[1]
        nodeICoords = ops.nodeCoord(nodeI)
        nodeJCoords = ops.nodeCoord(nodeJ)
        equalLength=np.sqrt((nodeICoords[0]-nodeJCoords[0])**2+(nodeICoords[1]-nodeJCoords[1])**2+
                            (nodeICoords[2]-nodeJCoords[2])**2)
        tipValue = 'equalDOF'
        if equalLength<=1.0e-10:
            pass
        else:
            self.eleSetNameList.append(tipValue + "_ele")
            self.saveEleList.append([[0,nodeI,nodeJ],tipValue + "_ele"])



    def element(self,*args):
        """
        ----------------------------------------------------------------------------------------------------------------
        element(eleType, eleTag, *eleNodes, *eleArgs)
        Create a OpenSees element.
        eleType (str)	element type
        eleTag (int)	element tag.
        eleNodes (list (int))	a list of element nodes, must be preceded with *.
        eleArgs (list)	a list of element arguments, must be preceded with *.
        ----------------------------------------------------------------------------------------------------------------
        """
        eval(f"ops.element{args}")  ###---create node in OpenSeesPy
        argsList=list(args)
        eleType=argsList[0]
        tipValue =eleType
        eleTag=argsList[1]
        if eleType in ['elasticBeamColumn','ElasticBeamColumn']:
            returnValue=next(((index, item) for index, item in enumerate(argsList[1:]) if isinstance(item, str)), None)
            if returnValue==None:
                transTag=argsList[-1]
            else:
                transTag=argsList[returnValue[0]]
            eleNodes=ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['realEle',eleNodes[0],eleNodes[1],transTag],tipValue + "_eleLocCordSys"])
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
        ################################################################################################################
        elif eleType in ['Truss','truss','TrussSection','trussSection','corotTruss','CorotTruss','corotTrussSection',
                         'CorotTrussSection']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['twoNodeLink','TwoNodeLink']:
            eleNodes = ops.eleNodes(eleTag)
            localXVector=[1,0,0]
            localYVector=[0,1,0]
            localZVector=[0,0,1]
            nodeICoords = ops.nodeCoord(eleNodes[0])
            nodeJCoords = ops.nodeCoord(eleNodes[1])
            equalLength = np.sqrt((nodeICoords[0] - nodeJCoords[0]) ** 2 + (nodeICoords[1] - nodeJCoords[1]) ** 2 +
                                  (nodeICoords[2] - nodeJCoords[2]) ** 2)
            if equalLength<1.0e-10:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            else:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localXVector=[nodeJCoords[0]-nodeICoords[0],nodeJCoords[1]-nodeICoords[1],
                            nodeJCoords[2]-nodeICoords[2]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localXVector = [nodeJCoords[0] - nodeICoords[0], nodeJCoords[1] - nodeICoords[1],
                                            nodeJCoords[2] - nodeICoords[2]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['specialEle', eleNodes[0], eleNodes[1], localXVector, localYVector],
                                          tipValue + "_eleLocCordSys"])
        ################################################################################################################
        elif eleType in ['Tri31','tri31']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['ShellNLDKGQ','shellNLDKGQ']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['quad','Quad']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['ShellMITC4','shellMITC4']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['ShellDKGQ', 'shellDKGQ']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['ShellDKGT', 'shellDKGT']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['ShellNLDKGQ', 'sellNLDKGQ']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['ShellNLDKGT', 'shellNLDKGT']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['ShellNL', 'shellNL']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['bbarQuad', 'BbarQuad']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['enhancedQuad', 'EnhancedQuad']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['SSPquad','sSPquad']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['MVLEM_3D','mVLEM_3D']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['SFI_MVLEM_3D', 'sFI_MVLEM_3D']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['quadUP','QuadUP']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['bbarQuadUP','BbarQuadUP']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        # elif eleType in ['9_4_QuadUP']:
        #     tipValue="number_"+tipValue
        #     eleNodes = ops.eleNodes(eleTag)
        #     node1,node2,node3,node4=eleNodes[:4]
        #     eleNodes=[node1,node2,node3,node4]
        #     saveList = []
        #     saveList.append([eleTag] + eleNodes + ["2D"]) ####---去除最中心节点
        #     self.eleSetNameList.append(tipValue + "_ele")
        #     self.saveInstance.saveEles(elesSaveName=tipValue + "_ele", elesList=saveList)
        ################################################################################################################
        elif eleType in ['SSPquadUP','sSPquadUP']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['SimpleContact2D','simpleContact2D']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['SimpleContact3D','simpleContact3D']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['BeamContact2D','beamContact2D']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['BeamContact3D','beamContact3D']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['BeamEndContact3D','beamEndContact3D']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['VS3D4','vS3D4']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['AV3D4','aV3D4']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['SurfaceLoad','surfaceLoad']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["2D"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################



        ################################################################################################################
        elif eleType in ['FourNodeTetrahedron','fourNodeTetrahedron']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["Tetrahedron"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['stdBrick','StdBrick']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["Brick"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['bbarBrick','BbarBrick']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["Brick"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['bbarBrick','BbarBrick']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["Brick"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['SSPbrick','sSPbrick']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["Brick"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['brickUP','BrickUP']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["Brick"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['bbarBrickUP','BbarBrickUP']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["Brick"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['SSPbrickUP','sSPbrickUP']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["Brick"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['AC3D8','aC3D8']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["Brick"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['ASI3D8','aSI3D8']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes + ["Brick"],tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################


        ################################################################################################################
        elif eleType in ['zeroLength', 'ZeroLength']:
            eleNodes = ops.eleNodes(eleTag)
            localXVector = [1, 0, 0]
            localYVector = [0, 1, 0]
            localZVector = [0, 0, 1]
            if "-orient" in argsList:
                orientIndex = argsList.index('-orient')
                localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['specialEle', eleNodes[0], eleNodes[1], localXVector, localYVector],
                                          tipValue + "_eleLocCordSys"])
        ################################################################################################################
        elif eleType in ['zeroLengthND', 'ZeroLengthND']:
            eleNodes = ops.eleNodes(eleTag)
            localXVector = [1, 0, 0]
            localYVector = [0, 1, 0]
            localZVector = [0, 0, 1]
            if "-orient" in argsList:
                orientIndex = argsList.index('-orient')
                localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['specialEle', eleNodes[0], eleNodes[1], localXVector, localYVector],
                                          tipValue + "_eleLocCordSys"])
        ################################################################################################################
        elif eleType in ['zeroLengthSection', 'ZeroLengthSection']:
            eleNodes = ops.eleNodes(eleTag)
            localXVector = [1, 0, 0]
            localYVector = [0, 1, 0]
            localZVector = [0, 0, 1]
            if "-orient" in argsList:
                orientIndex = argsList.index('-orient')
                localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['specialEle', eleNodes[0], eleNodes[1], localXVector, localYVector],
                                          tipValue + "_eleLocCordSys"])
        ################################################################################################################
        elif eleType in ['CoupledZeroLength', 'coupledZeroLength']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['zeroLengthContact2D', 'ZeroLengthContact2D','zeroLengthContact3D','ZeroLengthContact3D']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['zeroLengthInterface2D', 'ZeroLengthInterface2D']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['zeroLengthImpact3D', 'ZeroLengthImpact3D']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        ################################################################################################################
        elif eleType in ['ModElasticBeam2d','modElasticBeam2d']:
            returnValue = next(((index, item) for index, item in enumerate(argsList[1:]) if isinstance(item, str)),None)
            if returnValue == None:
                transTag = argsList[-1]
            else:
                transTag = argsList[returnValue[0]]
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['realEle', eleNodes[0], eleNodes[1], transTag],tipValue + "_eleLocCordSys"])
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
        ################################################################################################################
        elif eleType in ['ElasticTimoshenkoBeam', 'elasticTimoshenkoBeam']:
            returnValue = next(((index, item) for index, item in enumerate(argsList[1:]) if isinstance(item, str)),None)
            if returnValue == None:
                transTag = argsList[-1]
            else:
                transTag = argsList[returnValue[0]]
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['realEle', eleNodes[0], eleNodes[1], transTag],
                                          tipValue + "_eleLocCordSys"])
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
        ################################################################################################################
        elif eleType in ['dispBeamColumn', 'DispBeamColumn']:
            transTag=argsList[4]
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['realEle', eleNodes[0], eleNodes[1], transTag],
                                          tipValue + "_eleLocCordSys"])
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
        ################################################################################################################
        elif eleType in ['forceBeamColumn', 'ForceBeamColumn']:
            transTag=argsList[4]
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['realEle', eleNodes[0], eleNodes[1], transTag],
                                          tipValue + "_eleLocCordSys"])
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
        ################################################################################################################
        elif eleType in ['nonlinearBeamColumn', 'NonlinearBeamColumn']:
            returnValue = next(((index, item) for index, item in enumerate(argsList[1:]) if isinstance(item, str)),None)
            if returnValue == None:
                transTag = argsList[-1]
            else:
                transTag = argsList[returnValue[0]]
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['realEle', eleNodes[0], eleNodes[1], transTag],
                                          tipValue + "_eleLocCordSys"])
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
        ################################################################################################################
        elif eleType in ['dispBeamColumnInt', 'DispBeamColumnInt']:
            transTag=argsList[6]
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['realEle', eleNodes[0], eleNodes[1], transTag],
                                          tipValue + "_eleLocCordSys"])
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
        ################################################################################################################
        elif eleType in ['MVLEM', 'mVLEM']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['SFI_MVLEM', 'sFI_MVLEM']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['beamColumnJoint','BeamColumnJoint']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['ElasticTubularJoint','elasticTubularJoint']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['Joint2D','joint2D']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['Joint2D','joint2D']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['CatenaryCable','catenaryCable']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################



        ################################################################################################################
        elif eleType in ['elastomericBearingPlasticity','ElastomericBearingPlasticity']:
            eleNodes = ops.eleNodes(eleTag)
            localXVector=[1,0,0]
            localYVector=[0,1,0]
            localZVector=[0,0,1]
            nodeICoords = ops.nodeCoord(eleNodes[0])
            nodeJCoords = ops.nodeCoord(eleNodes[1])
            equalLength = np.sqrt((nodeICoords[0] - nodeJCoords[0]) ** 2 + (nodeICoords[1] - nodeJCoords[1]) ** 2 +
                                  (nodeICoords[2] - nodeJCoords[2]) ** 2)
            if equalLength<1.0e-10:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            else:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localXVector=[nodeJCoords[0]-nodeICoords[0],nodeJCoords[1]-nodeICoords[1],
                            nodeJCoords[2]-nodeICoords[2]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localXVector = [nodeJCoords[0] - nodeICoords[0], nodeJCoords[1] - nodeICoords[1],
                                            nodeJCoords[2] - nodeICoords[2]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]

            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['specialEle', eleNodes[0], eleNodes[1], localXVector, localYVector],
                                          tipValue + "_eleLocCordSys"])
        ################################################################################################################
        elif eleType in ['ElastomericBearingBoucWen','elastomericBearingBoucWen']:
            eleNodes = ops.eleNodes(eleTag)
            localXVector=[1,0,0]
            localYVector=[0,1,0]
            localZVector=[0,0,1]
            nodeICoords = ops.nodeCoord(eleNodes[0])
            nodeJCoords = ops.nodeCoord(eleNodes[1])
            equalLength = np.sqrt((nodeICoords[0] - nodeJCoords[0]) ** 2 + (nodeICoords[1] - nodeJCoords[1]) ** 2 +
                                  (nodeICoords[2] - nodeJCoords[2]) ** 2)
            if equalLength<1.0e-10:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            else:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localXVector=[nodeJCoords[0]-nodeICoords[0],nodeJCoords[1]-nodeICoords[1],
                            nodeJCoords[2]-nodeICoords[2]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localXVector = [nodeJCoords[0] - nodeICoords[0], nodeJCoords[1] - nodeICoords[1],
                                            nodeJCoords[2] - nodeICoords[2]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['specialEle', eleNodes[0], eleNodes[1], localXVector, localYVector],
                                          tipValue + "_eleLocCordSys"])
        ################################################################################################################
        elif eleType in ['flatSliderBearing','FlatSliderBearing']:
            eleNodes = ops.eleNodes(eleTag)
            localXVector=[1,0,0]
            localYVector=[0,1,0]
            localZVector=[0,0,1]
            nodeICoords = ops.nodeCoord(eleNodes[0])
            nodeJCoords = ops.nodeCoord(eleNodes[1])
            equalLength = np.sqrt((nodeICoords[0] - nodeJCoords[0]) ** 2 + (nodeICoords[1] - nodeJCoords[1]) ** 2 +
                                  (nodeICoords[2] - nodeJCoords[2]) ** 2)
            if equalLength<1.0e-10:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            else:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localXVector=[nodeJCoords[0]-nodeICoords[0],nodeJCoords[1]-nodeICoords[1],
                            nodeJCoords[2]-nodeICoords[2]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localXVector = [nodeJCoords[0] - nodeICoords[0], nodeJCoords[1] - nodeICoords[1],
                                            nodeJCoords[2] - nodeICoords[2]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['specialEle', eleNodes[0], eleNodes[1], localXVector, localYVector],
                                          tipValue + "_eleLocCordSys"])
        ################################################################################################################
        elif eleType in ['singleFPBearing','SingleFPBearing']:
            eleNodes = ops.eleNodes(eleTag)
            localXVector=[1,0,0]
            localYVector=[0,1,0]
            localZVector=[0,0,1]
            nodeICoords = ops.nodeCoord(eleNodes[0])
            nodeJCoords = ops.nodeCoord(eleNodes[1])
            equalLength = np.sqrt((nodeICoords[0] - nodeJCoords[0]) ** 2 + (nodeICoords[1] - nodeJCoords[1]) ** 2 +
                                  (nodeICoords[2] - nodeJCoords[2]) ** 2)
            if equalLength<1.0e-10:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            else:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localXVector=[nodeJCoords[0]-nodeICoords[0],nodeJCoords[1]-nodeICoords[1],
                            nodeJCoords[2]-nodeICoords[2]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localXVector = [nodeJCoords[0] - nodeICoords[0], nodeJCoords[1] - nodeICoords[1],
                                            nodeJCoords[2] - nodeICoords[2]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['specialEle', eleNodes[0], eleNodes[1], localXVector, localYVector],
                                          tipValue + "_eleLocCordSys"])
        ################################################################################################################
        elif eleType in ['TFP','tFP']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['TripleFrictionPendulum','tripleFrictionPendulum']:
            eleNodes = ops.eleNodes(eleTag)
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.eleSetNameList.append(tipValue + "_ele")
        ################################################################################################################
        elif eleType in ['multipleShearSpring','MultipleShearSpring']:
            eleNodes = ops.eleNodes(eleTag)
            localXVector=[1,0,0]
            localYVector=[0,1,0]
            localZVector=[0,0,1]
            nodeICoords = ops.nodeCoord(eleNodes[0])
            nodeJCoords = ops.nodeCoord(eleNodes[1])
            equalLength = np.sqrt((nodeICoords[0] - nodeJCoords[0]) ** 2 + (nodeICoords[1] - nodeJCoords[1]) ** 2 +
                                  (nodeICoords[2] - nodeJCoords[2]) ** 2)
            if equalLength<1.0e-10:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            else:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localXVector=[nodeJCoords[0]-nodeICoords[0],nodeJCoords[1]-nodeICoords[1],
                            nodeJCoords[2]-nodeICoords[2]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localXVector = [nodeJCoords[0] - nodeICoords[0], nodeJCoords[1] - nodeICoords[1],
                                            nodeJCoords[2] - nodeICoords[2]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['specialEle', eleNodes[0], eleNodes[1], localXVector, localYVector],
                                          tipValue + "_eleLocCordSys"])
        ################################################################################################################
        elif eleType in ['KikuchiBearing','kikuchiBearing']:
            eleNodes = ops.eleNodes(eleTag)
            localXVector=[1,0,0]
            localYVector=[0,1,0]
            localZVector=[0,0,1]
            nodeICoords = ops.nodeCoord(eleNodes[0])
            nodeJCoords = ops.nodeCoord(eleNodes[1])
            equalLength = np.sqrt((nodeICoords[0] - nodeJCoords[0]) ** 2 + (nodeICoords[1] - nodeJCoords[1]) ** 2 +
                                  (nodeICoords[2] - nodeJCoords[2]) ** 2)
            if equalLength<1.0e-10:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            else:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localXVector=[nodeJCoords[0]-nodeICoords[0],nodeJCoords[1]-nodeICoords[1],
                            nodeJCoords[2]-nodeICoords[2]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localXVector = [nodeJCoords[0] - nodeICoords[0], nodeJCoords[1] - nodeICoords[1],
                                            nodeJCoords[2] - nodeICoords[2]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['specialEle', eleNodes[0], eleNodes[1], localXVector, localYVector],
                                          tipValue + "_eleLocCordSys"])
        ################################################################################################################
        elif eleType in ['YamamotoBiaxialHDR','yamamotoBiaxialHDR']:
            eleNodes = ops.eleNodes(eleTag)
            localXVector=[1,0,0]
            localYVector=[0,1,0]
            localZVector=[0,0,1]
            nodeICoords = ops.nodeCoord(eleNodes[0])
            nodeJCoords = ops.nodeCoord(eleNodes[1])
            equalLength = np.sqrt((nodeICoords[0] - nodeJCoords[0]) ** 2 + (nodeICoords[1] - nodeJCoords[1]) ** 2 +
                                  (nodeICoords[2] - nodeJCoords[2]) ** 2)
            if equalLength<1.0e-10:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            else:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localXVector=[nodeJCoords[0]-nodeICoords[0],nodeJCoords[1]-nodeICoords[1],
                            nodeJCoords[2]-nodeICoords[2]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localXVector = [nodeJCoords[0] - nodeICoords[0], nodeJCoords[1] - nodeICoords[1],
                                            nodeJCoords[2] - nodeICoords[2]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['specialEle', eleNodes[0], eleNodes[1], localXVector, localYVector],
                                          tipValue + "_eleLocCordSys"])
        ################################################################################################################
        elif eleType in ['ElastomericX','elastomericX']:
            eleNodes = ops.eleNodes(eleTag)
            localXVector=[1,0,0]
            localYVector=[0,1,0]
            localZVector=[0,0,1]
            nodeICoords = ops.nodeCoord(eleNodes[0])
            nodeJCoords = ops.nodeCoord(eleNodes[1])
            equalLength = np.sqrt((nodeICoords[0] - nodeJCoords[0]) ** 2 + (nodeICoords[1] - nodeJCoords[1]) ** 2 +
                                  (nodeICoords[2] - nodeJCoords[2]) ** 2)
            if equalLength<1.0e-10:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            else:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localXVector=[nodeJCoords[0]-nodeICoords[0],nodeJCoords[1]-nodeICoords[1],
                            nodeJCoords[2]-nodeICoords[2]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localXVector = [nodeJCoords[0] - nodeICoords[0], nodeJCoords[1] - nodeICoords[1],
                                            nodeJCoords[2] - nodeICoords[2]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['specialEle', eleNodes[0], eleNodes[1], localXVector, localYVector],
                                          tipValue + "_eleLocCordSys"])
        ################################################################################################################
        elif eleType in ['LeadRubberX','leadRubberX']:
            eleNodes = ops.eleNodes(eleTag)
            localXVector=[1,0,0]
            localYVector=[0,1,0]
            localZVector=[0,0,1]
            nodeICoords = ops.nodeCoord(eleNodes[0])
            nodeJCoords = ops.nodeCoord(eleNodes[1])
            equalLength = np.sqrt((nodeICoords[0] - nodeJCoords[0]) ** 2 + (nodeICoords[1] - nodeJCoords[1]) ** 2 +
                                  (nodeICoords[2] - nodeJCoords[2]) ** 2)
            if equalLength<1.0e-10:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            else:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localXVector=[nodeJCoords[0]-nodeICoords[0],nodeJCoords[1]-nodeICoords[1],
                            nodeJCoords[2]-nodeICoords[2]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localXVector = [nodeJCoords[0] - nodeICoords[0], nodeJCoords[1] - nodeICoords[1],
                                            nodeJCoords[2] - nodeICoords[2]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['specialEle', eleNodes[0], eleNodes[1], localXVector, localYVector],
                                          tipValue + "_eleLocCordSys"])
        ################################################################################################################
        elif eleType in ['HDR','hDR']:
            eleNodes = ops.eleNodes(eleTag)
            localXVector=[1,0,0]
            localYVector=[0,1,0]
            localZVector=[0,0,1]
            nodeICoords = ops.nodeCoord(eleNodes[0])
            nodeJCoords = ops.nodeCoord(eleNodes[1])
            equalLength = np.sqrt((nodeICoords[0] - nodeJCoords[0]) ** 2 + (nodeICoords[1] - nodeJCoords[1]) ** 2 +
                                  (nodeICoords[2] - nodeJCoords[2]) ** 2)
            if equalLength<1.0e-10:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            else:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localXVector=[nodeJCoords[0]-nodeICoords[0],nodeJCoords[1]-nodeICoords[1],
                            nodeJCoords[2]-nodeICoords[2]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localXVector = [nodeJCoords[0] - nodeICoords[0], nodeJCoords[1] - nodeICoords[1],
                                            nodeJCoords[2] - nodeICoords[2]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['specialEle', eleNodes[0], eleNodes[1], localXVector, localYVector],
                                          tipValue + "_eleLocCordSys"])
        ################################################################################################################
        elif eleType in ['RJWatsonEqsBearing','rJWatsonEqsBearing']:
            eleNodes = ops.eleNodes(eleTag)
            localXVector=[1,0,0]
            localYVector=[0,1,0]
            localZVector=[0,0,1]
            nodeICoords = ops.nodeCoord(eleNodes[0])
            nodeJCoords = ops.nodeCoord(eleNodes[1])
            equalLength = np.sqrt((nodeICoords[0] - nodeJCoords[0]) ** 2 + (nodeICoords[1] - nodeJCoords[1]) ** 2 +
                                  (nodeICoords[2] - nodeJCoords[2]) ** 2)
            if equalLength<1.0e-10:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            else:
                if "-orient" in argsList:
                    orientIndex=argsList.index('-orient')
                    nextIndex=next((index for index, item in enumerate(argsList[int(orientIndex+1):])
                                    if isinstance(item, str)), None)
                    if nextIndex==None:
                        vectNum=len(argsList)-orientIndex-1
                        if vectNum==3:
                            localYVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localXVector=[nodeJCoords[0]-nodeICoords[0],nodeJCoords[1]-nodeICoords[1],
                            nodeJCoords[2]-nodeICoords[2]]
                        else:
                            localXVector=[argsList[orientIndex+1],argsList[orientIndex+2],argsList[orientIndex+3]]
                            localYVector=[argsList[orientIndex+4],argsList[orientIndex+5],argsList[orientIndex+6]]
                    else:
                        if nextIndex==3:
                            localYVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localXVector = [nodeJCoords[0] - nodeICoords[0], nodeJCoords[1] - nodeICoords[1],
                                            nodeJCoords[2] - nodeICoords[2]]
                        else:
                            localXVector = [argsList[orientIndex + 1], argsList[orientIndex + 2], argsList[orientIndex + 3]]
                            localYVector = [argsList[orientIndex + 4], argsList[orientIndex + 5], argsList[orientIndex + 6]]
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['specialEle', eleNodes[0], eleNodes[1], localXVector, localYVector],
                                          tipValue + "_eleLocCordSys"])
        ################################################################################################################
        elif eleType in ['FPBearingPTV','fPBearingPTV']:
            eleNodes = ops.eleNodes(eleTag)
            orientIndex=19
            localXVector = [argsList[orientIndex], argsList[orientIndex + 1], argsList[orientIndex + 2]]
            localYVector = [argsList[orientIndex + 3], argsList[orientIndex + 4], argsList[orientIndex + 5]]
            self.eleSetNameList.append(tipValue + "_ele")
            self.EleLocalCoordSysSetNameList.append(tipValue + "_eleLocCordSys")
            self.saveEleList.append([[eleTag] + eleNodes,tipValue + "_ele"])
            self.EleLocalCoordSys.append([['specialEle', eleNodes[0], eleNodes[1], localXVector, localYVector],
                                          tipValue + "_eleLocCordSys"])
        ################################################################################################################
        else:
            print(123)
        ################################################################################################################

    def rigidLink(self,*args):
        """
        ----------------------------------------------------------------------------------------------------------------
        rigidLink(type, rNodeTag, cNodeTag)
        ----------------------------------------------
        Create a multi-point constraint between nodes.
        ----------------------------------------------
        type (str)
        string-based argument for rigid-link type:
        'bar': only the translational degree-of-freedom will be constrained to be exactly the same
        as those at the master node
        'beam': both the translational and rotational degrees of freedom are constrained.
        rNodeTag (int)	integer tag identifying the master node
        cNodeTag (int)	integar tag identifying the slave node
        ----------------------------------------------
        ----------------------------------------------------------------------------------------------------------------
        """
        eval(f"ops.rigidLink{args}")
        argsList = list(args)
        rigidType=argsList[0]
        rNode=argsList[1]
        cNode=argsList[2]
        rNodeCoords = ops.nodeCoord(rNode)
        cNodeCoords = ops.nodeCoord(cNode)
        equalLength = np.sqrt((rNodeCoords[0] -cNodeCoords[0]) ** 2 + (rNodeCoords[1] -cNodeCoords[1]) ** 2 +
                              (rNodeCoords[2] -cNodeCoords[2]) ** 2)
        tipValue = 'rigidLink'
        if equalLength <= 1.0e-10:
            pass
        else:
            self.eleSetNameList.append(tipValue + "_ele")
            self.saveEleList.append([[0, rNode, cNode],tipValue + "_ele"])
    ####################################################################################################################
    def section(self,*args):
        """
        ----------------------------------------------------------------------------------------------------------------
        section(secType, secTag, *secArgs)
        ----------------------------------------------
        Reference the useage in OpenSeesPy
        ----------------------------------------------
        ----------------------------------------------------------------------------------------------------------------
        """
        eval(f"ops.section{args}")
        self.currentSectTag=args[1]
        self.fiberSectDict[self.currentSectTag]=[]
        self.fiberSectDict[self.currentSectTag].append(['section']+list(args))
    ####################################################################################################################
    def patch(self,*args):
        """
        ----------------------------------------------------------------------------------------------------------------
        Reference the useage in OpenSeesPy
        ----------------------------------------------------------------------------------------------------------------
        """
        eval(f"ops.patch{args}")
        self.fiberSectDict[self.currentSectTag].append(['patch']+list(args))
    ####################################################################################################################
    def layer(self,*args):
        """
        ----------------------------------------------------------------------------------------------------------------
        Reference the useage in OpenSeesPy
        ----------------------------------------------------------------------------------------------------------------
        """
        eval(f"ops.layer{args}")
        self.fiberSectDict[self.currentSectTag].append(['layer']+list(args))
    ####################################################################################################################
    def integration_fiberSection(self,eleTag,fiberList,matTagList,GJValue=1.0e10):
        """
        ----------------------------------------------------------------------------------------------------------------
        Construct fiber seciton
        ------------------------------------------
        Inputs:
            eleTag(int)-the number of fiber section
            fiberList(list)-the fiber information list, eg. [[[yloc0_0,zloc0_0,A0_0],[yloc1_0,zloc01_0,A1_0],...],
                [[yloc0_1,zloc0_1,A0_1],[yloc1_1,zloc01_1,A1_1],...],...]
            matTagList(list)-material number list corresponding to each element in fiberList,eg.[1,2,...]
            GJValue-(float)-linear-elastic torsional stiffness assigned to the section (default value takes 1.0e10)
            tipsString(str)-print information on console
        ----------------------------------------------------------------------------------------------------------------
        """
        ops.section('Fiber', int(eleTag), '-GJ', GJValue)
        [[ops.fiber(eachItem[0], eachItem[1], eachItem[2], matTagList[i1]) for eachItem in fiberList[i1]]
         for i1 in range(len(fiberList))]
    ####################################################################################################################
    def _makeDirs(self,savePath):
        """
        ----------------------------------------------------------------------------------------------------------------
        Make directory if not exists,used only internally
        ------------------------------------------
        savePath(str)-the path of the directory
        ----------------------------------------------------------------------------------------------------------------
        """
        if os.path.exists(savePath):
            pass
        else:
            os.makedirs(savePath)

    ####################################################################################################################

    ####################################################################################################################
    def integration_recorderNode(self,savePath,filename,nodeLists,dofLists,responseType):
        """
        ----------------------------------------------------------------------------------------------------------------
        Records the response of a number of nodes at every converged step
        ------------------------------------------
        savePath(str)-the path of the directory,eg.'nodeDisp'
        fileName(str)-the name of the txt file, eg. 'case1'
        nodeLists(list)-nodes that need record responses, eg. [1,2,3,4]
        dofLists(list)-the specified dof at the nodes whose response is requested.eg. [1,2,3]
        responseType(str)-a string indicating response required
            including:
            'disp' displacement
            'vel' velocity
            'accel' acceleration
            'incrDisp' incremental displacement
            'reaction' nodal reaction
            'eigen i' eigenvector for mode i
            'rayleighForces' damping forces
        ----------------------------------------------------------------------------------------------------------------
        """
        self._makeDirs(savePath)
        fileName = savePath + '/' +filename+ '.txt'
        linkstr = f"ops.recorder('Node', '-file','{fileName}', '-time', '-node',"
        for each in nodeLists:
            linkstr+=f"{each}"+f","
        linkstr+=f"'-dof',"
        for each in dofLists:
            linkstr+=f"{each}"+f","
        linkstr+=f"'{responseType}')"
        eval(linkstr)

    ####################################################################################################################
    def integration_recorderElement(self,savePath,filename,eleList,responseTypeList):
        """
        ----------------------------------------------------------------------------------------------------------------
        Records the response of a number of elements at every converged step
        ------------------------------------------
        savePath(str)-the path of the directory,eg.'eleForce'
        fileName(str)-the name of the txt file, eg. 'case1'
        eleLists(list)-elements that need record responses, eg. [1,2,3,4]
        responseTypeList(list)-arguments which are passed to the setResponse()
            include:
            ['axialForce']-for truss element,1 column for each element
            ['section','1','force']-for nonlinear element force at integrationPoint 1, 4column for each element
            ['section', '1', 'deformation']-for nonlinear element deformation at integrationPoint 1,4column for each element
            ['localForce']-for elestic beamcolumn element and zerolength element force
            ['deformation']--for elestic beamcolumn element and zerolength element deformation
        ----------------------------------------------------------------------------------------------------------------
        """
        self._makeDirs(savePath)
        fileName = savePath + '/' +filename+ '.txt'
        linkstr = f"ops.recorder('Element', '-file','{fileName}', '-time', '-ele',"
        for each in eleList:
            linkstr+=f"{each}"+f","
        for i1 in range(len(responseTypeList)-1):
            linkstr += f"'{responseTypeList[i1]}'" + f","
        linkstr+=f"'{responseTypeList[-1]}'"+f")"
        eval(linkstr)
    ####################################################################################################################
    def integration_gravityLoad(self,nodesList):
        """
        ----------------------------------------------------------------------------------------------------------------
        Apply gravity load to associated nodes
        ------------------------------------------
        nodesList(list)-eg.[[[node1Tag,node1Mass],[],...],[],...]
        ----------------------------------------------------------------------------------------------------------------
        ops.timeSeries('Linear', 1)
        ops.pattern('Plain', 1, 1)
        for each in nodesList:
            ops.load(int(each[0]), 0.0, 0.0, -each[1] * 9.81, 0.0, 0.0, 0.0)
        ----------------------------------------------------------------------------------------------------------------
        """
        ops.timeSeries('Linear', 1)
        ops.pattern('Plain', 1, 1)
        for each in nodesList:
            ops.load(int(each[0]), 0.0, 0.0, -each[1] * 9.81, 0.0, 0.0, 0.0)
    ####################################################################################################################
    def integration_analysisGravity(self,totalStep=1,recordList=None):
        """
        ----------------------------------------------------------------------------------------------------------------
        Static gravity load analysis
        ------------------------------------------
        totalStep(int)-Number of analysis steps to perform
        recordList(list)-responses need to be recordedd
        ----------------------------------------------------------------------------------------------------------------
        """
        totalStep =totalStep
        ops.system('UmfPack')
        ops.constraints('Transformation')
        ops.numberer('RCM')
        ops.test('NormDispIncr', 1.0e-8, 2000)
        ops.algorithm('KrylovNewton')
        ops.integrator('LoadControl',1.0/float(totalStep))
        ops.analysis('Static')
        ops.analyze(int(totalStep))
        ops.loadConst('-time', 0.0) ##-在后续分析步考虑重力作用(将重力视常荷载),并将拟时间置0
        #######################################################
        if recordList!=None:
            nodeDict={}
            trussEleResponseDict={}
            zeroEleResponseDict={}
            zeroEleDirectionDict={}
            nonEleSectResponsesDict={}
            nonEleSectNumberDict={}
            nonZeroEleResponsesDict={}
            for each in recordList:
                if each[0]=='node':
                    nodeIdenty, resType,nodeTags= each[0], each[1], each[2]
                    nodeItemDict={(nodeIdenty+'_'+resType+'_'+str(eachNode)):[] for eachNode in nodeTags}
                    nodeDict={**nodeDict,**nodeItemDict}##Merge two dicts
                elif each[0]=='trussEle':
                    responseType,eleTags =each[1],each[2]
                    eleItemDict={('trussEle_'+responseType+'_'+str(eachEle)):[] for eachEle in eleTags}
                    trussEleResponseDict = {**trussEleResponseDict, **eleItemDict}  ##Merge two dicts
                elif each[0]=='zeroEle':
                    responseType, directions,eleTags = each[1], each[2],each[3]
                    eleItemDict = {('zeroEle_' + responseType + '_' + str(eachEle)): [] for eachEle in eleTags}
                    zeroEleResponseDict = {**zeroEleResponseDict, **eleItemDict}  ##Merge two dicts
                    eleDirectDict = {('zeroEle_' + responseType + '_' + str(eachEle)):directions for eachEle in eleTags}
                    zeroEleDirectionDict = {**zeroEleDirectionDict, **eleDirectDict}  ##Merge two dicts
                elif each[0]=='nonEleSection':
                    responseType,sectNum,eleTags=each[1],each[2],each[3]
                    eleItemDict = {('nonEle_' + responseType + '_' + str(eachEle)): [] for eachEle in eleTags}
                    nonEleSectResponsesDict = {**nonEleSectResponsesDict, **eleItemDict}  ##Merge two dicts
                    sectNumDict = {('nonEle_' + responseType + '_' + str(eachEle)): sectNum for eachEle in eleTags}
                    nonEleSectNumberDict = {**nonEleSectNumberDict, **sectNumDict}  ##Merge two dicts
                elif each[0]=='nonZeroEle':
                    responseType,eleTags = each[1], each[2]
                    eleItemDict = {('nonZeroEle_' + responseType + '_' + str(eachEle)): [] for eachEle in eleTags}
                    nonZeroEleResponsesDict = {**nonZeroEleResponsesDict, **eleItemDict}  ##Merge two dicts
        ####################---recorderProcess---###########
        if recordList != None:
            if nodeDict:
                nodeKeys = nodeDict.keys()
                nodeResNameDict = {'disp': 'nodeDisp', 'vel': 'nodeVel', 'accel': 'nodeAccel',
                                   'reaction': 'nodeReaction'}
                [[resType := eachkey.split('_')[1], nodeTag := eachkey.split('_')[2],
                  tempValue1 := [0.0],
                  tempValue2 := eval(f"ops.{nodeResNameDict[resType]}({nodeTag})"),
                  tempValue3 := [round(tempValue2[i1], 6) for i1 in range(3)],
                  tempValue := tempValue1 + tempValue3,
                  nodeDict['node_' + resType + '_' + str(nodeTag)].append(tempValue)] for eachkey in
                 nodeKeys]  ##海象运算符加列表解析
                [[resType := eachkey.split("_")[1], nodeTag := eachkey.split("_")[2],
                  saveValueList := nodeDict['node_' + resType + '_' + str(nodeTag)],
                  self.saveInstance.saveNodeTimeHistory(nodeSaveName=eachkey,
                nodeHistoryList=saveValueList)] for eachkey in nodeKeys]
            if trussEleResponseDict:
                eleKeys = trussEleResponseDict.keys()
                eleResNameDict = {'axialForce': 'basicForce', 'axialDeform': 'basicDeformation'}
                [[resType := eachkey.split("_")[1], eleTag := eachkey.split("_")[2],
                  tempValue1 := [0.0],
                  tempValue2 := [round(eval(f"ops.{eleResNameDict[resType]}({eleTag})[0]"), 3)],
                  tempValue := tempValue1 + tempValue2,
                  trussEleResponseDict['trussEle_' + resType + '_' + str(eleTag)].append(tempValue)] for
                 eachkey in eleKeys]
                [[resType := eachkey.split("_")[1], eleTag := eachkey.split("_")[2],
                  saveValueList := trussEleResponseDict['trussEle_' + resType + '_' + str(eleTag)],
                  self.saveInstance.saveTrussEleResponseTimeHistory(eleSaveName=eachkey,
                eleHistoryList=saveValueList)] for eachkey in eleKeys]
            if zeroEleResponseDict:
                eleKeys = zeroEleResponseDict.keys()
                [[resType := eachkey.split("_")[1], eleTag := eachkey.split("_")[2],
                  tempValue1 := [0.0],
                  tempValue2 := eval(f"ops.eleResponse({eleTag},'{resType}')"),
                  tempValue3 := [[round(each, 3) for each in tempValue2]],
                  tempValue := tempValue1 + tempValue3 + [zeroEleDirectionDict[eachkey]],
                  zeroEleResponseDict['zeroEle_' + resType + '_' + str(eleTag)].append(tempValue)] for
                 eachkey in eleKeys]  ##海象操作符
                [[resType := eachkey.split("_")[1], eleTag := eachkey.split("_")[2],
                  saveValueList := zeroEleResponseDict['zeroEle_' + resType + '_' + str(eleTag)],
                  self.saveInstance.saveZeroEleResponseTimeHistory(eleSaveName=eachkey,
                eleHistoryList=saveValueList)] for eachkey in eleKeys]
            if nonEleSectResponsesDict:
                eleKeys = nonEleSectResponsesDict.keys()
                digitNumDict = {'sectionForce': 3, 'sectionDeformation': 10}
                [[resType := eachkey.split("_")[1], eleTag := eachkey.split("_")[2],
                  tempValue := [0.0] + [
                      round(eval(f"ops.{resType}({eleTag},{nonEleSectNumberDict[eachkey]},1)"),
                            digitNumDict[resType]),
                      round(eval(f"ops.{resType}({eleTag},{nonEleSectNumberDict[eachkey]},2)"),
                            digitNumDict[resType]),
                      round(eval(f"ops.{resType}({eleTag},{nonEleSectNumberDict[eachkey]},3)"),
                            digitNumDict[resType]),
                      round(eval(f"ops.{resType}({eleTag},{nonEleSectNumberDict[eachkey]},4)")),
                      digitNumDict[resType]],
                  nonEleSectResponsesDict['nonEle_' + resType + '_' + str(eleTag)].append(tempValue)] for
                 eachkey in eleKeys]
                [[resType := eachkey.split("_")[1], eleTag := eachkey.split("_")[2],
                  saveValueList := nonEleSectResponsesDict['nonEle_' + resType + '_' + str(eleTag)],
                  self.saveInstance.saveNonEleSectResponseTimeHistory(eleSaveName=eachkey,
                eleHistoryList=saveValueList)] for eachkey in eleKeys]
            if nonZeroEleResponsesDict:
                eleKeys = nonZeroEleResponsesDict.keys()
                [[resType := eachkey.split("_")[1], eleTag := eachkey.split("_")[2],
                  tempValue1 := [0.0],
                  tempValue2 := eval(f"ops.eleResponse({eleTag},'{resType}')"),
                  tempValue3 := [round(each, 3) for each in tempValue2],
                  tempValue := tempValue1 + tempValue3,
                  nonZeroEleResponsesDict[eachkey].append(tempValue)] for eachkey in eleKeys]
                [[resType := eachkey.split("_")[1], eleTag := eachkey.split("_")[2],
                  saveValueList := nonZeroEleResponsesDict[eachkey],
                  self.saveInstance.saveNonZeroEleResponseTimeHistory(eleSaveName=eachkey,
                    eleHistoryList=saveValueList)] for eachkey in eleKeys]
    ####################################################################################################################
    def integration_analysisModal(self,numModes=10):
        """
        ----------------------------------------------------------------------------------------------------------------
        Modal analysis
        ------------------------------------------
        numModes(int)-number of eigenvalues required
        ----------------------------------------------------------------------------------------------------------------
        """
        tipsString='modal'
        eigenValues = ops.eigen(numModes)
        allNodesTag=ops.getNodeTags()
        self.modalNameList.append(tipsString+'_mode')
        for eachMode in range(numModes):
            saveList = []
            for eachNode in allNodesTag:
                nodeEigenValue = ops.nodeEigenvector(eachNode, int(eachMode + 1))
                saveList.append([eachNode] + nodeEigenValue)
            self.saveInstance.saveModes(modesName=tipsString+'_mode'+'_'+str(eachMode+1), modesList=saveList)
        savePeridList=[]
        for i1 in range(numModes):
            periodT = 2.0 * 3.1415926 / float(eigenValues[i1] ** 0.5)
            savePeridList.append([i1+1,periodT])
        self.saveInstance.savePeriod(periodList=savePeridList)
        if numModes>=10:
            for i2 in range(10):
                print(str(i2 + 1) + ' th period is: ' + str(savePeridList[i2]) + ' second')
        else:
            for i2 in range(numModes):
                print(str(i2 + 1) + ' th period is: ' + str(savePeridList[i2]) + ' second')

    ####################################################################################################################
    def integration_analysisModalProperties(self,numEigen,pflag=1,outname=None):
        """
        ----------------------------------------------------------------------------------------------------------------
            Details
            -------
                This script will return the modal properties of an OpenSeespy model.

            Information
            -----------
                Author: Volkan Ozsarac, Earthquake Engineering PhD Candidate
                Affiliation: University School for Advanced Studies IUSS Pavia
                e-mail: volkanozsarac@iusspavia.it

            References
            ----------
                Chopra, A.K. 2012. Dynamics of Structures: Theory and
                Applications to Earthquake Engineering, Prentice Hall.

            Notes
            -----
                Total (activated) mass is obtained by summing the masses assigned to the
                unrestrained degrees of freedoms (DOFs). Thus, it should not be confused
                with total mass assigned to all DOFs. Influence vectors for rotational
                excitation are not correct at the moment, this addition remains as future work.
                Which reference point to use is not clear for rotational excitations.
                SAP2000 and Seismostruct use different reference points.

            Parameters
            ----------
            numEigen : int
                Number of eigenvalues to calculate.
            pflag    : int (1 or 0)
                flag to print output information on screen
            outname  : str, optional (The default is None)
                if not None and pFlag==1, the modal properties for the
                first numEigen modes will be writtend into outname.csv.

            Returns
            -------
            T        : numpy.ndarray
                Period array for the first numEigen modes.
            Mratios  : dictionary
                Effective modal mass participation ratios for the first numEigen modes.
            Mfactors : dictionary
                Modal particpation factors for the first numEigen modes.
            Mtots    : dictionary
                Total activated masses.
        ----------------------------------------------------------------------------------------------------------------
            """
        import numpy as np
        import openseespy.opensees as op
        import sys

        op.wipeAnalysis()
        op.numberer("Plain")
        op.system('FullGeneral')
        op.algorithm('Linear')
        op.analysis('Transient')

        # Extract the Mass Matrix
        # Note that this is not the global mass matrix, but unrestrained part (Muu)
        op.integrator('GimmeMCK', 1.0, 0.0, 0.0)
        op.analyze(1, 0.0)
        # Number of equations in the model
        N = op.systemSize()  # Has to be done after analyze
        Mmatrix = op.printA('-ret')  # Or use op.printA('-file','M.out')
        Mmatrix = np.array(Mmatrix)  # Convert the list to an array
        Mmatrix.shape = (N, N)  # Make the array an NxN matrix
        print('\n************************************************************', \
              '\nExtracting the mass matrix, ignore the warnings...')

        # Determine maximum number of DOFs/node used in the system
        NDF = 0
        for node in op.getNodeTags():
            temp = len(op.nodeDOFs(node))
            if temp > NDF: NDF = temp

        DOFs = []  # List containing indices of unrestrained DOFs
        used = {}  # Dictionary with nodes and associated unrestrained DOFs
        ldict = {}  # Dictionary containing influence vectors
        Mratios = {}  # Dictionary containing effective modal masses ratios
        Mfactors = {}  # Dictionary containing modal participation factors
        for i in range(1, NDF + 1):
            ldict[i] = np.zeros([N, 1])
            Mratios[i] = np.zeros(numEigen)
            Mfactors[i] = np.zeros(numEigen)

        # Create the influence vectors, and get the unrestrained DOFs assigned to the nodes
        # TODO -1: The influence vectors are not correct in case of rotational excitations
        # One typical approach is to use center of mass on plane
        idx = 0  # Counter for unrestrained DOFs
        for node in op.getNodeTags():  # Start iterating over each node
            used[node] = []  # Unrestrain local DOF ids
            ndof = len(op.nodeDOFs(node))  # Total number of DOFs assigned
            for j in range(ndof):  # Iterate over each DOF
                temp = op.nodeDOFs(node)[j]  # Get the global DOF id (-1 if restrained)
                if temp not in DOFs and temp >= 0:  # Check if this DOF is unrestrained and is not known before
                    DOFs.append(temp)  # Save the global id of DOF
                    used[node].append(j + 1)  # Save the local id of DOF
                    ldict[j + 1][idx, 0] = 1  # Influence vectors for horizontal and vertical excitations
                    idx += 1  # Increase the counter

        # This does not seem necessary when numberer is "Plain"
        # But lets reorganize the mass matrix anyway
        Mmatrix = Mmatrix[DOFs, :][:, DOFs]

        # Calculate the total masses assigned to the unrestrained DOFs
        Mtots = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        for i in range(1, NDF + 1):
            Mtots[i] = (ldict[i].T @ Mmatrix @ ldict[i])[0, 0]

        # Perform eigenvalue analysis
        op.wipeAnalysis()
        listSolvers = ['-genBandArpack', '-fullGenLapack', '-symmBandLapack']
        ok = 1
        for s in listSolvers:
            print("Using %s as solver..." % s[1:])
            try:
                eigenValues = op.eigen(s, numEigen)
                catchOK = 0
                ok = 0
            except:
                catchOK = 1

            if catchOK == 0:
                for i in range(numEigen):
                    if eigenValues[i] < 0:
                        ok = 1
                if ok == 0:
                    print('Eigenvalue analysis is completed.')
                    break
        if ok != 0:
            print("Error on eigenvalue something is wrong...")
            sys.exit()
        else:
            Lambda = np.asarray(eigenValues)
            Omega = Lambda ** 0.5
            T = 2 * np.pi / Omega
            frq = 1 / T

        # Note: influence factors for rotational excitation is wrong!
        # Obtain modal properties
        for mode in range(1, numEigen + 1):
            idx = 0
            phi = np.zeros([N, 1])  # Eigen vector
            for node in used:
                for dof in used[node]:
                    phi[idx, 0] = op.nodeEigenvector(node, mode, dof)
                    idx += 1

            phi = phi / (phi.T @ Mmatrix @ phi) ** 0.5  # Normalize the eigen vector by modal mass
            Mn = phi.T @ Mmatrix @ phi  # Modal mass (should always be equal to 1)

            for j in range(1, NDF + 1):
                if Mtots[j] != 0:  # Check if any mass is assigned
                    Ln = phi.T @ Mmatrix @ ldict[j]  # Modal excitation factor
                    Mnstar = (Ln ** 2 / Mn)[0, 0]  # Effective modal mass
                    Mfactors[j][mode - 1] = Ln / Mn  # Modal participation factor
                    Mratios[j][mode - 1] = (Mnstar / Mtots[j] * 100)  # Effective modal mass participation ratio [%]

        for j in range(1, 7):
            try:
                Mratios[j]
            except:
                Mratios[j] = np.zeros(numEigen)
                Mfactors[j] = np.zeros(numEigen)

        # TODO-1: Results are not correct for rotational excitation cases, for now ignore those.
        del Mratios[6], Mratios[5], Mratios[4]
        del Mfactors[6], Mfactors[5], Mfactors[4]

        # Calculate cumulative modal mass participation ratio
        sM1 = np.cumsum(Mratios[1]);
        sM2 = np.cumsum(Mratios[2]);
        sM3 = np.cumsum(Mratios[3])

        # Print modal analysis results
        if pflag == 1:
            arguments = []
            arguments.append('Modal Periods and Frequencies')
            arguments.append('%4s|%8s|%10s|%12s|%12s' \
                             % ('Mode', 'T [sec]', 'f [Hz]', '\u03C9 [rad/sec]', '\u03BB [rad\u00b2/sec\u00b2]'))
            for mode in range(numEigen):
                arguments.append('%4s|%8s|%10s|%12s|%12s' \
                                 % ("{:.0f}".format(mode + 1), "{:.4f}".format(T[mode]), "{:.3f}".format(frq[mode]), \
                                    "{:.2f}".format(Omega[mode]), "{:.2f}".format(Lambda[mode])))
            arguments.append('Total Activated Masses')
            arguments.append('%8s|%8s|%8s' \
                             % ('M\u2081', 'M\u2082', 'M\u2083'))
            arguments.append('%8s|%8s|%8s' \
                             % ("{:.2f}".format(Mtots[1]), "{:.2f}".format(Mtots[2]), "{:.2f}".format(Mtots[3])))
            arguments.append('Modal Mass Participation Factors')
            arguments.append('%4s|%7s|%7s|%7s' \
                             % ('Mode', '\u0393\u2081', '\u0393\u2082', '\u0393\u2083'))
            for mode in range(numEigen):
                arguments.append('%4s|%7s|%7s|%7s' % ("{:.0f}".format(mode + 1), \
                                                      "{:.3f}".format(Mfactors[1][mode]),
                                                      "{:.3f}".format(Mfactors[2][mode]),
                                                      "{:.3f}".format(Mfactors[3][mode])))
            arguments.append('Effective Modal Mass Participation Ratios [%]')
            arguments.append('%4s|%7s|%7s|%7s' \
                             % ('Mode', 'U\u2081', 'U\u2082', 'U\u2083'))
            for mode in range(numEigen):
                arguments.append('%4s|%7s|%7s|%7s' % ("{:.0f}".format(mode + 1), \
                                                      "{:.3f}".format(Mratios[1][mode]),
                                                      "{:.3f}".format(Mratios[2][mode]),
                                                      "{:.3f}".format(Mratios[3][mode])))
            arguments.append('Cumulative Effective Modal Mass Participation Ratios [%]')
            arguments.append('%4s|%7s|%7s|%7s' \
                             % ('Mode', '\u2211U\u2081', '\u2211U\u2082', '\u2211U\u2083'))
            for mode in range(numEigen):
                arguments.append('%4s|%7s|%7s|%7s' % ("{:.0f}".format(mode + 1), \
                                                      "{:.3f}".format(sM1[mode]), "{:.3f}".format(sM2[mode]),
                                                      "{:.3f}".format(sM3[mode])))

                # To the screen
            arguments = '\n'.join(arguments);
            print(arguments)

            # To the .csv file
            if outname != None:
                with open(outname + '.csv', 'w', encoding='utf-32') as f:
                    f.write(arguments)

        return T, Mratios, Mfactors, Mtots
    ####################################################################################################################
    def integration_earthquakeExcite(self,RayleighDamping,waveLenth,dt,dirList,motionList,factor=9.81,recordList=None,waveNumber=None):
        """
        ----------------------------------------------------------------------------------------------------------------
        Apply a uniform excitation to a model acting in a certain direction
        ------------------------------------------
        RayleighDamping(list)-set the values of Rayleigh damping, with two options,
            option 1: RayleighDamping=['mode-1',dampingRatio,Tstart,Tend]
                    dampRatio(float)-the damping ratio for the structure,eg.0.05
                    Tstart,Tend(float)-the start and end periods for calculating rayleigh damping
            option 2: RayleighDamping=['mode-2',α,β1,β2,β3]
                    D=α×M＋β1×Kcurrent＋β2×Kinit＋β3×KlastCommit
        waveLenth(int)-the length of the ground motion
        dt(float)-the time interval of the motion
        dirList(list)-direction in which ground motion acts,eg. [1,3]
            1 corresponds to translation along the global X axis
            2 corresponds to translation along the global Y axis
            3 corresponds to translation along the global Z axis
            4 corresponds to rotation about the global X axis
            5 corresponds to rotation about the global Y axis
            6 corresponds to rotation about the global Z axis
        motionList(list)-grond motion paths corresponding to the dirList,eg.[path_acc_X,path_acc_Z]
        factor(float)-a value used to scale the ground motion time history
        waveNumber-ground motion number, used for print informaiton on screen
        ----------------------------------------------------------------------------------------------------------------
        """
        if RayleighDamping[0]=='mode-1':
            dampRatio,Tstart,Tend=RayleighDamping[1:]
            w1=2.0*np.pi/float(Tstart)
            w2=2.0*np.pi/float(Tend)
            a = dampRatio * 2.0 * w1 * w2 / float(w1 + w2)
            b = dampRatio * 2 / float(w1 +w2)
            ### D=α×M＋β1×Kcurrent＋β2×Kinit＋β3×KlastCommit Longitudinal direction
            ops.rayleigh(a, 0.0, 0.0,b)
            print('Rayleigh damping: ',a,0.0,0.0,b)
        elif RayleighDamping[0]=='mode-2':
            a,b1,b2,b3=RayleighDamping[1:]
            ops.rayleigh(a,b1,b2,b3)
            print('Rayleigh damping: ',a,b1,b2,b3)
        else:
            pass
        ops.loadConst('-time', 0.0)
        currentLength = waveLenth
        currentDt = dt
        dir_L, dir_T, dir_V = 1, 2, 3
        gmFact =factor
        for i1 in range(len(dirList)):
            ops.timeSeries('Path', int(i1+100), '-dt', currentDt, '-filePath',motionList[i1], '-factor', gmFact)
            ops.pattern('UniformExcitation', int(i1+1000), int(dirList[i1]), '-accel', int(i1+100))
        ######################################################
        ops.wipeAnalysis()
        ops.constraints('Transformation')
        ops.numberer('RCM')
        ops.system('UmfPack')
        # ops.test('NormDispIncr', tol,maxNumIter)
        # ops.algorithm('KrylovNewton')
        # ops.integrator('Newmark', 0.5, 0.25)
        # ops.analysis('Transient')
        ######################################################
        #######################################################
        writeInterNum=200 ###---每200时间步将结果写入数据库一次
        if recordList!=None:
            nodeDict={}
            trussEleResponseDict={}
            zeroEleResponseDict={}
            zeroEleDirectionDict={}
            nonEleSectResponsesDict={}
            nonEleSectNumberDict={}
            nonZeroEleResponsesDict={}
            for each in recordList:
                if each[0]=='node':
                    nodeIdenty, resType,nodeTags= each[0], each[1], each[2]
                    nodeItemDict={(nodeIdenty+'_'+resType+'_'+str(eachNode)):[] for eachNode in nodeTags}
                    nodeDict={**nodeDict,**nodeItemDict}##Merge two dicts
                elif each[0]=='trussEle':
                    responseType,eleTags =each[1],each[2]
                    eleItemDict={('trussEle_'+responseType+'_'+str(eachEle)):[] for eachEle in eleTags}
                    trussEleResponseDict = {**trussEleResponseDict, **eleItemDict}  ##Merge two dicts
                elif each[0]=='zeroEle':
                    responseType, directions,eleTags = each[1], each[2],each[3]
                    eleItemDict = {('zeroEle_' + responseType + '_' + str(eachEle)): [] for eachEle in eleTags}
                    zeroEleResponseDict = {**zeroEleResponseDict, **eleItemDict}  ##Merge two dicts
                    eleDirectDict = {('zeroEle_' + responseType + '_' + str(eachEle)):directions for eachEle in eleTags}
                    zeroEleDirectionDict = {**zeroEleDirectionDict, **eleDirectDict}  ##Merge two dicts
                elif each[0]=='nonEleSection':
                    responseType,sectNum,eleTags=each[1],each[2],each[3]
                    eleItemDict = {('nonEle_' + responseType + '_' + str(eachEle)): [] for eachEle in eleTags}
                    nonEleSectResponsesDict = {**nonEleSectResponsesDict, **eleItemDict}  ##Merge two dicts
                    sectNumDict = {('nonEle_' + responseType + '_' + str(eachEle)): sectNum for eachEle in eleTags}
                    nonEleSectNumberDict = {**nonEleSectNumberDict, **sectNumDict}  ##Merge two dicts
                elif each[0]=='nonZeroEle':
                    responseType,eleTags = each[1], each[2]
                    eleItemDict = {('nonZeroEle_' + responseType + '_' + str(eachEle)): [] for eachEle in eleTags}
                    nonZeroEleResponsesDict = {**nonZeroEleResponsesDict, **eleItemDict}  ##Merge two dicts
        ######################################################
        ######################################################
        startTime = time.perf_counter()
        tCurrent = ops.getTime()
        tFinal = currentLength * currentDt
        timeList = [tCurrent]
        maxNumIter=1000
        tol=1.0e-4
        deltaTList=[]
        deltaT=currentDt
        while (tCurrent < tFinal):
            deltaTList.append(deltaT)
            if deltaT<currentDt:
                if len(set(deltaTList[-400:]))==1:
                    deltaT=deltaT*2
                    print("The initial dt is:", currentDt, ", and the increase current dt is:", deltaT)
                if deltaT>=currentDt:
                    deltaT=currentDt
            ####['NormDispIncr', 'RelativeEnergyIncr', 'EnergyIncr', 'RelativeNormUnbalance',
            ##### 'RelativeNormDispIncr', 'NormUnbalance']
            ops.test('NormDispIncr', tol,maxNumIter)
            #####['KrylovNewton',, ['SecantNewton','-initial'], ['ModifiedNewton','-initial'],
            ##### ['RaphsonNewton','-initial'], 'PeriodicNewton','BFGS', 'Broyden', 'NewtonLineSearch'],前四个zengjia,'-initial'
            ops.algorithm('ModifiedNewton','-initial')  ##收敛性好于前两个
            # ops.algorithm('KrylovNewton')
            NewmarkGamma = 0.5
            NewmarkBeta = 0.25
            ops.integrator('Newmark', NewmarkGamma, NewmarkBeta)
            ops.analysis('Transient')
            ok = ops.analyze(1, deltaT)
            if (ok == 0):
                tCurrent = ops.getTime()
                timeList.append(tCurrent)
                endTime = time.perf_counter()
                realTime = endTime - startTime
                ##################################################
                ####################---recorderProcess---###########
                if recordList!=None:
                    if nodeDict:
                        nodeKeys=nodeDict.keys()
                        nodeResNameDict={'disp':'nodeDisp','vel':'nodeVel','accel':'nodeAccel','reaction':'nodeReaction'}
                        if (len(nodeDict[list(nodeKeys)[0]])>=writeInterNum) or (tCurrent>=tFinal):
                            [[resType:=eachkey.split("_")[1],nodeTag:=eachkey.split("_")[2],
                              saveValueList:=nodeDict['node_'+resType+'_'+str(nodeTag)],
                              self.saveInstance.saveNodeTimeHistory(nodeSaveName=eachkey, nodeHistoryList=saveValueList)
                              ] for eachkey in nodeKeys]
                            for eachkey in nodeKeys:
                                nodeDict[eachkey] = []
                        [[resType:=eachkey.split('_')[1],nodeTag:=eachkey.split('_')[2],tempValue1:=[round(tCurrent,4)],
                          tempValue2:=eval(f"ops.{nodeResNameDict[resType]}({nodeTag})"),
                            tempValue3:=[round(tempValue2[i1],6) for i1 in range(3)],
                          tempValue:=tempValue1+tempValue3,
                          nodeDict['node_' + resType + '_' + str(nodeTag)].append(tempValue)] for eachkey in nodeKeys] ##海象运算符加列表解析
                    if trussEleResponseDict:
                        eleKeys = trussEleResponseDict.keys()
                        eleResNameDict = {'axialForce': 'basicForce','axialDeform':'basicDeformation'}
                        if (len(trussEleResponseDict[list(eleKeys)[0]])>=writeInterNum) or (tCurrent>=tFinal):
                            [[resType:=eachkey.split("_")[1],eleTag:=eachkey.split("_")[2],
                              saveValueList:=trussEleResponseDict['trussEle_'+resType+'_'+str(eleTag)],
                              self.saveInstance.saveTrussEleResponseTimeHistory(eleSaveName=eachkey,
                              eleHistoryList=saveValueList)] for eachkey in eleKeys]
                            for eachkey in eleKeys:
                                trussEleResponseDict[eachkey] = []
                        [[resType:=eachkey.split("_")[1],eleTag:=eachkey.split("_")[2],tempValue1:=[round(tCurrent,4)],
                          tempValue2:=[round(eval(f"ops.{eleResNameDict[resType]}({eleTag})[0]"),3)],
                          tempValue:=tempValue1+tempValue2,
                          trussEleResponseDict['trussEle_'+resType+'_'+str(eleTag)].append(tempValue)] for eachkey in eleKeys]
                    if zeroEleResponseDict:
                        eleKeys = zeroEleResponseDict.keys()
                        if (len(zeroEleResponseDict[list(eleKeys)[0]])>=writeInterNum) or (tCurrent>=tFinal):
                            [[resType:=eachkey.split("_")[1],eleTag:=eachkey.split("_")[2],
                              saveValueList:=zeroEleResponseDict['zeroEle_'+resType+'_'+str(eleTag)],
                              self.saveInstance.saveZeroEleResponseTimeHistory(eleSaveName=eachkey,
                              eleHistoryList=saveValueList)] for eachkey in eleKeys]
                            for eachkey in eleKeys:
                                zeroEleResponseDict[eachkey] = []
                        [[resType:=eachkey.split("_")[1],eleTag:=eachkey.split("_")[2],tempValue1:=[round(tCurrent,4)],
                          tempValue2:=eval(f"ops.eleResponse({eleTag},'{resType}')"),
                          tempValue3:=[[round(each,3) for each in tempValue2]],
                          tempValue:= tempValue1 + tempValue3+[zeroEleDirectionDict[eachkey]],
                          zeroEleResponseDict['zeroEle_'+resType+'_'+str(eleTag)].append(tempValue)] for eachkey in eleKeys]##海象操作符
                    if nonEleSectResponsesDict:
                        eleKeys = nonEleSectResponsesDict.keys()
                        digitNumDict = {'sectionForce':3,'sectionDeformation':10}
                        if (len(nonEleSectResponsesDict[list(eleKeys)[0]])>=writeInterNum) or (tCurrent>=tFinal):
                            [[resType:=eachkey.split("_")[1],eleTag:=eachkey.split("_")[2],
                              saveValueList:=nonEleSectResponsesDict['nonEle_'+resType+'_'+str(eleTag)],
                              self.saveInstance.saveNonEleSectResponseTimeHistory(eleSaveName=eachkey,
                            eleHistoryList=saveValueList)] for eachkey in eleKeys]
                            for eachkey in eleKeys:
                                nonEleSectResponsesDict[eachkey] = []
                        [[resType:=eachkey.split("_")[1],eleTag:=eachkey.split("_")[2],
                          tempValue := [round(tCurrent, 4)] + [round(eval(f"ops.{resType}({eleTag},{nonEleSectNumberDict[eachkey]},1)"),
                                                                     digitNumDict[resType]),
                            round(eval(f"ops.{resType}({eleTag},{nonEleSectNumberDict[eachkey]},2)"),digitNumDict[resType]),
                            round(eval(f"ops.{resType}({eleTag},{nonEleSectNumberDict[eachkey]},3)"),digitNumDict[resType]),
                            round(eval(f"ops.{resType}({eleTag},{nonEleSectNumberDict[eachkey]},4)")),digitNumDict[resType]],
                          nonEleSectResponsesDict['nonEle_' + resType + '_' + str(eleTag)].append(tempValue)] for eachkey in eleKeys]
                    if nonZeroEleResponsesDict:
                        eleKeys = nonZeroEleResponsesDict.keys()
                        if (len(nonZeroEleResponsesDict[list(eleKeys)[0]])>=writeInterNum) or (tCurrent>=tFinal):
                            [[resType:=eachkey.split("_")[1],eleTag:=eachkey.split("_")[2],
                              saveValueList:=nonZeroEleResponsesDict[eachkey],
                              self.saveInstance.saveNonZeroEleResponseTimeHistory(eleSaveName=eachkey,
                            eleHistoryList=saveValueList)] for eachkey in eleKeys]
                            for eachkey in eleKeys:
                                nonZeroEleResponsesDict[eachkey] = []
                        [[resType := eachkey.split("_")[1], eleTag := eachkey.split("_")[2],tempValue1:=[round(tCurrent, 4)],
                          tempValue2:=eval(f"ops.eleResponse({eleTag},'{resType}')"),
                        tempValue3:=[round(each,3) for each in tempValue2],tempValue := tempValue1 + tempValue3,
                         nonZeroEleResponsesDict[eachkey].append(tempValue)] for eachkey in eleKeys]
                ###################################
                ###################################
                print('KrylovNewton',f'ground motion={waveNumber}','tol=',tol,'maxNumIter=',maxNumIter, 'totalTime=',
                      tFinal, 'tCurrent=',"{:.6f}".format(tCurrent),'time cost=', "{:.1f}".format(realTime), 'second')
            else:
                if deltaT>=0.000001*currentDt:
                    deltaT=deltaT*0.5
                    print("The initial dt is:",currentDt,", and the decrease current dt is:",deltaT)
                else:
                    print(f"ground moition {waveNumber}"," failed!")
                    break
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
        from auxiliaryModules.SecPropertyCalDxfPy.SecPropertyCalDxfPy import SecPropertyCalDxfPy

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
        from auxiliaryModules.CalculateIMs.IMs import  IMs
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
        from auxiliaryModules.responseSpectCalculate.responseSpectMain import SaSvSd

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
        from auxiliaryModules.baseLineCorrectionAndFiltering.BaseLineCorrectionAndFiltering import AccToVelocity
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
        from auxiliaryModules.baseLineCorrectionAndFiltering.BaseLineCorrectionAndFiltering import VelToDisplacement
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
        from auxiliaryModules.baseLineCorrectionAndFiltering.BaseLineCorrectionAndFiltering import DispToVelocity
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
        from auxiliaryModules.baseLineCorrectionAndFiltering.BaseLineCorrectionAndFiltering import VelToAccele
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
        from auxiliaryModules.baseLineCorrectionAndFiltering.BaseLineCorrectionAndFiltering import polynomialBaseLineCorrect
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
        from auxiliaryModules.baseLineCorrectionAndFiltering.BaseLineCorrectionAndFiltering import improvedWuBaseLineCorrect
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
        from auxiliaryModules.baseLineCorrectionAndFiltering.BaseLineCorrectionAndFiltering import accFilter
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
        from auxiliaryModules.MCAnalysis.Material import Material
        from auxiliaryModules.MCAnalysis.MCAnalysis import MC
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
        from auxiliaryModules.MCAnalysis.Material import Material
        from auxiliaryModules.MCAnalysis.MCAnalysis import MC
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
        from auxiliaryModules.pythonInteractSAP2000.SAP2000Py import SAP2000Py
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
    shakeInstance=ShakeTableTest()
    # scaleRatioDict = shakeInstance.scaleRatio(lengthRatio=0.2, stressRatio=0.3, acceleratioRatio=1)
    # print(scaleRatioDict)
    times=np.loadtxt("WN_Responses/1-WN-times.txt")
    acc_1_AX5=np.loadtxt("WN_Responses/1-WN-T1-5-AX.txt")
    acc_1_AX1 = np.loadtxt("WN_Responses/1-WN-T1-1-AX.txt")
    acc_1_AX3 = np.loadtxt("WN_Responses/1-WN-T1-3-AX.txt")
    acc_1_AX4 = np.loadtxt("WN_Responses/1-WN-T1-4-AX.txt")
    acc_1_GAX1=np.loadtxt("WN_Responses/1-WN-GAX-1.txt")
    # pltHandle=shakeInstance.plotAcc([times,times,times,times],[acc_1_AX5,acc_1_AX4,acc_1_AX3,acc_1_AX1],
    #                                 labelsList=['T1-5-AX','T1-4-AX','T1-3-AX','T1-1-AX'])
    # pltHandle.show()
    dt=times[1]-times[0]
    pltHandle=shakeInstance.freResFunc(dt,3,acc_1_AX5,[acc_1_AX1],['1'],10,90)
    pltHandle.show()


















