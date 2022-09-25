# SAPBridge
An seismic analysis program for bridges    
##########################################################################    
Author: Junjun Guo([HomePage](https://github.com/Junjun1guo))    
E-mail: guojj@tongji.edu.cn/guojj_ce@163.com    
Environemet: Successfully excucted in python 3.8    
##########################################################################
______
- [Tutorial-1:Install SAPBridge and view OpenSeesPy model](#Tutorials-1)
- [Tutorial-2:Quickly generate model nodes and elements with AutoCAD dxf file](#Tutorial-2)

______
## Tutorials-1      
### Install SAPBridge and view OpenSeesPy model
1. Download the zip file
2. Run the example model (AnExampleBridgeOpenSeesPyModel.py) and generate the result database (resultsDB_1_1.db)
3. Download SAPBridge from https://fbs.sh/JunjunGuo/SAPBridge/SAPBridgeSetup.exe, and install it
4. When encounter error after installation, just close the window, and reopen it.
5. Select SAPBridge and right click the mouse, then click the properties and choose running the program as an administrator.
6. Click loadResultDB button, and load the result database (resultsDB_1_1.db)
7. Then display the model and conduct post process.     
Prepare your own openseespy model by referring the file AnExampleBridgeOpenSeesPyModel.py      
### Notes: compatible modules: records==0.5.3, sQLAlchemy==1.3.20     
<img src="https://github.com/Junjun1guo/SAPBridge/blob/main/figures/model.JPG" width =100% height =100% div align="center">
<img src="https://github.com/Junjun1guo/SAPBridge/blob/main/figures/modeShape.JPG" width =100% height =100% div align="center">
<img src="https://github.com/Junjun1guo/SAPBridge/blob/main/figures/timeHistory.JPG" width =100% height =100% div align="center">
<img src="https://github.com/Junjun1guo/SAPBridge/blob/main/figures/hysteretic.JPG" width =100% height =100% div align="center">
______    
## Tutorial-2 
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
## Tutorials-1      
