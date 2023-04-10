# SAPBridge (Version 0.4.0)
An seismic analysis program for bridges    
##########################################################################    
Author: Junjun Guo([HomePage](https://github.com/Junjun1guo))    
E-mail: guojj@tongji.edu.cn/guojj_ce@163.com    
Environemet: Successfully excucted in python 3.8    
##########################################################################
______
- [Tutorial-1:Auxiliary modules](#Tutorials-1)
- [Tutorial-2:Install SAPBridge and view OpenSeesPy model](#Tutorials-2)
- [Tutorial-3:Quickly generate model nodes and elements with AutoCAD dxf file](#Tutorial-3)
- [Tutorial-4:2D soil profile meshing  with AutoCAD dxf file](#Tutorial-4)
______
## Tutorials-2      
### Install SAPBridge and view OpenSeesPy model
1. Download the zip file
2. Run the example model (eg. exmple 1)
3. Download SAPBridge from https://fbs.sh/JunjunGuo/SAPBridge/SAPBridgeSetup.exe, and install it
4. When encounter error after installation, just close the window, and reopen it.
5. Select SAPBridge and right click the mouse, then click the properties and choose running the program as an administrator.
6. Click loadResultDB button, and load the result database 
7. Then display the model and conduct post process.     
Prepare your own openseespy model by referring the examples      
### Notes: compatible modules: records==0.5.3, sQLAlchemy==1.3.20     
<img src="https://github.com/Junjun1guo/SAPBridge/blob/main/figures/model.JPG" width =100% height =100% div align="center">
<img src="https://github.com/Junjun1guo/SAPBridge/blob/main/figures/modeShape.JPG" width =100% height =100% div align="center">
<img src="https://github.com/Junjun1guo/SAPBridge/blob/main/figures/shellWall.jpg" width =100% height =100% div align="center">
<img src="https://github.com/Junjun1guo/SAPBridge/blob/main/figures/timeHistory.JPG" width =100% height =100% div align="center">
<img src="https://github.com/Junjun1guo/SAPBridge/blob/main/figures/hysteretic.JPG" width =100% height =100% div align="center">

______  
## Tutorial-3      
### Quickly generate model nodes and elements with AutoCAD dxf file                
1. To access the auxiliary module, you need to get an free license. (Send your computer MAC address (eg.1A-2B-3C-D4-E5-F6 )
        to guojj@tongji.edu.cn to get a license by institute Email!)    
2. After entering the Quick model module, clicking the "ModelPath" button to select an folder to save the model database and the generated model nodes and elements.(There generates a template dxf file named "cadModelTemplate.dxf" with several specific layers,such as girder,pier,etc., plot each model part in the corresponding layer.), see Figure 2.1.
3. Setting the number of segments for arc and spline, the elements length of girder, pier and cap beam.
4. Clicking the "DXFModelLoad" button to load your model dxf file. (You can reference an example girder model dxf file constructed with the generated template file, called "girderBridgeExample.dxf", see Figure 2.2)
5. Clicking the "generateModel" button to automatically generate the model nodes and elements, and save them into the model database and txt files in the selected folder.
6. Go to the main windown of SAPBridge, clicking the button "loadModelDB" to load the generated model database, and display the model, see Figures 2.3 and 2.4. In addition, the model can be visualized with node and element tags, see Figures 2.5 and 2.6.
<img src="https://github.com/Junjun1guo/SAPBridge/blob/main/figures/quicklyGenerateModel-1.jpg" width =100% height =100% div align="center">
<p align="center">Figure 2.1 </p>
<img src="https://github.com/Junjun1guo/SAPBridge/blob/main/figures/dxfModel.jpg" width =100% height =100% div align="center">
<p align="center">Figure 2.2 </p>
<img src="https://github.com/Junjun1guo/SAPBridge/blob/main/figures/quickModel.jpg" width =100% height =100% div align="center">
<p align="center">Figure 2.3 </p>
<img src="https://github.com/Junjun1guo/SAPBridge/blob/main/figures/modelNodesElements.jpg" width =100% height =100% div align="center">
<p align="center">Figure 2.4 </p>
<img src="https://github.com/Junjun1guo/SAPBridge/blob/main/figures/modelNodesElementsStr.jpg" width =100% height =100% div align="center">
<p align="center">Figure 2.5 </p>
<img src="https://github.com/Junjun1guo/SAPBridge/blob/main/figures/modelNodesElementsInt.jpg" width =100% height =100% div align="center">
<p align="center">Figure 2.6 </p>      

______
## Tutorial-4      
### 2D soil profile meshing  with AutoCAD dxf file
1. Open the 2D soil profile divide window, see Figure 3.1.
2. Click "resultsSavePath" button to select an folder to save the generated nodes and elements files.
3. Click "dxfModelLoad" button to load the soil profile dxf file (see the example dxf file-soilProfile.dxf).
4. Enter the layer name of the rectangular border of the soil profile (Make sure the soil profile is within the rectangular border).
5. Specify the width and height of the divided elements.
6. Click the "meshSoilProfile" button to divide the rectangular region (see Figure 3.2).
7. Then, entering the layer name of the closed boundary of a local soil region, and enter the number of the soil region. 
8. Click "soilIdentify" button to identify the generated elements that within the specified soil region.
9. Repeat steps 7 and 8 until meshing all the soil regions (see Figure 3.3).
10. Finally, click "saveNodesEles" button to save the nodes and the elements of each soil region to the selected folder.

<img src="https://github.com/Junjun1guo/SAPBridge/blob/main/figures/soilProfileMeshPanel.jpg" width =100% height =100% div align="center">
<p align="center">Figure 3.1 </p>
<img src="https://github.com/Junjun1guo/SAPBridge/blob/main/figures/soilProfileRectangleMesh.jpg" width =100% height =100% div align="center">
<p align="center">Figure 3.2 </p>
<img src="https://github.com/Junjun1guo/SAPBridge/blob/main/figures/soilProfileRegionMesh.jpg" width =100% height =100% div align="center">
<p align="center">Figure 3.3 </p>
