#-*-coding: UTF-8-*-
#####Units: Length-m, Force-kN, mass-ton, Stress-kpa(10e-3MPa), g=9.81m/s2 pho=ton/mm3
########################################################################################################################
#  Author: Junjun Guo,Tongji University. https://github.com/Junjun1guo
#  E-mail: guojj@tongji.edu.cn/guojj_ce@163.com
#  Environemet: Successfully executed in python 3.8
#  Date: 2023-04-03
########################################################################################################################
########################---import modules---#################################
import numpy as np
import os
import math
import pandas as pd
from time import time
import openseespy.opensees as ops
import sys
sys.path.append("..")
############################----import auxiliary modules---#######################################
###---CalculateGroundMotionIMs is a class for calculate ground motion intensity measure,please use the command
###---print(help(CalculateGroundMotionIMs)) to check the structure and the usage of the class
from auxiliaryModules.mainMod  import CalculateGroundMotionIMs
###---GroundMotionProcess is a class for ground motion baseline correction ,fltering, and conversion among acceleration,
###---velocity and displacement, please use the command print(help(GroundMotionProcess)) to check the structure and
###---the usage of the class
from auxiliaryModules.mainMod import GroundMotionProcess
###---OpenSeesPyX is a class for the visualization and quick construction of OpenSeesPy model. please use the command
###---print(help(OpenSeesPyX)) to check the structure and the usage of the class
from auxiliaryModules.mainMod import OpenSeesPyX
###---SectionPropertyCalculate is class for calculating the section properties. please use the command
###---print(help(SectionPropertyCalculate)) to check the structure and the usage of the class
from auxiliaryModules.mainMod import SectionPropertyCalculate
###---SectionFiberDivide is a class for section fiber divide, used for quickly construct fiber-based nonlinear elements.
###---please use the command print(help(SectionFiberDivide)) to check the structure and the usage of the class
from auxiliaryModules.mainMod import SectionFiberDivide
###---SectMCAnalysis is a class for section moment curvature analysis. please use the command
###---print(help(SectMCAnalysis)) to check the structure and the usage of the class
from auxiliaryModules.mainMod import SectMCAnalysis
###---ExciteAnyDirectionOpenSees is a class for horizontally rotate FE model,it is convinient to get the rotated node
###---coordinates use this class. please use the command print(help(ExciteAnyDirectionOpenSees)) to check the structure
###---and the usage of the class
from auxiliaryModules.mainMod import ExciteAnyDirectionOpenSees
###---PythonInteractSAP2000 is a class for python  interacting with the SAP2000 program.
from auxiliaryModules.mainMod import PythonInteractSAP2000
########################################################################################################################
########################################################################################################################
########################################################################################################################
##################---初始化辅助类OpenSeesPyX用于OPenSeesPy模型可视化及后处理---############
opsX = OpenSeesPyX(dataBaseName="cableStayedBrideModel")  ###初始化OpenSeesPyX类
########################################################################################################################
##########################################---定义模型维数及自由度数---######################################################
ops.wipe()
ops.model('basic','-ndm',3,'-ndf',6)
########################################################################################################################
##########################################---定义模型维数及自由度数---######################################################
cableNodes = np.loadtxt('modelInformation/cableNodes.txt')
for each in cableNodes:
    nodeTageValue = int(each[0])
    xCoordValue = float(each[1])
    yCoordValue = float(each[2])
    zCoordValue = float(each[3])
    nodeMassValue = float(each[4])
    ###---为了可视化采用opsX,参数跟ops中完全一致
    opsX.node(nodeTageValue, xCoordValue, yCoordValue, zCoordValue, '-mass', nodeMassValue, nodeMassValue,nodeMassValue, 0.0, 0.0, 0.0)
    opsX.auxiliary_writeModelInformationToDB()  ###---将模型信息写入数据库，以便在SAPBridge中显示模型
