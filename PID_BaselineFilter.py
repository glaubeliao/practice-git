import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pybaselines import Baseline, utils

time=[]
Concentration=[]
column=[]

i=1
for line in open('5Mix5.csv','r'):
    i=i+1
    data=line.split(',')  #  Data 用,隔開

    if i>23:              # 去掉標頭
        column.append(data)

#---------------------------------
R=pd.DataFrame(column)
#print(R)
# Dataframe to array
#---------------------------------
data=R.to_numpy()
#---------------------------------

print(data.shape[0])  # Total Data Number
#print(data[0][1])    # 第一筆 Data
size=data.shape[0]


i=1
for line in range(size):
    Input=data[line][1]
#    print(Input)
    Concentration.append(float(Input)*1000)
#    time.append(i)
    i=i+1

#---------------------------------
data1=np.array(Concentration)
size=data1.size
x = np.linspace(1, size, size)
y=data1
#---------------------------------

baseline_fitter = Baseline(x_data=x)

bkg_1 = baseline_fitter.modpoly(y, poly_order=3)[0]
bkg_2 = baseline_fitter.asls(y, lam=1e7, p=0.02)[0]
bkg_3 = baseline_fitter.mor(y, half_window=30)[0]
bkg_4 = baseline_fitter.snip(y, max_half_window=40, decreasing=True, smooth_half_window=3)[0]

y1=y-bkg_3

#plt.plot(x, y, label='raw data', lw=1.5)
#plt.plot(x, bkg_1, '--', label='modpoly')
#plt.plot(x, bkg_2, '--', label='asls')
#plt.plot(x, bkg_3, '--', label='mor')
#plt.plot(x, bkg_4, '--', label='snip')
plt.plot(x,y1, label='After Baseline_Filter')

plt.legend()
plt.show()


#y1=y-bkg_3
#plt.plot(x,y)
