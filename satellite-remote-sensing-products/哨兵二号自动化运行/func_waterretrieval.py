#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2020/10/26 16:28:19
@Author  :   zhaohui li
@Contact :   shuju3@tech-5d.com
@功能: 水质反演
'''

import os
from osgeo import  gdal
from osgeo import osr
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from scipy.optimize import curve_fit
from scipy.stats.stats import pearsonr
# from sklearn.metrics import r2_score

BANDS=['B','G','R','NIR']
Methods=['singleband','exp','minus','divide','minus_divide','log']
Methods_table=['BandX','e(BandX)','BandY-BandX','BandY/BandX','(BandY-BandX)/(BandY+BandX)','ln(BandY)/BandX']
titles=['BandX','$\\rm {e^{BandX}}$','BandY-BandX',"$\\rm \\frac{BandY}{BandX}$",'$\\rm \\frac{BandY-BandX}{BandY+BandX}$','$\\rm \\frac{ln^{BandY}}{BandX}$']
# axis_font = {'fontname': 'Arial', 'size': 15}
title_font = {'fontname': 'SimHei', 'size': 18, 'color': 'black',
              'weight': 'normal', 'verticalalignment': 'bottom'}


class rasterinfo():
    '''
    tif信息
    '''
    def __init__(self,rows,cols,n_bands,geo_transform,proj,bands_data,band_idx):
        self.rows=rows
        self.cols=cols
        self.n_bands=n_bands
        self.transforms=geo_transform
        self.projection=proj
        self.dataarray=bands_data / 10000.0
        self.b_index=band_idx[0]
        self.g_index=band_idx[1]
        self.r_index=band_idx[2]
        self.nir_index=band_idx[3]

def read_tif_multiband(raster_data_path,band_idx):
    raster_dataset=gdal.Open(raster_data_path,gdal.GA_ReadOnly)
    geo_transform=raster_dataset.GetGeoTransform()
    proj = raster_dataset.GetProjection()
    bands_data=[]
    for b in range(1,raster_dataset.RasterCount+1):
        band=raster_dataset.GetRasterBand(b)
        bands_data.append(band.ReadAsArray())
    
    bands_data=np.dstack(bands_data)
    rows,cols,n_bands=bands_data.shape
    del raster_dataset,band
    raster=rasterinfo(rows,cols,n_bands,geo_transform,proj,bands_data,band_idx)
    return raster

def write_geotiff(fname,data,geo_transform,projection):
    driver=gdal.GetDriverByName("GTiff")
    rows,cols=data.shape
    dataset=driver.Create(fname,cols,rows,1,gdal.GDT_Float32)
    dataset.SetGeoTransform(geo_transform)
    dataset.SetProjection(projection)
    band=dataset.GetRasterBand(1)
    band.WriteArray(data)
    dataset=None # 关闭文件

def lonlat2geo(proj, lon, lat):
    '''
    将经纬度坐标转为投影坐标（具体的投影坐标系由给定数据确定）
    :param dataset: GDAL地理数据
    :param lon: 地理坐标lon经度
    :param lat: 地理坐标lat纬度
    :return: 经纬度坐标(lon, lat)对应的投影坐标
    '''
    prosrs = osr.SpatialReference()
    prosrs.ImportFromWkt(proj)
    geosrs = prosrs.CloneGeogCS()
    ct = osr.CoordinateTransformation(geosrs, prosrs)
    coords = ct.TransformPoint(lat, lon)
    return coords[:2]
    
def geo2imagexy(geo_transform, x, y):
    '''
    根据GDAL的六参数模型将给定的投影或地理坐标转为影像图上坐标（行列号）
    '''
    trans = geo_transform
    a = np.array([[trans[1], trans[2]], [trans[4], trans[5]]])
    b = np.array([x - trans[0], y - trans[3]])
    return np.linalg.solve(a, b)  # 使用numpy的linalg.solve进行二元一次方程的求解

def getspectral(lon,lat,raster):
    # rows,cols,n_bands,geo_transform,proj,bands_data=read_tif_multiband(filename)
    [x,y]=lonlat2geo(raster.projection, lon, lat)
    xy=geo2imagexy(raster.transforms,x,y)
    row=int(xy[1])
    col=int(xy[0])
    b=raster.dataarray[row,col,raster.b_index]
    g=raster.dataarray[row,col,raster.g_index]
    r=raster.dataarray[row,col,raster.r_index]
    nir=raster.dataarray[row,col,raster.nir_index]

    return row,col,b,g,r,nir

def getsampletable(inputtable,sheetnames,tiffile,band_idx,savepath):
    raster=read_tif_multiband(tiffile,band_idx)
    df=pd.read_excel(inputtable,sheet_name=sheetnames)
    lons=df.iloc[:,1].values
    lats=df.iloc[:,2].values
    # 获取光谱值
    sampledata=pd.DataFrame([],columns=['row','col','b','g','r','nir'])
    for i,lon in enumerate(lons):
        sampledata.loc[i,'row'],sampledata.loc[i,'col'], \
                sampledata.loc[i,'b'],sampledata.loc[i,'g'], \
                    sampledata.loc[i,'r'],sampledata.loc[i,'nir']=getspectral(lon,lats[i],raster)
        
    sampledata.to_excel(savepath+'\\sample_spectral.xlsx',sheet_name='specdata',index=False)
    return sampledata

def get_bandcom(arrayxs,method):
    '''
    arrayxs:包含光谱值的2维数组
    method:方法
    '''
    array_res=np.zeros((arrayxs.shape[1],arrayxs.shape[1],arrayxs.shape[0]))
    array_model=[['' for x in range(arrayxs.shape[1])] for x1 in range(arrayxs.shape[1])]
    if method=='minus':
        for i in range(arrayxs.shape[1]):
            for j in range(arrayxs.shape[1]):
                array_res[i][j][:]=arrayxs.iloc[:,i]-arrayxs.iloc[:,j]
                array_model[i][j]=BANDS[i]+'-'+BANDS[j]+';'+BANDS[i]+','+BANDS[j]+','+method
    elif method=='divide':
        for i in range(arrayxs.shape[1]):
            for j in range(arrayxs.shape[1]):
                array_res[i][j][:]=arrayxs.iloc[:,i]/arrayxs.iloc[:,j]
                array_model[i][j]=BANDS[i]+'/'+BANDS[j]+';'+BANDS[i]+','+BANDS[j]+','+method
    elif method=='minus_divide':
        for i in range(arrayxs.shape[1]):
            for j in range(arrayxs.shape[1]):
                array_res[i][j][:]=(arrayxs.iloc[:,i]-arrayxs.iloc[:,j])/(arrayxs.iloc[:,i]+arrayxs.iloc[:,j])
                array_model[i][j]='('+BANDS[i]+'-'+BANDS[j]+')/('+BANDS[i]+'+'+BANDS[j]+')'+';'+BANDS[i]+','+BANDS[j]+','+method
    elif method=='log':
        for i in range(arrayxs.shape[1]):
            for j in range(arrayxs.shape[1]):
                array_res[i][j][:]=list(map(np.log,arrayxs.iloc[:,i]))/arrayxs.iloc[:,j]
                array_model[i][j]='log('+BANDS[i]+')/'+BANDS[j]+';'+BANDS[i]+','+BANDS[j]+','+method
    else:
        print('method error!')
    return array_res,array_model


def getpearsonr(arrayxs,y,m):
    '''
    arrayxs:包含光谱组合值的3维数组
    y:待构建模型的水色与水质参数
    '''
    if arrayxs.ndim==3:
        array_r=np.zeros((arrayxs.shape[1],arrayxs.shape[1]))
        for i in range(arrayxs.shape[1]):
            for j in range(arrayxs.shape[1]):
                pccs=np.corrcoef(list(arrayxs[i][j][:]),list(y))
                array_r[i][j]=pccs[0][1]
        tmp=np.absolute(array_r)
        tmp_idx=np.where(tmp==np.nanmax(tmp))
        idxi,idxj=tmp_idx[0][0],tmp_idx[1][0]
        return array_r,idxi,idxj
    elif arrayxs.ndim==2 and m=='singleband':
        array_r=np.zeros(arrayxs.shape[1])
        array_model=['' for x in array_r]
        for i in range(arrayxs.shape[1]):
            pccs=np.corrcoef(list(arrayxs.iloc[:,i].values),list(y))
            array_r[i]=pccs[0][1]
            array_model[i]=BANDS[i]+';'+BANDS[i]+','+BANDS[i]+','+m
        tmp=np.absolute(array_r)
        tmp_idx=np.where(tmp==np.nanmax(tmp))
        idxi=tmp_idx[0][0]
        return array_r,array_model,idxi
    elif arrayxs.ndim==2 and m=='exp':
        array_r=np.zeros(arrayxs.shape[1])
        array_model=['' for x in array_r]
        for i in range(arrayxs.shape[1]):
            pccs=np.corrcoef(list(map(np.log,arrayxs.iloc[:,i])),list(y))
            array_r[i]=pccs[0][1]
            array_model[i]='exp('+BANDS[i]+')'+';'+BANDS[i]+','+BANDS[i]+','+m
        tmp=np.absolute(array_r)
        tmp_idx=np.where(tmp==np.nanmax(tmp))
        idxi=tmp_idx[0][0]
        return array_r,array_model,idxi

def plotheatmap(ax,r,xyticks,title):
    r=np.absolute(np.around(r,decimals=2))
    if r.ndim<2:
        r=r.reshape(1,-1)
    im=ax.imshow(r,cmap='YlGnBu',vmin=0,vmax=1)
    if r.shape[0]==1:
        ax.set_xticks(np.arange(len(xyticks)))
        ax.set_xticklabels(xyticks)
        ax.set_yticks([])
        for i in range(len(xyticks)):
            ax.text(i,0,r[0][i],ha='center',va='center',color='k')
    else:
        ax.set_xticks(np.arange(len(xyticks)))
        ax.set_yticks(np.arange(len(xyticks)))
        ax.set_xticklabels(xyticks)
        ax.set_yticklabels(xyticks)
        plt.setp(ax.get_yticklabels(), rotation=45, ha="right",
         rotation_mode="anchor")
        for i in range(len(xyticks)):
            for j in range(len(xyticks)):
                ax.text(i,j,r[i][j],ha='center',va='center',color='k')
    ax.set_title(title,**title_font)

def func_exp(x, a, b):    
    return a * np.exp(b * x)

def func_power(x,a,b):
    return a*np.power(x,b)

def get_stats(ypred,y):
    rmse=np.sqrt(np.nanmean((y-ypred)**2))      #rmse
    # rsquare=r2_score(y,ypred)
    ymean=np.nanmean(y)         #mean
    rrmse=rmse/ymean*100        #rrmse
    mre=np.nanmean(abs(ypred-y)/y)*100  #mre
    ssreg=np.nansum((ypred-ymean)**2)   
    ssres=np.nansum((ypred-y)**2)
    sstot=np.nansum((y-ymean)**2)
    # rsquare=ssreg/sstot
    rsquare=1-ssres/sstot
    return rsquare,rmse,rrmse,mre

def exp_fit(x,y):
    functype='exp'
    try:
        popt, pcov = curve_fit(func_exp, x, y)  # popt 是拟合参数。按自定义的方程func_exp,带入x,y进行拟合，获取拟合方程的系数
        temp = np.array([x,y]).T
        temp=temp[np.argsort(temp[:,0])]    #np.argsort:将x中的元素从小到大排列，提取其对应的index(索引)，然后输出到y
        ypred = func_exp(temp[:,0], popt[0], popt[1])   # 根据x,方程系数，输出拟合数值ypred
        formula = r"y=" + '%.2f' % popt[0] +'*' + "e^(" + '%.2f' % popt[1] + "*x)"
        rsquare,rmse,rrmse,mre=get_stats(ypred,temp[:,1])
        print(functype,':',rsquare,popt)
    except:
        formula,rsquare,rmse,rrmse,mre='canfitexp',0,0,0,0
        popt=[0,0]
    return formula,rsquare,rmse,rrmse,mre,functype,popt

def power_fit(x,y):
    functype='power'
    try:
        popt, pcov = curve_fit(func_power, x, y)  # popt 是拟合参数
        temp = np.array([x,y]).T
        temp=temp[np.argsort(temp[:,0])]
        ypred = func_power(temp[:,0], popt[0], popt[1])
        formula = r"y=" + '%.2f' % popt[0] +'*' + "x^" + '%.2f' % popt[1]
        rsquare,rmse,rrmse,mre=get_stats(ypred,temp[:,1])
        print(functype,':',rsquare,rmse,rrmse,mre)
    except:
        formula,rsquare,rmse,rrmse,mre='canfitpower',0,0,0,0
        popt=[0,0]
    return formula,rsquare,rmse,rrmse,mre,functype,popt

def poly_fit_xy(x,y,level):
    p=np.polyfit(x,y,level) #拟合方程
    a=np.poly1d(p)          #获取拟合方程的系数
    ypred=np.polyval(p,x)   #通过拟合获取的数值ypred
    rsquare,rmse,rrmse,mre=get_stats(ypred,y)   #统计r2,rmse,rrmse,mre
    if level==1:
        formula = 'y=' + '%.2f' % a[1] + 'x' + '+' + '%.2f' % a[0]
        functype='poly1'        
    else:
        formula = 'y=' + '%.2f' % a[2] + 'x^2' + '+' + '%.2f' % a[1]+'x'+'+'+'%.2f'%a[0]
        functype='poly2'
    print(functype,':',rsquare,rmse,rrmse,mre)
    return formula,rsquare,rmse,rrmse,mre,functype,p

def getbestmodel(x,y):
    bestmodel=[]
    if len(x)<4:
        bestmodel=list(poly_fit_xy(x,y,1))      #如果采样点少于4个，线性拟合
    else:
        tmp=[]
        tmp.append(list(poly_fit_xy(x,y,1)))    #一次拟合,return:formula,rsquare,rmse,rrmse,mre,functype,p
        tmp.append(list(poly_fit_xy(x,y,2)))    #二次拟合
        # tmp.append(list(exp_fit(x,y)))          #指数拟合 y = a*e^(b*x)
        # tmp.append(list(power_fit(x,y)))        #幂函数拟合 y = a*x^(b)
        tmp=np.array(tmp)       
        idx=np.argmax(tmp[:,1]) #返回一个numpy数组中最大值的索引值
        bestmodel=tmp[idx,:]    #formula,rsquare,rmse,rrmse,mre,functype,p
    print(bestmodel)
    return bestmodel

def writeyable(writer,array,title,sheetname,startrow,startcol,columns,idx,ifshowidx):
    df=pd.DataFrame([title])
    df.to_excel(writer,sheet_name=sheetname,startrow=startrow,startcol=startcol,float_format="%.4f",index=False,header=None)
    df=pd.DataFrame(array,columns=columns,index=idx)
    df.to_excel(writer,sheet_name=sheetname,startrow=startrow,startcol=startcol,float_format="%.4f",index=ifshowidx)

def getarrayx(b1,b2,method):
    if method==Methods[0]:
        arrayx=b1
    elif method==Methods[1]:
        arrayx=np.array(list(map(np.exp,b1)))
    elif method==Methods[2]:
        arrayx=b1-b2
    elif method==Methods[3]:
        arrayx=b1/b2
    elif method==Methods[4]:
        arrayx=(b1-b2)/(b1+b2)
    else: #method==Methods[5]
        arrayx=np.array(list(map(np.log,b1)))/b2
    return arrayx

def derivewaterpara(arrayx,fitmethod,popt):
    x=arrayx.reshape(-1)
    if (fitmethod=='poly1') | (fitmethod=='poly2'):
        ypred=np.polyval(popt,x)
    elif fitmethod=='exp':
        ypred = func_exp(x, popt[0], popt[1])
    else:
        ypred = func_power(x, popt[0], popt[1])
    return ypred.reshape(arrayx.shape)

# data:读光谱   sampletable：读化验值     parameters:待反演数据    
def derive_model(data,parameters):
    savefile='./model_r_stats.xlsx'
    # 采样数据与光谱数据link
    sampledata=pd.concat([data['b'],data['g'],data['r'],data['nir']],axis=1)
    arrayx=sampledata.copy()
    for para in parameters:
        sampledata[para]=data[para]
    sampledata=sampledata.dropna()

    Outtable,Outmodel=[],[]
    writer=pd.ExcelWriter(savefile)
    for ylabel in parameters:
        y=sampledata[ylabel].values
        Res=[]
        fig,axs=plt.subplots(3,2,figsize=(3*2.8,5*2.8))
        fig.subplots_adjust(top=1,hspace=0.4,wspace=0.225,left=0.09)
        ysheetname=ylabel
        for i in range(len(Methods)):
            method=Methods[i]
            if (method=='singleband') | (method=='exp'):
                array_r,array_model,idx=getpearsonr(arrayx,y,method)
                # plot heatmap of r
                plotheatmap(axs[(i)//2][(i)%2],array_r,BANDS,titles[i]+" ~ "+ylabel)
                # save to excel
                writeyable(writer,array_r,Methods_table[i],sheetname=ysheetname,startrow=0,startcol=i*9, \
                    columns=['-'],idx=BANDS,ifshowidx=True)
                Res.append([array_r[idx],array_model[idx],arrayx.iloc[:,idx].values])
            else:
                array_res,array_model=get_bandcom(arrayx,method)
                array_res[array_res==0]=np.nan
                array_r,idxi,idxj=getpearsonr(array_res,y,method)
                # plot heatmap of r
                plotheatmap(axs[(i)//2][(i)%2],array_r,BANDS,titles[i]+" ~ "+ylabel)
                # save to excel
                writeyable(writer,array_r,Methods_table[i],sheetname=ysheetname,startrow=((i-2)//2+1)*10,startcol=((i-2)%2)*9, \
                    columns=BANDS,idx=BANDS,ifshowidx=True)
                Res.append([array_r[idxi][idxj],array_model[idxi][idxj],array_res[idxi][idxj]])

        # 写入最大相关性的波段组合模型
        df=pd.DataFrame(Res,columns=['r','model','specvalue'])  
        tmp=np.absolute(df['r'].values) #取r最大的光谱组合
        tmp_idx=np.where(tmp==np.nanmax(tmp))
        idx_model=tmp_idx[0][0]
        df1=pd.DataFrame(np.vstack([df.loc[idx_model]['model'],df.loc[idx_model]['r']]).T,columns=['最佳波段组合模型','最大相关系数'])
        df1.to_excel(writer,sheet_name=ysheetname,startrow=29,startcol=0,float_format="%.4f",index=False)
        array=np.vstack([y,df.loc[idx_model]['specvalue']]).T       #写出采样值和r最大的光谱组合对应的数值
        writeyable(writer,array,'-',sheetname=ysheetname,startrow=32,startcol=0, \
                    columns=['采样值','波段组合光谱值'],idx=range(array.shape[0]),ifshowidx=True)

        array=array.astype('float')     #采样值和r最大的光谱组合对应的数值
        # 计算最佳拟合模型
        bestmodel=getbestmodel(array[:,1],array[:,0])   #r最大的光谱组合对应的数值作为自变量，采样值作为因变量，构建模型。返回formula,rsquare,rmse,rrmse,mre,functype,p
        outtable=np.hstack(([ysheetname,df.loc[idx_model]['model']],bestmodel))
        print(outtable)
        Outtable.append(outtable[0:-2])
        print(Outtable)
        Outmodel.append(outtable)
        print(Outmodel)
        # plt.show()
        fig.savefig('./pearson_'+ysheetname+'.png',dpi=300)

    dfouttable=pd.DataFrame(np.vstack(Outtable),columns=['水质参数','波段组合','拟合方程','R2','RMSE','RRMSE(%)','MRE(%)'])
    dfouttable.to_excel(writer,sheet_name='fitmodel',float_format="%.4f",index=False)
    writer.save()
    writer.close()
    return Outmodel

# # 水质反演
# def waterretrieve(tiffile,band_idx,outmodel,parameters):
#     path = os.path.abspath(os.path.dirname(os.path.dirname(tiffile))) 
#     waterQA_path = os.path.join(path,"waterQA")
#     if not os.path.exists(waterQA_path):
#         os.mkdir(waterQA_path)
#     raster=read_tif_multiband(tiffile,band_idx)
#     for i in range(len(outmodel)):
#         ylabel=parameters[i]
#         bandcom=(outmodel[i][1]).split(';')[1]
#         method=bandcom.split(',')[2]
#         band1=BANDS.index(bandcom.split(',')[0])
#         band2=BANDS.index(bandcom.split(',')[1])
#         b1=(raster.dataarray[:,:,band1]).astype('float')
#         b2=(raster.dataarray[:,:,band2]).astype('float')
#         # ## added
#         idx=b1==0
#         # b1[idx]=0
#         # b2[idx]=1 # 防止除以0值
#         ## 
#         arrayx=getarrayx(b1,b2,method)

#         fitmethod=outmodel[i][-2]
#         popt=outmodel[i][-1]
#         ypred=derivewaterpara(arrayx,fitmethod,popt)
#         # 剔除个别异常值+非水域值
#         ypred[idx]=0
#         ypred[ypred<0]=0
#         if ylabel=='codmn':
#             ypred[ypred>100]=0
#         elif ylabel=='nh3n':
#             ypred[ypred>20]=0
#         elif ypred=='tp':
#             ypred[ypred>10]=0
#         elif ypred=='tn':
#             ypred[ypred>10]=0
#         f = os.path.basename(tiffile)
#         outfile = os.path.join(waterQA_path,f.replace("_WTREF","_"+ylabel))
#         print(outfile)
#         write_geotiff(outfile,ypred,raster.transforms,raster.projection)
# 水质反演
def waterretrieve(tiffile,band_idx,outmodel,parameters):
    raster=read_tif_multiband(tiffile,band_idx)
    print(raster.shape)
    savename=tiffile.split('\\')[-1].replace('.tif','')
    for i in range(len(outmodel)):
        ylabel=parameters[i]
        bandcom=(outmodel[i][1]).split(';')[1]
        method=bandcom.split(',')[2]
        band1=BANDS.index(bandcom.split(',')[0])
        band2=BANDS.index(bandcom.split(',')[1])
        b1=(raster.dataarray[:,:,band1]).astype('float')
        b2=(raster.dataarray[:,:,band2]).astype('float')
        # ## added
        idx=b1==0
        # b1[idx]=0
        # b2[idx]=1 # 防止除以0值
        ## 
        arrayx=getarrayx(b1,b2,method)

        fitmethod=outmodel[i][-2]
        popt=outmodel[i][-1]
        ypred=derivewaterpara(arrayx,fitmethod,popt)
        # 剔除个别异常值+非水域值

        rast=raster.dataarray[:,:,0]
        ypred[rast＞errorValue]=0

        ypred[idx]=0
        ypred[ypred<0]=0
        if ylabel=='codmn':
            ypred[ypred>100]=0
        elif ylabel=='nh3n':
            ypred[ypred>20]=0
        elif ylabel=='tp':
            ypred[ypred==0]=0
        elif ylabel=='tn':
            ypred[ypred>20]=0
        elif ylabel=='chla':
            ypred[ypred>100]=0
        elif ylabel=='ntu':
            ypred[ypred>40]=0

        write_geotiff('./'+savename+'_'+ylabel+'.tif',ypred,raster.transforms,raster.projection)