########################################################################################################################
##########################################---建立拉索材料---##############################################################
cableMaterial = np.loadtxt('modelInformation/newCableMat.txt')
cableYieldStress=1.67e6
for each in cableMaterial:
    cableMatTag = int(each[0])
    cableEValue = float(each[1])
    preStrValue = float(each[2])
    eps0Value = -preStrValue / float(cableEValue)
    epsyNValue = 0.0
    epsyPValue = cableYieldStress / float(cableEValue) + eps0Value
    ops.uniaxialMaterial('ElasticPP', cableMatTag, cableEValue, epsyPValue, epsyNValue, eps0Value)
########################################################################################################################
##########################################---建立拉索单元---##############################################################
cableEle = np.loadtxt('modelInformation/newCableEle.txt')
for each in cableEle:
    EleTag = int(each[0])
    NodeI = int(each[1])
    NodeJ = int(each[2])
    A = float(each[3])
    MatTag = int(each[4])
    opsX.element('Truss', EleTag, NodeI, NodeJ, A, MatTag)
########################################################################################################################
##########################################---建立主梁节点---##############################################################
girderNode = np.loadtxt('modelInformation/GirderNode.txt')
for each in girderNode:
    nodeTageValue = int(each[0])
    xCoordValue = float(each[1])
    yCoordValue = float(each[2])
    zCoordValue = float(each[3])
    nodeMassValue = float(each[4])
    ###---为了可视化采用opsX,参数跟ops中完全一致
    opsX.node(nodeTageValue, xCoordValue, yCoordValue, zCoordValue, '-mass', nodeMassValue, nodeMassValue,nodeMassValue, 0.0, 0.0, 0.0)
########################################################################################################################
##########################################---建立主梁局部坐标转换---########################################################
girderTransf = np.loadtxt('modelInformation/newGirderTransf.txt')
for each in girderTransf:
    TransfTag = int(each[0])
    localZXCoord = float(each[1])
    localZYCoord = float(each[2])
    localZZCoord = float(each[3])
    ###---为了显示单元局部坐标轴,采用opsX,局部1,2,3采用红、绿、蓝表示
    opsX.geomTransf('PDelta', TransfTag, localZXCoord, localZYCoord, localZZCoord)
########################################################################################################################
##########################################---建立主梁单元---##############################################################
girderEle = np.loadtxt('modelInformation/GirderEle.txt')
for each in girderEle:
    EleTag = int(each[0])
    NodeI = int(each[1])
    NodeJ = int(each[2])
    A = float(each[3])
    E = float(each[4])
    G = float(each[5])
    J = float(each[6])
    Iy = float(each[7])
    Iz = float(each[8])
    Transf = int(each[9])
    opsX.element('elasticBeamColumn', EleTag, NodeI, NodeJ, A, E, G, J, Iy, Iz, Transf)
########################################################################################################################
##########################################---建立墩柱节点---##############################################################
pierNode = np.loadtxt('modelInformation/newPierNodes.txt')
for each in pierNode:
    nodeTageValue = int(each[0])
    xCoordValue = float(each[1])
    yCoordValue = float(each[2])
    zCoordValue = float(each[3])
    nodeMassValue = float(each[4])
    ###---为了可视化采用opsX,参数跟ops中完全一致
    opsX.node(nodeTageValue, xCoordValue, yCoordValue, zCoordValue, '-mass', nodeMassValue, nodeMassValue,nodeMassValue, 0.0, 0.0, 0.0)
########################################################################################################################
##########################################---建立墩柱局部坐标转换---########################################################
pierTransf = np.loadtxt('modelInformation/newPierTransfRotate-1.txt')
for each in pierTransf:
    TransfTag = int(each[0])
    localZXCoord = float(each[1])
    localZYCoord = float(each[2])
    localZZCoord = float(each[3])
    ###---为了显示单元局部坐标轴,采用opsX,局部1,2,3采用红、绿、蓝表示
    opsX.geomTransf('PDelta', TransfTag, localZXCoord, localZYCoord, localZZCoord)
########################################################################################################################
##########################################---建立弹性墩柱单元---###########################################################
elasticPylonEle = np.loadtxt('modelInformation/elasticPylonEle.txt')
for each in elasticPylonEle:
    EleTag = int(each[0])
    NodeI = int(each[1])
    NodeJ = int(each[2])
    A = float(each[3])
    E = float(each[4])
    G = float(each[5])
    J = float(each[6])
    Iy = float(each[7])
    Iz = float(each[8])
    Transf = int(each[9])
    opsX.element('elasticBeamColumn', EleTag, NodeI, NodeJ, A, E, G, J, Iy, Iz, Transf)
