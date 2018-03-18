# -*- coding: utf-8 -*-
"""
Created on Wed Dec 13 09:31:56 2017

@author: pattenh1
"""

import os
import cv2
import SimpleITK as sitk
import ijroi
import datetime
import time
import numpy as np
import pandas as pd
import lxml.etree
import lxml.builder
import matplotlib
from matplotlib import cm
from regToolboxMSRC.utils.reg_utils import register_elx_, reg_image_preprocess, parameter_files, transform_mc_image_sitk


class BrukerFlexROIs(object):
    def __init__(self, roi_image_fp, img_res, is_mask=False):
        self.type = 'ROI Container'
        self.roi_image_fp = roi_image_fp
        target_image = sitk.ReadImage(roi_image_fp)
        self.img_res = float(img_res)

        self.zero_image = np.zeros(target_image.GetSize()[::-1])

        self.roi_corners = []

        if is_mask == True:
            self.roi_mask = sitk.ReadImage(roi_image_fp)
            self.roi_mask.SetSpacing((self.img_res, self.img_res))

    ##this function parses the ImageJ ROI file into all corners and far corners for rectangle ROIs
    #it only keeps the corners necessary for cv2 drawing
    def get_rectangles_ijroi(self, ij_rois_fp):

        rois = ijroi.read_roi_zip(ij_rois_fp)
        allcoords = [poly[1] for poly in rois]
        corners = [rect[[0, 2]] for rect in allcoords]
        self.roi_corners = corners
        self.allcoords = allcoords

    ###grabs polygonal ijrois
    def get_polygons_ijroi(self, ij_rois_fp):

        rois = ijroi.read_roi_zip(ij_rois_fp)
        polyallcoords = [poly[1] for poly in rois]
        self.polygons = polyallcoords

    ##this function draws the mask needed for general FI rois
    def draw_rect_mask(self, return_np=False):
        if len(self.roi_corners) == 0:
            raise ValueError('Rois have not been generated')

        for i in range(len(self.roi_corners)):
            if i == 0:
                filled = cv2.rectangle(
                    self.zero_image,
                    (self.roi_corners[i][0][1], self.roi_corners[i][0][0]),
                    (self.roi_corners[i][1][1], self.roi_corners[i][1][0]),
                    (255),
                    thickness=-1)
            else:
                filled = cv2.rectangle(
                    filled,
                    (self.roi_corners[i][0][1], self.roi_corners[i][0][0]),
                    (self.roi_corners[i][1][1], self.roi_corners[i][1][0]),
                    (255),
                    thickness=-1)

        if return_np == True:
            self.np_roi_mask = filled.astype(np.uint8)

        self.roi_mask = sitk.GetImageFromArray(filled.astype(np.uint8))
        self.roi_mask.SetSpacing((self.img_res, self.img_res))

    ##this function slices all the rois into sitk images
    def get_rect_rois_as_images(self, image_fp):
        if len(self.roi_corners) == 0:
            raise ValueError('Rois have not been generated')

        bg_image = sitk.ReadImage(image_fp)
        roi_slices = []

        for i in range(len(self.allcoords)):
            roi_slices.append(bg_image[self.allcoords[i][0][1]:self.allcoords[
                i][1][1], self.allcoords[i][0][0]:self.allcoords[i][3][0]])
        self.roi_slices = []
        self.roi_slices.append(roi_slices)

    def get_index_and_overlap(self, ims_index_map_fp, ims_res, img_res):
        if self.polygons:
            ims_idx_np = sitk.GetArrayFromImage(
                sitk.ReadImage(ims_index_map_fp))
            scale_factor = ims_res / img_res
            zero_img = np.zeros(ims_idx_np.shape[::-1])

            for i in range(len(self.polygons)):
                fill = cv2.fillConvexPoly(zero_img, self.polygons[i].astype(
                    np.int32), i + 1)

            fill = np.transpose(fill)

            dfs = []

            for i in range(len(self.polygons)):
                whereresult = ims_idx_np[[
                    np.where(fill == i + 1)[0],
                    np.where(fill == i + 1)[1]
                ]]

                uniques, counts = np.unique(whereresult, return_counts=True)

                df_intermed = pd.DataFrame({
                    'roi_index': i + 1,
                    'ims_index': uniques,
                    'overlap': counts / scale_factor**2
                })

                dfs.append(df_intermed)

            df = pd.concat(dfs)
            self.rois_ims_indexed = df

        else:
            raise ValueError('polygon coordinates have not been loaded')

    def get_pg_rois_as_image(self):
        if self.polygons:
            zero_img = self.zero_image.copy()
            
            for i in range(len(self.polygons)):
                cc = cv2.fillConvexPoly(zero_img, self.polygons[i].astype(
                    np.int32), i + 1)
    
            cc = np.transpose(cc)
            self.pg_cc_mask = sitk.GetImageFromArray(cc.astype(np.uint32))
            self.pg_cc_mask.SetSpacing((self.img_res, self.img_res))
            
        else:
            raise ValueError('polygon coordinates have not been loaded')

