#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 yangkang <yangkang@gagogroup.com>. All rights reserved.
import gc
import os
import sys
import warnings as warn

import numpy as np
from osgeo import gdal, gdalconst

gdalRetileLocation = 'gdal_retile.py'
gdalMergeLocation = 'gdal_merge.py'
pythonLocation = ''


def resampleBicubic(srcImageFilename, sourceds, matchds, outname, interpmethod):
    '''
    function resampleBicubic(srcImageFilename, sourceds, matchds, outname):
    This function produces a resampled, bicubic, 4-band multispectral Geotiff
    image file. There are four input arguments. The first is the name of the
    panchromatic (1-band, high-resolution) Geotiff image file. The second
    and third input arguments are the GDAL objects produced by (for example)
    sourceds = gdal.Open(multifname.tif) and matchds = gdal.Open(panfname.tif).
    The last argument is the output name (string). When this function is
    called, it produces the resampled, 4-band (RGB,NIR) multispectral
    Geotiff image file.

    @author: Gerasimos Michalitsianos
    Science Systems and Applications, Inc.
    June 2015

    '''

    srcProjection = sourceds.GetProjection()
    srcGeotransform = sourceds.GetGeoTransform()
    matchProjection = matchds.GetProjection()
    matchGeotransform = matchds.GetGeoTransform()
    ncols = matchds.RasterXSize
    nrows = matchds.RasterYSize
    dst_fn = outname

    if not os.path.exists(outname):
        dst_ds = gdal.GetDriverByName('GTiff').Create(dst_fn, ncols, nrows, 4, gdalconst.GDT_Float32)
        dst_ds.SetGeoTransform(matchGeotransform)
        dst_ds.SetProjection(matchProjection)
        gdal.ReprojectImage(sourceds, dst_ds, srcProjection, matchProjection, interpmethod)
        dst_ds = None
        del dst_ds
    return dst_fn


def writeImg(imgs, outname, dspan):
    '''
    function writeImg(imgs,outname,dspan):
    This function writes out a 4-band Geotiff image.
    The 4 Numpy arrays should be stored in the list
    'imgs', an outname string should be provided, and
    the GDAL object dspan = gdal.Open(panfname.tif)
    should also be provided, to extract map information.

    @author: Gerasimos Michalitsianos
    Science Systems and Applications, Inc.
    June 2015
    '''

    if os.path.exists(outname):
        os.remove(outname)
    else:
        nrows, ncols = imgs[0].shape
        driv = gdal.GetDriverByName('GTiff')
        dst = driv.Create(outname, ncols, nrows, 3, gdal.GDT_Int16)

        dst.SetGeoTransform(dspan.GetGeoTransform())
        dst.SetProjection(dspan.GetProjection())
        dst.GetRasterBand(1).WriteArray(imgs[2])
        dst.GetRasterBand(2).WriteArray(imgs[1])
        dst.GetRasterBand(3).WriteArray(imgs[0])
        # dst.GetRasterBand(4).WriteArray(imgs[3])
        dst = None
        del dst


def broveySharpen(dsmulti, dspan):
    '''
    function broveySharpen(dsmulti,dspan):
    This function returns a list holding 4 pan-sharpened
    images (Numpy arrays): the red, green, blue, and NIR
    bands. The Brovey pan-sharpening technique is used here
    to pansharpen the Numpy arrays. The gdal objects
    (dsmulti=gdal.Open(multifname.tif, dspan = gdal.Open(panfname.tif)
    should both be provided, so the arrays can be extracted.

    @author: Gerasimos Michalitsianos
    Science Systems and Applications, Inc.
    June 2015

    '''

    try:

        with warn.catch_warnings():
            warn.filterwarnings('ignore', category=RuntimeWarning)

            pan = dspan.GetRasterBand(1).ReadAsArray().astype(float)
            red = dsmulti.GetRasterBand(3).ReadAsArray()
            green = dsmulti.GetRasterBand(2).ReadAsArray()
            blue = dsmulti.GetRasterBand(1).ReadAsArray()
            nir = dsmulti.GetRasterBand(4).ReadAsArray()

            redsharp = np.multiply(np.true_divide(red, red + green + blue + nir), pan)
            greensharp = np.multiply(np.true_divide(green, red + green + blue + nir), pan)
            bluesharp = np.multiply(np.true_divide(blue, red + green + blue + nir), pan)
            nirsharp = np.multiply(np.true_divide(nir, red + green + blue + nir), pan)

            return [redsharp, greensharp, bluesharp, nirsharp]

    except:
        return [None, None, None, None]


