#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: nhp
"""

import os
import time
import datetime
from regToolboxMSRC.utils.reg_utils import register_elx_n, check_im_size_fiji, reg_image_preprocess, parameter_load, transform_mc_image_sitk
import SimpleITK as sitk

##MSM registration: this performs registration of two images from the same section to a serial section.


def register_MSM(source_fp,
                 source_res,
                 target1_fp,
                 target1_res,
                 target2_fp,
                 target2_res,
                 source_mask_fp,
                 target1_mask_fp,
                 target2_mask_fp,
                 wd,
                 source_img_type,
                 target1_img_type,
                 target2_img_type,
                 reg_model1,
                 reg_model2,
                 project_name,
                 intermediate_output=False,
                 bounding_box_source=False,
                 bounding_box_target1=False,
                 bounding_box_target2=False,
                 pass_in_project_name=False,
                 pass_in=None):
    """This function performs registration between 2 images from the same
    tissue section to a third image from a serial section. The initial
    registrations are linear and the final is fixed as non-linear.

    Parameters
    ----------
    source_fp : str
        String file path to source image
    source_res : float
        Image resolution of source image, specified in microns / pixel
    target1_fp : str
        String file path to first target image
    target1_res : float
        Image resolution of first target image image, specified in microns / pixel
    target2_fp : str
        String file path to second target image
    target2_res : float
        Image resolution of second target image image, specified in microns / pixel
    source_mask_fp : str or SimpleITK.Image()
        String file path to binary mask for source image or SimpleITK.Image()
        Using a mask image from memory is helpful in some registration routines
        where there are multiple registrations and the mask must be transformed
        to continue.
    target1_mask_fp : str or SimpleITK.Image()
        String file path to binary mask for target image or SimpleITK.Image()
    target2_mask_fp : str or SimpleITK.Image()
        String file path to binary mask for target image or SimpleITK.Image()
    wd : str
        String directory path to where outputs will go
    source_img_type : str
        string of either 'RGB_l' or 'AF' for source image
        'RGB_l' specifices an RGB image with a light background,
        like brightfield microscopy.
        'AF' specifices a multilayer fluorescence image or RGB image with
        a dark background.
    target1_img_type : str
        string of either 'RGB_l' or 'AF' for first target image
    target2_img_type : str
        string of either 'RGB_l' or 'AF' for second target image
    reg_model1 : str or file path to Sitk.ParameterMap()
        The elastix parameter file for the registration between source image
        and target image 1
    reg_model2 : str or file path to Sitk.ParameterMap()
        The elastix parameter file for the registration between target image 1
        and target image 2
    project_name : str
        String prepended to file outputs
    return_image : boolean
        Whether or not to return the from IMS_registrations.
        This is required when there is an initial rigid transformation followed
        by a non-linear transformation on the previously aligned image.
    intermediate_output : boolean
        Whether or not to write the intermediate initial registration image
        or only the final non-linears.
    bounding_box : boolean
        Whether to use the mask as a bounding_box to crop the area of interest
        This has been useful when registering a small image to a very large one
        where the registration initializes poor.
        This setting will find the transformation on the crop, then paste the
        registered image back to the original dimensions of the target image.
    pass_in_project_name : boolean
        This parameter is used to pass in the project name from the reg_tlbx_gui
    pass_in : str
        Time stamped name fragment inherited from the GUI

    Returns
    -------
        The function writes the transformation files and images in the specified
        working directory.
    """

    #set up output information
    if pass_in_project_name == False:
        ts = datetime.datetime.fromtimestamp(
            time.time()).strftime('%Y%m%d_%H_%M_%S_')
        os.chdir(wd)
        os.makedirs(os.path.join(os.getcwd(), ts + project_name + "_images"))
        opdir = ts + project_name + "_images"
        pass_in = ts + project_name

    else:
        os.chdir(wd)
        os.makedirs(os.path.join(os.getcwd(), pass_in + "_images"))
        opdir = pass_in + "_images"

    #load registration parameters based on input
    reg_param1 = parameter_load(reg_model1)
    reg_param2 = parameter_load(reg_model2)
    print(project_name + ': registration hyperparameters loaded')

    #load images for registration:
    source = reg_image_preprocess(
        source_fp,
        source_res,
        img_type=source_img_type,
        mask_fp=source_mask_fp,
        bounding_box=bounding_box_source)

    print(project_name + ": source image loaded")

    target1 = reg_image_preprocess(
        target1_fp,
        target1_res,
        img_type=target1_img_type,
        mask_fp=target1_mask_fp,
        bounding_box=bounding_box_target1)

    print(project_name + ": target 1 image loaded")

    reg_param1['MaximumNumberOfIterations'] = ['100']  #testing
    reg_param2['MaximumNumberOfIterations'] = ['100']  #testing
    reg_param1['AutomaticTransformInitialization'] = ['false']  #testing
    reg_param2['AutomaticTransformInitialization'] = ['false']  #testing

    #registration
    src_tgt1_tform = register_elx_n(
        source,
        target1,
        reg_param1,
        output_dir=pass_in + "_tforms_src_tgt1",
        output_fn=pass_in + "_init_src_tgt1.txt",
        return_image=False,
        logging=True)

    #transform result and save output
    os.chdir(wd)

    if intermediate_output == True:
        tformed_im = transform_mc_image_sitk(
            source_fp, src_tgt1_tform, source_res, override_tform=False)

        sitk.WriteImage(tformed_im,
                        os.path.join(os.getcwd(), opdir,
                                     project_name + "_src_tgt1.tif"), True)

    target2 = reg_image_preprocess(
        target2_fp,
        target2_res,
        img_type=target2_img_type,
        mask_fp=target2_mask_fp,
        bounding_box=bounding_box_target2)

    print(project_name + ": target 2 image loaded")

    ##get target 2 image metaData in case of bounding box masking:
    tgt1_tgt2_tform_init, init_img = register_elx_n(
        target1,
        target2,
        reg_param2,
        output_dir=pass_in + "_tforms_tgt1_tgt2_init",
        output_fn=pass_in + "tgt1_tgt2_init.txt",
        return_image=True,
        logging=True)

    #transform tgt1_tgt2 init result and save output

    os.chdir(wd)

    if intermediate_output == True:
        tformed_im = transform_mc_image_sitk(
            target1_fp,
            tgt1_tgt2_tform_init,
            target1_res,
            override_tform=False)

        sitk.WriteImage(tformed_im,
                        os.path.join(os.getcwd(), opdir,
                                     project_name + "_src_tgt1.tif"), True)

    reg_param_nl = parameter_load('nl')

    reg_param_nl['MaximumNumberOfIterations'] = ['200']  #testing

    ##register using nl transformation
    if target1_mask_fp != None:
        target1_mask_fp = transform_mc_image_sitk(
            target1_mask_fp,
            src_tgt_tform_init,
            target1_res,
            from_file=True,
            is_binary_mask=True,
            override_tform=False)

    target1 = reg_image_preprocess(
        init_img,
        target_res,
        img_type='in_memory',
        mask_fp=target1_mask_fp,
        bounding_box=False)

    tgt1_tgt2_tform_nl = register_elx_(
        target1,
        target2,
        reg_param_nl,
        output_dir=pass_in + "_tforms_tgt1_tgt2_nl",
        output_fn=pass_in + "tgt1_tgt2_nl.txt",
        return_image=False,
        logging=True)

    ##tgt1 to tgt2
    tformed_im = transform_mc_image_sitk(target1_fp, tgt1_tgt2_tform_init,
                                         target1_res)
    tformed_im = transform_mc_image_sitk(
        tformed_im, tgt1_tgt2_tform_nl, target2_res, from_file=False)

    if check_im_size_fiji(tformed_im) == True:
        sitk.WriteImage(tformed_im,
                        os.path.join(os.getcwd(), opdir,
                                     project_name + "_tgt1_tgt2.mha"), True)
    else:
        sitk.WriteImage(tformed_im,
                        os.path.join(os.getcwd(), opdir,
                                     project_name + "_tgt1_tgt2.tif"), True)

    ##source to tgt2
    tformed_im = transform_mc_image_sitk(source_fp, src_tgt1_tform, source_res)
    tformed_im = transform_mc_image_sitk(
        tformed_im, tgt1_tgt2_tform_init, target1_res, from_file=False)
    tformed_im = transform_mc_image_sitk(
        tformed_im, tgt1_tgt2_tform_nl, target2_res, from_file=False)

    #    if bounding_box == True and os.path.exists(target2_mask_fp):
    #        tformed_im = paste_to_original_dim(tformed_im, fixed_x, fixed_y, final_size_2D)

    if check_im_size_fiji(tformed_im) == True:
        sitk.WriteImage(tformed_im,
                        os.path.join(os.getcwd(), opdir,
                                     project_name + "_src_tgt2.mha"), True)
    else:
        sitk.WriteImage(tformed_im,
                        os.path.join(os.getcwd(), opdir,
                                     project_name + "_src_tgt2.tif"), True)

    return


if __name__ == '__main__':
    import yaml
    import sys
    with open(sys.argv[1]) as f:
        # use safe_load instead load
        dataMap = yaml.safe_load(f)

    register_MSM(
        dataMap['source_fp'],
        dataMap['source_res'],
        dataMap['target1_fp'],
        dataMap['target1_res'],
        dataMap['target2_fp'],
        dataMap['target2_res'],
        dataMap['source_mask_fp'],
        dataMap['target1_mask_fp'],
        dataMap['target2_mask_fp'],
        dataMap['wd'],
        dataMap['source_img_type'],
        dataMap['target_img_type1'],
        dataMap['target_img_type2'],
        dataMap['reg_model1'],
        dataMap['reg_model2'],
        dataMap['project_name'],
        intermediate_output=dataMap['intermediate_output'],
        bounding_box_source=dataMap['bounding_box_source'],
        bounding_box_target1=dataMap['bounding_box_target1'],
        bounding_box_target2=dataMap['bounding_box_target2'])
