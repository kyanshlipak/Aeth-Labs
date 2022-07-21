import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import argrelextrema
import scipy.optimize
from scipy.signal import find_peaks
from scipy.signal import savgol_filter

def addFileToDF(fileName,df1,df2):
    fileName = fileName.replace('C:\\Users\\Kyan Shlipak\\Documents\\Solenoid Pulse DataFrames\\ ','',1)
    fileName = fileName.replace('.pkl','',1)    
    items = fileName.split(' ')
    data = []
    for item in items:
        try:
            data.append(float(item))
        except ValueError:
            data.append(item)
            
    if len(data) == 10:
        data.append(50)
    
    if data[0] == "Pulse" and (data[7] not in df1.values or data[6] not in df1.values):
        df1 = pd.concat([df1, pd.DataFrame([data], columns = ["type", "date", "time","df_runtime", "pulse_duration", "starting_sample_temp", "starting_ewm", "peak", "air_setpoint", "propane_setpoint", "sampling_flow"]) ],ignore_index=True)
    elif data[0] == "Flush" and (data[7] not in df2.values and data[6] not in df2.values):
        df2 = pd.concat([df2, pd.DataFrame([data], columns = ["type", "date", "time","df_runtime", "flush_duration", "starting_sample_temp", "starting_ewm", "low", "air_setpoint", "propane_setpoint", "sampling_flow"]) ],ignore_index=True)
        
    return [df1, df2]
def pulseToFilePath(series):
    return f'C:\\Users\\Kyan Shlipak\\Documents\\Solenoid Pulse DataFrames\\ {series["type"]} {series["date"]} {series["time"]} {str(series["df_runtime"])} {str(series["pulse_duration"])} {str(series["starting_sample_temp"])} {str(series["starting_ewm"])} {str(series["peak"])} {str(series["air_setpoint"])} {str(series["propane_setpoint"])} {str(series["sampling_flow"])}.pkl'

def flushToFilePath(series):
     return f'C:\\Users\\Kyan Shlipak\\Documents\\Solenoid Pulse DataFrames\\ {series["type"]} {series["date"]} {series["time"]} {str(series["df_runtime"])} {str(series["flush_duration"])} {str(series["starting_sample_temp"])} {str(series["starting_ewm"])} {str(series["low"])} {str(series["air_setpoint"])} {str(series["propane_setpoint"])} {str(series["sampling_flow"])}.pkl'
        
def getDF(filePath):
    try:
        df = pd.read_pickle(filePath)
    except OSError as e:
        items = filePath.split(' ')
        items[-1] = ".pkl"
        newPath = ' '.join(items)
        newPath=newPath.replace(' .pkl','.pkl')
        df =  pd.read_pickle(newPath)
    return df

def commonValue(bccAll):
    vals = []
    for arr in bccAll:
        twoHundreds = []
        for i in arr:
            x = int(i/200)*200
            if x not in twoHundreds:
                twoHundreds.append(x)
        vals.append(twoHundreds)
        
    #print(vals)
    #find common value
    s = None
    for lista in vals:
        if not s:
            s = set(lista)
        else:
            s &= set(lista)
    listS = list(s)
    listS.sort()
    #print(listS[int(len(listS)/2)])
    return(listS[int(len(listS)/2)])

def plotFlushSamePlot(axis, pullRate,paths):
    maxval = 0
    bccAll = []
    for i in range(len(paths)):
        fileName = paths[i].replace('C:\\Users\\Kyan Shlipak\\Documents\\Solenoid Pulse DataFrames\\ ','',1)
        fileName = fileName.replace('.pkl','',1)    
        items = fileName.split(' ')
        if int(float(items[-1])) == pullRate:
            bccAll.append(getDF(paths[i])["bcc ewm"].to_numpy())
            if max(getDF(paths[i])["bcc ewm"].to_numpy()) > maxval: maxval = max(getDF(paths[i])["bcc ewm"].to_numpy())
    plots = []
    
    ys = []
    
    for bccvals in bccAll:
        yhat = savgol_filter(bccvals, 70, 4)
        [m,T] = fit(axis, range(len(yhat)),yhat,(40000,0.01),False)
        x = list(range(len(yhat)))
        y = []
        for i in x:
            y.append(int(m*np.e**(-(T)*i)))
        ys.append(y)

    
    commonval = commonValue(ys)
    
    for bccvals in bccAll:
        yhat = savgol_filter(bccvals, 70, 4)
        commonIndex = np.where((yhat >= commonval - 150) & (yhat <= commonval + 150) )[0][0]
        x = list(range(-commonIndex, -commonIndex+len(yhat)))
            
        #plt.plot(bccvals)
        axis.plot(x,yhat)
        plots.append([x,yhat])
        
    axis.set_ylim([0,maxval+4000])
    return flushLineBestFit(axis, plots)

def monoExp(x, m, t):
    return m * np.exp(-t * x)

