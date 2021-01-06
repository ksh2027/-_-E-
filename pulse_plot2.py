import matplotlib.pyplot as plt
import numpy as np
import time
import time, random
import math
import serial
import tkinter as tk                #GUI模組
import threading                    #多執行緒模組
from collections import deque
from scipy import signal 

        
def job():                          #子執行緒跑的副程式，將tkinter相關的程式放入此副程式中
    
    #'開始量測'按鈕指令
    def startmeasure():             
        global K
        K = 1
    #'FIR濾波'按鈕指令
    def startFIR():
        global F
        if(len(PData.axis_y1)==500):
            F = 1        
    #'顯示即時心率'按鈕指令
    def heartmeasure():
        global heartrate
        if(len(PData.axis_y1)==500):
            text1.delete(1.0, "end")
            text1.insert("insert",heartrate)
            text1.insert("insert","次/分")
            root.after(100,heartmeasure)
    #'計算HRV'按鈕指令
    def HRVmeasure():
        global H,HRV,count
        if(len(PData.axis_y1)==500):
            H=1
            count=count+1
            if count>200:
                H=0
                text2.delete(1.0, "end")   
                text2.insert("insert","error")
                count=0
                HRV=[]
            elif len(HRV)==10:
                H=0
                text2.delete(1.0, "end")
                text2.insert("insert",round(1000*np.std(HRV, ddof=1)))    
                text2.insert("insert","ms")
                count=0
                HRV=[]
                H=0
            elif len(HRV)<10:
                text2.delete(1.0, "end")
                text2.insert("insert",len(HRV))    
                text2.insert("insert","/10")
                root.after(100,HRVmeasure)
    #'結束程式'按鈕指令
    def end():
        global K
        root.quit()   
        K=-1
    
    #tkinter視窗介面設定    
    root = tk.Tk()                   
    root.title('心率量測')
    root.geometry('600x600')
    bt_start = tk.Button(root, text='開始量測', command=startmeasure,height = 5,width = 15,font=100)
    bt_FIR = tk.Button(root, text='FIR濾波', command=startFIR,height = 5,width = 15,font=100)
    bt_heart = tk.Button(root, text='顯示即時心率', command=heartmeasure,height = 5,width = 15,font=100)
    bt_HRV = tk.Button(root, text='計算HRV', command=HRVmeasure,height = 5,width = 15,font=100)
    bt_end = tk.Button(root, text='結束程式', command=end,height = 5,width = 15,font=100)
    text1 = tk.Text(root,width=10, height=1)
    text1.configure(font=100)
    text2 = tk.Text(root,width=10, height=1)
    text2.configure(font=100)
    bt_start.pack()
    bt_FIR.pack()
    bt_heart.pack()
    text1.pack()
    bt_HRV.pack()
    text2.pack()
    bt_end.pack()
    root.mainloop()  

#主執行緒
t = threading.Thread(target = job)
t.start()                                                     #開始子執行緒

#Display loading 
class PlotData:
    def __init__(self, max_entries=30):
        self.axis_x = deque(maxlen=max_entries)
        self.axis_y = deque(maxlen=max_entries)
        self.axis_y1 = deque(maxlen=max_entries)
    def add(self, x, y):
        self.axis_x.append(x)
        self.axis_y.append(y)
        self.axis_y1.append(y-np.mean(self.axis_y))          #y1為y扣除平均值的訊號

#設定FIR濾波器套用的陣列b
b=[1]
for i in range(2,21):                                        #從0.1pi到pi之間，每0.05pi產生一個零點，共產生38個零點
    a=np.array([1,-(np.exp(1j*0.05*i*np.pi)+np.exp(-1j*0.05*i*np.pi)),1])     
    b=np.array(np.convolve(b,a))

#繪製fig1:z-domain圖
angle = np.linspace(-np.pi, np.pi, 50)
cirx = np.sin(angle)
ciry = np.cos(angle) 
fig1=plt.figure(figsize=(8,8))
plt.plot(cirx, ciry,'k-')
for i in range(2,21):
    plt.plot(0, 0, 'x', markersize=12,color='purple')
    plt.text(0.1,0.1,38,fontsize=15)
    zero=np.roots(b)
    plt.plot(np.real(zero), np.imag(zero), 'o', markersize=12,color='pink')
