#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 yangkang <yangkang@gagogroup.com>. All rights reserved.
import glob
import json
import os
import shutil
import struct
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict

import numpy as np
from osgeo import gdal, osr

calibration_param = {
    'GF1':
        {'PMS1':
             {'2013': {'PAN': {'gain': 0.1886, 'offset': -13.127},
                       'Band1': {'gain': 0.2082, 'offset': 4.6186},
                       'Band2': {'gain': 0.1672, 'offset': 4.8768},
                       'Band3': {'gain': 0.1748, 'offset': 4.8924},
                       'Band4': {'gain': 0.1883, 'offset': -9.4771}},
              '2014': {'PAN': {'gain': 0.1963, 'offset': 0.0000},
                       'Band1': {'gain': 0.2247, 'offset': 0.0000},
                       'Band2': {'gain': 0.1892, 'offset': 0.0000},
                       'Band3': {'gain': 0.1889, 'offset': 0.0000},
                       'Band4': {'gain': 0.1939, 'offset': 0.0000}},
              '2015': {'PAN': {'gain': 0.1956, 'offset': 0.0000},
                       'Band1': {'gain': 0.2110, 'offset': 0.0000},
                       'Band2': {'gain': 0.1802, 'offset': 0.0000},
                       'Band3': {'gain': 0.1806, 'offset': 0.0000},
                       'Band4': {'gain': 0.1870, 'offset': 0.0000}},
              '2016': {'PAN': {'gain': 0.1982, 'offset': 0.0000},
                       'Band1': {'gain': 0.2320, 'offset': 0.0000},
                       'Band2': {'gain': 0.1870, 'offset': 0.0000},
                       'Band3': {'gain': 0.1795, 'offset': 0.0000},
                       'Band4': {'gain': 0.1960, 'offset': 0.0000}}},
         'PMS2':
             {'2013': {'PAN': {'gain': 0.1878, 'offset': -7.9371},
                       'Band1': {'gain': 0.2072, 'offset': 7.5348},
                       'Band2': {'gain': 0.1776, 'offset': 3.9395},
                       'Band3': {'gain': 0.1770, 'offset': -1.7445},
                       'Band4': {'gain': 0.1909, 'offset': -7.2053}},
              '2014': {'PAN': {'gain': 0.2147, 'offset': 0.0000},
                       'Band1': {'gain': 0.2419, 'offset': 0.0000},
                       'Band2': {'gain': 0.2047, 'offset': 0.0000},
                       'Band3': {'gain': 0.2009, 'offset': 0.0000},
                       'Band4': {'gain': 0.2058, 'offset': 0.0000}},
              '2015': {'PAN': {'gain': 0.2018, 'offset': 0.0000},
                       'Band1': {'gain': 0.2242, 'offset': 0.0000},
                       'Band2': {'gain': 0.1887, 'offset': 0.0000},
                       'Band3': {'gain': 0.1882, 'offset': 0.0000},
                       'Band4': {'gain': 0.1963, 'offset': 0.0000}},
              '2016': {'PAN': {'gain': 0.1979, 'offset': 0.0000},
                       'Band1': {'gain': 0.2240, 'offset': 0.0000},
                       'Band2': {'gain': 0.1851, 'offset': 0.0000},
                       'Band3': {'gain': 0.1793, 'offset': 0.0000},
                       'Band4': {'gain': 0.1863, 'offset': 0.0000}}},
         'WFV1':
             {'2013': {'Band1': {'gain': 0.1709, 'offset': -0.0007},
                       'Band2': {'gain': 0.1398, 'offset': -0.0007},
                       'Band3': {'gain': 0.1195, 'offset': -0.0004},
                       'Band4': {'gain': 0.1338, 'offset': -0.0037}},
              '2014': {'Band1': {'gain': 0.2004, 'offset': 0.0000},
                       'Band2': {'gain': 0.1648, 'offset': 0.0000},
                       'Band3': {'gain': 0.1243, 'offset': 0.0000},
                       'Band4': {'gain': 0.1563, 'offset': 0.0000}},
              '2015': {'Band1': {'gain': 0.1816, 'offset': 0.0000},
                       'Band2': {'gain': 0.1560, 'offset': 0.0000},
                       'Band3': {'gain': 0.1412, 'offset': 0.0000},
                       'Band4': {'gain': 0.1368, 'offset': 0.0000}},
              '2016': {'Band1': {'gain': 0.1843, 'offset': 0.0000},
                       'Band2': {'gain': 0.1477, 'offset': 0.0000},
                       'Band3': {'gain': 0.1220, 'offset': 0.0000},
                       'Band4': {'gain': 0.1365, 'offset': 0.0000}}},
         'WFV2':
             {'2013': {'Band1': {'gain': 0.1663, 'offset': -0.0021},
                       'Band2': {'gain': 0.1466, 'offset': -0.0028},
                       'Band3': {'gain': 0.1058, 'offset': -0.0045},
                       'Band4': {'gain': 0.1112, 'offset': -0.0001}},
              '2014': {'Band1': {'gain': 0.1733, 'offset': 0.0000},
                       'Band2': {'gain': 0.1383, 'offset': 0.0000},
                       'Band3': {'gain': 0.1122, 'offset': 0.0000},
                       'Band4': {'gain': 0.1391, 'offset': 0.000}},
              '2015': {'Band1': {'gain': 0.1684, 'offset': 0.0000},
                       'Band2': {'gain': 0.1527, 'offset': 0.0000},
                       'Band3': {'gain': 0.1373, 'offset': 0.0000},
                       'Band4': {'gain': 0.1263, 'offset': 0.0000}},
              '2016': {'Band1': {'gain': 0.1929, 'offset': 0.0000},
                       'Band2': {'gain': 0.1540, 'offset': 0.0000},
                       'Band3': {'gain': 0.1349, 'offset': 0.0000},
                       'Band4': {'gain': 0.1359, 'offset': 0.0000}}},
         'WFV3':
             {'2013': {'Band1': {'gain': 0.1718, 'offset': -0.0012},
                       'Band2': {'gain': 0.1603, 'offset': -0.0053},
                       'Band3': {'gain': 0.1427, 'offset': -0.0032},
                       'Band4': {'gain': 0.1297, 'offset': -0.0015}},
              '2014': {'Band1': {'gain': 0.1745, 'offset': 0.0000},
                       'Band2': {'gain': 0.1514, 'offset': 0.0000},
                       'Band3': {'gain': 0.1257, 'offset': 0.0000},
                       'Band4': {'gain': 0.1462, 'offset': 0.0000}},
              '2015': {'Band1': {'gain': 0.1770, 'offset': 0.0000},
                       'Band2': {'gain': 0.1589, 'offset': 0.0000},
                       'Band3': {'gain': 0.1385, 'offset': 0.0000},
                       'Band4': {'gain': 0.1344, 'offset': 0.0000}},
              '2016': {'Band1': {'gain': 0.1753, 'offset': 0.0000},
                       'Band2': {'gain': 0.1565, 'offset': 0.0000},
                       'Band3': {'gain': 0.1480, 'offset': 0.0000},
                       'Band4': {'gain': 0.1322, 'offset': 0.0000}}},
         'WFV4':
             {'2013': {'Band1': {'gain': 0.1869, 'offset': -0.0069},
                       'Band2': {'gain': 0.1604, 'offset': -0.0038},
                       'Band3': {'gain': 0.1430, 'offset': -0.0031},
                       'Band4': {'gain': 0.1340, 'offset': -0.0007}},
              '2014': {'Band1': {'gain': 0.1713, 'offset': 0.0000},
                       'Band2': {'gain': 0.1600, 'offset': 0.0000},
                       'Band3': {'gain': 0.1497, 'offset': 0.0000},
                       'Band4': {'gain': 0.1435, 'offset': 0.0000}},
              '2015': {'Band1': {'gain': 0.1886, 'offset': 0.0000},
                       'Band2': {'gain': 0.1645, 'offset': 0.0000},
                       'Band3': {'gain': 0.1467, 'offset': 0.0000},
                       'Band4': {'gain': 0.1378, 'offset': 0.0000}},
              '2016': {'Band1': {'gain': 0.1973, 'offset': 0.0000},
                       'Band2': {'gain': 0.1714, 'offset': 0.0000},
                       'Band3': {'gain': 0.1500, 'offset': 0.0000},
                       'Band4': {'gain': 0.1572, 'offset': 0.0000}}}
         },

    'GF2':
        {'PMS1':
             {'2014': {'PAN': {'gain': 0.1630, 'offset': -0.6077},
                       'Band1': {'gain': 0.1585, 'offset': -0.8765},
                       'Band2': {'gain': 0.1883, 'offset': -0.9742},
                       'Band3': {'gain': 0.1740, 'offset': -0.7652},
                       'Band4': {'gain': 0.1897, 'offset': -0.7233}},
              '2015': {'PAN': {'gain': 0.1538, 'offset': 0.0000},
                       'Band1': {'gain': 0.1457, 'offset': 0.0000},
                       'Band2': {'gain': 0.1604, 'offset': 0.0000},
                       'Band3': {'gain': 0.1550, 'offset': 0.0000},
                       'Band4': {'gain': 0.1731, 'offset': 0.0000}},
              '2016': {'PAN': {'gain': 0.1501, 'offset': 0.0000},
                       'Band1': {'gain': 0.1322, 'offset': 0.0000},
                       'Band2': {'gain': 0.1550, 'offset': 0.0000},
                       'Band3': {'gain': 0.1477, 'offset': 0.0000},
                       'Band4': {'gain': 0.1613, 'offset': 0.0000}}
              },
         'PMS2':
             {'2014': {'PAN': {'gain': 0.1823, 'offset': 0.1654},
                       'Band1': {'gain': 0.1748, 'offset': -0.5930},
                       'Band2': {'gain': 0.1817, 'offset': -0.2717},
                       'Band3': {'gain': 0.1741, 'offset': -0.2879},
                       'Band4': {'gain': 0.1975, 'offset': -0.2773}},
              '2015': {'PAN': {'gain': 0.1823, 'offset': 0.0000},
                       'Band1': {'gain': 0.1761, 'offset': 0.0000},
                       'Band2': {'gain': 0.1843, 'offset': 0.0000},
                       'Band3': {'gain': 0.1677, 'offset': 0.0000},
                       'Band4': {'gain': 0.1830, 'offset': 0.0000}},
              '2016': {'PAN': {'gain': 0.1863, 'offset': 0.0000},
                       'Band1': {'gain': 0.1762, 'offset': 0.0000},
                       'Band2': {'gain': 0.1856, 'offset': 0.0000},
                       'Band3': {'gain': 0.1754, 'offset': 0.0000},
                       'Band4': {'gain': 0.1980, 'offset': 0.0000}}}
         }
}

