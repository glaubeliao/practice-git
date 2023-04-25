import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.misc import electrocardiogram
from scipy.signal import find_peaks, peak_widths
from scipy.signal import savgol_filter   # smooth


folder="/MEK_0ppb_1"
#folder="/zair_2"
folder1="."+folder+"/"

#-獲取當前資料夾名稱然後存成dir_path變數---------------
dir_path = os.path.dirname(os.path.realpath(__file__))
#--------------------------------------------------------

#-要分析的 data 要放在 data 這個資料夾------------------

dir_path=dir_path+folder # Watch out

# 讀取資料夾內所有檔案名稱然後放進all_file_name這個list裡
all_file_name = os.listdir(dir_path)
#-------------------------------------------------------


TotalData=[]

Trig=30
Trig1=50

F1=25      # File Start
F2=30      # File End

for N in range(F1,F2):
    i=0
    fileName=all_file_name[N]
    file=folder1+all_file_name[N] 
    #print(file)
    column0=[]     # m/z
    column1=[]     # Intensity
    #column2=[]     # Moleular Name
    for line in open(file,'r'):
        data=line.split(',')  #  Data 用,隔開
    
        if i>5:               # 去掉標頭
            column0.append(float(data[0]))
            #column2.append(str("unknown"))
            ADC=float(data[1].strip())
            
            if ADC < Trig:
                ADC=30
                column1.append(ADC) # 去掉 /n
            else:
                column1.append(ADC) # 去掉 /n
        i=i+1
    TotalData.append(column1)  # merge data 

#print(column0.index(58.02))
M=pd.DataFrame(column0) # Dada of M/z
#Name=pd.DataFrame(column2) # Name
#print(M[0:80].mean()) # 多點合并

R=pd.DataFrame(TotalData) # Data of all files
R=R.transpose()
print(R)
#Rsum=R.mean(axis=1)
Rsum=R.median(axis=1)
print(Rsum)
df2=pd.concat([M,Rsum],axis=1)
# rename Index
df2=df2.set_axis(['m/z','adc'], axis=1, inplace=False)
#print(df2)

#x=[]
x=df2['m/z']
#y=[]
y=df2['adc']
#


# Smooth Data --------------------------------------
#y=y.rolling(40).mean()
y=savgol_filter(y, 51, 3)
#---------------------------------------------------

# m/z output 為整數
#--------------------------------------------------
y1=pd.DataFrame(y)
df3=pd.concat([M,y1],axis=1)
df3=df3.round(0)
df3=df3.set_axis(['m/z','adc'], axis=1, inplace=False)
#print(df3)
#df3.to_excel('ZeroAir.xlsx')
#--------------------------------------------------

#--------------------------------------------------
PeakADC=[]
TargetM=[72]

for M in TargetM:
    
    filt=df3['m/z']==M
    ss=df3.loc[filt].max().round(0)
    PeakADC.append(ss)

PeakADC=pd.DataFrame(PeakADC)
#print(PeakADC)
#---------------------------------------------------



#---------------------------------------------------
peaks, _ = find_peaks(y, height=Trig1)
#results_half = peak_widths(y, peaks, rel_height=0.5)
#print(results_half)
#print(peaks)
#---------------------------------------------------

#---------------------------------------------------
MM=x[peaks].to_numpy()
#print(MM)

df4=pd.DataFrame(MM)
df4=df4.round(1) #四捨五入到小數點第一位
df4=df4.set_axis(['m/z_auto'], axis=1, inplace=False)
df5=pd.DataFrame(y[peaks])
df5=df5.round(0) #四捨五入到小數點第一位
df5=df5.set_axis(['adc_auto'], axis=1, inplace=False)
df6=pd.concat([df4,df5],axis=1)
#print(df6)
#---------------------------------------------------


#---------------------------------------------------
# 判斷最有可能的VOC
mshift=[]
adcshift=[]
corr=[]
diff=[]
i=0

for m_auto in df6['m/z_auto']:
    for m in TargetM:
        d=m_auto-m
        dev=abs(m_auto-m)
        if dev <2:
            #NewM=df6['m/z_auto'][i]
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
#df10=df10.sort_values('corr').drop_duplicates(subset=['adc_shift'],keep='last')
df11=df11.sort_values('corr',ascending=False).drop_duplicates(subset=['adc'],keep='first') # 判斷最有可能的VOC
df11=df11.sort_values('adc',ascending=False).drop_duplicates(subset=['m/z'],keep='first') # Delete 重覆adc_shift
#df11=df11.sort_values('corr',ascending=False).drop_duplicates(subset=['adc'],keep='first') # 判斷最有可能的VOC
df11=df11.sort_values('m/z')
#df11=pd.concat([df10,df9],axis=1)
#print(df11)

#for line in df11['adc']:
#    print(line)
#---------------------------------------------------

#---------------------------------------------------

fig = plt.figure()
plt.plot(x,y)
plt.plot(PeakADC["m/z"],PeakADC['adc'],'+')
plt.plot(df11["m/z"]+df11["diff"],df11["adc"],'o')
#plt.plot(x,y)
#plt.hlines(*results_half[1:], color="C2")
#print(results_half[1:][1][0])
#print(results_half[1:][2][0])
#print(x[1748])
#print(x[1783])
#print(x[1783]-x[1748])
#print(x[4543])
#print(x[4579])
#print(x[4579]-x[4543])

# Labeland Title
plt.xlabel("m/z", fontsize=20)
plt.xticks(fontsize=10)
plt.ylabel("ADC", fontsize=20)
plt.yticks(fontsize=10)
#plt.title("Enrich", fontsize=16)
plt.show()