########################################################################################################################
##########################################---建立各种单轴材料---###########################################################
HRB235Number = opsX.auxiliary_materialReNumber('HRB235')  ###---用于返回材料编号
ops.uniaxialMaterial('Steel01',HRB235Number, 235.e3, 2.1e8, 0.005)
HRB335Number = opsX.auxiliary_materialReNumber('HRB335')
ops.uniaxialMaterial('Steel01', HRB335Number,335.e3, 2.1e8, 0.005)
HRB400Number = opsX.auxiliary_materialReNumber('HRB400')
ops.uniaxialMaterial('Steel01',HRB400Number,400.0e3,2.05e8,0.006775)
C40_CoverNumber = opsX.auxiliary_materialReNumber('C40_Cover')
ops.uniaxialMaterial('Concrete01',C40_CoverNumber,-22780,-0.0020,-22780 * 0.2,-0.004)
C50_CoverNumber = opsX.auxiliary_materialReNumber('C50_Cover')
ops.uniaxialMaterial('Concrete01',C50_CoverNumber,-27540,-0.0020,-27540 * 0.2,-0.004)
C55_CoverNumber = opsX.auxiliary_materialReNumber('C55_Cover')
ops.uniaxialMaterial('Concrete01',C55_CoverNumber,-30175,-0.0020,-30175 * 0.2,-0.004)
C40_CoreNumber = opsX.auxiliary_materialReNumber('C40_Core')
ops.uniaxialMaterial('Concrete01',C40_CoreNumber,-30944,-0.00558,-30944 * 0.2,-0.0282)
C50_CoreNumber = opsX.auxiliary_materialReNumber('C50_Core')
ops.uniaxialMaterial('Concrete01',C50_CoreNumber,-36759,-0.00535,-36759 * 0.2,-0.0268)
C55_CoreNumber = opsX.auxiliary_materialReNumber('C55_Core')
ops.uniaxialMaterial('Concrete01',C55_CoreNumber,-42677,-0.00614,-42677 * 0.2,-0.0315)
########################################################################################################################
##########################################---建立纤维截面---##############################################################
###construct upper section
pylonUpperCover = np.loadtxt('fiberInfo/pylonUpper/coverDivide.txt')
pylonUpperCore = np.loadtxt('fiberInfo/pylonUpper/coreDivide.txt')
pylonUpperBar = np.loadtxt('fiberInfo/pylonUpper/barDivide.txt')
pylonUpperList = [pylonUpperCover, pylonUpperCore, pylonUpperBar]
pylonUpperMatList = [opsX.materialNumberDict['C55_Cover'], opsX.materialNumberDict['C55_Core'],
                     opsX.materialNumberDict['HRB400']]
ops.section('Fiber', 41082, '-GJ', 1.0e10)
[ops.fiber(eachItem[0], eachItem[1], eachItem[2],pylonUpperMatList[i1]) for i1 in range(len(pylonUpperList))
 for eachItem in pylonUpperList[i1]]

pylonUpperCover = np.loadtxt('fiberInfo/pierFiber1/coverDivide.txt')
pylonUpperCore = np.loadtxt('fiberInfo/pierFiber1/coreDivide.txt')
pylonUpperBar = np.loadtxt('fiberInfo/pierFiber1/barDivide.txt')
pylonUpperList = [pylonUpperCover, pylonUpperCore, pylonUpperBar]
pylonUpperMatList = [opsX.materialNumberDict['C40_Cover'], opsX.materialNumberDict['C40_Core'],
                     opsX.materialNumberDict['HRB400']]
ops.section('Fiber', 11001, '-GJ', 1.0e10)
[ops.fiber(eachItem[0], eachItem[1], eachItem[2],pylonUpperMatList[i1]) for i1 in range(len(pylonUpperList))
 for eachItem in pylonUpperList[i1]]

