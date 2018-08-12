#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 yangkang <yangkang@gagogroup.com>. All rights reserved.
import glob
import os

import requests
from .gdalmerge import main
from osgeo import gdal
from osgeo import osr
from .tifftiler import GlobalMercator


class ImageTiler(object):
    @classmethod
    def base_map_tile(cls, input_path, tile_path, min_level, max_level):

        if not os.path.exists(tile_path):
            os.makedirs(tile_path)
        files = glob.glob('%s/*tiff' % input_path)
        for tiff_file in files:
            file_name = os.path.splitext(os.path.basename(tiff_file))[0]
            file_int16 = os.path.join(input_path, (file_name + '_int16.tiff'))
            os.system('gdal_translate -ot int16 %s %s' % (tiff_file, file_int16))
            os.remove(tiff_file)
            file_nodata = os.path.join(input_path, (file_name + '_-99.tiff'))
            band1, band2, band3 = cls.get_no_data(file_int16)
            os.system('gdalwarp -srcnodata "%s %s %s" -dstnodata "-99 -99 -99" %s %s' %
                      (band1, band2, band3, file_int16, file_nodata))
            os.remove(file_int16)
            file_stretch = os.path.join(input_path, (file_name + '_stretch.tiff'))
            min_band1, max_band1, min_band2, max_band2, min_band3, max_band3 = \
                cls.get_stretch_min_max(file_nodata)
            os.system('gdal_translate -ot Byte -of Gtiff -a_nodata 0 \
                      -scale_1 %s %s 1 255 \
                      -scale_2 %s %s 1 255 \
                      -scale_3 %s %s 1 255 \
                      %s %s ' % (min_band1, max_band1, min_band2, max_band2,
                                 min_band3, max_band3, file_nodata, file_stretch))
            os.remove(file_nodata)
            os.system('rm %s/*.xml' % input_path)
        vrt_file = os.path.join(input_path, ('basemap.vrt'))
        os.system('gdalbuildvrt -srcnodata 0 %s %s/*stretch.tiff' % (vrt_file, input_path))
        os.system(' gdal2tiles.py -a 0 -z "%s-%s" %s %s' % (min_level, max_level, vrt_file, tile_path))
        # TiffTiler.tile_single_tiff(vrt_file, min_level, max_level, tile_path)

    @classmethod
    def get_no_data(cls, file):
        data_set = gdal.Open(file, gdal.GA_ReadOnly)
        nodatas = []
        for i in range(data_set.RasterCount):
            matrix = data_set.GetRasterBand(i + 1).ReadAsArray()
            nodatas.append(matrix[0][0])
        return nodatas

    @classmethod
    def get_stretch_min_max(cls, file):

        hdata_set = gdal.Open(file, gdal.GA_ReadOnly)
        band_min_max = []
        for iBand in range(hdata_set.RasterCount):
            hBand = hdata_set.GetRasterBand(iBand + 1)

            offset = hBand.GetOffset()
            if offset is None:
                offset = 0.0
            scale = hBand.GetScale()
            if scale is None:
                scale = 1.0

            dfMin, dfMax = hBand.GetMinimum(), hBand.GetMaximum()
            if dfMin is not None:
                dfMin = (dfMin * scale) + offset
            if dfMax is not None:
                dfMax = (dfMax * scale) + offset
            # stats = hBand.GetStatistics(bApproxStats, bStats)
            hist = hBand.GetDefaultHistogram(force=True)
            cnt = 0
            sum = 0
            sumTotal = 0
            if hist is not None:
                # use dfMin and dfMax from previous calls when possible
                if dfMin is None:
                    dfMin = (hist[0] * scale) + offset
                if dfMax is None:
                    dfMax = (hist[1] * scale) + offset
                nBucketCount = hist[2]
                panHistogram = hist[3]
            increment = round(((dfMax - dfMin) / nBucketCount), 2)
            value = dfMin
            for bucket in panHistogram:
                sumTotal = sumTotal + bucket

            hist_stats = {}
            for bucket in panHistogram:
                sum = sum + bucket
                # normalize cumlative
                nsum = sum / float(sumTotal)
                # ine = "%d\t%0.2f\t%d\t%0.6f" % (cnt, value, bucket, nsum)
                hist_stats[nsum] = value
                cnt = cnt + 1
                value = value + increment

            min_result = int(hist_stats[cls.find_closet(hist_stats.keys(), 0.02)])
            max_result = int(hist_stats[cls.find_closet(hist_stats.keys(), 0.98)])

            band_min_max.append(min_result)
            band_min_max.append(max_result)
        return band_min_max

    @classmethod
    def find_closet(cls, datalist, value):

        gap = 1
        for data in datalist:
            d_value = abs(data - value)
            if d_value < gap:
                gap = d_value
                result = data
        return result


