#-*-coding: UTF-8-*-
#########################################################################
#  Author: Junjun Guo
#  E-mail: guojj@tongji.edu.cn/guojj_ce@163.com/guojj01@gmail.com
#  Environemet: Successfully executed in python 3.8
#  Date: 2021-08-12
#########################################################################
#import necessary modules
import numpy as np
import sys
import ezdxf  #ezdxf is a Python package to create new DXF files and read/modify/write existing DXF files
from itertools import chain
import math
from .sectionproperties.pre import sections
from .sectionproperties.analysis.cross_section import CrossSection
#########################################################################
def is_in_2d_polygon(point, vertices):
    """
    ---determine whether the point in the closed curved lines composed of vertices,anticlockwise for vertices---
    vertices:(closed polygon)[[0,0],[2,0],[2,1],[1,1],[1,2],[2,2],[2,3],[0,3],[0,0]]
    point:[1.01,1.01]
    """
    px = point[0]
    py = point[1]
    angle_sum = 0

    size = len(vertices)
    if size < 3:
        raise ValueError("len of vertices < 3")
    j = size - 1
    for i in range(0, size):
        sx = vertices[i][0]
        sy = vertices[i][1]
        tx = vertices[j][0]
        ty = vertices[j][1]
        #determine whether the node in a line based on the distance from the node to the line
        # y = kx + b, -y + kx + b = 0
        k = (sy - ty) / (sx - tx + 0.000000000001)  # avoid divide zero
        b = sy - k * sx
        dis = np.abs(k * px - 1 * py + b) / np.sqrt(k * k + 1)
        if dis < 0.000001:  #the node in the line
            if sx <= px <= tx or tx <= px <= sx:  #the node in the line
                return True
        #calculate the angle
        angle = math.atan2(sy - py, sx - px) - math.atan2(ty - py, tx - px)
        #the angle shoule with [-pi,pi]
        if angle >= math.pi:
            angle = angle - math.pi * 2
        elif angle <= -math.pi:
            angle = angle + math.pi * 2
        #cumulation
        angle_sum += angle
        j = i
    #calculate the diffrence between the sum angles and 2pi with a small threshold
    return np.abs(angle_sum - math.pi * 2) < 0.00000000001
#########################################################################

#########################################################################
class Sample():
    """
    ---uniform sample class---
    for example:
    N = 100
    bounds=[(50,250),(1,14)]
    instance=Sample(bounds,N)
    results=instance.LHSample()
    """
    def __init__(self, bounds, N):
        """
        initial data
        bounds: variable bounds, such as bounds=[(10,21),(21,34)]
        N:sample numbers
        """
        self.bounds = bounds
        self.N = N
        self.D = len(self.bounds)

    def LHSample(self):
        result = np.empty([self.N, self.D])
        temp = np.empty([self.N])
        d = 1.0 / self.N

        for i in range(self.D):

            for j in range(self.N):
                temp[j] = np.random.uniform(
                    low=j * d, high=(j + 1) * d, size=1)[0]

            np.random.shuffle(temp)

            for j in range(self.N):
                result[j, i] = temp[j]

        b = np.array(self.bounds)
        lower_bounds = b[:, 0]
        upper_bounds = b[:, 1]
        if np.any(lower_bounds > upper_bounds):
            print("The parameters low bound value should smaller than the upper bound!")
            return

        #   sample * (upper_bound - lower_bound) + lower_bound
        np.add(np.multiply(result,
                           (upper_bounds - lower_bounds),
                           out=result),
               lower_bounds,
               out=result)

        return result
#########################################################################

