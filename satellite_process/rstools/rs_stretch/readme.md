#Readme 
标签：图像拉伸
---
1. 使用说明：
---
功能：实现遥感图像的最大最小值拉伸、一定百分比拉伸、直方图均衡化、局部自适应直方图均衡化。
---
运行示例：python im_stretch.py <input_fname> <strech_modle> <output_fname> [--percent=<strech_percent>]

The <input_fname> argument must be the path to a GeoTIFF image.
The <strech_modle> argument must be one of the strech_modles 'max_min_strech' 'percent_strech' 'equalize_hist' 'equalize_adapthist'
The <output_fname> argument must be a filename where the classification will be saved (GeoTIFF format).
If [--percent=<strech_percent>] is given ,it mast be a  positive integer.such as if strech percent is 2%,then <strech_percent>=2

2.运行环境：
---
ubuntu 系统 python 3.5
依赖包：见requirements.txt
