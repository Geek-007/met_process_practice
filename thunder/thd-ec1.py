#coding:utf-8
import numpy as np
import glob
# from matplotlib import pyplot as plt
from scipy.optimize import fsolve

from netCDF4 import Dataset


lonslice = slice(192, 229)
latslice = slice(104, 129)


# def get_t(l):
#     data=f.variables["t"][t, level == l, :, :][0]
#     data-=273.15
#     return data
#
# def get_rh(l):
#     data = f.variables["r"][t, level == l, :, :][0]
#     return data

def get_t(l):
    data=f.variables["t"][0, level == l, latslice, lonslice][0]
    data-=273.15
    return data

def get_rh(l):
    data = f.variables["r"][0, level == l, latslice, lonslice][0]
    return data

def get_td(l):
    t=get_t(l)
    rh=get_rh(l)
    a=np.where(t>-30,17.269,17.67)
    b=np.where(t>-30,237.29,243.5)
    es=6.112*np.exp(a*t/(t+b))
    rh[rh<1]=1

    e=rh*es/100
    c=np.log(e/6.112)
    td=b*c/(a-c)
    return td


def get_si():
    t850=get_t(850)
    td850=get_td(850)
    t500=get_t(500)

    pp=500.0

    si=9999*np.ones_like(t850)
    for i in range(si.shape[0]):
        for j in range(si.shape[1]):
            if t850[i,j]>80 or t850[i,j]<=-100 or td850[i,j]>80 or td850[i,j]<=-110:
                continue

            es=6.112*np.exp(17.67*t850[i,j]/(t850[i,j]+243.5))
            e=6.112*np.exp(17.67*td850[i,j]/(td850[i,j]+243.5))

            r=622*e/(850.0-e)
            u=e/es*100
            tk=t850[i,j]+273.15
            tlcl=55.0+1/(1/(tk-55.0)-np.log(u/100)/2840)

            thse=tk*((1000.0/850.0)**(0.2854*(1-0.28*0.001*r)))*np.exp((3.376/tlcl-0.00254)*r*(1+0.81*0.001*r))
            plcl=850*((tlcl/tk)**(1004.07/287.05))
            if plcl<500:
                te500=tk*((500.0/850.0)**(287.05/1004.07))-273.15
            else:
                def pt500(x):
                    t1=x[0]
                    e = 6.112 * np.exp(17.67 * t1 / (t1 + 243.5))
                    r = 622 * e / (pp - e)
                    thse1 = (t1 + 273.15) * (1000.0 / pp) ** (0.2854 * (1 - 0.28 * 0.001 * r)) * np.exp(
                        (3.376 / tlcl - 0.00254) * r * (1 + 0.81 * 0.001 * r))
                    return [thse1-thse]

                t1=tlcl-273.15
                te500=fsolve(pt500,[t1],xtol=1e-5)[0]

            si[i,j]=t500[i,j]-te500
    return si


def get_a():
    t850 = get_t(850)
    td850 = get_td(850)
    t700 = get_t(700)
    td700 = get_td(700)
    t500 = get_t(500)
    td500 = get_td(500)

    ttd850 = t850 - td850
    ttd700 = t700 - td700
    ttd500 = t500 - td500

    a = t850 - t500 - ttd850 - ttd700 - ttd500
    return a


def si_index():
    si=get_si()
    si=np.where(si<=0,1,0)
    return si

def ki_index():
    t850=get_t(850)
    t500=get_t(500)
    t700=get_t(700)
    td850=get_td(850)
    td700=get_td(700)

    k=(t850-t500)+td850-(t700-td700)
    ki=np.where(k>=33,1,0)
    return ki

def dt_index(level):
    t=get_t(level)
    td=get_td(level)
    dt=t-td
    dti=np.where(dt<=3,1,0)
    return dti

def dt85_index():
    t850=get_t(850)
    t500=get_t(500)
    dt85=t850-t500
    # print(dt85)
    dt85i=np.where(dt85>=23.0,1,0)
    return dt85i

# def cape_index():
#     cape=get_cape()
#     capei=np.where(cape>=500,1,0)
#     return capei
#
# def w_index():
#     w=get_w850()
#     wi=np.where(w<=0,1,0)
#     return wi


def a_index():
    a = get_a()
    ai = np.where(a > 10.0, 1, 0)
    return ai

def calc_thdstrm():
    k1 = ki_index()
    k2 = si_index()
    k3 = a_index()
    k4 = dt_index(700)
    k5 = dt_index(850)
    k6 = dt_index(925)
    k7 = dt85_index()
    thdstrm = 110.0 + 154 * k1 + 142 * k2 + 61 * k3 + 146 * k4 + 131 * k5 + 30 * k6 + 97 * k7
    thdstrm /= 10
    print(thdstrm)
    return thdstrm

def draw_boundary(ax):
    import sys
    import shapefile
    if sys.platform=="win32":
        sf = shapefile.Reader(r'C:\workspace\Budweiser\shp\bou2_4l.shp')
    else:
        sf = shapefile.Reader(r'/home/forecastcenter/shapefile/bou2_4l.shp')
    shapes = sf.shapes()
    for item in shapes:
        ps = np.array(item.points)
        ax.plot(ps[:, 0], ps[:, 1], 'k', linewidth=0.4)

def ecmwf():
    dt = "20160630"
    f = Dataset(r"ec\%s.nc" % dt, "r")
    level = f.variables["level"][:]

    ncf = Dataset("td_" + dt + ".nc", "w")
    ncf.createDimension("Time", 4)
    ncf.createDimension("Lat", 49)
    ncf.createDimension("Lon", 73)

    tim = ncf.createVariable("Time", "i4", ("Time"))
    tim[:] = f.variables["time"][:]
    tim.units = f.variables["time"].units
    tim.long_name = f.variables["time"].long_name
    tim.calendar = f.variables["time"].calendar

    lon = ncf.createVariable("Lon", "f4", ("Lon",))
    lon[:] = np.linspace(108, 117, 73)

    lat = ncf.createVariable("Lat", "f4", ("Lat",))
    lat[:] = np.linspace(34, 28, 49)

    tp = ncf.createVariable("TP", "f4", ("Time", "Lat", "Lon",))
    tp.description = "THUNDER POTENTIAL"
    tp.coordinates = "XLONG XLAT XTIME"

    tdrecord = ncf.createVariable("TDT", "f4", ("Time", "Lat", "Lon",))
    tdrecord.description = "THUNDER FREQUENCY RECORD"
    tdrecord.coordinates = "XLONG XLAT XTIME"
    tdrecord[:] = np.load("tdgrid\\%s.npy" % dt)

    for t in range(4):
        thdstrm = calc_thdstrm()
        tp[t, :] = thdstrm.astype(np.float32)

    ncf.close()



if __name__ == "__main__":
    ec_dir = "/home/forcastcenter/ec/ec/"
    ec_file = sorted(glob.glob(ec_dir + "*20170501*"))
    print(ec_file[0])
    f = Dataset(ec_file[0] , "r")
    level = f.variables["level"][:]
    thdstrm = calc_thdstrm()
    # print(thdstrm)
