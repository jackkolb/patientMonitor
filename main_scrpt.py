from matplotlib import pyplot as plt
import json
from numpy import arange, where, NaN
from scipy.interpolate import interp1d
import matplotlib as mpl
from matplotlib.animation import FuncAnimation
# PyAudio works best on Windows
from playsound_usingPyAudio import play_sound
# PlaySound works best on Linux
#from  playsound_usingPlaySound import play_sound

import threading
import urllib3
http = urllib3.PoolManager()

newBeat=False
mpl.rcParams['toolbar'] = 'None' 


def time_generator(maxTime=5,fps=1/30):
    cur = 0
    while True: 
        if cur > maxTime:
            cur=0
            break
        yield cur
        cur += 1/fps

        
def fixdata(datain):
    ts_og=[val['x'] for val in datain]
    ts_og=[5*t/max(ts_og) for t in ts_og]
    signal_og=[val['y'] for val in datain]    
    interp_func = interp1d(ts_og, signal_og, 'slinear')
    ts=arange(0,5+.001,.001)
    signal = interp_func(ts)
    return {'t':ts,'signal':signal}


def makeMonitorFigure(plot_mapping):
    plt.close('all')
    text_top={'wave_ecg':'ECG bpm', 'wave_pleth':r'SpO$_2$%', 'wave_nibp':'BP mmHg', 'wave_etco2':r'ETCO$_2$ kPa' }
    text_middle={'wave_ecg':'-', 'wave_pleth':'-', 'wave_nibp':'---/---', 'wave_etco2':'-    RR --' }
    plot_mapping_colors={'wave_ecg':"#00FC00", 'wave_pleth':"#00FCFF", 'wave_nibp':"#FFFF00", 'wave_etco2':"#FF78FF"}
    plt.close('all')
    plt.rcParams.update({
    "lines.color": "white",
    "patch.edgecolor": "white",
    "text.color": "black",
    "axes.facecolor": "white",
    "axes.edgecolor": "lightgray",
    "axes.labelcolor": "white",
    "xtick.color": "white",
    "ytick.color": "white",
    "grid.color": "lightgray",
    "figure.facecolor": "black",
    "figure.edgecolor": "black",
    "savefig.facecolor": "black",
    "savefig.edgecolor": "black"})
    fig, axs = plt.subplots(len(plot_mapping))
    fig.suptitle('Patient Monitor',fontsize=28)
    lines={}
    pmtext={}
    for ax,cKey in zip(axs.flat,plot_mapping.keys()):
        ax.axis('off')
        ax.set_xlim([-1,5])
        ax.set_ylim([-10,110])
        ax.set_facecolor('black')
        cLine,=ax.plot([], [], linewidth=5,color=plot_mapping_colors[cKey])
        cPoint,=ax.plot([],[],color=plot_mapping_colors[cKey], marker='o', markersize=8)
        lines[cKey]=[cLine, cPoint]
        ax.text(-1, 70.0, text_top[cKey], fontsize=20,horizontalalignment='left',color=plot_mapping_colors[cKey])
        pmtext[cKey]=ax.text(-1, 40.0, text_middle[cKey], fontsize=20,horizontalalignment='left',color=plot_mapping_colors[cKey])
        
    return fig,lines,pmtext


def loadPatientData(fname):
    f_id=open(fname,'r')
    pd=json.load(f_id)
    f_id.close()
    for cKey in ['wave_ecg', 'wave_pleth', 'wave_nibp', 'wave_etco2']:
        pd[cKey]=fixdata(pd[cKey])
    return pd 

def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)


def checkPatientStatus(): 
    vitals_state = -1
    try:
        response = http.request('GET', 'http://128.61.187.166:8080/var', timeout=2.0, retries=False)
        vitals_state = int(json.loads(response.data.decode('utf-8'))['vitals-state'])
    except (urllib3.exceptions.NewConnectionError, urllib3.exceptions.ConnectTimeoutError ):
        print('HTTP Connection failed.')
    if vitals_state == 1:
        fname = 'pd_1.json'
    elif vitals_state == 0:
        fname = 'pd_2.json'
    else:
        fname = 'pd_increasedICP.json'
    return fname
    