for i1 in range(41001, 41019):
    pylonUpperCover = np.loadtxt('fiberInfo/4pylonBottom/' + str(i1) + '_coverDivide.txt')
    pylonUpperCore = np.loadtxt('fiberInfo/4pylonBottom/' + str(i1) + '_coreDivide.txt')
    pylonUpperBar = np.loadtxt('fiberInfo/4pylonBottom/' + str(i1) + '_barDivide.txt')
    pylonUpperList = [pylonUpperCover, pylonUpperCore, pylonUpperBar]
    pylonUpperMatList = [opsX.materialNumberDict['C55_Cover'], opsX.materialNumberDict['C55_Core'],
                         opsX.materialNumberDict['HRB400']]
    ops.section('Fiber', int(i1), '-GJ', 1.0e10)
    [ops.fiber(eachItem[0], eachItem[1], eachItem[2], pylonUpperMatList[i1]) for i1 in range(len(pylonUpperList))
     for eachItem in pylonUpperList[i1]]

for i1 in range(51001, 51015):
    pylonUpperCover = np.loadtxt('fiberInfo/5pylonBottom/' + str(i1) + '_coverDivide.txt')
    pylonUpperCore = np.loadtxt('fiberInfo/5pylonBottom/' + str(i1) + '_coreDivide.txt')
    pylonUpperBar = np.loadtxt('fiberInfo/5pylonBottom/' + str(i1) + '_barDivide.txt')
    pylonUpperList = [pylonUpperCover, pylonUpperCore, pylonUpperBar]
    pylonUpperMatList = [opsX.materialNumberDict['C55_Cover'], opsX.materialNumberDict['C55_Core'],
                         opsX.materialNumberDict['HRB400']]
    ops.section('Fiber', int(i1), '-GJ', 1.0e10)
    [ops.fiber(eachItem[0], eachItem[1], eachItem[2], pylonUpperMatList[i1]) for i1 in range(len(pylonUpperList))
     for eachItem in pylonUpperList[i1]]

for i1 in range(41019, 41029):
    pylonUpperCover = np.loadtxt('fiberInfo/4pylonMiddle/' + str(i1) + '_coverDivide.txt')
    pylonUpperCore = np.loadtxt('fiberInfo/4pylonMiddle/' + str(i1) + '_coreDivide.txt')
    pylonUpperBar = np.loadtxt('fiberInfo/4pylonMiddle/' + str(i1) + '_barDivide.txt')
    pylonUpperList = [pylonUpperCover, pylonUpperCore, pylonUpperBar]
    pylonUpperMatList = [opsX.materialNumberDict['C55_Cover'], opsX.materialNumberDict['C55_Core'],
                         opsX.materialNumberDict['HRB400']]
    ops.section('Fiber', int(i1), '-GJ', 1.0e10)
    [ops.fiber(eachItem[0], eachItem[1], eachItem[2], pylonUpperMatList[i1]) for i1 in range(len(pylonUpperList))
     for eachItem in pylonUpperList[i1]]

for i1 in range(41072, 41082):
    pylonUpperCover = np.loadtxt('fiberInfo/4pylonMiddle/' + str(i1) + '_coverDivide.txt')
    pylonUpperCore = np.loadtxt('fiberInfo/4pylonMiddle/' + str(i1) + '_coreDivide.txt')
    pylonUpperBar = np.loadtxt('fiberInfo/4pylonMiddle/' + str(i1) + '_barDivide.txt')
    pylonUpperList = [pylonUpperCover, pylonUpperCore, pylonUpperBar]
    pylonUpperMatList = [opsX.materialNumberDict['C55_Cover'], opsX.materialNumberDict['C55_Core'],
                         opsX.materialNumberDict['HRB400']]
    ops.section('Fiber', int(i1), '-GJ', 1.0e10)
    [ops.fiber(eachItem[0], eachItem[1], eachItem[2], pylonUpperMatList[i1]) for i1 in range(len(pylonUpperList))
     for eachItem in pylonUpperList[i1]]

