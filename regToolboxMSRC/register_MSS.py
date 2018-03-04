#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 27 14:15:05 2018

@author: nhp
"""

import os
import time
import datetime
from regToolboxMSRC.utils.reg_utils import register_elx_, transform_mc_image_sitk, paste_to_original_dim, check_im_size_fiji, reg_image_preprocess, parameter_load
import SimpleITK as sitk

def register_MSS(source_fp, source_res,
                 target_fp, target_res,
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
    src_tgt_tform_init, init_img = register_elx_(source.image, target.image, reg_param1, moving_mask = source_mask_fp,  fixed_mask = target_mask_fp, output_dir= ts + project_name + "_tforms_src_tgt_init", output_fn = ts + project_name +"_init_src_tgt_init.txt", return_image = True, logging = True, bounding_box=False)


    #transform result and save output
    os.chdir(wd)

    if intermediate_output == True:
        tformed_im = transform_mc_image_sitk(source_fp, src_tgt_tform_init, source_res)
        sitk.WriteImage(tformed_im, os.path.join(os.getcwd(),opdir, project_name + "_src_tgt_init.tif"), True)

    del source

    reg_param_nl = parameter_load('nl')

    ##register using nl transformation
    if source_mask_fp != None:
        source_mask_fp = transform_mc_image_sitk(source_mask_fp, src_tgt_tform_init, source_res, from_file=True, is_binary_mask = True)

    src_tgt_tform_nl = register_elx_(init_img, target.image, reg_param_nl, moving_mask = source_mask_fp,  fixed_mask = target_mask_fp, output_dir= ts + project_name + "_tforms_src_tgt_nl", output_fn = ts + project_name +"init_src_tgt_nl.txt", return_image = False ,logging = True, bounding_box = False)


    ##source to tgt2
    tformed_im = transform_mc_image_sitk(source_fp, src_tgt_tform_init, source_res)
    tformed_im = transform_mc_image_sitk(tformed_im, src_tgt_tform_nl, source_res, from_file=False)

#    if bounding_box == True and os.path.exists(target2_mask_fp):
#        tformed_im = paste_to_original_dim(tformed_im, fixed_x, fixed_y, final_size_2D)

    if check_im_size_fiji(tformed_im) == True:
        sitk.WriteImage(tformed_im, opdir + project_name + "_src_tgt.mha", True)
    else:
        sitk.WriteImage(tformed_im, opdir + project_name + "_src_tgt.tif", True)

    return

if __name__ == '__main__':
    import yaml
    import sys
    with open(sys.argv[1]) as f:
        # use safe_load instead load
        dataMap = yaml.safe_load(f)

    register_MSS(dataMap['source_fp'], dataMap['source_res'], #source image
                 dataMap['target_fp'], dataMap['target_res'], #target image
                 dataMap['source_mask_fp'], dataMap['target_mask_fp'], #masks
                 dataMap['wd'], #output directory
                 dataMap['source_img_type'], dataMap['target_img_type'], #image type info 'RGB_l' or 'AF'
                 dataMap['reg_model'], #initial transformation model
                 dataMap['project_name'],
                 intermediate_output = dataMap['intermediate_output'], bounding_box = dataMap['bounding_box'])
