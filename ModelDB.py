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
import records
########################################################################################################################
class ModelDB(object):
    """保存模型信息到数据库"""
    def __init__(self,dbPath):
        """
        初始化数据库
        输入:
        dbPath(str)-数据库路径及名称
        """
        self._dbPath=dbPath

    def initDB(self,dbPath):
        """初始化数据库"""
        self.db=records.Database('sqlite:///'+dbPath)
        tableNames=self.db.get_table_names()
        for each in tableNames:
            self.db.query("DROP TABLE IF EXISTS "+each)
        import sqlite3
        con = sqlite3.connect(dbPath)  # Open the database in sqlite
        con.execute("VACUUM")  # Execute the vacuum command
        con.close()  # Close the database

    def saveSectDB(self,tableName,sectName,values):
        """
        ---将截面特性结果保存到数据库---
        tableName(str)-表名
        sectName(str)-截面名称
        values(list)-保存的值,[A,Iyy,Izz,J,Cy,Cz]
        """
        db=records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        saveDict={'sectTag':sectName,'A':values[0],'Iyy':values[1],'Izz':values[2],'J':values[3],'Cy':values[4],
                  'Cz':values[5]}
        nodesTable = f"""
                                CREATE TABLE IF NOT EXISTS
                                {tableName}(
                                sectTag MESSAGE_TEXT PRIMARY KEY NOT NULL,
                                A REAL  NOT NULL,
                                Iyy REAL  NOT NULL,
                                Izz REAL  NOT NULL,
                                J REAL NOT NULL,
                                Cy REAL NOT NULL,
                                Cz REAL NOT NULL);"""
        db.query(nodesTable)  # 创建列表
        insertNodes = f"""
                                INSERT OR REPLACE INTO
                                {tableName}(sectTag,A,Iyy,Izz,J,Cy,Cz)
                                values (:sectTag,:A,:Iyy,:Izz,:J,:Cy,:Cz) """  # values中的tags等为实参,nodes中为形参
        db.bulk_query(insertNodes, saveDict)
        db = records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        db.close()

    def getSectDB(self,tableName,sectName):
        """
        ---获取截面特性函数---
        tableName(str)-表名
        sectName(str)-截面名称
        """

        db = records.Database('sqlite:///' + self._dbPath)
        conn = db.get_connection()  # connect to the sqlite database
        try:
            queryValue = conn.query(f'''select * from {tableName} where sectTag="{sectName}";''')
            returnValue = queryValue.all(as_dict=True)  # return samples as dict list
            return returnValue
        except:
            print("Something is wrong!")
            return

    def saveNodes(self,nodesList):
        """
        ---保存模型节点到模型数据库,[[nodeTag,nodeNumber,xCoord,yCoord,zCoord],]---
        """
        db = records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        db.query("DROP TABLE IF EXISTS modelNodes")

        nodesDict = [{'nodeTag': str(each[0]),'nodeNumber':int(each[1]), 'Coords': str(each[2:])} for each in nodesList]
        nodesTable = """
                                CREATE TABLE IF NOT EXISTS
                                modelNodes(
                                nodeTag MESSAGE_TEXT NOT NULL,
                                nodeNumber INT NOT NULL,
                                Coords MESSAGE_TEXT NOT NULL);"""
        db.query(nodesTable)  # 创建列表
        insertNodes = """
                                INSERT INTO
                                modelNodes(nodeTag,nodeNumber,Coords)
                                values (:nodeTag,:nodeNumber,:Coords) """  # values中的tags等为实参,nodes中为形参
        db.bulk_query(insertNodes, nodesDict)
        db = records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        db.close()

    def getNodes(self):
        """
        ---返回模型节点字典---
        """
        db = records.Database('sqlite:///' + self._dbPath)
        conn = db.get_connection()  # connect to the sqlite database
        try:
            queryValue = conn.query('select * from modelNodes;')
            returnValue = queryValue.all(as_dict=True)  # return samples as dict list
            return returnValue
        except:
            print(f'''table modelNodes doesn't exitst!''')
            return

    def saveEles(self,elesList):
        """
        ---保存模型单元,[[eleTag,eleNumber,nodeITag,nodeJTag],]---
        """
        db = records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        db.query("DROP TABLE IF EXISTS modelEles")
        nodesDict = [{'eleTag': str(each[0]), 'eleNumber': int(each[1]), 'nodeITag': str(each[2]),'nodeJTag':str(each[3])}
                     for each in elesList]
        nodesTable = """
                                        CREATE TABLE IF NOT EXISTS
                                        modelEles(
                                        eleTag MESSAGE_TEXT NOT NULL,
                                        eleNumber INT NOT NULL,
                                        nodeITag MESSAGE_TEXT NOT NULL,
                                        nodeJTag MESSAGE_TEXT NOT NULL);"""
        db.query(nodesTable)  # 创建列表
        insertNodes = """
                                        INSERT INTO
                                        modelEles(eleTag,eleNumber,nodeITag,nodeJTag)
                                        values (:eleTag,:eleNumber,:nodeITag,:nodeJTag) """  # values中的tags等为实参,nodes中为形参
        db.bulk_query(insertNodes, nodesDict)
        db = records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        db.close()

    def getEles(self):
        """
        ---返回模型单元字典---
        """
        db = records.Database('sqlite:///' + self._dbPath)
        conn = db.get_connection()  # connect to the sqlite database
        try:
            queryValue = conn.query('select * from modelEles;')
            returnValue = queryValue.all(as_dict=True)  # return samples as dict list
            return returnValue
        except:
            print(f'''table modelEles doesn't exitst!''')
            return

    def saveFEMNodes(self,tableName,nodesList):
        """
        ---保存有限元模型节点信息---
        tableName(str)-表名称
        nodesList=[[nodeTag,x,y,z,nodeMass],]
        """
        db = records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        saveDict = [{'nodeTag':str(eachNode[0]), 'X':float(eachNode[1]), 'Y':float(eachNode[2]),
                     'Z':float(eachNode[3]), 'mass':float(eachNode[4])} for eachNode in nodesList]
        nodesTable = f"""
                                        CREATE TABLE IF NOT EXISTS
                                        {tableName}(
                                        nodeTag MESSAGE_TEXT PRIMARY KEY NOT NULL,
                                        X REAL  NOT NULL,
                                        Y REAL  NOT NULL,
                                        Z REAL  NOT NULL,
                                        mass REAL NOT NULL);"""
        db.query(nodesTable)  # 创建列表
        insertNodes = f"""
                                        INSERT OR REPLACE INTO
                                        {tableName}(nodeTag,X,Y,Z,mass)
                                        values (:nodeTag,:X,:Y,:Z,:mass) """  # values中的tags等为实参,nodes中为形参
        db.bulk_query(insertNodes, saveDict)
        db = records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        db.close()

    def getFEMResults(self, tableName):
        """
        ---返回表tableName所有值---
        tableName(str)-节点表名称
        """
        db = records.Database('sqlite:///' + self._dbPath)
        conn = db.get_connection()  # connect to the sqlite database
        try:
            queryValue = conn.query(f'''select * from {tableName};''')
            returnValue = queryValue.all(as_dict=True)  # return samples as dict list
            return returnValue
        except:
            print(f'''table {tableName} doesn't exitst!''')
            return

    def getRowValue(self,tableName,primaryKeyName):
        """
        ---获取一行值---
        tableName(str)-表名称
        primaryKeyName(str)-关键字取值
        """
        db = records.Database('sqlite:///' + self._dbPath)
        conn = db.get_connection()  # connect to the sqlite database
        try:
            keyName=None
            primaryKeyDict = conn.query(f'''select * from pragma_table_info("{tableName}");''')
            for each in primaryKeyDict:
                if each['pk']==1:
                    keyName=each['name']
            queryValue = conn.query(f'''select * from {tableName} where "{keyName}"="{primaryKeyName}";''')
            returnValue = queryValue.all(as_dict=True)  # return samples as dict list
            return returnValue
        except:
            print(f'''table {tableName} doesn't exitst!''')
            return

    def updateRowValue(self,tableName,primaryKeyName,updateDict):
        """
        ---更新行指定列值---
        tableName(str)-表名称
        primaryKeyName(str)-关键字取值
        updateDict(dict)-需要更新的列值字典,{key1:value1,key2:value2,...}
        """
        db = records.Database('sqlite:///' + self._dbPath)
        conn = db.get_connection()  # connect to the sqlite database
        updateStr=""
        for eachItem in updateDict:
            updateStr+=eachItem+"="+str(updateDict[eachItem])+","
        addStr=updateStr.rsplit(",",1)[0]
        keyName = None
        primaryKeyDict = conn.query(f'''select * from pragma_table_info("{tableName}");''')
        for each in primaryKeyDict:
            if each['pk'] == 1:
                keyName = each['name']
        queryValue = conn.query(f'''UPDATE {tableName} SET {addStr} WHERE "{keyName}"="{primaryKeyName}";''')

    def saveFEM_elasticBeamColumn_eles(self,tableName,elesList):
        """
        ---保存elastciBeamColumn单元信息到模型数据库---
        tableName(str)-表名称
        elesList(list)-单元属性列表,[[eleTag,nodeI,nodeJ,A,E,G,J,Iy,Iz,Transf],...]
        """
        db = records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        saveDict = [{'eleTag': str(eachEle[0]), 'nodeI': int(eachEle[1]),'nodeJ': int(eachEle[2]),
            'A': float(eachEle[3]),'E': float(eachEle[4]),'G': float(eachEle[5]),'J': float(eachEle[6]),
            'Iy': float(eachEle[7]),'Iz': float(eachEle[8]),'localZTag':int(eachEle[9]),} for eachEle in elesList]
        nodesTable = f"""
                                                CREATE TABLE IF NOT EXISTS
                                                {tableName}(
                                                eleTag MESSAGE_TEXT PRIMARY KEY NOT NULL,
                                                nodeI INT NOT NULL,
                                                nodeJ INT NOT NULL,
                                                A REAL NOT NULL,
                                                E REAL NOT NULL,
                                                G REAL NOT NULL,
                                                J REAL NOT NULL,
                                                Iy REAL NOT NULL,
                                                Iz REAL NOT NULL,
                                                localZTag INT NOT NULL);"""
        db.query(nodesTable)  # 创建列表
        insertNodes = f"""
                            INSERT OR REPLACE INTO
                            {tableName}(eleTag,nodeI,nodeJ,A,E,G,J,Iy,Iz,localZTag)
                            values (:eleTag,:nodeI,:nodeJ,:A,:E,:G,:J,:Iy,:Iz,:localZTag) """
        db.bulk_query(insertNodes, saveDict)
        db = records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        db.close()

    def saveFEM_nonlinearBeamColumn_eles(self,tableName,elesList):
        """
        ---保存nonlinearBeamColumn单元信息到模型数据库---
        tableName(str)-表名称
        elesList(list)-单元属性列表,[[eleTag,nodeI,nodeJ,EleGeomTransf,EleSection],...]
        """
        db = records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        saveDict = [{'eleTag': str(eachEle[0]), 'nodeI': int(eachEle[1]),'nodeJ': int(eachEle[2]),
            'EleGeomTransf': int(eachEle[3]),'EleSection':int(eachEle[4]),} for eachEle in elesList]
        nodesTable = f"""
                                                CREATE TABLE IF NOT EXISTS
                                                {tableName}(
                                                eleTag MESSAGE_TEXT PRIMARY KEY NOT NULL,
                                                nodeI INT NOT NULL,
                                                nodeJ INT NOT NULL,
                                                EleGeomTransf INT NOT NULL,
                                                EleSection INT NOT NULL);"""
        db.query(nodesTable)  # 创建列表
        insertNodes = f"""
                            INSERT OR REPLACE INTO
                            {tableName}(eleTag,nodeI,nodeJ,EleGeomTransf,EleSection)
                            values (:eleTag,:nodeI,:nodeJ,:EleGeomTransf,:EleSection) """
        db.bulk_query(insertNodes, saveDict)
        db = records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        db.close()

    def saveFEM_localZVector(self,tableName,localZList):
        """
        ---保存单元局部Z轴向量到数据库---
        tableName(str)-表名称
        localZList(list)-单元属性列表,[[eleTag,localZX,localZY,localZZ],...]
        """
        db = records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        saveDict = [{'eleTag': str(eachLocal[0]), 'localZX': float(eachLocal[1]), 'localZY': float(eachLocal[2]),
                     'localZZ': float(eachLocal[3]) } for eachLocal in localZList]
        nodesTable = f"""
                                                        CREATE TABLE IF NOT EXISTS
                                                        {tableName}(
                                                        eleTag MESSAGE_TEXT PRIMARY KEY NOT NULL,
                                                        localZX REAL NOT NULL,
                                                        localZY REAL NOT NULL,
                                                        localZZ REAL NOT NULL);"""
        db.query(nodesTable)  # 创建列表
        insertNodes = f"""
                                    INSERT OR REPLACE INTO
                                    {tableName}(eleTag,localZX,localZY,localZZ)
                                    values (:eleTag,:localZX,:localZY,:localZZ) """
        db.bulk_query(insertNodes, saveDict)
        db = records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        db.close()

    def saveFEM_fiberEles(self,tableName,fibersList):
        """
        ---保存截面纤维单元---
        tableName(str)-纤维截面名称
        fibersList(list)-截面纤维单元列表,[[]]
        """
        pass

    def saveFEM_fiberMaterial(self,tableName,fiberMatList):
        """
        ---保存截面纤维单元材料(cover,core,bar)---
        tableName(str)-纤维材料名称
        fiberMatList(list)-纤维材料列表,[sectName,coverPara,corePara,barPara]
        """
        db = records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        saveDict = [{'sectName': str(fiberMatList[0]), 'coverPara': str(fiberMatList[1]), 'corePara': str(fiberMatList[2]),
                     'barPara': str(fiberMatList[3])}]
        nodesTable = f"""
                    CREATE TABLE IF NOT EXISTS
                    {tableName}(
                    sectName MESSAGE_TEXT PRIMARY KEY NOT NULL,
                    coverPara MESSAGE_TEXT NOT NULL,
                    corePara MESSAGE_TEXT NOT NULL,
                    barPara MESSAGE_TEXT NOT NULL);"""
        db.query(nodesTable)  # 创建列表
        insertNodes = f"""
                    INSERT OR REPLACE INTO
                    {tableName}(sectName,coverPara,corePara,barPara)
                    values (:sectName,:coverPara,:corePara,:barPara) """
        db.bulk_query(insertNodes, saveDict)
        db = records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        db.close()

    def saveFEM_springStiffness(self,tableName,springStifnessList):
        """
        ---弹簧刚度值---
        tableName(str)-弹簧刚度表名
        springStifnessList(list)-弹簧刚度值springStifnessList,[[foundationName,U1,U2,U3,R1,R2,R3],]
        """
        db = records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        saveDict = [{'foundationName': str(each[0]), 'U1': float(each[1]), 'U2': float(each[2]),
                     'U3': float(each[3]),'R1': float(each[4]),'R2': float(each[5]),
                    'R3': float(each[6])} for each in springStifnessList]
        nodesTable = f"""
                            CREATE TABLE IF NOT EXISTS
                            {tableName}(
                            foundationName MESSAGE_TEXT PRIMARY KEY NOT NULL,
                            U1 REAL NOT NULL,
                            U2 REAL NOT NULL,
                            U3 REAL NOT NULL,
                            R1 REAL NOT NULL,
                            R2 REAL NOT NULL,
                            R3 REAL NOT NULL);"""
        db.query(nodesTable)  # 创建列表
        insertNodes = f"""
                            INSERT OR REPLACE INTO
                            {tableName}(foundationName,U1,U2,U3,R1,R2,R3)
                            values (:foundationName,:U1,:U2,:U3,:R1,:R2,:R3) """
        db.bulk_query(insertNodes, saveDict)
        db = records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        db.close()

    def saveFEM_bearingEle(self,tableName,bearingEleList):
        """
        ---支座单元特性值---
        tableName(str)-支座单元表名称
        bearingEleList(list)-支座单元列表,[[bearingEle,nodeI,nodeJ,localXList,localYList],]
        """
        db = records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        saveDict = [{'bearingEle': str(each[0]), 'nodeI': int(each[1]), 'nodeJ': int(each[2]),
                     'localXList': str(each[3]), 'localYList': str(each[4])} for each in bearingEleList]
        nodesTable = f"""
                                    CREATE TABLE IF NOT EXISTS
                                    {tableName}(
                                    bearingEle MESSAGE_TEXT PRIMARY KEY NOT NULL,
                                    nodeI INT NOT NULL,
                                    nodeJ INT NOT NULL,
                                    localXList MESSAGE_TEXT NOT NULL,
                                    localYList MESSAGE_TEXT  NOT NULL);"""
        db.query(nodesTable)  # 创建列表
        insertNodes = f"""
                                    INSERT OR REPLACE INTO
                                    {tableName}(bearingEle,nodeI,nodeJ,localXList,localYList)
                                    values (:bearingEle,:nodeI,:nodeJ,:localXList,:localYList) """
        db.bulk_query(insertNodes, saveDict)
        db = records.Database('sqlite:///' + self._dbPath)  # connect to the sqlite database
        db.close()


########################################################################################################################
########################################################################################################################
if __name__ == '__main__':
    dbPath = "ModelInfoDB.db"
    dbInstance=ModelDB(dbPath)
    # dbInstance.initDB(dbPath)
    # returnValues=dbInstance.getSectDB(tableName='bridgeSect',sectName='capBeam')
    # print(returnValues)
    # dbInstance.saveNodes([['girder_1',1,2.3,4.2,5.3]])
    # nodes=dbInstance.getNodes()
    # dbInstance.saveEles([['ele_1',1,'node_1','node_2']])
    # nodesList=[[1,1.1,1.2,1.1,1.2],[2,1.2,1.3,1.4,5.3]]
    # dbInstance.saveFEMNodes(tableName='girderNodes',nodesList=nodesList)
    # returnValues=dbInstance.getFEMNodes('girderNodes')
    # print(returnValues)
    # returnValue=dbInstance.getRowValue(tableName='girderNodes',primaryKeyName="2")
    # print(returnValue)
    dbInstance.updateRowValue(tableName='girderNodes',primaryKeyName="2",updateDict={'X':1,'Y':2,'Z':3})



