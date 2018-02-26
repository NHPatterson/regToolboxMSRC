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

class reg_image(object):
    '''
        Container class for image meta data and processing between ITK and cv2
            
    '''
    def __init__(self, filepath, im_format, img_res = 1):
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
                self.image.SetSpacing((self.spacing,self.spacing, float(1)))
            else:
                self.image.SetSpacing((self.spacing,self.spacing))



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
                raise ValueError('Channel depth != 3, image is not RGB type'
                                 )

        if self.im_format == 'np':
            if self.image.shape == 3 and self.image.shape[2] == 3:
                image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            else:
                raise ValueError('Channel depth != 3, image is not RGB type'
                                 )

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
                    image = np.sum(image,0)
                    #print(image.dtype)
                    #image = cast_8bit_np(image)
                    
                if compression == 'mean':
                    image = np.mean(image,0)
                    #print(image.dtype)
                    
                if compression == 'max':
                    image = np.max(image,0)
                    #print(image.dtype)
                    #image = cast_8bit_np(image)
                
                self.image = sitk.GetImageFromArray(image)
                self.image = sitk.RescaleIntensity(self.image, 0, 255)
                self.image = sitk.Cast(self.image, sitk.sitkUInt8)
                #self.image.SetSpacing(self.spacing)
                self.image.SetSpacing((self.spacing,self.spacing))

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
    
                image = cast_8bit_np(image)
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
            self.image.SetSpacing((self.spacing,self.spacing))

class parameter_files(object):
    '''
        Class to load SimpleITK parameters from file
    '''
    def __init__(self):
        resource_package = 'regToolboxMSRC'  
    
        pkg_resources.resource_stream(resource_package, '/'.join(('parameter_files', 'testing.txt')))
        self.testing = sitk.ReadParameterFile(pkg_resources.resource_stream(resource_package, '/'.join(('parameter_files', 'testing.txt'))))
        self.rigid = sitk.ReadParameterFile(pkg_resources.resource_stream(resource_package, '/'.join(('parameter_files', 'rigid.txt'))))
        self.scaled_rigid = sitk.ReadParameterFile(pkg_resources.resource_stream(resource_package, '/'.join(('parameter_files', 'scaled_rigid.txt'))))
        self.affine = sitk.ReadParameterFile(pkg_resources.resource_stream(resource_package, '/'.join(('parameter_files', 'affine.txt'))))
        self.nl = sitk.ReadParameterFile(pkg_resources.resource_stream(resource_package, '/'.join(('parameter_files', 'nl.txt'))))
        self.correction = sitk.ReadParameterFile(pkg_resources.resource_stream(resource_package, '/'.join(('parameter_files', 'fi_correction.txt'))))
            
def get_mask_bb(mask_fp):
    '''
        Uses cv2 to get bounding box after reading image from file, assumes image is an uint8 mask.
        Returns top-left x,y pixel coordinates and the width and height of bounding box.
        
        :param mask_fp: File path to the mask image
    '''
    mask = sitk.GetArrayFromImage(sitk.ReadImage(mask_fp))
    hi,cnt,cnt2 = cv2.findContours(mask, 1, 2)
    x,y,w,h = cv2.boundingRect(cnt[0])
    return x,y,w,h