# Gdal定义的datatype与 python struct定义的datatype的对应关系
GDAL_DATATYPE_LUT = {
    "float32": "f",
    "float64": "d",
    "int16": "h",
    "uint16": "H",
    "int32": "i",
    "uint32": "I",
}


class GfManager(object):
    """
    高分影像预处理模块
    """

    @classmethod
    def tar_to_tiff(cls, path):
        """
        批量将tar.gz 文件进行解压，并进行粗校正，同时生成缩略图
        :param path: 高分tar.gz 所在文件夹路径
        :return: None
        """

        # 解压并进行粗校正
        indicator = 1.0
        paths = glob.glob("%s/*.tar.gz" % path)
        for file in paths:
            try:
                os.stat("%s/temp" % path)
            except:
                os.mkdir("%s/temp" % path)
            os.system("tar -zxvf " + file + " -C %s/temp" % path)
            tiff_files = glob.glob("%s/temp/*.tiff" % path)
            for tif_file in tiff_files:
                file_name = os.path.splitext(os.path.basename(tif_file))[0]
                outfile = file_name + '.tiff'
                # xml_file = file_name + ".xml"
                # os.system("mv %s/temp/%s %s/%s" % (path, xml_file, path, xml_file))
                os.system("gdalwarp -rpc -t_srs EPSG:4326 %s %s" %
                          (tif_file, '%s/%s' % (path, outfile)))
                os.system("rm %s/temp/%s.*" %
                          (path, os.path.split(tif_file)[1][:-5]))
            print("tar_to_tiff is processing %.f %%" % (indicator / len(paths) * 100))
            indicator += 1
        shutil.rmtree("%s/temp" % path)

        # 生成缩略图
        print("thumbnail file is processing")
        pan_tiff_files = glob.glob("%s/*PAN*.tiff" % path)
        for file in pan_tiff_files:
            cls.get_thumbnail(file)

    @classmethod
    def get_vrt_thumbnail(cls, path):
        """
        生成全部拼接的vrt缩略图
        :param path: 全色波段图像路径
        :return: None
        """
        pan_tiff_files = glob.glob("%s/*PAN*.tiff" % path)
        dataset = gdal.Open(pan_tiff_files[0], gdal.GA_ReadOnly)
        xsize, ysize = dataset.GetGeoTransform()[1] * 1000, -dataset.GetGeoTransform()
        vrt_file = os.path.join(path, ('fullmap.vrt'))
        os.system('gdalbuildvrt -srcnodata 0 %s %s/*PAN*.tiff' % (vrt_file, path))
        thumbnail_file = os.path.join(path, ('thumbnail.vrt'))
        os.system('gdal_translate -of PNG -tr %s %s %s %s' % (xsize, ysize, vrt_file, thumbnail_file))

    @classmethod
    def get_thumbnail(cls, file):
        """
        生成单个文件的缩略图
        :param file: 文件绝对路径
        :return: None
        """
        file_name = os.path.splitext(os.path.basename(file))[0]
        thumbnail_file = file_name + "_thumbnail.tiff"
        dataset = gdal.Open(file, gdal.GA_ReadOnly)
        xsize, ysize = dataset.GetGeoTransform()[1] * 1000, -dataset.GetGeoTransform()[5] * 1000
        os.system("gdalwarp -tr %s %s -dstnodata 0 %s %s" % (xsize, ysize, file, thumbnail_file))

    def calibrate(self, file, out_file):
        """
        高分影像辐射校正
        :param file: 待校正文件
        :param out_file:校正后文件
        :return:None
        """

        file_name = os.path.splitext(os.path.basename(file))[0]
        satellite = file_name.split('_')[0]
        sensor = file_name.split('_')[1]
        year = file_name.split('_')[4][:4]

        dataset = gdal.Open(file, gdal.GA_ReadOnly)
        driver = gdal.GetDriverByName('GTiff')
        geotransform = dataset.GetGeoTransform()
        xSize, ySize = dataset.RasterXSize, dataset.RasterYSize
        originX, originY = geotransform[0], geotransform[3]
        pixel_width, pixel_height = geotransform[1], geotransform[5]

        if dataset.RasterCount == 4:
            out_raster = driver.Create(out_file, xSize, ySize, 4, gdal.GDT_Int16)
            out_raster.SetGeoTransform((originX, pixel_width, 0, originY, 0, pixel_height))
            for i in range(4):
                band = dataset.GetRasterBand(i + 1).ReadAsArray()
                band_number = 'Band%s' % (i + 1)
                band = np.multiply(self.calibrate_specific_band(satellite, sensor, year, band_number, band), 1)
                out_band = out_raster.GetRasterBand(i + 1)
                out_band.WriteArray(band)
            outRasterSRS = osr.SpatialReference()
            outRasterSRS.ImportFromWkt(dataset.GetProjectionRef())
            out_raster.SetProjection(outRasterSRS.ExportToWkt())
            out_band.FlushCache()

        else:
            out_raster = driver.Create(out_file, xSize, ySize, 1, gdal.GDT_Int16)
            out_raster.SetGeoTransform((originX, pixel_width, 0, originY, 0, pixel_height))
            band = dataset.GetRasterBand(1).ReadAsArray()
            band_number = 'PAN'
            band = np.multiply(self.calibrate_specific_band(satellite, sensor, year, band_number, band), 1)
            out_band = out_raster.GetRasterBand(1)
            out_band.WriteArray(band)
            outRasterSRS = osr.SpatialReference()
            outRasterSRS.ImportFromWkt(dataset.GetProjectionRef())
            out_raster.SetProjection(outRasterSRS.ExportToWkt())
            out_band.FlushCache()

    def calibrate_specific_band(self, satellite, sensor, year, band_number, array):
        """
        对特定波段进行校正
        :param satellite: GF1，GF2
        :param sensor:传感器类型
        :param year:年
        :param band_number:波段👌
        :param array:待校正图像数组
        :return:校正后图像数组
        """
        year = list(calibration_param[satellite][sensor].keys())[self.index_min([abs(int(x) - int(year))
                                                                                 for x in calibration_param[satellite][
                                                                                     sensor].keys()])]
        print(calibration_param[satellite][sensor][year][band_number])
        return np.add(np.multiply(array, calibration_param[satellite][sensor][year][band_number]['gain']),
                      calibration_param[satellite][sensor][year][band_number]['offset'])

    @staticmethod
    def index_min(values):
        return min(range(len(values)), key=values.__getitem__)


