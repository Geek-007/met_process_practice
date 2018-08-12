#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2016 yangkang <yangkang@gagogroup.com>. All rights reserved.
# from cmadownload import CmaDownload
# from cma2db import CmaToDb
from __future__ import unicode_literals

import datetime
import glob
import os
import time
from io import BytesIO

import numpy as np
import pandas as pd
import psycopg2 as pg
import requests
from PIL import Image
from PIL import ImageEnhance
from bs4 import BeautifulSoup
from pytesseract import image_to_string


class CmaToDb(object):
    """
    cma 数据插入数据库
    """

    def __init__(self, input_path, host, dbname, port, db_user, db_password):
        self.input_path = input_path
        self.host = host
        self.dbname = dbname
        self.port = port
        self.user = db_user
        self.password = db_password

    def cma_to_db(self):
        """
        1.解压下载cma的zip压缩包；
        2.cma 数据入库

        """

        # 1.解压zip文件
        zips = glob.glob("%s/S*00.zip" % self.input_path)
        for zip in zips:
            os.system('unzip %s -d %s' % (zip, zip[:-4]))

        # 2.连接数据库,数据入库
        conn = pg.connect(host=self.host, dbname=self.dbname,
                          port=self.port, user=self.user, password=self.password)
        files = glob.glob(os.path.join(str(self.input_path) + '/S*', "S*00.txt"))
        for file in files:
            self.weather_to_db(conn, self.input_path, file)
        conn.close()

        # 3.删除cma文件
        os.system("rm %s/*.zip" % self.input_path)
        os.system("rm -r %s/S*00" % self.input_path)

    def weather_to_db(self, conn, basedir, fname):
        """
        :param conn:  连接数据库
        :param basedir: cma文件路径
        :param fname: 单个cma文件
        :return:
        """
        # print(fname)
        df = pd.read_table(os.path.join(basedir, fname), delim_whitespace=True)
        sqltmp = "insert into weather_station_observations_hourly\
                 (tmax, tmp, tmin, rh, rhmin, apcp, wnd_gust_spd, wnd_gust_dir, wnd_max_spd, wnd_max_dir,wnd_spd, wnd_dir, stid, datetime ) values(\
                 {tmax}, {tmp}, {tmin}, {rh}, {rhmin}, {apcp}, {wnd_gust_spd}, {wnd_gust_dir}, {wnd_max_spd}, {wnd_max_dir}, {wnd_spd}, {wnd_dir}, {stid},'{dt}');"
        columns = df.columns

        cur = conn.cursor()
        for i in range(len(df)):
            row = df.iloc[i, :]
            # print(row)

            stid = self.check_var('Station_Id_C', columns, row)
            if ('Year' in columns) and ('Mon' in columns) and ('Day' in columns) and ('Hour' in columns):
                dt = (datetime.datetime(int(row['Year']), int(row['Mon']), int(row['Day']), int(row['Hour']))).strftime(
                    "%Y-%m-%d %H:00:00")
            else:
                dt = 'NaN'
            tmax = self.check_var('TEM_Max', columns, row)
            tmp = self.check_var('TEM', columns, row)
            tmin = self.check_var('TEM_Min', columns, row)
            rh = self.check_var('RHU', columns, row)
            rhmin = self.check_var('RHU_Min', columns, row)
            apcp = self.check_var('PRE_1h', columns, row)
            wnd_gust_spd = self.check_var('WIN_S_Inst_Max', columns, row)
            wnd_gust_dir = self.check_var('WIN_D_INST_Max', columns, row)
            wnd_max_spd = self.check_var('WIN_S_Max', columns, row)
            wnd_max_dir = self.check_var('WIN_D_S_Max', columns, row)
            wnd_spd = self.check_var('WIN_S_Avg_10mi', columns, row)
            wnd_dir = self.check_var('WIN_D_Avg_10mi', columns, row)

            sql = sqltmp.format(tmax=tmax, tmp=tmp, tmin=tmin, \
                                rh=rh, rhmin=rhmin, \
                                apcp=apcp, \
                                wnd_gust_spd=wnd_gust_spd, wnd_gust_dir=wnd_gust_dir, \
                                wnd_max_spd=wnd_max_spd, wnd_max_dir=wnd_max_dir, \
                                wnd_spd=wnd_spd, wnd_dir=wnd_dir, \
                                stid=int(stid), dt=dt)
            # print(sql)
            try:
                cur.execute(sql)
            except Exception as err:
                conn.rollback()
                print(err)
            conn.commit()
        cur.close()

    @staticmethod
    def check_var(variable, columns, row):
        """
        判断表中变量数据是否存在
        :param variable: 气象变量
        :param columns: 列
        :param row: 行
        :return:
        """

        if variable in columns:
            var = row[variable]
        else:
            var = np.nan
        return var