def fihsSharpen(dsmulti, dspan):
    '''
    function fihsSharpen(dsmulti,dspan):
    This function returns a list holding 4 pan-sharpened
    images (Numpy arrays): the red, green, blue, and NIR
    bands. The FIHS pan-sharpening technique is used here
    to pansharpen the Numpy arrays. The gdal objects
    (dsmulti=gdal.Open(multifname.tif, dspan = gdal.Open(panfname.tif)
    should both be provided, so the arrays can be extracted.

    @author: Gerasimos Michalitsianos
    Science Systems and Applications, Inc.
    June 2015

    '''

    try:

        with warn.catch_warnings():
            warn.filterwarnings('ignore', category=RuntimeWarning)

            pan = dspan.GetRasterBand(1).ReadAsArray().astype(float)
            red = dsmulti.GetRasterBand(3).ReadAsArray()
            green = dsmulti.GetRasterBand(2).ReadAsArray()
            blue = dsmulti.GetRasterBand(1).ReadAsArray()
            nir = dsmulti.GetRasterBand(4).ReadAsArray()

            L = (red + green + blue + nir) / float(4)
            redsharp = red + (pan - L)
            greensharp = green + (pan - L)
            bluesharp = blue + (pan - L)
            nirsharp = nir + (pan - L)

            return [redsharp, greensharp, bluesharp, nirsharp]

    except:
        return [None, None, None, None]


def Brovey(panfname, multifname, out_path):
    dspan = gdal.Open(panfname)
    dsmulti = gdal.Open(multifname)

    if dspan.RasterCount != 1:
        print('First command line input argument (panchromatic geotiff image file) should have 1 band.')
        sys.exit()

    if dsmulti.RasterCount != 4:
        print('Second command line input argument (multispectral geotiff image file) should have 4 bands (RGB,NIR)')
        sys.exit()
    resampledMultifname = os.path.join(out_path, os.path.basename(multifname).replace('.tif', '_Resampled.tif'))
    # resampledMultifname = multifname.replace('.tif', '_Resampled.tif')
    resampledMultifname = resampleBicubic(multifname, dsmulti, dspan, resampledMultifname, gdalconst.GRA_Cubic)
    if not os.path.isfile(resampledMultifname):
        print('Failure to resample multispectral file: ')
        print(multifname)
        sys.exit()
    if ('None' not in str(type(dspan))) and ('None' not in str(type(dsmulti))):
        fulloutnamebrovey = resampledMultifname.replace('_Resampled.tif', '_panSharpenedBrovey.tif')
        if not os.path.exists(fulloutnamebrovey):
            # ---- tile up huge, resampled multispectral file
            dim = 4.0
            nrows, ncols = dsmulti.RasterYSize, dsmulti.RasterXSize
            xtiledim, ytiledim = int(ncols / dim), int(nrows / dim)  #
            # ---- create a tile command and then subsequently run it, tiles go to directory as pan/MS
            targetDirectory = os.path.dirname(panfname)
            tileslistName = os.path.join(targetDirectory, 'multispectralTiles.csv')
            tileslistNamePan = os.path.join(targetDirectory, 'panchromaticTiles.csv')

            tilecmd = pythonLocation + gdalRetileLocation + ' -ps ' + str(xtiledim) + ' ' + \
                      str(ytiledim) + ' -targetDir ' + targetDirectory + ' -csv ' + os.path.basename(
                tileslistName) + ' ' + resampledMultifname
            tilecmdPan = pythonLocation + gdalRetileLocation + ' -ps ' + str(xtiledim) + ' ' + \
                         str(ytiledim) + ' -targetDir ' + targetDirectory + ' -csv ' + os.path.basename(
                tileslistNamePan) + ' ' + panfname

            os.system(tilecmd)
            os.system(tilecmdPan)

            if os.path.exists(os.path.join(targetDirectory, tileslistName)) and os.path.exists(
                    os.path.join(targetDirectory, tileslistNamePan)):
                lines = open(tileslistName, 'r').readlines()
                linesPan = open(tileslistNamePan, 'r').readlines()
            else:
                print()
                print('.csv files do not exist: ')
                print(tileslistName)
                print(tileslistNamePan)
                sys.exit()

            if len(lines) > 0 and len(linesPan) > 0 and (len(lines) == len(linesPan)):
                # ---- these lists will hold names of pan-sharpened tiles
                outputTileNamesBrovey = []
                for i in range(len(lines)):
                    # ---- get name of 4-band bicubic-resampled tile (geotiff), name of pan geotiff tile
                    tilenametiff = os.path.join(os.path.dirname(multifname), lines[i].split(';')[0])
                    tilenametiffPan = os.path.join(os.path.dirname(panfname), linesPan[i].split(';')[0])
                    # ---- make sure our file files (both pan+multi) exist
                    if not os.path.exists(tilenametiff):
                        print('File does not exist: ', tilenametiff)
                        sys.exit()
                    elif not os.path.exists(tilenametiffPan):
                        print('File does not exist: ', tilenametiffPan)
                        sys.exit()
                        # ---- now we need to establish outfile names for pan-sharpened tiff files
                    outputNameTileBrovey = tilenametiff.replace('.tif', '_PanSharpenedBrovey.tif')
                    # ----- now we need to convert geotiff tile file to pan-sharpened images
                    dsmulti_tile = gdal.Open(tilenametiff)
                    dspan_tile = gdal.Open(tilenametiffPan)

                    imgsBrovey = broveySharpen(dsmulti_tile, dspan_tile)
                    # if None not in imgsBrovey:
                    if imgsBrovey is not None:
                        writeImg(imgsBrovey, outputNameTileBrovey, dspan_tile)
                        outputTileNamesBrovey.append(outputNameTileBrovey)
                        del imgsBrovey
                        gc.collect()

                    if os.path.exists(outputNameTileBrovey):
                        os.remove(tilenametiff)
                        os.remove(tilenametiffPan)

                if len(outputTileNamesBrovey) > 0:
                    # ---- now we need to take all pan-sharpened FIHS/Brovey tiles, and mosaic them ... using gdal_merge
                    mosaicCmdBrovey = gdalMergeLocation + ' -o ' + fulloutnamebrovey + ' -of GTiff '
                    mosaicCmdListBrovey = []
                    mosaicCmdListBrovey.extend([mosaicCmdBrovey])
                    mosaicCmdListBrovey.extend(outputTileNamesBrovey)
                    mosaicCmdBrovey = ' '.join(mosaicCmdListBrovey)
                    mosaicCmdBrovey = mosaicCmdBrovey + ' > logfile.txt'
                    if not os.path.exists(fulloutnamebrovey): os.system(mosaicCmdBrovey)
                # ---- clean up some files we don't need anymore
                os.remove('logfile.txt')
    for i in outputTileNamesBrovey:
        os.remove(i)
    os.remove(resampledMultifname)
    os.remove(tileslistName)
    os.remove(tileslistNamePan)


