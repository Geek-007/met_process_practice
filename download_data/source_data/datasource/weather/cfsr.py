#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2016 jinhuan <zhujinhuan@gagogroup.com>. All rights reserved.
import os

class CFSR_Downloader(object):
    """
    每月下载CFSR再分析数据

    Args:
        password: 账号密码
        username： 账号
        year： 所需下载年份 eg：2017
        mon： 所需下载月份  eg：2
        dir： 数据下载路径 eg：./

    Returns:
        下载的每月每要素一个文件，eg：
        apcp.cdas1.201701.grb2
        dswsfc.cdas1.201701.grb2
        rh2m.cdas1.201701.grb2
        tmax.cdas1.201701.grb2
        tmin.cdas1.201701.grb2
        tmp2m.cdas1.201701.grb2
        wnd10m.cdas1.201701.grb2
    """
    def __init__(self, year, mon, dir):
        self.username = os.environ.get('CFSRUSER')
        self.password = os.environ.get('CFSRPASSWORD')
        self.dir = dir
        self.year = year
        self.mon = mon

    def get_cfsr(self):
        os.system("../shell/Download_CFSR.sh %s %s %s %s %s" % (self.password, self.username, self.year, self.mon, self.dir))