# -*- coding: utf-8 -*-
"""
@author: pattenh1
"""

import sys
import os
from PyQt5 import QtWidgets, uic, QtCore
from regToolboxMSRC.register_MSM import register_MSM
from regToolboxMSRC.register_SSM import register_SSM
from regToolboxMSRC.register_SSS import register_SSS
from regToolboxMSRC.register_MSS import register_MSS
from regToolboxMSRC.find_IMS_overlap import IMS_ablation_overlap
from regToolboxMSRC.roi_extraction import extract_ROI_coordinates
from regToolboxMSRC.utils.reg_utils import transform_from_gui
from regToolboxMSRC.utils.ims_utils import ImsPixelMaps
from regToolboxMSRC.bruker_hist_directed import bruker_output_xmls
from regToolboxMSRC.arbitrary_img_tform import arbitrary_transform
import SimpleITK as sitk
import pkg_resources
import time
import datetime
import yaml

#TODO: make this less shitty


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        '''Initializes the default parameters and links up GUI buttons
        to functions.
        '''
        super(MainWindow, self).__init__()
        self.SSM_source_fp = 'fp'
        self.SSM_target1_fp = 'fp'
        self.SSM_target2_fp = 'fp'
        self.SSM_src_mask_fp = None
        self.SSM_tgt1_mask_fp = None
        self.SSM_tgt2_mask_fp = None
        self.SSM_wd = ''
        self.SSM_bounding_box = False
        self.SSM_reg_model1 = 'affine'
        self.SSM_reg_model2 = 'affine'

        self.MSM_source_fp = 'fp'
        self.MSM_target1_fp = 'fp'
        self.MSM_target2_fp = 'fp'
        self.MSM_src_mask_fp = None
        self.MSM_tgt1_mask_fp = None
        self.MSM_tgt2_mask_fp = None
        self.MSM_wd = ''
        self.MSM_bounding_box = False
        self.MSM_reg_model1 = 'affine'
        self.MSM_reg_model2 = 'affine'

        self.SSS_source_fp = 'fp'
        self.SSS_target_fp = 'fp'
        self.SSS_src_mask_fp = None
        self.SSS_tgt_mask_fp = None
        self.SSS_wd = ''
        self.SSS_bounding_box = False
        self.SSS_reg_model1 = 'affine'

        self.MSS_source_fp = 'fp'
        self.MSS_target_fp = 'fp'
        self.MSS_src_mask_fp = None
        self.MSS_tgt_mask_fp = None
        self.MSS_wd = ''
        self.MSS_bounding_box = False
        self.MSS_reg_model1 = 'affine'

        self.HDR_source_fp = 'fp'
        self.HDR_target_fp = 'fp'
        self.HDR_ijrois_fp = 'fp'
        self.HDR_wd = ''

        self.IMS_data_fp = 'fp'
        self.IMS_wd = ''

        self.IMS_SS_source_fp = 'fp'
        self.IMS_SS_target_fp = 'fp'
        self.IMS_SS_source_key_fp = 'fp'
        self.IMS_SS_target_key_fp = 'fp'
        self.IMS_SS_init_tform_fp = 'fp'
        self.IMS_SS_nl_tform_fp = 'fp'
        self.IMS_SS_wd = ''

        self.IMS_CE_source_fp = 'fp'
        self.IMS_CE_source_key_fp = 'fp'
        self.IMS_CE_source_key_fp = 'fp'
        self.IMS_CE_wd = ''

        self.TFM_transforms = []
        self.TFM_source_fp = 'fp'
        self.TFM_ij_rois_fp = None
        self.TFM_wd = ''

        #load in data stored in package
        resource_package = 'regToolboxMSRC'
        resource_path = '/'.join(('GUI', 'MSRC_toolbox_v0_3.ui'))
        template = pkg_resources.resource_stream(resource_package,
                                                 resource_path)

        self.ui = uic.loadUi(template)
        self.ui.show()

        #self.ui.SaveParam.clicked.connect(self.SaveParam_oc)
        #self.ui.LoadParam.clicked.connect(self.LoadParam_oc)

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
        self.ui.SSM_source_img_type.addItem("RGB_l")
        self.ui.SSM_source_img_type.addItem("AF")

        self.ui.SSM_target_img_type1.addItem("Not set...")
        self.ui.SSM_target_img_type1.addItem("RGB_l")
        self.ui.SSM_target_img_type1.addItem("AF")

        self.ui.SSM_target_img_type2.addItem("Not set...")
        self.ui.SSM_target_img_type2.addItem("RGB_l")
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
        self.ui.MSM_source_img_type.addItem("RGB_l")
        self.ui.MSM_source_img_type.addItem("AF")

        self.ui.MSM_target_img_type1.addItem("Not set...")
        self.ui.MSM_target_img_type1.addItem("RGB_l")
        self.ui.MSM_target_img_type1.addItem("AF")

        self.ui.MSM_target_img_type2.addItem("Not set...")
        self.ui.MSM_target_img_type2.addItem("RGB_l")
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
        self.ui.SSS_source_img_type.addItem("RGB_l")
        self.ui.SSS_source_img_type.addItem("AF")

        self.ui.SSS_target_img_type.addItem("Not set...")
        self.ui.SSS_target_img_type.addItem("RGB_l")
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
        self.ui.MSS_source_img_type.addItem("RGB_l")
        self.ui.MSS_source_img_type.addItem("AF")

        self.ui.MSS_target_img_type.addItem("Not set...")
        self.ui.MSS_target_img_type.addItem("RGB_l")
        self.ui.MSS_target_img_type.addItem("AF")

        #image type combo boxs
        self.ui.MSS_button_register_images.clicked.connect(self.MSS_register)

        ############# IMS: image buttons
        self.ui.IMS_button_source.clicked.connect(self.IMS_data_oc)

        #set wd button
        self.ui.IMS_button_wd.clicked.connect(self.IMS_oc_wd)

        #image type combo boxs
        self.ui.IMS_button_generate_map.clicked.connect(self.IMS_generate_maps)

        ############# IMS_SS: image buttons
        self.ui.IMS_SS_button_source.clicked.connect(self.IMS_SS_oc_src_img)
        self.ui.IMS_SS_button_target.clicked.connect(self.IMS_SS_oc_tgt_img)

        self.ui.IMS_SS_button_source_key.clicked.connect(
            self.IMS_SS_oc_src_key)
        self.ui.IMS_SS_button_target_key.clicked.connect(
            self.IMS_SS_oc_tgt_key)

        self.ui.IMS_SS_button_init_tform.clicked.connect(
            self.IMS_SS_oc_init_tform)
        self.ui.IMS_SS_button_nl_tform.clicked.connect(self.IMS_SS_oc_nl_tform)

        #set wd button
        self.ui.IMS_SS_button_wd.clicked.connect(self.IMS_SS_oc_wd)

        self.ui.IMS_SS_button_overlap.clicked.connect(self.IMS_SS_overlap)

        ############# IMS_CE: image buttons
        self.ui.IMS_CE_button_source.clicked.connect(self.IMS_CE_oc_src_img)

        self.ui.IMS_CE_button_source_key.clicked.connect(
            self.IMS_CE_oc_src_key)

        self.ui.IMS_CE_button_annotations.clicked.connect(
            self.IMS_CE_oc_annotations)

        self.ui.IMS_CE_button_wd.clicked.connect(self.IMS_CE_oc_wd)

        self.ui.IMS_CE_button_extract_coords.clicked.connect(
            self.IMS_CE_extraction)

        ############# HDR: image buttons
        self.ui.HDR_button_source.clicked.connect(self.HDR_oc_src_img)
        self.ui.HDR_button_target.clicked.connect(self.HDR_oc_tgt_img)
        self.ui.HDR_button_rois.clicked.connect(self.HDR_oc_ijrois)

        #set wd button
        self.ui.HDR_button_wd.clicked.connect(self.HDR_oc_wd)

        self.ui.HDR_button_register_images.clicked.connect(self.HDR_register)

        ############# TFM: image buttons
        self.ui.TFM_button_source.clicked.connect(self.TFM_oc_src_img)
        self.ui.TFM_button_ijrois.clicked.connect(self.TFM_oc_ijrois)

        self.ui.TFM_button_transform.clicked.connect(self.TFM_oc_transform)

        ##set wd button
        self.ui.TFM_button_wd.clicked.connect(self.TFM_oc_wd)

        self.ui.TFM_button_apply_transform.clicked.connect(self.TFM_register)

        ############# Parameter loading/saving buttons
        self.ui.SSM_save_params.clicked.connect(self.SSM_oc_save_param)
        self.ui.SSM_load_params.clicked.connect(self.SSM_oc_load_param)

        self.ui.MSM_save_params.clicked.connect(self.MSM_oc_save_param)
        self.ui.MSM_load_params.clicked.connect(self.MSM_oc_load_param)

        self.ui.SSS_save_params.clicked.connect(self.SSS_oc_save_param)
        self.ui.SSS_load_params.clicked.connect(self.SSS_oc_load_param)

        self.ui.MSS_save_params.clicked.connect(self.MSS_oc_save_param)
        self.ui.MSS_load_params.clicked.connect(self.MSS_oc_load_param)

        ##TODO : add param loading/saving for IMS_SS
        #self.ui.MSS_save_params.clicked.connect(self.MSS_oc_save_param)
        #self.ui.MSS_load_params.clicked.connect(self.MSS_oc_load_param)

