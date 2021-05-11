# vendor_neutral_SUV_calculation

DICOM_SUV_calculation_technical_note.pdf: This technical note has not yet been published but lays out the complexities of SUV calculation.

vendor_neutral_suv.py: This is a vendor-neutral SUV calculation function which takes the dicom header object produced by pydicom.read_file() as input. The function outputs SUV if it can be calculated otherwise an exception detailing why calculation is not possible will be raised.

This function is based on QIBA’s vendor-neutral pseudo-code for SUV calculation found here: https://qibawiki.rsna.org/index.php/Standardized_Uptake_Value_(SUV)

In testing, images with units=CNTS and images with series date/time>acquisition date/time were not encountered, so sections of the code which deal with these conditions could not be tested.

This function has been tested with 9 PET series from Siemens, Phillips, and GE scanners, as well as a digital reference object (http://depts.washington.edu/petctdro/DROsuv_main.html ref: L. A. Pierce, B. F. Elston, D. A. Clunie, D. Nelson, and P. E. Kinahan, “A Digital Reference Object to Analyze Calculation Accuracy of PET Standardized Uptake Value.,” Radiology, p. 141262, May 2015.)
