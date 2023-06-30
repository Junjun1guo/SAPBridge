# -*-coding: UTF-8-*-
import matplotlib.pyplot as plt
import numpy as np
import os
import copy
###############################################################################
class Regression():
    def __init__(self, data):
        self.data = data

    def __corrCoeff(self, yestimate, yrecord):
        # correlation coeffient computer
        # input:yestimate--回归得到的预测值（Nx1）列向量
        # yrecord--实验得到的值（Nx1）列向量
        # output:correlation coeffient
        corr = np.corrcoef(yestimate.T, yrecord.T)
        coeff = corr[0, 1]
        return coeff

    def __std(self, yestimate, yrecord):
        SSres = sum(np.array(np.array(yrecord) - np.array(yestimate)) ** 2)
        std = SSres / float(len(yrecord))
        return std ** 0.5

    #######################################
    def __deterCoeff(self, yestimate, Y):
        # compute coeffient of determination R2
        # input:yestimate--回归得到的预测值（Nx1）列向量
        ##Y--实验得到的值（Nx1）列向量
        ##output:R2
        ymean = float(sum(Y)) / len(Y)
        SStot = sum(np.array(np.array(Y) - ymean) ** 2)
        SSres = sum(np.array(np.array(Y) - np.array(yestimate)) ** 2)
        R2 = 1 - np.array(SSres) / SStot
        return R2

    #######################################
    def linearRegression(self):
        # 一般线性回归，data为数据，其中最后一列为y值，x的排序按xo,x1,x2....
        # y=xT*w,其中x为变量列矩阵，w为回归系数列矩阵
        # error=sum((yi-xi.trans*w)**2)
        # w=inv(xTx)*xT*y
        # return:w-regression coeffient coeff-correlation coeffient R2-coeffient of determination
        matdata = np.mat(self.data)
        X = matdata[:, :-1]
        Y = matdata[:, -1]
        xTx = X.T * X
        if np.linalg.det(xTx) == 0.0:
            print("matrix singularity")
            return
        else:
            w = xTx.I * (X.T * Y)
        yestimate = X * w
        # correlation coeffient compute
        coeff = self.__corrCoeff(yestimate, Y)
        std = self.__std(yestimate, Y)

        # compute coeffient of determination R2
        R2 = self.__deterCoeff(yestimate, Y)

        return (w, coeff, R2, yestimate, std)


##############---acceleration (g) to veloctiy (cm/s)---##############
def AccToVelocity(dt, acc):
    """
    from acceleration (g) to velocity (cm/s)
    dt:time interval (s)
    acc: acceleration time history (g/s2)
    vel: velocity time history (cm/s)
    output:vel-velocity time history (cm/s)
    """
    vel = [0]
    num = len(acc)
    for i in range(num - 1):
        velocity = (acc[i] + acc[i + 1]) * dt / float(2) * 981 + vel[-1]
        vel.append(velocity)
    return vel


#############---velocity (cm/s) to displacement (cm)---#############
def VelToDisplacement(dt, vel):
    """
    from velocity (cm/s) to displacement (cm)
    input:dt-time interval(s)
    vel-velocity time history(cm/s)
    output:disp-displacement time history(cm)
    """
    disp = [0]
    num = len(vel)
    for i in range(num - 1):
        displacement = (vel[i] + vel[i + 1]) * dt / float(2) + disp[-1]
        disp.append(displacement)
    return disp


#############---displacement (cm) to velocity (cm/s)---#############
def DispToVelocity(dt, disp):
    """
    from displacement (cm) to velocity (cm/s)
    input:dt-time interval(s)
    disp-displacement time history (cm)
    output:velocity time history(cm/s)
    """
    n = len(disp)
    vel = []
    vel[0] = disp[0] / float(dt)
    for i in range(n - 1):
        vell = (disp[i + 1] - disp[i]) / float(dt)
        vel.append(vell)
    return vel


#############---velocity (cm/s) to acceleration (g/s2)---#############
def VelToAccele(dt, vel):
    """
    from velocity (cm/s) to acceleration (g)
    input:dt-time interval(s)
    vel-velocity time history(cm/s)
    output:acceleration time history(g)
    """
    n = len(vel)
    acc = []
    acc[0] = vel[0] / float(981.0 * float(dt))
    for i in range(n - 1):
        accel = (vel[i + 1] - vel[i]) / float(981.0 * float(dt))
        acc.append(accel)
    return acc


