import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import argrelextrema
import scipy.optimize
from scipy.signal import find_peaks
from scipy.signal import savgol_filter
import pathlib
dirpath = str(pathlib.Path().resolve())

#create dataframe where each row is a saved panda dataframe. This allows the program to apply filters to all the saved files
def addFileToDF(fileName,df1,df2):
    #get the keywords from the filename and store as 'items'
    fileName = fileName.replace(dirpath + '\\Solenoid Pulse DataFrames\\ ','',1)
    fileName = fileName.replace('.pkl','',1)    
    items = fileName.split(' ')
    
    #convert numbers to floats in order to run numerical operations o them
    data = []
    for item in items:
        try:
            data.append(float(item))
        except ValueError:
            data.append(item)
            
    #compensate for before the pulling flow rate was included as part of the file path
    if len(data) == 10:
        data.append(50)
    
    #add to pulse and flush dataframes while preventing any exact duplicates
    if data[0] == "Pulse" and (data[7] not in df1.values or data[6] not in df1.values):
        df1 = pd.concat([df1, pd.DataFrame([data], columns = ["type", "date", "time","df_runtime", "pulse_duration", "starting_sample_temp", "starting_ewm", "peak", "air_setpoint", "propane_setpoint", "sampling_flow"]) ],ignore_index=True)
    elif data[0] == "Flush" and (data[7] not in df2.values and data[6] not in df2.values):
        df2 = pd.concat([df2, pd.DataFrame([data], columns = ["type", "date", "time","df_runtime", "flush_duration", "starting_sample_temp", "starting_ewm", "low", "air_setpoint", "propane_setpoint", "sampling_flow"]) ],ignore_index=True)
    
    #return one dataframe of all the pulse files and another of all the flush files
    return [df1, df2]

#convert a row from dfpulsefiles to the corresponding file path
def pulseToFilePath(series):
    return dirpath + f'\\Solenoid Pulse DataFrames\\ {series["type"]} {series["date"]} {series["time"]} {str(series["df_runtime"])} {str(series["pulse_duration"])} {str(series["starting_sample_temp"])} {str(series["starting_ewm"])} {str(series["peak"])} {str(series["air_setpoint"])} {str(series["propane_setpoint"])} {str(series["sampling_flow"])}.pkl'

#convert a row from dfflushfiles to the corresponding file path
def flushToFilePath(series):
     return dirpath +  f'\\Solenoid Pulse DataFrames\\ {series["type"]} {series["date"]} {series["time"]} {str(series["df_runtime"])} {str(series["flush_duration"])} {str(series["starting_sample_temp"])} {str(series["starting_ewm"])} {str(series["low"])} {str(series["air_setpoint"])} {str(series["propane_setpoint"])} {str(series["sampling_flow"])}.pkl'
        

#convert from filepath to dataframe
def getDF(filePath):
    try:
        df = pd.read_pickle(filePath)
    except OSError as e: #in case we get an error from mismatching spaces
        items = filePath.split(' ')
        items[-1] = ".pkl"
        newPath = ' '.join(items)
        newPath=newPath.replace(' .pkl','.pkl')
        df =  pd.read_pickle(newPath)
    return df

#find a common value to align decay fits
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



def monoExp(x, m, t):
    return m * np.exp(-t * x)

def fit(axis, xs,ys,p0,graph):
    xs = np.array(xs)
    startx = int(xs[0]) 
    xs = xs-startx # have all plots start with x at x =0
    
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
    if graph:
        axis.plot(xs+startx, monoExp(xs, m, t), '--', label=f"Y = {m} * e^(-{t} * x)")
    
    # inspect the parameters
    #print(f"Y = {m} * e^(-{t} * x)")
    return [m,t]
    
