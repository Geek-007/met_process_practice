# -*- coding: utf-8 -*-
# # @Author  : guoanboyu
# @Email   : guoanboyu@gagogroup.com
import datetime
import json
from typing import List, Dict

import numpy as np
import pandas as pd
import requests

class CorrectGrid(object):
    '''
    用2345天气网的预报结果订正gfs预报结果。采取方法如下：
    对于任一一个网格点，找到离它最近的气象站点，并以该气象站点经纬度为圆心1°的距离为半径画圆，在该圆范围内的所有站点作为订正此网格点的备选站点。
    从2345预报结果中提取所有备选城市中的最高气温、最低气温以及降水数据，与gfs预报结果求平均，得到订正后的预报结果。
    '''
    def __init__(self, lat: str, lon: str, day: str, api_var: str):
        '''
        :param lat: 预报地点纬度
        :param lon: 预报地点经度
        :param day: 预报的天数
        :param api_var: 气象参数类型，apcp: 降水，tmax: 最高温, tmin: 最低温。若需多个参数用“,”分隔，中间不加空格，
        '''
        self.lat = float(lat)
        self.lon = float(lon)
        self.day = int(day)
        self.var = api_var[1:-1].split(",")
        self.api_var = api_var

    def request_api(self) -> (List[Dict]):
        '''
        请求gagogroup接口获取所要gfs预报数据
        :return: 返回包含所请求变量的字典
        '''
        header = {"Token": "gdc_longrun"}
        host = 'https://api.gagogroup.cn/api/v2/'
        url = host + '/weather/forecast?lon=%s&lat=%s&hrs=%s&features=%s'%(self.lon, self.lat, (self.day)*24, self.api_var)
        try:
            respond = requests.get(url, headers=header)
        except Exception as err:
            print(err)
        else:
            forecastWeather = json.loads(respond.content)['data']['forecastWeather']
        return forecastWeather

    def gfs_forcastdata(self, forecastWeather: List[Dict], var_name: str) -> (List[float]):
        '''
        传入tmax，tmin，apcp其中某一个变量名，则分别计算每天的最高气温、最低气温、累计降水，并返回一个列表
        :param forecastWeather: 为request_api函数返回的字典
        :param var_name: 所请求的某一个变量名
        :return: 返回一个列表，长度为所请求预报天数
        '''
        var_result = {}
        for value in forecastWeather:
            frcsttime = datetime.datetime.strptime(str(value['date']), "%Y-%m-%dT%H:%M:%S.000Z") + datetime.timedelta(hours=8)
            frcsttime = frcsttime.strftime("%Y-%m-%d")
            # print(frcsttime, value)
            # 最高气温
            if frcsttime in var_result.keys():
                var = var_result[frcsttime]
                var.append(float(value[var_name]))
            else:
                var_result[frcsttime] = [float(value[var_name])]
        # print(var_result)
        if var_name == "tmax":
            var = list(map(max, var_result.values()))
        elif var_name == "tmin":
            var = list(map(min, var_result.values()))
        elif var_name == "apcp":
            var = list(map(sum, var_result.values()))
        return var

    def select_city(self) -> (List):
        '''
        查找、合并生成所有用来订正某网格点的备选站点列表
        :return: 返回一个列表，每个元素为省名+县名
        '''
        province, city, lat, lon, height = self.get_city()
        city_list = list(zip(province, city, lat, lon, height))
        #筛选站点标准
        city_circle = []
        distance = []
        # 找到距指定经纬度距离最近的站点
        for province_c, city_c, lat_c, lon_c, height_c in city_list:
            distance.append(np.power(np.power(lat_c - self.lat, 2) + np.power(lon_c - self.lon, 2), 0.5))
        city_index = distance.index(min(distance))
        # 找到距该站点距离为1°的所有站点
        for province_c, city_c, lat_c, lon_c, height_c in city_list:
            d = np.power(np.power(lat_c - lat[city_index], 2) + np.power(lon_c - lon[city_index], 2), 0.5)
            dh = abs(height[city_index] - height_c)
            if d < 1 and dh < 200:
                city_circle.append(province_c + " " + city_c)
        return city_circle

    def correct_gfs(self) -> (List):
        '''
        用2345天气网预报结果修正gfs预报结果
        :return: 返回一个字典，key为变量名，value为长度为所请求预报天数的列表
        '''
        cities = self.select_city()
        gfs_data = self.request_api()
        f2345_data = self.get_f2345()
        vars_amend = {}
        for var_name in self.var:
            var_o = self.gfs_forcastdata(gfs_data, var_name)
            #从json文件中读取符合标准的城市
            var_cities = []
            for city in cities:
                if city in f2345_data.keys():
                    var = f2345_data[city][var_name][:self.day]
                    var_cities.append(var)
                else:
                    pass
            var_cities.append(var_o)
            #对符合筛选标准的城市每天的气温求平均
            var_amend = list(map(np.nanmean, zip(*var_cities)))
            vars_amend[var_name] = var_amend
        return vars_amend

    def out_json(self) -> (Dict):
        '''
        将修正结果生成指定的json格式
        :return: 生成json格式
        {'data': {'forecastWeather': [{'date': '2017-05-08T00:00:00.000Z', 'tmax': 26.12, 'tmin': 7.43, 'apcp': 0.0}]}}
        '''
        forecastWeather = []
        results = {}
        vars_amend = self.correct_gfs()
        for day in range(self.day):
            day_result = {}
            frcstdate = datetime.datetime.now().date() + datetime.timedelta(days=day)
            frcstdate = frcstdate.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            day_result['date'] = frcstdate
            for name in self.var:
                day_result[name] = round(float(vars_amend[name][day]) * 100) / 100
            forecastWeather.append(day_result)
        results["data"] = {"forecastWeather": forecastWeather}
        return results

    def get_city(self) -> (List, List, List, List, List):
        '''
        获取全国2278个气象站所在区县的名字、经度、纬度、以及高度信息
        :return: DataFrame，第一列为省名，第二列为县名，第三列为纬度，第四列为经度，第五列为高度
        '''
        filename = '/mnt/f2345_data/china_region/station_edit_over_01(1229add_194_remark).csv'
        data = pd.read_csv(filename)
        province = data['ok'].tolist()
        city = data['name'].tolist()
        lat = data['lat'].tolist()
        lon = data['lon'].tolist()
        height = data['heigh'].tolist()
        return province, city, lat, lon, height

    def get_f2345(self) -> (Dict):
        '''
        获取2345天气网站爬取到的预报结果
        :return:  返回一个json，key为2596个省名区县名，value也是一个字典，包含tmax，tmin，apcp三个key，value为长度所预报天数的列表，
        {"北京 北京": {"tmax": [31.0, 29.0, 29.0, 32.0, 30.0, 28.0, 29.0, 31.0, 34.0, 39.0, 31.0, 29.0, 33.0, 35.0, 36.0],
                       "tmin": [16.0, 15.0, 15.0, 17.0, 17.0, 14.0, 17.0, 16.0, 15.0, 20.0, 16.0, 12.0, 18.0, 21.0, 20.0],
                       "apcp": [0.0, 5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 17.45, 17.45]}}
        '''
        today = datetime.datetime.now().date()
        filename = '/mnt/f2345_data/f2345_%s.json'%(today)
        with open(filename, 'r') as json_file:
            text = json_file.read()
        data = json.loads(text)
        return data

if __name__ == '__main__':
    province, city, lat, lon, height = get_city()
    grid = CorrectGrid('52.96666667','122.5166667', '15', '[tmax,tmin,apcp]')
    results = grid.out_json()
    print(results)
