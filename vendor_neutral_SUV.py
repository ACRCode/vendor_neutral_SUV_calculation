# -*- coding: utf-8 -*-
"""
Created on Mon Sep 14 14:38:32 2020

@author: Kendall Schmidt kschmidt2@acr.org
"""

import os
import pydicom
from datetime import datetime
from datetime import timedelta
import math 
import pandas as pd
import numpy as np

def convert_to_SUV(dicom_header):
    #converts a single dicom PET image to SUV
    
    corrected_image = dicom_header.CorrectedImage;
    decay_correction = dicom_header.DecayCorrection;
    
    try:
        if 'DECY' in corrected_image and 'ATTN' in corrected_image and decay_correction == 'START':
            pass
    except:
        raise Exception('cannot perform SUV conversion: "DECY" not in corrected_image or "ATTN" not in corrected_image or decay_correction != "START"')
        
    else:
        
        pixel_data = dicom_header.pixel_array
        slope = dicom_header.RescaleSlope
        intercept = dicom_header.RescaleIntercept
        img = pixel_data * slope + intercept
        
        if dicom_header.Units == 'BQML':
            
            half_life = float(dicom_header.RadiopharmaceuticalInformationSequence[0].RadionuclideHalfLife) #seconds
            series_date = dicom_header.SeriesDate
            series_time = dicom_header.SeriesTime.split('.')[0]
            acquisition_date = dicom_header.AcquisitionDate
            acquisition_time = dicom_header.AcquisitionTime.split('.')[0]
            
            series_datetime = datetime.strptime(series_date + series_time,  '%Y%m%d%H%M%S')
            acquisition_datetime = datetime.strptime(acquisition_date + acquisition_time,  '%Y%m%d%H%M%S')
            
            series_acq_diff = acquisition_datetime - series_datetime
            
            if series_acq_diff.days >= 0:
             
                scan_datetime = series_datetime
                
            else: # may be a post-processed series
                
                try: #check GE private tag for PET scan datetime
                    
                    scan_datetime = datetime.strptime(dicom_header[0x9, 0x100d].value.split('.')[0],  '%Y%m%d%H%M%S')
                    
                except: #may be a Siemens series with altered date and time
                    #have not encountered data that fit this criteria, so have not valiated this section
                    #if input fits this criteria, an exception will be raised
                    try:
                        if dicom_header.FrameReferenceTime > 0 & dicom_header.ActualFrameDuration > 0:
                            
                             frame_ref_time = dicom_header.FrameReferenceTime / 1000 #convert frame reference time to seconds
                             frame_datetime = timedelta(seconds=frame_ref_time) #datetime format conversion
                             frame_duration = dicom_header.ActualFrameDuration / 1000
                             decay_constant = math.log(2) / half_life
                             decay_during_frame = decay_constant * frame_duration
                             avg_count_rate_frame = 1 / (decay_constant * math.log(decay_during_frame / (1 - math.exp(-decay_during_frame))))
                             scan_datetime = acquisition_datetime - frame_datetime + avg_count_rate_frame 
                    except:        
                     
                             raise Exception('cannot perform SUV conversion: series date/time is after acquisition date/time and frame reference time and/or actual frame duration <= 0')
                
            try:    
                
                start_datetime = datetime.strptime(dicom_header.RadiopharmaceuticalInformationSequence[0].RadiopharmaceuticalStartDateTime.split('.')[0],  '%Y%m%d%H%M%S')
                
            except:
                
                start_time = dicom_header.RadiopharmaceuticalInformationSequence[0].RadiopharmaceuticalStartTime.split('.')[0]
                start_datetime = datetime.strptime(series_date + start_time.split('.')[0],  '%Y%m%d%H%M%S')
                
            decay_datetime = scan_datetime - start_datetime # decay time in datetime duration
            decay_time = decay_datetime.seconds  #convert decay time to seconds
            injected_dose = dicom_header.RadiopharmaceuticalInformationSequence[0].RadionuclideTotalDose #in Bq
            decayed_dose = injected_dose * 2 ** (-decay_time / half_life)
            weight = dicom_header.PatientWeight #in kg
            SUV_image = img * (weight * 1000 / decayed_dose)
            
        elif dicom_header.Units == 'CNTS':
            #have not encountered data that fit this criteria, so have not valiated this section
            #if input fits this criteria, an exception will be raised
            
            try:
                
                SUV_image = img * dicom_header[0x7053, 0x1000].value
                
            except:
                    
                try:
                    
                    #bqml_image = slope * dicom_header[0x7053, 0x1009].value
                    dicom_header.Units = 'BQML'
                    dicom_header.pixel_array = dicom_header[0x7053, 0x1009].value
                    convert_to_SUV(dicom_header)   
                    
                except:
                    
                    raise Exception('cannot perform SUV conversion: units="CNTS" and dicom tags (0x7053, 0x1000) and (0x7053, 0x1009) are not present')
        
        elif dicom_header.Units == 'GML':
            
            SUV_image = img
        return SUV_image

# example usage:
series_path = 'path/to/PET/dicoms'

for entry in os.scandir(series_path):
    if entry.path[-4:]=='.dcm':
        dicom_header = pydicom.read_file(entry.path, force=True)
        suv_img = convert_to_SUV(dicom_header)
        #additional code here