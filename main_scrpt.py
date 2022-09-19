from matplotlib import pyplot as plt
import json
from numpy import arange, zeros, where, array, NaN
from scipy.interpolate import interp1d
import matplotlib as mpl
from matplotlib.animation import FuncAnimation
from pydub import AudioSegment
from pydub.playback import play
import threading 

newBeat=False
sound = AudioSegment.from_wav('beep.wav')
beep_thread = threading.Thread(target=play, args=(sound,))
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
    text_top={'wave_ecg':'ECG bpm', 'wave_pleth':r'SpO$_2$%', 'wave_bp':'BP mmHg', 'wave_etco2':r'ETCO$_2$ kPa' }
    text_middle={'wave_ecg':'-', 'wave_pleth':'-', 'wave_bp':'---/---', 'wave_etco2':'-    RR --' }



    plt.close('all')
    fig, axs = plt.subplots(len(plot_mapping))
    fig.suptitle('Patient Monitor',fontsize=28)
    lines={}
    pmtext={}
    for ax,cKey in zip(axs.flat,plot_mapping.keys()):
        ax.axis('off')
        ax.set_xlim([-1,5])
        ax.set_ylim([-10,110])
        ax.set_facecolor('black')
        cLine,=ax.plot([], [], linewidth=5,color='green')
        cPoint,=ax.plot([],[],color='green', marker='o', markersize=8)
        lines[cKey]=[cLine, cPoint]
        ax.text(-1, 70.0, text_top[cKey], fontsize=20,horizontalalignment='left')
        pmtext[cKey]=ax.text(-1, 40.0, text_middle[cKey], fontsize=20,horizontalalignment='left')
        
    return fig,lines,pmtext

def plotWaveForms(fig,lines,pmtext,plot_mapping,pd):
    for cWave in plot_mapping.keys():
        xdata=pd[cWave]['t']
        ydata=pd[cWave]['signal']
        lines[cWave][0].set_data(xdata, ydata)
        lines[cWave][1].set_data(xdata[-1],ydata[-1])
        
    pmtext['wave_ecg'].set_text('%d'%pd['vs_hr'])
    pmtext['wave_pleth'].set_text('%d'%pd['vs_spo2'])
    pmtext['wave_bp'].set_text('%d/%d'%(pd['vs_sbp'],pd['vs_dbp']))
    pmtext['wave_etco2'].set_text('%d  RR%d'%(pd['vs_etco2'],pd['vs_rr']))
        
        


def updateWaveForm(tc,wave,line,fps,hide=1,isBeat=False):
    global newBeat
    xdata=wave['t'].copy()
    ydata=wave['signal'].copy()
    idx=where((xdata>tc) & (xdata<tc+hide))[0]
    idx_new=where((xdata<=tc) & (xdata>tc-1/fps))[0]
    xdata[idx]=NaN
    ydata[idx]=NaN
    xc=xdata[idx_new]
    yc=ydata[idx_new]
    line[0].set_data(xdata, ydata)
    line[1].set_data(xc[-1],yc[-1])
    
    if (isBeat) & (max(yc)>80) & (newBeat==False):
        print(yc)
        beep_thread = threading.Thread(target=play, args=(sound,))
        beep_thread.start()
        newBeat=True
    elif newBeat==True & (max(yc)<25):
        newBeat=False     

    return line
   

def updateWaveForms(tc,pd,lines,pmtext,plot_mapping,fps):
    for cWave in plot_mapping.keys():
        updateWaveForm(tc,pd[cWave],lines[cWave],fps,isBeat=cWave=='wave_ecg')
    # if tc+1/fps>=5:
    #     updateMeasurements(pd,pmtext)
    

    


def loadPatientData(fname):
    f_id=open(fname,'r')
    pd=json.load(f_id)
    f_id.close()
    for cKey in ['wave_ecg', 'wave_pleth', 'wave_bp', 'wave_etco2']:
        pd[cKey]=fixdata(pd[cKey])
    return pd 
    
fname='pd_1.json'
pd=loadPatientData(fname)

maxTime=5
fps=30

plot_mapping={'wave_ecg':0, 'wave_pleth':1, 'wave_bp':2, 'wave_etco2':3}
fig,lines,pmtext=makeMonitorFigure(plot_mapping)
plotWaveForms(fig,lines,pmtext,plot_mapping,pd)

ani = FuncAnimation(fig, updateWaveForms, 
                    fargs=(pd,lines,pmtext,plot_mapping,fps) ,
                    frames=time_generator(maxTime,fps), 
                    blit=False, 
                    interval=1000/fps,
                    repeat=True)