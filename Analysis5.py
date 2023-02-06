import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.misc import electrocardiogram
from scipy.signal import find_peaks
from sklearn.cluster import KMeans
from scipy.signal import savgol_filter   # smooth


def TargetM(F1,F2,folder,file_name,Trig1,Molecular):
    TotalData=[]

    for N in range(F1,F2):
        i=0
        fileName=file_name[N]
        file=folder+file_name[N] 
        column0=[]     # m/z
        column1=[]     # Intensity
    
        for line in open(file,'r',encoding="utf-8"): #注意此行
            data=line.split(',')  #  Data 用,隔開
    
            if i>5:               # 去掉標頭
                column0.append(float(data[0]))
                column1.append(float(data[1].strip()))

            i=i+1
            
        TotalData.append(column1)
             
    M=pd.DataFrame(column0) # Dada of M/z
    R=pd.DataFrame(TotalData) # Data of all files
    R=R.transpose()
    Rmean=R.mean(axis=1)
    df2=pd.concat([M,Rmean],axis=1)
    # rename Index
    df2=df2.set_axis(['m/z','adc'], axis=1, inplace=False)

    x=df2['m/z']
    y=df2['adc']

    # Smooth Data --------------------------------------
    y=savgol_filter(y, 51, 3)
    #---------------------------------------------------

    # m/z output 為整數
    #--------------------------------------------------
    y1=pd.DataFrame(y)
    df3=pd.concat([M,y1],axis=1)
    df3=df3.round(0)
    df3=df3.set_axis(['m/z','adc'], axis=1, inplace=False)
    #--------------------------------------------------

    # Target M
    PeakADC=[]
    #TargetM=[58,60,74,88,92]
    Molecular

    for M in Molecular:
    
        filt=df3['m/z']==M
        ss=df3.loc[filt].max().round(0)
        PeakADC.append(ss)

    PeakADC=pd.DataFrame(PeakADC)
    #---------------------------------------------------

    #---------------------------------------------------
    peaks, _ = find_peaks(y, height=Trig1)
    #---------------------------------------------------

    #---------------------------------------------------
    MM=x[peaks].to_numpy()
    df4=pd.DataFrame(MM)
    df4=df4.round(1) #四捨五入到小數點第一位
    df4=df4.set_axis(['m/z_auto'], axis=1, inplace=False)
    df5=pd.DataFrame(y[peaks])
    df5=df5.round(0) #四捨五入到小數點第一位
    df5=df5.set_axis(['adc_auto'], axis=1, inplace=False)
    df6=pd.concat([df4,df5],axis=1)
    #---------------------------------------------------
    #---------------------------------------------------
    # 判斷最有可能的VOC
    mshift=[]
    adcshift=[]
    corr=[]
    diff=[]
    i=0

    for m_auto in df6['m/z_auto']:
        for m in Molecular:
            d=m_auto-m
            dev=abs(m_auto-m)
            if dev <2:
                NewM=m
                shift=d # 有正負
                mshift.append(NewM)
                Newadc=df6['adc_auto'][i]
                adcshift.append(Newadc)
                diff.append(shift)       # 記錄 m/z 的位移，有正負
                corr.append(abs(2-dev))  # corr 換成最大
            
        i=i+1
        
    df7=pd.DataFrame(mshift)
    df7=df7.set_axis(['m/z'], axis=1, inplace=False)
    df8=pd.DataFrame(adcshift)
    df8=df8.set_axis(['adc'], axis=1, inplace=False)
    df9=pd.DataFrame(corr)
    df9=df9.set_axis(['corr'], axis=1, inplace=False)
    df10=pd.DataFrame(diff)
    df10=df10.set_axis(['diff'], axis=1, inplace=False)

    df11=pd.concat([df7,df8,df9,df10],axis=1)
    df11=df11.sort_values('corr',ascending=False).drop_duplicates(subset=['adc'],keep='first') # 判斷最有可能的VOC
    df11=df11.sort_values('adc',ascending=False).drop_duplicates(subset=['m/z'],keep='first') # Delete 重覆adc_shift
    df11=df11.sort_values('m/z')
    #df11=df11.replace(np.nan,30)
    return df11


