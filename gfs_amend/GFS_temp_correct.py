# -*- coding: utf-8 -*-
import pandas as pd
import psycopg2
import requests
import json
import datetime
import numpy as np

# lat纬度，lon经度 , days天数, var变量

class Grid(object):
	def __init__(self,lat:float,lon:float,day:int,var:str):
		self.lat = lat
		self.lon = lon
		self.day = day
		self.var = var

	def request_api(self)->(list):
		header = {"Token": "gdc_longrun"}
		host = 'https://api.gagogroup.cn/api/v2/'
		url = host + '/weather/forecast?lon=%s&lat=%s&hrs=%s&features=[%s]'%(self.lon, self.lat, (self.day-1)*24, self.var)
		try:
			respond = requests.get(url, headers=header)
		except Exception as e:
			print(e)
		else:
			forecastWeather = json.loads(respond.content)['data']['forecastWeather']
		return forecastWeather

	def gfs_forcastdata(self)->(list, list):
		forecastWeather = self.request_api()
		date = datetime.datetime.now().date() 
		var_result = {}
		for value in forecastWeather:
			frcsttime = datetime.datetime.strptime(str(value['date']), "%Y-%m-%dT%H:%M:%S.000Z") + datetime.timedelta(hours=8)
			frcsttime = frcsttime.strftime("%Y-%m-%d")
			# 最高气温
			if frcsttime in var_result.keys():
				var = var_result[frcsttime]
				var.append(float(value[self.var]))
			else:
				var_result[frcsttime] = [float(value[self.var])]
		if self.var == "tmax":
			var = list(map(max, var_result.values()))
		elif self.var == "tmin":
			var = list(map(min, var_result.values()))
		return(var)

	def select_city(self):
		province, city, lat, lon, height = get_city()
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

	def correct_gfs(self):
		var_o = self.gfs_forcastdata()
		cities = self.select_city()
		today = datetime.datetime.now().date()
		filename = '/home/guoanboyu/Project/GFS/data/f2345_%s.csv'%(today)
		# date = datetime.datetime.strptime(str(date) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
		df = pd.read_csv(filename, header=None, names=["province", "city", "datetime", "tmax", "tmin", "apcp"])
		# a = df.loc[(df["province"] == "%s"%'黑龙江') & (df["city"] == "%s"%'漠河')]
		# print(a) 

		#从数据库中读取符合标准的城市
		# conn = psycopg2.connect(database="farmlanddb", user="guoanboyu", password="gaby123")
		# cur = conn.cursor()

		var_cities = []
		for city in cities:
			# sql = "select province,city,datetime,%s from %s where province='%s' and city='%s';" \
			# 		%(self.var, 'f2345_data', city.split(" ")[0], city.split(" ")[1])
			# cur.execute(sql)
			# days_f2345 = cur.fetchall()
			#处理不为空的城市数据
			# if len(days_f2345) != 0:
			#提取每个城市15天的最高最低气温数据
			# for i in range(self.day):
			# frcstdate = datetime.datetime.strptime(str(today + datetime.timedelta(days = i)) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
			f2345_var = df.loc[(df["province"] == "%s"%city.split(" ")[0]) & (df["city"] == "%s"%city.split(" ")[1]), "tmax"].values
			frcstdate = df.loc[(df["province"] == "%s"%city.split(" ")[0]) & (df["city"] == "%s"%city.split(" ")[1]), "datetime"].values
			# f2345_var = f2345_var.values
			print(f2345_var)	
			# f2345_var = get_var(frcstdate, days_f2345)
			var_cities = f2345_var.tolist()
			date = frcstdate.tolist()
		var_cities.append(var_o)
		#对符合筛选标准的城市每天的气温求平均
		var_amend = list(map(np.nanmean, zip(*var_cities)))

		results = {}
		forecastWeather = []
		for var, frcstdate in list(zip(var_amend, date)):
			frcstdate = frcstdate - datetime.timedelta(hours=8)
			frcstdate = frcstdate.strftime("%Y-%m-%dT%H:%M:%S.000Z")
			forecastWeather.append({'date': frcstdate, self.var: round(float(var) * 100) / 100})
			results.update({"data": {"forecastWeather": forecastWeather}})
		results = json.dumps(results)
		return results

def get_var(frcstdate, data) ->(list, list):
	#若某时刻不存在温度数据则赋值为-999
	result_var = -999
	for day in data:
		if str(day[2])[:10] == str(frcstdate)[:10]:
			result_var = day[3]
			break
	if result_var == -999:
		result_var = np.nan
	return result_var

def get_city() ->(list, list, list, list, list):
	filename = '/home/guoanboyu/Project/china_region/station_edit_over_01(1229add_194_remark).csv'
	data     = pd.read_csv(filename)
	province = data['ok'].tolist()
	city     = data['name'].tolist()
	lat      = data['lat'].tolist()
	lon      = data['lon'].tolist()
	height   = data['heigh'].tolist()
	return province, city, lat, lon, height

if __name__ == '__main__':
	grid = Grid(52.96666667, 122.5166667, 15, 'tmax')
	begin = datetime.datetime.now()
	results = grid.correct_gfs()
	# print(results)
	end = datetime.datetime.now()
	print(end - begin)
