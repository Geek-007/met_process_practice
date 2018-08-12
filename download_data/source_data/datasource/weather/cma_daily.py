#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2016 jinhuan <zhujinhuan@gagogroup.com>. All rights reserved.
from __future__ import unicode_literals
import glob
import os,sys
import json
import datetime,time
import psutil
from io import BytesIO
from bs4 import BeautifulSoup
import requests
from PIL import Image
import pandas as pd
import matplotlib.pyplot as plt 
from PIL import ImageEnhance 
from pytesseract import image_to_string

class Cma194Downloader(object):
    """国际气象观测站站点数据下载

    下载中国气象数据共享网（http://data.cma.cn/data/detail/dataCode/SURF_CLI_CHN_MUL_DAY_CES_V3.0.html）上的
    中国194个站点1951年1月以来
    本站气压、气温、降水量、蒸发量、相对湿度、风向风速、日照时数和0cm地温要素的日值数据。
    滞后3个月，每月更新一次数据，需每月调用下载一次。

    Args:
        CMAUSER：中国气象数据共享网的账号
        CMAPASSWORD：中国气象数据共享网的密码
        DOWNLOADPATH：下载文件存放路径
        date_s: 下载起始时间 eg: "2017-01";
        date_e: 下载结束时间 eg: "2017-03";

    Returns:
        下载的每月每要素一个文件，eg：
        SURF_CLI_CHN_MUL_DAY_CES-GST-12030-0cm-201602.TXT
        SURF_CLI_CHN_MUL_DAY_CES-EVP-13240-201602.TXT
        SURF_CLI_CHN_MUL_DAY_CES-RHU-13003-201602.TXT
        SURF_CLI_CHN_MUL_DAY_CES-PRE-13011-201602.TXT
        SURF_CLI_CHN_MUL_DAY_CES-PRS-10004-201602.TXT
        SURF_CLI_CHN_MUL_DAY_CES-SSD-14032-201602.TXT
        SURF_CLI_CHN_MUL_DAY_CES-WIN-11002-201602.TXT
        SURF_CLI_CHN_MUL_DAY_CES-TEM-12001-201602.TXT
    """

    def __init__(self, date_s, date_e):
        self.username = os.environ.get('CMAUSER')
        self.password = os.environ.get('CMAPASSWORD')
        self.download_path = os.environ.get('DOWNLOADPATH')
        self.date_s = date_s
        self.date_e = date_e

    def get_cma_data(self):
        """登录并下载数据

        模拟登陆下载流程：
        => 模拟登陆中国气象数据共享网data.cma.cn -- prepare() + login()；
        => 查询数据 -- search();
        => 加入购物车并检查是否成功 -- add_to_cart() + cart_confirm();
        => 提交订单 -- commit();
        => 下载数据 -- download();

        """
        username = self.username
        password = self.password
        download_path=self.download_path
        os.chdir(download_path)

        # Step 1 : 检索信息
        product_code = "SURF_CLI_CHN_MUL_DAY_CES_V3.0"

        # Step 2 :  登录
        is_login = False
        while not is_login:
            captcha, PHPSESSID = self.prepare()
            is_login = self.login(PHPSESSID, username, password, captcha)

        # Step 3 : 数据查询
        SearchConds = self.search(PHPSESSID, product_code, self.date_s, self.date_e)
        self.add_to_cart(PHPSESSID, product_code, SearchConds)
        carlist, carlist_val = self.cart_confirm(PHPSESSID)
        self.commit(PHPSESSID, carlist, carlist_val)

        # Step 4 : 下载订单
        time.sleep(3600)
        urls = ["http://data.cma.cn/order/list/type/online.html"]
        for url in urls:
            self.download(PHPSESSID, url)

        # Step 5 : 下载订单中的数据
        time.sleep(120)
        basedir = os.getcwd()
        files = os.listdir(basedir)
        files.sort()
        for fil in files:
            if fil.endswith('.txt'):
                os.system('wget -i %s' % (fil))

        fils = glob.glob(os.path.join(str(basedir), "SURF*Expires*"))
        for ff in fils:
            os.system('mv "%s" %s' % (ff, (ff.split("/")[-1]).split("?")[0]))
        os.system('rm *txt')

    def prepare(self):
        """
        获取验证码
        """

        login_url = "http://data.cma.cn/user/toLogin.html"
        response = requests.get(login_url)
        soup = BeautifulSoup(response.text, "html.parser")
        tag = soup.find_all('img', id='yw0')[0]

        captcha_url = 'http://data.cma.cn%s' % (tag.attrs['src'])

        headers = {
            "Host": "data.cma.cn",
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

    def login(self, PHPSESSID, username, password, captcha):
        """
        登陆中国气象数据共享网
        """

        url = "http://data.cma.cn/user/Login.html"
        headers = {
            "Host": "data.cma.cn",
            "Origin": "http://data.cma.cn",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "http://data.cma.cn/site/index.html",
            "Cookie": "PHPSESSID=%s; SERVERID=3de774487f1a2b08a62184a804717207|1470213667|1470213340" % (PHPSESSID),
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
                print("登录成功~")
                return True
            else:
                print("登录失败, 重试")
                return False
        except requests.exceptions.RequestException:
            return False

    def search(self, PHPSESSID, product_code, dateS, dateE):
        """
        查询数据
        """ 

        url = "http://data.cma.cn/data/search.html?dataCode=%s" % (product_code)
        headers = {
            "Host": "data.cma.cn",
            "Origin": "http://data.cma.cn",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "http://data.cma.cn/data/detail/dataCode/SURF_CLI_CHN_MUL_DAY_CES_V3.0.html",
            "Cookie": "PHPSESSID=%s" % (PHPSESSID),
        }
        data = [('dateS', dateS), ('dateE', dateE), ('dataCode', product_code), ('dataCodeInit', product_code)]
        try:
            response = requests.post(url, data=data, headers=headers)
            soup = BeautifulSoup(response.text, "lxml")
            tags = soup.find_all('input', type='checkbox')
            SearchConds = []
            for tag in tags:
                if 'name' in str(tag):
                    SearchConds.append(json.loads(tag.attrs['value']))
            return SearchConds
        except requests.exceptions.RequestException:
            print('查询失败~')

    def add_to_cart(self, PHPSESSID, product_code, SearchConds):
        """
        将查到的数据加入购物车
        """

        url = "http://data.cma.cn/order/ajax.html"
        headers = {
            "Host": "data.cma.cn",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": "PHPSESSID=%s" % (PHPSESSID)
        }

        for val in SearchConds:
            data = {
                "act": "addCar",
                "code": product_code,
                "selectFileInfo": json.dumps(SearchConds),
                "storageType": 1,
                "fileNum": len(SearchConds)
            }

            try:
                response = requests.post(url, headers=headers, data=data)
            except Exception:
                pass

    def cart_confirm(self, PHPSESSID):
        """
        确认已经将数据加入购物车
        """
        url = "http://data.cma.cn/order/carView.html"
        headers = {
            "Host": "data.cma.cn",
            "Cookie": "PHPSESSID=%s" % (PHPSESSID)
        }

        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            cars = soup.find_all(
                'input', type='checkbox', checked="checked")
            carlist = []
            for car in cars:
                if 'name' in car.attrs:
                    carlist = car.attrs['name']
                    carlist_val = car.attrs['value']
                    print("加入购物车成功~")
            if len(carlist) == 0: print('加入购物车失败~')
            return carlist, carlist_val
        except requests.exceptions.RequestException:
            print('加入购物车失败~')

    def commit(self, PHPSESSID, carlist, carlist_val):
        """
        提交订单
        """
        url = "http://data.cma.cn/order/createOrder.html"
        headers = {
            "Host": "data.cma.cn",
            "Referer": "http://data.cma.cn/order/carView.html",
            "Cookie": "PHPSESSID=%s" % (PHPSESSID)
        }
        params = {
            carlist: carlist_val
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.json()["data"]["message"] == "SUCCESS":
                print('订单提交成功~')
            else:
                print('订单提交失败~')
        except requests.exceptions.RequestException:
            print('订单提交失败~')

    def download(self, PHPSESSID, url):
        """
        下载提交的订单
        """
        headers = {"Cookie": "PHPSESSID=%s" % (PHPSESSID)}
        try:
            response = requests.post(url, headers=headers)
            soup = BeautifulSoup(response.text, "lxml")
            tags = soup.select('a')
            flag = 0
            for tag in tags:
                if tag.has_attr('class'):
                    if tag['class'] == ['down1218']:
                        out_file = (tag['href'].split("/S")[-1]).split("?")[0]
                        print ('wget "%s" -O S%s' % (tag['href'], out_file))
                        os.system('wget "%s" -O S%s' % (tag['href'], out_file))
        except requests.exceptions.RequestException:
            print('errors happened')

