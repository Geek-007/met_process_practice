# -*- coding: utf-8 -*-
import io 
import re
import pandas as pd
import json,sys
import psycopg2
from lxml import etree
import requests
import datetime,time
from bs4 import BeautifulSoup
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8') #改变标准输出的默认编码  

class WeatherData(object):
	def __init__(self,  province:str, city:str, frcstdate:int,\
						tmax:float, tmin:float, wind:float, apcp:float):
		self.province      = province
		self.city          = city
		self.frcstdate     = frcstdate
		self.tmax          = tmax
		self.tmin          = tmin
		self.wind    	   = wind
		self.apcp          = apcp

def get_city() ->(list,list,list,list):
	filename = '/home/guoanboyu/Project/china_region/station_edit_over_01(1229add_194_remark).csv'
	data     = pd.read_csv(filename)
	province = data['ok'].tolist()
	city     = data['name'].tolist()
	lat      = data['lat'].tolist()
	lon      = data['lon'].tolist()

	return province, city, lat, lon 

def request_api(lat,lon) ->(list):
	header = {"Token": "gdc_longrun"}
	host = 'https://api.gagogroup.cn/api/v2/'
	url = host + '/weather/forecast?lon=%s&lat=%s&hrs=384&features=[tmax,tmin,apcp,wnd_spd]'%(lon, lat)
	respond = requests.get(url, headers=header)
	forecastWeather = json.loads(respond.content)['data']['forecastWeather']
	return forecastWeather

def db_insert(table_name, results):
	conn = psycopg2.connect(database="farmlanddb", user="guoanboyu", password="gaby123")
	cur = conn.cursor()
	sqltmp = "insert into %s (province, city, datetime, tmax, tmin, wind, apcp) \
			values('{province}','{city}','{datetime}','{tmax}','{tmin}','{wind}','{apcp}');"%table_name
	for day in results:
		sql = sqltmp.format(province=day.province,city=day.city,datetime=day.frcstdate,\
							tmax=day.tmax,tmin=day.tmin,wind=day.wind,apcp=day.apcp)
		# sql = "select * from f2345_data ;"
		try:
			cur.execute(sql)
			# row = c.fetchall()
			# print(row)
		except Exception as err:
			conn.rollback()
			print (err)
	conn.commit()
	conn.close()

def db_delete(table_name):
	conn = psycopg2.connect(database="farmlanddb", user="guoanboyu", password="gaby123")
	cur = conn.cursor()
	sql = "delete from %s ;" %(table_name)
	try:
		cur.execute(sql)
	except Exception as err:
		conn.rollback()
		print (err)
	else:
		conn.commit()
		conn.close()

def get_GFS_forcastdata(forecastWeather, province, city, table_name):
	date = datetime.datetime.now().date() #+ datetime.timedelta(days=1)
	results = []
	for i in range(15):
		frcstdate = datetime.datetime.strptime(str(date), "%Y-%m-%d") + datetime.timedelta(days=i)   #输出的预报时间
		tmax = []
		tmin = []
		apcp = []
		wind = []
		# print(frcstdate)
		for value in forecastWeather:
			frcsttime = datetime.datetime.strptime(str(value['date']), "%Y-%m-%dT%H:%M:%S.000Z") + datetime.timedelta(hours=8)
			if str(frcsttime)[:10] == str(frcstdate)[:10]:
				# print(frcstdate, value['date'], value['windSpeed'])
				try:
					tmax.append(float(value['tmax']))
					tmin.append(float(value['tmin']))
					wind.append(float(value['windSpeed']))
					apcp.append(float(value['apcp']))
					# print(frcstdate, value['date'], value['tmax'], value['tmin'], value['apcp'], value['windSpeed'])
				except Exception as e:
					print(e)
					tmax.append(-999)
					tmin.append(999)
					wind.append(np.nan)
					apcp.append(0)	
					# print(frcstdate, value['date'], value['tmax'], value['tmin'], value['apcp'], value['windSpeed'])
		# print(tmax)
		# print(np.ma.masked_equal(tmax, -999))
		tmax = max(tmax)
		tmin = min(tmin)
		apcp = sum(apcp)
		wind = np.nanmean(wind)
		# print(tmax)
		tmax = round(float(tmax)*100)/100         #日最高温
		tmin = round(float(tmin)*100)/100         #日最低温
		apcp = round(float(apcp)*100)/100         #日累计降水
		wind = round(float(wind)*100)/100         #日平均风速
		# print(province, city, frcstdate, tmax, tmin, apcp, wind)
		data = WeatherData(province, city, frcstdate, tmax, tmin, wind, apcp)
		results.append(data)
	db_insert(table_name, results)
	
if __name__ == '__main__':
	db_delete('gfs_data')        #清空数据库
	province, city, lat, lon = get_city()
	city_list = list(zip(province, city, lat, lon))
	num = 1
	for province,city,lat,lon in city_list[:]:
		print(str(num)+"."+province+" "+city)
		forecastWeather = request_api(lat, lon)
		get_GFS_forcastdata(forecastWeather, province, city, 'gfs_data')
		num = num + 1