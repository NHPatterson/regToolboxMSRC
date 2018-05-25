#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: pattenh1
"""
import os
from regToolboxMSRC.utils.flx_utils import ROIhandler
from regToolboxMSRC.utils.reg_utils import transform_mc_image_sitk, parameterFile_load, reg_image_preprocess
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
        source = reg_image_preprocess(
            source_fp,
            src_reso,
            img_type='none',
            mask_fp=None,
            bounding_box=False)

    elif src_type == 'ijroi' and ij_rois_fp != None:
        try:
            roi_mask = ROIhandler(source_fp, 1, is_mask=False)
            roi_mask.get_polygons_ijroi(ij_rois_fp)
            roi_mask.draw_polygon_mask(binary_mask=True, flip_xy=True)
            roi_mask = roi_mask.pg_mask

            source = reg_image_preprocess(
                roi_mask,
                src_reso,
                img_type='in_memory',
                mask_fp=None,
                bounding_box=False)

        except:
            print('invalid ImageJ ROIs file')

    else:
        print('Error: input is neither an image nor an ROI file')

    for i in range(len(transforms)):

        transform = parameterFile_load(transforms[i])

        if i == 0:
            print('first')
            if len(transforms) == 1:
                override = True
            else:
                override = False

            image = transform_mc_image_sitk(
                source.image,
                transform,
                src_reso,
                from_file=False,
                is_binary_mask=False,
                override_tform=override)

        if i > 0 and i < len(transforms) - 1:
            print('intermediate')
            source = reg_image_preprocess(
                image,
                image.GetSpacing()[0],
                img_type='in_memory',
                mask_fp=None,
                bounding_box=False)

            image = transform_mc_image_sitk(
                source.image,
                transform,
                image.GetSpacing()[0],
                from_file=False,
                is_binary_mask=False,
                override_tform=False)

        if i > 0 and i == len(transforms) - 1:
            print('last')
            source = reg_image_preprocess(
                image,
                image.GetSpacing()[0],
                img_type='in_memory',
                mask_fp=None,
                bounding_box=False)

            image = transform_mc_image_sitk(
                source.image,
                transform,
                image.GetSpacing()[0],
                from_file=False,
                is_binary_mask=False,
                override_tform=False)

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
