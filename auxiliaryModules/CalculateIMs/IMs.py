# -*- coding: utf-8 -*-
import numpy as np
import math
from .responseSpectMain import SaSvSd
############################################################
class IMs():
	"""
	地震动强度指标计算
	"""
	def __init__(self,acc,t):
		"""
		类的初始化
		:param acc: 加速度时程（g)
		:param t:采样间隔（s)
		"""
		self.acc=acc
		self.t=t
		self.num=len(self.acc)
	###############################
	def PGA(self):
		"""
		:return: 地震动峰值加速度(g)
		"""
		pga=np.fabs(self.acc).max()
		return pga
	###############################
	def AcctoVelocity (self):
		"""
		:return: 加速度时程转为速度时程(cm/s)
		"""
		vel=[0]
		acc=self.acc
		for i in range(self.num-1):
			velocity=(acc[i]+acc[i+1])*self.t/2*981+vel[-1]
			vel.append(velocity)
		return vel
	###############################
	def PGV (self):
		"""
		:return:地震动峰值速度(cm/s)
		"""
		veloc=self.AcctoVelocity()
		pgv=np.fabs(veloc).max()
		return pgv
	###############################
	def AcctoDisp(self):
		"""
		:return: 加速度时程转为位移时程(cm)
		"""
		disp = [0]
		veld = self.veloc = self.AcctoVelocity()
		for i in range(self.num - 1):
			displacement = (veld[i] + veld[i + 1]) * self.t / 2 + disp[-1]
			disp.append(displacement)
		return disp
	###############################
	def PGD(self):
		"""
		:return: 地震动峰值位移（cm)
		"""
		dispc = self.AcctoDisp()
		pgd = np.fabs(dispc).max()
		return pgd
	###############################
	def VmaxDivAmax(self):
		"""
		:return:峰值速度与峰值加速度比值(s)
		"""
		vmax = self.PGV()
		amax = self.PGA() * 981
		ratio = vmax / amax
		return ratio
	###############################
	def aRMS(self):
		"""
		:return: 加速度均方根(g)
		"""
		a2 = np.array(self.acc ** 2)
		ttol = self.num * self.t
		atol = sum(a2) * self.t
		arms = (atol / ttol) ** 0.5
		return arms
	###############################
	def vRMS(self):
		"""
		:return:速度均方根(cm/s)
		"""
		vel = np.array(self.AcctoVelocity())
		vel2 = vel ** 2
		ttol = self.num * self.t
		vtol = sum(vel2) * self.t
		vrms = (vtol / ttol) ** 0.5
		return vrms
	###############################
	def dRMS(self):
		"""
		:return: 位移均方根(cm)
		"""
		disp = np.array(self.AcctoDisp())
		disp2 = disp ** 2
		ttol = self.num * self.t
		dtol = sum(disp2) * self.t
		drms = (dtol / ttol) ** 0.5
		return drms
	###############################
	def AI(self):
		"""
		:return:Arias轻度（m/s)
		"""
		a2 = self.acc * 9.81
		a3 = np.array(a2)
		a3tol = sum(a3 ** 2) * self.t
		ai = a3tol * math.pi / (2 * 9.81)
		return ai
	###############################
	def Ic(self):
		"""
		:return:特征强度(g3/2*s1/2)
		"""
		ttol = self.num * self.t
		Ic = (self.aRMS()) ** (1.5) * (ttol) ** 0.5
		return Ic
	###############################
	def SED(self):
		"""
		:return: 比能密度(cm2/s)
		"""
		vel = self.AcctoVelocity()
		velarr = np.array(vel)
		sed = sum(velarr ** 2) * self.t
		return sed
	###############################
	def CAV(self):
		"""
		:return:累计绝对速度（cm/s)
		"""
		accarr = np.array(self.acc)
		accabs = np.fabs(accarr) * 981
		cav = sum(accabs) * self.t
		return cav
	###############################
	def DisptoVelocity(self, displacement, t):
		"""
		将位移时程（cm)转为速度时程(cm/s)
		:param displacement: 位移时程(cm)
		:param t: 采样间隔(s)
		:return: 速度时程(cm/s)
		"""
		n = len(displacement)
		vel = [0]
		disp = displacement
		for i in range(n - 1):
			vell = 2 * (disp[i + 1] - disp[i]) / t - vel[-1]
			vel.append(vell)
		return vel
	###############################
	def VeltoAccele (self,vel,t):
		"""
		速度时程(cm/s)转换为加速度时程(g)
		:param vel: 速度时程（cm/s)
		:param t: 采样间隔(s)
		:return: 加速度时程(g)
		"""
		n = len(vel)
		acc = [0]
		for i in range(n - 1):
			accel = (vel[i + 1] - vel[i]) / (981 * float(dt))
			acc.append(accel)
		return acc
	###############################
	def ASI(self):
		"""
		:return:加速度谱强度(g*s)
		"""
		T=np.arange(0.1,0.52,0.02)
		Tr,Sar,Svr,Sdr= self.calResponseSpe(1, T, 0.05)
		asi = sum(Sar) * 0.02
		return asi
	###############################
	def calResponseSpe (self,m,T,beta):
		"""
		:param m:单自由度质量，默认为11
		:param T:周期列表(s)
		:param beta:阻尼比
		:return:周期点，绝对加速度（g)，速度(cm/s)及位移峰值(cm)
		"""
		sa,sv,sd = responseSpectMain.SaSvSd(self.acc,self.t, T, beta)
		return T,sa,sv,sd
	###############################
	def VSI(self):
		"""
		:return:速度谱强度（cm)
		"""
		T = np.arange(0.1, 2.52, 0.02)
		Tr, Sar, Svr, Sdr = self.calResponseSpe(1, T, 0.05)
		vsi = sum(Svr) * 0.02
		return vsi
	###############################
	def __SMR (self,response):
		#this parameter gives the sustained maximum acceleration/velocity during three cycles,
		#and is defined as the third highest absolute value of acceleration/velocity in the time-history
		#(note: in order for an absolute value to be considered as a "maximum", it must be larger than values 20 steps before and 20 steps after).
		#Nuttli O.W. [1979] "The relation of sustained maximum ground acceleration and velocity to earthquake intensity and magnitude,
		#" Miscellaneous Paper S-71-1, Report 16, U.S. Army Corps of Engineers, Waterways Experiment Station, Vicksburg, Mississippi.
		a=response
		aBefore=a[0:19]
		aAfter=a[-20:-1]
		aMiddle=a[20:-21]
		b=[]
		c=[]
		for i in range(len(aMiddle)-1):
			if aMiddle[i]*aMiddle[i+1]<0:
				b.append(i)
		for i in np.arange(0,len(b)-1,1):
			c.append(np.fabs(aMiddle[b[i]:b[i+1]]).max())
		c.sort()
		return c[-3]
	###############################
	def SMA(self):
		"""
		:return: 持续最大加速度(g),加速度时程绝对值第三高值
		"""
		sma = self.__SMR(self.acc)
		return sma
	###############################
	def SMV (self):
		"""
		:return: 持续最大速度(cm/s)，速度时程绝对值第三高值
		"""
		smv=self.__SMR(self.AcctoVelocity ())
		return smv
	###############################
	def A95 (self):
		#The acceleration level below which 95% of the total Arias intensity is contained.
		#In other words, if the entire accelerogram yields a value of Ia equal to 100, the
		#A95 parameter is the threshold of acceleration such that integrating all the values
		#of the accelerogram below it, one gets an Ia=95. (g)
		ai=self.AI()
		threshold=0.95*ai
		acc=np.fabs(self.acc*9.81)
		t=self.t
		acc.sort()
		acclist=[0]
		for i in range(len(acc)):
			acclist.append((math.pi/(2*9.81))*(acc[i]**2*self.t)+acclist[-1])
		for i in range(len(acclist)):
			if acclist[i]>=threshold:
				a95=acc[i-1]/9.81
				break
		return a95
	###############################
	def Ia (self):
		#Compound acc.-related IM  (g.s**1/3)
		#Riddell R, Garcia J (2001) Hysteretic energy spectrum and damage control. Earthq Eng Struct Dyn30(12):1791–1816
		#Ia=PGA*(td**1/3) td=t2-t1   t1=t(5%AI)  t2=t(95%AI)
		ai=self.AI()
		thresholdt1=0.05*ai
		thresholdt2=0.95*ai
		t=self.t
		acc=self.acc*9.81
		acclist=[0]
		t1=[]
		t2=[]
		for i in range(len(acc)):
			acclist.append((math.pi/(2*9.81))*(acc[i]**2*self.t)+acclist[-1])
		for i1 in range(len(acclist)):
			if acclist[i1]>=thresholdt1:
				t1.append(i1*t)
				break
		for i2 in range(len(acclist)):
			if acclist[i2]>=thresholdt2:
				t2.append(i2*t)
				break
		td=t2[0]-t1[0]
		pga=self.PGA()
		Ia=pga*(td**(1.0/3.0))
		return Ia
	###############################
	def FI (self):
		#Fajfar intensity  (cm/s**0.75)
		#Fajfar P, Vidic T, Fischinger M (1990) A measure of earthquake motion capacity to damage medium-period
		#structures. Soil Dyn Earthq Eng 9(5):236–242
		#FI=PGV*td**0.25   td=t2-t1   t1=t(5%AI)  t2=t(95%AI)
		ai=self.AI()
		thresholdt1=0.05*ai
		thresholdt2=0.95*ai
		t=self.t
		acc=self.acc*9.81
		acclist=[0]
		t1=[]
		t2=[]
		for i in range(len(acc)):
			acclist.append((math.pi/(2*9.81))*(acc[i]**2*self.t)+acclist[-1])
		for i1 in range(len(acclist)):
			if acclist[i1]>=thresholdt1:
				t1.append(i1*t)
				break
		for i2 in range(len(acclist)):
			if acclist[i2]>=thresholdt2:
				t2.append(i2*t)
				break
		td=t2[0]-t1[0]
		pgv=self.PGV()
		fi=pgv*(td**(0.25))
		return fi
	###############################
	def Iv (self):
		#Compound vel.-related IM (cm**2/3)/s**1/3
		#Riddell R, Garcia J (2001) Hysteretic energy spectrum and damage control. Earthq Eng Struct Dyn
		#30(12):1791–1816
		#IvPGV**(2/3)*td(1/3)
		ai=self.AI()
		thresholdt1=0.05*ai
		thresholdt2=0.95*ai
		t=self.t
		acc=self.acc*9.81
		acclist=[0]
		t1=[]
		t2=[]
		for i in range(len(acc)):
			acclist.append((math.pi/(2*9.81))*(acc[i]**2*self.t)+acclist[-1])
		for i1 in range(len(acclist)):
			if acclist[i1]>=thresholdt1:
				t1.append(i1*t)
				break
		for i2 in range(len(acclist)):
			if acclist[i2]>=thresholdt2:
				t2.append(i2*t)
				break
		td=t2[0]-t1[0]
		pgv=self.PGV()
		Iv=pgv**(2.0/3.0)*(td**(1.0/3.0))
		return Iv
	###############################
	def Id (self):
		#Compound disp.-related IM (cm.s**1/3)
		##Riddell R, Garcia J (2001) Hysteretic energy spectrum and damage control. Earthq Eng Struct Dyn
		#30(12):1791–1816
		#Id=PGD*td**1/3
		ai=self.AI()
		thresholdt1=0.05*ai
		thresholdt2=0.95*ai
		t=self.t
		acc=self.acc*9.81
		acclist=[0]
		t1=[]
		t2=[]
		for i in range(len(acc)):
			acclist.append((math.pi/(2*9.81))*(acc[i]**2*self.t)+acclist[-1])
		for i1 in range(len(acclist)):
			if acclist[i1]>=thresholdt1:
				t1.append(i1*t)
				break
		for i2 in range(len(acclist)):
			if acclist[i2]>=thresholdt2:
				t2.append(i2*t)
				break
		td=t2[0]-t1[0]
		pgd=self.PGD()
		Id=pgd*(td**(1.0/3.0))
		return Id
#################################################
if __name__=='__main__':
	acc = np.loadtxt("1.txt")
	imInstance = IMs(acc, 0.01)
	print("PGA:",imInstance.PGA())
	print("PGV:", imInstance.PGV())
	print("PGD:", imInstance.PGD())
	print("vmax/amax:", imInstance.VmaxDivAmax())
	print("aRMS:", imInstance.aRMS())
	print("vRMS:", imInstance.vRMS())
	print("dRMS:", imInstance.dRMS())
	print("AI:", imInstance.AI())
	print("Ic:", imInstance.Ic())
	print("SED:", imInstance.SED())
	print("CAV:", imInstance.CAV())
	print("ASI:", imInstance.ASI())
	print("VSI:", imInstance.VSI())
	print("SMA:", imInstance.SMA())
	print("SMV:", imInstance.SMV())
	print("A95:", imInstance.A95())
	print("Ia:", imInstance.Ia())
	print("FI:", imInstance.FI())
	print("Iv:", imInstance.Iv())
	print("Id:", imInstance.Id())





