def fit(axis, xs,ys,p0,graph):
    xs = np.array(xs)
    startx = int(xs[0])
    xs = xs-startx
    
    # perform the fit
    params, cv = scipy.optimize.curve_fit(monoExp, xs, ys, p0)
    m, t = params

    # determine quality of the fit
    squaredDiffs = np.square(ys - monoExp(xs, m, t))
    squaredDiffsFromMean = np.square(ys - np.mean(ys))
    rSquared = 1 - np.sum(squaredDiffs) / np.sum(squaredDiffsFromMean)
    #print(f"R² = {rSquared}")

    m = round(m,2)
    t = round(t,7)
    # plot the results
    if graph:axis.plot(xs+startx, monoExp(xs, m, t), '--', label=f"Y = {m} * e^(-{t} * x)")
    
    # inspect the parameters
    #print(f"Y = {m} * e^(-{t} * x)")
    return [m,t]
    
def extrapolate():
    pass
        
def flushLineBestFit(axis, flushPlots):
    df = pd.DataFrame(columns = ["x","y"])
    for pair in flushPlots:
        data = {"x":pair[0],"y":pair[1]}
        newdf = pd.DataFrame(data)
        newdf.set_index('x',inplace = True)
        df = pd.concat([df,newdf],axis = 1)
        fit(axis, pair[0],pair[1],(40000,0.01),False)
    df_means = df.mean(axis = 1)
    #df_means.index.tolist()
    vals = []
    vals = np.polyfit(df_means.index.tolist(), df_means.tolist(),2)
    return fit(axis, df_means.index.tolist(), df_means.tolist(), (40000,0.01),True)
                             
def getPeaks(yhat, estimatedLag):
    #find initial peaks
    peaks,t = find_peaks(yhat[:(270+estimatedLag)], distance=60)
    realPeaks = []
            
    #sort out peaks from before the pulse
    ipeaks = []
    for i in range(len(peaks)):
        if peaks[i] > (95+estimatedLag) and peaks[i] < 230+estimatedLag:
            ipeaks.append(peaks[i])
        if len(ipeaks) > 1:
            x = []
            for i in range(len(ipeaks)):
                x.append(yhat[ipeaks[i]])
            ipeaks = [ipeaks[x.index(max(x))]]
    return(ipeaks)
                             
def plotPulseSamePlot(axis, pullRate, maxlines, paths, estimatedLag):
    dis = []
    slopes = []
    colors = ["red","orange","green","blue","purple","magenta","grey","black","brown"]
    newpaths = paths
    sums = []
    for path in range(len(newpaths)):
        bccvals = getDF(newpaths[path])["bcc ewm"].to_numpy()
        fileName = newpaths[path].replace('C:\\Users\\Kyan Shlipak\\Documents\\Solenoid Pulse DataFrames\\ ','',1)
        fileName = fileName.replace('.pkl','',1)    
        items = fileName.split(' ')
        if len(bccvals) >= 400 and int(float(items[-1])) == pullRate:
            yhat = savgol_filter(bccvals, 70, 3)

            #have them all start at the same y 
            #starty = yhat[0]
            minima = argrelextrema(yhat[0:(120+estimatedLag)], np.less)
            minimay = yhat[0:(120+estimatedLag)][argrelextrema(yhat[0:(120+estimatedLag)], np.less)]
            for i in range(len(yhat)):
                yhat[i] = yhat[i] - minimay[-1]
                bccvals[i] = bccvals[i] -  minimay[-1]
            
            
            
            peaks = getPeaks(yhat,estimatedLag)
            axis.plot(peaks[0], yhat[peaks[0]], "o",color ="blue")
            
            #plot line of best fit for beginning
            xfit = list(range((120+estimatedLag)))
            m,b = np.polyfit(xfit,yhat[:(120+estimatedLag)],1)
            yfit = list((val*m+b) for val in xfit)
            #ax3.plot(xfit,yfit,color = colors[path%len(colors)])
            
            #find and plot minima
            minima = argrelextrema(yhat[0:(120+estimatedLag)], np.less)
            minimay = yhat[0:(120+estimatedLag)][argrelextrema(yhat[0:(120+estimatedLag)], np.less)]
            minimaIndex = minima[0][np.where(minimay == min(minimay))[-1][-1]]
            minimaValue =  min(minimay)
            
            axis.plot(minimaIndex,minimaValue,'o',color = 'red')
            
            #find when the plot goes under the initial minima y value
            xstop = 399
            for i in range(peaks[0],400):
                if yhat[i] < minimaValue:
                    xstop = i
                    break
                    
            axis.plot(xstop,yhat[xstop],'o',color = "green")
            
            Sum = 0
            for i in range(minimaIndex,xstop):
                Sum += yhat[i]
            sums.append(Sum)
            
            #calculate average jump
            dis.append(yhat[peaks[0]] - minimaValue)
            slopes.append(m)
            #axis.plot(bccvals)
            axis.plot(yhat,color = colors[path%len(colors)],label = str(round(yhat[peaks[0]] - minimaValue,2)) )
    sums.sort()
    if len(sums) > 1: sums.pop(0)
    if len(sums) > 2:
        if sums[-1] > sums[-2]*4: sums.pop(-1)
    print("sum avg",np.mean(sums))
    return {'area':np.mean(sums),'jump':np.mean(dis)}
    
#fig2.canvas.draw()
#plotFlushSamePlot(ax3, 50)
#plotFlushSamePlot(ax3, 150)
#plotPulseSamePlot(ax3,150,10)
#plotPulseSamePlot(ax4,50,10)