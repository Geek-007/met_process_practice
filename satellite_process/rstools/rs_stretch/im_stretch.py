'''
Image stretch
Usage:
    im_stretch.py <input_fname> <strech_modle> <output_fname> [--percent=<strech_percent>]
    im_stretch.py -h | --help
    The <input_fname> argument must be the path to a GeoTIFF image.
    The <strech_modle> argument must be one of the strech_modles 'max_min_strech' 'percent_strech' 'equalize_hist' 'equalize_adapthist'
    The <output_fname> argument must be a filename where the classification will be saved (GeoTIFF format).
    If [--percent=<strech_percent>] is given ,it mast be a  positive integer.such as if strech percent is 2%,then <strech_percent>=2
Options:
  -h --help  Show this screen.
  --percent=<strech_percent> strech percent.
'''
import os
import sys

import numpy as np
from osgeo import gdal
from skimage import exposure


def get_no_data(file):
    dataset = gdal.Open(file, gdal.GA_ReadOnly)
    nodatas = []
    for i in range(dataset.RasterCount):
        matrix = dataset.GetRasterBand(i + 1).ReadAsArray()
        nodatas.append(matrix[0][0])
    return nodatas


def get_mask(file):
    dataset = gdal.Open(file, gdal.GA_ReadOnly)
    matrix = dataset.GetRasterBand(1).ReadAsArray()
    mask = np.ones(matrix.shape)
    mask = np.where(matrix < 0, 0, mask)
    return mask


def get_band_min_max(file, mask, percent):
    band_min_max = []
    Dataset = gdal.Open(file, gdal.GA_ReadOnly)
    for i_band in range(Dataset.RasterCount):
        band = Dataset.GetRasterBand(i_band + 1).ReadAsArray()
        mask = np.array(mask, dtype=bool)
        band_flatten = band[mask]
        band_unique = np.unique(band_flatten)
        hist, bins = np.histogram(band_flatten, bins=band_unique)
        cdf = hist.cumsum()
        cdf_fre = cdf.astype('float64') / cdf[-1]
        # band_min_idx = np.argmin(np.abs(cdf_fre) - 0.02)
        # band_max_idx=np.argmin(np.abs(cdf_fre - 0.98))
        band_min_idx = np.argmin(np.abs(cdf_fre - percent / 100))
        band_max_idx = np.argmin(np.abs(cdf_fre - (1 - percent / 100)))

        band_min_max.append(band_unique[band_min_idx])
        band_min_max.append(band_unique[band_max_idx])
    return band_min_max


def write_geotiff(fname, band_r, band_g, band_b, geo_transform, projection, data_type=gdal.GDT_Byte):
    driver = gdal.GetDriverByName('GTiff')
    rows, cols = band_r.shape
    outRaster = driver.Create(fname, cols, rows, 3, data_type)
    outRaster.SetGeoTransform(geo_transform)
    outRaster.SetProjection(projection)
    outband1 = outRaster.GetRasterBand(1)
    outband1.WriteArray(band_r)
    outband2 = outRaster.GetRasterBand(2)
    outband2.WriteArray(band_g)
    outband3 = outRaster.GetRasterBand(3)
    outband3.WriteArray(band_b)
    outRaster = None  # Close the file
    return