class GetGoogleMap(object):
    """

    """

    def __init__(self):
        self.global_mercator = GlobalMercator()

    @staticmethod
    def get_tile(email,min_level,max_level,lon_min,lon_max,lat_min,lat_max):

        payload = {
            'email': email,
            'minLevel': min_level,
            'maxLevel': max_level,
            'lonMin': lon_min,
            'lonMax':  lon_max,
            'latMin': lat_min,
            'latMax': lat_max
        }
        r = requests.post("http://139.219.239.252/job/tiff", json=payload)
        print(r.text)

    def get_merge_tiff(self, input_path, out_path):

        array_list = []
        for root, dirs, files in os.walk(input_path):
            for f in files:
                array_list.append(os.path.join(root, f))

        if not os.path.exists('%s/tmp' % input_path):
            os.mkdir('%s/tmp' % input_path)
        tmp_path = '%s/tmp' % input_path

        print('convert array to tiff...')
        del array_list[0]
        del array_list[0]
        for file in array_list:
            out_file = os.path.join(tmp_path, os.path.basename(file))
            if os.stat(file).st_size != 0:
                self.array_to_tiff(file, out_file)

        print('merge file .....')
        self.merge_tiff(tmp_path, out_path)

    def array_to_tiff(self, file, tiff_file):

        tmp_file = os.path.splitext(file)[0]
        tx = int(tmp_file.split('/')[-2])
        ty = int(tmp_file.split('/')[-1])
        zoom = int(tmp_file.split('/')[-3])
        ty = (2 ** zoom - 1) - ty

        bounds = self.global_mercator.TileBounds(tx, ty, zoom)
        origin_x = bounds[0]
        origin_y = bounds[3]
        pixel_width = self.global_mercator.Resolution(zoom)
        pixel_height = -self.global_mercator.Resolution(zoom)
        data_set = gdal.Open(file, gdal.GA_ReadOnly)
        band1 = data_set.GetRasterBand(1).ReadAsArray()
        band2 = data_set.GetRasterBand(2).ReadAsArray()
        band3 = data_set.GetRasterBand(3).ReadAsArray()
        cols = band1.shape[1]
        rows = band1.shape[0]

        tmp_tiff = os.path.splitext(tiff_file)[0] + '_tmp.tiff'
        driver = gdal.GetDriverByName('GTiff')
        out_raster = driver.Create(tmp_tiff, cols, rows, 3, gdal.GDT_Byte)
        out_raster.SetGeoTransform((origin_x, pixel_width, 0, origin_y, 0, pixel_height))
        out_band = out_raster.GetRasterBand(1)
        out_band.WriteArray(band1)
        out_band2 = out_raster.GetRasterBand(2)
        out_band2.WriteArray(band2)
        out_band3 = out_raster.GetRasterBand(3)
        out_band3.WriteArray(band3)
        out_raster_srs = osr.SpatialReference()
        out_raster_srs.ImportFromEPSG(3857)
        out_raster.SetProjection(out_raster_srs.ExportToWkt())
        out_band.FlushCache()

    @staticmethod
    def merge_tiff(input_path, out_path):
        files = glob.glob('%s/*.tiff' % input_path)
        for file in files:
            outfile = os.path.join(out_path, os.path.basename(file))
            os.system("gdalwarp -t_srs EPSG:4326 %s %s" % (file, outfile))
        merge_files = glob.glob('%s/*.tiff' % out_path)
        parameter_list = []
        parameter_list.append(os.path.join(os.getcwd(), 'gdalmerge.py'))
        parameter_list.append('-o')
        parameter_list.append('%s/fina.tiff'%out_path)
        parameter_list.extend(merge_files)
        main(parameter_list)
