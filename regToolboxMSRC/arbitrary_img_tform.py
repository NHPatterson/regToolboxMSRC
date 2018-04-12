#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 13 09:31:56 2017

@author: pattenh1
"""
import os
from regToolboxMSRC.utils.flx_utils import ROIhandler
from regToolboxMSRC.utils.reg_utils import RegImage_load, transform_mc_image_sitk


def arbitrary_transform(source_fp,
                        transforms,
                        TFM_wd,
                        src_reso,
                        project_name,
                        src_type='image',
                        ij_rois_fp = None):

    if src_type == 'image':
        image = RegImage_load(source_fp, src_reso)
    if src_type == 'ijroi' and ij_rois_fp != None:
        

    for i in range(len(transforms)):
        if i == 0:
            source = transform_mc_image_sitk(
                image,
                transforms[i],
                src_reso,
                from_file=False,
                is_binary_mask=False)
        if i > 0:
            source = transform_mc_image_sitk(
                source,
                transforms[i],
                source.GetSpacing()[0],
                from_file=False,
                is_binary_mask=False)
    os.chdir(TFM_wd)
    sitk.WriteImage(source, project_name + ".tif", True)


if __name__ == '__main__':
    import yaml
    import sys
    with open(sys.argv[1]) as f:
        # use safe_load instead load
        dataMap = yaml.safe_load(f)

    extract_ROI_coordinates(dataMap['index_image_fp'],
                            dataMap['annotation_fp'], dataMap['IMS_key_fp'],
                            dataMap['project_name'], dataMap['ims_res'],
                            dataMap['img_res'])
