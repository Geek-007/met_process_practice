#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 yangkang <yangkang@gagogroup.com>. All rights reserved.
from osgeo import gdal
from osgeo import osr
import numpy as np
import glob
import os
import re

class Mosaic():

    def __init__(self):
        # 经纬最大范围
        self.Xmin = -180.0
        self.Xmax = 180.0
        self.Ymin = -90.0
        self.Ymax = 90.0
        # 等级:0-15
        self.TILEMATRIX = 0
        # 初始这个切片的左下经纬
        self.minLeft = 0
        self.minBottom = 0

        self.longAdd = 0
        self.latAdd = 0
        # 初始这个切片的行列
        self.Col = 0
        self.Row = 0

    def array2raster(self, newRasterfn, rasterOrigin, pixelWidth, pixelHeight, reversed_1, reversed_2, reversed_3):

        cols = reversed_1.shape[1]
        rows = reversed_1.shape[0]
        originX = rasterOrigin[0]
        originY = rasterOrigin[1]

        driver = gdal.GetDriverByName('GTiff')
        outRaster = driver.Create(newRasterfn, cols, rows, 3, gdal.GDT_Byte)
        outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
        outband = outRaster.GetRasterBand(1)
        outband.WriteArray(reversed_1)
        outband2 = outRaster.GetRasterBand(2)
        outband2.WriteArray(reversed_2)
        outband3 = outRaster.GetRasterBand(3)
        outband3.WriteArray(reversed_3)
        outRasterSRS = osr.SpatialReference()
        outRasterSRS.ImportFromEPSG(4326)
        outRaster.SetProjection(outRasterSRS.ExportToWkt())
        outband.FlushCache()

    # 行列转化为经纬度
    def change(self):
        power = 2 ** (self.TILEMATRIX + 1)
        self.longAdd = (self.Xmax - self.Xmin) / power
        self.minLeft = self.longAdd * self.Col + self.Xmin

        power = 2 ** self.TILEMATRIX
        self.latAdd = (self.Ymax - self.Ymin) / power
        self.minBottom = self.Ymax - self.latAdd * self.Row


    def run(self, newRasterfn, file):
        file_name = os.path.basename(file)
        tmp = re.findall("\d+", file_name)
        # print(tmp)
        self.Col = int(tmp[0])
        self.Row = int(tmp[1])
        self.TILEMATRIX = int(tmp[2])
        self.change()

        rasterOrigin = (self.minLeft, self.minBottom)
        dataset = gdal.Open(file,gdal.GA_ReadOnly)
        band1 = dataset.GetRasterBand(1).ReadAsArray()
        band2 = dataset.GetRasterBand(2).ReadAsArray()
        band3 = dataset.GetRasterBand(3).ReadAsArray()
        # reversed_1 = band1[::-1] # reverse array so the tif looks like the array
        # reversed_2 = band2[::-1]
        # reversed_3 = band3[::-1]
        self.array2raster(newRasterfn, rasterOrigin, self.longAdd, -self.latAdd, band1, band2, band3) # convert array to raster


if __name__ == "__main__":
    files=glob.glob("./map_png/*.png")
    for file in files:
        file_name=os.path.basename(file)
        newRasterfn = './map_tiff/'+file_name[:-4]+'.tiff'
        print('convert %s to tiff '% file_name)
        mosaic = Mosaic()
        mosaic.run(newRasterfn,file)