###############################################################################
def polynomialBaseLineCorrect(acc, dt):
    """
    cubic polynomial baseline correction
    Input:
    ---acc-acceleration time history (g)
    ---time interval (sec)
    Output:
    ---corretAcc,corretVel,corretDisp-the filted acceleration (g)
       velocity (cm/s) and displacement (cm)
    """
    acc[0] = 0
    acc[-1] = 0
    x0 = [1 for i1 in range(len(acc))]
    x1 = [dt * i2 for i2 in range(len(acc))]
    x2 = [i3 ** 2 for i3 in x1]
    x3 = [i4 ** 3 for i4 in x1]
    vel = AccToVelocity(dt, acc)
    disp = VelToDisplacement(dt, vel)
    data = np.hstack((np.mat(x0).T, np.mat(x1).T, np.mat(x2).T, np.mat(x3).T,  np.mat(acc).T))
    instance = Regression(data)
    result = instance.linearRegression()
    yest = result[3]
    times = [dt * i5 for i5 in range(len(acc))]
    corretAcc = [acc[i6] - yest[i6, 0] for i6 in range(len(acc))]
    corretVel = AccToVelocity(dt, corretAcc)
    corretDisp = VelToDisplacement(dt, corretVel)
    return corretAcc, corretVel, corretDisp
###############################################################################
###############################################################################
class Sample():
    def __init__(self, bounds, N):
        """
        initial data
        bounds: variable bounds, such as bounds=[(10,21),(21,34)]
        N:sample numbers
        """
        self.bounds = bounds
        self.N = N
        self.D = len(self.bounds)

    def LHSample(self):
        result = np.empty([self.N, self.D])
        temp = np.empty([self.N])
        d = 1.0 / self.N

        for i in range(self.D):

            for j in range(self.N):
                temp[j] = np.random.uniform(
                    low=j * d, high=(j + 1) * d, size=1)[0]

            np.random.shuffle(temp)

            for j in range(self.N):
                result[j, i] = temp[j]

        b = np.array(self.bounds)
        lower_bounds = b[:, 0]
        upper_bounds = b[:, 1]
        if np.any(lower_bounds > upper_bounds):
            print("The parameters low bound value should smaller than the upper bound!")
            return

        #   sample * (upper_bound - lower_bound) + lower_bound
        np.add(np.multiply(result,
                           (upper_bounds - lower_bounds),
                           out=result),
               lower_bounds,
               out=result)

        return result
