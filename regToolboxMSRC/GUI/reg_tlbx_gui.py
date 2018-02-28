# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 15:32:32 2017

@author: pattenh1
"""

import sys
import os
from PyQt5 import QtWidgets, uic, QtCore
from regToolboxMSRC import register_SSS, register_SSM, register_MSS, register_MSM
from regToolboxMSRC.utils.reg_utils import transform_from_gui
from regToolboxMSRC.utils.ims_utils import IMS_pixel_maps
from regToolboxMSRC.utils.flx_utils import bruker_output_xmls
import SimpleITK as sitk
import xml.etree.ElementTree as ET
import xml.dom.minidom
import pkg_resources
import time
import datetime
import yaml

class MainWindow(QtWidgets.QMainWindow):
    
    def __init__(self):
        super(MainWindow, self).__init__()
        self.SSM_source_fp = 'fp'
        self.SSM_target1_fp = 'fp'
        self.SSM_target2_fp = 'fp'
        self.SSM_src_mask_fp = 'none'
        self.SSM_tgt1_mask_fp = 'none'
        self.SSM_tgt2_mask_fp = 'none'
        self.SSM_wd = ''
        self.SSM_bounding_box = False
        
        self.MSM_source_fp = 'fp'
        self.MSM_target1_fp = 'fp'
        self.MSM_target2_fp = 'fp'
        self.MSM_src_mask_fp = 'none'
        self.MSM_tgt1_mask_fp = 'none'
        self.MSM_tgt2_mask_fp = 'none'
        self.MSM_wd = ''
        self.MSM_bounding_box = False

        
        self.SSS_source_fp = 'fp'
        self.SSS_target_fp = 'fp'
        self.SSS_src_mask_fp = 'none'
        self.SSS_tgt_mask_fp = 'none'
        self.SSS_wd = ''
        self.SSS_bounding_box = False

        
        self.MSS_source_fp = 'fp'
        self.MSS_target_fp = 'fp'
        self.MSS_src_mask_fp = 'none'
        self.MSS_tgt_mask_fp = 'none'
        self.MSS_wd = ''
        self.MSS_bounding_box = False
        
        self.HDR_source_fp = 'fp'
        self.HDR_target_fp = 'fp'
        self.HDR_ijrois_fp = 'fp'
        self.HDR_wd = '' 
        
        self.IMS_data_fp = 'fp'
        self.IMS_wd = '' 
        
        self.TFM_transforms = []
        self.TFM_source_fp = 'fp'
        self.TFM_wd = ''
        
        #load in data stored in package
        resource_package = 'regToolboxMSRC'  
        resource_path = '/'.join(('GUI', 'MSRC_toolbox_v0_3.ui'))  
        template = pkg_resources.resource_stream(resource_package, resource_path)
        
        self.ui = uic.loadUi(template)
        self.ui.show()
        
        self.ui.SaveParam.clicked.connect(self.SaveParam_oc)
        self.ui.LoadParam.clicked.connect(self.LoadParam_oc)


############# SSM: image buttons
        self.ui.SSM_button_source.clicked.connect(self.SSM_oc_src_img)
        self.ui.SSM_button_target1.clicked.connect(self.SSM_oc_tgt_img1)
        self.ui.SSM_button_target2.clicked.connect(self.SSM_oc_tgt_img2)
        self.ui.SSM_button_src_mask.clicked.connect(self.SSM_oc_src_mask)
        self.ui.SSM_button_tgt_mask1.clicked.connect(self.SSM_oc_tgt_mask1)
        self.ui.SSM_button_tgt_mask2.clicked.connect(self.SSM_oc_tgt_mask2)
        
        #set wd button
        self.ui.SSM_button_wd.clicked.connect(self.SSM_oc_wd)

        #image type combo boxs
        self.ui.SSM_source_img_type.addItem("Not set...")
        self.ui.SSM_source_img_type.addItem("HE")
        self.ui.SSM_source_img_type.addItem("AF")

        self.ui.SSM_target_img_type1.addItem("Not set...")
        self.ui.SSM_target_img_type1.addItem("HE")
        self.ui.SSM_target_img_type1.addItem("AF")
        
        self.ui.SSM_target_img_type2.addItem("Not set...")
        self.ui.SSM_target_img_type2.addItem("HE")
        self.ui.SSM_target_img_type2.addItem("AF")
        
        #image type combo boxs
        self.ui.SSM_button_register_images.clicked.connect(self.SSM_register)

############# MSM: image buttons
        self.ui.MSM_button_source.clicked.connect(self.MSM_oc_src_img)
        self.ui.MSM_button_target1.clicked.connect(self.MSM_oc_tgt_img1)
        self.ui.MSM_button_target2.clicked.connect(self.MSM_oc_tgt_img2)
        self.ui.MSM_button_src_mask.clicked.connect(self.MSM_oc_src_mask)
        self.ui.MSM_button_tgt_mask1.clicked.connect(self.MSM_oc_tgt_mask1)
        self.ui.MSM_button_tgt_mask2.clicked.connect(self.MSM_oc_tgt_mask2)
        
        #set wd button
        self.ui.MSM_button_wd.clicked.connect(self.MSM_oc_wd)

        #image type combo boxs
        self.ui.MSM_source_img_type.addItem("Not set...")
        self.ui.MSM_source_img_type.addItem("HE")
        self.ui.MSM_source_img_type.addItem("AF")

        self.ui.MSM_target_img_type1.addItem("Not set...")
        self.ui.MSM_target_img_type1.addItem("HE")
        self.ui.MSM_target_img_type1.addItem("AF")
        
        self.ui.MSM_target_img_type2.addItem("Not set...")
        self.ui.MSM_target_img_type2.addItem("HE")
        self.ui.MSM_target_img_type2.addItem("AF")
        
        #image type combo boxs
        self.ui.MSM_button_register_images.clicked.connect(self.MSM_register)

############# SSM: image buttons        
        self.ui.SSS_button_source.clicked.connect(self.SSS_oc_src_img)
        self.ui.SSS_button_target.clicked.connect(self.SSS_oc_tgt_img)

        self.ui.SSS_button_src_mask.clicked.connect(self.SSS_oc_src_mask)
        self.ui.SSS_button_tgt_mask.clicked.connect(self.SSS_oc_tgt_mask)

        
        #set wd button
        self.ui.SSS_button_wd.clicked.connect(self.SSS_oc_wd)

        #image type combo boxs
        self.ui.SSS_source_img_type.addItem("Not set...")
        self.ui.SSS_source_img_type.addItem("HE")
        self.ui.SSS_source_img_type.addItem("AF")

        self.ui.SSS_target_img_type.addItem("Not set...")
        self.ui.SSS_target_img_type.addItem("HE")
        self.ui.SSS_target_img_type.addItem("AF")
        
        #image type combo boxs
        self.ui.SSS_button_register_images.clicked.connect(self.SSS_register)
        
############# MSS: image buttons        
        self.ui.MSS_button_source.clicked.connect(self.MSS_oc_src_img)
        self.ui.MSS_button_target.clicked.connect(self.MSS_oc_tgt_img)

        self.ui.MSS_button_src_mask.clicked.connect(self.MSS_oc_src_mask)
        self.ui.MSS_button_tgt_mask.clicked.connect(self.MSS_oc_tgt_mask)

        #set wd button
        self.ui.MSS_button_wd.clicked.connect(self.MSS_oc_wd)

        #image type combo boxs
        self.ui.MSS_source_img_type.addItem("Not set...")
        self.ui.MSS_source_img_type.addItem("HE")
        self.ui.MSS_source_img_type.addItem("AF")

        self.ui.MSS_target_img_type.addItem("Not set...")
        self.ui.MSS_target_img_type.addItem("HE")
        self.ui.MSS_target_img_type.addItem("AF")
        
        #image type combo boxs
        self.ui.MSS_button_register_images.clicked.connect(self.MSS_register)
        
############# IMS: image buttons        
        self.ui.IMS_button_source.clicked.connect(self.IMS_data_oc)

        #set wd button
        self.ui.IMS_button_wd.clicked.connect(self.IMS_oc_wd)

        #image type combo boxs
        self.ui.IMS_button_generate_map.clicked.connect(self.IMS_generate_maps)

############# HDR: image buttons        
        self.ui.HDR_button_source.clicked.connect(self.HDR_oc_src_img)
        self.ui.HDR_button_target.clicked.connect(self.HDR_oc_tgt_img)
        self.ui.HDR_button_rois.clicked.connect(self.HDR_oc_ijrois)


        #set wd button
        self.ui.HDR_button_wd.clicked.connect(self.HDR_oc_wd)
        
        self.ui.HDR_button_register_images.clicked.connect(self.HDR_register)
        
############# TFM: image buttons        
        self.ui.TFM_button_source.clicked.connect(self.TFM_oc_src_img)
        self.ui.TFM_button_transform.clicked.connect(self.TFM_oc_transform)
        
        ##set wd button
        self.ui.TFM_button_wd.clicked.connect(self.TFM_oc_wd)
        
        self.ui.TFM_button_apply_transform.clicked.connect(self.TFM_register)

############# file path functions       
    def openFileNameDialog(self):    
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self,"Open file...", "","All Files (*);;Python Files (*.py)")
        return(file_name)
    
    def openFileDirDialog(self):    
        wd = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory...")
        return(wd)
    
    def saveFileDialog(self):    
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self,"Save parameter file (.xml)","","All Files (*);;XML Files (*.xml)")
        return fileName
    
############## xml saving and loading functions 
#    def get_params_xml(self):
#        root = ET.Element("MSRC_param_file")
#		##save all parameters in XML for easy reloading
#
#        SSM_params = ET.SubElement(root, "SSM_params")
#        MSM_params = ET.SubElement(root, "MSM_params")
#        SSS_params = ET.SubElement(root, "SSS_params")
#        MSS_params = ET.SubElement(root, "MSS_params")
#        IMS_params = ET.SubElement(root, "IMS_params")
#        HDR_params = ET.SubElement(root, "HDR_params")
#
#		##SSM
#        ET.SubElement(SSM_params, "SSM_source_fp").text = self.SSM_source_fp
#        ET.SubElement(SSM_params, "SSM_target1_fp").text = self.SSM_target1_fp
#        ET.SubElement(SSM_params, "SSM_target2_fp").text = self.SSM_target2_fp
#        ET.SubElement(SSM_params, "SSM_src_mask_fp").text = self.SSM_src_mask_fp
#        ET.SubElement(SSM_params, "SSM_tgt1_mask_fp").text = self.SSM_tgt1_mask_fp
#        ET.SubElement(SSM_params, "SSM_tgt2_mask_fp").text = self.SSM_tgt2_mask_fp
#        ET.SubElement(SSM_params, "SSM_wd").text = self.SSM_wd
#        ET.SubElement(SSM_params, "SSM_source_img_type").text = self.ui.SSM_source_img_type.currentText()
#        ET.SubElement(SSM_params, "SSM_target_img_type1").text = self.ui.SSM_target_img_type1.currentText()
#        ET.SubElement(SSM_params, "SSM_target_img_type2").text = self.ui.SSM_target_img_type2.currentText()
#        ET.SubElement(SSM_params, "SSM_src_reso").text = self.ui.SSM_src_reso.text()
#        ET.SubElement(SSM_params, "SSM_tgt1_reso").text = self.ui.SSM_tgt1_reso.text()
#        ET.SubElement(SSM_params, "SSM_tgt2_reso").text = self.ui.SSM_tgt2_reso.text()
#        ET.SubElement(SSM_params, "SSM_Reg_model1").text = self.ui.SSM_Reg_model1.currentText()
#        ET.SubElement(SSM_params, "SSM_Reg_model2").text = self.ui.SSM_Reg_model2.currentText()
#        ET.SubElement(SSM_params, "SSM_textbox_fn").text = self.ui.SSM_textbox_fn.text()
#
#		##MSM
#        ET.SubElement(MSM_params, "MSM_source_fp").text = self.MSM_source_fp
#        ET.SubElement(MSM_params, "MSM_target1_fp").text = self.MSM_target1_fp
#        ET.SubElement(MSM_params, "MSM_target2_fp").text = self.MSM_target2_fp
#        ET.SubElement(MSM_params, "MSM_src_mask_fp").text = self.MSM_src_mask_fp
#        ET.SubElement(MSM_params, "MSM_tgt1_mask_fp").text = self.MSM_tgt1_mask_fp
#        ET.SubElement(MSM_params, "MSM_tgt2_mask_fp").text = self.MSM_tgt2_mask_fp
#        ET.SubElement(MSM_params, "MSM_wd").text = self.MSM_wd
#        ET.SubElement(MSM_params, "MSM_source_img_type").text = self.ui.MSM_source_img_type.currentText()
#        ET.SubElement(MSM_params, "MSM_target_img_type1").text = self.ui.MSM_target_img_type1.currentText()
#        ET.SubElement(MSM_params, "MSM_target_img_type2").text = self.ui.MSM_target_img_type2.currentText()
#        ET.SubElement(MSM_params, "MSM_src_reso").text = self.ui.MSM_src_reso.text()
#        ET.SubElement(MSM_params, "MSM_tgt1_reso").text = self.ui.MSM_tgt1_reso.text()
#        ET.SubElement(MSM_params, "MSM_tgt2_reso").text = self.ui.MSM_tgt2_reso.text()
#        ET.SubElement(MSM_params, "MSM_Reg_model1").text = self.ui.MSM_Reg_model1.currentText()
#        ET.SubElement(MSM_params, "MSM_Reg_model2").text = self.ui.MSM_Reg_model2.currentText()
#        ET.SubElement(MSM_params, "MSM_textbox_fn").text = self.ui.MSM_textbox_fn.text()
#
#		##SSS
#        ET.SubElement(SSS_params, "SSS_source_fp").text = self.SSS_source_fp
#        ET.SubElement(SSS_params, "SSS_target_fp").text = self.SSS_target_fp
#        ET.SubElement(SSS_params, "SSS_src_mask_fp").text = self.SSS_src_mask_fp
#        ET.SubElement(SSS_params, "SSS_tgt_mask_fp").text = self.SSS_tgt_mask_fp
#        ET.SubElement(SSS_params, "SSS_wd").text = self.SSS_wd
#        ET.SubElement(SSS_params, "SSS_source_img_type").text = self.ui.SSS_source_img_type.currentText()
#        ET.SubElement(SSS_params, "SSS_target_img_type").text = self.ui.SSS_target_img_type.currentText()
#        ET.SubElement(SSS_params, "SSS_src_reso").text = self.ui.SSS_src_reso.text()
#        ET.SubElement(SSS_params, "SSS_tgt_reso").text = self.ui.SSS_tgt_reso.text()
#        ET.SubElement(SSS_params, "SSS_Reg_model1").text = self.ui.SSS_Reg_model1.currentText()
#        ET.SubElement(SSS_params, "SSS_textbox_fn").text = self.ui.SSS_textbox_fn.text()
#
#		##MSS
#        ET.SubElement(MSS_params, "MSS_source_fp").text = self.MSS_source_fp
#        ET.SubElement(MSS_params, "MSS_target_fp").text = self.MSS_target_fp
#        ET.SubElement(MSS_params, "MSS_src_mask_fp").text = self.MSS_src_mask_fp
#        ET.SubElement(MSS_params, "MSS_tgt_mask_fp").text = self.MSS_tgt_mask_fp
#        ET.SubElement(MSS_params, "MSS_wd").text = self.MSS_wd
#        ET.SubElement(MSS_params, "MSS_source_img_type").text = self.ui.MSS_source_img_type.currentText()
#        ET.SubElement(MSS_params, "MSS_target_img_type").text = self.ui.MSS_target_img_type.currentText()
#        ET.SubElement(MSS_params, "MSS_src_reso").text = self.ui.MSS_src_reso.text()
#        ET.SubElement(MSS_params, "MSS_tgt_reso").text = self.ui.MSS_tgt_reso.text()
#        ET.SubElement(MSS_params, "MSS_Reg_model1").text = self.ui.MSS_Reg_model1.currentText()
#        ET.SubElement(MSS_params, "MSS_textbox_fn").text = self.ui.MSS_textbox_fn.text()
#
#		##IMS
#        ET.SubElement(IMS_params, "IMS_data_fp").text = self.IMS_data_fp
#        ET.SubElement(IMS_params, "IMS_wd").text = self.IMS_wd
#        ET.SubElement(IMS_params, "IMS_ims_reso").text = self.ui.IMS_ims_reso.text()
#        ET.SubElement(IMS_params, "IMS_micro_reso").text = self.ui.IMS_micro_reso.text()
#        ET.SubElement(IMS_params, "IMS_padding").text = self.ui.IMS_padding.text()
#        ET.SubElement(IMS_params, "IMS_textbox_fn").text = self.ui.IMS_textbox_fn.text()
#
#		##HDR
#        ET.SubElement(HDR_params, "HDR_source_fp").text = self.HDR_source_fp
#        ET.SubElement(HDR_params, "HDR_target_fp").text = self.HDR_target_fp
#        ET.SubElement(HDR_params, "HDR_wd").text = self.HDR_wd
#        ET.SubElement(HDR_params, "HDR_ims_reso").text = self.ui.HDR_ims_reso.text()
#        ET.SubElement(HDR_params, "HDR_par_fp").text = self.ui.HDR_par_fp.text()
#        ET.SubElement(HDR_params, "HDR_roi_names").text = self.ui.HDR_roi_names.text()
#        ET.SubElement(HDR_params, "HDR_textbox_fn").text = self.ui.HDR_textbox_fn.text()
#
#		#tree = ET.ElementTree(root)
#        return root
#    
#    def parse_params_xml(self, xml_fp):
#        doc = ET.parse(xml_fp).getroot()
#        
#        SSM_params_parsed = []
#        MSM_params_parsed = []
#        SSS_params_parsed = []
#        MSS_params_parsed = []
#        IMS_params_parsed = []
#        HDR_params_parsed = []
#        
#        for element in doc.findall('SSM_params/'):
#            if element.text == None:
#                SSM_params_parsed.append('')
#            else:
#                SSM_params_parsed.append(element.text)
#        
#        for element in doc.findall('MSM_params/'):
#            if element.text == None:
#                MSM_params_parsed.append('')
#            else:
#                MSM_params_parsed.append(element.text)
#        
#        for element in doc.findall('SSS_params/'):
#            if element.text == None:
#                SSS_params_parsed.append('')
#            else:
#                SSS_params_parsed.append(element.text)
#        
#        for element in doc.findall('MSS_params/'):
#            if element.text == None:
#                MSS_params_parsed.append('')
#            else:
#                MSS_params_parsed.append(element.text)
#        
#        for element in doc.findall('IMS_params/'):
#            if element.text == None:
#                IMS_params_parsed.append('')
#            else:
#                IMS_params_parsed.append(element.text)
#                
#        for element in doc.findall('HDR_params/'):
#            if element.text == None:
#                HDR_params_parsed.append('')
#            else:
#                HDR_params_parsed.append(element.text)
#        
#        return SSM_params_parsed, MSM_params_parsed, SSS_params_parsed, MSS_params_parsed, IMS_params_parsed, HDR_params_parsed
    
#    def SaveParam_oc(self):
#        xml_params = self.get_params_xml()
#        fileName = self.saveFileDialog()
#        if fileName:
#            stringed = ET.tostring(xml_params)
#            reparsed = xml.dom.minidom.parseString(stringed)
#
#            myfile = open(fileName, "w")  
#            myfile.write(reparsed.toprettyxml(indent="\t")) 
#            
#    def LoadParam_oc(self):
#        fileName = self.openFileNameDialog()
#        #print(os.path.splitext(fileName)[1].lower())
#        if fileName and os.path.splitext(fileName)[1].lower() == '.xml':
#            SSM_params_parsed, MSM_params_parsed, SSS_params_parsed, MSS_params_parsed, IMS_params_parsed, HDR_params_parsed = self.parse_params_xml(fileName)
#            ##SSM
#            #print(SSM_params_parsed)
#            ##load in parameters into class
#            self.SSM_source_fp                         = SSM_params_parsed[0 ]
#            self.SSM_target1_fp                        = SSM_params_parsed[1 ]
#            self.SSM_target2_fp                        = SSM_params_parsed[2 ]
#            self.SSM_src_mask_fp                       = SSM_params_parsed[3 ]
#            self.SSM_tgt1_mask_fp                      = SSM_params_parsed[4 ]
#            self.SSM_tgt2_mask_fp                      = SSM_params_parsed[5 ]
#            self.SSM_wd                                = SSM_params_parsed[6 ]
#            
#            
#            ##set imageType Regmodel
#            index = self.ui.SSM_source_img_type.findText(SSM_params_parsed[7 ], QtCore.Qt.MatchFixedString)
#            if index >= 0:
#            	 self.ui.SSM_source_img_type.setCurrentIndex(index)
#            
#            index = self.ui.SSM_target_img_type1.findText(SSM_params_parsed[8 ], QtCore.Qt.MatchFixedString)
#            if index >= 0:
#            	 self.ui.SSM_target_img_type1.setCurrentIndex(index)
#            	
#            index = self.ui.SSM_target_img_type2.findText(SSM_params_parsed[9 ], QtCore.Qt.MatchFixedString)
#            if index >= 0:
#            	 self.ui.SSM_target_img_type2.setCurrentIndex(index)	
#            
#            
#            self.ui.SSM_src_reso.setText(SSM_params_parsed[10])
#            self.ui.SSM_tgt1_reso.setText(SSM_params_parsed[11])
#            self.ui.SSM_tgt2_reso.setText(SSM_params_parsed[12])
#            
#            ##set combobox Regmodel
#            index = self.ui.SSM_Reg_model1.findText(SSM_params_parsed[13 ], QtCore.Qt.MatchFixedString)
#            if index >= 0:
#            	 self.ui.SSM_Reg_model1.setCurrentIndex(index)
#            
#            index = self.ui.SSM_Reg_model2.findText(SSM_params_parsed[14 ], QtCore.Qt.MatchFixedString)
#            if index >= 0:
#            	 self.ui.SSM_Reg_model2.setCurrentIndex(index)
#            	 
#            self.ui.SSM_textbox_fn.setText(SSM_params_parsed[15])
#            
#            
#            ##update boxes
#            if SSM_params_parsed[0 ] == 'fp':
#                self.ui.SSM_textbox_source.setText("source image not set...")
#            else:
#                self.ui.SSM_textbox_source.setText(os.path.basename(SSM_params_parsed[0 ]))
#
#            if SSM_params_parsed[1 ] == 'fp':
#                self.ui.SSM_textbox_target1.setText("source image not set...")
#            else:
#                self.ui.SSM_textbox_target1.setText(os.path.basename(SSM_params_parsed[1 ]))
#                
#            if SSM_params_parsed[2 ] == 'fp':
#                self.ui.SSM_textbox_target2.setText("source image not set...")
#            else:
#                self.ui.SSM_textbox_target2.setText(os.path.basename(SSM_params_parsed[3 ]))
#            	
#            if SSM_params_parsed[6 ] == '':
#                self.ui.SSM_textbox_wd.setText("working directory not set...")
#            else:
#                self.ui.SSM_textbox_wd.setText(SSM_params_parsed[6 ])
#            
#            
#            ##MSM
#            ##load in parameters into class
#            self.MSM_source_fp                         = MSM_params_parsed[0 ]
#            self.MSM_target1_fp                        = MSM_params_parsed[1 ]
#            self.MSM_target2_fp                        = MSM_params_parsed[2 ]
#            self.MSM_src_mask_fp                       = MSM_params_parsed[3 ]
#            self.MSM_tgt1_mask_fp                      = MSM_params_parsed[4 ]
#            self.MSM_tgt2_mask_fp                      = MSM_params_parsed[5 ]
#            self.MSM_wd                                = MSM_params_parsed[6 ]
#            
#            
#            ##set imageType Regmodel
#            index = self.ui.MSM_source_img_type.findText(MSM_params_parsed[7 ], QtCore.Qt.MatchFixedString)
#            if index >= 0:
#            	 self.ui.MSM_source_img_type.setCurrentIndex(index)
#            
#            index = self.ui.MSM_target_img_type1.findText(MSM_params_parsed[8 ], QtCore.Qt.MatchFixedString)
#            if index >= 0:
#            	 self.ui.MSM_target_img_type1.setCurrentIndex(index)
#            	
#            index = self.ui.MSM_target_img_type2.findText(MSM_params_parsed[9 ], QtCore.Qt.MatchFixedString)
#            if index >= 0:
#            	 self.ui.MSM_target_img_type2.setCurrentIndex(index)	
#            
#            
#            self.ui.MSM_src_reso.setText(MSM_params_parsed[10])
#            self.ui.MSM_tgt1_reso.setText(MSM_params_parsed[11])
#            self.ui.MSM_tgt2_reso.setText(MSM_params_parsed[12])
#            
#            ##set combobox Regmodel
#            index = self.ui.MSM_Reg_model1.findText(MSM_params_parsed[13 ], QtCore.Qt.MatchFixedString)
#            if index >= 0:
#            	 self.ui.MSM_Reg_model1.setCurrentIndex(index)
#            
#            index = self.ui.MSM_Reg_model2.findText(MSM_params_parsed[14 ], QtCore.Qt.MatchFixedString)
#            if index >= 0:
#            	 self.ui.MSM_Reg_model2.setCurrentIndex(index)
#            	 
#            self.ui.MSM_textbox_fn.setText(MSM_params_parsed[15])
#            
#            
#            ##update boxes
#            if MSM_params_parsed[0 ] == 'fp':
#                self.ui.MSM_textbox_source.setText("source image not set...")
#            else:
#                self.ui.MSM_textbox_source.setText(os.path.basename(MSM_params_parsed[0 ]))
#
#            if MSM_params_parsed[1 ] == 'fp':
#                self.ui.MSM_textbox_target1.setText("source image not set...")
#            else:
#                self.ui.MSM_textbox_target1.setText(os.path.basename(MSM_params_parsed[1 ]))
#                
#            if MSM_params_parsed[2 ] == 'fp':
#                self.ui.MSM_textbox_target2.setText("source image not set...")
#            else:
#                self.ui.MSM_textbox_target2.setText(os.path.basename(MSM_params_parsed[3 ]))
#            	
#            if MSM_params_parsed[6 ] == '':
#                self.ui.MSM_textbox_wd.setText("working directory not set...")
#            else:
#                self.ui.MSM_textbox_wd.setText(MSM_params_parsed[6 ])
#            
#            ##SSS
#            
#            ##load in parameters into class
#            self.SSS_source_fp                         = SSS_params_parsed[0 ]
#            self.SSS_target_fp                         = SSS_params_parsed[1 ]
#            self.SSS_src_mask_fp                       = SSS_params_parsed[2 ]
#            self.SSS_tgt1_mask_fp                      = SSS_params_parsed[3 ]
#            self.SSS_wd                                = SSS_params_parsed[4 ]
#            
#            ##set imageType Regmodel
#            index = self.ui.SSS_source_img_type.findText(SSS_params_parsed[5 ], QtCore.Qt.MatchFixedString)
#            if index >= 0:
#            	 self.ui.SSS_source_img_type.setCurrentIndex(index)
#            
#            index = self.ui.SSS_target_img_type.findText(SSS_params_parsed[6 ], QtCore.Qt.MatchFixedString)
#            if index >= 0:
#            	 self.ui.SSS_target_img_type.setCurrentIndex(index)
#            	
#            
#            self.ui.SSS_src_reso.setText(SSS_params_parsed[7])
#            self.ui.SSS_tgt_reso.setText(SSS_params_parsed[8])
#            
#            ##set combobox Regmodel
#            index = self.ui.SSS_Reg_model1.findText(SSS_params_parsed[9 ], QtCore.Qt.MatchFixedString)
#            if index >= 0:
#            	 self.ui.SSS_Reg_model1.setCurrentIndex(index)
#            
#            
#            self.ui.SSS_textbox_fn.setText(SSS_params_parsed[10])
#            
#            
#            ##update boxes
#            if SSS_params_parsed[0 ] == 'fp':
#                self.ui.SSS_textbox_source.setText("source image not set...")
#            else:
#                self.ui.SSS_textbox_source.setText(os.path.basename(SSS_params_parsed[0 ]))
#            
#            if SSS_params_parsed[1 ] == 'fp':
#                self.ui.SSS_textbox_target.setText("source image not set...")
#            else:
#                self.ui.SSS_textbox_target.setText(os.path.basename(SSS_params_parsed[1 ]))
#            
#            if SSS_params_parsed[4 ] == '':
#                self.ui.SSS_textbox_wd.setText("working directory not set...")
#            else:
#                self.ui.SSS_textbox_wd.setText(os.path.basename(SSS_params_parsed[4 ]))
#            
#            ##MSS
#            
#            ##load in parameters into class
#            self.MSS_source_fp                         = MSS_params_parsed[0 ]
#            self.MSS_target_fp                         = MSS_params_parsed[1 ]
#            self.MSS_src_mask_fp                       = MSS_params_parsed[2 ]
#            self.MSS_tgt1_mask_fp                      = MSS_params_parsed[3 ]
#            self.MSS_wd                                = MSS_params_parsed[4 ]
#            
#            
#            ##set imageType Regmodel
#            index = self.ui.MSS_source_img_type.findText(MSS_params_parsed[5 ], QtCore.Qt.MatchFixedString)
#            if index >= 0:
#            	 self.ui.MSS_source_img_type.setCurrentIndex(index)
#            
#            index = self.ui.MSS_target_img_type.findText(MSS_params_parsed[6 ], QtCore.Qt.MatchFixedString)
#            if index >= 0:
#            	 self.ui.MSS_target_img_type.setCurrentIndex(index)
#            	
#            
#            self.ui.MSS_src_reso.setText(MSS_params_parsed[7])
#            self.ui.MSS_tgt_reso.setText(MSS_params_parsed[8])
#            
#            ##set combobox Regmodel
#            index = self.ui.MSS_Reg_model1.findText(MSS_params_parsed[9 ], QtCore.Qt.MatchFixedString)
#            if index >= 0:
#            	 self.ui.MSS_Reg_model1.setCurrentIndex(index)
#            
#            
#            self.ui.MSS_textbox_fn.setText(MSS_params_parsed[10])
#            
#            
#            ##update boxes
#            if MSS_params_parsed[0 ] == 'fp':
#                self.ui.MSS_textbox_source.setText("source image not set...")
#            else:
#                self.ui.MSS_textbox_source.setText(os.path.basename(MSS_params_parsed[0 ]))
#            
#            if MSS_params_parsed[1 ] == 'fp':
#                self.ui.MSS_textbox_target.setText("source image not set...")
#            else:
#                self.ui.MSS_textbox_target.setText(os.path.basename(MSS_params_parsed[1 ]))
#            
#            if MSS_params_parsed[4 ] == '':
#                self.ui.MSS_textbox_wd.setText("working directory not set...")
#            else:
#                self.ui.MSS_textbox_wd.setText(MSS_params_parsed[4 ])
#
#            ##IMS
#
#            ##load in parameters into class
#            self.IMS_data_fp                           = IMS_params_parsed[0 ]
#            self.IMS_wd                                = IMS_params_parsed[1 ]
#            
#            self.ui.IMS_ims_reso.setText(IMS_params_parsed[2])
#            self.ui.IMS_micro_reso.setText(IMS_params_parsed[3])
#            self.ui.IMS_padding.setText(IMS_params_parsed[4])
#            self.ui.IMS_textbox_fn.setText(IMS_params_parsed[5])
#            
#            
#            ##update boxes
#            if MSS_params_parsed[0 ] == 'fp':
#                self.ui.IMS_textbox_source.setText("IMS data not set...")
#            else:
#                self.ui.IMS_textbox_source.setText(os.path.basename(IMS_params_parsed[0]))
#            
#            if IMS_params_parsed[1 ] == '':
#                self.ui.IMS_textbox_wd.setText("working directory not set...")
#            else:
#                self.ui.IMS_textbox_wd.setText(IMS_params_parsed[1 ])
#
#            
#            ##HDR            
#            ##load in parameters into class
#            self.HDR_source_fp                         = HDR_params_parsed[0 ]
#            self.HDR_target_fp                         = HDR_params_parsed[1 ]
#            self.HDR_wd                                = HDR_params_parsed[2 ]
#                        	            
#            self.ui.HDR_ims_reso.setText(HDR_params_parsed[3])
#            self.ui.HDR_par_fp.setText(HDR_params_parsed[4])
#            self.ui.HDR_roi_names.setText(HDR_params_parsed[5])            
#            self.ui.HDR_textbox_fn.setText(HDR_params_parsed[6])
#            
#            ##update boxes
#            if HDR_params_parsed[0 ] == 'fp':
#                self.ui.HDR_textbox_source.setText("source image not set...")
#            else:
#                self.ui.HDR_textbox_source.setText(os.path.basename(HDR_params_parsed[0 ]))
#            
#            if HDR_params_parsed[1 ] == 'fp':
#                self.ui.HDR_textbox_target.setText("target image not set...")
#            else:
#                self.ui.HDR_textbox_target.setText(os.path.basename(HDR_params_parsed[1 ]))
#            
#            if HDR_params_parsed[2 ] == '':
#                self.ui.HDR_textbox_wd.setText("working directory not set...")
#            else:
#                self.ui.HDR_textbox_wd.setText(os.path.basename(HDR_params_parsed[2]))
            
            
############# SSM on click buttons
    def SSM_oc_src_img(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.SSM_textbox_source.setText("source image not set...")
        else:
            self.ui.SSM_textbox_source.setText(os.path.basename(file_name))
            self.SSM_source_fp = file_name
        
    def SSM_oc_tgt_img1(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.SSM_textbox_target1.setText("target image 1 not set...")
        else:
            self.ui.SSM_textbox_target1.setText(os.path.basename(file_name))
            self.SSM_target1_fp = file_name
    
    def SSM_oc_tgt_img2(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.SSM_textbox_target2.setText("target image 2 not set...")
        else:
            self.ui.SSM_textbox_target2.setText(os.path.basename(file_name))
            self.SSM_target2_fp = file_name
        
    def SSM_oc_src_mask(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.SSM_src_mask_fp = 'none'
        else:
            #self.ui.SSM_textbox_source.setText(os.path.basename(file_name))
            self.SSM_src_mask_fp = file_name
        
    def SSM_oc_tgt_mask1(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.SSM_tgt1_mask_fp = 'none'
        else:
            #self.ui.SSM_textbox_target1.setText(os.path.basename(file_name))
            self.SSM_tgt1_mask_fp = file_name
    
    def SSM_oc_tgt_mask2(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.SSM_tgt2_mask_fp = 'none'
        else:
            #self.ui.SSM_textbox_target2.setText(os.path.basename(file_name))
            self.SSM_tgt2_mask_fp = file_name
            
    def SSM_oc_wd(self):
        wd_dir = self.openFileDirDialog()
        if len(wd_dir) == 0:
            self.ui.SSM_textbox_wd.setText("working directory not set...")
        else:
            self.ui.SSM_textbox_wd.setText(wd_dir)
            self.SSM_wd = wd_dir
    
    def SSM_register(self, params = True):
        if os.path.exists(self.SSM_source_fp) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set the source image!", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        
        elif os.path.exists(self.SSM_target1_fp) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set target image 1!",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        
        elif os.path.exists(self.SSM_target2_fp) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set target image 2!",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        
        elif os.path.exists(self.SSM_wd) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set the working directory!",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        
        elif str(self.ui.SSM_source_img_type.currentText()) == "Not set..." or str(self.ui.SSM_target_img_type1.currentText()) == "Not set..." or str(self.ui.SSM_target_img_type2.currentText()) == "Not set...":
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set all image types!",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return    
        
        else:
            if self.ui.SSM_intermediate_export.isChecked() == True:
                intermed = True
            else:
                intermed = False
            
            #xml_params = self.get_params_xml()
            
            SSM_source_img_type = str(self.ui.SSM_source_img_type.currentText())
            SSM_target_img_type1 = str(self.ui.SSM_target_img_type1.currentText())
            SSM_target_img_type2 = str(self.ui.SSM_target_img_type2.currentText())
            
            source_res = str(self.ui.SSM_src_reso.text())
            target1_res = str(self.ui.SSM_tgt1_reso.text())
            target2_res = str(self.ui.SSM_tgt2_reso.text())
            
            reg_model1 = str(self.ui.SSM_Reg_model1.currentText())   
            if reg_model1 == 'import...':
                reg_model1 = self.openFileNameDialog()
                
            reg_model2 = str(self.ui.SSM_Reg_model2.currentText())
            if reg_model2 == 'import...':
                reg_model2 = self.openFileNameDialog()
            
            project_name = str(self.ui.SSM_textbox_fn.text())
            
            ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H_%M_%S_')

            SSM_params = dict(
                param_mode = 'SSM',
                source_fp = self.SSM_source_fp, 
                source_res = source_res, 
                target1_fp = self.SSM_target1_fp, 
                target1_res = target1_res, 
                target2_fp = target2_res, 
                target2_res = target2_res, 
                source_mask_fp = self.SSM_src_mask_fp,
                target1_mask_fp = self.SSM_tgt1_mask_fp, 
                target2_mask_fp = self.SSM_tgt2_mask_fp,
                wd = self.SSM_wd, 
                source_img_type = SSM_source_img_type, 
                target_img_type1 = SSM_target_img_type1, 
                target_img_type2 = SSM_target_img_type2,
                reg_model1 = reg_model1,
                reg_model2 = reg_model2,
                project_name = project_name, 
                intermediate_output = intermed , 
                bounding_box = self.SSM_bounding_box,
                pass_in = ts + project_name
            )
            
            with open(os.path.join(self.SSM_wd,'SSM_'+ts + project_name + '_config', 'w')) as outfile:
                yaml.dump(SSM_params, outfile, default_flow_style=False)
            
            
#            self.SSM_source_fp, 
#            source_res, 
#            self.SSM_target1_fp, 
#            target1_res, 
#            self.SSM_target2_fp,
#            target2_res, 
#            self.SSM_src_mask_fp, 
#            self.SSM_tgt1_mask_fp, 
#            self.SSM_tgt2_mask_fp, 
#            self.SSM_wd, 
#            SSM_source_img_type, 
#            SSM_target_img_type1, 
#            SSM_target_img_type2, 
#            reg_model1, 
#            reg_model2, 
#            project_name, 
#            intermediate_output = intermed
            
            
            if params == False:
                print("Starting Registration...")
                print("Project Name: " + project_name)
                            
                print("Registering " + os.path.basename(self.SSM_source_fp) +", image type: "+ SSM_source_img_type + " to " + os.path.basename(self.SSM_target1_fp) +", image type: "+SSM_target_img_type1)
                
                print("Then registering " + os.path.basename(self.SSM_target1_fp) +", image type: "+SSM_target_img_type1 + " to "+ os.path.basename(self.SSM_target2_fp) +", imasge type: "+SSM_target_img_type2)
                
                print("Source -> Target 1 using registration model : " + reg_model1)
                print("Target1 -> Target 2 using registration model : " + reg_model2)
                       
                register_SSM(self.SSM_source_fp, source_res, 
                             self.SSM_target1_fp,target1_res, 
                             self.SSM_target2_fp,target2_res, 
                             self.SSM_src_mask_fp, self.SSM_tgt1_mask_fp, self.SSM_tgt2_mask_fp, 
                             self.SSM_wd, 
                             SSM_source_img_type, SSM_target_img_type1, SSM_target_img_type2, 
                             reg_model1, reg_model2, 
                             project_name, 
                             intermediate_output = intermed, bounding_box = False, 
                             pass_in_project_name=True, pass_in = ts + project_name)
                
                QtWidgets.QMessageBox.question(self, 'Registration Finished', "Check output directory for registered images",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

            return
        
############# SSS on click buttons
    def SSS_oc_src_img(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.SSS_textbox_source.setText("source image not set...")
        else:
            self.ui.SSS_textbox_source.setText(os.path.basename(file_name))
            self.SSS_source_fp = file_name
        
    def SSS_oc_tgt_img(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.SSS_textbox_target.setText("target image 1 not set...")
        else:
            self.ui.SSS_textbox_target.setText(os.path.basename(file_name))
            self.SSS_target_fp = file_name

    def SSS_oc_src_mask(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.SSS_src_mask_fp = 'none'
        else:
            #self.ui.SSM_textbox_source.setText(os.path.basename(file_name))
            self.SSS_src_mask_fp = file_name
        
    def SSS_oc_tgt_mask(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.SSS_tgt1_mask_fp = 'none'
        else:
            #self.ui.SSM_textbox_target1.setText(os.path.basename(file_name))
            self.SSS_tgt_mask_fp = file_name
            
    def SSS_oc_wd(self):
        wd_dir = self.openFileDirDialog()
        if len(wd_dir) == 0:
            self.ui.SSS_textbox_wd.setText("working directory not set...")
        else:
            self.ui.SSS_textbox_wd.setText(wd_dir)
            self.SSS_wd = wd_dir
        
    def SSS_register(self, params = True):
        if os.path.exists(self.SSS_source_fp) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set the source image!", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        
        elif os.path.exists(self.SSS_target_fp) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set the target image !",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif os.path.exists(self.SSS_wd) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set the working directory!",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        
        elif str(self.ui.SSS_source_img_type.currentText()) == "Not set..." or str(self.ui.SSS_target_img_type.currentText()) == "Not set...":
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set all image types!",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return    
        
        else:
            #xml_params = self.get_params_xml()
            
            SSS_source_img_type = str(self.ui.SSS_source_img_type.currentText())
            SSS_target_img_type = str(self.ui.SSS_target_img_type.currentText())
            
            source_res = str(self.ui.SSS_src_reso.text())
            target_res = str(self.ui.SSS_tgt_reso.text())
            
            reg_model1 = str(self.ui.SSS_Reg_model1.currentText())
            if reg_model1 == 'import...':
                reg_model1 = self.openFileNameDialog()

            project_name = str(self.ui.SSS_textbox_fn.text())
            
            ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H_%M_%S_')

            SSS_params = dict(
                param_mode = 'SSS',
                source_fp = self.SSS_source_fp, 
                source_res = source_res, 
                target1_fp = self.SSS_target_fp, 
                target1_res = target_res, 
                source_mask_fp = self.SSS_src_mask_fp,
                target1_mask_fp = self.SSS_tgt_mask_fp, 
                wd = self.SSS_wd, 
                source_img_type = SSS_source_img_type, 
                target_img_type1 = SSS_target_img_type, 
                reg_model1 = reg_model1,
                project_name = project_name, 
                bounding_box = self.SSS_bounding_box,
                pass_in = ts + project_name
            )
            
            with open(os.path.join(self.SSS_wd,'SSM_'+ts + project_name + '_config', 'w')) as outfile:
                yaml.dump(SSS_params, outfile, default_flow_style=False)
            
            if params == False:
                print("Starting Registration...")
                print("Project Name: " + project_name)
                
                print("Registering " + os.path.basename(self.SSS_source_fp) +", image type: "+ SSS_source_img_type + " to " + os.path.basename(self.SSS_target_fp) +", image type: "+SSS_target_img_type)
    
                print("Source -> Target using registration model : " + reg_model1)
                       
                register_SSS(self.SSS_source_fp, source_res, self.SSS_target_fp, target_res, self.SSS_src_mask_fp, self.SSS_tgt_mask_fp, self.SSS_wd, SSS_source_img_type, SSS_target_img_type, reg_model1, project_name, pass_in_project_name=True,pass_in = ts + project_name)
                
                QtWidgets.QMessageBox.question(self, 'Registration Finished', "Check output directory for registered images",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

            return

############# MSS on click buttons
    def MSS_oc_src_img(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.MSS_textbox_source.setText("source image not set...")
        else:
            self.ui.MSS_textbox_source.setText(os.path.basename(file_name))
            self.MSS_source_fp = file_name
        
    def MSS_oc_tgt_img(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.MSS_textbox_target.setText("target image 1 not set...")
        else:
            self.ui.MSS_textbox_target.setText(os.path.basename(file_name))
            self.MSS_target_fp = file_name

    def MSS_oc_src_mask(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.MSS_src_mask_fp = 'none'
        else:
            #self.ui.SSM_textbox_source.setText(os.path.basename(file_name))
            self.MSS_src_mask_fp = file_name
        
    def MSS_oc_tgt_mask(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.MSS_tgt1_mask_fp = 'none'
        else:
            #self.ui.SSM_textbox_target1.setText(os.path.basename(file_name))
            self.MSS_tgt_mask_fp = file_name
            
    def MSS_oc_wd(self):
        wd_dir = self.openFileDirDialog()
        if len(wd_dir) == 0:
            self.ui.MSS_textbox_wd.setText("working directory not set...")
        else:
            self.ui.MSS_textbox_wd.setText(wd_dir)
            self.MSS_wd = wd_dir
        
    def MSS_register(self):
        if os.path.exists(self.MSS_source_fp) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set the source image!", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        
        elif os.path.exists(self.MSS_target_fp) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set the target image !",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif os.path.exists(self.MSS_wd) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set the working directory!",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        
        elif str(self.ui.MSS_source_img_type.currentText()) == "Not set..." or str(self.ui.MSS_target_img_type.currentText()) == "Not set...":
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set all image types!",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return    
        
        else:
            #xml_params = self.get_params_xml()
            
            if self.ui.MSS_intermediate_export.isChecked() == True:
                intermed = True
            else:
                intermed = False
                
            MSS_source_img_type = str(self.ui.MSS_source_img_type.currentText())
            MSS_target_img_type = str(self.ui.MSS_target_img_type.currentText())
            
            source_res = str(self.ui.MSS_src_reso.text())
            target_res = str(self.ui.MSS_tgt_reso.text())


            reg_model1 = str(self.ui.MSS_Reg_model1.currentText())
            if reg_model1 == 'import...':
                reg_model1 = self.openFileNameDialog()
            
            if reg_model1 == 'nl':
                QtWidgets.QMessageBox.question(self, 'Warning...', "You have selected a non-linear transformation for initalization. This is not recommended.", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            
            
            project_name = str(self.ui.MSS_textbox_fn.text())
            
            ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H_%M_%S_')

            MSS_params = dict(
                param_mode = 'MSS',
                source_fp = self.MSS_source_fp, 
                source_res = source_res, 
                target1_fp = self.MSS_target_fp, 
                target1_res = target_res, 
                source_mask_fp = self.MSS_src_mask_fp,
                target1_mask_fp = self.MSS_tgt_mask_fp, 
                wd = self.MSS_wd, 
                source_img_type = MSS_source_img_type, 
                target_img_type1 = MSS_target_img_type, 
                reg_model1 = reg_model1,
                project_name = project_name, 
                bounding_box = self.MSS_bounding_box,
                pass_in = ts + project_name
            )
            
            with open(os.path.join(self.MSS_wd,'SSM_'+ts + project_name + '_config', 'w')) as outfile:
                yaml.dump(MSS_params, outfile, default_flow_style=False)
            
            
            print("Starting Registration...")
            print("Project Name: " + project_name)
            
            print("Registering " + os.path.basename(self.MSS_source_fp) +", image type: "+ MSS_source_img_type + " to " + os.path.basename(self.MSS_target_fp) +", image type: "+MSS_target_img_type)

            print("Source -> Target using registration model : " + reg_model1)
                   
            register_MSS(self.MSS_source_fp,source_res, self.MSS_target_fp,target_res, self.MSS_src_mask_fp, self.MSS_tgt_mask_fp, self.MSS_wd, MSS_source_img_type, MSS_target_img_type, reg_model1, project_name, intermediate_output = intermed, pass_in_project_name=True, pass_in = ts + project_name)
            
            QtWidgets.QMessageBox.question(self, 'Registration Finished', "Check output directory for registered images",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return


############# IMS on click buttons
    def IMS_data_oc(self):
        file_name = self.openFileNameDialog()
        ext = os.path.splitext(file_name)[1]
        data_types = ['.csv','.txt','.imzml','.sqlite']
        
        if len(file_name) == 0 or any(ext.lower() in s for s in data_types) == False:
            self.ui.IMS_textbox_source.setText("IMS data not set or incorrect format")
        else:
            self.ui.IMS_textbox_source.setText(os.path.basename(file_name))
            self.IMS_data_fp = file_name
        
    def IMS_oc_wd(self):
        wd_dir = self.openFileDirDialog()
        if len(wd_dir) == 0:
            self.ui.IMS_textbox_wd.setText("working directory not set...")
        else:
            self.ui.IMS_textbox_wd.setText(wd_dir)
            self.IMS_wd = wd_dir
        
    def IMS_generate_maps(self):
        if os.path.exists(self.IMS_data_fp) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set the source image!", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif os.path.exists(self.IMS_wd) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set the working directory!",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        
        else:                            
            ims_res = int(self.ui.IMS_ims_reso.text())
            img_res = int(self.ui.IMS_micro_reso.text())
            padding = int(self.ui.IMS_padding.text())

            project_name = str(self.ui.IMS_textbox_fn.text())
            
            print("Starting IMS pixel map generation...")
            print("Project Name: " + project_name)
            os.chdir(self.IMS_wd)
            pmap = IMS_pixel_maps(self.IMS_data_fp, ims_res, img_res, padding)
            
            pmap.IMS_reg_mask(stamping=True)
            sitk.WriteImage(pmap.IMS_registration_mask, project_name +"_regMask_"+"_imsres" +str(ims_res)+"_imgres"+str(img_res)+"_pad"+str(padding)+".tif",True)
            
            pmap.IMS_idxed_mask()
            sitk.WriteImage(pmap.IMS_indexed_mask, project_name +"_indexMask_"+"_imsres" +str(ims_res)+"_imgres"+str(img_res)+"_pad"+str(padding)+".mha",True)

            QtWidgets.QMessageBox.question(self, 'Pixel Map Generation Finished', "Check output directory for pixel map images",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return



############# MSM on click buttons
    def MSM_oc_src_img(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.MSM_textbox_source.setText("source image not set...")
        else:
            self.ui.MSM_textbox_source.setText(os.path.basename(file_name))
            self.MSM_source_fp = file_name
        
    def MSM_oc_tgt_img1(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.MSM_textbox_target1.setText("target image 1 not set...")
        else:
            self.ui.MSM_textbox_target1.setText(os.path.basename(file_name))
            self.MSM_target1_fp = file_name
    
    def MSM_oc_tgt_img2(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.MSM_textbox_target2.setText("target image 2 not set...")
        else:
            self.ui.MSM_textbox_target2.setText(os.path.basename(file_name))
            self.MSM_target2_fp = file_name
        
    def MSM_oc_src_mask(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.MSM_src_mask_fp = 'none'
        else:
            #self.ui.MSM_textbox_source.setText(os.path.basename(file_name))
            self.MSM_src_mask_fp = file_name
        
    def MSM_oc_tgt_mask1(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.MSM_tgt1_mask_fp = 'none'
        else:
            #self.ui.MSM_textbox_target1.setText(os.path.basename(file_name))
            self.MSM_tgt1_mask_fp = file_name
    
    def MSM_oc_tgt_mask2(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.MSM_tgt2_mask_fp = 'none'
        else:
            #self.ui.MSM_textbox_target2.setText(os.path.basename(file_name))
            self.MSM_tgt2_mask_fp = file_name
            
    def MSM_oc_wd(self):
        wd_dir = self.openFileDirDialog()
        if len(wd_dir) == 0:
            self.ui.MSM_textbox_wd.setText("working directory not set...")
        else:
            self.ui.MSM_textbox_wd.setText(wd_dir)
            self.MSM_wd = wd_dir
            
    def MSM_register(self):
        if os.path.exists(self.MSM_source_fp) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set the source image!", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        
        elif os.path.exists(self.MSM_target1_fp) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set target image 1!",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        
        elif os.path.exists(self.MSM_target2_fp) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set target image 2!",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        
        elif os.path.exists(self.MSM_wd) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set the working directory!",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        
        elif str(self.ui.MSM_source_img_type.currentText()) == "Not set..." or str(self.ui.MSM_target_img_type1.currentText()) == "Not set..." or str(self.ui.MSM_target_img_type2.currentText()) == "Not set...":
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set all image types!",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return    
        
        else:
            xml_params = self.get_params_xml()
            if self.ui.MSM_intermediate_export.isChecked() == True:
                intermed = True
            else:
                intermed = False
            
            MSM_source_img_type = str(self.ui.MSM_source_img_type.currentText())
            MSM_target_img_type1 = str(self.ui.MSM_target_img_type1.currentText())
            MSM_target_img_type2 = str(self.ui.MSM_target_img_type2.currentText())
            
            source_res = str(self.ui.MSM_src_reso.text())
            target1_res = str(self.ui.MSM_tgt1_reso.text())
            target2_res = str(self.ui.MSM_tgt2_reso.text())
            
            reg_model1 = str(self.ui.MSM_Reg_model1.currentText())
            if reg_model1 == 'import...':
                reg_model1 = self.openFileNameDialog()
            reg_model2 = str(self.ui.MSM_Reg_model2.currentText())
            
            if reg_model2 == 'import...':
                reg_model2 = self.openFileNameDialog()
            project_name = str(self.ui.MSM_textbox_fn.text())
            
            print("Starting Registration...")
            print("Project Name: " + project_name)
            
            print("Registering " + os.path.basename(self.MSM_source_fp) +", image type: "+ MSM_source_img_type + " to " + os.path.basename(self.MSM_target1_fp) +", image type: "+MSM_target_img_type1)
            
            print("Then registering " + os.path.basename(self.MSM_target1_fp) +", image type: "+MSM_target_img_type1 + " to "+ os.path.basename(self.MSM_target2_fp) +", imasge type: "+MSM_target_img_type2)
            
            print("Source -> Target 1 using registration model : " + reg_model1)
            print("Target1 -> Target 2 using registration model : " + reg_model2)
                   
            register_MSM(self.MSM_source_fp,source_res ,self.MSM_target1_fp, target1_res,self.MSM_target2_fp, target2_res, self.MSM_src_mask_fp, self.MSM_tgt1_mask_fp, self.MSM_tgt2_mask_fp, self.MSM_wd, MSM_source_img_type, MSM_target_img_type1, MSM_target_img_type2, reg_model1, reg_model2, project_name, xml_params, intermediate_output = intermed )
            
            QtWidgets.QMessageBox.question(self, 'Registration Finished', "Check output directory for registered images",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

            return

############# HDR on click buttons
    def HDR_oc_src_img(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.HDR_textbox_source.setText("source image not set...")
        else:
            self.ui.HDR_textbox_source.setText(os.path.basename(file_name))
            self.HDR_source_fp = file_name
        
    def HDR_oc_tgt_img(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.HDR_textbox_target.setText("target image 1 not set...")
        else:
            self.ui.HDR_textbox_target.setText(os.path.basename(file_name))
            self.HDR_target_fp = file_name
            
    def HDR_oc_ijrois(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.HDR_textbox_rois.setText("rois not set...")
        else:
            self.ui.HDR_textbox_rois.setText(os.path.basename(file_name))
            self.HDR_ijrois_fp = file_name
            
    def HDR_oc_wd(self):
        wd_dir = self.openFileDirDialog()
        if len(wd_dir) == 0:
            self.ui.HDR_textbox_wd.setText("working directory not set...")
        else:
            self.ui.HDR_textbox_wd.setText(wd_dir)
            self.HDR_wd = wd_dir
        
    def HDR_register(self):
        if os.path.exists(self.HDR_source_fp) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set the source image!", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        
        elif os.path.exists(self.HDR_target_fp) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set the target image !",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif os.path.exists(self.HDR_ijrois_fp) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set rois file path !",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif os.path.exists(self.HDR_wd) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set the working directory!",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
                
        else:
            #xml_params = self.get_params_xml()
            
            ims_resolution = str(self.ui.HDR_ims_reso.text())
            
            ims_method = str(self.ui.HDR_par_fp.text())
            roi_names = str(self.ui.HDR_roi_names.text())
            nsplit = str(self.ui.HDR_no_splits.text())
            
        
            project_name = str(self.ui.HDR_textbox_fn.text())
            
            print("Starting Registration...")
            print("Project Name: " + project_name)
            
            print("Registering " + os.path.basename(self.HDR_source_fp) +" to " + os.path.basename(self.HDR_target_fp))

            print("Source -> Target using registration model : flexImaging correction")
            bruker_output_xmls(self.HDR_source_fp, self.HDR_target_fp, self.HDR_wd, self.HDR_ijrois_fp, project_name, ims_resolution = ims_resolution, ims_method = ims_method, roi_name= roi_names, splits = nsplit)
            
            QtWidgets.QMessageBox.question(self, 'Registration Finished', "Check output directory for XML files",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

            return

############# HDR on click buttons
    def TFM_oc_src_img(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.TFM_textbox_source.setText("source image not set...")
        else:
            self.ui.TFM_textbox_source.setText(os.path.basename(file_name))
            self.TFM_source_fp = file_name
    
    def TFM_oc_wd(self):
        wd_dir = self.openFileDirDialog()
        if len(wd_dir) == 0:
            self.ui.TFM_textbox_wd.setText("working directory not set...")
        else:
            self.ui.TFM_textbox_wd.setText(wd_dir)
            self.TFM_wd = wd_dir
            
    def TFM_oc_transform(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            return
        else:
            tform = sitk.ReadParameterFile(file_name)
            self.TFM_transforms.append(tform)
            self.ui.TFM_tform_list.addItem(file_name)
            
        
    def TFM_register(self):
        if os.path.exists(self.TFM_source_fp) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set the source image!", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        
        elif len(self.TFM_transforms) == 0:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't added any transformations!",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        
        elif len(self.TFM_wd) == False:
            QtWidgets.QMessageBox.question(self, 'Error!', "You haven't set the working directory!",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        
        else:
            #xml_params = self.get_params_xml()
            #fix
            #src_reso = str(self.ui.TFM_ims_reso.text())
            src_reso = 0.92
            project_name = str(self.ui.TFM_textbox_fn.text())
            
            print("Starting Registration...")
            print("Project Name: " + project_name)
            
            print("Registering " + os.path.basename(self.HDR_source_fp) +" to " + os.path.basename(self.HDR_target_fp))

            print("Source -> Target using registration model : flexImaging correction")
            transform_from_gui(self.TFM_source_fp, self.TFM_transforms, self.TFM_wd, src_reso, project_name)
            
            QtWidgets.QMessageBox.question(self, 'Registration Finished', "Check output directory for XML files",QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

            return

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
