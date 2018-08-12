#!/usr/bin/env python
#coding=utf-8

import glob
import os
import WMTX
import MOSAIC

def main():
	left = input("请输入开始经度(-180~180)：")
	while float(left) > float(180) or float(left) < float(-180):
		left = input("输入开始经度不在范围内，请重新输入(-180~180)：")

	right = input("请输入结束经度(-180~180)：")
	while float(right) >= float(180) or float(right) < float(-180):
		right = input("输入结束经度不在范围内，请重新输入(-180~180)：")

	bottom = input("请输入开始纬度(-90~90)：")
	while float(bottom) > float(90) or float(bottom) < float(-90):
		bottom = input("输入开始纬度不在范围内，请重新输入(-90~90)：")

	top = input("请输入结束纬度(-90~90)：")
	while float(top) > float(90) or float(top) < float(-90):
		top = input("输入结束纬度不在范围内，请重新输入(-90~90)：")

	tilematrix = input("请输入等级(0-15)：")
	while int(tilematrix) > 15 or int(tilematrix) < 0:
		tilematrix = input("输入等级不在范围内，请重新输入(0-15)：")
	# 传入开始和结束经纬度和等级
	mapclass = WMTX.MapClass(left, right, bottom, top, tilematrix)
	mapclass.run()
	files=glob.glob("./map_png/*.png")
	for file in files:
		file_name=os.path.basename(file)
		newRasterfn = './map_tiff/'+file_name[:-4]+'.tiff'
		print('convert %s to tiff '% file_name)
		mosaic = MOSAIC.Mosaic()
		mosaic.run(newRasterfn, file)

if __name__ == "__main__":
	main()