###############################################################################
###############################################################################
def improvedWuBaseLineCorrect(accFilePath, velFilePath, dispFilePath, t, fileNamei, nIterate, saveAccPath, \
                   saveVelPath, saveDispPath, T3, T1Self=None, T2=None):
    """
	improved Wu et al method for basedline correction
	Wu Y-M, Wu C-F. Approximate recovery of coseismic deformation from Taiwan strong-motion records.
	 Journal of Seismology. 2007;11(2):159-70.
	:param accFilePath: the file path of acceleration
	:param velFilePath: the file path of velocity
	:param dispFilePath: the file path of displacement
	:param t: time interval of motion (s)
	:param fileNamei: fileName of the processed ground motion
	:param nIterate: sample numbers for t2 values
	:param saveAccPath: the save path of processed acceleration
	:param saveVelPath: the save path of processed velocity
	:param saveDispPath: the save path of processed displacement
	:param T3: T3 position in the motion
	:param T1Self: T1 position in the motion, if T1self is none,the program will automatically determine it
	:return: None
	--------------------------------------------------------------------------------------------------------------------
	###---Example
	###provide the acceleration, velocity and displacement paths of the unprocessed motion
    accFilePath='ChiChiEarthquakeAccg/N'
    velFilePath='ChiChiEarthquakeVel/N'
    dispFilePath='ChiChiEarthquakeDisp/N'
    ###provide the save paths for the processed acceleration, velocity and displacement
    saveAccPath='accBaselineCorre/N'
    saveVelPath='velBaselineCorre/N'
    saveDispPath='dispBaselineCorre/N'
    dt=0.005 #time interval (s)
    nIterate=100 # sample size for T2 position from T3 to the end
    fileNamei='TCU084' #file name of unprocessed motion
    # #########################################################################
    # #########################################################################
    #automatically determine T1 and T3,T1=(4500,5500),T3=(5000,7000)
    bounds = [(5000,7000),(5000,9000)]
    NIter=10 #iterate number for T1 and T3
    instance = Sample(bounds, NIter)
    samples =instance.LHSample()
    T1sample=samples[:,0]
    T3sample=samples[:,1]
    T1List=[]
    T2List=[]
    T3List=[]
    fvalueList=[]
    for j1 in range(NIter):
        print(j1)
        ###call the improved Wu et al. method to conduct baseline correction
        T11,T22,T33,fvalue=improvedMethod (accFilePath,velFilePath,dispFilePath,dt,\
                                       fileNamei,nIterate,saveAccPath,saveVelPath,saveDispPath,T3sample[j1],T1sample[j1])
        T1List.append(T11)
        T2List.append(T22)
        T3List.append(T33)
        fvalueList.append(fvalue)
    maxIndex=fvalueList.index(max(fvalueList))
    finalT1=T1List[maxIndex]
    finalT2=T2List[maxIndex]
    finalT3=T3List[maxIndex]
    print("finalT1,T2,T3",finalT1,finalT2,finalT3)
    #########################################################################
    #########################################################################
    T1=finalT1 #T1 position in the motion, if T1=None the program will automatically determine T1
    T3=finalT3 # T3 position in the motion
    T2=finalT2 # T2 position in the motion
    T11,T22,T33,fvalue=improvedMethod (accFilePath,velFilePath,dispFilePath,dt,\
                                           fileNamei,nIterate,saveAccPath,saveVelPath,saveDispPath,T3,T1,T2)
------------------------------------------------------------------------------------------------------------------------
	"""
    cwd = os.getcwd()
    pathAccE = os.path.join(cwd, accFilePath, str(fileNamei) + ".txt")
    txtopenAccE = np.loadtxt(pathAccE)
    copyAccE1 = copy.deepcopy(txtopenAccE)
    T3 = int(T3)
    for i2 in range(len(txtopenAccE)):
        if copyAccE1[i2] * 981 > 50:
            T150 = i2
            break
    pga = max(abs(txtopenAccE)) * 9.81 * 100  # convert acceleration to cm/s2

    if pga > 60:  # only pga>60 cm/s2 it needs baseline correction
        cwd = os.getcwd()
        pathDispE = os.path.join(cwd, dispFilePath,
                                 str(fileNamei) + ".txt")  # upload displacement time history to process
        txtopenDispE = np.loadtxt(pathDispE).tolist()
        lengthTxt = len(txtopenDispE)
        copyDispE = copy.deepcopy(txtopenDispE)
        reversedDispE = copyDispE.reverse()
        # automatically determine T1 position
        for i2 in range(lengthTxt):
            if txtopenDispE[-1] > 0:
                if copyDispE[i2] <= 0:
                    T1 = (lengthTxt - i2 - 1)
                    break
            else:
                if copyDispE[i2] >= 0:
                    T1 = (lengthTxt - i2 - 1)
                    break
        # if T1 position larger than that determined by Iwan etal (1985), then use Iwan's T1 position
        if T150 > T1:
            T1 = T150
        else:
            T1 = T1
        # if users provide T1, and use it in the following process
        if T1Self != None:
            T1 = int(T1Self)
        cwd = os.getcwd()
        pathVelE = os.path.join(cwd, velFilePath, str(fileNamei) + ".txt")
        txtopenVelE = np.loadtxt(pathVelE).tolist()
        v0 = []
        af = []
        fValue = []
        T22 = []
        maxfValue = None
        # randomly generage nIterate intergers between T3 and (lengthTxt-10)
        bounds = [(T3, lengthTxt - 10)]
        instance = Sample(bounds, nIterate)
        samples = list(instance.LHSample()[:, 0])
        if T2 != None:
            T2Index = T2
        else:
            for i3 in range(nIterate):
                # print(i3)
                T2 = int(samples[i3])
                X0 = [1 for x in range(T2, lengthTxt)]
                X1 = [x * t for x in range(T2, lengthTxt)]
                Y = txtopenVelE[T2:lengthTxt]
                hZX11 = np.mat(X0).T
                hZX33 = np.mat(X1).T
                hZY33 = np.mat(Y).T
                velData = np.hstack((hZX11, hZX33, hZY33))
                instanceVel = Regression(velData)
                wtotvel = instanceVel.linearRegression()
                wvel = wtotvel[0].tolist()
                v0vel = wvel[0][0]
                Afvel = wvel[1][0]
                # y=v0vel+Afvel*t
                Amvel = (v0vel + Afvel * T2 * t) / float((T2 - T1) * t)
                accOrignal = [x * 981 for x in txtopenAccE]
                for i4 in range(T1, T2):
                    accOrignal[i4] = accOrignal[i4] - Amvel
                for i5 in range(T2, len(accOrignal)):
                    accOrignal[i5] = accOrignal[i5] - Afvel
                velBaseline = AccToVelocity(t, accOrignal)
                dispBaseline = VelToDisplacement(t, velBaseline)

                X10 = [1 for x in range(T3, lengthTxt)]
                X11 = [x * t for x in range(T3, lengthTxt)]
                Y11 = dispBaseline[T3:lengthTxt]
                hZX1 = np.mat(X10).T
                hZX2 = np.mat(X11).T
                hZY = np.mat(Y11).T
                linerData = np.hstack((hZX1, hZX2, hZY))
                # call linear regression function to fit the displacement from T3 to end
                instance = Regression(linerData)
                wtot = instance.linearRegression()
                w = wtot[0].tolist()  # regression coefficients
                corrcoef = wtot[1]  # correlation coefficient
                var = wtot[4]  # standard deviation
                v00 = w[0][0]  # constant of the regression line
                aff = w[1][0]  # slope of the regression line
                r = corrcoef
                b = abs(aff)
                fvalue = abs(r) / float(b * var ** 2)  # calculate f value
                fValue.append(fvalue)
                v0.append(v00)
                af.append(aff)
                T22.append(T2)
            maxIndex = fValue.index(max(fValue))  # find the maximum f index
            T2Index = T22[maxIndex]  # obtain the optimized T2 position
            maxfValue = max(fValue)
        # conduct baseline correction based on the optimized T2
        X31 = [1 for x in range(T2Index, lengthTxt)]
        X33 = [x * t for x in range(T2Index, lengthTxt)]
        Y3 = txtopenVelE[T2Index:lengthTxt]
        hZX11 = np.mat(X31).T
        hZX33 = np.mat(X33).T
        hZY33 = np.mat(Y3).T
        velData = np.hstack((hZX11, hZX33, hZY33))
        instanceVel = Regression(velData)
        wtotvel = instanceVel.linearRegression()
        wvel = wtotvel[0].tolist()
        v0vel = wvel[0][0]
        Afvel = wvel[1][0]
        # y=v0vel+Afvel*t
        Amvel = (v0vel + Afvel * T2Index * t) / float((T2Index - T1) * t)
        accOrignal = [x * 981 for x in txtopenAccE]
        for i4 in range(T1, T2Index):
            accOrignal[i4] = accOrignal[i4] - Amvel
        for i5 in range(T2Index, len(accOrignal)):
            accOrignal[i5] = accOrignal[i5] - Afvel
        velBaseline = AccToVelocity(t, accOrignal)
        dispBaseline = VelToDisplacement(t, velBaseline)
        accToG = [x / float(981) for x in accOrignal]
        cwd = os.getcwd()
        # save the baseline corrected motion
        pathaccBaseCorreE = os.path.join(cwd, saveAccPath, str(fileNamei) + ".txt")
        np.savetxt(pathaccBaseCorreE, accToG, fmt="%f")

        pathvelBaseCorreE = os.path.join(cwd, saveVelPath, str(fileNamei) + ".txt")
        np.savetxt(pathvelBaseCorreE, velBaseline, fmt="%f")

        pathdispBaseCorreE = os.path.join(cwd, saveDispPath, str(fileNamei) + ".txt")
        np.savetxt(pathdispBaseCorreE, dispBaseline, fmt="%f")
        return T1, T2Index, T3, maxfValue
