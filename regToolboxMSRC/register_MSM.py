#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 27 15:54:42 2018

@author: nhp
"""

import os
import time
import datetime
from regToolboxMSRC.utils.reg_utils import register_elx_, transform_mc_image_sitk, paste_to_original_dim, check_im_size_fiji, reg_image_preprocess, parameter_load
import SimpleITK as sitk

##MSM registration: this performs registration of two images from the same section to a serial section.

def register_MSM(source_fp, source_res, 
                 target1_fp, target1_res , 
                 target2_fp, target2_res, 
                 source_mask_fp, target1_mask_fp, target2_mask_fp, 
                 wd, 
                 source_img_type, target1_img_type, target2_img_type, 
                 reg_model1, reg_model2, 
                 project_name,
                 return_image = False, intermediate_output = False, bounding_box = False):

    
    #set up output information
    ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H_%M_%S_')
    os.chdir(wd)
    os.makedirs(os.path.join(os.getcwd(),ts+ project_name+"_images"))
    opdir = ts + project_name + "_images"
    
    #load registration parameters based on input
    reg_param1 = parameter_load(reg_model1)
    reg_param2 = parameter_load(reg_model2)
    print(project_name + ': registration hyperparameters loaded')

    #load images for registration:    
    source = reg_image_preprocess(source_fp, source_res, img_type = source_img_type)
    print(project_name +": source image loaded")
        
    target1 = reg_image_preprocess(target1_fp, target1_res, img_type = target1_img_type)
    print(project_name +": target 1 image loaded")

    #registration
    src_tgt1_tform = register_elx_(source.image, target1.image, reg_param1, moving_mask = source_mask_fp,  fixed_mask = target1_mask_fp, output_dir= ts + project_name + "_tforms_src_tgt1", output_fn = ts + project_name +"_init_src_tgt1.txt", return_image = False,logging = True, bounding_box=False)
    
    #transform result and save output
    os.chdir(wd)

    if intermediate_output == True:
        tformed_im = transform_mc_image_sitk(source_fp, src_tgt1_tform, source_res)
        sitk.WriteImage(tformed_im, os.path.join(os.getcwd(),opdir, project_name + "_src_tgt1.tif"), True)

    del source
    
    target2 = reg_image_preprocess(target2_fp, target2_res, img_type = target2_img_type)
    print(project_name +": target 2 image loaded")
    
    ##get target 2 image metaData in case of bounding box masking:
    tgt1_tgt2_tform_init, init_img = register_elx_(target1.image, target2.image, reg_param2, moving_mask = target1_mask_fp,  fixed_mask = target2_mask_fp, output_dir= ts + project_name + "_tforms_tgt1_tgt2_init", output_fn = ts + project_name +"tgt1_tgt2_init.txt", return_image = True, logging = True, bounding_box = False)
    
    #transform tgt1_tgt2 init result and save output

    if intermediate_output == True:
        tformed_im = transform_mc_image_sitk(target1_fp, tgt1_tgt2_tform_init, target1_res)
        sitk.WriteImage(tformed_im, os.path.join(os.getcwd(),opdir, project_name + "_tgt1_tgt2_init.tif"), True)
    
    del target1
    
    reg_param_nl = parameter_load('nl')
    
    ##register using nl transformation
    if target1_mask_fp != None:
        target1_mask_fp = transform_mc_image_sitk(target1_mask_fp, tgt1_tgt2_tform_init, target1_res, from_file=True, is_binary_mask = True)
    
        tgt1_tgt2_tform_nl, init_img = register_elx_(init_img, target2.image, reg_param_nl, moving_mask = target1_mask_fp,  fixed_mask = target2_mask_fp, output_dir= ts + project_name + "_tforms_tgt1_tgt2_nl", output_fn = ts + project_name +"tgt1_tgt2_nl.txt", return_image = True, logging = True, bounding_box = False)
    
    
#    if bounding_box == True and os.path.exists(target2_mask_fp):
#        tformed_im = paste_to_original_dim(tformed_im, fixed_x, fixed_y, final_size_2D)
#    
    ##tgt1 to tgt2
    tformed_im = transform_mc_image_sitk(target1_fp, tgt1_tgt2_tform_init, target1_res)
    tformed_im = transform_mc_image_sitk(tformed_im, tgt1_tgt2_tform_nl, target2_res, from_file=False)
    
    if check_im_size_fiji(tformed_im) == True:
        sitk.WriteImage(tformed_im, opdir + project_name + "_tgt1_tgt2.mha", True)
    else:
        sitk.WriteImage(tformed_im, opdir + project_name + "_tgt1_tgt2.tif", True)

    ##source to tgt2
    tformed_im = transform_mc_image_sitk(source_fp, src_tgt1_tform, source_res)
    tformed_im = transform_mc_image_sitk(tformed_im, tgt1_tgt2_tform_init, target1_res, from_file=False)
    tformed_im = transform_mc_image_sitk(tformed_im, tgt1_tgt2_tform_nl, target2_res, from_file=False)
    
#    if bounding_box == True and os.path.exists(target2_mask_fp):
#        tformed_im = paste_to_original_dim(tformed_im, fixed_x, fixed_y, final_size_2D)
    
    if check_im_size_fiji(tformed_im) == True:
        sitk.WriteImage(tformed_im, opdir + project_name + "_src_tgt2.mha", True)
    else:
        sitk.WriteImage(tformed_im, opdir + project_name + "_src_tgt2.tif", True)

    return

if __name__ == '__main__':
    import yaml
    import sys 
    with open(sys.argv[1]) as f:
        # use safe_load instead load
        dataMap = yaml.safe_load(f)
    
    register_MSM(dataMap['source_fp'], dataMap['source_res'], 
                 dataMap['target1_fp'], dataMap['target1_res'], 
                 dataMap['target2_fp'], dataMap['target2_res'], 
                 dataMap['source_mask_fp'], dataMap['target1_mask_fp'], dataMap['target2_mask_fp'],
                 dataMap['wd'], 
                 dataMap['source_img_type'], dataMap['target_img_type1'], dataMap['target_img_type2'],
                 dataMap['reg_model1'],dataMap['reg_model2'],
                 dataMap['project_name'], 
                 intermediate_output = dataMap['intermediate_output'], bounding_box = dataMap['bounding_box'])