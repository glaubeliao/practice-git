import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


time=[]
Concentration=[]
column=[]

i=1
for line in open('Mix_5L_500ml_3.csv','r'):
    i=i+1
    data=line.split(',')  #  Data 用,隔開

    if i>23:              # 去掉標頭
        column.append(data)


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
    print(Input)
    Concentration.append(float(Input)*1000)
    time.append(i)
    i=i+1

fig = plt.figure()
#ax = fig.add_subplot(1, 1, 1)
#ax.plot(time,Concentration )

#plt.scatter(time,Concentration, marker='o')
plt.plot(time,Concentration)

# Labeland Title
plt.xlabel("t (sec)", fontsize=20)
plt.xticks(fontsize=10)
#plt.ylabel("ppb", fontsize=20)
plt.yticks(fontsize=10)
#plt.title("Acetone", fontsize=16)
plt.show()
