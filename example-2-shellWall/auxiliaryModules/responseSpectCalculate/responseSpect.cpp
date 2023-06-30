// responseSpect.cpp : 定义 DLL 应用程序的导出函数。
//

#include "stdafx.h"
#include <math.h>
#include <vector>
#include <iostream>
using namespace std;
#define PI acos(-1)

extern "C" _declspec(dllexport) void responseSpect(double beta,double dt,double* Tarray,\
	double* accArray,int accLength,int Tsize,double m,double* SaArray,double* SvArray,double* SdArray);

void responseSpect(double beta, double dt, double* Tarray, \
	double* accArray,int accLength, int Tsize,double m, double* SaArray, double* SvArray, double* SdArray)
	//Calculate acc,vel and disp response spectra,not pesudo response spectra
	//input:beta-damping ratio; dt-time interval; Tarray-point to period array with double type;
	//      accArray-point to acceleration time history (g) array;accLength-the length of acceleration array;
	//      Tsize-The size of period array; m-the mass of SDOF;SaArray-point to an array to store acc spectra;
	//      SvArray-point to an array to store vel spectra;SdArray-point to an array to store disp spectra;
{
	vector<double> accVecotor;
	double temp0;
	for (int i0 = 0; i0 < accLength; i0++)
	{
		temp0 = accArray[i0] * 9.81;
		accVecotor.push_back(temp0);
	}
	double r,b;
	r = 0.5;
	b = 0.25;
	double k,w0,c,acc0,a1,a2,a3,k1;
	int num1;
	double ptemp, disptemp, velTemp, accTemp;
	for (int i1 = 0; i1 <Tsize; i1++)
	{
		k = pow((2.0*PI / Tarray[i1]),2)*m;
		w0 = 2.0*PI / Tarray[i1];
		c = 2.0*m*w0*beta;
		double* accList = new double[accLength];
		double* velList = new double[accLength];
		double* dispList = new double[accLength];
		velList[0] = 0.0;
		dispList[0] = 0.0;
		acc0 = (accVecotor[0] - c * velList[0] - k * dispList[0]) / m;
		accList[0] = acc0;
		a1 = m / (b*dt*dt) + r * c / (b*dt);
		a2 = m / (b*dt) + (r / b - 1.0)*c;
		a3 = (1.0 / (2.0*b) - 1)*m + dt * c*(r / (2.0*b) - 1.0);
		k1 = k + a1;
		num1 = accLength - 1;
		for (int j1 = 0; j1 < num1; j1++)
		{
			ptemp = -accVecotor[j1 + 1] + a1 *dispList[j1] + a2 * velList[j1] + a3 *accList[j1];
			disptemp = ptemp / k1;
			dispList[j1 + 1] = disptemp;
			velTemp = r * (dispList[j1+1]-dispList[j1]) / (b*dt) + (1.0 - r / b)*velList[j1] +\
				dt *accList[j1]*(1.0 - r / (2.0*b));
			velList[j1 + 1] = velTemp;
			accTemp = (dispList[j1+1]-dispList[j1]) / (b*dt*dt) -velList[j1]/ (b*dt) \
				- accList[j1]*(1.0 / (2.0*b) - 1.0);
			accList[j1 + 1] = accTemp;

		}
		double maxAcc = 0.0, maxVel = 0.0, maxDisp = 0.0;
		for (int i2 = 0; i2 < accLength; i2++)
		{
			if (fabs(velList[i2]) > maxVel)
				maxVel = fabs(velList[i2]);
			if (fabs(dispList[i2]) > maxDisp)
				maxDisp = fabs(dispList[i2]);
			if (fabs(accList[i2] + accVecotor[i2]) > maxAcc)
				maxAcc = fabs(accList[i2] + accVecotor[i2]);
		}
		SaArray[i1] = maxAcc / 9.81;
		SvArray[i1] = maxVel * 100;
		SdArray[i1] = maxDisp * 100;
		
		delete[] accList;
		delete[] velList;
		delete[] dispList;
	}
}


