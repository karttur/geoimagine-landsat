'''
Created on 7 Oct 2018

@author: thomasgumbricht
'''

#import geoimagine.gis.mj_gis_v80 as mj_gis
import geoimagine.zipper.explode as zipper
import geoimagine.support.karttur_dt as mj_dt
#from geoimagine.kartturmain import RasterProcess
#import geoimagine.sentinel.gml_transform as gml_transform
from geoimagine.kartturmain import Composition, LayerCommon, RasterLayer
from geoimagine.support import ConvertLandsatScenesToStr,EarthSunDist
from geoimagine.mask import SingleBandMasking

#from sentinelsat.sentinel import SentinelAPI
import os
#import xml.etree.ElementTree as ET
from shutil import rmtree, move, copyfileobj
import urllib.request
import shutil
import subprocess
import landsatxplore
import numpy as np
import math
import gc

class AtmCorr:
    '''class for atmospheric correction of multi spectral image'''  
    def __init__(self, process, session, verbose):
        self.session = session
        self.verbose = verbose
        self.process = process
        print (self.process.proc.processid) 
        
    def _DNtoSRFI(self, sceneD, srcLayerD, calD, wlD, imgAttr):
        '''
        '''
        self.lsatprodid = sceneD['lsatprodid']
        #if this scene has a p value skip
        paramL = ['p','p2']
        queryD = {'lsatprodid':self.lsatprodid}
        p = self.session._SelectSceneDos(queryD,paramL)

        if p != None:
            return
        self.srcLayerD = srcLayerD
        #self.icRL = self.process.params.icRL
        self.wtBL = self.process.params.wtBL
        self.powFacC = self.process.params.powFacC
        self.msfac = self.process.params.msfac
        #self.cRL = self.icRL
        #self.icRLm1 = self.cRL-1
        self.esdist = imgAttr['esdist']
        self.sunelev = imgAttr['sunelev']
        self.sitoafac = math.sin(math.radians(imgAttr['sunelev'] )) / imgAttr['esdist']**2
        self.calD = calD
        self.wlD = wlD
        self.imgAttr = imgAttr
        self.cumHistoD = {}
        self.hedgeD = {}
        self.edgeD = {}
        for band in srcLayerD:
            self.hedgeD[band] = 0.001
            self.calD[band]['he'] = self.hedgeD[band]
                
        #Set the sunfactor 
        self._SunFactor()
        queryD = {'lsatprodid':self.lsatprodid}
        self.paramL =  ['band','minhisto','maxhisto','he','dnhelo','dnhehi','toahelo','chavez','srfpath','dnpath']
        recs = self.session._SelectBandDos(queryD,self.paramL)

        if len(recs) < len(self.srcLayerD):
            for band in self.srcLayerD:
                #Calculate the cumulative histo
                self._CumHisto(band)
            edgeres = self._FindEdge()
            if not edgeres:
                for band in ['bl','gl','rl']:
                    if self.calD[band]['toahelo'] <= 0:
                        print ('Trial1 failure')
                        self._plothisto()
                        edgeres = self._FindEdge(['bl','gl','rl'], maxdelta=0.05, maxmaxdelta=1.0)
                        self._plothisto()
                        for band in self.srcLayerD:
                            if self.calD[band]['toahelo'] <= 0:
                                print ('Total failure') 
                                return
                p = self._GetSRFPath()
                
                p = self._CalcSRFPath()
                
                p2 = self._SetSRFpaths(p)
                self._FitSRFPathToModel(p)
                print ('error p',self.calD['rl']['he'],p)
                self._testplot2(p)
                BALLE

                return False
            
        else:
            for b in recs:
                band = b[0]
                for n,item in enumerate(self.paramL):
                    self.calD[band][item] = b[n]
                    
            p = self._GetSRFPath()
            if self.process.params.powfacmin < p < self.process.params.powfacmax:
                return
            if not self.process.overwrite:
                return

        print ('BAND DOS')
        for band in self.calD:
            print (band, calD[band])
        p = self._CalcSRFPath()
        if not p:
            return
        '''
        #Calculate the c-factor
        self._CalcFacC(p)
        '''
        
    def _DOStoSRFI(self, sceneD, srcLayerD, calD, wlD, imgAttr):
        '''
        '''
        self.lsatprodid = sceneD['lsatprodid']
        #if this scene has a p value skip
        paramL = ['p','p2']
        queryD = {'lsatprodid':self.lsatprodid}
        p = self.session._SelectSceneDos(queryD,paramL)
        
        if p != None:
            return
        self.srcLayerD = srcLayerD
        #self.icRL = self.process.params.icRL
        self.wtBL = self.process.params.wtBL
        self.powFacC = self.process.params.powFacC
        self.msfac = self.process.params.msfac
        #self.cRL = self.icRL
        #self.icRLm1 = self.cRL-1
        self.esdist = imgAttr['esdist']
        self.sunelev = imgAttr['sunelev']
        self.sitoafac = math.sin(math.radians(imgAttr['sunelev'] )) / imgAttr['esdist']**2
        self.calD = calD
        self.wlD = wlD
        self.imgAttr = imgAttr
        self.cumHistoD = {}
                
        #Set the sunfactor 
        self._SunFactor()
        queryD = {'lsatprodid':self.lsatprodid}
        self.paramL =  ['band','minhisto','maxhisto','he','dnhelo','dnhehi','toahelo','chavez','srfpath','dnpath']
        recs = self.session._SelectBandDos(queryD,self.paramL)

        if len(recs) < len(self.srcLayerD):
            for band in self.srcLayerD:
                self.calD[band]['dnhelo'] = self.process.proc.paramsD[band]
                self._MapTOAReflectance(band, 'dnhelo')
                
            p = self._GetSRFPath()
            
            p = self._CalcSRFPath()
            self._testplot2(p)
            self._plothisto()
            
            p2 = self._SetSRFpaths(p)
            self._FitSRFPathToModel(p)

            self._testplot2(p)
            BALLE


            
        else:
            for b in recs:
                band = b[0]
                for n,item in enumerate(self.paramL):
                    self.calD[band][item] = b[n]
                    
            p = self._GetSRFPath()
            self._FitSRFPathToModel(p)
            self._testplot2(p)
            self._plothisto()
            if self.process.params.powfacmin < p < self.process.params.powfacmax:
                return
            if not self.process.overwrite:
                return

        print ('BAND DOS')
        for band in self.calD:
            print (band, calD[band])
        p = self._CalcSRFPath()
        if not p:
            return
        '''
        #Calculate the c-factor
        self._CalcFacC(p)
        '''
        
    def _FindEdge(self, checkBandL = False, maxdelta=0,maxmaxdelta=0):
        
        if not maxdelta:
            maxdelta = 0.05
        if not checkBandL:
            checkBandL = ['bl','gl','rl']
        loop = 0
        okflag = True
        while True:
            blerror = False
            glerror = False
            okflag = True
            self._HistoDOS()
            print ('innerloop:',loop)
            loop += 1
            
            for band in self.calD:
                print (band, self.calD[band])
            
            for b in checkBandL:
                if b in self.srcLayerD and self.calD[b]['toahelo'] < 0:
                    okflag = False
                    if not maxmaxdelta:
                        maxdelta = 0.5
                    else:
                        maxdelta = maxmaxdelta
            if 'bl' in self.srcLayerD and self.calD['bl']['toahelo'] < self.calD['gl']['toahelo']:
                okflag = False
                blerror = True
            if self.calD['gl']['toahelo'] < self.calD['rl']['toahelo']:
                okflag = False
                glerror = True
            
            
            for band in self.srcLayerD:
                self.hedgeD[band] += 0.0005
                self.calD[band]['he'] = self.hedgeD[band]
            if self.hedgeD['rl'] > maxdelta:
                break
            if okflag:
                break
            else:
                
                if blerror or glerror:
                    if blerror:
                        self.hedgeD['bl'] += 0.0005
                        self.calD['bl']['he'] = self.hedgeD['bl']
                    if glerror:
                        self.hedgeD['gl'] += 0.0005
                        self.calD['gl']['he'] = self.hedgeD['gl']

                    if not maxmaxdelta:
                        maxdelta = 0.5
                    else:
                        maxdelta = maxmaxdelta
                    
        if not okflag:
            print('WARNING, this scene cannot be solved at the moment',self.lsatprodid)
            return False
        return True
        
    def _HistoDOS(self):
        for band in self.srcLayerD:
            #Calculate dark and bright edges
            self._DarkEdge(band)
            self._BrightEdge(band)
            self._MapTOAReflectance(band, 'dnhelo')
            
    def _CalcFacC(self,p):
        for band in self.calD:
            c = 1+self.icRLm1 * math.pow(self.wlD[band]['wl'], p)
            if band == 'me': c *= 1.1
            if band == 'mf': c *= 1.5
            if band == 'mg': c *= 2.4
            c *= self.msfac
            self.calD[band]['cfac'] = c
       
    def _SunFactor(self):
        self.sunfactor = math.sin(math.radians(self.imgAttr['sunelev']))
            
    def _CumHisto(self,band):
        #print (self.srcLayerD[band].FPN)
        #self.srcLayerD[band].RasterOpenGetFirstLayer()
        if band in self.cumHistoD:
            return
        self.srcLayerD[band].ReadRasterLayer()
        null =  self.srcLayerD[band].comp.cellnull
        BAND = self.srcLayerD[band].layer.NPBAND.astype(np.int)
        #Get the max histo
        maxHisto = np.amax(BAND)
        #print ('null', null)
        #print ('band',BAND)
        
        if null == maxHisto:
            FIGUREOUTSOLUTION
        
        #Set null to maxHist+1
        BAND[BAND==null] = maxHisto+1
        #print ('band',BAND)

        minHisto = np.amin(BAND)

        nbins = maxHisto-minHisto
        self.calD[band]['offset'] = minHisto
        self.calD[band]['minhisto'] = minHisto
        self.calD[band]['maxhisto'] = maxHisto
        histo = np.histogram(BAND, bins=nbins, range=[minHisto,maxHisto])[0]

        cumHisto = np.empty((nbins), dtype=float)
        sumfq = sum(histo)
        #The first cumulative histo is only itself
        cumHisto[0] = histo[0] * 100 / sumfq
        for j in range (1,nbins):
            jm1 = j-1
            cumHisto[j] = cumHisto[jm1] + histo[j] * 100 / sumfq
        self.cumHistoD[band] = cumHisto
        
    def _DarkEdge(self,band):  
        dnhe = 0
        nbins = len(self.cumHistoD[band]) 
        for j in range (nbins-2):
            jp1 = j+1
            delta1 = self.cumHistoD[band][jp1]-self.cumHistoD[band][j]
            if band == 'bl':
                print ('hedge',self.hedgeD[band])
                print ('delta',j,delta1,self.cumHistoD[band][j],self.cumHistoD[band][jp1])
            if delta1 > self.hedgeD[band]:
                if band == 'bl':
                    print('    set',jp1)
                self.calD[band]['histo'] = self.cumHistoD[band][jp1+self.calD[band]['offset']]
                dnhe = jp1
                break
        #Convert back to actual value by adding the offset
        dnhe += self.calD[band]['offset']

        self.calD[band]['dnhelo'] = dnhe
        
    def _SearchDarkEdge(self,band,dnmin):  
        dnhe = 0
        nbins = len(self.cumHistoD[band]) 
        for j in range (nbins-2):
            jp1 = j+1
            delta1 = self.cumHistoD[band][jp1]-self.cumHistoD[band][j]
            if delta1 > self.hedgeD[band]: 
                dnhe = jp1+self.calD[band]['offset']
                break
        #Convert back to actual value by adding the offset
        dnhe += self.calD[band]['offset']
  
    def _BrightEdge(self,band):
        dnhe = 0
        nbins = len(self.cumHistoD[band]) 
        for j in range (nbins):
            if self.cumHistoD[band][j] > 99.9:
                dnhe = j-1
                break
            
        #Convert back to actual value by adding the offset
        dnhe += self.calD[band]['offset']
        self.calD[band]['dnhehi'] = dnhe
    
    def _MapTOAReflectance(self, band, edge):
        dn = self.calD[band][edge]
        if dn == self.srcLayerD[band].comp.cellnull:
            return self.dstLayerD[band].comp.srcCellNull
        toa = self.calD[band]['reflgain']*dn+self.calD[band]['reflbias'] 
        toa /= self.sunfactor
        item = edge.replace('dn','toa')
        self.calD[band][item] = toa
    
    def _MapDN(self,band,toa):
        toa = toa*self.sunfactor
        dn = (toa-self.calD[band]['reflbias'])/self.calD[band]['reflgain'] 
        return int(round(dn))
        
    def _CalcSRFPath(self):
        '''
        '''
        p = self._GetSRFPath()

        if self.process.params.powfacmin < p < self.process.params.powfacmax:
            p2 = self._SetSRFpaths(p)
            self._FitSRFPathToModel(p)
            insertD = {'lsatprodid':self.lsatprodid,'p':p,'p2':p2}
            self.session._InsertSceneDos(insertD, self.process.overwrite, self.process.delete)
            print ('p is ok',p)
            return p      
        elif p > self.process.params.powfacmax:
            print ('ini p is too large',p)
            for band in self.srcLayerD:
                self._CumHisto(band)
            edgeres = self._FindEdge()
            if not edgeres:
                p = self._GetSRFPath()
                self._FitSRFPathToModel(p)
                print ('error p',self.calD['rl']['he'],p)
                self._testplot2(p)
                self._plothisto()
                BALLE

                return False
            p = self._GetSRFPath()
            minp = p
            minhe = self.hedgeD['rl']
            
            #Test the theoretical p-value of other bands
            #Check the value of he, if less than 1%, find better dark edge
            if self.calD['rl']['he'] < 0.01:
                
                outerloop = 0
                while self.calD['rl']['he'] < 0.01:
                    print ('outerloop',outerloop)  
                    outerloop += 1
                    for band in self.srcLayerD:
                        self.hedgeD[band] += 0.0005
                        self.calD[band]['he'] = self.hedgeD[band]
                    edgeres = self._FindEdge()
                    if not edgeres:
                        p = self._GetSRFPath()
                        self._FitSRFPathToModel(p)
                        print ('error p',self.calD['rl']['he'],p)
                        self._testplot2(p)
                        BALLE
        
                        return False
                    p = self._GetSRFPath()
                    
                    self._PowVsDOS(p)
                    print ('new p',self.calD['rl']['he'],p)
                    if p < minp:
                        minp = p
                        minhe = self.hedgeD['rl']
                    if self.process.params.powfacmin < p < self.process.params.powfacmax:    
                        break
                    
                if p <= self.process.params.powfacmax:
                    print ('accepting he for p', p)

                    edgeres = self._FindEdge()
                    if not edgeres:
                        p = self._GetSRFPath()
                        self._FitSRFPathToModel(p)
                        print ('error p',self.calD['rl']['he'],p)
                        self._testplot2(p)
                        BALLE
        
                        return False
                    p = self._GetSRFPath()
                    self._FitSRFPathToModel(p)
                    print ('final p',self.calD['rl']['he'],p)
                    self._testplot2(p)

                    p2 = self._SetSRFpaths(p)
                    insertD = {'lsatprodid':self.lsatprodid,'p':p,'p2':p2}
                    self.session._InsertSceneDos(insertD, self.process.overwrite, self.process.delete)
                    return p
                else:
                    if minhe:
                        for band in self.srcLayerD:
                            self.hedgeD[band] = minhe
                            self.calD[band]['he'] = self.hedgeD[band]
                    edgeres = self._FindEdge()
                    if not edgeres:
                        p = self._GetSRFPath()
                        self._FitSRFPathToModel(p)
                        print ('error p',self.calD['rl']['he'],p)
                        self._testplot2(p)
                        BALLE
        
                        return False
                    p = self._GetSRFPath()
                    print ('best p',self.calD['rl']['he'],p)
    
                    #Set p to average of 'rl' and one longer band
                    pL = []
                    for b in self.pD:
                        if b in ['ma','mb','mc']:
                            pL.append(self.pD[b])
                    if len(pL) == 0:
                        mp = 2.2714
                    else:
                        mp = sum(pL)/(len(pL))
                    
                    p = (2*p + mp)/3
                    if p < 2.2714:
                        p = 2.2714
                    p2 = self._FitSRFPathToModel(p)   
                    self._testplot2(p)
                    if p < 5: 
                        insertD = {'lsatprodid':self.lsatprodid,'p':p,'p2':p2}
                        self.session._InsertSceneDos(insertD, self.process.overwrite, self.process.delete)
                        return p
                    return False
        elif p < self.process.params.powfacmax:
            print ('ini p is too small',p)
            
            for band in self.srcLayerD:
                self._CumHisto(band)
            edgeres = self._FindEdge()
            if not edgeres:
                p = self._GetSRFPath()
                self._FitSRFPathToModel(p)
                self._PowVsDOS(p)
                print ('error p',self.calD['rl']['he'],p)
                self._testplot2(p)
                self._plothisto()
                BALLE
                

                return False
            

                
            p = self._GetSRFPath()
            maxp = p
            maxhe = self.hedgeD['rl']
            
            #Test the theoretical p-value of other bands
            #Check the value of he, if less than 1%, find better dark edge
            if self.calD['rl']['he'] < 0.01:
                for band in self.srcLayerD:
                    self._CumHisto(band)
                outerloop = 0
                while self.calD['rl']['he'] < 0.01:
                    print ('outerloop',outerloop)
                    outerloop += 1
                    for band in self.srcLayerD:
                        self.hedgeD[band] += 0.0005
                        self.calD[band]['he'] = self.hedgeD[band]
                    edgeres = self._FindEdge()
                    if not edgeres:
                        p = self._GetSRFPath()
                        self._FitSRFPathToModel(p)
                        print ('error p',self.calD['rl']['he'],p)
                        self._testplot2(p)
                        BALLE
        
                        return False
                    p = self._GetSRFPath()
                    self._PowVsDOS(p)
                    print ('new p',self.calD['rl']['he'],p)
                    if p > maxp:
                        maxp = p
                        maxhe = self.hedgeD['rl']
                    if self.process.params.powfacmin < p < self.process.params.powfacmax:    
                        break
                    
                if p >= self.process.params.powfacmin:
                    print ('accepting he for p', p)

                    edgeres = self._FindEdge()
                    if not edgeres:
                        p = self._GetSRFPath()
                        self._FitSRFPathToModel(p)
                        print ('error p',self.calD['rl']['he'],p)
                        self._testplot2(p)
                        BALLE
        
                        return False
                    p = self._GetSRFPath()
                    self._FitSRFPathToModel(p)
                    print ('final p',self.calD['rl']['he'],p)
                    self._testplot2(p)

                    p2 = self._SetSRFpaths(p)
                    insertD = {'lsatprodid':self.lsatprodid,'p':p,'p2':p2}
                    self.session._InsertSceneDos(insertD, self.process.overwrite, self.process.delete)

                else:
                    if maxhe:
                        for band in self.srcLayerD:
                            self.hedgeD[band] = maxhe
                            self.calD[band]['he'] = self.hedgeD[band]
                    edgeres = self._FindEdge()
                    if not edgeres:
                        p = self._GetSRFPath()
                        self._FitSRFPathToModel(p)
                        print ('error p',self.calD['rl']['he'],p)
                        self._testplot2(p)
                        BALLE
        
                        return False
                    p = self._GetSRFPath()
                    print ('best p',self.calD['rl']['he'],p)
    
                    #Set p to average of 'rl' and one longer band
                    pL = []
                    for b in self.pD:
                        if b in ['ma','mb','mc']:
                            pL.append(self.pD[b])
                    if len(pL) == 0:
                        mp = 2.2714
                    else:
                        mp = sum(pL)/(len(pL))
                    
                    p = (p*2 + mp)/3
                    if p < 2.2714:
                        p = 2.2714
                    p2 = self._FitSRFPathToModel(p)
                    self._testplot2(p)
                    if p < 5:
                        
                        insertD = {'lsatprodid':self.lsatprodid,'p':p,'p2':p2}
                        self.session._InsertSceneDos(insertD, self.process.overwrite, self.process.delete)


    def _GetSRFPath(self):
        '''
        '''
        #Get the default darke edge SRF path for gl
        srfpathGL1 = self.calD['gl']['toahelo']
        wLenV = wLenGL = self.wlD['gl']['wl'] 
        srfpathV = srfpathGL1
        #check if the key blue exists in the calibDict 
        if 'bl' in self.calD:
            #Get the default darke edge SRF path for bl
            srfpathBL1 = self.calD['bl']['toahelo']
            wLenV = self.wtBL * self.wlD['bl']['wl'] + (1 - self.wtBL) * wLenGL
            srfpathV = (srfpathBL1 + srfpathGL1) / 2
        logsrfpathV = math.log(srfpathV)
        self.pD = {}
        for band in self.srcLayerD:
            if self.wlD[band]['wl'] <= self.wlD['gl']['wl']:
                continue
            if self.calD[band]['toahelo'] <= 0:
                continue
            logsrfpath = math.log(self.calD[band]['toahelo'])
            loglogwl = math.log(self.wlD[band]['wl'] / wLenV)
            difoflogs = logsrfpathV - logsrfpath
                 
            self.pD[band] = difoflogs / loglogwl

        p = self.pD['rl']
        return (p)

    def _FitSRFPathToModel(self,p):
        p2 = p*0.8
        for b in self.srcLayerD:
            #Set SRFpath using the assigned p value
            ##fitpath = self.calD[b]['toahelo'] * pow((self.wlD['rl']['wl'] / self.wlD[b]['wl']),p)
            if self.wlD[b]['wl'] <= self.wlD['gl']['wl']:
                fitpath = self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / self.wlD[b]['wl']),p)
            else:
                fitpath = self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / self.wlD[b]['wl']),p2)
            self.calD[b]['fitpath'] = fitpath
        return p2

    def _PowVsDOS(self,p):
        p2 = p*0.8
        #iterate over all bands
        for b in self.srcLayerD:
            if self.wlD[b]['wl'] < 0.745:              
                srfpath2 =  self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / self.wlD[b]['wl']),p)
            else:
                srfpath2 =  self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / self.wlD[b]['wl']),p2)                                           
            srfpath1 = self.calD[b]['toahelo']          
            srfpath = min(srfpath1, srfpath2) 
            #path must be positive
            srfpath = max(srfpath, 0) 
            
            dnpath = self._MapDN(b,srfpath)       

            self.calD[b]['chavez'] = srfpath2
            self.calD[b]['srfpath'] = srfpath
            self.calD[b]['dnpath'] = dnpath  
        return p2

    def _SetSRFpaths(self,p):
        '''
        '''
        p2 = self._PowVsDOS(p)
        #iterate over all bands
        for b in self.srcLayerD:
            insertD = {'lsatprodid':self.lsatprodid,'band':b}
            queryL = ['minhisto','maxhisto','he','dnhelo','dnhehi','toahelo','chavez','srfpath','dnpath'] 
            for key in self.calD[b]:
                if key in queryL:
                    insertD[key] = self.calD[b][key]
            self.session._InsertBandDos(insertD, self.process.overwrite, self.process.delete)
        return p2

                
    def _testplot(self,p):
        
        import matplotlib.pyplot as plt

        #p = 2.2714
        p2 = p*0.8
        A = np.linspace(0.450, 2.300, num=50)
                
        B = self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / A),p)
        C = self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / A),p2)
        
        D = self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / A),2.2714)
        E = self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / A),(2.2714*0.8))
        MASK = (A > self.wlD['rl']['wl'])
        CHAVEZ = np.copy(B)
        CHAVEZ[MASK] = C[MASK]
        
        MASK = (A > self.wlD['rl']['wl'])
        CHAVEZ0 = np.copy(D)
        CHAVEZ0[MASK] = E[MASK]
        x = []
        y = []
        y0 = []
        for b in self.calD:
            y.append(self.calD[b]['srfpath'])
            y0.append(self.calD[b]['toahelo'])
            x.append(self.wlD[b]['wl'])

        x = np.array(x)
        y = np.array(y)

        #slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
        #line = slope*x+intercept
        
        #plt.plot(x,y,'o', x, line)
        #plt.show()
        plt.plot(x,y0,'o', A, CHAVEZ0)
        plt.plot(x,y,'o', A, CHAVEZ)
        plt.show()
        '''
        BALLE
        #pylab.title('Linear Fit with Matplotlib')
        ax = plt.gca()
        ax.set_axis_bgcolor((0.898, 0.898, 0.898))
        fig = plt.gcf()
        py.plot_mpl(fig, filename='linear-Fit-with-matplotlib')



        #y = np.log(y)
        z = np.polyfit(x, y, 1)
        
        p = np.poly1d(z)
        
        xp = np.linspace(x.min(), x.max(), 100)
        
        plt.plot(x, y, '.', xp, p(xp), '-')
        #plt.xlim(np.amax(x), np.amin(x))  # decreasing 
        plt.show()
        '''

    def _testplot2(self,p):
        import matplotlib.pyplot as plt

        
        A = np.linspace(0.450, 2.300, num=50)
        if p:
            p2 = p*0.8
            B = self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / A),p)
            C = self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / A),p2)
            MASK = (A > self.wlD['rl']['wl'])
            CHAVEZ = np.copy(B)
            CHAVEZ[MASK] = C[MASK]
        
        D = self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / A),2.2714)
        E = self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / A),(2.2714*0.8))
        
        MASK = (A > self.wlD['rl']['wl'])
        CHAVEZ0 = np.copy(D)
        CHAVEZ0[MASK] = E[MASK]
        
        x = []
        y = []
        y0 = []
        y1 = []
        for b in self.srcLayerD:
            x.append(self.wlD[b]['wl'])

            y0.append(self.calD[b]['toahelo'])
            if p:
                y.append(self.calD[b]['srfpath'])
                y1.append(self.calD[b]['fitpath'])
            

        x = np.array(x)
        y = np.array(y)

        plt.plot(x,y,'mo', markersize=8,label='power law')
        "DOS to be plotted later to be on top"
        plt.plot(x,y0,'ko',markersize=6,label='DOS')
        if p:
            plt.plot(x,y1,'bo',markersize=4,label='fitted')
        plt.plot(A, CHAVEZ0, '-r', label='Chavez')
        if p:
            plt.plot(A, CHAVEZ, '-b', label='fitted')
        plt.legend(loc='upper right')
        if p:
            at = 'p = %(p)1.2f' %{'p':p}
            plt.annotate(at, xy=(1.0,0.04) )
        plt.show()
        
    def _plothisto(self):
        import matplotlib.pyplot as plt
        #xmax = 0
        yD = {}
        xD = {}
        cD = {'rl':'r','gl':'g','bl':'b','na':'y','mb':'c','mc':'m'}
        for band in self.srcLayerD:
            xD[band] =  np.arange(len(self.cumHistoD[band]))
            yD[band] = self.cumHistoD[band]
            dotlayout = '%so' %(cD[band])
            linelayout = '%s-' %(cD[band])
            plt.plot(self.calD[band]['dnhelo'],self.calD[band]['histo'],dotlayout,label=band)
            plt.plot(np.arange(len(self.cumHistoD[band])),self.cumHistoD[band],linelayout)
            
        plt.legend(loc='upper left')
        plt.title(self.lsatprodid)
 
        plt.show()


        