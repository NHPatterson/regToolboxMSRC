#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: nhp
"""

import os
import SimpleITK as sitk
import datetime
import time
from regToolboxMSRC.utils.reg_utils import register_elx_, reg_image_preprocess, parameter_files, transform_mc_image_sitk
from regToolboxMSRC.utils.flx_utils import ROIhandler, output_flex_rects, output_flex_polys, split_boxes, split_polys, mask_contours_to_boxes, mask_contours_to_polygons


def bruker_output_xmls(source_fp,
                       target_fp,
                       wd,
                       ijroi_fp,
                       project_name,
                       ims_resolution=10,
                       ims_method="par",
                       roi_name="roi",
                       splits="0",
                       roi_type=['rectangle', 'polygon']):

    ts = datetime.datetime.fromtimestamp(
        time.time()).strftime('%Y%m%d_%H_%M_%S_')
    no_splits = int(splits)

    #register
    os.chdir(wd)

    #get FI tform
    source_image = reg_image_preprocess(source_fp, 1, img_type='AF')
    target_image = reg_image_preprocess(target_fp, 1, img_type='AF')

    param = parameter_files()

    tmap_correction = register_elx_(
        source_image.image,
        target_image.image,
        param.correction,
        moving_mask=None,
        fixed_mask=None,
        output_dir=ts + project_name + "_tforms_FI_correction",
        output_fn=ts + project_name + "_correction.txt",
        logging=True)

    #rois:
    rois = ROIhandler(source_fp, 1, is_mask=False)

    if roi_type == 'rectangle':

        rois.get_rectangles_ijroi(ijroi_fp)
        rois.draw_rect_mask()

        rois = transform_mc_image_sitk(
            rois.box_mask,
            tmap_correction,
            1,
            from_file=False,
            is_binary_mask=True)

        rois = sitk.GetArrayFromImage(rois)
        #get bounding rect. after transformation
        roi_coords = mask_contours_to_boxes(rois)

        #save csv of data
        roi_coords.to_csv(ts + project_name + roi_name + ".csv", index=False)

        #parse csv file into flexImaging xml for RECTANGLES!!!! only!!
        output_flex_rects(
            roi_coords,
            imsres=ims_resolution,
            imsmethod=ims_method,
            roiname=roi_name + "_",
            filename=ts + project_name + roi_name + ".xml")

        if no_splits > 1:
            split_boxes(
                roi_coords,
                no_splits=no_splits,
                base_name=ts + project_name + roi_name,
                ims_res=ims_resolution,
                ims_method=ims_method,
                roi_name=roi_name)

    if roi_type == 'polygon':
        rois.get_polygons_ijroi(ijroi_fp)
        rois.draw_polygon_mask(binary_mask=True, flip_xy=True)
        rois.pg_mask = transform_mc_image_sitk(
            rois.pg_mask,
            tmap_correction,
            1,
            from_file=False,
            is_binary_mask=True)

        #rois = sitk.GetArrayFromImage(rois)

        #get pgs after transformation
        pgs = mask_contours_to_polygons(
            sitk.GetArrayFromImage(rois.pg_mask), arcLenPercent=0.01)
        rois.polygons = pgs

        output_flex_polys(
            rois.polygons,
            imsres=ims_resolution,
            imsmethod=ims_method,
            roiname=roi_name + "_",
            filename=ts + project_name + roi_name + ".xml")

        if no_splits > 1:
            split_polys(
                rois.polygons,
                no_splits=no_splits,
                base_name=ts + project_name + roi_name,
                ims_res=ims_resolution,
                ims_method=ims_method,
                roi_name=roi_name)

    return


if __name__ == '__main__':
    import yaml
    import sys
    with open(sys.argv[1]) as f:
        # use safe_load instead load
        dataMap = yaml.safe_load(f)

    bruker_output_xmls(dataMap['source_fp'], dataMap['target_fp'],
                       dataMap['wd'], dataMap['ijroi_fp'],
                       dataMap['project_name'], dataMap['ims_resolution'],
                       dataMap['ims_method'], dataMap['roi_name'],
                       dataMap['splits'], dataMap['roi_type'])