#make exponential decay fit for all the flushes combined
def flushLineBestFit(axis, flushPlots):
    df = pd.DataFrame(columns = ["x","y"])  #dataframe of all the flushes
    for pair in flushPlots:
        data = {"x":pair[0],"y":pair[1]}
        newdf = pd.DataFrame(data)
        newdf.set_index('x',inplace = True)
        df = pd.concat([df,newdf],axis = 1)
                
    df_means = df.mean(axis = 1) #average of all flushes at each x value
    return fit(axis, df_means.index.tolist(), df_means.tolist(), (40000,0.01),True)


def plotFlushSamePlot(axis, pullRate,paths):
    #maximum value in all of the flush plots, use to set ylimit
    maxval = 0
    
    #2d list of smoothed bcc vals
    bccAll = []
    for i in range(len(paths)):
        fileName = paths[i].replace('C:\\Users\\Kyan Shlipak\\Documents\\Solenoid Pulse DataFrames\\ ','',1)
        fileName = fileName.replace('.pkl','',1)    
        items = fileName.split(' ')
    
        #if the df has the same pulling flow rate, add it to bccAll
        if int(float(items[-1])) == pullRate:
            bccAll.append(getDF(paths[i])["bcc ewm"].to_numpy())
            
            #get max value
            if max(getDF(paths[i])["bcc ewm"].to_numpy()) > maxval: maxval = max(getDF(paths[i])["bcc ewm"].to_numpy())
    
    if len(bccAll) >= 1: #if there is at least one matching file

        #2d array of the x and smoothed y vals for ecah plot
        plots = []

        #fitted exponential decay curve for each plot
        ys = []

        #iterate through each list of smoothed flush bcc values 
        for bccvals in bccAll:
            yhat = savgol_filter(bccvals, 70, 4) #savgol list
            [m,T] = fit(axis, range(len(yhat)),yhat,(40000,0.01),False) #variables for fit
            x = list(range(len(yhat))) #x values list
            y = []
            for i in x:
                y.append(int(m*np.e**(-(T)*i))) #get y values based on fit function
            ys.append(y)

        #find a common value for each fit function
        commonval = commonValue(ys)

        #align the flushes according to the commonvalue
        for bccvals in bccAll:
            yhat = savgol_filter(bccvals, 70, 4)
            commonIndex = np.where((yhat >= commonval - 150) & (yhat <= commonval + 150) )[0][0]
            x = list(range(-commonIndex, -commonIndex+len(yhat)))

            #plt.plot(bccvals)
            axis.plot(x,yhat)  #plot flushes
            plots.append([x,yhat])

        axis.set_ylim([0,maxval+4000])
        return flushLineBestFit(axis, plots)
    return [20000,0.002] #return standard values if errors cause no value

#characterize peaks from pulse plots
def getPeaks(yhat, estimatedLag,mindex):
    #find initial peaks
    peaks,t = find_peaks(yhat[:(270+estimatedLag)], distance=60)
    realPeaks = []
            
    #sort out peaks from before the pulse
    ipeaks = []
    for i in range(len(peaks)):
        #only take peaks within acceptable range (not to much before or after the pulse)
        if peaks[i] > mindex and peaks[i] < 230+estimatedLag:
            ipeaks.append(peaks[i])
            
        #if there are multiple peaks, take the higest one
        if len(ipeaks) > 1:
            x = []
            for i in range(len(ipeaks)):
                x.append(yhat[ipeaks[i]])
            ipeaks = [ipeaks[x.index(max(x))]]
    return(ipeaks)
                             

