# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MRSLab
                                 A QGIS plugin
 Processing SAR data
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-02-03
        git sha              : $Format:%H$
        copyright            : (C) 2020 by MRSLab
        email                : bnarayanarao@iitb.ac.in
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
# from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
# from qgis.PyQt.QtGui import QIcon
# from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import *

from qgis.PyQt import *
from qgis.core import *
import requests
import numpy as np
import multiprocessing

# from PyQt5.QtWidgets import QAction, QMessageBox,QFileDialog
# from qgis.core import (QgsCoordinateReferenceSystem,
#                        QgsCoordinateTransform,
#                        QgsProject,
#                        QgsRectangle,
#                        QgsPointXY,
#                        QgsGeometry,
#                        QgsVectorLayer,
#                        QgsFeature,
#                        QgsMessageLog)
# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .SAR_Tools_dialog import MRSLabDialog
import os.path
from osgeo import gdal
import time
import os.path
# Create a lock for multiprocess
p_lock = multiprocessing.Lock()

############################################################################################################################################
############################################################################################################################################
class Worker(QtCore.QObject):
    '''GRVI '''
    def __init__(self,iFolder,T3,ws):
        QtCore.QObject.__init__(self)
        
        self.iFolder = iFolder
        self.T3 = T3
        self.ws=ws
        self.killed = False
        # self.mainObj = MRSLab()
    def run(self):
        finish_cond = 0
        try:
            def GRVI(T3_stack,ws):
        
                t11_T1 = T3_stack[:,:,0]
                t12_T1 = T3_stack[:,:,1]
                t13_T1 = T3_stack[:,:,2]
                t21_T1 = T3_stack[:,:,3]
                t22_T1 = T3_stack[:,:,4]
                t23_T1 = T3_stack[:,:,5]
                t31_T1 = T3_stack[:,:,6]
                t32_T1 = T3_stack[:,:,7]
                t33_T1 = T3_stack[:,:,8]
                
                nrows  = np.shape(T3_stack)[0]
                ncols = np.shape(T3_stack)[1]
                # nrows  = 100
                # ncols = 100
               
                span = np.zeros((ncols,nrows))
                rho_13_hhvv = np.zeros((ncols,nrows))
                temp_rvi = np.zeros((ncols,nrows))
                fp22 = np.zeros((ncols,nrows))
                GD_t1_t = np.zeros((ncols,nrows))
                GD_t1_d = np.zeros((ncols,nrows))
                GD_t1_rv = np.zeros((ncols,nrows))
                GD_t1_nd = np.zeros((ncols,nrows))
                GD_t1_c = np.zeros((ncols,nrows))
                GD_t1_lh = np.zeros((ncols,nrows))
                GD_t1_rh = np.zeros((ncols,nrows))
                beta = np.zeros((ncols,nrows))
                beta_1 = np.zeros((ncols,nrows))
                f = np.zeros((ncols,nrows))
                a = np.zeros((ncols,nrows))
                b = np.zeros((ncols,nrows))
                temp_gamma = np.zeros((ncols,nrows))
                t_d = np.zeros((46,1))
                t_nd = np.zeros((46,1))
                t_t = np.zeros((46,1))
                t_c = np.zeros((46,1))
                theta_map = np.zeros((ncols,nrows))
                
                D = (1/np.sqrt(2))*np.array([[1,0,1], [1,0,-1],[0,np.sqrt(2),0]])
                # %% for window processing
                wsi=wsj=ws
                
                inci=int(np.fix(wsi/2)) # Up & down movement margin from the central row
                incj=int(np.fix(wsj/2)) # Left & right movement from the central column
                # % Starting row and column fixed by the size of the patch extracted from the image of 21/10/1999
                
                starti=int(np.fix(wsi/2)) # Starting row for window processing
                startj=int(np.fix(wsj/2)) # Starting column for window processing
                
                stopi= int(nrows-inci)-1 # Stop row for window processing
                stopj= int(ncols-incj)-1 # Stop column for window processing
                        # %% Elementary targets
                
                M_d = np.array([[1,0,0,0], [ 0,1,0,0], [ 0,0,-1,0], [ 0,0,0,1]])
                M_nd = np.array([[0.625,0.375,0,0], [ 0.375,0.625,0,0], [ 0,0,-0.5,0], [ 0,0,0,0.5]])
                M_t = np.array([[1,0,0,0], [ 0,1,0,0], [ 0,0,1,0], [ 0, 0,0,-1]])
                M_c = np.array([[0.625,0.375,0,0], [ 0.375,0.625,0,0], [0,0,0.5,0], [ 0,0,0,-0.5]])
                M_lh = np.array([[1,0,0,-1], [ 0,0,0,0], [ 0,0,0,0], [ -1,0,0,1]])
                M_rh = np.array([[1,0,0,1], [ 0,0,0,0], [ 0,0,0,0], [ 1,0,0,1]])
                
                for ii in np.arange(startj,stopj+1):
        
                    # self.progress.emit(str(ii)+'/'+str(nrows))
                    self.pBar.emit(int((ii/nrows)*100))
                    for jj in np.arange(starti,stopi+1):
                
                        t11s = np.nanmean(t11_T1[ii-inci:ii+inci+1,jj-incj:jj+incj+1])#i sample
                        t12s = np.nanmean(t12_T1[ii-inci:ii+inci+1,jj-incj:jj+incj+1])#i sample
                        t13s = np.nanmean(t13_T1[ii-inci:ii+inci+1,jj-incj:jj+incj+1])#i sample
                        
                        t21s = np.nanmean(t21_T1[ii-inci:ii+inci+1,jj-incj:jj+incj+1])#i sample
                        t22s = np.nanmean(t22_T1[ii-inci:ii+inci+1,jj-incj:jj+incj+1])#i sample
                        t23s = np.nanmean(t23_T1[ii-inci:ii+inci+1,jj-incj:jj+incj+1])#i sample
                        
                        t31s = np.nanmean(t31_T1[ii-inci:ii+inci+1,jj-incj:jj+incj+1])#i sample
                        t32s = np.nanmean(t32_T1[ii-inci:ii+inci+1,jj-incj:jj+incj+1])#i sample
                        t33s = np.nanmean(t33_T1[ii-inci:ii+inci+1,jj-incj:jj+incj+1])#i sample
                
                        T_T1 = np.array([[t11s, t12s, t13s], [t21s, t22s, t23s], [t31s, t32s, t33s]])
                
                        #Coherency matrix
                        C_T1 = np.matmul(np.matmul((D.T),T_T1),D);
                        
                        span[ii,jj] = np.real(t11s + t22s + t33s)
                        temp_span = span[ii,jj]
                        # self.progress.emit(str('span Done'))
                        Temp_T1 = T_T1
                        
                        t11 = Temp_T1[0,0]; t12 = Temp_T1[0,1];        t13 = Temp_T1[0,2]
                        t21 = np.conj(t12); t22 = Temp_T1[1,1];        t23 = Temp_T1[1,2]
                        t31 = np.conj(t13); t32 = np.conj(t23);        t33 = Temp_T1[2,2]
                        
                        # %% Ratio of VV/HH (Used in Yamagichi Volume)
                        
                        hh = 0.5*(t11 + t22 + 2*np.real(t12)); #HH
                        hv = t33; #HV
                        vv = 0.5*(t11 + t22 - 2*np.real(t12)); #VV
                        vol_con = 10*np.log10(vv/hh);
                
                
                        # %% Kennaugh Matrix
                        
                        m11 = t11+t22+t33; m12 = t12+t21; m13 = t13+t31; m14 = -1j*(t23 - t32);
                        m21 = t12+t21; m22 = t11+t22-t33; m23 = t23+t32; m24 = -1j*(t13-t31);
                        m31 = t13+t31; m32 = t23+t32; m33 = t11-t22+t33; m34 = 1j*(t12-t21);
                        m41 = -1j*(t23-t32); m42 = -1j*(t13-t31); m43 = 1j*(t12-t21); m44 = -t11+t22+t33;
                        
                        M_T = 0.5*np.array([[m11, m12, m13, m14], [m21, m22, m23, m24], [m31, m32, m33, m34], [m41, m42, m43, m44]]);
                        
                        
                        M_T_theta = M_T;
                        
                        # %% GVSM
                        
                        t011 = M_T_theta[0,0] + M_T_theta[1,1] + M_T_theta[2,2] - M_T_theta[3,3];
                        t012 = M_T_theta[0,1] - 1j*M_T_theta[2,3];
                        t013 = M_T_theta[0,2] + 1j*M_T_theta[1,3];
                        t021 = np.conj(t012);
                        t022 = M_T_theta[0,0] + M_T_theta[1,1] - M_T_theta[2,2] + M_T_theta[3,3];
                        t023 = M_T_theta[1,2] +1j*M_T_theta[0,3];
                        t031 = np.conj(t013);
                        t032 = np.conj(t023);
                        t033 = M_T_theta[0,0] - M_T_theta[1,1] + M_T_theta[2,2] + M_T_theta[3,3];
                        
                        # %% T to C
                        
                        T0 = np.array([[t011/2, t012, t013], [t021, t022/2, t023], [t031, t032, t033/2]]);
                        C0 = np.matmul(np.matmul((D.T),T0),D);
                
                        # %% Gamma/Rho
                        
                        gamma = np.real(C0[0,0]/C0[2,2]); rho = 1/3;
                        temp_gamma[ii,jj]= np.real(gamma); #% variable to save
                        
                        # %% Covariance matrix
                        
                        c11 = gamma; c12 = 0; c13 = rho*np.sqrt(gamma);
                        c21 = 0; c22 = 0.5*(1 + gamma) - rho*np.sqrt(gamma); c23 = 0;
                        c31 = np.conj(rho)*np.sqrt(gamma); c32 = 0; c33 = 1;
                        
                        R = (3/2)*(1 + gamma) - rho*np.sqrt(gamma);
                        C1 = (1/R)*np.array([[c11, c12, c13], [c21, c22, c23], [c31, c32, c33]]);
                        # self.progress.emit(str('gamma and R Done'))
                        # %% Coherency matrix
                        
                        T1 = np.matmul(np.matmul(D,C1),(D.T));
                        
                        t11 = T1[0,0]; t12 = T1[0,1]; t13 = T1[0,2];
                        t21 = T1[1,0]; t22 = T1[1,1]; t23 = T1[1,2];
                        t31 = T1[2,0]; t32 = T1[2,1]; t33 = T1[2,2];
                        
                        m11 = t11+t22+t33; m12 = t12+t21; m13 = t13+t31; m14 = -1j*(t23 - t32);
                        m21 = t12+t21; m22 = t11+t22-t33; m23 = t23+t32; m24 = -1j*(t13-t31);
                        m31 = t13+t31; m32 = t23+t32; m33 = t11-t22+t33; m34 = 1j*(t12-t21);
                        m41 = -1j*(t23-t32); m42 = -1j*(t13-t31); m43 = 1j*(t12-t21); m44 = -t11+t22+t33;
                        
                        # %% Generalized Random Volume (Antropov et al.)
                        
                        M_rv = np.real(np.array([[m11, m12, m13, m14], [m21, m22, m23, m24], [m31, m32, m33, m34], [m41, m42, m43, m44]]));
                        
                        f[ii,jj] = 1;
                
                        # %% GD Volume
                        
                        num1 = np.matmul(((M_T_theta).T),M_rv); #% volume
                        num = np.trace(num1);
                        den1 = np.sqrt(abs(np.trace(np.matmul(((M_T_theta).T),M_T_theta))));
                        den2 = np.sqrt(abs(np.trace(np.matmul(((M_rv).T),M_rv))));
                        den = den1*den2;
                        temp_aa = np.real(2*np.arccos(num/den)*180/np.pi);
                        GD_t1_rv[ii,jj] = np.real(temp_aa/180);
                        # self.progress.emit(str('GD volume Done'))
                        # %% GD ALL
                        
                        num1 = np.matmul(((M_T_theta).T),M_c); #% cylinder
                        num = np.trace(num1);
                        den1 = np.sqrt(abs(np.trace(np.matmul(((M_T_theta).T),M_T_theta))));
                        den2 = np.sqrt(abs(np.trace(np.matmul(((M_c).T),M_c))));
                        den = den1*den2;
                        temp_aa = np.real(2*np.arccos(num/den)*180/np.pi);
                        GD_t1_c[ii,jj] = np.real(temp_aa/180);
                        # self.progress.emit(str('GD cylider Done'))
                        
                        num1 = np.matmul(((M_T_theta).T),M_t); #% trihedral
                        num = np.trace(num1);
                        den1 = np.sqrt(abs(np.trace(np.matmul(((M_T_theta).T),M_T_theta))));
                        den2 = np.sqrt(abs(np.trace(np.matmul(((M_t).T),M_t))));
                        den = den1*den2;
                        temp_aa = 2*np.arccos(num/den)*180/np.pi;
                        GD_t1_t[ii,jj] = np.real(temp_aa/180);
                        # self.progress.emit(str('GD trihedral Done'))
                        
                        num1 = np.matmul(((M_T_theta).T),M_d); #% dihedral
                        num = np.trace(num1);
                        den1 = np.sqrt(abs(np.trace(np.matmul(((M_T_theta).T),M_T_theta))));
                        den2 = np.sqrt(abs(np.trace(np.matmul(((M_d).T),M_d))));
                        den = den1*den2;
                        temp_aa = 2*np.arccos(num/den)*180/np.pi;
                        GD_t1_d[ii,jj] = np.real(temp_aa/180);
                        # self.progress.emit(str('GD dihedral Done'))
                        
                        num1 = np.matmul(((M_T_theta).T),M_nd); #% n-dihedral
                        num = np.trace(num1);
                        den1 = np.sqrt(abs(np.trace(np.matmul(((M_T_theta).T),M_T_theta))));
                        den2 = np.sqrt(abs(np.trace(np.matmul(((M_nd).T),M_nd))));
                        den = den1*den2;
                        temp_aa = 2*np.arccos(num/den)*180/np.pi;
                        GD_t1_nd[ii,jj] = np.real(temp_aa/180);
                        # self.progress.emit(str('GD n-dihedral Done'))
                        
                        # %% VI
                        
                        t_t = GD_t1_t[ii,jj];
                        t_d = GD_t1_d[ii,jj];
                        t_c = GD_t1_c[ii,jj];
                        t_nd = GD_t1_nd[ii,jj];
                        
                        a[ii,jj] = np.nanmax([t_t, t_d, t_c, t_nd]);
                        b[ii,jj] = np.nanmin([t_t, t_d, t_c, t_nd]);
                        beta[ii,jj] = (b[ii,jj]/a[ii,jj])**2;
                        # self.progress.emit(str('Beta val Done'))
                        # %% RVI
                        if np.isnan(np.real(T_T1)).any() or np.isinf(np.real(T_T1)).any() or np.isneginf(np.real(T_T1)).any():
                            T_T1 = np.array([[0,0],[0,0]])
                            temp_rvi[ii,jj] = 0
                            # self.progress.emit(str('invalid Value encountered!!'))
                            continue
                            
                        e_v = -np.sort(-np.linalg.eigvals(T_T1)); # sorting in descending order
                        e_v1 = e_v[0]; e_v2 = e_v[1]; e_v3 = e_v[2];
                        # self.progress.emit(str('Eigen val Done'))
                        
                        p1 = e_v1/(e_v1 + e_v2 + e_v3);
                        p2 = e_v2/(e_v1 + e_v2 + e_v3);
                        p3 = e_v3/(e_v1 + e_v2 + e_v3);
                        
                        p1=0 if p1<0 else p1
                        p2=0 if p2<0 else p2
                        p3=0 if p3<0 else p3
                            
                        p1=1 if p1>1 else p1
                        p2=1 if p2>1 else p2
                        p3=1 if p3>1 else p3
                        
                        
                        
                        temp_rvi[ii,jj] = np.real((4*p3)/(p1 + p2 + p3));
                
                # %% GRVI
                
                vi = np.power(beta, GD_t1_rv)*(1 - (1/f)*GD_t1_rv);
                
                x1 = np.power(beta, GD_t1_rv);
                x2 = (1 - GD_t1_rv);
                
                idx1 = np.argwhere(GD_t1_rv>f)
                vi[idx1] = 0;
                vi[~idx1] = vi[~idx1];
                
                # %% RVI scaled (0 - 1)
                
                rvi = temp_rvi;
                
                idx = np.argwhere(rvi>1)
                
                rvi[idx] = (3/4)*rvi[idx];
                rvi[~idx] = rvi[~idx];
                rvi[rvi==0] = np.NaN
                
                """Write files to disk"""
                ofilervi = self.iFolder+'/RVI.bin'
                infile = self.iFolder+'/T11.bin'
                write_bin(ofilervi,rvi,infile)
                ofilegrvi = self.iFolder+'/GRVI.bin'
                write_bin(ofilegrvi,vi,infile)     
                self.pBar.emit(100)
                self.progress.emit('>>> Finished GRVI calculation!!')
                # self.iface.addRasterLayer(self.inFolder+'\RVI.bin')
                # self.iface.addRasterLayer(self.inFolder+'\GRVI.bin')
                # return rvi,vi 
            
            
            def dop_fp(T3):
        
                DOP = np.zeros([np.size(T3,0),np.size(T3,1)])
                for i in range(np.size(T3,0)):
                    # self.progress.emit('Processed column '+str(i))
                    # stdout.write("\r[%.2f/%d] DOP" % ((i/np.size(T3,0))*100, 100)) 
                    # self.progress.emit(str(i))
                    self.pBar.emit((i/np.size(T3,0))*100)
                    for j in range(np.size(T3,1)):
                        det = np.abs(np.linalg.det(T3[i,j,:].reshape((3, 3))))
                        trace = np.abs(np.trace(T3[i,j,:].reshape((3, 3))))
                        if trace==0:
                            DOP[i][j]=0
                        # elif((27*det/trace**3)>1.0):
                        #     DOP[i][j]=0
                        else:
                            DOP[i][j] = np.sqrt(1-((27*det)/trace**3))
                            # print(DOP[i][j])
                    # stdout.flush()# clear the screen
                        #%%
                # self.progress.connect(self.showmsg)
                dop=DOP
                fname = 'DOP.bin'
                # f1= open(folder+'/'+fname, 'wb')
                # f1.write(bytearray(dop))
                # f1.close()
                dop.astype('float32').tofile(self.inFolder+'/'+fname)
                f2= open(self.inFolder+'/'+fname+'.hdr', 'w')
                header = ["ENVI\n",\
                          "description = {\n",\
                          " File Imported into ENVI.}\n",\
                          "samples = %d\n"%np.size(dop,1),\
                          "lines   = %d\n"%np.size(dop,0),\
                          "bands   = 1\n",\
                          "header offset = 0\n",\
                          "file type = ENVI Standard\n",\
                          "data type = 4\n",\
                          "interleave = bsq\n",\
                          "sensor type = Unknown\n",\
                          "byte order = 0\n",\
                          "wavelength units = Unknown\n"]
                f2.writelines(header)
                f2.close()
                # self.iface.addRasterLayer(self.inFolder+'\DOP.bin')
                self.progress.emit('Finished DOP calculation!!')
            # return DOP
                
            def read_bin(file):
            
                # data, geodata=load_data(file_name, gdal_driver='GTiff')
                ds = gdal.Open(file)
                band = ds.GetRasterBand(1)
                arr = band.ReadAsArray()
                # [cols, rows] = arr.shape
                return arr
            
            def write_bin(file,wdata,refData):
                
                ds = gdal.Open(refData)
                [cols, rows] = wdata.shape
            
                driver = gdal.GetDriverByName("ENVI")
                outdata = driver.Create(file, rows, cols, 1, gdal.GDT_Float32)
                outdata.SetGeoTransform(ds.GetGeoTransform())##sets same geotransform as input
                outdata.SetProjection(ds.GetProjection())##sets same projection as input
                
                outdata.SetDescription(file)
                outdata.GetRasterBand(1).WriteArray(wdata)
                # outdata.GetRasterBand(1).SetNoDataValue(np.NaN)##if you want these values transparent
                outdata.FlushCache() ##saves to disk!!    
        
            # self.dop_fp(self.T3)
            GRVI(self.T3,self.ws)
            
            finish_cond = 1
            
        
        except Exception as e:
            # forward the exception upstream
            self.error.emit(e, traceback.format_exc())
            
        self.finished.emit(finish_cond)
        
    # def kill(self):
    #     self.killed = True
        

        
    """***************************************"""
    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(Exception, str)
    progress = QtCore.pyqtSignal(str)     
    pBar =  QtCore.pyqtSignal(int)             

