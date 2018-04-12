#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: pattenh1
"""
import os
from regToolboxMSRC.utils.flx_utils import ROIhandler
from regToolboxMSRC.utils.reg_utils import RegImage_load, transform_mc_image_sitk, parameterFile_load
import SimpleITK as sitk


def arbitrary_transform(source_fp,
                        src_reso,
                        transforms,
                        wd='',
                        src_type='image',
                        ij_rois_fp=None,
                        project_name='',
                        write_image=False):

    if src_type not in ['image', 'ijroi']:
        print('invalid source image type')
        return

    if src_type == 'image':
        image = RegImage_load(source_fp, src_reso)
        image = image.image
    elif src_type == 'ijroi' and ij_rois_fp != None:
        try:
            image = ROIhandler(source_fp, 1, is_mask=False)
            image.get_polygons_ijroi(ij_rois_fp)
            image.draw_polygon_mask(binary_mask=True, flip_xy=True)
            image = image.pg_mask

        except:
            print('invalid ImageJ ROIs file')

    else:
        print('Error: input is neither an image nor an ROI file')

    for i in range(len(transforms)):
        transform = parameterFile_load(transforms[i])
        if i == 0:
            image = transform_mc_image_sitk(
                image,
                transform,
                src_reso,
                from_file=False,
                is_binary_mask=False)
        if i > 0:
            image = transform_mc_image_sitk(
                image,
                transform,
                image.GetSpacing()[0],
                from_file=False,
                is_binary_mask=False)
    if write_image == True:
        os.chdir(wd)
        sitk.WriteImage(image, project_name + ".tif", True)
    else:
        return image


if __name__ == '__main__':
    import yaml
    import sys
    with open(sys.argv[1]) as f:
        # use safe_load instead load
        dataMap = yaml.safe_load(f)

    arbitrary_transform(dataMap['source_fp'], dataMap['src_reso'],
                        dataMap['transforms'], dataMap['wd'],
                        dataMap['src_type'], dataMap['ij_rois_fp'],
                        dataMap['project_name'], dataMap['write_image'])