############# file path functions

    def openFileNameDialog(self, dialog_str=''):
        if dialog_str == '':
            dialog_str = 'Open file...'
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, dialog_str, "",
            "All Files (*);;Tiff Files (*.tif);;YAML Files (*.yaml)")
        return (file_name)

    def openFileDirDialog(self, dialog_str=''):
        if dialog_str == '':
            dialog_str = "Select Directory..."
        wd = QtWidgets.QFileDialog.getExistingDirectory(self, dialog_str)
        return (wd)

    def saveFileDialog(self):
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save parameter file (.yaml)", "",
            "All Files (*);;YAML Files (*.yaml)")
        return fileName

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
            self.SSM_src_mask_fp = None
        else:
            self.ui.SSM_textbox_source_mask.setText(
                os.path.basename(file_name))
            self.SSM_src_mask_fp = file_name

    def SSM_oc_tgt_mask1(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.SSM_tgt1_mask_fp = None
        else:
            self.ui.SSM_textbox_target1_mask.setText(
                os.path.basename(file_name))
            self.SSM_tgt1_mask_fp = file_name

    def SSM_oc_tgt_mask2(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.SSM_tgt2_mask_fp = None
        else:
            self.ui.SSM_textbox_target2_mask.setText(
                os.path.basename(file_name))
            self.SSM_tgt2_mask_fp = file_name

    def SSM_oc_wd(self):
        wd_dir = self.openFileDirDialog()
        if len(wd_dir) == 0:
            self.ui.SSM_textbox_wd.setText("working directory not set...")
        else:
            self.ui.SSM_textbox_wd.setText(wd_dir)
            self.SSM_wd = wd_dir

    def SSM_register(self, params=True):
        if os.path.exists(self.SSM_source_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the source image!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif os.path.exists(self.SSM_target1_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set target image 1!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif os.path.exists(self.SSM_target2_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set target image 2!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif os.path.exists(self.SSM_wd) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the working directory!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif str(self.ui.SSM_source_img_type.currentText(
        )) == "Not set..." or str(self.ui.SSM_target_img_type1.currentText(
        )) == "Not set..." or str(
                self.ui.SSM_target_img_type2.currentText()) == "Not set...":
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set all image types!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        else:
            if self.ui.SSM_intermediate_export.isChecked() == True:
                intermed = True
            else:
                intermed = False

            #xml_params = self.get_params_xml()

            SSM_source_img_type = str(
                self.ui.SSM_source_img_type.currentText())
            SSM_target_img_type1 = str(
                self.ui.SSM_target_img_type1.currentText())
            SSM_target_img_type2 = str(
                self.ui.SSM_target_img_type2.currentText())

            source_res = str(self.ui.SSM_src_reso.text())
            target1_res = str(self.ui.SSM_tgt1_reso.text())
            target2_res = str(self.ui.SSM_tgt2_reso.text())

            if self.ui.SSM_Reg_model1.currentText(
            ) == 'import...' and self.SSM_reg_model1 == 'affine':
                self.SSM_reg_model1 = self.openFileNameDialog()
            elif self.ui.SSM_Reg_model1.currentText(
            ) == 'import...' and self.SSM_reg_model1 != 'affine':
                self.SSM_reg_model1 = self.SSM_reg_model1
            else:
                self.SSM_reg_model1 = self.ui.SSM_Reg_model1.currentText()

            if self.ui.SSM_Reg_model2.currentText(
            ) == 'import...' and self.SSM_reg_model2 == 'affine':
                self.SSM_reg_model2 = self.openFileNameDialog()
            elif self.ui.SSM_Reg_model2.currentText(
            ) == 'import...' and self.SSM_reg_model2 != 'affine':
                self.SSM_reg_model2 = self.SSM_reg_model2
            else:
                self.SSM_reg_model2 = self.ui.SSM_Reg_model2.currentText()

            project_name = str(self.ui.SSM_textbox_fn.text())

            ts = datetime.datetime.fromtimestamp(
                time.time()).strftime('%Y%m%d_%H_%M_%S_')

            SSM_params = dict(
                param_mode='SSM',
                source_fp=self.SSM_source_fp,
                source_res=source_res,
                target1_fp=self.SSM_target1_fp,
                target1_res=target1_res,
                target2_fp=self.SSM_target2_fp,
                target2_res=target2_res,
                source_mask_fp=self.SSM_src_mask_fp,
                target1_mask_fp=self.SSM_tgt1_mask_fp,
                target2_mask_fp=self.SSM_tgt2_mask_fp,
                wd=self.SSM_wd,
                source_img_type=SSM_source_img_type,
                target_img_type1=SSM_target_img_type1,
                target_img_type2=SSM_target_img_type2,
                reg_model1=self.SSM_reg_model1,
                ui_reg_model1=self.ui.SSM_Reg_model1.currentText(),
                reg_model2=self.SSM_reg_model2,
                ui_reg_model2=self.ui.SSM_Reg_model2.currentText(),
                project_name=project_name,
                intermediate_output=intermed,
                bounding_box_source=True,
                bounding_box_target1=True,
                bounding_box_target2=True,
                pass_in=ts + project_name)

            with open(
                    os.path.join(self.SSM_wd,
                                 'SSM_' + ts + project_name + '_config.yaml'),
                    'w') as outfile:
                yaml.dump(SSM_params, outfile, default_flow_style=False)

            if params == False:
                print("Starting Registration...")
                print("Project Name: " + project_name)

                print("Registering " + os.path.basename(self.SSM_source_fp) +
                      ", image type: " + SSM_source_img_type + " to " +
                      os.path.basename(self.SSM_target1_fp) +
                      ", image type: " + SSM_target_img_type1)

                print("Then registering " + os.path.basename(
                    self.SSM_target1_fp) + ", image type: " +
                      SSM_target_img_type1 + " to " + os.path.basename(
                          self.SSM_target2_fp) + ", imasge type: " +
                      SSM_target_img_type2)

                print("Source -> Target 1 using registration model : " +
                      self.SSM_reg_model1)
                print("Target1 -> Target 2 using registration model : " +
                      self.SSM_reg_model2)

                register_SSM(
                    self.SSM_source_fp,
                    source_res,
                    self.SSM_target1_fp,
                    target1_res,
                    self.SSM_target2_fp,
                    target2_res,
                    self.SSM_src_mask_fp,
                    self.SSM_tgt1_mask_fp,
                    self.SSM_tgt2_mask_fp,
                    self.SSM_wd,
                    SSM_source_img_type,
                    SSM_target_img_type1,
                    SSM_target_img_type2,
                    self.SSM_reg_model1,
                    self.SSM_reg_model2,
                    project_name,
                    intermediate_output=intermed,
                    pass_in_project_name=True,
                    pass_in=ts + project_name)

                QtWidgets.QMessageBox.question(
                    self, 'Registration Finished',
                    "Check output directory for registered images",
                    QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

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
            self.SSS_src_mask_fp = None
        else:
            self.ui.SSS_textbox_source_mask.setText(
                os.path.basename(file_name))
            self.SSS_src_mask_fp = file_name

    def SSS_oc_tgt_mask(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.SSS_tgt1_mask_fp = None
        else:
            self.ui.SSS_textbox_target_mask.setText(
                os.path.basename(file_name))
            self.SSS_tgt_mask_fp = file_name

    def SSS_oc_wd(self):
        wd_dir = self.openFileDirDialog()
        if len(wd_dir) == 0:
            self.ui.SSS_textbox_wd.setText("working directory not set...")
        else:
            self.ui.SSS_textbox_wd.setText(wd_dir)
            self.SSS_wd = wd_dir

    def SSS_register(self, params=True):
        if os.path.exists(self.SSS_source_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the source image!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif os.path.exists(self.SSS_target_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the target image !",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif os.path.exists(self.SSS_wd) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the working directory!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif str(self.ui.SSS_source_img_type.currentText(
        )) == "Not set..." or str(
                self.ui.SSS_target_img_type.currentText()) == "Not set...":
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set all image types!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        else:
            #xml_params = self.get_params_xml()

            SSS_source_img_type = str(
                self.ui.SSS_source_img_type.currentText())
            SSS_target_img_type = str(
                self.ui.SSS_target_img_type.currentText())

            source_res = str(self.ui.SSS_src_reso.text())
            target_res = str(self.ui.SSS_tgt_reso.text())

            if self.ui.SSS_Reg_model1.currentText(
            ) == 'import...' and self.SSS_reg_model1 == 'affine':
                self.SSS_reg_model1 = self.openFileNameDialog()
            elif self.ui.SSS_Reg_model1.currentText(
            ) == 'import...' and self.SSS_reg_model1 != 'affine':
                self.SSS_reg_model1 = self.SSS_reg_model1
            else:
                self.SSS_reg_model1 = self.ui.SSS_Reg_model1.currentText()

            project_name = str(self.ui.SSS_textbox_fn.text())

            ts = datetime.datetime.fromtimestamp(
                time.time()).strftime('%Y%m%d_%H_%M_%S_')

            SSS_params = dict(
                param_mode='SSS',
                source_fp=self.SSS_source_fp,
                source_res=source_res,
                target_fp=self.SSS_target_fp,
                target_res=target_res,
                source_mask_fp=self.SSS_src_mask_fp,
                target1_mask_fp=self.SSS_tgt_mask_fp,
                wd=self.SSS_wd,
                source_img_type=SSS_source_img_type,
                target_img_type=SSS_target_img_type,
                reg_model1=self.SSS_reg_model1,
                ui_reg_model1=self.ui.SSS_Reg_model1.currentText(),
                project_name=project_name,
                bounding_box_source=True,
                bounding_box_target=True,
                pass_in=ts + project_name)

            with open(
                    os.path.join(self.SSS_wd,
                                 'SSS_' + ts + project_name + '_config.yaml'),
                    'w') as outfile:
                yaml.dump(SSS_params, outfile, default_flow_style=False)

            if params == False:
                print("Starting Registration...")
                print("Project Name: " + project_name)

                print("Registering " + os.path.basename(self.SSS_source_fp) +
                      ", image type: " + SSS_source_img_type + " to " +
                      os.path.basename(self.SSS_target_fp) + ", image type: " +
                      SSS_target_img_type)

                print("Source -> Target using registration model : " +
                      self.SSS_reg_model1)

                register_SSS(
                    self.SSS_source_fp,
                    source_res,
                    self.SSS_target_fp,
                    target_res,
                    self.SSS_src_mask_fp,
                    self.SSS_tgt_mask_fp,
                    self.SSS_wd,
                    SSS_source_img_type,
                    SSS_target_img_type,
                    self.SSS_reg_model1,
                    project_name,
                    pass_in_project_name=True,
                    pass_in=ts + project_name)

                QtWidgets.QMessageBox.question(
                    self, 'Registration Finished',
                    "Check output directory for registered images",
                    QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

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
            self.MSS_src_mask_fp = None
        else:
            self.ui.MSS_textbox_source_mask.setText(
                os.path.basename(file_name))
            self.MSS_src_mask_fp = file_name

    def MSS_oc_tgt_mask(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.MSS_tgt1_mask_fp = None
        else:
            self.ui.MSS_textbox_target_mask.setText(
                os.path.basename(file_name))
            self.MSS_tgt_mask_fp = file_name

    def MSS_oc_wd(self):
        wd_dir = self.openFileDirDialog()
        if len(wd_dir) == 0:
            self.ui.MSS_textbox_wd.setText("working directory not set...")
        else:
            self.ui.MSS_textbox_wd.setText(wd_dir)
            self.MSS_wd = wd_dir

    def MSS_register(self, params=True):
        if os.path.exists(self.MSS_source_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the source image!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif os.path.exists(self.MSS_target_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the target image !",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif os.path.exists(self.MSS_wd) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the working directory!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif str(self.ui.MSS_source_img_type.currentText(
        )) == "Not set..." or str(
                self.ui.MSS_target_img_type.currentText()) == "Not set...":
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set all image types!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        else:
            #xml_params = self.get_params_xml()

            if self.ui.MSS_intermediate_export.isChecked() == True:
                intermed = True
            else:
                intermed = False

            MSS_source_img_type = str(
                self.ui.MSS_source_img_type.currentText())
            MSS_target_img_type = str(
                self.ui.MSS_target_img_type.currentText())

            source_res = str(self.ui.MSS_src_reso.text())
            target_res = str(self.ui.MSS_tgt_reso.text())

            if self.ui.MSS_Reg_model1.currentText(
            ) == 'import...' and self.MSS_reg_model1 == 'affine':
                self.MSS_reg_model1 = self.openFileNameDialog()
            elif self.ui.MSS_Reg_model1.currentText(
            ) == 'import...' and self.MSS_reg_model1 != 'affine':
                self.MSS_reg_model1 = self.MSS_reg_model1
            else:
                self.MSS_reg_model1 = self.ui.MSS_Reg_model1.currentText()

            if self.MSS_reg_model1 == 'nl':
                QtWidgets.QMessageBox.question(
                    self, 'Warning...',
                    "You have selected a non-linear transformation for initalization. This is not recommended.",
                    QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

            project_name = str(self.ui.MSS_textbox_fn.text())

            ts = datetime.datetime.fromtimestamp(
                time.time()).strftime('%Y%m%d_%H_%M_%S_')

            MSS_params = dict(
                param_mode='MSS',
                source_fp=self.MSS_source_fp,
                source_res=source_res,
                target_fp=self.MSS_target_fp,
                target_res=target_res,
                source_mask_fp=self.MSS_src_mask_fp,
                target_mask_fp=self.MSS_tgt_mask_fp,
                wd=self.MSS_wd,
                source_img_type=MSS_source_img_type,
                target_img_type=MSS_target_img_type,
                reg_model1=self.MSS_reg_model1,
                ui_reg_model1=self.ui.MSS_Reg_model1.currentText(),
                project_name=project_name,
                bounding_box_source=True,
                bounding_box_target=True,
                pass_in=ts + project_name)

            with open(
                    os.path.join(self.MSS_wd,
                                 'MSS_' + ts + project_name + '_config.yaml'),
                    'w') as outfile:
                yaml.dump(MSS_params, outfile, default_flow_style=False)

            if params == False:
                print("Starting Registration...")
                print("Project Name: " + project_name)

                print("Registering " + os.path.basename(self.MSS_source_fp) +
                      ", image type: " + MSS_source_img_type + " to " +
                      os.path.basename(self.MSS_target_fp) + ", image type: " +
                      MSS_target_img_type)

                print("Source -> Target using registration model : " +
                      self.MSS_reg_model1)

                register_MSS(
                    self.MSS_source_fp,
                    source_res,
                    self.MSS_target_fp,
                    target_res,
                    self.MSS_src_mask_fp,
                    self.MSS_tgt_mask_fp,
                    self.MSS_wd,
                    MSS_source_img_type,
                    MSS_target_img_type,
                    self.MSS_reg_model1,
                    project_name,
                    intermediate_output=intermed,
                    pass_in_project_name=True,
                    pass_in=ts + project_name)

                QtWidgets.QMessageBox.question(
                    self, 'Registration Finished',
                    "Check output directory for registered images",
                    QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
                return

############# IMS on click buttons

    def IMS_data_oc(self):
        file_name = self.openFileNameDialog()
        ext = os.path.splitext(file_name)[1]
        data_types = ['.csv', '.txt', '.imzml', '.sqlite']

        if len(file_name) == 0 or any(ext.lower() in s
                                      for s in data_types) == False:
            self.ui.IMS_textbox_source.setText(
                "IMS data not set or incorrect format")
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
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the source image!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif os.path.exists(self.IMS_wd) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the working directory!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        else:
            ims_res = int(self.ui.IMS_ims_reso.text())
            img_res = int(self.ui.IMS_micro_reso.text())
            padding = int(self.ui.IMS_padding.text())

            project_name = str(self.ui.IMS_textbox_fn.text())

            print("Starting IMS pixel map generation...")
            print("Project Name: " + project_name)
            os.chdir(self.IMS_wd)
            ims_mapping = ImsPixelMaps(self.IMS_data_fp, ims_res, img_res,
                                       padding)

            ims_mapping.generate_reg_mask(stamping=True)
            sitk.WriteImage(
                ims_mapping.IMS_reg_template,
                project_name + "_regMask" + "_IMSres" + str(ims_res) +
                "_MicroRes" + str(img_res) + "_pad" + str(padding) + ".tif",
                True)

            ims_mapping.generate_idx_mask()
            sitk.WriteImage(
                ims_mapping.IMS_indexed_mask,
                project_name + "_indexMask_" + "_imsres" + str(ims_res) +
                "_imgres" + str(img_res) + "_pad" + str(padding) + ".mha",
                True)

            ims_mapping.spots.to_csv(
                project_name + "_IMS_mapping_key.csv",
                index=True,
                index_label='pixel_idx')

            QtWidgets.QMessageBox.question(
                self, 'Pixel Map Generation Finished',
                "Check output directory for pixel map images",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
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
            self.MSM_src_mask_fp = None
        else:
            self.ui.MSM_textbox_source_mask.setText(
                os.path.basename(file_name))
            self.MSM_src_mask_fp = file_name

    def MSM_oc_tgt_mask1(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.MSM_tgt1_mask_fp = None
        else:
            self.ui.MSM_textbox_target1_mask.setText(
                os.path.basename(file_name))
            self.MSM_tgt1_mask_fp = file_name

    def MSM_oc_tgt_mask2(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.MSM_tgt2_mask_fp = None
        else:
            self.ui.MSM_textbox_target2_mask.setText(
                os.path.basename(file_name))
            self.MSM_tgt2_mask_fp = file_name

    def MSM_oc_wd(self):
        wd_dir = self.openFileDirDialog()
        if len(wd_dir) == 0:
            self.ui.MSM_textbox_wd.setText("working directory not set...")
        else:
            self.ui.MSM_textbox_wd.setText(wd_dir)
            self.MSM_wd = wd_dir

    def MSM_register(self, params=True):
        if os.path.exists(self.MSM_source_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the source image!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif os.path.exists(self.MSM_target1_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set target image 1!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif os.path.exists(self.MSM_target2_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set target image 2!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif os.path.exists(self.MSM_wd) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the working directory!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif str(self.ui.MSM_source_img_type.currentText(
        )) == "Not set..." or str(self.ui.MSM_target_img_type1.currentText(
        )) == "Not set..." or str(
                self.ui.MSM_target_img_type2.currentText()) == "Not set...":
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set all image types!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        else:
            #xml_params = self.get_params_xml()
            if self.ui.MSM_intermediate_export.isChecked() == True:
                intermed = True
            else:
                intermed = False

            MSM_source_img_type = str(
                self.ui.MSM_source_img_type.currentText())
            MSM_target_img_type1 = str(
                self.ui.MSM_target_img_type1.currentText())
            MSM_target_img_type2 = str(
                self.ui.MSM_target_img_type2.currentText())

            source_res = str(self.ui.MSM_src_reso.text())
            target1_res = str(self.ui.MSM_tgt1_reso.text())
            target2_res = str(self.ui.MSM_tgt2_reso.text())

            if self.ui.MSM_Reg_model1.currentText(
            ) == 'import...' and self.MSM_reg_model1 == 'affine':
                self.MSM_reg_model1 = self.openFileNameDialog()
            elif self.ui.MSM_Reg_model1.currentText(
            ) == 'import...' and self.MSM_reg_model1 != 'affine':
                self.MSM_reg_model1 = self.MSM_reg_model1
            else:
                self.MSM_reg_model1 = self.ui.MSM_Reg_model1.currentText()

            if self.ui.MSM_Reg_model2.currentText(
            ) == 'import...' and self.MSM_reg_model2 == 'affine':
                self.MSM_reg_model2 = self.openFileNameDialog()
            elif self.ui.MSM_Reg_model2.currentText(
            ) == 'import...' and self.MSM_reg_model2 != 'affine':
                self.MSM_reg_model2 = self.MSM_reg_model2
            else:
                self.MSM_reg_model2 = self.ui.MSM_Reg_model2.currentText()

            project_name = str(self.ui.MSM_textbox_fn.text())

            ts = datetime.datetime.fromtimestamp(
                time.time()).strftime('%Y%m%d_%H_%M_%S_')

            MSM_params = dict(
                param_mode='MSM',
                source_fp=self.MSM_source_fp,
                source_res=source_res,
                target1_fp=self.MSM_target1_fp,
                target1_res=target1_res,
                target2_fp=self.MSM_target2_fp,
                target2_res=target2_res,
                source_mask_fp=self.MSM_src_mask_fp,
                target1_mask_fp=self.MSM_tgt1_mask_fp,
                target2_mask_fp=self.MSM_tgt2_mask_fp,
                wd=self.MSM_wd,
                source_img_type=MSM_source_img_type,
                target_img_type1=MSM_target_img_type1,
                target_img_type2=MSM_target_img_type2,
                reg_model1=self.MSM_reg_model1,
                ui_reg_model1=self.ui.MSM_Reg_model1.currentText(),
                reg_model2=self.MSM_reg_model2,
                ui_reg_model2=self.ui.MSM_Reg_model2.currentText(),
                project_name=project_name,
                intermediate_output=intermed,
                bounding_box_source=True,
                bounding_box_target1=True,
                bounding_box_target2=True,
                pass_in=ts + project_name)

            with open(
                    os.path.join(self.MSM_wd,
                                 'MSM_' + ts + project_name + '_config.yaml'),
                    'w') as outfile:
                yaml.dump(MSM_params, outfile, default_flow_style=False)

            if params == False:
                print("Starting Registration...")
                print("Project Name: " + project_name)

                print("Registering " + os.path.basename(self.MSM_source_fp) +
                      ", image type: " + MSM_source_img_type + " to " +
                      os.path.basename(self.MSM_target1_fp) +
                      ", image type: " + MSM_target_img_type1)

                print("Then registering " + os.path.basename(
                    self.MSM_target1_fp) + ", image type: " +
                      MSM_target_img_type1 + " to " + os.path.basename(
                          self.MSM_target2_fp) + ", imasge type: " +
                      MSM_target_img_type2)

                print("Source -> Target 1 using registration model : " +
                      self.MSM_reg_model1)
                print("Target1 -> Target 2 using registration model : " +
                      self.MSM_reg_model2)

                register_MSM(
                    self.MSM_source_fp,
                    source_res,
                    self.MSM_target1_fp,
                    target1_res,
                    self.MSM_target2_fp,
                    target2_res,
                    self.MSM_src_mask_fp,
                    self.MSM_tgt1_mask_fp,
                    self.MSM_tgt2_mask_fp,
                    self.MSM_wd,
                    MSM_source_img_type,
                    MSM_target_img_type1,
                    MSM_target_img_type2,
                    self.MSM_reg_model1,
                    self.MSM_reg_model2,
                    project_name,
                    intermediate_output=intermed,
                    pass_in_project_name=True,
                    pass_in=ts + project_name)

                QtWidgets.QMessageBox.question(
                    self, 'Registration Finished',
                    "Check output directory for registered images",
                    QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

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
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the source image!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif os.path.exists(self.HDR_target_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the target image !",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif os.path.exists(self.HDR_ijrois_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set rois file path !",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif os.path.exists(self.HDR_wd) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the working directory!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        else:
            #xml_params = self.get_params_xml()

            ims_resolution = str(self.ui.HDR_ims_reso.text())

            ims_method = str(self.ui.HDR_par_fp.text())
            roi_names = str(self.ui.HDR_roi_names.text())
            nsplit = str(self.ui.HDR_no_splits.text())

            project_name = str(self.ui.HDR_textbox_fn.text())

            selected_roi_type = self.ui.HDR_roi_type.currentText()

            print("Starting Registration...")
            print("Project Name: " + project_name)

            print("Registering " + os.path.basename(self.HDR_source_fp) +
                  " to " + os.path.basename(self.HDR_target_fp))

            print(
                "Source -> Target using registration model : flexImaging correction"
            )

            bruker_output_xmls(
                self.HDR_source_fp,
                self.HDR_target_fp,
                self.HDR_wd,
                self.HDR_ijrois_fp,
                project_name,
                ims_resolution=ims_resolution,
                ims_method=ims_method,
                roi_name=roi_names,
                splits=nsplit,
                roi_type=selected_roi_type)

            QtWidgets.QMessageBox.question(
                self, 'Registration Finished',
                "Check output directory for XML files",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

            return

############# IMS_SS on click buttons

    def IMS_SS_oc_src_img(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.IMS_SS_textbox_source.setText("source image not set...")
        else:
            self.ui.IMS_SS_textbox_source.setText(os.path.basename(file_name))
            self.IMS_SS_source_fp = file_name

    def IMS_SS_oc_tgt_img(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.IMS_SS_textbox_target.setText("target image 1 not set...")
        else:
            self.ui.IMS_SS_textbox_target.setText(os.path.basename(file_name))
            self.IMS_SS_target_fp = file_name

    def IMS_SS_oc_src_key(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.IMS_SS_textbox_source_key.setText("source key not set...")
        else:
            self.ui.IMS_SS_textbox_source_key.setText(
                os.path.basename(file_name))
            self.IMS_SS_source_key_fp = file_name

    def IMS_SS_oc_tgt_key(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.IMS_SS_textbox_target_key.setText(
                "target key 1 not set...")
        else:
            self.ui.IMS_SS_textbox_target_key.setText(
                os.path.basename(file_name))
            self.IMS_SS_target_key_fp = file_name

    def IMS_SS_oc_init_tform(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.IMS_SS_textbox_init_tform.setText(
                "initial transform not set...")
        else:
            self.ui.IMS_SS_textbox_init_tform.setText(
                os.path.basename(file_name))
            self.IMS_SS_init_tform_fp = file_name

    def IMS_SS_oc_nl_tform(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.IMS_SS_textbox_nl_tform.setText(
                "non-linear transform not set...")
        else:
            self.ui.IMS_SS_textbox_nl_tform.setText(
                os.path.basename(file_name))
            self.IMS_SS_nl_tform_fp = file_name

    def IMS_SS_oc_wd(self):
        wd_dir = self.openFileDirDialog()
        if len(wd_dir) == 0:
            self.ui.IMS_SS_textbox_wd.setText("working directory not set...")
        else:
            self.ui.IMS_SS_textbox_wd.setText(wd_dir)
            self.IMS_SS_wd = wd_dir

    def IMS_SS_overlap(self):
        if os.path.exists(self.IMS_SS_source_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the source image!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        if os.path.exists(self.IMS_SS_target_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the target image!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        if os.path.exists(self.IMS_SS_source_key_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the source IMS key!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        if os.path.exists(self.IMS_SS_target_key_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the target IMS key!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        if os.path.exists(self.IMS_SS_init_tform_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the initial transform!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        if os.path.exists(self.IMS_SS_wd) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the working directory!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        ##non-linear transformation is optional
        if os.path.exists(self.IMS_SS_nl_tform_fp) == False:
            nl_tform = None
        else:
            print('non-linear transformation used')
            nl_tform = self.IMS_SS_nl_tform_fp

        source_res = str(self.ui.IMS_SS_src_reso.text())
        target_res = str(self.ui.IMS_SS_tgt_reso.text())
        project_name = str(self.ui.IMS_SS_textbox_fn.text())

        ims_res = str(self.ui.IMS_SS_ims_reso.text())
        micro_res = str(self.ui.IMS_SS_micro_reso.text())

        IMS_ablation_overlap(
            self.IMS_SS_source_fp,
            self.IMS_SS_target_fp,
            source_res,
            target_res,
            self.IMS_SS_source_key_fp,
            self.IMS_SS_target_key_fp,
            self.IMS_SS_init_tform_fp,
            nl_tform,
            ims_res=float(ims_res),
            img_res=float(micro_res),
            project_name=project_name,
            wd=self.IMS_SS_wd)

        QtWidgets.QMessageBox.question(
            self, 'Overlap Calculation Finished',
            "Check output directory for indexed overlap .csv",
            QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

############# IMS_CE on click buttons

    def IMS_CE_oc_src_img(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.IMS_CE_textbox_source.setText("source image not set...")
        else:
            self.ui.IMS_CE_textbox_source.setText(os.path.basename(file_name))
            self.IMS_CE_source_fp = file_name

    def IMS_CE_oc_src_key(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.IMS_CE_textbox_source_key.setText("source key not set...")
        else:
            self.ui.IMS_CE_textbox_source_key.setText(
                os.path.basename(file_name))
            self.IMS_CE_source_key_fp = file_name

    def IMS_CE_oc_annotations(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.IMS_CE_textbox_annotations.setText(
                "annotations file not set...")
        else:
            self.ui.IMS_CE_textbox_annotations.setText(
                os.path.basename(file_name))
            self.IMS_CE_annotations_fp = file_name

    def IMS_CE_oc_wd(self):
        wd_dir = self.openFileDirDialog()
        if len(wd_dir) == 0:
            self.ui.IMS_CE_textbox_wd.setText("working directory not set...")
        else:
            self.ui.IMS_CE_textbox_wd.setText(wd_dir)
            self.IMS_CE_wd = wd_dir

    def IMS_CE_extraction(self):
        if os.path.exists(self.IMS_CE_source_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the source image!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        if os.path.exists(self.IMS_CE_source_key_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the source IMS key!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        if os.path.exists(self.IMS_CE_annotations_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the annotations file!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        if os.path.exists(self.IMS_CE_wd) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the working directory!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        project_name = str(self.ui.IMS_CE_textbox_fn.text())

        ims_res = str(self.ui.IMS_CE_ims_reso.text())
        micro_res = str(self.ui.IMS_CE_micro_reso.text())

        extract_ROI_coordinates(
            self.IMS_CE_source_fp,
            self.IMS_CE_annotations_fp,
            self.IMS_CE_source_key_fp,
            project_name,
            ims_res=float(ims_res),
            img_res=float(micro_res),
            wd=self.IMS_CE_wd)

        QtWidgets.QMessageBox.question(
            self, 'ROI extraction complete',
            "Check output directory for ROI overlap .csv",
            QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

############# HDR on click buttons

    def TFM_oc_src_img(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.TFM_textbox_source.setText("source image not set...")
        else:
            self.ui.TFM_textbox_source.setText(os.path.basename(file_name))
            self.TFM_source_fp = file_name

    def TFM_oc_ijrois(self):
        file_name = self.openFileNameDialog()
        if len(file_name) == 0:
            self.ui.TFM_textbox_ijrois.setText("source image not set...")
        else:
            self.ui.TFM_textbox_ijrois.setText(os.path.basename(file_name))
            self.TFM_ij_rois_fp = file_name

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
            try:
                tform = sitk.ReadParameterFile(file_name)
                self.TFM_transforms.append(tform)
                self.ui.TFM_tform_list.addItem(file_name)
            except:
                QtWidgets.QMessageBox.question(
                    self, 'Error!', "The loaded parameter is invalid",
                    QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

    def TFM_register(self):
        if os.path.exists(self.TFM_source_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the source image!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif len(self.TFM_transforms) == 0:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't added any transformations!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif len(self.TFM_wd) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!', "You haven't set the working directory!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        elif str(self.ui.TFM_src_reso.text()) == 'ijroi' and os.path.exists(
                self.TFM_source_fp) == False:
            QtWidgets.QMessageBox.question(
                self, 'Error!',
                "The ImageJ ROI must be set if ijroi is the roi_type",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        else:
            src_reso = str(self.ui.TFM_src_reso.text())

            project_name = str(self.ui.TFM_textbox_fn.text())

            selected_roi_type = self.ui.TFM_roi_type.currentText()

            print("Starting Registration...")
            print("Project Name: " + project_name)

            print("Registering " + os.path.basename(self.HDR_source_fp) +
                  " to " + os.path.basename(self.HDR_target_fp))

            print(
                "Source -> Target uing registration model : flexImaging correction"
            )

            arbitrary_transform(
                self.TFM_source_fp,
                src_reso,
                self.TFM_transforms,
                wd=self.TFM_wd,
                src_type=selected_roi_type,
                ij_rois_fp=self.TFM_ij_rois_fp,
                project_name=project_name,
                write_image=True)

            QtWidgets.QMessageBox.question(
                self, 'Registration Finished',
                "Check output directory for transformed images",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

            return


##load params functions

    def MSM_oc_save_param(self):
        self.MSM_register(params=True)

    def MSM_oc_load_param(self):
        param_fp = self.openFileNameDialog()
        with open(param_fp) as f:
            # use safe_load instead load
            param_map = yaml.safe_load(f)

        if param_map['param_mode'] != 'MSM':
            print('The config file specified is the incorrected type:' +
                  param_map['param_mode'])
            print('Expected: MSM Recieved: ' + param_map['param_mode'])
            return

        else:

            self.MSM_source_fp = param_map['source_fp']
            self.ui.MSM_textbox_source.setText(
                os.path.basename(param_map['source_fp']))

            self.ui.MSM_src_reso.setText(param_map['source_res'])

            self.MSM_target1_fp = param_map['target1_fp']
            self.ui.MSM_textbox_target1.setText(
                os.path.basename(param_map['target1_fp']))

            self.ui.MSM_tgt1_reso.setText(param_map['target1_res'])

            self.MSM_target2_fp = param_map['target2_fp']
            self.ui.MSM_textbox_target2.setText(
                os.path.basename(param_map['target2_fp']))

            self.ui.MSM_tgt2_reso.setText(param_map['target2_res'])

            self.MSM_src_mask_fp = param_map['source_mask_fp']
            self.MSM_tgt1_mask_fp = param_map['target1_mask_fp']
            self.MSM_tgt2_mask_fp = param_map['target2_mask_fp']

            self.ui.MSM_textbox_source_mask.setText(
                os.path.basename(param_map['source_mask_fp']))

            self.ui.MSM_textbox_target1_mask.setText(
                os.path.basename(param_map['target1_mask_fp']))

            self.ui.MSM_textbox_target2_mask.setText(
                os.path.basename(param_map['target2_mask_fp']))

            self.MSM_wd = param_map['wd']
            self.ui.MSM_textbox_wd.setText(param_map['wd'])

            self.ui.MSM_textbox_fn.setText(param_map['project_name'])

            index = self.ui.MSM_source_img_type.findText(
                param_map['source_img_type'], QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.ui.MSM_source_img_type.setCurrentIndex(index)

            index = self.ui.MSM_target_img_type1.findText(
                param_map['target_img_type1'], QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.ui.MSM_target_img_type1.setCurrentIndex(index)

            index = self.ui.MSM_target_img_type2.findText(
                param_map['target_img_type2'], QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.ui.MSM_target_img_type2.setCurrentIndex(index)

            index = self.ui.MSM_Reg_model1.findText(param_map['ui_reg_model1'],
                                                    QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.ui.MSM_Reg_model1.setCurrentIndex(index)

            index = self.ui.MSM_Reg_model2.findText(param_map['ui_reg_model2'],
                                                    QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.ui.MSM_Reg_model2.setCurrentIndex(index)

            self.MSM_reg_model1 = param_map['reg_model2']
            self.MSM_reg_model2 = param_map['reg_model2']

            self.ui.MSM_intermediate_export.setChecked(
                param_map['intermediate_output'])

    def SSM_oc_save_param(self):
        self.SSM_register(params=True)

    def SSM_oc_load_param(self):
        param_fp = self.openFileNameDialog()
        with open(param_fp) as f:
            # use safe_load instead load
            param_map = yaml.safe_load(f)

        if param_map['param_mode'] != 'SSM':
            print('The config file specified is the incorrected type:' +
                  param_map['param_mode'])
            print('Expected: SSM \n Recieved: ' + param_map['param_mode'])
            return

        else:

            self.SSM_source_fp = param_map['source_fp']
            self.ui.SSM_textbox_source.setText(
                os.path.basename(param_map['source_fp']))

            self.ui.SSM_src_reso.setText(param_map['source_res'])
            self.ui.SSM_textbox_target1.setText(
                os.path.basename(param_map['target1_fp']))

            self.SSM_target1_fp = param_map['target1_fp']
            self.ui.SSM_textbox_target2.setText(
                os.path.basename(param_map['target2_fp']))

            self.ui.SSM_tgt1_reso.setText(param_map['target1_res'])

            self.SSM_target2_fp = param_map['target2_fp']

            self.ui.SSM_tgt2_reso.setText(param_map['target2_res'])

            self.SSM_src_mask_fp = param_map['source_mask_fp']
            self.SSM_tgt2_mask_fp = param_map['target1_mask_fp']
            self.SSM_tgt2_mask_fp = param_map['target2_mask_fp']

            self.ui.SSM_textbox_source_mask.setText(
                os.path.basename(param_map['source_mask_fp']))

            self.ui.SSM_textbox_target1_mask.setText(
                os.path.basename(param_map['target1_mask_fp']))

            self.ui.SSM_textbox_target2_mask.setText(
                os.path.basename(param_map['target2_mask_fp']))

            self.SSM_wd = param_map['wd']
            self.ui.SSM_textbox_wd.setText(param_map['wd'])

            self.ui.SSM_textbox_fn.setText(param_map['project_name'])

            index = self.ui.SSM_source_img_type.findText(
                param_map['source_img_type'], QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.ui.SSM_source_img_type.setCurrentIndex(index)

            index = self.ui.SSM_target_img_type1.findText(
                param_map['target_img_type1'], QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.ui.SSM_target_img_type1.setCurrentIndex(index)

            index = self.ui.SSM_target_img_type2.findText(
                param_map['target_img_type2'], QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.ui.SSM_target_img_type2.setCurrentIndex(index)

            index = self.ui.SSM_Reg_model1.findText(param_map['ui_reg_model1'],
                                                    QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.ui.SSM_Reg_model1.setCurrentIndex(index)

            index = self.ui.SSM_Reg_model2.findText(param_map['ui_reg_model2'],
                                                    QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.ui.SSM_Reg_model2.setCurrentIndex(index)

            self.SSM_reg_model1 = param_map['reg_model1']
            self.SSM_reg_model2 = param_map['reg_model2']

            self.ui.SSM_intermediate_export.setChecked(
                param_map['intermediate_output'])

    def SSS_oc_save_param(self):
        self.SSS_register(params=True)

    def SSS_oc_load_param(self):
        param_fp = self.openFileNameDialog()
        with open(param_fp) as f:
            # use safe_load instead load
            param_map = yaml.safe_load(f)

        if param_map['param_mode'] != 'SSS':
            print('The config file specified is the incorrected type:' +
                  param_map['param_mode'])
            print('Expected: SSS \n Recieved: ' + param_map['param_mode'])
            return

        else:

            self.SSS_source_fp = param_map['source_fp']
            self.ui.SSS_textbox_source.setText(
                os.path.basename(param_map['source_fp']))

            self.ui.SSS_src_reso.setText(param_map['source_res'])

            self.SSS_target_fp = param_map['target_fp']
            self.ui.SSS_textbox_target.setText(
                os.path.basename(param_map['target_fp']))

            self.ui.SSS_tgt_reso.setText(param_map['target_res'])

            self.SSS_src_mask_fp = param_map['source_mask_fp']
            self.SSS_tgt_mask_fp = param_map['target1_mask_fp']

            self.ui.SSS_textbox_source_mask.setText(
                os.path.basename(param_map['source_mask_fp']))

            self.ui.SSS_textbox_target_mask.setText(
                os.path.basename(param_map['target_mask_fp']))

            self.SSS_wd = param_map['wd']
            self.ui.SSS_textbox_wd.setText(param_map['wd'])

            self.ui.SSS_textbox_fn.setText(param_map['project_name'])

            index = self.ui.SSS_source_img_type.findText(
                param_map['source_img_type'], QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.ui.SSS_source_img_type.setCurrentIndex(index)

            index = self.ui.SSS_target_img_type.findText(
                param_map['target_img_type'], QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.ui.SSS_target_img_type.setCurrentIndex(index)

            index = self.ui.SSS_Reg_model1.findText(param_map['ui_reg_model1'],
                                                    QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.ui.SSS_Reg_model1.setCurrentIndex(index)

            self.SSS_reg_model1 = param_map['reg_model1']

    def MSS_oc_save_param(self):
        self.MSS_register(params=True)

    def MSS_oc_load_param(self):
        param_fp = self.openFileNameDialog()
        with open(param_fp) as f:
            # use safe_load instead load
            param_map = yaml.safe_load(f)

        if param_map['param_mode'] != 'MSS':
            print('The config file specified is the incorrected type:' +
                  param_map['param_mode'])
            print('Expected: MSS \n Recieved: ' + param_map['param_mode'])
            return

        else:

            self.MSS_source_fp = param_map['source_fp']
            self.ui.MSS_textbox_source.setText(
                os.path.basename(param_map['source_fp']))

            self.ui.MSS_src_reso.setText(param_map['source_res'])

            self.MSS_target_fp = param_map['target_fp']
            self.ui.MSS_textbox_target.setText(
                os.path.basename(param_map['target_fp']))

            self.ui.MSS_tgt_reso.setText(param_map['target_res'])

            self.MSS_src_mask_fp = param_map['source_mask_fp']
            self.MSS_tgt_mask_fp = param_map['target_mask_fp']

            self.ui.MSS_textbox_source_mask.setText(
                os.path.basename(param_map['source_mask_fp']))

            self.ui.MSS_textbox_target_mask.setText(
                os.path.basename(param_map['target_mask_fp']))

            self.MSS_wd = param_map['wd']
            self.ui.MSS_textbox_wd.setText(param_map['wd'])

            self.ui.MSS_textbox_fn.setText(param_map['project_name'])

            index = self.ui.MSS_source_img_type.findText(
                param_map['source_img_type'], QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.ui.MSS_source_img_type.setCurrentIndex(index)

            index = self.ui.MSS_target_img_type.findText(
                param_map['target_img_type'], QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.ui.MSS_target_img_type.setCurrentIndex(index)

            index = self.ui.MSS_Reg_model1.findText(param_map['ui_reg_model1'],
                                                    QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.ui.MSS_Reg_model1.setCurrentIndex(index)

            self.MSS_reg_model1 = param_map['reg_model1']

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