plt.grid()
plt.xlim((-2, 2))
plt.xlabel('Real')
plt.ylim((-2, 2))
plt.ylabel('Imag')

#initial
fig2, ((ax1, ax3), (ax2, ax4)) = plt.subplots(2,2)
line1, = ax1.plot(0)
line2, = ax2.plot(0)
line3, = ax3.plot(0)
line4, = ax4.plot(0)
fig2.set_size_inches(16, 8)
plt.show(block = False)
plt.setp(line2,color = 'r')
PData= PlotData(500)                      #設定資料存入數量為500
ax1.set_ylim(-10,10)
ax2.set_ylim(0,150)
ax3.set_ylim(-10,10)
ax4.set_ylim(0,150)

# plot parameters
print ('plotting data...')
# open serial port
strPort='com4'
ser = serial.Serial(strPort, 115200)
ser.flush()

start = time.time()

x=np.linspace(-250,249,500)              #頻譜橫軸以頻率為單位表示

#各式參數宣告
past_time_point=0
time_point=0
slope=0
K=0
F=0
H=0
HRV=[]
count=0

while True:
    if K==1:                                                    #'開始量測'按鈕執行
        for ii in range(10):
            try:
                data = float(ser.readline())
                PData.add(time.time() - start, data)
            except:
                pass

        if(len(PData.axis_y1)==500):                            #存入500筆資料後才可進行傅立葉轉換頻譜、濾波、心率量測等功能
            y1f = np.fft.fftshift(np.fft.fft(PData.axis_y1))     #傅立葉轉換後將範圍調整至[-250, 249]

            #y_mid=signal.medfilt(PData.axis_y1,3)               #3點中值濾波器
            y_fir =signal.lfilter(b/np.sum(abs(b)), 1, PData.axis_y1)   #FIR低通濾波器
            y2f = np.fft.fftshift(np.fft.fft(y_fir))
            
            for i in range(0,9):                                #從最後10筆資料找尋斜率變換位置
                if (y_fir[491+i]-y_fir[490+i]) <0 :
                    
                    if slope==1:                                #斜率由正轉負時(波峰)
                        wave=time_point-past_time_point         #wave:上一個波峰到這一個波峰的時間差(即時心跳週期)
                        past_time_point = time_point
                        if wave!=0 and (60/wave)<150 and (60/wave)>40:        #每分鐘心率過濾在40到150之間
                            heartrate=round(60*1/wave)
                            if (H==1) and len(HRV)<10 and (abs(wave-np.mean(HRV))<0.15 or len(HRV)==0): #'計算HRV'按鈕執行，取十個心跳計算HRV
                                HRV.append(wave)                                                        
                            
                    slope=-1            
                elif (y_fir[491+i]-y_fir[490+i]) >0 :
                    slope=1
                    time_point = PData.axis_x[491+i]
                else :
                    slope=0 
        
        
        ax1.set_xlim(PData.axis_x[0], PData.axis_x[0]+5)
        ax2.set_xlim(-250, 249)

        if F==1:                                                #'FIR濾波'按鈕執行   
            ax3.set_xlim(PData.axis_x[0], PData.axis_x[0]+5)
            ax4.set_xlim(-250, 249)

        ax1.set_title("Original signal")
        ax2.set_title("Spectrum of original signal")
        ax3.set_title("Signal after FIR")
        ax4.set_title("Spectrum of signal after FIR")

        line1.set_xdata(PData.axis_x)
        line1.set_ydata(PData.axis_y1)
        if(len(PData.axis_y1)==500):
            line2.set_xdata(x)
            line2.set_ydata(abs(y1f))
            
            if F==1:                                            #'FIR濾波'按鈕執行 
                line3.set_xdata(PData.axis_x)
                line3.set_ydata(y_fir)
                line4.set_xdata(x)
                line4.set_ydata(abs(y2f))

        fig2.canvas.draw()
        fig2.canvas.flush_events()      
    elif K==-1:                                                 #'結束程式'按鈕執行
        plt.close(fig1)
        plt.close(fig2)
        break