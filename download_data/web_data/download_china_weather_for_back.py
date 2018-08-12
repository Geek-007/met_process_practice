# -*- coding: utf-8 -*-
import io 
import re
import json
import psycopg2
from lxml import etree
import requests
import os,sys
import pandas as pd
import datetime,time
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8') #改变标准输出的默认编码  


class Weather_data(object):
	"""

	"""
	def __init__(self, frcstdate, msg, tmax, tmin, wind_speed, wind_deg, fine_frcst):
		"""
		:param frcstdate:      An integer of datetime represent the forecast date
		:param msg:            A string represent the weather condition
		:param tmax:           A string represent the maximum air temperature
		:param tmin:           A string represent the minimum air temperature
		:param wind_speed:     A string represent the direction of wind
		:param wind_deg:       A string represent the speed of wind
		:param fine_frcst:     A
		"""
		self.frcstdate     = frcstdate
		self.msg           = msg
		self.tmax          = tmax
		self.tmin          = tmin
		self.wind_speed    = wind_speed
		self.wind_deg      = wind_deg
		self.fine_frcst    = fine_frcst



'''
--------------Get Openmweathermap forecast data-------------------
'''
def Convert_date(value):
   format = '%Y-%m-%d'
   value = time.localtime(value)         #格式化时间戳为本地的时间
   dt = time.strftime(format, value)     #strftime处理的类型是time.struct_time，实际上是一个tuple。strptime和localtime都会返回这个类型。
   return dt

def Get_openweathermap(lat, lon):
	host  = 'http://api.openweathermap.org/'
	appid = '1bc1f19e7fba3524f02cfbca1696c391'
	url  = host+'data/2.5/forecast/daily?lat=%s&lon=%s&cnt=15&appid=%s' %(lat, lon, appid)
	tmin = []
	tmax = []
	date = []
	clouds = []
	snow = []
	rain  = []
	speed = []
	deg = []
	try:
		respond = requests.get(url)
	except (requests.ConnectionError, requests.HTTPError ) as e:
		print("登录过程出现异常，%s" % e.error)
	else:
		html = respond.content
		json_html = json.loads(html)
		city = json_html['city']             #包含城市信息，有时所请求的经纬度可能与地名不对应
		for value in json_html['list']:
			date.append(Convert_date(value['dt']))
			tmin.append(value['temp']['min']-273.15)
			tmax.append(value['temp']['max']-273.15)
			speed.append(value['speed'])
			deg.append(value['deg'])
			clouds.append(value['clouds'])
			if "snow" in value.keys():
				snow.append(value['snow'])      #单位mm
			else:
				snow.append(0)
			if "rain" in value.keys():
				rain.append(value['rain'])
			else:
				rain.append(0)

	data = pd.DataFrame({'tmin':tmin,'tmax':tmax,'speed':speed,'deg':deg,'clouds':clouds,'snow':snow,'rain':rain},index=date)


'''
--------------Get 2345 data-------------------
'''
def Get_2345_cityurl():
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
				province_list.insert(num,(url,province))
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