def mask_contours_to_boxes(binary_mask):

    ret, threshsrc = cv2.threshold(binary_mask, 1, 256, 0)
    im2, contours, hierarchy = cv2.findContours(threshsrc, cv2.RETR_EXTERNAL,
                                                cv2.CHAIN_APPROX_NONE)

    xs = []
    ys = []
    ws = []
    hs = []

    for i in range(len(contours)):
        cnt = contours[i]
        x, y, w, h = cv2.boundingRect(cnt)
        xs.append(x)
        ys.append(y)
        ws.append(w)
        hs.append(h)
    boxes = pd.DataFrame(xs, columns=['x1'])
    boxes['y1'] = ys
    boxes['x2'] = np.array(xs) + np.array(ws)
    boxes['y2'] = np.array(ys) + np.array(hs)

    boxes['p1'] = boxes['x1'].map(str) + ',' + boxes['y1'].map(str)
    boxes['p2'] = boxes['x2'].map(str) + ',' + boxes['y2'].map(str)

    boxes = boxes.sort_values(['y1'], ascending=True)
    boxes = boxes.reset_index()

    return (boxes)


#randomly split rois and reset parameters
def split_boxes(roi_coords,
                no_splits=4,
                base_name="base",
                ims_res="20",
                ims_method="par",
                roi_name="roi"):

    shuffled_rois = roi_coords.sample(frac=1)
    nrow_df = shuffled_rois.shape[0]
    no_per_group = nrow_df / no_splits
    select_seq = np.arange(0, nrow_df - 1, np.floor(no_per_group))

    splits = []
    for i in range(no_splits):

        if i == 0:
            splits.append(shuffled_rois.iloc[0:int(select_seq[i + 1])])

        elif i > 0 and i < no_splits - 1:

            first_idx = int(select_seq[i])
            last_idx = int(select_seq[i + 1])
            splits.append(shuffled_rois.iloc[first_idx:last_idx])

        else:

            first_idx = int(select_seq[i])
            last_idx = int(nrow_df)
            splits.append(shuffled_rois.iloc[first_idx:last_idx])

    for i in range(len(splits)):
        splits[i] = splits[i].sort(['y1'], ascending=True)
        splits[i] = splits[i].reset_index(drop=True)

        #save csv of data
        splits[i].to_csv(base_name + "_" + str(i) + ".csv", index=False)

        #parse csv file into flexImaging xml for RECTANGLES!!!! only!!
        output_flex_rects(
            splits[i],
            imsres=ims_res,
            imsmethod=ims_method,
            roiname=roi_name + "_split" + str(i) + "_",
            filename=base_name + "_" + str(i) + ".xml")