for i1 in range(51015, 51025):
    pylonUpperCover = np.loadtxt('fiberInfo/5pylonMiddle/' + str(i1) + '_coverDivide.txt')
    pylonUpperCore = np.loadtxt('fiberInfo/5pylonMiddle/' + str(i1) + '_coreDivide.txt')
    pylonUpperBar = np.loadtxt('fiberInfo/5pylonMiddle/' + str(i1) + '_barDivide.txt')
    pylonUpperList = [pylonUpperCover, pylonUpperCore, pylonUpperBar]
    pylonUpperMatList = [opsX.materialNumberDict['C55_Cover'], opsX.materialNumberDict['C55_Core'],
                         opsX.materialNumberDict['HRB400']]
    ops.section('Fiber', int(i1), '-GJ', 1.0e10)
    [ops.fiber(eachItem[0], eachItem[1], eachItem[2], pylonUpperMatList[i1]) for i1 in range(len(pylonUpperList))
     for eachItem in pylonUpperList[i1]]

for i1 in range(51068, 51078):
    pylonUpperCover = np.loadtxt('fiberInfo/5pylonMiddle/' + str(i1) + '_coverDivide.txt')
    pylonUpperCore = np.loadtxt('fiberInfo/5pylonMiddle/' + str(i1) + '_coreDivide.txt')
    pylonUpperBar = np.loadtxt('fiberInfo/5pylonMiddle/' + str(i1) + '_barDivide.txt')
    pylonUpperList = [pylonUpperCover, pylonUpperCore, pylonUpperBar]
    pylonUpperMatList = [opsX.materialNumberDict['C55_Cover'], opsX.materialNumberDict['C55_Core'],
                         opsX.materialNumberDict['HRB400']]
    ops.section('Fiber', int(i1), '-GJ', 1.0e10)
    [ops.fiber(eachItem[0], eachItem[1], eachItem[2], pylonUpperMatList[i1]) for i1 in range(len(pylonUpperList))
     for eachItem in pylonUpperList[i1]]
########################################################################################################################
##########################################---建立非线性单元---#############################################################
nonLinearPylonEle = np.loadtxt('modelInformation/nonLinerPylonEle.txt')
integrationPoint=5
for each in nonLinearPylonEle:
    EleTag = int(each[0])
    EleNodeI = int(each[1])
    EleNodeJ = int(each[2])
    EleGeomTransf = int(each[3])
    EleSection = int(each[4])
    opsX.element('nonlinearBeamColumn', EleTag, EleNodeI, EleNodeJ, integrationPoint,EleSection, EleGeomTransf)
########################################################################################################################
##########################################---建立横梁单元局部坐标转换---#####################################################
crossBeamTransf = np.loadtxt('modelInformation/newCrossBeamTransf.txt')
for each in crossBeamTransf:
    TransfTag = int(each[0])
    localZXCoord = float(each[1])
    localZYCoord = float(each[2])
    localZZCoord = float(each[3])
    ###---为了显示单元局部坐标轴,采用opsX,局部1,2,3采用红、绿、蓝表示
    opsX.geomTransf('PDelta', TransfTag, localZXCoord, localZYCoord, localZZCoord)
########################################################################################################################
##########################################---建立横梁单元---##############################################################
crossBeamEle = np.loadtxt('modelInformation/crossBeamEle.txt')
for each in crossBeamEle:
    EleTag = int(each[0])
    NodeI = int(each[1])
    NodeJ = int(each[2])
    A = float(each[3])
    E = float(each[4])
    G = float(each[5])
    J = float(each[6])
    Iy = float(each[7])
    Iz = float(each[8])
    Transf = int(each[9])
    opsX.element('elasticBeamColumn', EleTag, NodeI, NodeJ, A, E, G, J, Iy, Iz, Transf)
########################################################################################################################
##########################################---建立其他节点---##############################################################
otherNodes = np.loadtxt('modelInformation/newOtherNodes.txt')
for each in otherNodes:
    nodeTageValue = int(each[0])
    xCoordValue = float(each[1])
    yCoordValue = float(each[2])
    zCoordValue = float(each[3])
    nodeMassValue = float(each[4])
    ###---为了可视化采用opsX,参数跟ops中完全一致
    opsX.node(nodeTageValue, xCoordValue, yCoordValue, zCoordValue, '-mass', nodeMassValue, nodeMassValue,nodeMassValue, 0.0, 0.0, 0.0)