def Get_2345_forcastdata(city_url,city_name):
	conn = psycopg2.connect(database="farmlanddb", user="guoanboyu", password="gaby123")
	cur = conn.cursor()
	header = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
	today_date=datetime.datetime.now()
	city_forecast = pd.DataFrame()
	forecast_tmin = []

	city_list = list(zip(city_url, city_name))
	num = 1
	for url, name in city_list:
		print(str(num) + "." + url)
		try:
			response = requests.get(url,headers=header,timeout=3)
		except Exception as e:
			print(e)
			city_list.insert(num,(url, name))
		else:
			province = name.split('-')[0]
			city = name.split('-')[1]
			num = num + 1
			soup = BeautifulSoup(response.content, "html.parser")
			results_15days = []
			# 当天及未来6天预报
			tags = soup.select('div[class="week week_day7"] li')
			for tag in tags:
				for child in tag.descendants:
					if ('class="blue"' in str(child)): tmin = (child.string)
					if ('class="red"' in str(child)): tmax = (str(child.string).split('℃')[0])
				for string in tag.stripped_strings:
					if '月' in string: date = string
					if ('晴' in string) or ('云' in string) or ('阴' in string) or ('雨' in string): msg = string
					if '风' in string: 
						wind_speed = str(string).split(' ')[1]
						wind_deg   = str(string).split(' ')[0]
				dt = datetime.datetime(today_date.year, int(date[:-1][:2]), int(date[:-1][3:5]))
				results_15days.append({'province':province, 'city':city, 'frcstdate': dt, 'tmin': tmin, 'tmax': tmax, 'wind_speed': wind_speed, 'wind_deg': wind_deg, 'msg': msg})
			# 未来7-15天预报
			tags = soup.select('div[class="week week_day8"] li')
			for tag in tags:
				for child in tag.descendants:
					if ('class="blue"' in str(child) and '周' not in str(child)): 
						tmin = (child.string)
					else:
						tmin = None
					if ('class="red"' in str(child) and '周' not in str(child)): 
						tmax = (str(child.string).split('℃')[0])
					else:
						tmax = None
				for string in tag.stripped_strings:
					if '月' in string: date = string
					if ('晴' in string) or ('云' in string) or ('阴' in string) or ('雨' in string): 
						msg = string
					else:
						msg = None
					if '风' in string: 
						wind_speed = str(string).split('风')[1]
						wind_deg   = str(string).split('风')[0]+"风"
					else:
						wind_deg = None
						wind_speed = None
				dt = datetime.datetime(today_date.year, int(date[:-1][:2]), int(date[:-1][3:5]))
				results_15days.append({'province':province, 'city':city, 'frcstdate':dt, 'tmin':tmin, 'tmax':tmax, 'wind_speed':wind_speed, 'wind_deg':wind_deg, 'msg':msg})    #一个城市15天的结果

			sqltmp = "insert into f2345_data (province,city,datetime, tmax, tmin, weather, wind_speed, wind_deg) values('{province}','{city}','{datetime}','{tmax}','{tmin}','{weather}','{wind_speed}','{wind_deg}');"
			c = conn.cursor()
			for r in results_15days:
				if r['tmax'] != None:
					sql = sqltmp.format(province=r['province'],city=r['city'],datetime=r['frcstdate'],tmax=r['tmax'],tmin=r['tmin'],weather=r['msg'],wind_speed=r['wind_speed'],wind_deg=r['wind_deg'])
					# sql = "select * from f2345_data where datetime='%s';"%dt
					#print (sql)
					try:
						c.execute(sql)
						# row = c.fetchall()
						# print(row)
					except Exception as err:
						conn.rollback()
						print (err)
					conn.commit()
				else:
					pass
	conn.close()
	# 		city_forecast[name] = results_15days            #所有城市的结果
	# city_forecast.T.to_csv(r'/home/guoanboyu/Project/GFS/data/forecast_2345.csv')


'''
--------------Get tianqi data-------------------
'''
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
				print(province_name+city.get_text())
				city_name.append(province_name+"-"+city.string)
				city_url.append(city['href'])
		print(len(city_name),len(city_url))
		return city_url,city_name                 #3223个城市

def Get_tianqi_forcastdata(city_url, city_name):
	header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
	today_date=datetime.datetime.now()
	city_forecast = pd.DataFrame()
	
	city_list = list(zip(city_url, city_name))
	num = 1
	for url,name in city_list[:]:
		province = name.split('-')[0]
		city = name.split('-')[1]
		print(str(num) + "." + url)
		try:
			response = requests.get(url,headers=header,timeout=3)
		except Exception as e:
			print(e)
			city_list.insert(num, (url, name))
		else:
			num = num + 1
			soup = BeautifulSoup(response.content, "html.parser")
			results_15days = [0]*15
			# 当天及未来15天预报
			tags = soup.select('div[class="table_day15"]')  #15个tags代表15天
			for day_num, tag in enumerate(tags[:]):           #每一天循环一次
				for child in tag.descendants:
					if ('class="cmax"' in str(child)):
						tmax = (str(child.string).split('℃')[0])
					if ('class="cmin"' in str(child)):
						tmin = (str(child.string).split('℃')[0])
				# print tmax,tmin
				for string in tag.stripped_strings:             #输出的字符串中可能包含了很多空格或空行,使用 .stripped_strings 可以去除多余空白内容
					if '月' in string: date = string
					if ('晴' in string) or ('云' in string) or ('阴' in string) or ('雨' in string): msg = string
					if '风' in string: 
						wind_speed = str(string).split(' ')[1]
						wind_deg = str(string).split(' ')[0]
				dt = datetime.datetime(today_date.year, int(date[:-1][:2]), int(date[:-1][3:5]))
				print(dt)
				results_15days.append({'province':province, 'city':city, 'frcstdate':dt, 'tmin':tmin, 'tmax':tmax, 'wind_speed':wind_speed, 'wind_deg':wind_deg, 'msg':msg})    #一个城市15天的结果

			sqltmp = "insert into tianqi_data (province,city,datetime, tmax, tmin, weather, wind_speed, wind_deg) values('{province}','{city}','{datetime}',{tmax},{tmin},'{weather}','{wind_speed}','{wind_deg}');"
			c = conn.cursor()
			for r in results_15days:
				sql = sqltmp.format(province=r['province'],city=r['city'],datetime=r['frcstdate'],tmax=r['tmax'],tmin=r['tmin'],weather=r['msg'],wind_speed=r['wind_speed'],wind_deg=r['wind_deg'])
				# sql = "select * from f2345_data where datetime='%s';"%dt
				#print (sql)
				try:
					c.execute(sql)
					# row = c.fetchall()
					# print(row)
				except Exception as err:
					conn.rollback()
					print (err)
				conn.commit()
	conn.close()
	# city_forecast.T.to_csv(r'/home/guoanboyu/Project/GFS/data/forecast_tianqi.csv')