#########################################################################
class SecPropertyCalDxfPy():
    """
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

    """
    def __init__(self,dxfFileName,numCircleSeg=20,numArcSeg=10,numEllipseSeg=20,
                 numSplineSeg=20):
        """
        ---Initialize the class---
        dxfFileName:the full path of the dxf file,for example-
        "F:\pythonInteractSAP2000\circle.dxf"
        numCircleSeg(int)-the total number of lines approximate a circle
        numArcSe(int)-the total number of lines approximate an arc
        numEllipseSeg(int)-the total number of lines approximate an ellipse
        numEllipseArcSeg(int)-the total number of lines approximate an ellipse arc
        """
        self.dxfFileName=dxfFileName
        try:
            self.doc = ezdxf.readfile(self.dxfFileName)
        except IOError:
            print(f'Not a DXF file or a generic I/O error.')
            sys.exit(1)
        except ezdxf.DXFStructureError:
            print(f'Invalid or corrupted DXF file.')
            sys.exit(2)
        self.msp=self.doc.modelspace()

        self.numCircleSeg=numCircleSeg #the total number of lines approximate a circle
        self.numArcSeg=numArcSeg # the total number of lines approximate an arc
        self.numEllipseSeg=numEllipseSeg #the total number of lines approximate an ellipse
        self.numSplineSeg=numSplineSeg #the total number of lines approximate spline between two knots
    def _anticlockSortPoint(self,setPointList,pointPairList,pointCoordDict):
        """
        ---Anticolck sorting points in a loop---
        setPointList:[0,1,2,3...]
        pointPairList:[[0,1],[1,2],...]
        pointCoordList:{0:[0.123,3.456],1:[45.342,67.897]}
        """
        zValues=[pointCoordDict[each][1] for each in setPointList]
        zMinIndex=zValues.index(min(zValues))
        startP=setPointList[zMinIndex]
        linkTwoP=[each for each in pointPairList if startP in each]
        x0,y0=pointCoordDict[startP][0],pointCoordDict[startP][1]
        setList=list(set(list(chain(*linkTwoP))))
        linkP=[each for each in setList if each!=startP]
        x1,y1=pointCoordDict[linkP[0]][0],pointCoordDict[linkP[0]][1]
        x2, y2 = pointCoordDict[linkP[1]][0], pointCoordDict[linkP[1]][1]
        angle1=math.atan2(y1-y0,x1-x0)
        angle2=math.atan2(y2-y0,x2-x0)
        if angle1<0:
            angle1=angle1*180/3.14159+360
        else:
            angle1=angle1*180/3.14159
        if angle2 < 0:
            angle2 = angle2 * 180 / 3.14159 + 360
        else:
            angle2 = angle2 * 180 / 3.14159
        if angle1>angle2:
            nextP=linkP[1]
        else:
            nextP=linkP[0]
        sortedPList=[]
        sortedPList.append(startP)
        sortedPList.append(nextP)
        for i2 in range(len(setPointList)-2):
            select=[each for each in pointPairList if sortedPList[-1] in each]
            finalSelect=[ each for each in select if not (set(each).issubset(set(sortedPList)))]
            finalValue=[each2 for each2 in finalSelect[0] if each2!=sortedPList[-1]]
            sortedPList.append(finalValue[0])
        return sortedPList

    def _outLoopDetermine(self,sortedLoopList,pointCoordDict):
        """
        ___Determine the outloop of the section ___
        """
        yMaxMin=[pointCoordDict[i1][0] for i1 in range(len(pointCoordDict))]
        yMax,yMin=max(yMaxMin),min(yMaxMin)
        zMaxMin = [pointCoordDict[i1][1] for i1 in range(len(pointCoordDict))]
        zMax, zMin = max(zMaxMin), min(zMaxMin)
        outSortList=None
        innerSortList=[]
        for each in sortedLoopList:
            eachY=[pointCoordDict[item1][0] for item1 in each]
            eachZ = [pointCoordDict[item1][1] for item1 in each]
            if (yMax in eachY) and (zMax in eachZ):
                outSortList=each
            else:
                innerSortList.append(each)
        return outSortList,innerSortList

    def pointPosDetermine(self,outSortList,innerSortList,pointCoordDict):
        """
        ---Determine a point whether in a region or not---
        """
        numSample=1000
        yzOut = [pointCoordDict[outSortList[i1]] for i1 in range(len(outSortList))]
        yOut=[each1[0] for each1 in yzOut]
        zOut=[each2[1] for each2 in yzOut]
        ymin,ymax=min(yOut),max(yOut)
        zmin,zmax=min(zOut),max(zOut)
        outBounds=[(ymin,ymax),(zmin,zmax)]
        instance = Sample(outBounds, numSample)
        results = instance.LHSample()
        yzOut.append(yzOut[0])
        outVerticeList=yzOut
        InnerVerticeList=[]
        Holes=[]
        for each in innerSortList:
            yzInner = [pointCoordDict[each[i1]] for i1 in range(len(each))]
            yzInner.append(yzInner[0])
            InnerVerticeList.append(yzInner)
        holesList=[]
        for eachInnner in InnerVerticeList:
            for eachSample in results:
                eachSample=[round(eachSample[0],3),round(eachSample[1],3)]
                logicValue=is_in_2d_polygon(eachSample, eachInnner)
                if logicValue==True:
                    holesList.append(list(eachSample))
                    break
        controlP=None
        for eachSample in results:
           eachSample = [round(eachSample[0], 3), round(eachSample[1], 3)]
           logicValueOut= is_in_2d_polygon(eachSample, outVerticeList)
           logicValueInnerList=[]
           for eachInner in InnerVerticeList:
               logicValueInner1 = is_in_2d_polygon(eachSample, eachInner)
               logicValueInnerList.append(logicValueInner1)
           if (logicValueOut==True) and (True not in logicValueInnerList):
               controlP=eachSample
               break
           else:
               continue
        return controlP,holesList

    def _getLayerObject(self,layerName):
        """
        ---Get the line object from layer in CAD---
        """
        try:
            layer = self.doc.layers.get(layerName)
        except ezdxf.lldxf.const.DXFTableEntryError:
            print(f'{layerName} layer not exists!')
            sys.exit(1)

        points = []
        eachLineIJCoord = []

        numCircleSeg=self.numCircleSeg
        numArcSeg=self.numArcSeg
        numEllipseSeg=self.numEllipseSeg
        numSplineSeg=self.numSplineSeg
        Entity = self.msp.query(f"""*[layer=="{layerName}"]""")
        finalsValue=[each for each in Entity]
        #####################################
        # process spline object
        try:
            splineEntity = self.msp.query(f"""SPLINE[layer=="{layerName}"]""")
            for each in splineEntity:
                pointsList = []
                pointVector = [eachValue for eachValue in each.flattening(1e8,numSplineSeg)]
                for eachPoints in pointVector:
                    pointsList.append([round(eachPoints[0], 6), round(eachPoints[1], 6)])
                    points.append([round(eachPoints[0], 6), round(eachPoints[1], 6)])
                for i2 in range(len(pointsList)):
                    startP = [round(pointsList[i2][0], 6), round(pointsList[i2][1], 6)]
                    endP = [round(pointsList[i2 + 1][0], 6), round(pointsList[i2 + 1][1], 6)]
                    eachLineIJCoord.append([startP, endP])
        except:
            pass
        #####################################
        # process ellipse object
        try:
            ellipseEntity = self.msp.query(f"""ELLIPSE[layer=="{layerName}"]""")
            for each in ellipseEntity:
                pointsList=[]
                pointVector=[eachValue for eachValue in each.flattening(1e8,numEllipseSeg)]
                for eachPoints in pointVector:
                    pointsList.append([round(eachPoints[0], 6), round(eachPoints[1], 6)])
                    points.append([round(eachPoints[0], 6), round(eachPoints[1], 6)])
                for i2 in range(len(pointsList)):
                    startP = [round(pointsList[i2][0], 6), round(pointsList[i2][1], 6)]
                    endP = [round(pointsList[i2 + 1][0], 6), round(pointsList[i2 + 1][1], 6)]
                    eachLineIJCoord.append([startP, endP])
        except:
            pass
        #####################################
        # process circle object
        try:
            circleEntity = self.msp.query(f"""CIRCLE[layer=="{layerName}"]""")
            for each in circleEntity:
                centerPoint=each.dxf.center
                radius=each.dxf.radius
                deltaAngle=360.0/numCircleSeg
                circlePointList=[]
                for i1 in range(numCircleSeg):
                    sinValue=math.sin(i1*deltaAngle*3.1415926/180.0)
                    cosValue = math.cos(i1 * deltaAngle * 3.1415926 / 180.0)
                    pointY=centerPoint[0]+radius*cosValue
                    pointZ=centerPoint[1]+radius*sinValue
                    circlePointList.append([round(pointY,6),round(pointZ,6)])
                    points.append([round(pointY,6),round(pointZ,6)])
                circlePointList.append(circlePointList[0])
                points.append(circlePointList[0])
                for i2 in range(len(circlePointList)-1):
                    startP=[round(circlePointList[i2][0], 6), round(circlePointList[i2][1], 6)]
                    endP = [round(circlePointList[i2+1][0], 6), round(circlePointList[i2+1][1], 6)]
                    eachLineIJCoord.append([startP,endP])
        except:
            pass
        #####################################
        # process arc object
        try:
            arcEntity = self.msp.query(f"""ARC[layer=="{layerName}"]""")
            for each in arcEntity:
                centerPoint=each.dxf.center
                arcRadius=each.dxf.radius
                arcStartPoint=each.start_point
                arcEndPoint=each.end_point
                arcStartAngle=each.dxf.start_angle
                arcEndAngle=each.dxf.end_angle
                deltaAngle=(arcEndAngle-arcStartAngle)/numArcSeg
                arcPointList = []
                arcPointList.append([round(arcStartPoint[0],6),round(arcStartPoint[1],6)])
                for i3 in range(numArcSeg):
                    angles=(arcStartAngle+(i3+1)*deltaAngle)
                    sinValue = math.sin(angles * 3.1415926 / 180.0)
                    cosValue = math.cos(angles * 3.1415926 / 180.0)
                    pointY = centerPoint[0] + arcRadius * cosValue
                    pointZ = centerPoint[1] + arcRadius * sinValue
                    arcPointList.append([round(pointY,6),round(pointZ,6)])
                    points.append([round(pointY, 6), round(pointZ, 6)])
                arcPointList.append([round(arcEndPoint[0],6),round(arcEndPoint[1],6)])
                for i4 in range(len(arcPointList)-1):
                    startP = [round(arcPointList[i4][0], 6), round(arcPointList[i4][1], 6)]
                    endP = [round(arcPointList[i4 + 1][0], 6), round(arcPointList[i4 + 1][1], 6)]
                    eachLineIJCoord.append([startP, endP])
        except:
            pass
        #####################################
        # process LWPOLYLINE object
        try:
            LWPolineEntity=self.msp.query(f"""LWPOLYLINE[layer=="{layerName}"]""")
            for each in LWPolineEntity:
                LWPoints = [items for items in each.vertices_in_wcs()]
                for each1 in LWPoints:
                    points.append([round(each1[0], 6), round(each1[1], 6)])
                if each.dxf.flags==1:#polyline is closed
                    for i1 in range(len(LWPoints) - 1):
                        startP = [round(LWPoints[i1][0], 6), round(LWPoints[i1][1], 6)]
                        endP = [round(LWPoints[i1 + 1][0], 6), round(LWPoints[i1 + 1][1], 6)]
                        eachLineIJCoord.append([startP, endP])
                    startP1 = [round(LWPoints[-1][0], 6), round(LWPoints[-1][1], 6)]
                    endP1 = [round(LWPoints[0][0], 6), round(LWPoints[0][1], 6)]
                    eachLineIJCoord.append([startP1, endP1])
                else:
                    for i1 in range(len(LWPoints)-1):
                        startP=[round(LWPoints[i1][0], 6), round(LWPoints[i1][1], 6)]
                        endP = [round(LWPoints[i1+1][0], 6),round(LWPoints[i1+1][1], 6)]
                        eachLineIJCoord.append([startP,endP])
        except:
            pass
        #####################################
        # process LINE object
        try:
            lines = self.msp.query(f"""LINE[layer=="{layerName}"]""")
            for eachLine in lines:
                startP = eachLine.dxf.start
                endP = eachLine.dxf.end
                points.append([round(startP[0], 6), round(startP[1], 6)])
                points.append([round(endP[0], 6), round(endP[1], 6)])
            for eachLine in lines:
                startP = [round(eachLine.dxf.start[0], 6), round(eachLine.dxf.start[1], 6)]
                endP = [round(eachLine.dxf.end[0], 6), round(eachLine.dxf.end[1], 6)]
                eachLineIJCoord.append([startP, endP])
        except:
            pass
        #####################################
        filtPoints=[]
        for each1 in points:
            if each1 not in filtPoints:
                filtPoints.append(each1)
        pointsDict={i1:filtPoints[i1] for i1 in range(len(filtPoints))}
        new_dict = {str(v) : k for k, v in pointsDict.items()}
        eachLineIJ=[]
        for eachLine in eachLineIJCoord:
            PI=new_dict[str(eachLine[0])]
            PJ = new_dict[str(eachLine[1])]
            eachLineIJ.append([int(PI),int(PJ)])

        pointKeys=pointsDict.keys()
        loopList=[]
        while (len(eachLineIJ)!=0):
            iterloop=[]
            iterloop=[eachLineIJ[0]]
            eachLineIJ.remove(eachLineIJ[0])
            while len(set(list(chain(*iterloop)))&set(list(chain(*eachLineIJ))))!=0: #&--sets interaction
                for each1 in eachLineIJ:
                    if len(set(list(chain(*iterloop)))&set(each1))!=0:#&--sets interaction
                        iterloop.append(each1)
                        eachLineIJ.remove(each1)
            loopList.append(iterloop)
        loopPointList=[]
        for each in loopList:
            eachLoop=list(set(list(chain(*each))))
            loopPointList.append(eachLoop)
        #anticlock sort points
        antiSortPList=[]
        for i1 in range(len(loopList)):
            antiSortP=self._anticlockSortPoint(loopPointList[i1], loopList[i1],pointsDict)
            antiSortPList.append(antiSortP)
        outSortList,innerSortList=self._outLoopDetermine(antiSortPList,pointsDict)
        controlP,holesList=self.pointPosDetermine(outSortList,innerSortList,pointsDict)

        return pointsDict,outSortList,innerSortList,controlP,holesList

    def controlPointDetermine(self,outSortList,pointsDict):
        """
        ---Determine the control point of a solid section ---
        """
        numSample = 1000
        yzOut = [pointsDict[outSortList[i1]] for i1 in range(len(outSortList))]
        yOut = [each1[0] for each1 in yzOut]
        zOut = [each2[1] for each2 in yzOut]
        ymin, ymax = min(yOut), max(yOut)
        zmin, zmax = min(zOut), max(zOut)
        outBounds = [(ymin, ymax), (zmin, zmax)]
        instance = Sample(outBounds, numSample)
        results = instance.LHSample()
        yzOut.append(yzOut[0])
        outVerticeList = yzOut
        controlP = None
        for eachSample in results:
            eachSample1 = [round(eachSample[0], 6), round(eachSample[1],6)]
            logicValueOut = is_in_2d_polygon(eachSample1, outVerticeList)
            if (logicValueOut == True):
                controlP = eachSample
                break
            else:
                continue
        return controlP

    def _getLayerSolidPolygon(self,layerName):
        """
        ---Take out the line object of the solid polygon in CAD---
        """
        try:
            layer=self.doc.layers.get(layerName)
        except ezdxf.lldxf.const.DXFTableEntryError:
            print(f'{layerName} layer not exists!')
            sys.exit(1)
        lines = self.msp.query(f"""LINE[layer=="{layerName}"]""")
        points=[]
        for eachLine in lines:
            startP=eachLine.dxf.start
            endP=eachLine.dxf.end
            points.append([round(startP[0],6),round(startP[1],6)])
            points.append([round(endP[0],6),round(endP[1],6)])
        filtPoints=[]
        for each1 in points:
            if each1 not in filtPoints:
                filtPoints.append(each1)
        pointsDict={i1:filtPoints[i1] for i1 in range(len(filtPoints))}
        new_dict = {str(v) : k for k, v in pointsDict.items()}
        eachLineIJ=[]
        for eachLine in lines:
            startP = [round(eachLine.dxf.start[0],6),round(eachLine.dxf.start[1],6)]
            endP=[round(eachLine.dxf.end[0],6),round(eachLine.dxf.end[1],6)]
            PI=new_dict[str(startP)]
            PJ=new_dict[str(endP)]
            eachLineIJ.append([int(PI),int(PJ)])
        pointKeys=pointsDict.keys()
        loopList=[]
        while (len(eachLineIJ)!=0):
            iterloop=[]
            iterloop=[eachLineIJ[0]]
            eachLineIJ.remove(eachLineIJ[0])
            while len(set(list(chain(*iterloop)))&set(list(chain(*eachLineIJ))))!=0:
                    for each1 in eachLineIJ:
                        if len(set(list(chain(*iterloop)))&set(each1))!=0:
                            iterloop.append(each1)
                            eachLineIJ.remove(each1)
            loopList.append(iterloop)
        loopPointList=[]
        for each in loopList:
            eachLoop=list(set(list(chain(*each))))
            loopPointList.append(eachLoop)
        #anticlock sort points
        antiSortPList=[]
        for i1 in range(len(loopList)):
            antiSortP=self._anticlockSortPoint(loopPointList[i1], loopList[i1],pointsDict)
            antiSortPList.append(antiSortP)
        outSortList, innerSortList = self._outLoopDetermine(antiSortPList, pointsDict)
        controlP=self.controlPointDetermine(outSortList,pointsDict)
        return pointsDict,outSortList,controlP

    def _scaleAndShiftNodes(self,points,holes,control_points,scaleFactor):
        """---scale and shift the section nodes---"""
        yValuesMin = min([each[0] for each in points])
        zValuesMin = min([each[1] for each in points])
        shiftY, shiftZ = (0 - yValuesMin), (0 - zValuesMin)
        scaleShiftPoints = [[round((each[0] + shiftY)/scaleFactor, 3), round((each[1] + shiftZ)/scaleFactor, 3)]
                            for each in points]
        scaleShiftHoles = [[round((each[0] + shiftY)/scaleFactor, 3), round((each[1]+ shiftZ)/scaleFactor, 3)]
                           for each in holes]
        scaleShiftControlPoint = [[round((each[0] + shiftY)/scaleFactor, 3), round((each[1]+ shiftZ)/scaleFactor, 3)]
                                  for each in control_points]
        return scaleShiftPoints, scaleShiftHoles, scaleShiftControlPoint

    def _scaleAndShiftNodesSolid(self,points,control_points,scaleFactor):
        """
        ---scale and shift the solid section nodes---
        """
        # scalePoints = [[each[0] * scaleFactor, each[1] * scaleFactor] for each in points]
        # yValuesMin = min([each[0] for each in scalePoints])
        # zValuesMin = min([each[1] for each in scalePoints])
        # shiftY, shiftZ = (0 - yValuesMin), (0 - zValuesMin)
        # scaleShiftPoints = [[round(each[0] + shiftY, 3), round(each[1] + shiftZ, 3)] for each in scalePoints]
        # scaleShiftControlPoint = [[round(each[0] * scaleFactor + shiftY, 3), round(each[1] * scaleFactor + shiftZ, 3)]
        #                           for each in control_points]
        # return scaleShiftPoints, scaleShiftControlPoint

        # scalePoints = [[each[0] * scaleFactor, each[1] * scaleFactor] for each in points]
        yValuesMin = min([each[0] for each in points])
        zValuesMin = min([each[1] for each in points])
        shiftY, shiftZ = (0 - yValuesMin), (0 - zValuesMin)
        ShiftPoints = [[round(each[0] + shiftY, 3), round(each[1] + shiftZ, 3)] for each in points]
        scaleShiftPoints=[[round(each[0]/scaleFactor, 3), round(each[1]/scaleFactor, 3)] for each in ShiftPoints]
        scaleShiftControlPoint = [[round((each[0]+ shiftY)/scaleFactor, 3), round((each[1]+ shiftZ)/scaleFactor, 3)]
                                  for each in control_points]
        return scaleShiftPoints, scaleShiftControlPoint


    def getSectionProperty(self,layerName,scaleFactor=1,meshSize=0.1):
        """
        ---return the cross sectional properties of the polygon in certain layer---
        layerName: the layer name that the line objects ploted
        meshSize: the maximum size of the meshed element
        scaleFactor: the sacle factor equals to the length in CAD divides measure scaling factor and the converted size
        return:
        [A, Iyy, Izz, J, Cy, Cz]
        A-Cross-sectional area
        Iyy-Second moments of area about the global y axis
        Izz-Second moments of area about the global z axis
        J-Torsion constant
        Cy,Cz-the relative distance between elastic centroid and (ymin,zmin)
        """
        outAntiNodesList=None
        innerAntiNodesList=None
        sortNodesList=None
        try:
            pointsDict,outSortList,innerSortList,controlP,holesList=self._getLayerObject(layerName)
            outAntiNodesList=outSortList
            innerAntiNodesList=innerSortList
            points=[pointsDict[i1] for i1 in range(len(pointsDict))]
            facets=[]
            for i2 in range(len(outSortList)):
                try:
                    facets.append([outSortList[i2],outSortList[i2+1]])
                except IndexError:
                    facets.append([outSortList[i2],outSortList[0]])
            for eachLoop in innerSortList:
                for i3 in range(len(eachLoop)):
                    try:
                        facets.append([eachLoop[i3], eachLoop[i3 + 1]])
                    except IndexError:
                        facets.append([eachLoop[i3], eachLoop[0]])
            holes = holesList
            control_points = [controlP]
            perimeter = outSortList
            points, holes, control_points = self._scaleAndShiftNodes(points, holes, control_points, scaleFactor)
            sortNodesList=points

        except:
            self._getLayerSolidPolygon(layerName)
            pointsDict,outSortList,controlP=self._getLayerSolidPolygon(layerName)
            outAntiNodesList = outSortList
            holesList=[]
            points = [pointsDict[i1] for i1 in range(len(pointsDict))]
            facets = []
            for i2 in range(len(outSortList)):
                try:
                    facets.append([outSortList[i2], outSortList[i2 + 1]])
                except IndexError:
                    facets.append([outSortList[i2], outSortList[0]])
            holes = holesList
            control_points = [controlP]
            perimeter = outSortList
            points,control_points=self._scaleAndShiftNodesSolid(points, control_points, scaleFactor)
            sortNodesList = points
        geometry=sections.CustomSection(points,facets,holes,control_points,perimeter)
        geometry.plot_geometry()
        meshSize=meshSize*1
        mesh=geometry.create_mesh(mesh_sizes=[meshSize])
        section= CrossSection(geometry, mesh)
        section.plot_mesh()
        # section.display_mesh_info()
        section.calculate_geometric_properties(time_info=False)
        section.calculate_warping_properties(time_info=False)
        # section.calculate_plastic_properties(time_info=False)
        area=section.get_area() #cross section area
        ixx_c,iyy_c,_=section.get_ic() #second moments of area centroidal axis
        j=section.get_j() #St.Venant torsion constant
        A_sx,A_sy=section.get_As() #shear area for loading about the centroidal axix
        qx,qy=section.get_q() #first moment of area about the global axis
        cx,cy=section.get_c() #elastic centroid
        sectA=round(area,6)
        sectIyy=round(ixx_c,9)
        sectIzz=round(iyy_c,9)
        sectCenterY=round(cx,3)
        sectCenterZ=round(cy,3)

        yPoints = [each[0] for each in points]
        zPoints=[each[1] for each in points]
        ymin,zmin=min(yPoints),min(zPoints)
        centerYDisp=sectCenterY-ymin #the elastic center Y relative to minimum y coordinate
        centerZDisp=sectCenterZ-zmin #the elastic center Z relative to minimum z coordinate
        return sectA,sectIyy,sectIzz,j,centerYDisp,centerZDisp,sortNodesList,outAntiNodesList,innerAntiNodesList

#########################################################################
if __name__ == '__main__':
    #############################################
    ###---section properties calculation---
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