########################################################################################################################
##########################################---建立节点固接---##############################################################
fixList = [19000, 29000, 39000, 49000, 59000, 69000, 79000, 89000, 99000]
for each in fixList:
    ops.fix(int(each), 1, 1, 1, 1, 1, 1)
########################################################################################################################
##########################################---建立大刚度单元模拟固接---######################################################
equlDOF = np.loadtxt('modelInformation/equalDOF.txt')
for each in equlDOF:
    EleTag = int(each[0])
    NodeI = int(each[1])
    NodeJ = int(each[2])
    A = float(each[3])
    E = float(each[4])
    G = float(each[5])
    J = float(each[6])
    Iy = float(each[7])
    Iz = float(each[8])
    Transf = int(each[9])
    opsX.element('elasticBeamColumn', EleTag, NodeI, NodeJ, A, E, G, J, Iy, Iz, Transf)
########################################################################################################################
##########################################---建立支座单元---##############################################################
uniaxialMatExpre=[('ENT', 9000, 1.0E7),('Elastic', 8000, 1.0E8),('ElasticPP', 9001, 2.5E5, 0.002),
                  ('ElasticPP', 9002, 4.5E5, 0.002),('ElasticPP', 9003, 5.0E5, 0.002),('ElasticPP', 9004, 2.5E5, 0.002),
                  ('ElasticPP', 9005, 2.5E5, 0.002),('ElasticPP', 9006, 5.0E5, 0.002),('ElasticPP', 9007, 4.5E5, 0.002),
                  ('ElasticPP', 9008, 4.5E5, 0.002),('ElasticPP', 9009, 2.5E5, 0.002)]
[eval(f"ops.uniaxialMaterial{each}") for each in uniaxialMatExpre]
###############################
specialEleTransfList = []
brTraf = np.loadtxt('modelInformation/newBearingTransf.txt')
bearingEleNode=[(2301, 2301, 2302),(2401, 2401, 2402),(2101, 2101, 2102),(2201, 2201, 2202),(3101, 3101, 3102),
                (3201, 3201, 3202),(4101, 4101, 4102),(4201, 4201, 4202),(5101, 5101, 5102),(5201, 5201, 5202),
                (6101, 6101, 6102),(6201, 6201, 6202),(7101, 7101, 7102),(7201, 7201, 7202),(8101, 8101, 8102),
                (8201, 8201, 8202),(9101, 9101, 9102),(9201, 9201, 9202)]
materialTag=[(9000, 9001, 8000),(9000, 9001, 8000),(9000, 9002, 9002),(9000, 9002, 9002),(9000, 9003, 9003),
             (9000, 9003, 9003),(9000, 9004, 8000),(9000, 9004, 8000),(9000, 9005, 8000),(9000, 9005, 8000),
             (9000, 9006, 9006),(9000, 9006, 9006),(9000, 9007, 9007),(9000, 9007, 9007),(9000, 9008, 9008),
             (9000, 9008, 9008),(9000, 9009, 8000),(9000, 9009, 8000)]
beIn=[0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8]
for i1 in range(18):
    opsX.element('zeroLength', bearingEleNode[i1][0],bearingEleNode[i1][1],bearingEleNode[i1][2], '-mat',
                materialTag[i1][0],materialTag[i1][1],materialTag[i1][2], '-dir', 1, 2, 3, '-orient', 0, 0, 1,
                            brTraf[beIn[i1]][0], brTraf[beIn[i1]][1], brTraf[beIn[i1]][2])
##################---建立弹簧单元---#########################
springStiffnessName = [["U1_1", "U2_1", "U3_1", "R1_1", "R2_1", "R3_1"],
                       ["U1_2", "U2_2", "U3_2", "R1_2", "R2_2", "R3_2"],
                       ["U1_3", "U2_3", "U3_3", "R1_3", "R2_3", "R3_3"],
                       ["U1_4", "U2_4", "U3_4", "R1_4", "R2_4", "R3_4"],
                       ["U1_5", "U2_5", "U3_5", "R1_5", "R2_5", "R3_5"],
                       ["U1_6", "U2_6", "U3_6", "R1_6", "R2_6", "R3_6"],
                       ["U1_7", "U2_7", "U3_7", "R1_7", "R2_7", "R3_7"],
                       ["U1_8", "U2_8", "U3_8", "R1_8", "R2_8", "R3_8"],
                       ["U1_9", "U2_9", "U3_9", "R1_9", "R2_9", "R3_9"]]
