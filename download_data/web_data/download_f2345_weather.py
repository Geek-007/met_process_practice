# -*- coding: utf-8 -*-
import re
import json
import psycopg2
import requests
import datetime, time
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup

class WeatherData(object):
	def __init__(self,  province:str, city:str, frcstdate:int, apcp:str,\
						tmax:int, tmin:int, wind_speed:str, wind_deg:str):
		self.province      = province
		self.city          = city
		self.frcstdate     = frcstdate
		self.apcp          = apcp
		self.tmax          = tmax
		self.tmin          = tmin
		self.wind_speed    = wind_speed
		self.wind_deg      = wind_deg

def Get_2345_cityurl() ->(list,list):
	header = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
	host = 'http://tianqi.2345.com/'
	try:
		response = requests.get(host,headers=header,timeout=3)
	except Exception as e:
		print(e)
	else:
		soup = BeautifulSoup(response.content, "html.parser")
		tags = soup.find("div",attrs={'class':'clearfix custom'})
		province_name = []
		province_url = []
		city_url = []
		city_name = []
		data = {}
		num = 1
		#获得各省份url
		for child in tags:
			province_url.append(host+child['href'])
			province_name.append(child.string)
		#获得各城市url
		province_list = list(zip(province_url,province_name))
		for url,province in province_list:  #province_url
			try:
				print(str(num) + "." + url)
				response = requests.get(url,headers=header,timeout=3)
			except Exception as e:
				print(e)
				province_list.insert(num, (url,province))
			else:
				num = num + 1
				soup = BeautifulSoup(response.content, "html.parser")
				tags = soup.select('div[class="citychk"] dd a[href]')
				for city in tags:
					city_url.append(host+city['href'])
					city_name.append(province+"-"+city.string)
					# print(province+city.string)
				data[province] = {'url': city_url, 'city':city_name}   #34个省份
		print("1.Get all cities url")
		print(len(city_url))
		return city_url,city_name      #2597个city

def Get_2345_forcastdata(city_url,city_name,table_name):
	header = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
	city_list = list(zip(city_url, city_name))
	num = 1
	result = {}
	for url, name in city_list:
		print(str(num) + "." + url)
		try:
			response = requests.get(url,headers=header,timeout=3)
		except Exception as e:
			print(e)
			city_list.insert(num, (url, name))
		else:
			province = name.split('-')[0]
			city = name.split('-')[1]
			num = num + 1
			soup = BeautifulSoup(response.content, "html.parser")
			# 当天及未来6天预报
			result_7days = Parse_forecast_result(soup, 'div[class="week week_day7"] li',province, city)
			result_8days = Parse_forecast_result(soup, 'div[class="week week_day8"] li',province, city)
			result_15days = result_7days + result_8days    #一个城市15天的结果
			DB_insert(table_name, result_15days)
			jsonString = merge_dic(result_15days)

			result.update(jsonString)
	# print(result)
	today = datetime.datetime.now().date()
	filename = '/home/guoanboyu/Project/GFS/data/f2345_%s.json'%(today)
	fp = open(filename, "a")
	fp.write(json.dumps(result))
	fp.close()

def Parse_forecast_result(soup, tag, province, city):
	results = []
	today = datetime.datetime.now()
	days = soup.select(tag)
	for day in days:
		if '更新中' not in str(day):
			# print('获取天气数据目标正常')
			for child in day.descendants:
				if ('class="blue"' in str(child)): 
					tmin = (child.string)
				if ('class="red"' in str(child) and '℃' in str(child)): 
					tmax = (str(child.string).split('℃')[0])
			for string in day.stripped_strings:
				if ('晴' in string) or ('云' in string) or ('阴' in string) or ('雨' in string) or ('雪' in string) or ('沙' in string) or ('尘' in string): 
					apcp = get_var(string)
				if '风' in string: 
					wind_speed = str(string).split('风')[1]
					wind_deg   = str(string).split('风')[0]
				if '月' in string: 
					date = string
			frcstdate = datetime.datetime(today.year, int(date[:-1][:2]), int(date[:-1][3:5]))
			data = WeatherData(province, city, frcstdate, apcp, tmax, tmin, wind_speed, wind_deg)
		else:
			# print('更新中')
			data = WeatherData(province, city, None, np.nan, np.nan, np.nan, None, None)
		results.append(data)
	return results  

def get_var(string) ->(list, list):
	rain = 0.0
	weather = string
	if "雨" not in weather and "雪" not in weather:
		rain = 0.0
	elif "大暴" and "特大暴" in weather:
		rain = (175.0 + 299.9) / 2
	elif ("大暴" in weather):
		rain = (100.0 + 249.9) / 2
	elif "暴雨转大暴雨" in weather:
		rain = (75.0 + 174.9) / 2
	elif ("暴" in weather) and ("大" not in weather):
		rain = (50.0 + 99.9) / 2
	elif "大" and "暴" in weather:
		rain = (38.0 + 74.9) / 2
	elif ("大" in weather)and ("中" not in weather):
		rain = (25.0 + 49.9) / 2
	elif "中" and "大" in weather:
		rain = (17.0 + 37.9) / 2
	elif ("中" in weather) and ("小" not in weather):
		rain = (10.0 + 24.9) / 2
	elif "小" and "中" in weather:
		rain = (5.0 + 16.9) / 2
	else:
		rain = (0.1 + 9.9) / 2
	return rain

def merge_dic(result_15days):
	jsonString = {}
	tmax = []
	tmin = []
	apcp = []
	for day in result_15days:
		if day.apcp != None:
			tmax.append(float(day.tmax))
			tmin.append(float(day.tmin))
			apcp.append(float(day.apcp))
		else:
			tmax.append(np.nan)
			tmin.append(np.nan)
			apcp.append(np.nan)
	jsonString[day.province + " " + day.city] = {"tmax": tmax, "tmin": tmin, "apcp": apcp}
	return jsonString

def DB_insert(table_name, results):
	conn = psycopg2.connect(database="farmlanddb", user="guoanboyu", password="gaby123")
	cur = conn.cursor()
	sqltmp = "insert into %s (province, city, datetime, apcp, tmax, tmin, wind_speed, wind_deg) \
			values('{province}','{city}','{datetime}','{apcp}','{tmax}','{tmin}','{wind_speed}','{wind_deg}');"%table_name
	for day in results:
		sql = sqltmp.format(province=day.province,city=day.city,datetime=day.frcstdate,apcp=day.apcp,\
							tmax=day.tmax,tmin=day.tmin,wind_speed=day.wind_speed,wind_deg=day.wind_deg)
		try:
			cur.execute(sql)
		except Exception as err:
			conn.rollback()
			print (err)
	conn.commit()
	conn.close()

def DB_delete(table_name):
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

if __name__ == '__main__':
	DB_delete('f2345_data')        #清空数据库
	city_url,city_name = Get_2345_cityurl()
	Get_2345_forcastdata(city_url, city_name,'f2345_data')