#plot all pulses from the filepaths provided on the same plot
def plotPulseSamePlot(axis, pullRate, maxlines, paths, estimatedLag):
    dis = [] #distance between minima and maxima
    slopes = [] #the slope leading up to the pulse (not used much)
    colors = ["red","orange","yellow","green","aqua","dodgerblue","magenta"]
    newpaths = paths 
    sums = [] #areas under curves
    for path in range(len(newpaths)): #iterate through each path
        bccvals = getDF(newpaths[path])["bcc ewm"].to_numpy() #bcc exponentially weighted mean
        fileName = newpaths[path].replace(dirpath + '\\Solenoid Pulse DataFrames\\ ','',1)
        fileName = fileName.replace('.pkl','',1)    
        items = fileName.split(' ')
        if len(bccvals) >= 400: #make sure the length is at least 400 so can use for charaacterization
            yhat = savgol_filter(bccvals, 70, 3) #savgol filter of the EWM

            #have them all start at the same y 
            #starty = yhat[0]
            minima = argrelextrema(yhat[0:(135+estimatedLag)], np.less) #get x coords of local minima
            minimay = yhat[0:(135+estimatedLag)][argrelextrema(yhat[0:(135+estimatedLag)], np.less)] #get y vals of local minima
            if len(minimay) == 0:
                minima = [[100+estimatedLag]]
                minimay = [yhat[100+estimatedLag]]
            minimaIndex = minima[0][np.where(minimay == min(minimay))[-1][-1]] #get index of lowest minima of the minima
                
            for i in range(len(yhat)):
                #have the plots all start at the same y value (the value of each of their minima)
                yhat[i] = yhat[i] - minimay[-1]
                bccvals[i] = bccvals[i] -  minimay[-1]
            
            #get x coord of peak
            peaks = getPeaks(yhat,estimatedLag,minimaIndex)
            if len(peaks)>0:
                axis.plot(peaks[0], yhat[peaks[0]], "o",color ="blue") #plot where the peak is
            else:
                peaks = [np.where( yhat == max(yhat[140:399]) )[-1][-1] ]
                axis.plot(peaks[0],yhat[peaks[0]],"o",color = "blue")
            
            #plot line of best fit for the 100 seconds before the pule
            xfit = list(range((135+estimatedLag)))
            m,b = np.polyfit(xfit,yhat[:(135+estimatedLag)],1)
            yfit = list((val*m+b) for val in xfit)
            #ax3.plot(xfit,yfit,color = colors[path%len(colors)])

                        #starty = yhat[0]
            minima = argrelextrema(yhat[0:(135+estimatedLag)], np.less) #get x coords of local minima
            minimay = yhat[0:(135+estimatedLag)][argrelextrema(yhat[0:(135+estimatedLag)], np.less)] #get y vals of local minima
            if len(minimay) == 0:
                minima = [[100]]
                minimay = [yhat[100]]

            
            minimaIndex = minima[0][np.where(minimay == min(minimay))[-1][-1]] #get index of lowest minima of the minima
            minimaValue =  min(minimay) #get lowest minima
            
        
            axis.plot(minimaIndex,minimaValue,'o',color = 'red')
            
            #find when the plot goes under the initial minima y value
            xstop = 399
            for i in range(peaks[0],400):
                if yhat[i] < minimaValue:
                    xstop = i
                    break
            
            #plot where the program will stop getting area under curve
            axis.plot(xstop,yhat[xstop],'o',color = "green")
            
            #get area under curve
            Sum = 0
            for i in range(minimaIndex,xstop):
                Sum += yhat[i]
            Sum = abs(Sum)
            sums.append(Sum)
            
            #add jump to list of jumps
            dis.append(yhat[peaks[0]] - minimaValue)
            slopes.append(m)
            #axis.plot(bccvals)
            
            #plot the smoothed pulse
            axis.plot(yhat,color = colors[path%len(colors)],label = str(round(yhat[peaks[0]] - minimaValue,2)) )
    
    #sort area under curve and remove outliers
    sums.sort()
    if len(sums) > 2: sums.pop(0)
    if len(sums) > 2:
        if sums[-1] > sums[-2]*4: sums.pop(-1)
    
    
    print("sum avg",np.mean(sums))
    return {'area':np.mean(sums),'jump':np.mean(dis)}
    
#fig2.canvas.draw()
#plotFlushSamePlot(ax3, 50)
#plotFlushSamePlot(ax3, 150)
#plotPulseSamePlot(ax3,150,10)
#plotPulseSamePlot(ax4,50,10)