stiffVal=[[4.92e6,4.73e6,1.01e7,1.42e9,2.82e8,6.91e8],
          [6.14e6,5.90e6,9.84e6,1.40e9,2.92e8,8.56e8],
          [1.3e7,1.27e7,2.12e7,3.14e9,1.13e9,2.06e9],
          [6.29e7,5.93e7,7.48e7,2.08e10,1.05e10,2.35e10],
          [4.72e7,4.45e7,8.7e7,2.38e10,1.18e10,1.77e10],
          [4.15e6,4.18e6,1.54e7,2.06e9,3.05e8,5.83e8],
          [4.43e6,4.46e6,1.54e7,2.06e9,3.06e8,6.20e8],
          [4.32e6,4.35e6,1.54e7,2.07e9,3.1e8,6.06e8],
          [4.6e6,4.63e6,1.54e7,2.07e9,3.15e8,6.43e8]]

brTraf = np.loadtxt('modelInformation/newBearingTransf.txt')
springEleNode=[(19000, 19000, 19001),(29000, 29000, 29001),(39000, 39000, 39001),(49000, 49000, 49001),
               (59000, 59000, 59001),(69000, 69000, 69001),(79000, 79000, 79001),(89000, 89000, 89001),
               (99000, 99000, 99001)]
specialEleTransfList = []
for i1 in range(9):
    numbers0 = opsX.auxiliary_materialReNumber(springStiffnessName[i1][0])
    ops.uniaxialMaterial('Elastic', numbers0, stiffVal[i1][0])
    numbers1 = opsX.auxiliary_materialReNumber(springStiffnessName[i1][1])
    ops.uniaxialMaterial('Elastic', numbers1, stiffVal[i1][1])
    numbers2 = opsX.auxiliary_materialReNumber(springStiffnessName[i1][2])
    ops.uniaxialMaterial('Elastic', numbers2, stiffVal[i1][2])
    numbers3 = opsX.auxiliary_materialReNumber(springStiffnessName[i1][3])
    ops.uniaxialMaterial('Elastic', numbers3, stiffVal[i1][3])
    numbers4 = opsX.auxiliary_materialReNumber(springStiffnessName[i1][4])
    ops.uniaxialMaterial('Elastic', numbers4, stiffVal[i1][4])
    numbers5 = opsX.auxiliary_materialReNumber(springStiffnessName[i1][5])
    ops.uniaxialMaterial('Elastic', numbers5, stiffVal[i1][5])
    opsX.element('zeroLength', springEleNode[i1][0],springEleNode[i1][1],springEleNode[i1][2], '-mat',
                numbers0,numbers1,numbers2,numbers3,numbers4,numbers5, '-dir', 1, 2,3, 4,5, 6,'-orient', 0, 0, 1,
                brTraf[i1][0], brTraf[i1][1], brTraf[i1][2]),
########################################################################################################################
# opsX.auxiliary_writeModelInformationToDB() ###---将模型信息写入数据库，以便在SAPBridge中显示模型
########################################################################################################################
##########################################---施加重力荷载---##############################################################
nodesTags=ops.getNodeTags()
nodesMass=[ops.nodeMass(each)[0] for each in nodesTags]
nodeList=[[node,mass] for node,mass in zip(nodesTags, nodesMass)]
ops.timeSeries('Linear', 1)
ops.pattern('Plain', 1, 1)
for each in nodeList:
    ops.load(int(each[0]), 0.0, 0.0, -each[1] * 9.81, 0.0, 0.0, 0.0)