def FIHS(panfname, multifname, out_path):
    dspan = gdal.Open(panfname)
    dsmulti = gdal.Open(multifname)

    if dspan.RasterCount != 1:
        print('First command line input argument (panchromatic geotiff image file) should have 1 band.')
        sys.exit()

    if dsmulti.RasterCount != 4:
        print('Second command line input argument (multispectral geotiff image file) should have 4 bands (RGB,NIR)')
        sys.exit()
    # resampledMultifname = multifname.replace('.tif', '_Resampled.tif')
    resampledMultifname = os.path.join(out_path, os.path.basename(multifname).replace('.tif', '_Resampled.tif'))
    resampledMultifname = resampleBicubic(multifname, dsmulti, dspan, resampledMultifname, gdalconst.GRA_Cubic)

    if not os.path.isfile(resampledMultifname):
        print('Failure to resample multispectral file: ')
        print(multifname)
        sys.exit()

    if ('None' not in str(type(dspan))) and ('None' not in str(type(dsmulti))):

        fulloutnamefihs = resampledMultifname.replace('_Resampled.tif', '_panSharpenedFIHS.tif')

        if not os.path.exists(fulloutnamefihs):

            # ---- tile up huge, resampled multispectral file
            dim = 4.0
            nrows, ncols = dsmulti.RasterYSize, dsmulti.RasterXSize
            xtiledim, ytiledim = int(ncols / dim), int(nrows / dim)  #

            # ---- create a tile command and then subsequently run it, tiles go to directory as pan/MS
            targetDirectory = os.path.dirname(panfname)
            tileslistName = os.path.join(targetDirectory, 'multispectralTiles.csv')
            tileslistNamePan = os.path.join(targetDirectory, 'panchromaticTiles.csv')

            tilecmd = pythonLocation + gdalRetileLocation + ' -ps ' + str(xtiledim) + ' ' + \
                      str(ytiledim) + ' -targetDir ' + targetDirectory + ' -csv ' + os.path.basename(
                tileslistName) + ' ' + resampledMultifname
            tilecmdPan = pythonLocation + gdalRetileLocation + ' -ps ' + str(xtiledim) + ' ' + \
                         str(ytiledim) + ' -targetDir ' + targetDirectory + ' -csv ' + os.path.basename(
                tileslistNamePan) + ' ' + panfname

            os.system(tilecmd)
            os.system(tilecmdPan)

            if os.path.exists(os.path.join(targetDirectory, tileslistName)) and os.path.exists(
                    os.path.join(targetDirectory, tileslistNamePan)):
                lines = open(tileslistName, 'r').readlines()
                linesPan = open(tileslistNamePan, 'r').readlines()
            else:
                print()
                print('.csv files do not exist: ')
                print(tileslistName)
                print(tileslistNamePan)
                sys.exit()

            if len(lines) > 0 and len(linesPan) > 0 and (len(lines) == len(linesPan)):

                # ---- these lists will hold names of pan-sharpened tiles

                outputTileNamesFIHS = []

                for i in range(len(lines)):

                    # ---- get name of 4-band bicubic-resampled tile (geotiff), name of pan geotiff tile
                    tilenametiff = os.path.join(os.path.dirname(multifname), lines[i].split(';')[0])
                    tilenametiffPan = os.path.join(os.path.dirname(panfname), linesPan[i].split(';')[0])

                    # ---- make sure our file files (both pan+multi) exist
                    if not os.path.exists(tilenametiff):
                        print('File does not exist: ', tilenametiff)
                        sys.exit()
                    elif not os.path.exists(tilenametiffPan):
                        print('File does not exist: ', tilenametiffPan)
                        sys.exit()

                        # ---- now we need to establish outfile names for pan-sharpened tiff files
                    outputNameTileFIHS = tilenametiff.replace('.tif', '_PanSharpenedFIHS.tif')

                    # ----- now we need to convert geotiff tile file to pan-sharpened images
                    dsmulti_tile = gdal.Open(tilenametiff)
                    dspan_tile = gdal.Open(tilenametiffPan)

                    imgsFIHS = fihsSharpen(dsmulti_tile, dspan_tile)
                    # if None not in imgsFIHS:
                    if imgsFIHS is not None:
                        writeImg(imgsFIHS, outputNameTileFIHS, dspan_tile)
                        outputTileNamesFIHS.append(outputNameTileFIHS)
                        del imgsFIHS
                        gc.collect()

                    if os.path.exists(outputNameTileFIHS):
                        os.remove(tilenametiff)
                        os.remove(tilenametiffPan)

                if len(outputTileNamesFIHS) > 0:

                    # ---- now we need to take all pan-sharpened FIHS/Brovey tiles, and mosaic them ... using gdal_merge
                    mosaicCmdFIHS = gdalMergeLocation + ' -o ' + fulloutnamefihs + ' -of GTiff '
                    mosaicCmdListFIHS = []
                    mosaicCmdListFIHS.extend([mosaicCmdFIHS])
                    mosaicCmdListFIHS.extend(outputTileNamesFIHS)
                    mosaicCmdFIHS = ' '.join(mosaicCmdListFIHS)
                    mosaicCmdFIHS = mosaicCmdFIHS + ' > logfile.txt'
                    if not os.path.exists(fulloutnamefihs): os.system(mosaicCmdFIHS)

                # ---- clean up some files we don't need anymore
                os.remove('logfile.txt')

    for i in outputTileNamesFIHS:
        os.remove(i)
    os.remove(resampledMultifname)
    os.remove(tileslistName)
    os.remove(tileslistNamePan)


def pan_sharpen(panfname, multifname, method, out_path):
    """
    融合多波段影像和全色波段影像
    :param panfname:全色波段影像绝对路径
    :param multifname:多波段影像绝对路径
    :param method: 'FIHS'，'Brovey' 两种，一般选择'FIHS'
    :param out_path：融合影像输出路径
    :return:None
    """
    # ---- make sure actual files exist and are .tif files
    if not os.path.exists(panfname):
        print('File does not exist: ', panfname)
        sys.exit()
    elif not os.path.exists(multifname):
        print('File does not exist: ', multifname)
        sys.exit()
    elif not panfname.endswith('.tiff'):
        print('First command line input argument panchromatic image file should be a geotiff.')
        sys.exit()
    elif not multifname.endswith('.tiff'):
        print('Second command line input argument multispectral image file should be a geotiff.')
        sys.exit()

    if method == 'Brovey':
        Brovey(panfname, multifname, out_path)

    if method == 'FIHS':
        FIHS(panfname, multifname, out_path)