############################################################################################################################################
############################################################################################################################################
class MRSLab(object):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface


        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'MRSLab_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.dlg = MRSLabDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&SAR tools')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None
        ##################################################################
        # USER VARIABLES
        
        self.inFolder=''
        # self.ws = 5
        
        self.toolbar = self.iface.addToolBar(u'SAR Tools')
        self.toolbar.setObjectName(u'SAR Tools')
        
        
        self.dlg.pb_browse.setEnabled(False)
        self.dlg.le_infolder.setEnabled(False)
        self.dlg.sb_ws.setEnabled(False)
        # self.dlg.lineEdit.clear()

        
    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('MRSLab', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)
        self.Startup()
        

        
        
        self.dlg.pb_browse.clicked.connect(self.openRaster)
        self.dlg.pb_view.clicked.connect(self.viewData)
        self.dlg.clear_terminal.clicked.connect(self.clear_log)
        # self.dlg.pb_dop.clicked.connect(lambda: Worker.dop_fp(self.T3_stack))
        self.dlg.cb_mat_type.currentIndexChanged.connect(self.Cob_mode)
        self.ws = int(self.dlg.sb_ws.value())
        
        self.dlg.pb_process.clicked.connect(self.startWorker)
        
        # self.iface.addRasterLayer(self.inFolder+'\RVI.bin')
        # self.iface.addRasterLayer(self.inFolder+'\GRVI.bin')
        # logger = self.dlg.terminal
        # logger.append('Completed Processing!!')
        
        return action
            

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/SAR_Tools/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Process SAR data'),
            callback=self.run,
            parent=self.iface.mainWindow())


        

    def Cob_mode(self):
        # For terminal outputs
        logger = self.dlg.terminal
        global mat_type

        mat_type=self.dlg.cb_mat_type.currentIndex()
        if mat_type == 1:
            logger.append('\n     Selected Matrix type: T3\n')
            self.dlg.le_infolder.setEnabled(True)
            self.dlg.pb_browse.setEnabled(True)
            self.dlg.sb_ws.setEnabled(True)
        elif mat_type == 2:
            logger.append('\n     Selected Matrix type: C3\n')
            self.dlg.le_infolder.setEnabled(True)
            self.dlg.pb_browse.setEnabled(True)
            self.dlg.sb_ws.setEnabled(True)
        else:
            self.dlg.le_infolder.setEnabled(False)
            self.dlg.pb_browse.setEnabled(False)
            self.dlg.sb_ws.setEnabled(False)
            
            
            
            
    def viewData(self):
        log_text = self.dlg.terminal
        log_text.append('Data loaded in to QGIS\n')
        
        mat_type = self.dlg.cb_mat_type.currentIndex()
        
        if self.inFolder is not None and mat_type==1:
            # self.loadRasters()
            self.iface.addRasterLayer(self.inFolder+'\T11.bin')
            self.iface.addRasterLayer(self.inFolder+'\T22.bin')
            self.iface.addRasterLayer(self.inFolder+'\T33.bin')
            self.iface.addRasterLayer(self.inFolder+'\T12_imag.bin')
            self.iface.addRasterLayer(self.inFolder+'\T12_real.bin')
            self.iface.addRasterLayer(self.inFolder+'\T13_imag.bin')
            self.iface.addRasterLayer(self.inFolder+'\T13_real.bin')
            self.iface.addRasterLayer(self.inFolder+'\T23_imag.bin')
            self.iface.addRasterLayer(self.inFolder+'\T23_real.bin')

            if os.path.isfile(self.inFolder+'\RVI.bin'):
                self.iface.addRasterLayer(self.inFolder+'\RVI.bin')
            if os.path.isfile(self.inFolder+'\GRVI.bin'):
                self.iface.addRasterLayer(self.inFolder+'\GRVI.bin')
                
        elif self.inFolder is not None and mat_type==2:
            self.iface.addRasterLayer(self.inFolder+'\C11.bin')
            self.iface.addRasterLayer(self.inFolder+'\C22.bin')
            self.iface.addRasterLayer(self.inFolder+'\C33.bin')
            self.iface.addRasterLayer(self.inFolder+'\C12_imag.bin')
            self.iface.addRasterLayer(self.inFolder+'\C12_real.bin')
            self.iface.addRasterLayer(self.inFolder+'\C13_imag.bin')
            self.iface.addRasterLayer(self.inFolder+'\C13_real.bin')
            self.iface.addRasterLayer(self.inFolder+'\C23_imag.bin')
            self.iface.addRasterLayer(self.inFolder+'\C23_real.bin')
            if os.path.isfile(self.inFolder+'\RVI.bin'):
                self.iface.addRasterLayer(self.inFolder+'\RVI.bin')
            if os.path.isfile(self.inFolder+'\GRVI.bin'):
                self.iface.addRasterLayer(self.inFolder+'\GRVI.bin')
            
    def clear_log(self):
        self.dlg.terminal.clear()
        self.Startup()
        self.dlg.cb_mat_type.setCurrentIndex(0)
        self.dlg.le_infolder.clear()
        self.dlg.le_infolder.setEnabled(False)
        self.dlg.pb_browse.setEnabled(False)
        self.dlg.progressBar.setValue(0)
        self.dlg.sb_ws.setEnabled(False)
        # log = self.dlg.terminal
        # log.append('MRS Lab\n')
        
    def showmsg(self, signal):
        log = self.dlg.terminal
        log.append(str(signal))  
        
    def T3_C3(self,T3_stack):
        nrows = np.size(T3_stack,0)
        ncols = np.size(T3_stack,1)
        C3_stack = np.zeros(np.shape(T3_stack),dtype=np.complex64)
        "Special Unitary Matrix"
        D = (1/np.sqrt(2))*np.array([[1,0,1], [1,0,-1],[0,np.sqrt(2),0]])
        for i in range(nrows):
            # self.dlg.terminal.append('>>> '+str(i)+'/'+str(nrows))
            self.dlg.progressBar.setValue(int((i/nrows)*100))
            for j in range(ncols):
                T3 = T3_stack[i,j,:]
                T3 = np.reshape(T3,(3,3))
                C3 = np.matmul(np.matmul((D.T),T3),D);
                C3_stack[i,j,:] = C3.flatten()
                
        self.dlg.progressBar.setValue(100)
        return C3_stack
    
    def C3_T3(self,C3_stack):
        nrows = np.size(C3_stack,0)
        ncols = np.size(C3_stack,1)
        T3_stack = np.zeros(np.shape(C3_stack),dtype=np.complex64)
        "Special Unitary Matrix"
        D = (1/np.sqrt(2))*np.array([[1,0,1], [1,0,-1],[0,np.sqrt(2),0]])
        for i in range(nrows):
            # self.dlg.terminal.append('>>> '+str(i)+'/'+str(nrows))
            self.dlg.progressBar.setValue(int((i/nrows)*100))
            for j in range(ncols):
                C3 = C3_stack[i,j,:]
                C3 = np.reshape(C3,(3,3))
                T3 = np.matmul(np.matmul((D),C3),D.T);
                T3_stack[i,j,:] = T3.flatten()
        self.dlg.progressBar.setValue(100)
        return T3_stack
    
    def openRaster(self):
        """Open raster from file dialog"""
        
        self.inFolder =str(QFileDialog.getExistingDirectory(self.dlg, "Select T3/C3 Folder"))
        self.dlg.le_infolder.setText(self.inFolder)
        # print(self.inFolder)
        mat_type = self.dlg.cb_mat_type.currentIndex()
        logger = self.dlg.terminal
        
        if self.inFolder is not None and mat_type==1:
            
            self.T3_stack = self.load_T3(self.inFolder)
            logger.append('>>> T3 Loaded \nConverting T3 to C3...')
            self.C3_stack  = self.T3_C3(self.T3_stack)
            logger.append('>>> Ready to process.')
            
        elif self.inFolder is not None and mat_type==2:

            logger.append('>>> C3 selected')
            self.C3_stack = self.load_C3(self.inFolder)
            logger.append('>>> C3 Loaded \nConverting C3 to T3...')
            self.T3_stack  = self.C3_T3(self.C3_stack)
            logger.append('>>> Ready to process.')
            
    def load_C3(self,folder):
        
        C11 = self.read_bin(folder+"\C11.bin")
        C22 = self.read_bin(folder+"\C22.bin")
        C33 = self.read_bin(folder+"\C33.bin")

        C12_i = self.read_bin(folder+'\C12_imag.bin')
        C12_r = self.read_bin(folder+'\C12_real.bin')
        C13_i = self.read_bin(folder+'\C13_imag.bin')
        C13_r = self.read_bin(folder+'\C13_real.bin')
        C23_i = self.read_bin(folder+'\C23_imag.bin')
        C23_r = self.read_bin(folder+'\C23_real.bin')
            
        C12 = C12_r + 1j*C12_i
        C13 = C13_r + 1j*C13_i
        C23 = C23_r + 1j*C23_i
        
        return np.dstack((C11,C12,C13,np.conj(C12),C22,C23,np.conj(C13),np.conj(C23),C33))
    
    
    def load_T3(self,folder):
        
        T11 = self.read_bin(folder+"\T11.bin")
        T22 = self.read_bin(folder+"\T22.bin")
        T33 = self.read_bin(folder+"\T33.bin")

        T12_i = self.read_bin(folder+'\T12_imag.bin')
        T12_r = self.read_bin(folder+'\T12_real.bin')
        T13_i = self.read_bin(folder+'\T13_imag.bin')
        T13_r = self.read_bin(folder+'\T13_real.bin')
        T23_i = self.read_bin(folder+'\T23_imag.bin')
        T23_r = self.read_bin(folder+'\T23_real.bin')
            
        T12 = T12_r + 1j*T12_i
        T13 = T13_r + 1j*T13_i
        T23 = T23_r + 1j*T23_i
        
        return np.dstack((T11,T12,T13,np.conj(T12),T22,T23,np.conj(T13),np.conj(T23),T33))
    
    def read_bin(self,file):

        # data, geodata=load_data(file_name, gdal_driver='GTiff')
        ds = gdal.Open(file)
        band = ds.GetRasterBand(1)
        arr = band.ReadAsArray()
        # [cols, rows] = arr.shape
    
        return arr 

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&SAR tools'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = MRSLabDialog()
        
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
        
    def Startup(self):
        # For terminal outputs
        logger = self.dlg.terminal
        logger.append('   Welcome to SARtools. A QGIS plugin to calculate GRVI (Generalized Volume Vegetation Index) \n')
        logger.append('       Let\'s get started --> Start with Selecting polarimetric matrix\n')
        

    
    
    def startWorker(self):
        # worker = Worker(ip_user, custom, custom_names, browse, browse_selected_obj, browse_selected_ext_obj, browse_selected_mode, shape_path, if_clip)
        
        # mat_type=self.dlg.cb_mat_type.currentIndex()
        # if mat_type==2:
        #     self.
        
        self.dlg.terminal.append('>>> Calculating GRVI...')
        worker = Worker(self.inFolder,self.T3_stack,self.ws)

        # start the worker in a new thread
        thread = QtCore.QThread()
        worker.moveToThread(thread)
        # self.workerFinished =1
        worker.finished.connect(self.workerFinished)
        worker.error.connect(self.workerError)

        worker.progress.connect(self.showmsg)
        worker.pBar.connect(self.pBarupdate)
        thread.started.connect(worker.run)
        thread.start()
        
        self.thread = thread
        self.worker = worker
        # time.sleep(0.1)
        # worker.kill
            
    def pBarupdate(self, signal):
        pB = self.dlg.progressBar
        pB.setValue(int(signal))
        # log.append(str(signal))  

    def workerFinished(self,finish_cond):
        logger = self.dlg.terminal
        logger.append('>>> Process completed with window size of '+str(self.ws))
        # clean up the worker and thread
        self.viewData()
        self.worker.deleteLater()
        self.thread.quit()
        self.thread.wait()
        self.thread.deleteLater()

        if finish_cond == 0:
            logger.append('>>> Process stopped in between ! You are good to go again.')

    def workerError(self, e, exception_string):
        logger = self.dlg.terminal
        logger.append('>>> :-( Error:\n\n %s' %str(exception_string))
    
    
    
    # progress = QtCore.pyqtSignal(str)