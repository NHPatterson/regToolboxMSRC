# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 13:48:04 2017

@author: pattenh1
"""

import numpy as np
import cv2
import os
import SimpleITK as sitk
#import pandas as pd
import time
import datetime
import xml.etree.ElementTree as ET
import xml.dom.minidom
import pkg_resources


class RegImage(object):
    '''
        Container class for image meta data and processing between ITK and cv2

    '''

    def __init__(self, filepath, im_format, img_res=1):
        '''
        Container class for image meta data and processing between ITK and cv2
            :param filepath: filepath to the image
            :type filepath: str

            :param im_format: 'sitk' - SimpleITK format or 'np' - numpy (cv2)
            :type im_format: str

            :param im_res: pixel spacing of image
            :type im_res: float

        '''
        self.type = 'Registration Image Container'
        self.filepath = filepath
        self.im_format = im_format
        self.spacing = float(img_res)

        image = sitk.ReadImage(self.filepath)
        if im_format == 'np':
            self.image = sitk.GetArrayFromImage(image)

        if im_format == 'sitk':
            self.image = image
            if len(self.image.GetSpacing()) == 3:
                self.image.SetSpacing((self.spacing, self.spacing, float(1)))
            else:
                self.image.SetSpacing((self.spacing, self.spacing))

    def to_greyscale(self):
        '''
        Converts RGB image to greyscale using cv2. (sitk images will eventually be converted using ITK...)
        '''
        if self.im_format == 'sitk':
            if self.image.GetNumberOfComponentsPerPixel() == 3:
                spacing = self.image.GetSpacing()
                image = sitk.GetArrayFromImage(self.image)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                image = sitk.GetImageFromArray(image)
                image.SetSpacing(spacing)
            else:
                raise ValueError('Channel depth != 3, image is not RGB type')

        if self.im_format == 'np':
            if self.image.shape == 3 and self.image.shape[2] == 3:
                image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            else:
                raise ValueError('Channel depth != 3, image is not RGB type')

        self.image = image
        self.type = self.type + '-Greyscaled'

    def compress_AF_channels(self, compression):
        '''
        This converts multi 2D layer images like multichannel fluorescence images to a single layer by summing, taking the mean or max of the layer.
        The final image will be rescaled to unsigned 8-bit.

        :param compression: 'sum', 'mean', or 'max'.
        '''
        if self.im_format == 'sitk':
            if self.image.GetDepth() > 1:
                image = sitk.GetArrayFromImage(self.image)

                if compression == 'sum':
                    image = np.sum(image, 0)
                    #print(image.dtype)
                    #image = cast_8bit_np(image)

                if compression == 'mean':
                    image = np.mean(image, 0)
                    #print(image.dtype)

                if compression == 'max':
                    image = np.max(image, 0)
                    #print(image.dtype)
                    #image = cast_8bit_np(image)

                self.image = sitk.GetImageFromArray(image)
                self.image = sitk.RescaleIntensity(self.image, 0, 255)
                self.image = sitk.Cast(self.image, sitk.sitkUInt8)
                #self.image.SetSpacing(self.spacing)
                self.image.SetSpacing((self.spacing, self.spacing))

                self.type = self.type + '-AF channels compressed'
            else:
                raise ValueError('Only one layer, image is not multichannel')

        if self.im_format == 'np':
            if len(self.image.shape) == 3 and self.image.shape[0] > 1:
                image = self.image

                if compression == 'sum':
                    image = image.sum(axis=0)
                if compression == 'mean':
                    image = image.mean(axis=0)
                if compression == 'max':
                    image = image.max(axis=0)

                #image = cast_8bit_np(image)
                self.image = image
                self.type = self.type + '-AF channels compressed'
            else:
                raise ValueError('Only one layer, image is not multichannel')

    def invert_intensity(self):
        '''
        This will invert the intensity scale of a greyscale image. This is useful with histological images where the background is 'whitish.'

        '''
        if self.im_format == 'sitk':
            #use sitk filters instead of CV2 conversion
            image = sitk.InvertIntensity(self.image)

            #img_bu = self.image
            #image = sitk.GetArrayFromImage(self.image)
            #image = cv2.bitwise_not(image)
            #image = sitk.GetImageFromArray(image)

            # image.CopyInformation(img_bu)

        if self.im_format == 'np':
            image = cv2.bitwise_not(self.image)

        self.image = image
        self.type = self.type + '-image intensity inverted'

    def flip_type(self):
        '''
        This is a convenience function that flips an image between cv2 and SimpleITK formats.
        '''
        if self.im_format == 'sitk':
            self.image = sitk.GetArrayFromImage(self.image)
            self.im_format = 'np'

        else:
            self.image = sitk.GetImageFromArray(self.image)
            self.im_format = 'sitk'
            self.image.SetSpacing((self.spacing, self.spacing))


class parameter_files(object):
    '''
        Class to load SimpleITK parameters from file
    '''

    def __init__(self):
        resource_package = 'regToolboxMSRC'

        self.testing = sitk.ReadParameterFile(
            pkg_resources.resource_filename(resource_package, '/'.join(
                ('parameter_files', 'testing.txt'))))
        self.rigid = sitk.ReadParameterFile(
            pkg_resources.resource_filename(resource_package, '/'.join(
                ('parameter_files', 'rigid.txt'))))
        self.scaled_rigid = sitk.ReadParameterFile(
            pkg_resources.resource_filename(resource_package, '/'.join(
                ('parameter_files', 'scaled_rigid.txt'))))
        self.affine = sitk.ReadParameterFile(
            pkg_resources.resource_filename(resource_package, '/'.join(
                ('parameter_files', 'affine.txt'))))
        self.nl = sitk.ReadParameterFile(
            pkg_resources.resource_filename(resource_package, '/'.join(
                ('parameter_files', 'nl.txt'))))
        self.correction = sitk.ReadParameterFile(
            pkg_resources.resource_filename(resource_package, '/'.join(
                ('parameter_files', 'fi_correction.txt'))))
        self.affine_test = sitk.ReadParameterFile(
            pkg_resources.resource_filename(resource_package, '/'.join(
                ('parameter_files', 'affine_test.txt'))))


def get_mask_bb(mask_fp):
    '''
        Uses sitk to get bounding box after reading image from file, assumes image is an uint8 mask.
        Returns top-left x,y pixel coordinates and the width and height of bounding box.

        :param mask_fp: File path to the mask image
    '''
    mask = sitk.ReadImage(mask_fp)
    mask = sitk.ConnectedComponent(mask)
    lab_stats = sitk.LabelStatisticsImageFilter()
    lab_stats.Execute(mask, mask)
    bb = lab_stats.GetBoundingBox(1)
    x, y, w, h = bb[0], bb[2], bb[1] - bb[0], bb[3] - bb[2]
    return x, y, w, h


def register_elx_(moving,
                  fixed,
                  param,
                  moving_mask=None,
                  fixed_mask=None,
                  output_dir="transformations",
                  output_fn="myreg.txt",
                  return_image=False,
                  logging=True,
                  bounding_box=False):
    '''
    Utility function to register 2D images and save their results in a user named subfolder and transformation text file.

    :param moving: SimpleITK image set as moving image. Can optionally pass sitk.ReadImage(moving_img_fp) to load image from file. Warning that usually this function is accompanied using the 'RegImage' class where image spacing is set

    :param fixed: SimpleITK image set as fixed image. Can optionally pass sitk.ReadImage(fixed_img_fp) to load image from file. Warning that usually this function is accompanied using the 'RegImage' class where image spacing is set

    :param param: Elastix paramter file loaded into SWIG. Can optionally pass sitk.ReadParameterFile(parameter_fp) to load text parameter from file. See http://elastix.isi.uu.nl/ for example parameter files

    :param moving_mask: Filepath to moving image (a binary mask) or the moving image itself. Function will type check the image.

    :param fixed_mask:
        Filepath to fixed mask image (a binary mask) or the SimpleITK fixed mask image itself.
        Function will type check the image.

    :param moving_mask:
        Filepath to fixed mask image (a binary mask) or the SimpleITK fixed mask image itself.
        Function will type check the image.

    :param output_dir:
        String used to create a folder in the current working directory to store registration outputs (iteration information and transformation parameter file)

    :param output_fn:
        String used to name transformation file in the output_fn directory

    :param logging:
        Boolean, whether SimpleElastix should log to console. Note that this logging doesn't work in IPython notebooks

    :param bounding_box:
        Currently experimental that addresses masking in SimpleElastix by cropping images to the bounding box of their mask

    :return: Transformation file and optionally the registered moving image
    :return type: SimpleITK parameter map and SimpleITK image

    '''
    try:
        selx = sitk.SimpleElastix()
    except:
        selx = sitk.ElastixImageFilter()

    if logging == True:
        selx.LogToConsoleOn()

    param_selx = param
    #turns off returning the image in the paramter file
    if return_image == False:
        param_selx['WriteResultImage'] = ('false', )

    selx.SetParameterMap(param_selx)

    fixed_shape = fixed.GetSize()
    moving_shape = moving.GetSize()

    bbox_dict = {}
    #set masks if used
    if moving_mask == None:
        pass
    else:
        if isinstance(moving_mask, type(sitk.Image())) == True:
            mask_moving = moving_mask
            mask_moving.SetSpacing(moving.GetSpacing())
            selx.SetMovingMask(mask_moving)

        else:
            mask_moving = sitk.ReadImage(moving_mask)
            mask_moving.SetSpacing(moving.GetSpacing())
            selx.SetMovingMask(mask_moving)

        if bounding_box == True:
            moving_x, moving_y, moving_w, moving_h = get_mask_bb(moving_mask)
            print(moving_x, moving_y, moving_w, moving_h)
            mask_moving = mask_moving[moving_x:moving_x + moving_w, moving_y:
                                      moving_y + moving_h]

            moving = moving[moving_x:moving_x + moving_w, moving_y:
                            moving_y + moving_h]
            moving.SetOrigin((0, 0))
            bbox_dict.update({
                'moving_x': moving_x,
                'moving_y': moving_y,
                'moving_w': moving_w,
                'moving_h': moving_h,
                'moving_shape': moving_shape
            })

    if fixed_mask == None:
        pass
    else:
        if isinstance(fixed_mask, type(sitk.Image())) == True:
            mask_fixed = fixed_mask
            mask_moving.SetSpacing(moving.GetSpacing())
            selx.SetMovingMask(mask_moving)

        else:
            mask_fixed = sitk.ReadImage(fixed_mask)
            mask_fixed.SetSpacing(fixed.GetSpacing())
            selx.SetMovingMask(mask_fixed)

        if bounding_box == True:
            fixed_x, fixed_y, fixed_w, fixed_h = get_mask_bb(fixed_mask)
            print(fixed_x, fixed_y, fixed_w, fixed_h)

            mask_fixed = mask_fixed[fixed_x:fixed_x + fixed_w, fixed_y:
                                    fixed_y + fixed_h]
            fixed = fixed[fixed_x:fixed_x + fixed_w, fixed_y:fixed_y + fixed_h]
            fixed.SetOrigin((0, 0))

            bbox_dict.update({
                'fixed_x': fixed_x,
                'fixed_y': fixed_y,
                'fixed_w': fixed_w,
                'fixed_h': fixed_h,
                'fixed_shape': fixed_shape
            })
        #mask_fixed.SetSpacing(fixed.GetSpacing())
        #selx.SetFixedMask(mask_fixed)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    selx.SetOutputDirectory(os.path.join(os.getcwd(), output_dir))

    selx.SetFixedImage(fixed)
    selx.SetMovingImage(moving)

    selx.LogToFileOn()
    #execute registration:
    if return_image == True:
        transformed_image = selx.Execute()
    else:
        selx.Execute()

    os.rename(
        os.path.join(os.getcwd(), output_dir, 'TransformParameters.0.txt'),
        os.path.join(os.getcwd(), output_dir, output_fn + '.txt'))

    transformationMap = selx.GetTransformParameterMap()

    ##really elegant function return below:
    if len(bbox_dict) > 0 and return_image == True:
        return transformationMap, transformed_image, bbox_dict

    elif len(bbox_dict) == 0 and return_image == True:
        return transformationMap, transformed_image

    elif len(bbox_dict) > 0 and return_image == False:
        return transformationMap, bbox_dict

    else:
        return transformationMap


def paste_to_original_dim(transformed_image, fixed_x, fixed_y, final_size_2D):
    '''
        Experimental support function to used 'crops' of singular masks rather than using Elastix masking (which seems not to work...)
        Returns image in coordinate original coordinate space

        :param fixed_x:
            top-left x coordinate of mask's bounding box

        :param fixed_y:
            top-left y coordinate of mask's bounding box

        :param final_size_2D:
            m x n dimensions of fixed image from registration


    '''

    if transformed_image.GetNumberOfComponentsPerPixel() == 3:
        print('RGB_image')
        placeholder = sitk.Image([final_size_2D[0], final_size_2D[1]],
                                 transformed_image.GetPixelIDValue(), 3)
        placeholder.GetSize()
        transformed_image = sitk.Paste(
            placeholder,
            transformed_image,
            transformed_image.GetSize(),
            destinationIndex=[fixed_x, fixed_y])

    elif transformed_image.GetDepth() > 1:
        print('multichannel_image')

        placeholder = sitk.Image(
            [final_size_2D[0], final_size_2D[1],
             transformed_image.GetDepth()],
            transformed_image.GetPixelIDValue())
        #print('image made')
        #print(str(placeholder.GetSize()))
        #print(str(transformed_image.GetSize()))
        transformed_image = sitk.Paste(
            placeholder,
            transformed_image,
            transformed_image.GetSize(),
            destinationIndex=[fixed_x, fixed_y, 0])

    elif transformed_image.GetDepth(
    ) < 1 and transformed_image.GetNumberOfComponentsPerPixel() == 1:
        print('singlechannel_image')
        placeholder = sitk.Image([final_size_2D[0], final_size_2D[1]],
                                 transformed_image.GetPixelIDValue())
        placeholder.GetSize()
        transformed_image = sitk.Paste(
            placeholder,
            transformed_image,
            transformed_image.GetSize(),
            destinationIndex=[fixed_x, fixed_y])

    return transformed_image


def check_im_size_fiji(image):
    '''
        Checks to see if image size is too large to be loaded into FIJI as a .tiff

        :param image:
            SimpleITK image
    '''
    impixels = image.GetSize()[0] * image.GetSize()[1]

    if len(image.GetSize()) > 2:
        impixels = impixels * image.GetSize()[2]

    impixels = impixels * image.GetNumberOfComponentsPerPixel()

    return impixels > 10**9


def transform_image(moving, transformationMap):

    try:
        transformix = sitk.SimpleTransformix()
    except:
        transformix = sitk.TransformixImageFilter()

    transformix.SetMovingImage(moving)
    transformix.SetTransformParameterMap(transformationMap)
    transformix.LogToConsoleOff()
    moving_tformed = transformix.Execute()
    return (moving_tformed)


def transform_mc_image_sitk(image_fp,
                            transformationMap,
                            img_res,
                            from_file=True,
                            is_binary_mask=False):

    if from_file == True:
        print('image loaded from file')
        image = sitk.ReadImage(image_fp)
        if len(image.GetSpacing()) == 3:
            image.SetSpacing((float(img_res), float(img_res), float(1)))
        else:
            image.SetSpacing((float(img_res), float(img_res)))

    if from_file == False:
        print('image loaded from memory')
        image = image_fp

    # grayscale image transformation
    if image.GetNumberOfComponentsPerPixel() == 1 and image.GetDepth() == 0:
        print('transforming grayscale image')
        tformed_image = transform_image(image, transformationMap)
        print('casting grayscale image')
        if is_binary_mask == True:
            tformed_image = sitk.Cast(tformed_image, sitk.sitkUInt8)
            return tformed_image
        else:
            tformed_image = sitk.RescaleIntensity(tformed_image, 0, 255)
            tformed_image = sitk.Cast(tformed_image, sitk.sitkUInt8)
            return tformed_image

    # RGB image
    if image.GetNumberOfComponentsPerPixel() > 1:
        tformed_image = []
        for chan in range(image.GetNumberOfComponentsPerPixel()):
            print('getting image ' + str(chan) + ' of RGB')
            channel = sitk.VectorIndexSelectionCast(image, chan)
            print('transforming image ' + str(chan) + ' of RGB')
            channel = transform_image(channel, transformationMap)
            print('rescaling image ' + str(chan) + ' of RGB')
            channel = sitk.RescaleIntensity(channel, 0, 255)
            tformed_image.append(channel)
        print('composing RGB')
        tformed_image = sitk.Compose(tformed_image)
        tformed_image = sitk.Cast(tformed_image, sitk.sitkVectorUInt8)
        return tformed_image

    #multilayer 2D image, i.e. multichannel fluorescence
    if image.GetDepth() > 0:
        tformed_image = []
        for chan in range(image.GetDepth()):
            print('getting image ' + str(chan) + ' of multi-layer image')
            channel = image[:, :, chan]
            print('transforming image ' + str(chan) + ' of multi-layer image')
            channel = transform_image(channel, transformationMap)
            print('rescaling image ' + str(chan) + ' of multi-layer image')
            channel = sitk.RescaleIntensity(channel, 0, 255)
            tformed_image.append(channel)

        print('adding images to sequence')
        tformed_image = sitk.JoinSeries(tformed_image)
        print('casting to 8-bit')
        tformed_image = sitk.Cast(tformed_image, sitk.sitkUInt8)
        return tformed_image

    return tformed_image


def transform_from_gui(source_fp, transforms, TFM_wd, src_reso, project_name):
    for i in range(len(transforms)):
        if i == 0:
            source = transform_mc_image_sitk(
                source_fp,
                transforms[i],
                src_reso,
                from_file=True,
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


def write_param_xml(xml_params, opdir, ts, project_name):
    stringed = ET.tostring(xml_params)
    reparsed = xml.dom.minidom.parseString(stringed)

    myfile = open(opdir + ts + project_name + '_parameters.xml', "w")
    myfile.write(reparsed.toprettyxml(indent="\t"))
    myfile.close()
    return


def prepare_output(wd, project_name, xml_params):
    #prepare folder name

    ts = datetime.datetime.fromtimestamp(
        time.time()).strftime('%Y%m%d_%H_%M_%S_')
    os.chdir(wd)
    os.makedirs(ts + project_name + "_images")
    opdir = ts + project_name + "_images\\"

    #output parameters to XML file
    #output parameters to XML file
    write_param_xml(xml_params, opdir, ts, project_name)


def reg_image_preprocess(image_fp, img_res, img_type='RGB_l'):
    if img_type in ['RGB_l', 'AF']:
        if img_type == "RGB_l":
            out_image = RegImage(image_fp, 'sitk', img_res)
            out_image.to_greyscale()
            out_image.invert_intensity()

        else:
            out_image = RegImage(image_fp, 'sitk', img_res)
            if out_image.image.GetDepth() > 1:
                out_image.compress_AF_channels('max')
            if out_image.image.GetNumberOfComponentsPerPixel() == 3:
                out_image.to_greyscale()
    else:
        print(img_type + ' is an invalid image type (valid: RGB_l & AF)')

    return out_image


def parameter_load(reg_model):
    if isinstance(reg_model, str):
        if reg_model in [
                'affine', 'affine_test', 'fi_correction', 'nl', 'rigid',
                'scaled_rigid', 'testing'
        ]:
            reg_param = getattr(parameter_files(), reg_model)
            return reg_param

        else:
            try:
                reg_param = sitk.ReadParameterFile(reg_model)
                return reg_param
            except:
                print('invalid parameter file')
    else:
        print(
            'parameter input is not a filepath or default parameter file str')
