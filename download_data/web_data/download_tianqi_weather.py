# -*- coding: utf-8 -*-
import io 
import re
import json,sys
import psycopg2
from lxml import etree
import requests
import datetime,time
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8') #改变标准输出的默认编码  

class WeatherData(object):
	def __init__(self,  province:str, city:str, frcstdate:int, weather:str,\
						tmax:int, tmin:int, wind_speed:str, wind_deg:str):
		self.province      = province
		self.city          = city
		self.frcstdate     = frcstdate
		self.weather       = weather
		self.tmax          = tmax
		self.tmin          = tmin
		self.wind_speed    = wind_speed
		self.wind_deg      = wind_deg

def Get_tianqi_cityurl():
	city_url = []
	city_name = []
	host = 'http://tianqi.com/'
	header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
	try:
		response = requests.get(host+"15tianqi",timeout=10)     #获取15天预报
	except Exception as e:
		print(e)
	else:
		soup = BeautifulSoup(response.content.decode('gb2312', 'ignore'), "html.parser")    #先确保html经过了解码，否则会出现解析出错情况。
		provinces = soup.select('dl[class="list_jd"]')
		for province in provinces[:]:
			province = BeautifulSoup(str(province), "html.parser")
			if len(province.select('dt a')[0].get_text()) == 10:
				province_name = province.select('dt a')[0].get_text()[:3]
			else:
				province_name = province.select('dt a')[0].get_text()[:2]
			for city in province.select('li a'):
				# print(province_name+city.get_text())
				city_name.append(province_name+"-"+city.string)
				city_url.append(city['href'])
		print(len(city_name),len(city_url))
		print("1.Get all cities url")
		return city_url,city_name                 #3223个城市

def Get_tianqi_forcastdata(city_url, city_name, DB_table):
	header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}	
	city_list = list(zip(city_url, city_name))
	num = 1
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
			# 当天及未来15天预报
			result_15days = Parse_forecast_result(soup, 'div[class="table_day15"]', province, city)   #一个城市15天的结果
			DB_insert(DB_table, result_15days)

def Parse_forecast_result(soup, tag, province, city):
	results = []
	today = datetime.datetime.now()
	days = soup.select(tag)
	for day in days:
		tmp = []
		#解析温度数据
		for child in day.descendants:
			if ('℃' in str(child) and str(child.string)!='None'): 
				tmp.append(child.string.split('℃')[0])
		# print(tmp)
		if "" in tmp:
			tmin = -999
			tmax = -999
		else:
			tmax = max(list(map(int, tmp)))
			tmin = min(list(map(int, tmp)))
		#解析天气数据
		if day.select('li')[2].get_text().split('：')[1] != "":
			weather =  day.select('li')[2].get_text().split('：')[1]
		else:
			weather = None
		#解析风、日期数据
		for string in day.stripped_strings:
			if '风' in string and '刮风' not in string: 
				wind_speed = str(string).split(' ')[1]
				wind_deg   = str(string).split(' ')[0]
			elif '刮风' in string:
				wind_speed = str(string).split(' ')[0]
				wind_deg   = None
			else:
				wind_speed = None
				wind_deg   = None				
			if '月' in string: 
				date = str(string)
		frcstdate = datetime.datetime(today.year, int(date.split('月')[0]), int(date.split('月')[1].split('日')[0]))
		# print(frcstdate, tmax, tmin, weather, wind_speed, wind_deg)
		#生成数据结构，并生成15天的数据list
		data = WeatherData(province, city, frcstdate, weather, tmax, tmin, wind_speed, wind_deg)
		results.append(data)
	return results			

def DB_insert(table_name, results):
	conn = psycopg2.connect(database="farmlanddb", user="guoanboyu", password="gaby123")
	cur = conn.cursor()
	sqltmp = "insert into %s (province, city, datetime, weather, tmax, tmin, wind_speed, wind_deg) \
			values('{province}','{city}','{datetime}','{weather}','{tmax}','{tmin}','{wind_speed}','{wind_deg}');"%table_name
	for day in results:
		sql = sqltmp.format(province=day.province,city=day.city,datetime=day.frcstdate,weather=day.weather,\
							tmax=day.tmax,tmin=day.tmin,wind_speed=day.wind_speed,wind_deg=day.wind_deg)
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
	DB_delete('tianqi_data')
	city_url,city_name = Get_tianqi_cityurl()
	Get_tianqi_forcastdata(city_url, city_name, "tianqi_data")