class BIPManager(object):
    """
    读取BIP文件操作
    """

    def query_data_series_from_bip(self, local_bip_dir, hv, pixel_x, pixel_y, from_date, to_date):
        """

        :param local_bip_dir:
        :param hv:
        :param pixel_x:
        :param pixel_y:
        :param from_date:
        :param to_date:
        :return:
        """
        years = range(from_date.year, to_date.year + 1, 1)

        get_start_date = lambda year: from_date if year == from_date.year else datetime(
            year, 1, 1)
        get_end_date = lambda year: to_date if year == to_date.year else datetime(
            year, 12, 31)
        data_serise = {}
        for year in years:
            local_bip_path = os.path.join(local_bip_dir, 'NDVI.{0}.{1}.bip'.format(year, hv))
            data_serise.update(
                self.query_data_series_from_single_bip(local_bip_path, pixel_x, pixel_y, get_start_date(year),
                                                       get_end_date(year)))
        return data_serise

    def query_data_series_from_single_bip(self, local_bip_path, pixel_x, pixel_y,
                                          from_date, to_date):
        local_hdr_path = os.path.splitext(local_bip_path)[0] + '.hdr'

        with open(local_hdr_path, 'rb') as f:
            image_header = f.read()

        info = self.parse_bip_header(image_header)
        # geo_transform = info["geoTransform"]
        datatype = info["dataType"]
        data_type_length = info["itemSize"]
        x_size = info["xSize"]
        band = info["band"]
        pixel_offset = self.get_pixel_offset(x=pixel_x, y=pixel_y, x_size=x_size,
                                             band=len(band),
                                             data_type_length=data_type_length)

        valid_band = OrderedDict(sorted(
            (date, position) for date, position in band.items() if from_date <= date <= to_date))
        position_list = list(valid_band.values())
        date_list = list(valid_band.keys())
        start_position = position_list[0]
        end_position = position_list[-1]

        with open(local_bip_path, 'rb') as f:
            f.seek(pixel_offset + (start_position - 1) * data_type_length)
            buffer = f.read(
                data_type_length * (end_position - start_position + 1))
        value_list = self.get_pixel_value(buffer, datatype, data_type_length)
        date_series = {}
        for date, ndvi in zip(date_list, value_list):
            date_series[date] = ndvi
        return date_series
        # return [{"date": date.strftime('%Y-%m-%d'),
        #          "ndvi": ndvi} for date, ndvi in zip(date_list, value_list)]

    @classmethod
    def parse_bip_header(cls, bip_header: bytes) -> Dict:
        """
        头文件是一个json, 该方法用于解析从json文件中读取的bytes
        :param bip_header: 从json文件中读取的bytes
        :return: Dict
        """
        # if info['type'].lower() != 'BIP':
        #     raise TypeError("not a BIP file")
        # else:
        string = bip_header.decode('utf-8').replace('\'', '\"')
        data = json.loads(string)
        data["band"] = dict(
            (datetime.fromtimestamp(float(k)), int(v)) for k, v in data["band"].items())
        return data

    @staticmethod
    def get_pixel_offset(x: float, y: float, x_size: int, band: int, data_type_length: int) -> int:
        """
        获取给定坐标的点的偏移量
        :param x: 点在图像中的x坐标
        :param y: 点在图像中的y坐标
        :param x_size: 图像的列数
        :param band: 存储了多少个波段/时相
        :param data_type_length: 存储的数据类型的长度(多少位), 对应头文件中的itemSize字段
        :return: 偏移量
        """
        return band * data_type_length * (x + x_size * y)

    @classmethod
    def get_pixel_value(cls, buf: bytes, data_type: str, data_type_length: int) -> Any:
        """
        buffer转换为pixel value
        :param buf:
        :param data_type:
        :param data_type_length:
        :return:
        """
        value_list = []

        for byte_chunk in cls.chunks(buf, data_type_length):
            pixel_value, = struct.unpack(GDAL_DATATYPE_LUT[data_type.lower()], byte_chunk)
            value_list.append(pixel_value)

        return value_list

    @staticmethod
    def chunks(input_list: Any, chunk_length: int):
        """
        把input_list分为chunk_size份子list
        """
        for i in range(0, len(input_list), chunk_length):
            yield input_list[i:i + chunk_length]


