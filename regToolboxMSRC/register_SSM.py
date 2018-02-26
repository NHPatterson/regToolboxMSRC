#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 10:11:21 2018

@author: nhp
"""
import os
import time
import datetime
from regToolboxMSRC.utils.reg_utils import parameter_files, register_elx_, transform_mc_image_sitk, reg_image, paste_to_original_dim, check_im_size_fiji
import SimpleITK as sitk

def register_SSM(source_fp, source_res, target1_fp, target1_res , target2_fp, target2_res, source_mask_fp, target1_mask_fp, target2_mask_fp, wd, source_img_type, target_img_type1,target_img_type2, reg_model1, reg_model2, project_name, intermediate_output = False, bounding_box = False):

    ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H_%M_%S_')
    os.chdir(wd)
    os.makedirs(ts + project_name + "_images")
    opdir = ts + project_name + "_images\\"
    
    #load registration parameters based on input
    if reg_model1 == "Rigid":
        reg_param1 = parameter_files().rigid    
    elif reg_model1 == "Affine":
        reg_param1 = parameter_files().affine   
        
    if reg_model2 == "Rigid":
        reg_param2 = parameter_files().rigid    
    elif reg_model2 == "Affine":
        reg_param2 = parameter_files().affine
    
    #load images for registration:
    
    if source_img_type == "HE":
        source = reg_image(source_fp,'sitk', source_res)
        source.to_greyscale()
        source.invert_intensity()
        
    else:
        source = reg_image(source_fp,'sitk', source_res)
        if source.image.GetDepth() > 1:
            source.compress_AF_channels('max')
    
    print("source image loaded")
        
    if target_img_type1 == "HE":
        target1 = reg_image(target1_fp,'sitk', target1_res)
        target1.to_greyscale()
        target1.invert_intensity()
        
    else:
        target1 = reg_image(target1_fp,'sitk', target1_res)
        if target1.image.GetDepth() > 1:
            target1.compress_AF_channels('max')


    print("target 1 image loaded")

    
    
    #register

    
    #img_output_dir = os.getcwd() + "\\" + ts + project_name + "_tforms" +"\\"

    
    src_tgt1_tform = register_elx_(source.image, target1.image, reg_param1, moving_mask = source_mask_fp,  fixed_mask = target1_mask_fp, output_dir= ts + project_name + "_tforms_src_tgt1", output_fn = ts + project_name +"_"+reg_model1+"_src_tgt1.txt", logging = True)
    
    #transform result and save output
    os.chdir(wd)

    if intermediate_output == True:
        tformed_im = transform_mc_image_sitk(source_fp, src_tgt1_tform, source_res)
        sitk.WriteImage(tformed_im, opdir + project_name + "_src_tgt1.tif", True)


    del source
    
    if target_img_type2 == "HE":
        target2 = reg_image(target2_fp,'sitk', target2_res)
        target2.to_greyscale()
        target2.invert_intensity()
        
    else:
        target2 = reg_image(target2_fp,'sitk', target2_res)
        if target2.image.GetDepth() > 1:
            target2.compress_AF_channels('max')

    print("target 2 image loaded")
    ##get target 2 image metaData in case of bounding box masking:
    final_size_2D = target2.image.GetSize()
    
    if bounding_box == True and os.path.exists(target2_mask_fp):
        tgt1_tgt2_tform,fixed_x, fixed_y, fixed_w, fixed_h, fixed_shape_original = register_elx_(target1.image, target2.image, reg_param2, moving_mask = target1_mask_fp,  fixed_mask = target2_mask_fp, output_dir= ts + project_name + "_tforms_tgt1_tgt2", output_fn = ts + project_name +"_"+reg_model1+"_tgt1_tgt2.txt", logging = True, bounding_box = True)
    
    else:
        tgt1_tgt2_tform = register_elx_(target1.image, target2.image, reg_param2, moving_mask = target1_mask_fp,  fixed_mask = target2_mask_fp, output_dir= ts + project_name + "_tforms_tgt1_tgt2", output_fn = ts + project_name +"_"+reg_model1+"_tgt1_tgt2.txt", logging = True, bounding_box = False)
    
    
    #transform result and save output
    tformed_im = transform_mc_image_sitk(target1_fp, tgt1_tgt2_tform, target1_res)
    
    if bounding_box == True and os.path.exists(target2_mask_fp):
        tformed_im = paste_to_original_dim(tformed_im, fixed_x, fixed_y, final_size_2D)
    
    if check_im_size_fiji(tformed_im) == True:
        sitk.WriteImage(tformed_im, opdir + project_name + "_tgt1_tgt2.mha", True)
    else:
        sitk.WriteImage(tformed_im, opdir + project_name + "_tgt1_tgt2.tif", True)

    ##source to tgt2
    tformed_im = transform_mc_image_sitk(source_fp, src_tgt1_tform, source_res)
    tformed_im = transform_mc_image_sitk(tformed_im, tgt1_tgt2_tform, source_res, from_file=False)
    
    if bounding_box == True and os.path.exists(target2_mask_fp):
        tformed_im = paste_to_original_dim(tformed_im, fixed_x, fixed_y, final_size_2D)
    
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
    
    register_SSM(dataMap['source_fp'], dataMap['source_res'], 
                 dataMap['target1_fp'], dataMap['target1_res'], 
                 dataMap['target2_fp'], dataMap['target2_res'], 
                 dataMap['source_mask_fp'], dataMap['target1_mask_fp'], dataMap['target2_mask_fp'],
                 dataMap['wd'], 
                 dataMap['source_img_type'], dataMap['target_img_type1'], dataMap['target_img_type2'],
                 dataMap['reg_model1'],dataMap['reg_model2'],
                 dataMap['project_name'], 
                 intermediate_output = dataMap['intermediate_output'], bounding_box = dataMap['bounding_box'])