def output_flex_rects(boundingRect_df,
                      imsres="100",
                      imsmethod="mymethod.par",
                      roiname="myroi_",
                      filename="myxml.xml"):

    ##FI boxes to FlexImaging format:
    cmap = cm.get_cmap('Spectral', len(boundingRect_df))  # PiYG
    rgbs = []
    for i in range(cmap.N):
        rgb = cmap(
            i)[:3]  # will return rgba, we take only first 3 so we get rgb
        rgbs.append(matplotlib.colors.rgb2hex(rgb))

    metadata_df = pd.DataFrame(
        np.arange(1,
                  len(boundingRect_df) + 1, 1), columns=['idx'])
    metadata_df['namefrag'] = roiname
    metadata_df['name'] = metadata_df['namefrag'] + metadata_df['idx'].map(str)
    metadata_df['SpectrumColor'] = rgbs

    areaxmls = []

    for j in range(len(boundingRect_df)):
        E = lxml.builder.ElementMaker()
        ROOT = E.Area
        FIELD1 = E.Raster
        FIELD2 = E.Method
        POINT1 = E.Point
        POINT2 = E.Point

        imsraster = str(imsres) + ',' + str(imsres)

        the_doc = ROOT(
            '',
            Type="0",
            Name=metadata_df['name'][j],
            Enabled="0",
            ShowSpectra="0",
            SpectrumColor=metadata_df['SpectrumColor'][j])
        the_doc.append(FIELD1(imsraster))
        the_doc.append(FIELD2(imsmethod))
        the_doc.append(POINT1(str(boundingRect_df['p1'][j])))
        the_doc.append(POINT2(str(boundingRect_df['p2'][j])))

        areaxmls.append(
            lxml.etree.tostring(
                the_doc, pretty_print=True, encoding='unicode'))

    f = open(filename, 'w')
    for i in range(len(areaxmls)):
        f.write(areaxmls[i])  # python will convert \n to os.linesep
    f.close()


#ims_rois = BrukerFlexROIs('/home/nhp/testing_data/slide2_s3_BF_0001.jpg',1,is_mask=True)
#ims_rois.get_rectangles_ijroi('/home/nhp/testing_data/slide2_s3_rois.zip')
#ims_rois.draw_rect_mask()
#
#stats = sitk.LabelStatisticsImageFilter()
#bboxes = []
#for label in stats.GetLabels():
#    if label == 0:
#        pass
#    else:
#        bbox = stats.GetBoundingBox(label)
#        bboxes.append(bbox)
#
#bboxes = np.array(bboxes)
#
#
#stats.Execute(sitk.ConnectedComponent(ims_rois.roi_mask),sitk.ConnectedComponent(ims_rois.roi_mask))
#while i > 0:
#    bbox = stats.GetBoundingBox()
#ims_rois.roi_mask.GetPixelIDTypeAsString()
#sitk.WriteImage(ims_rois.roi_mask, '/home/nhp/test.mha',True)

def bruker_output_xmls(source_fp,
                       target_fp,
                       wd,
                       ijroi_fp,
                       project_name,
                       ims_resolution=10,
                       ims_method="par",
                       roi_name="roi",
                       splits="0"):

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
    rois = BrukerFlexROIs(source_fp, 1, is_mask=False)
    rois.get_rectangles_ijroi(ijroi_fp)
    rois.draw_rect_mask(return_np=False)
    rois = transform_mc_image_sitk(
        rois.roi_mask,
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

    return


##testing:
#fp_moving = 'D:/testing_data/BrukerFlexROIs_testing/171127 mouse liver malaria_BF_set1sec2.jpg'
#fp_fixed = 'D:/testing_data/BrukerFlexROIs_testing/171127 mouse liver malaria_BF_set1sec2_0001.jpg'
#wd = 'D:/testing_data/BrukerFlexROIs_testing'
#ijroi_fp = 'D:/testing_data/BrukerFlexROIs_testing/lesion_rois.zip'
#project_name = 'FI_rois_malaria_testing'
#ims_resolution = 20
#ims_method = "parameter_file"
#roi_name= "roi"