'''
--------------Get China weather data-------------------
'''
def get_cities_url(forecast_url):
	city_url = []
	city_url_15d = []
	city_name = []
	header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
	try:
		response = requests.get(forecast_url, headers=header, timeout=3)
	except Exception as e:
		print(e)
		response = requests.get(forecast_url, headers=header, timeout=3)
	else:
		# 获取各中国各区域url    ['华北', '东北', '华南', '西北', '西南', '华东', '华中']
		region_url = []
		region_name = []
		soup = BeautifulSoup(response.content, "html.parser")
		china = soup.select('div[class="maptabboxinBox"] h4 a')
		for region in china:
			region_url.append(region['href'])
			region_name.append(region.get_text())
		city_url  = []
		city_url_15d = []
		city_name = []
		num = 1
		for url in region_url[:]:
			try:
				print(str(num)+'.'+url)
				response = requests.get(url, headers=header, timeout=3)
			except Exception as e:
				print(e)
				region_url.insert(num, url)
			else:
				num = num + 1
				soup = BeautifulSoup(response.content, "html.parser")
				all_cities = soup.select('td[width="83"] a')
				for city in all_cities:
					city_url.append(city['href'])
					city_url_15d.append(city['href'][:-16]+"15d"+city['href'][-16:])
					city_name.append(city.get_text())
		city_url = list(set(city_url))
		city_url_15d = list(set(city_url_15d))
		city_name = list(set(city_name))
		print(len(city_url))
		return city_url,city_url_15d,city_name     #

def get_citycode(path):
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

def download_7days_data(response, date):
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
				precipitation = frcsttime.split(',')[2]
				tmp = frcsttime.split(',')[3]
				wind = frcsttime.split(',')[4] + " " + frcsttime.split(',')[5]
				day_refine.append({"time": time, "precipitation": precipitation, "tmp": tmp, "wind": wind})
			day7_refine.append(day_refine)
	else:
		day7_refine.append(None)
	# 获取前7天预报
	tags = soup.select('ul[class="t clearfix"] li')
	for day_num, tag in enumerate(tags[:]):  # 一个tag一天
		day = BeautifulSoup(str(tag), "html.parser")
		frcstdate = date + datetime.timedelta(days=day_num)  #day.select('h1')[0].get_text()
		precipitation = day.select('p[class="wea"]')[0].get_text()
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
		if day7_refine == None:
			# results_7days.append(Weather_data(frcstdate,precipitation,tmax,tmin,wind_speed,wind_deg,day7_refine[day_num]))
			results_7days.append({'frcstdate': frcstdate, 'precipitation': precipitation, 'tmax': tmax, 'tmin': tmin,
								  'wind_speed': wind_speed, 'wind_deg': wind_deg, 'fine_frcst':day7_refine[day_num]})
		else:
			results_7days.append({'frcstdate': frcstdate, 'precipitation': precipitation, 'tmax': tmax, 'tmin': tmin,
								  'wind_speed': wind_speed, 'wind_deg': wind_deg})
	return(results_7days)