class CmaDownloader(object):
    """
    cma 气象站点数据下载
    """

    # def __init__(self):
    #     self.username = os.environ.get('CMAUSER')
    #     self.password = os.environ.get('CMAPASSWORD')
    #     self.download_path = os.environ.get('DOWNLOADPATH')


    @classmethod
    def get_cma_data(cls, username, password, download_path):

        if not os.path.exists(download_path):
            os.makedirs(download_path)

        product_code = "A.0012.0001"
        # 　Step 1 : 检索信息
        #  站点
        station_padir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
        station_grandpadir = os.path.split(station_padir)[0]
        station_info = pd.read_csv(os.path.join(station_grandpadir, 'data/stationid.csv'))
        station_ids = list(station_info[(station_info.站名 != "极地") & (
            station_info.站名 != "香港") & (station_info.站名 != "澳门") & (station_info.站名 != "台湾")].区站号)
        # 站点要素
        elements = ["PRS", "PRS_Sea", "PRS_Max", "PRS_Min", "WIN_S_Max", "WIN_S_Inst_Max",
                    "WIN_D_INST_Max", "WIN_D_Avg_10mi", "WIN_S_Avg_10mi", "WIN_D_S_Max", "TEM", "TEM_Max", "TEM_Min",
                    "RHU",
                    "VAP", "RHU_Min", "PRE_1h"]
        # 时间
        yesterday = (
            datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        date_s = '%s 00' % yesterday
        date_e = '%s 23' % yesterday
        # dateS = '2016-08-27 00'
        # dateE = '2016-08-27 23'

        # 　Step 2 :  登录
        is_login = False
        while not is_login:
            captcha, phpsessid = cls.cma_hourly_get_captcha()
            is_login = cls.cma_hourly_login(phpsessid, username, password, captcha)

        # Step 3 : 数据检索，加入购物车，提交订单，生成订单
        # 　单个订单长度限制为100个,　因此对订单进行拆分
        order_limit = 100
        order_num = 0
        for i in range(0, len(station_ids), order_limit):
            order_num += 1
            # 查找数据并加入购物车
            search_cond, search_cond_page = cls.cma_hourly_search(phpsessid, product_code, date_s, date_e,
                                                                  station_ids[i:i + order_limit], elements)
            cls.cma_hourly_add_to_cart(phpsessid, product_code, search_cond, search_cond_page)
            carlist = cls.cma_hourly_cart_confirm(phpsessid)
            # 生成订单
            cls.cma_hourly_commit(phpsessid, carlist)

        # Step 4 : 下载22个订单
        time.sleep(3600)
        print(order_num)
        urls = ["http://data.cma.cn/order/list/3.html?type=online",
                "http://data.cma.cn/order/list/2.html?type=online",
                "http://data.cma.cn/order/list/type/online.html"]
        # order_num= 22, 2 + 10 + 10
        num = 2
        for url in urls:
            print(url)
            cls.cma_hourly_download(phpsessid, url, num, download_path)
            num = 10

    @staticmethod
    def cma_hourly_get_captcha():
        """
        获取识别验证码
        :return: 返回验证码字符串
        """

        login_url = "http://data.cma.cn/user/toLogin.html"
        response = requests.get(login_url)
        soup = BeautifulSoup(response.text, "html.parser")
        tag = soup.find_all('img', id='yw0')[0]

        captcha_url = 'http://data.cma.cn%s' % (tag.attrs['src'])

        headers = {
            "Host": "data.cma.cn",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }

        try:
            response = requests.get(captcha_url, headers=headers)
            PHPSESSID = response.headers["Set-Cookie"].split(';')[0].split('=')[1]
            img = Image.open(BytesIO(response.content))
            enhancer = ImageEnhance.Contrast(img)
            im_en = enhancer.enhance(4)
            captcha = image_to_string(im_en)
            return captcha, PHPSESSID

        except requests.exceptions.RequestException:
            print('获取验证码失败')
            return None

    @staticmethod
    def cma_hourly_login(phpsessid, username, password, captcha):
        """
        模拟登陆
        :param phpsessid:
        :param username:
        :param password:
        :param captcha:
        :return:
        """
        url = "http://data.cma.cn/user/Login.html"
        headers = {
            "Host": "data.cma.cn",
            "Origin": "http://data.cma.cn",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "http://data.cma.cn/site/index.html",
            "Cookie": "PHPSESSID=%s; SERVERID=3de774487f1a2b08a62184a804717207|1470213667|1470213340" % phpsessid,
            "Content-Length": "68"
        }
        data = {
            "userName": username,
            "password": password,
            "verifyCode": captcha
        }

        try:
            response = requests.post(url, headers=headers, data=data)
            if response.json()["status"] == 100:
                return True
            else:
                return False
        except requests.exceptions.RequestException:
            return False

    @staticmethod
    def cma_hourly_search(phpsessid, product_code, date_s, date_e, station_ids, elements):

        url = "http://data.cma.cn/data/search.html?dataCode=A.0012.0001"
        headers = {
            "Host": "data.cma.cn",
            "Origin": "http://data.cma.cn",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "http://data.cma.cn/dataService/index/datacode/A.0012.0001.html",
            "Cookie": "PHPSESSID=%s" % (phpsessid),
        }
        elements = list(zip(['elements[]'] * len(elements), elements))
        station_ids = list(zip(['station_ids[]'] * len(station_ids), station_ids))
        date_s = [('dateS', date_s)]
        date_e = [('dateE', date_e)]
        other = [('hidden_limit_timeRange', '7'),
                 ('hidden_limit_timeRangeUnit', 'Day'),
                 ('isRequiredHidden[]', 'dateS'),
                 ('isRequiredHidden[]', 'dateE'),
                 ('isRequiredHidden[]', 'station_ids[]'),
                 ('isRequiredHidden[]', 'elements[]'),
                 ('select', 'on'),
                 ('dataCode', product_code),
                 ('dataCodeInit', product_code)]
        data = elements + station_ids + date_s + date_e + other
        try:
            response = requests.post(
                url, data=data, headers=headers)
            if response.status_code == 200:
                print('查询完毕~')
                soup = BeautifulSoup(response.text, "html.parser")
                search_cond = soup.find_all(
                    'input', id='SearchCond')[0].attrs['value']
                search_cond_page = soup.find_all(
                    'input', id='SearchCondPage')[0].attrs['value']
                return search_cond, search_cond_page
            else:
                print('查询失败~')
        except requests.exceptions.RequestException:
            print('查询失败~')

    @staticmethod
    def cma_hourly_add_to_cart(phpsessid, product_code, search_cond, search_cond_page):
        url = "http://data.cma.cn/order/car.html"
        headers = {
            "Host": "data.cma.cn",
            "Origin": "http://data.cma.cn",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "http://data.cma.cn/dataService/index/datacode/A.0012.0001.html",
            "Cookie": "PHPSESSID=%s" % (phpsessid)
        }
        data = {
            "SearchCond": search_cond,
            "storageType": "0",
            "fileNum": "0",
            "SearchCondPage": search_cond_page,
            "code": product_code,
            "selectFileInfo": ""
        }

        try:
            response = requests.post(
                url, data=data, headers=headers)
        except requests.exceptions.RequestException:
            print('加入购物车失败~')

    @staticmethod
    def cma_hourly_cart_confirm(phpsessid):
        url = "http://data.cma.cn/order/carView.html"
        headers = {
            "Host": "data.cma.cn",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36",
            "Referer": "http://data.cma.cn/data/search.html?dataCode=A.0012.0001",
            "Cookie": "PHPSESSID=%s" % (phpsessid)
        }

        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            cars = soup.find_all(
                'input', type='checkbox', checked="checked")
            for car in cars:
                if 'name' in car.attrs:
                    carlist = car.attrs['name']
            print("加入购物车成功~")
            return carlist
        except requests.exceptions.RequestException:
            print('加入购物车失败~')

    @staticmethod
    def cma_hourly_commit(phpsessid, carlist):
        url = "http://data.cma.cn/order/createOrder.html"
        headers = {
            "Host": "data.cma.cn",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36",
            "Referer": "http://data.cma.cn/order/carView.html",
            "Cookie": "PHPSESSID=%s" % (phpsessid)
        }
        params = {
            carlist: ""
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.json()["data"]["message"] == "SUCCESS":
                print('订单提交成功~')
            else:
                print('订单提交失败~')
        except requests.exceptions.RequestException:
            print('订单提交失败~')

    @staticmethod
    def cma_hourly_download(phpsessid, url, num, download_path):
        download_path = download_path + '/'
        headers = {"Cookie": "PHPSESSID=%s" % phpsessid}
        try:
            response = requests.post(url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            tags = soup.select('a')
            flag = 0
            for tag in tags:
                if tag.has_attr('class'):
                    if tag['class'] == ['down1218']:
                        out_file = (tag['href'].split("/S20")[-1]).split("?")[0]
                        print('wget "%s" -O S20%s' % (tag['href'], out_file))
                        os.system('wget "%s" -O %sS20%s' % (tag['href'], download_path, out_file))
                        flag += 1
                        if flag >= num:
                            break
        except requests.exceptions.RequestException:
            print('errors happened')
