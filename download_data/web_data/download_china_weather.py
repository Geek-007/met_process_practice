# -*- coding: utf-8 -*-
import re
import json
import requests
import pandas as pd
import datetime
from bs4 import BeautifulSoup

class WeatherData(object):
    """Forecast data structure of each city

    Each city have 15 days forecast data.This data include below attribute.

    Attribute:
        :param frcstdate:      An integer of datetime represent the forecast date
        :param msg:            A string represent the weather condition
        :param tmax:           A string include ℃ represent the maximum air temperature
        :param tmin:           A string include ℃ represent the minimum air temperature
        :param wind_speed:     A string represent the speed of wind
        :param wind_deg:       A string represent the direction of wind
        :param fine_frcst:     A class of WeatherDataHour represent the fine weather forecast
    """
    def __init__(self, frcstdate:int, msg:str, tmax:str, tmin:str, wind_speed:str, wind_deg:str):
        self.frcstdate     = frcstdate
        self.msg           = msg
        self.tmax          = tmax
        self.tmin          = tmin
        self.wind_speed    = wind_speed
        self.wind_deg      = wind_deg

class WeatherDataHour(object):
    def __init__(self, time:int, msg:str, tmp:str, wind_speed:str, wind_deg:str):
        """Refine forecast data structure of each city

        Each city have 7 days refine forecast data.This data include below attribute.

        :param time:        An integer of datetime represent the forecast time
        :param msg:         A string represent the weather condition
        :param tmp:         A string represent air temperature at forecast time
        :param wind_speed:  A string represent the speed of wind
        :param wind_deg:    A string represent the direction of wind
        """
        self.time       = time
        self.msg        = msg
        self.tmp        = tmp
        self.wind_speed = wind_speed
        self.wind_deg   = wind_deg

def get_citycode(path:str) -> (str,str,str):
    url = 'http://www.weather.com.cn/weather/'
    url_15d = 'http://www.weather.com.cn/weather15d/'
    city_url = []
    city_url_15d = []
    city_name = []
    f = open(path, 'rb')
    lines = f.readlines()
    for line in lines:
        if len(line) > 10:
            # print(url+linesplit(',')[0]+'.shtml')
            city_url.append(url+line.decode('utf-8').split('=')[0]+'.shtml')
            city_url_15d.append(url_15d+line.decode('utf-8').split('=')[0]+'.shtml')
            city_name.append(line.decode('utf-8').split('=')[1])
    return city_url,city_url_15d,city_name

def download_7days_data(response, date:int) -> (list,list):
    '''Get 7 days forecast result of each county.

       Args:
           :param response:  A html response used requests.models.Response
           :param date:      An integer represent today

       Returns:
           results_7days:    A list include 7 data,each data is a class of WeatherData represent one day forecast result
           day7_refine:      A list include 7 data,each data is also a list represent different time of forecast result in that day.
       '''
    date_hour = datetime.datetime.strptime(str(date)+" 00", '%Y-%m-%d %H')
    results_7days = []
    soup = BeautifulSoup(response.content, "html.parser")
    # 处理精细化预报数据
    day7_refine = []
    if len(soup.select('div[class="c7d"] script')) != 0:
        hour3data = soup.select('div[class="c7d"] script')[0].get_text()
        frcst_hour = str(re.findall('"7d":.*', hour3data))[7:]
        day_num = 0
        for day in frcst_hour.split(']')[:7]:     #某一天下的精细预报
            day_refine = []
            for frcsttime in day[3:-1].split('","'):        #某一天下所有时间的精细预报
                day = frcsttime.split(',')[0].split('日')[0]
                hour = frcsttime.split()[0].split('日')[1][:2]
                if int(hour) == 2:
                    day_num = day_num + 1
                    time = date_hour + datetime.timedelta(days=day_num, hours=int(hour))
                else:
                    time = date_hour + datetime.timedelta(days=day_num, hours=int(hour))
                msg = frcsttime.split(',')[2]
                tmp = frcsttime.split(',')[3]
                wind_deg = frcsttime.split(',')[4]
                wind_speed = frcsttime.split(',')[5]
                day_refine.append(WeatherDataHour(time,msg,tmp,wind_speed,wind_deg))
            # print(len(day_refine))
                # day_refine.append({"time": time, "precipitation": msg, "tmp": tmp, "wind_speed": wind_speed, "wind_deg":wind_deg})
            day7_refine.append(day_refine)
        # print(len(day7_refine))
    else:
        day7_refine = None
    # 获取前7天预报
    tags = soup.select('ul[class="t clearfix"] li')
    for day_num, tag in enumerate(tags[:]):  # 一个tag一天
        day = BeautifulSoup(str(tag), "html.parser")
        frcstdate = date + datetime.timedelta(days=day_num)  #day.select('h1')[0].get_text()
        msg = day.select('p[class="wea"]')[0].get_text()
        tmin = day.select('p[class="tem"] i')[0].get_text()
        if len(day.select('p[class="tem"] span')) != 0:
            tmax = day.select('p[class="tem"] span')[0].get_text()
        else:
            tmax = None
        wind_speed = day.select('p[class="win"] i')[0].get_text()
        if len(day.select('p[class="win"] em span')) == 2 :
            wind_deg1 = day.select('p[class="win"] em span')[0]['title']
            wind_deg2 = day.select('p[class="win"] em span')[1]['title']
            wind_deg  = str(wind_deg1) + "转" + str(wind_deg2)
        else:
            wind_deg1 = day.select('p[class="win"] em span')[0]['title']
            wind_deg2 = None
            wind_deg  = str(wind_deg1)
        if day7_refine != None:
            results_7days.append(WeatherData(frcstdate, msg, tmax, tmin, wind_speed, wind_deg))
            # results_7days.append({'frcstdate': frcstdate, 'msg': msg, 'tmax': tmax, 'tmin': tmin,
            #                       'wind_speed': wind_speed, 'wind_deg': wind_deg, 'fine_frcst':day7_refine[day_num]})
        else:
            results_7days.append(WeatherData(frcstdate, msg, tmax, tmin, wind_speed, wind_deg))
            # results_7days.append({'frcstdate': frcstdate, 'msg': msg, 'tmax': tmax, 'tmin': tmin,
            #                       'wind_speed': wind_speed, 'wind_deg': wind_deg})
    return(results_7days,day7_refine)