def im_strech(input_fname, strech_modle, output_fname, strech_percent):
    input_path_splitext = os.path.splitext(input_fname)[0]
    file_int16 = input_path_splitext + '_int16.tiff'
    os.system('gdal_translate -ot int16 %s %s' % (input_fname, file_int16))
    file_nodata = input_path_splitext + '_nodata.tiff'
    band1_nodata, band2_nodata, band3_nodata = get_no_data(file_int16)
    os.system('gdalwarp -srcnodata "%s %s %s" -dstnodata "-99 -99 -99" %s %s' %
              (band1_nodata, band2_nodata, band3_nodata, file_int16, file_nodata))
    os.remove(file_int16)
    nodata_mask = get_mask(file_nodata)
    if strech_modle == 'max_min_strech':
        min_band1, max_band1, min_band2, max_band2, min_band3, max_band3 = \
            get_band_min_max(file_nodata, nodata_mask, 0)
        os.system('gdal_translate -ot Byte -of Gtiff -a_nodata 0 \
                                        -scale_1 %s %s 0 255 \
                                        -scale_2 %s %s 0 255 \
                                        -scale_3 %s %s 0 255 \
                                        %s %s ' % (min_band1, max_band1, min_band2, max_band2,
                                                   min_band3, max_band3, file_nodata, output_fname))
    elif strech_modle == 'percent_strech':
        min_band1, max_band1, min_band2, max_band2, min_band3, max_band3 = \
            get_band_min_max(file_nodata, nodata_mask, strech_percent)
        os.system('gdal_translate -ot Byte -of Gtiff -a_nodata 0 \
                                               -scale_1 %s %s 0 255 \
                                               -scale_2 %s %s 0 255 \
                                               -scale_3 %s %s 0 255 \
                                               %s %s ' % (min_band1, max_band1, min_band2, max_band2,
                                                          min_band3, max_band3, file_nodata, output_fname))
    elif strech_modle == 'equalize_hist':
        min_band1, max_band1, min_band2, max_band2, min_band3, max_band3 = \
            get_band_min_max(file_nodata, nodata_mask, strech_percent)
        file_strech = input_path_splitext + '_strech.tiff'
        os.system('gdal_translate -ot Byte -of Gtiff -a_nodata 0 \
                                                       -scale_1 %s %s 0 255 \
                                                       -scale_2 %s %s 0 255 \
                                                       -scale_3 %s %s 0 255 \
                                                       %s %s ' % (min_band1, max_band1, min_band2, max_band2,
                                                                  min_band3, max_band3, file_nodata, file_strech))

        nodata_mask = np.array(nodata_mask, dtype=bool)
        dataset = gdal.Open(file_strech, gdal.GA_ReadOnly)
        geo_transform = dataset.GetGeoTransform()
        proj = dataset.GetProjectionRef()

        band_r = dataset.GetRasterBand(1).ReadAsArray()
        band_r_equalize_hist = exposure.equalize_hist(band_r, mask=nodata_mask)
        band_g = dataset.GetRasterBand(2).ReadAsArray()
        band_g_equalize_hist = exposure.equalize_hist(band_g, mask=nodata_mask)
        band_b = dataset.GetRasterBand(3).ReadAsArray()
        band_b_equalize_hist = exposure.equalize_hist(band_b, mask=nodata_mask)

        write_geotiff(output_fname, band_r_equalize_hist, band_g_equalize_hist, band_b_equalize_hist, geo_transform,
                      proj)
    elif strech_modle == 'equalize_adapthist':
        min_band1, max_band1, min_band2, max_band2, min_band3, max_band3 = \
            get_band_min_max(file_nodata, nodata_mask, strech_percent)
        file_strech = input_path_splitext + '_strech.tiff'
        os.system('gdal_translate -ot Byte -of Gtiff -a_nodata 0 \
                                                       -scale_1 %s %s 0 255 \
                                                       -scale_2 %s %s 0 255 \
                                                       -scale_3 %s %s 0 255 \
                                                       %s %s ' % (min_band1, max_band1, min_band2, max_band2,
                                                                  min_band3, max_band3, file_nodata, file_strech))

        dataset = gdal.Open(file_strech, gdal.GA_ReadOnly)
        geo_transform = dataset.GetGeoTransform()
        proj = dataset.GetProjectionRef()

        band_r = dataset.GetRasterBand(1).ReadAsArray()
        band_r_equalize_adapthist = exposure.equalize_adapthist(band_r)
        band_g = dataset.GetRasterBand(2).ReadAsArray()
        band_g_equalize_adapthist = exposure.equalize_adapthist(band_g)
        band_b = dataset.GetRasterBand(3).ReadAsArray()
        band_b_equalize_adapthist = exposure.equalize_adapthist(band_b)
        band_r_equalize_adapthist = (band_r_equalize_adapthist * 255).astype(np.uint8)
        band_g_equalize_adapthist = (band_g_equalize_adapthist * 255).astype(np.uint8)
        band_b_equalize_adapthist = (band_b_equalize_adapthist * 255).astype(np.uint8)
        write_geotiff(output_fname, band_r_equalize_adapthist, band_g_equalize_adapthist, band_b_equalize_adapthist,
                      geo_transform,
                      proj)


def main():
    input_fname = sys.argv[1]
    strech_modle = sys.argv[2]
    output_fname = sys.argv[3]
    if len(sys.argv) == 4:
        strech_percent = 0
    else:
        strech_percent = float(sys.argv[4])

    # opts=docopt(__doc__)
    # print(opts)
    # input_fname=opts["<input_fname>"]
    # strech_modle=opts["<strech_modle>"]
    # output_fname=opts["output_fname"]
    # strech_percent=opts['-- percent'] if opts['-- percent'] else 0

    # path = "/home/hlx/re1.tiff"
    im_strech(input_fname, strech_modle, output_fname, strech_percent)


if __name__ == "__main__":
    main()
