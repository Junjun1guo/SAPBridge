#-*-coding: UTF-8-*-
#########################################################################
#  Author: Junjun Guo
#  E-mail: guojj@tongji.edu.cn/guojj_ce@163.com
#  Environemet: Successfully excucted in python 3.8
#########################################################################
#import necessary modules
from .responseSpectWrapper import returnSaSvSd
import numpy as np

def SaSvSd(acc,dt,T,beta):
	"""
	acceleration,velocity and displacement response spectra calculation
	:param acc:acceleration time history(g)
	:param dt:time interval(s)
	:param T:periods list
	:param beta:damping ratio
	:return:Sa(g),Sv(cm/s),Sd(cm)
	"""
	m=1
	Tarray=T
	accArray=acc.tolist()
	accLength=len(accArray)
	Tsizes=len(T)
	SaArray = np.zeros((Tsizes,), dtype=np.float).tolist()
	SvArray = np.zeros((Tsizes,), dtype=np.float).tolist()
	SdArray = np.zeros((Tsizes,), dtype=np.float).tolist()
	Sa, Sv, Sd = returnSaSvSd(beta, dt, Tarray, accArray, accLength, Tsizes, m, SaArray, SvArray, SdArray)
	return Sa[:],Sv[:],Sd[:]