class Monitor():
    def __init__(self,fname='pd_1.json',fps=30,numFrames=None):
        self.fps=fps
        self.numFrames=numFrames
        self.load_waveform(fname)
        self.pd=self.pd_new.copy()
        self.fname=fname
        self.plot_mapping={'wave_ecg':0, 'wave_pleth':1, 'wave_nibp':2, 'wave_etco2':3}
        self.fig,self.lines,self.pmtext=makeMonitorFigure(self.plot_mapping)
        self.plotWaveForms()
    
    def load_waveform(self,fname):
        self.pd_new=loadPatientData(fname)
        

    def plotWaveForms(self):
        for cWave in self.plot_mapping.keys():
            xdata=self.pd[cWave]['t']
            ydata=self.pd[cWave]['signal']
            self.lines[cWave][0].set_data(xdata, ydata)
            self.lines[cWave][1].set_data(xdata[-1],ydata[-1])
            
        self.pmtext['wave_ecg'].set_text('%d'%self.pd['vs_hr'])
        self.pmtext['wave_pleth'].set_text('%d'%self.pd['vs_spo2'])
        self.pmtext['wave_nibp'].set_text('%d/%d'%(self.pd['vs_sbp'],self.pd['vs_dbp']))
        self.pmtext['wave_etco2'].set_text('%d  RR%d'%(self.pd['vs_etco2'],self.pd['vs_rr']))

    def updateWaveForms(self,tc):
        if tc==0:
            fname=checkPatientStatus()
            if self.fname!=fname:
                self.load_waveform(fname)
                self.fname=fname
                for cKey in ['vs_hr','vs_spo2','vs_sbp','vs_dbp','vs_etco2','vs_rr']:
                    self.pd[cKey]=self.pd_new[cKey]
                self.pmtext['wave_ecg'].set_text('%d'%self.pd_new['vs_hr'])
                self.pmtext['wave_pleth'].set_text('%d'%self.pd_new['vs_spo2'])
                self.pmtext['wave_nibp'].set_text('%d/%d'%(self.pd['vs_sbp'],self.pd['vs_dbp']))
                self.pmtext['wave_etco2'].set_text('%d  RR%d'%(self.pd['vs_etco2'],self.pd['vs_rr']))
        
            
        for cWave in self.plot_mapping.keys():
            self.updateWaveForm(tc,cWave,isBeat=cWave=='wave_ecg')


    
    def updateWaveForm(self,tc,cWave,isBeat=False, hide=1):
        global newBeat

        xdata=self.pd[cWave]['t'].copy()
        idx_replace=where((xdata<=tc) & (xdata>=tc-1/self.fps))[0]
        idx_hide=where((xdata>tc) & (xdata<tc+hide))[0]


        self.pd[cWave]['signal'][idx_replace]=self.pd_new[cWave]['signal'][idx_replace].copy()
        ydata=self.pd[cWave]['signal'].copy()

        xdata[idx_hide]=NaN        
        ydata[idx_hide]=NaN
        
        xc=xdata[idx_replace]
        yc=ydata[idx_replace]
        self.lines[cWave][0].set_data(xdata, ydata)
        self.lines[cWave][1].set_data(xc[-1],yc[-1])
        
        if (isBeat) & (max(yc)>80) & (newBeat==False):
            beep_thread = threading.Thread(target=play_sound, args=('beep.wav',))
            beep_thread.start()
            newBeat=True
        elif newBeat==True & (max(yc)<25):
            newBeat=False     

maxTime=5
fps=30
frameGenerator=time_generator(maxTime,fps)
monitor=Monitor(fps=fps,numFrames=5001)





ani = FuncAnimation(monitor.fig, monitor.updateWaveForms, 
                    frames=frameGenerator, 
                    blit=False, 
                    interval=1000/fps,
                    repeat=True)
plt.show()