def register_elx_(moving, fixed, param, moving_mask = None,  fixed_mask = None, output_dir= "transformations", output_fn = "myreg.txt", return_image = True, logging = True, bounding_box = True):
    '''
    Utility function to register 2D images and save their results in a user named subfolder and transformation text file.
    
    :param moving: SimpleITK image set as moving image. Can optionally pass sitk.ReadImage(moving_img_fp) to load image from file. Warning that usually this function is accompanied using the 'reg_image' class where image spacing is set
    
    :param fixed: SimpleITK image set as fixed image. Can optionally pass sitk.ReadImage(fixed_img_fp) to load image from file. Warning that usually this function is accompanied using the 'reg_image' class where image spacing is set
        
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
    selx = sitk.SimpleElastix()
    
    if logging == True:
        selx.LogToConsoleOn()

    param_selx = param
    #turns off returning the image in the paramter file
    if return_image == False:
        param_selx['WriteResultImage'] = ('false',)
    
    selx.SetParameterMap(param_selx)
    
    #set masks if used
    if moving_mask == None :
        pass
    else:
        mask_moving = sitk.ReadImage(moving_mask)
#        if bounding_box == True:
#            moving_x,moving_y,moving_w,moving_h = get_mask_bb(moving_mask)
#            mask_moving = mask_moving[moving_x:moving_x+moving_w,moving_y:moving_y+moving_h]
#            moving = moving[moving_x:moving_x+moving_w,moving_y:moving_y+moving_h]

        mask_moving.SetSpacing(moving.GetSpacing())
        selx.SetMovingMask(mask_moving)
        
    if fixed_mask == None :
        pass
    else:
        mask_fixed = sitk.ReadImage(fixed_mask)
        fixed_shape_original = mask_fixed.GetSize()
        if bounding_box == True:
            fixed_x,fixed_y,fixed_w,fixed_h = get_mask_bb(fixed_mask)
            mask_fixed = mask_fixed[fixed_x:fixed_x+fixed_w,fixed_y:fixed_y+fixed_h]
            fixed = fixed[fixed_x:fixed_x+fixed_w,fixed_y:fixed_y+fixed_h]
            
        mask_fixed.SetSpacing(fixed.GetSpacing())
        selx.SetFixedMask(mask_fixed)

    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    selx.SetOutputDirectory(os.getcwd() + "\\" + output_dir)
    
    selx.SetFixedImage(fixed)
    selx.SetMovingImage(moving)
    
    selx.LogToFileOn()
    #execute registration:
    if return_image == True:
        transformimage = selx.Execute()
    else:
        selx.Execute()
    
    os.rename(os.getcwd()+ "\\" + output_dir + "\\TransformParameters.0.txt", os.getcwd()+ "\\" + output_dir + "\\" + output_fn)
    
    transformationMap = selx.GetTransformParameterMap()
    
    if fixed_mask != "none" and bounding_box == True:
        return transformationMap, fixed_x, fixed_y, fixed_w, fixed_h, fixed_shape_original
    elif return_image == True:
        return transformationMap, transformed_image
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
        placeholder = sitk.Image([final_size_2D[0],final_size_2D[1]],transformed_image.GetPixelIDValue(), 3)
        placeholder.GetSize()
        transformed_image = sitk.Paste(placeholder, transformed_image, transformed_image.GetSize(), destinationIndex=[fixed_x, fixed_y])
    
    elif transformed_image.GetDepth() > 1:
        print('multichannel_image')

        placeholder = sitk.Image([final_size_2D[0],final_size_2D[1],transformed_image.GetDepth()],transformed_image.GetPixelIDValue())
        #print('image made')
        #print(str(placeholder.GetSize()))
        #print(str(transformed_image.GetSize()))
        transformed_image = sitk.Paste(placeholder, transformed_image, transformed_image.GetSize(), destinationIndex=[fixed_x, fixed_y,0])
    
    elif transformed_image.GetDepth() < 1 and transformed_image.GetNumberOfComponentsPerPixel() == 1:
        print('singlechannel_image')
        placeholder = sitk.Image([final_size_2D[0],final_size_2D[1]],transformed_image.GetPixelIDValue())
        placeholder.GetSize()
        transformed_image = sitk.Paste(placeholder, transformed_image, transformed_image.GetSize(), destinationIndex=[fixed_x, fixed_y])

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
    transformix = sitk.SimpleTransformix()
    transformix.SetMovingImage(moving)
    transformix.SetTransformParameterMap(transformationMap)
    transformix.LogToConsoleOff()
    moving_tformed = transformix.Execute()
    return(moving_tformed)
            
def transform_mc_image_sitk(image_fp, transformationMap, img_res, from_file = True, is_binary_mask = False):
    
    if from_file == True:
        print('image loaded from file')
        image = sitk.ReadImage(image_fp)
        if len(image.GetSpacing()) == 3:
            image.SetSpacing((float(img_res),float(img_res), float(1)))
        else:
            image.SetSpacing((float(img_res),float(img_res)))
        
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
            print('getting image ' + str(chan) + ' of RGB' )
            channel = sitk.VectorIndexSelectionCast(image, chan)
            print('transforming image ' + str(chan) + ' of RGB' )
            channel = transform_image(channel, transformationMap)
            print('rescaling image ' + str(chan) + ' of RGB' )
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
                print('getting image ' + str(chan) + ' of multi-layer image' )
                channel = image[:,:,chan]
                print('transforming image ' + str(chan) + ' of multi-layer image' )
                channel = transform_image(channel, transformationMap)
                print('rescaling image ' + str(chan) + ' of multi-layer image' )
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
            source = transform_mc_image_sitk(source_fp, transforms[i], src_reso, from_file = True, is_binary_mask = False)
        if i > 0:
            source = transform_mc_image_sitk(source, transforms[i], source.GetSpacing()[0], from_file = False, is_binary_mask = False)
    os.chdir(TFM_wd)
    sitk.WriteImage(source, project_name + ".tif",True)

def write_param_xml(xml_params, opdir, ts, project_name):
    stringed = ET.tostring(xml_params)
    reparsed = xml.dom.minidom.parseString(stringed)
    
    myfile = open(opdir + ts + project_name + '_parameters.xml', "w")  
    myfile.write(reparsed.toprettyxml(indent="\t")) 
    myfile.close()
    return

def prepare_output(wd, project_name, xml_params):
    #prepare folder name

    ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H_%M_%S_')
    os.chdir(wd)
    os.makedirs(ts + project_name + "_images")
    opdir = ts + project_name + "_images\\"
    
    #output parameters to XML file
    #output parameters to XML file
    write_param_xml(xml_params, opdir, ts, project_name)
    
def register_SSM(source_fp, source_res, target1_fp, target1_res , target2_fp, target2_res, source_mask_fp, target1_mask_fp, target2_mask_fp, wd, source_img_type, target_img_type1,target_img_type2, reg_model1, reg_model2, project_name, xml_params, intermediate_output = False, bounding_box = False):


    
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

def register_SSS(source_fp, source_res, target_fp, target_res, source_mask_fp, target_mask_fp, wd, source_img_type, target_img_type, reg_model1, project_name, xml_params):
    
    #prepare folder name
    ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H_%M_%S_')
    
    #register
    os.chdir(wd)
    os.makedirs(ts + project_name + "_images")
    opdir = ts + project_name + "_images\\"
    
    #output parameters to XML file
    #output parameters to XML file
    write_param_xml(xml_params, opdir, ts, project_name)
    
    #load registration parameters based on input
    if reg_model1 == "Rigid":
        reg_param1 = parameter_files().rigid    
    elif reg_model1 == "Affine":
        reg_param1 = parameter_files().affine   
    
    #load images for registration:
    
    if source_img_type == "HE":
        source = reg_image(source_fp,'sitk', source_res)
        source.to_greyscale()
        source.invert_intensity()
        
    else:
        source = reg_image(source_fp,'sitk', source_res)
        if source.image.GetDepth() > 1:
            source.compress_AF_channels('max')



    print(source.type)
    print(source.image.GetSize())
    print("source image loaded")
        
    if target_img_type == "HE":
        target = reg_image(target_fp,'sitk', target_res)
        target.to_greyscale()
        target.invert_intensity()
        
    else:
        target = reg_image(target_fp,'sitk', target_res)
        if target.image.GetDepth() > 1:
            target.compress_AF_channels('max')

    print(target.type)
    print(target.image.GetSize())
    print("target image loaded")

    
    src_tgt1_tform = register_elx_(source.image, target.image, reg_param1, moving_mask = source_mask_fp,  fixed_mask = target_mask_fp, output_dir= ts + project_name + "_tforms_src_tgt", output_fn = ts + project_name +"_"+reg_model1+"_src_tgt.txt", logging = True)
    
    #transform result and save output
    tformed_im = transform_mc_image_sitk(source_fp, src_tgt1_tform, source_res)
    sitk.WriteImage(tformed_im, opdir + project_name + "_src_tgt.tif", True)

    
    return

def register_MSS(source_fp, source_res, target_fp, target_res, source_mask_fp, target_mask_fp, wd, source_img_type, target_img_type, reg_model1, project_name, xml_params, intermediate_output = True, bounding_box = True):

    #prepare folder name
    ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H_%M_%S_')
    
    #register
    os.chdir(wd)
    os.makedirs(ts + project_name + "_images")
    opdir = ts + project_name + "_images\\"

    #output parameters to XML file
    #output parameters to XML file
    write_param_xml(xml_params, opdir, ts, project_name)
    
    #load registration parameters based on input
    if reg_model1 == "Rigid":
        reg_param1 = parameter_files().rigid    
    elif reg_model1 == "Affine":
        reg_param1 = parameter_files().affine   
    
    #load images for registration:
        
    if source_img_type == "HE":
        source = reg_image(source_fp,'sitk', source_res)
        source.to_greyscale()
        #source.invert_intensity()
        
    else:
        source = reg_image(source_fp,'sitk', source_res)
        if source.image.GetDepth() > 1:
            source.compress_AF_channels('max')

    
    print("source image loaded")
        
    if target_img_type == "HE":
        target = reg_image(target_fp,'sitk',target_res)
        target.to_greyscale()
        #target.invert_intensity()
        
    else:
        target = reg_image(target_fp,'sitk', target_res)
        if target.image.GetDepth() > 1:
            target.compress_AF_channels('max')


    print("target image loaded")
    final_size_2D = target.image.GetSize()

    if bounding_box == True and os.path.exists(target_mask_fp):
        src_tgt1_tform_init, init_img, fixed_x, fixed_y, fixed_w, fixed_h, fixed_shape_original = register_elx_img(source.image, target.image, reg_param1, moving_mask = source_mask_fp,  fixed_mask = target_mask_fp, output_dir= ts + project_name + "_tforms_src_tgt", output_fn = ts + project_name +"_"+reg_model1+"_src_tgt.txt", logging = True, bounding_box = True)
    
    else:
        src_tgt1_tform_init, init_img = register_elx_img(source.image, target.image, reg_param1, moving_mask = source_mask_fp,  fixed_mask = target_mask_fp, output_dir= ts + project_name + "_tforms_src_tgt", output_fn = ts + project_name +"_"+reg_model1+"_src_tgt.txt", logging = True)
    
    
    
    #src_tgt1_tform_init, init_img = register_elx_img(source.image, target.image, reg_param1, moving_mask = source_mask_fp,  fixed_mask = target_mask_fp, output_dir= ts + project_name + "_tforms_src_tgt", output_fn = ts + project_name +"_"+reg_model1+"_src_tgt.txt", logging = True)
    
    del source
    
    
    if bounding_box == True and os.path.exists(target_mask_fp):
        src_tgt1_tform_nl, fixed_x, fixed_y, fixed_w, fixed_h, fixed_shape_original = register_elx_(init_img, target.image, parameter_files().nl, moving_mask = source_mask_fp,  fixed_mask = target_mask_fp, output_dir= ts + project_name + "_tforms_src_tgt", output_fn = ts + project_name +"_nl_src_tgt.txt", logging = True, bounding_box = True)
    
    else:
        src_tgt1_tform_nl = register_elx_(init_img, target.image, parameter_files().nl, moving_mask = source_mask_fp,  fixed_mask = target_mask_fp, output_dir= ts + project_name + "_tforms_src_tgt", output_fn = ts + project_name +"_"+reg_model1+"_src_tgt.txt", logging = True)
    
    
    
#    #transform result and save output
#    if intermediate_output == True:
#        tformed_im = transform_mc_image_sitk(source_fp, src_tgt1_tform_init, source_res)
#        sitk.WriteImage(tformed_im, opdir + project_name + "_init_src_tgt.tif", True)
#    
#    src_tgt1_tform_nl = register_elx_(init_img, target.image, parameter_files().nl, moving_mask = source_mask_fp,  fixed_mask = target_mask_fp, output_dir= ts + project_name + "_tforms_src_tgt", output_fn = ts + project_name +"_nl_src_tgt.txt", logging = True)
    
    
    #transform and write output images:
    tformed_im = transform_mc_image_sitk(source_fp, src_tgt1_tform_init, source_res)
    tformed_im = transform_mc_image_sitk(tformed_im, src_tgt1_tform_nl, source_res, from_file = False)
    
    if bounding_box == True and os.path.exists(target_mask_fp):
        tformed_im = paste_to_original_dim(tformed_im, fixed_x, fixed_y, final_size_2D)
    
    if check_im_size_fiji(tformed_im) == True:
        sitk.WriteImage(tformed_im, opdir + project_name + "_src_tgt.mha", True)
    else:
        sitk.WriteImage(tformed_im, opdir + project_name + "_src_tgt.tif", True)
    
    #sitk.WriteImage(tformed_im, opdir + project_name + "_nl_src_tgt.tif", True)
    
    return

def register_MSM(source_fp, source_res, target1_fp, target1_res , target2_fp, target2_res, source_mask_fp, target1_mask_fp, target2_mask_fp, wd, source_img_type, target_img_type1,target_img_type2, reg_model1, reg_model2, project_name, xml_params, intermediate_output = False):
    
    
    #prepare folder name
    ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H_%M_%S_')
    
    #register
    os.chdir(wd)
    os.makedirs(ts + project_name + "_images")
    opdir = ts + project_name + "_images\\"
    
    #output parameters to XML file
    write_param_xml(xml_params, opdir, ts, project_name)

    
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
        target1 = reg_image(target1_fp,'sitk', source_res)
        target1.to_greyscale()
        target1.invert_intensity()
        
    else:
        target1 = reg_image(target1_fp,'sitk', source_res)
        if target1.image.GetDepth() > 1:
            target1.compress_AF_channels('max')


    print("target 1 image loaded")

    

    
    #img_output_dir = os.getcwd() + "\\" + ts + project_name + "_tforms" +"\\"

    
    src_tgt1_tform = register_elx_(source.image, target1.image, reg_param1, moving_mask = source_mask_fp,  fixed_mask = target1_mask_fp, output_dir= ts + project_name + "_tforms_src_tgt1", output_fn = ts + project_name +"_"+reg_model1+"_src_tgt1.txt", logging = True)
    
    #transform result and save output
    os.chdir(wd)

    if intermediate_output == True:
        tformed_im = transform_mc_image_sitk(source_fp, src_tgt1_tform, source_res)
        sitk.WriteImage(tformed_im, opdir + project_name + "_src_tgt1.tif", True)


    del source
    
    if target_img_type2 == "HE":
        target2 = reg_image(target2_fp,'sitk')
        target2.to_greyscale()
        target2.invert_intensity()
        
    else:
        target2 = reg_image(target2_fp,'sitk')
        if target2.image.GetDepth() > 1:
            target2.compress_AF_channels('max')

    print("target 2 image loaded")
    
    tgt1_tgt2_tform_init, init_img = register_elx_(target1.image, target2.image, reg_param2, moving_mask = target1_mask_fp,  fixed_mask = target2_mask_fp, output_dir= ts + project_name + "_tforms_tgt1_tgt2", output_fn = ts + project_name +"_"+reg_model1+"_tgt1_tgt2.txt", logging = True)
    
    tgt1_tgt2_tform_nl = register_elx_img(init_img, target2.image, parameter_files().nl, moving_mask = "none",  fixed_mask = target2_mask_fp, output_dir= ts + project_name + "_tforms_src_tgt", output_fn = ts + project_name +"_nl_src_tgt.txt", logging = True)
    

    #transform source 1 and write output images:
    tformed_im = transform_mc_image_sitk(source_fp, src_tgt1_tform, source_res)
    sitk.WriteImage(tformed_im, opdir + project_name + "_lin_src_tgt1.tif", True)
    tformed_im = transform_mc_image_sitk(tformed_im, tgt1_tgt2_tform_init, source_res, from_file = False)
    tformed_im = transform_mc_image_sitk(tformed_im, tgt1_tgt2_tform_nl, source_res, from_file = False)
    sitk.WriteImage(tformed_im, opdir + project_name + "_nl_src_tgt2.tif", True)
    
    #transform target 1 to target 2 and write output images:
    tformed_im = transform_mc_image_sitk(target1_fp, tgt1_tgt2_tform_init, target1_res, from_file = True)
    tformed_im = transform_mc_image_sitk(tformed_im, tgt1_tgt2_tform_nl, target1_res, from_file = False)
    sitk.WriteImage(tformed_im, opdir + project_name + "_nl_tgt1_tgt2.tif", True)
    
    return
    
