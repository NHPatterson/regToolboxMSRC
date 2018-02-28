#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 27 14:08:20 2018

@author: nhp
"""

import os
import time
import datetime
from regToolboxMSRC.utils.reg_utils import register_elx_, transform_mc_image_sitk, paste_to_original_dim, check_im_size_fiji, reg_image_preprocess, parameter_load
import SimpleITK as sitk


def register_SSS(source_fp, source_res, 
                 target_fp, target_res , 
                 source_mask_fp, target_mask_fp,
                 wd, 
                 source_img_type, target_img_type,
                 reg_model, 
                 project_name,
                 return_image = False, intermediate_output = False, bounding_box = False, 
                 pass_in_project_name=False, pass_in= None):

    
    #set up output information
    if pass_in_project_name == False:
        ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H_%M_%S_')
        os.chdir(wd)
        os.makedirs(os.path.join(os.getcwd(),ts+ project_name+"_images"))
        opdir = ts + project_name + "_images"
    else:
        os.chdir(wd)
        os.makedirs(os.path.join(os.getcwd(),pass_in+"_images"))
        opdir = pass_in + "_images"

    
    #load registration parameters based on input
    reg_param1 = parameter_load(reg_model)
    print(project_name + ': registration hyperparameters loaded')

    #load images for registration:    
    source = reg_image_preprocess(source_fp, source_res, img_type = source_img_type)
    print(project_name +": source image loaded")
        
    target = reg_image_preprocess(target_fp, target_res, img_type = target_img_type)
    print(project_name +": target image loaded")

    #registration
    src_tgt1_tform = register_elx_(source.image, target.image, reg_param1, moving_mask = source_mask_fp,  fixed_mask = target_mask_fp, output_dir= ts + project_name + "_tforms_src_tgt1", output_fn = ts + project_name +"_init_src_tgt1.txt", return_image = False,logging = True, bounding_box=False)
    
    #transform result and save output
    os.chdir(wd)

    tformed_im = transform_mc_image_sitk(source_fp, src_tgt1_tform, source_res)
    
#    if bounding_box == True and os.path.exists(target2_mask_fp):
#        tformed_im = paste_to_original_dim(tformed_im, fixed_x, fixed_y, final_size_2D)
    
    if check_im_size_fiji(tformed_im) == True:
        sitk.WriteImage(tformed_im, opdir + project_name + "_src_tgt1.mha", True)
    else:
        sitk.WriteImage(tformed_im, opdir + project_name + "_src_tgt1.tif", True)

    return os.path.join(os.getcwd(), opdir, project_name + "_src_tgt1.tif")

if __name__ == '__main__':
    import yaml
    import sys 
    with open(sys.argv[1]) as f:
        # use safe_load instead load
        dataMap = yaml.safe_load(f)
    
    register_SSS(dataMap['source_fp'], dataMap['source_res'], 
                 dataMap['target_fp'], dataMap['target_res'], 
                 dataMap['source_mask_fp'], dataMap['target_mask_fp'], 
                 dataMap['wd'], 
                 dataMap['source_img_type'], dataMap['target_img_type'],
                 dataMap['reg_model'],
                 dataMap['project_name'], 
                 intermediate_output = dataMap['intermediate_output'], bounding_box = dataMap['bounding_box'],
                 pass_in_project_name=True, pass_in= None)