def download_15days_data(response, date:int) -> (list):
    '''Get 8-15days forecast result of each county.

    Args:
        :param response:  A html response used requests.models.Response
        :param date:      An integer represent today

    Return:
        A list include 8 data,each data is a class of　WeatherData
    '''
    results_15days = []
    soup = BeautifulSoup(response.content, "html.parser")
    tags = soup.select('ul[class="t clearfix"] li')  # 15个tags代表15天
    for day_num,tag in enumerate(tags[:]):  # 一个tag一天
        day = BeautifulSoup(str(tag), "html.parser")
        frcstdate = date + datetime.timedelta(days=day_num+7)  #day.select('span[class="time"]')[0].get_text()
        msg = day.select('span[class="wea"]')[0].get_text()
        tmax = day.select('span[class="tem"]')[0].get_text().split("/")[0]
        tmin = day.select('span[class="tem"]')[0].get_text().split("/")[1]
        wind_speed = day.select('span[class="wind1"]')[0].get_text()
        wind_deg = day.select('span[class="wind"]')[0].get_text()
        # results_15days.append(WeatherData(frcstdate,precipitation,tmax,tmin,wind_speed,wind_deg,None))
        results_15days.append({'frcstdate': frcstdate, 'msg': msg, 'tmax': tmax, 'tmin': tmin,
                                'wind_speed': wind_speed, 'wind_deg': wind_deg})
    return (results_15days)

def download_chinaweatherdata() -> (list,list):
    '''Get China weather 15days forecast data

    Returns:
        weather_results:       A list have 2 dimensions.The first dimension represent county.
                               The second dimension represent the forecast date.And each element in
                               this list is a WeatherData class.
        weather_results_refine:A list have 3 dimensions.The first dimension represent county.
                               The second dimension represent the forecast date.The third dimension
                               represent the forecast hour.And each element in this list is a
                               WeatherDataHour class.
    '''
    date = datetime.datetime.now().date()
    forecast_url = 'http://www.weather.com.cn/static/html/weather.shtml'
    path = 'E:\GAGO\GFS\citycode.txt'
    city_url, city_url_15d, city_name= get_citycode(path)
    print(len(city_name))

    num_7d = 1
    num_15d = 1
    result_7days = []
    ressule_7days_refine = []
    result_15days = []


    for url in city_url[:1]:
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
        # 获取前7天预报
        try:
            print(str(num_7d) + "." + url)
            response = requests.get(url, headers=header, timeout=5)
        except Exception as e:
            print(e)
            city_url.insert(num_7d, url)
        else:
            num_7d = num_7d +1
            result, result_refine = download_7days_data(response, date)
            result_7days.append(result)
            ressule_7days_refine.append(result_refine)
    for url in city_url_15d[:1]:
        # 获取8-15天预报
        try:
            print(str(num_15d) + "." + url)
            response_15d = requests.get(url, headers=header, timeout=5)
        except Exception as e:
            print(e)
            city_url_15d.insert(num_15d, url)
        else:
            num_15d = num_15d + 1
            result = download_15days_data(response_15d, date)
            result_15days.append(result)

    # city_forecast = pd.DataFrame()
    weather_results = []
    weather_results_refine = []
    for day7,day15,refine in list(zip(result_7days, result_15days, ressule_7days_refine)):
        weather_results.append(day7 + day15)
        weather_results_refine.append(refine)
    # print(weather_results[0][0].frcstdate)
    # print(weather_results_refine[0][0][0].time)
    return(weather_results,weather_results_refine)

if __name__ == '__main__':
    result,refine_result=download_chinaweatherdata()