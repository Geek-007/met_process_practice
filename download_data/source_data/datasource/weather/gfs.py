#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2016 yangkang<yangkang@gagogroup.com>. All rights reserved.
import datetime
from typing import Any, Tuple, Union,List,Dict

import os


GFS_DEFINATION={
    "APCP": ["surface","2_m_above_ground","10_m_above_ground"],
    "TMP": ["2_m_above_ground","10_m_above_ground","surface"],
    "RH": ["2_m_above_ground","10_m_above_ground","surface"],
    "UGRD": ["10_m_above_ground","2_m_above_ground","surface"],
    "VGRD": ["10_m_above_ground","2_m_above_ground","surface"],
    "TMAX": ["2_m_above_ground","10_m_above_ground","surface"],
    "TMIN": ["2_m_above_ground","10_m_above_ground","surface"]
}

class GfsDownloader(object):
    """
    获取GFS下载链接，下载，并获取对应文件名
    """
    def __init__(self,download_path):
        self.download_path=download_path


    def get_gfs_data(self,date:datetime,gfs_defination:Dict):
        """
        下载gfs文件
        :param date:预测日期
        :param gfs_defination: 气象参数字典
        """

        for parameter in gfs_defination:
            gfs_url = self.get_url_list(date, parameter, gfs_defination[parameter])
            file_name = self.get_filename_list(date, parameter, gfs_defination[parameter])
            for i in range(len(gfs_url)):
                try:
                    os.system('wget "%s" -O %s' % (gfs_url[i], os.path.join(self.download_path, file_name[i])))
                except Exception:
                    print('errors happened', gfs_url[i])


    def get_filename(self,date: datetime,forcast_hour: int, parameter: str, level :str=None):


        parameter,level=self.check_parameter_level(parameter,level)
        filename= "GFS-%s-%s-%s.grb2" % (parameter,''.join(level[:4].split('_')), (date + datetime.timedelta(hours=forcast_hour)).strftime("%Y-%m-%d-%H"))
        if filename not in self.get_filename_list(date,parameter,level):
            raise Exception("check your input variable! ")
        filename_abspath=os.path.join(self.download_path,filename)
        return filename_abspath

    def get_url_list(self, date: datetime, parameter: str, level: str=None) \
            -> List[str]:
        """

        :param date:预测起始时间
        :param parameter:气象参数,目前限定APCP,TMAX,TMIN,TMP,RH,UGRD,VGRD七类
        :param level:气象要素的level， 目前限定 2m_above_ground,10m_above_ground,surface 三类
        :return:预测产品的下载地址List， 长度为173
        """

        #判断输入气象参数是否合适
        parameter, level = self.check_parameter_level(parameter, level)

        # 未来0h - 120h 预测时间间隔为1h, 未来120h - 240h 预测时间间隔为3h, 未来240h - 384h 预测时间间隔为12h
        forecast_hour = list(range(0, 120, 1)) + list(range(120, 240, 3)) + list(range(240, 396, 12))
        subregion = 'leftlon=0&rightlon=360&toplat=90&bottomlat=-90'
        url_list = []
        for hour in forecast_hour:
            file = 'gfs.t%02dz.pgrb2.0p25.f%03d' % (date.hour, hour)
            url = 'http://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file={file}&lev_{lev}=on&var_{var}=on&{subregion}&dir=%2Fgfs.{date}'.format(
                file=file, lev=level, var=parameter, subregion=subregion,
                date=date.strftime('%Y%m%d%H'))
            url_list.append(url)
        return url_list


    def get_filename_list(self, date: datetime, parameter: str , level: str=None)-> List[str]:
        """
        生成GFS产品对应的文件名
        用于生成与get_url_list方法得到的url List一一对应的文件名.
        :param date: 预测的起始日期
        :param parameter: 预测的气象要素
        :param level:气象要素的level
        :return: GFS产品文件名List，格式为GFS-{parameter}-{level(abbreviation)}-{Year}-{month}-{day}-{hour}.grb2，长度为173,
        """
        parameter, level = self.check_parameter_level(parameter, level)
        forecast_hour = list(range(0, 120, 1)) + list(range(120, 240, 3)) + list(range(240, 396, 12))
        filename_list = []
        for hour in forecast_hour:
            filename_list.append(
                "GFS-%s-%s-%s.grb2" % (parameter,''.join(level[:4].split('_')), (date + datetime.timedelta(hours=hour)).strftime("%Y-%m-%d-%H")))

        return filename_list

    def check_parameter_level(self,parameter:str, level:str):
        """
        检查气象参数是否合格
        :param parameter:
        :param level:
        :return:
        """
        parameter=parameter.upper()
        print(GFS_DEFINATION[parameter])
        if parameter not in GFS_DEFINATION.keys():
            raise Exception("invalid paramerer",parameter)
        if level is None:
            level = GFS_DEFINATION[parameter][0]
        elif level in GFS_DEFINATION[parameter]:
                level=level
        else:
                raise Exception("invalid level",level)

        return parameter,level