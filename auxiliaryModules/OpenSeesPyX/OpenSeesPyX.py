########################################################################################################################
#  Author: Junjun Guo
#  E-mail: guojj@tongji.edu.cn/guojj_ce@163.com
#    Date: 05/02/2020
########################################################################################################################
import os
import numpy as np
import openseespy.opensees as ops
import time
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Wedge
from .SqliteDB import SqliteDB  ##sqlite database to store opensees results
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
        Notes:
            To use this auxiliary function, the section fiber should be constructed with the OpenSeesPyX command
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
                    [[bar := Circle((yi,zi), r, ec='k', fc='k', zorder=10),ax.add_patch(bar)] for zi, yi in zip(Z, Y)]

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
                    [[bar := Circle((yi,zi), r_bar, ec='k', fc='k', zorder=10),ax.add_patch(bar)] for zi, yi in zip(Z, Y)]

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
                    print('Warning! Patch quad is non-convex or counter-clockwise defined or has at least 3'
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
                    [[[zy := np.array([[Y[j, k],Z[j, k]],
                                           [Y[j, k + 1],Z[j, k + 1]],
                                           [Y[j + 1, k + 1],Z[j + 1, k + 1]],
                                           [Y[j + 1, k],Z[j + 1, k]]]),poly := Polygon(zy, closed=True, ec='k',
                                           fc=matColorDict[matTag]),
                       ax.add_patch(poly)] for k in range(nJK)] for j in range(nIJ)]
                else:
                    # horizontal lines
                    [plt.plot([ay, by],[az, bz], 'b-', zorder=1) for az, bz, ay, by in zip(IJz, LKz, IJy, LKy)]
                    # vertical lines
                    [plt.plot( [ay, by],[az, bz], 'b-', zorder=1) for az, bz, ay, by in zip(JKz, ILz, JKy, ILy)]

            if item[0] == 'patch' and item[1] == 'circ':
                matTag, nc, nr = item[2], item[3], item[4]
                yC, zC, ri, re = item[5], item[6], item[7], item[8]
                a0, a1 = item[9], item[10]
                dr = (re - ri) / nr
                dth = (a1 - a0) / nc
                [[rj := ri + j * dr,rj1 := rj + dr,[[thi:= a0 + i * dth,thi1:= thi + dth,wedge:= Wedge((yC,zC),
                    rj1, thi, thi1, width=dr, ec='k',lw=1, fc=matColorDict[matTag]),ax.add_patch(wedge)]
                                                    for i in range(nc)]] for j in range(nr)]
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

        [self.saveInstance.saveNodes(nodesSaveName=eachKey, nodeList=nodeDict[eachKey]) for eachKey in nodeDict.keys()]
        self.saveNodeList=[]###---empty the list after writing data to database

        geomDict={}
        for eachItem in self.saveGeomfList:
            if eachItem[1] not in geomDict.keys():
                geomDict[eachItem[1]] = []
                geomDict[eachItem[1]].append(eachItem[0])
            else:
                geomDict[eachItem[1]].append(eachItem[0])
        [self.saveInstance.saveGeomTransf(geomTransfSaveName=eachKey,geomfList=geomDict[eachKey]) for eachKey in geomDict.keys()]
        self.saveGeomfList=[]

        eleDict={}
        for eachItem in self.saveEleList:
            if eachItem[1] not in eleDict.keys():
                eleDict[eachItem[1]] = []
                eleDict[eachItem[1]].append(eachItem[0])
            else:
                eleDict[eachItem[1]].append(eachItem[0])
        [self.saveInstance.saveEles(elesSaveName=eachKey, elesList=eleDict[eachKey]) for eachKey in eleDict.keys()]
        self.saveEleList=[]

        eleLocCoordDict={}
        for eachItem in self.EleLocalCoordSys:
            if eachItem[1] not in eleLocCoordDict.keys():
                eleLocCoordDict[eachItem[1]] = []
                eleLocCoordDict[eachItem[1]].append(eachItem[0])
            else:
                eleLocCoordDict[eachItem[1]].append(eachItem[0])
        [self.saveInstance.saveEleLocalCoordSys(SaveName=eachKey,EleLocalCoordSys=eleLocCoordDict[eachKey])
         for eachKey in eleLocCoordDict.keys()]
        self.EleLocalCoordSys=[]


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
        [ops.load(int(each[0]), 0.0, 0.0, -each[1] * 9.81, 0.0, 0.0, 0.0) for each in nodesList]
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
        [[saveList:= [],[[nodeEigenValue:= ops.nodeEigenvector(eachNode, int(eachMode + 1)),
                          saveList.append([eachNode] + nodeEigenValue)] for eachNode in allNodesTag],
          self.saveInstance.saveModes(modesName=tipsString+'_mode'+'_'+str(eachMode+1), modesList=saveList)]
         for eachMode in range(numModes)]

        savePeridList=[]
        [[periodT:= 2.0 * 3.1415926 / float(eigenValues[i1] ** 0.5),savePeridList.append([i1+1,periodT])] for i1 in range(numModes)]
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
if __name__ == "__main__":
    pass