########################################################################################################################
##########################################---记录响应---#################################################################
#######响应记录列表
###########for node, ('node', 'disp', [1, 2, 3])-(keyWord,responseType,nodeTagsList)
###########('node', 'disp', [1, 2, 3]), ('node', 'vel', [1, 2, 3]),('node','accel',[1,2,3]),
###########('node','reaction',[1,2,3])
###########对于truss单元-('trussEle','axialForce',[45001,45002,45003])-（keyword,responseType,eleTags)
###########('trussEle','axialDeform',[45001,45002,45003])
###########对于zeroLength单元，('zeroEle','deformation',[1,2,3],[2301,2101,3101])
##############################('zeroEle','localForce',[1,2,3],[2301,2101,3101])
###########对于nonLinearEle单元section，('nonEleSection','sectionForce',1,[41001, 41018, 41019])
###################('nonEleSection','sectionDeformation',1,[41001, 41018, 41019])
###########对于NonZero单元，('nonZeroEle','localForce',[41001, 41018, 41019])
girderNodeList = [each for each in range(1, 446)]
nodeRespList = [41129, 51125, 223]
pylonEleNumList = [41001, 41018, 41019, 41081, 41082, 51001, 51014, 51015, 51077, 51078, 11001, 11016, 21001, 21020,
                   31001, 31016, 61001, 61016, 71001, 71020, 81001, 81020, 91001, 91020]
cableEleList = [each for each in range(45001, 45039)] + [each for each in range(46001, 46039)]
BearingList = [2301, 2101, 3101, 4101, 5101, 6101, 7101, 8101, 9101]
recordList = [('node', 'disp', girderNodeList), ('node', 'disp', nodeRespList), ('node', 'accel', nodeRespList),
              ('trussEle', 'axialForce', cableEleList), ('zeroEle', 'deformation', [1, 2, 3], BearingList),
              ('zeroEle', 'localForce', [1, 2, 3], BearingList),
              ('nonEleSection', 'sectionForce', 1, pylonEleNumList),
              ('nonEleSection', 'sectionDeformation', 1, pylonEleNumList),
              ('nonZeroEle', 'localForce', [41001, 41018, 41019])]
########################################################################################################################
start=time()
opsX.auxiliary_writeModelInformationToDB() ###---将模型信息写入数据库，以便在SAPBridge中显示模型
end=time()
print("写入数据库时间为:",end-start)
########################################################################################################################
##########################################---重力分析---##################################################################
opsX.integration_analysisGravity(totalStep=1,recordList=None) ###---采用集成式方法进行自重分析(包装了自重分析相关命令)
########################################################################################################################
##########################################---模态分析---##################################################################
opsX.integration_analysisModal(numModes=50) ###---采用集成式方法进行自重分析(包装了模态分析相关命令)
####---opsX.integration_analysisModalProperties(numEigen=50,pflag=1,outname=None) ###---详细动力特性分析
########################################################################################################################
##########################################---时程分析---##################################################################
waveLength =7997
dt =0.005
waveNumber=1 ###---地震动编号，用于屏幕输出
acc_X = 'inputGroundMotion/horizontal/1.txt'
acc_Z = 'inputGroundMotion/vertical/1.txt'
recordList = [('node', 'disp', girderNodeList),('node', 'disp', nodeRespList),('node', 'accel', nodeRespList),
              ('node', 'vel', nodeRespList),('trussEle','axialForce',cableEleList),('trussEle','axialDeform',cableEleList),
              ('zeroEle','deformation',[1,2,3],BearingList),('zeroEle','localForce',[1,2,3],BearingList),
              ('nonEleSection','sectionForce',1,pylonEleNumList),('nonEleSection','sectionDeformation',1,pylonEleNumList),
              ('nonZeroEle','localForce',[41001, 41025])],
# opsX.integration_earthquakeExcite(RayleighDamping=['mode-1',dampingRatio,Tstart,Tend],waveLenth=length,dt=dt,
# 								  dirList=[1],motionList=[pathName],recordList=None)
#####----RayleighDamping=['mode-2',alphaM,betaK,betaKinit,betaKcommit],RayleighDamping=['mode-1',dampingRatio,Tstart,Tend]
opsX.integration_earthquakeExcite(['mode-1',0.03, 13.385, 0.206], waveLenth=waveLength,
                                     dt=dt, dirList=[1, 3], motionList=[acc_X, acc_Z],recordList=recordList,waveNumber=1)
########################################################################################################################
