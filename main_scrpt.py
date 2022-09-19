from matplotlib import pyplot as plt
import json
from numpy import arange, zeros, where, array, NaN
from scipy.interpolate import interp1d
from matplotlib.animation import FuncAnimation
from pydub import AudioSegment
from pydub.playback import play
import threading 

newBeat=False
sound = AudioSegment.from_wav('beep.wav')
beep_thread = threading.Thread(target=play, args=(sound,))


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
    fig, axs = plt.subplots(len(plot_mapping))
    fig.suptitle('Patient Monitor')
    lines={}
    for ax,cKey in zip(axs.flat,plot_mapping.keys()):
        ax.axis('off')
        ax.set_xlim([0,5])
        ax.set_ylim([-10,110])
        ax.set_facecolor('black')
        cLine,=ax.plot([], [], linewidth=5,color='green')
        cPoint,=ax.plot([],[],color='green', marker='o', markersize=8)
        lines[cKey]=[cLine, cPoint]
    return fig,lines

def plotWaveForms(fig,lines,plot_mapping,pd):
    for cWave in plot_mapping.keys():
        xdata=pd[cWave]['t']
        ydata=pd[cWave]['signal']
        lines[cWave][0].set_data(xdata, ydata)
        lines[cWave][1].set_data(xdata[-1],ydata[-1])


def updateWaveForm(tc,wave,line,hide=1,isBeat=False):
    global newBeat
    xdata=wave['t'].copy()
    ydata=wave['signal'].copy()
    idx=where((xdata>tc) & (xdata<tc+hide))
    idxc=list(where(xdata<=tc)[0])
    xdata[idx]=NaN
    ydata[idx]=NaN
    xc=xdata[idxc[-1]]
    yc=ydata[idxc[-1]]
    line[0].set_data(xdata, ydata)
    line[1].set_data(xc,yc)
    
    if (isBeat) & (yc>.5) & (newBeat==False):
        beep_thread = threading.Thread(target=play, args=(sound,))
        beep_thread.start()
        newBeat=True
    elif newBeat==True & (yc<.25):
            newBeat=False     

    return line
   

def updateWaveForms(tc,pd,lines,plot_mapping):
    for cWave in plot_mapping.keys():
        updateWaveForm(tc,pd[cWave],lines[cWave],isBeat=cWave=='wave_ecg')
    

    


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
fig,lines=makeMonitorFigure(plot_mapping)
plotWaveForms(fig,lines,plot_mapping,pd)

for c in range(1):
    ani = FuncAnimation(fig, updateWaveForms, 
                        fargs=(pd,lines,plot_mapping) ,
                        frames=time_generator(maxTime,fps), 
                        blit=False, 
                        interval=1000/fps,
                        repeat=False)