###############################################################################
###############################################################################
def accFilter(acc,dt,freq_corner,filter_order=4):
    """
    --------------------------------------------------------------------------------------------------------------------
    High pass acceleration filter based on FFT
    --------------------------------------------------------------------------------------------------------------------
    Inputs:
        acc(g)-acceleration time history
        dt(float)-acc time interval
        freq_corner (Hz)-the cut frequency, (Empirical approach，freq_corner=10.0**(1.4071 - 0.3452 * momentMag)  ##In Hz)
        filter_order-butterworth filter order (default value=4)
    """
    acc=list(acc)
    num_steps=len(acc)
    if num_steps % 2 == 1:
        acc+=[0.0]
        num_steps=len(acc)
    padding_duration = 0.5 * 1.5 * filter_order / float(freq_corner)
    num_pads = int(np.ceil(padding_duration / dt))
    accel_padded_1 = np.zeros(num_pads + num_steps + num_pads)
    accel_padded_1[num_pads:(num_steps + num_pads)] = np.array(acc)
    ###---计算归一化的截断频率
    accel_fft = np.fft.fft(accel_padded_1)
    freq = np.fft.fftfreq(len(accel_padded_1),dt).tolist()
    accelFftAbs = abs(accel_fft)
    num_samples = len(accel_fft)
    filter = np.zeros(int((num_samples / 2) + 1))
    for i2 in range(len(filter)):
        tempFreq = (freq[i2] / freq_corner) ** (2.0 * filter_order)
        filter[i2] = np.sqrt(tempFreq / (1.0 + tempFreq))
    highpass_filter = np.zeros(2 * len(filter) - 2)
    highpass_filter[:len(filter)] = filter
    highpass_filter[len(filter):] = filter[1:(len(filter) - 1)][::-1]
    accel_fft_filt = accel_fft * highpass_filter
    filtered_acc = np.real(np.fft.ifft(accel_fft_filt))
    return filtered_acc,num_pads
###############################################################################
###############################################################################
if __name__ == '__main__':
    pass