def download_15days_data(response, date):
	results_15days = []
	soup = BeautifulSoup(response.content, "html.parser")
	tags = soup.select('ul[class="t clearfix"] li')  # 15个tags代表15天
	for day_num,tag in enumerate(tags[:]):  # 一个tag一天
		day = BeautifulSoup(str(tag), "html.parser")
		frcstdate = date + datetime.timedelta(days=day_num+7)  #day.select('span[class="time"]')[0].get_text()
		precipitation = day.select('span[class="wea"]')[0].get_text()
		tmax = day.select('span[class="tem"]')[0].get_text().split("/")[0]
		tmin = day.select('span[class="tem"]')[0].get_text().split("/")[1]
		wind_speed = day.select('span[class="wind1"]')[0].get_text()
		wind_deg = day.select('span[class="wind"]')[0].get_text()
		# results_15days.append(Weather_data(frcstdate,precipitation,tmax,tmin,wind_speed,wind_deg,None))
		results_15days.append({'frcstdate': frcstdate, 'precipitation': precipitation, 'tmax': tmax, 'tmin': tmin,
								'wind_speed': wind_speed, 'wind_deg': wind_deg})
	return (results_15days)

def download_chinaweatherdata():
	date = datetime.datetime.now().date()
	forecast_url = 'http://www.weather.com.cn/static/html/weather.shtml'
	path = 'E:\GAGO\GFS\citycode.txt'
	city_url, city_url_15d, city_name= get_citycode(path)
	print(len(city_name))    

	num_7d = 1
	num_15d = 1
	result_7days = []
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
			result = download_7days_data(response, date)
			result_7days.append(result)
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

	weather_results = []
	city_forecast = pd.DataFrame()
	print(len(result_7days),len(result_15days),len(city_name))
	for day7,day15,name in list(zip(result_7days, result_15days, city_name)):
		# weather_results.append(day7 + day15)
		weather_results = day7 + day15
		print(weather_results)
		city_forecast[name] = weather_results
	city_forecast.T.to_csv('/home/guoanboyu/forecast_system/China_Weather/ChinaWeather.csv')
	# print(weather_results[0][1]._Weather_data__frcstdate)

def get_cityurl():
	url_part = 'http://www.weather.com.cn/weather/.shtml'
	citycode = 101010100
	while 101010100 <= citycode < 101050101:
		url = url_part[:-6]+str(citycode)+url_part[-6:]
		try:
			response = requests.get(url, timeout=3)
		except Exception as e:
			print(e)
			citycode = citycode
		else:
			soup = BeautifulSoup(response.content, 'html.parser')
			if len(soup.select('div[class="crumbs fl"]')) !=0:
				city = soup.select('div[class="crumbs fl"] span')[-1].get_text()
				if city == "城区" and len(soup.select('div[class="crumbs fl"] a')) ==2:
					city = soup.select('div[class="crumbs fl"] a')[1].get_text()
				elif city == "城区" and len(soup.select('div[class="crumbs fl"] a')) ==1:
					city = soup.select('div[class="crumbs fl"] a')[0].get_text()
				print("citycode:%s，cityname:%s"%(citycode,city))
				with open(r'E:\GAGO\GFS\citycode1.txt', 'a') as f:
					f.writelines(str(citycode) + "=" + str(city) + "\n")
				citycode = citycode + 1
			else:
				print("citycode:%s, 不存在"%(citycode))
				citycode = int(str(citycode)[:-1]+"0")
				citycode = citycode + 10

	citycode = 101050101
	while 101050101 <= citycode <= 101340406:
		url = url_part[:-6]+str(citycode)+url_part[-6:]
		try:
			response = requests.get(url, timeout=3)
		except Exception as e:
			print(e)
			citycode = citycode
		else:
			soup = BeautifulSoup(response.content, 'html.parser')
			if len(soup.select('div[class="crumbs fl"]')) !=0:
				city = soup.select('div[class="crumbs fl"] span')[-1].get_text()
				if city == "城区" and len(soup.select('div[class="crumbs fl"] a')) ==2:
					city = soup.select('div[class="crumbs fl"] a')[1].get_text()
				elif city == "城区" and len(soup.select('div[class="crumbs fl"] a')) ==1:
					city = soup.select('div[class="crumbs fl"] a')[0].get_text()
				print("citycode:%s，cityname:%s"%(citycode,city))
				with open(r'E:\GAGO\GFS\citycode1.txt', 'a') as f:
					f.writelines(str(citycode) + "=" + str(city) + "\n")
				citycode = citycode + 1
			else:
				print("citycode:%s, 不存在"%(citycode))
				citycode = int(str(citycode)[:-1]+"1")
				citycode = citycode + 10


if __name__ == '__main__':
	# lat = 49.0
	# lon = 126.0
	# Get_openweathermap(lat, lon)

	city_url,city_name = Get_2345_cityurl()
	Get_2345_forcastdata(city_url,city_name)

	# city_url, city_name = Get_tianqi_cityurl()
	# Get_tianqi_forcastdata(city_url, city_name)

	# download_chinaweatherdata()
