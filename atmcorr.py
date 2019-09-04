'''
Created on 7 Oct 2018

@author: thomasgumbricht
'''

import matplotlib.pyplot as plt
import array as arr
#import geoimagine.gis.mj_gis_v80 as mj_gis
import geoimagine.zipper.explode as zipper
import geoimagine.support.karttur_dt as mj_dt
#from geoimagine.kartturmain import RasterProcess
#import geoimagine.sentinel.gml_transform as gml_transform
from geoimagine.kartturmain import Composition, LayerCommon, RasterLayer
from geoimagine.support import ConvertLandsatScenesToStr,EarthSunDist,Today
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
    def __init__(self, process, session, verbose, lsatscene):
        '''TGTODO this should be inherented to Landsat rather than being its own class
        '''
        self.session = session
        self.verbose = verbose
        self.process = process
        self.lsatscene = lsatscene
        print (self.process.proc.processid)
            
    def _SetParams(self,sceneD,srcLayerD,dstLayerD,imgAttr,wlD,calD):
        self.lsatprodid = sceneD['lsatprodid']
        #if this scene has a p value skip
        paramL = ['rlp','multip','method']
        queryD = {'lsatprodid':self.lsatprodid}
        p = self.session._SelectSceneDos(queryD,paramL)

        #if p != None:
        #    return 
        self.srcLayerD = srcLayerD
        self.dstLayerD = dstLayerD
        self.icRL = self.process.params.icRL
        self.cRL = self.icRL
        self.icRLm1 = self.cRL-1
        
        self.wtBL = self.process.params.wtBL
        self.powFacC = self.process.params.powFacC
        self.msfac = self.process.params.msfac
        
        
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
        self.paramL =  ['band','minhisto','maxhisto','he','dnhelo','dnhehi','dospath','dosdn',
                        'chavezpath','chavezdn','parispath','parisdn','rlfitpath','rlfitdn','multifitpath','multifitdn']

        recs = self.session._SelectBandDos(queryD,self.paramL) 

        return p, recs
        
    def _DNtoSRFI(self, sceneD, srcLayerD, dstLayerD, calD, wlD, imgAttr):
        '''
        '''
        p, recs = self._SetParams(sceneD,srcLayerD,dstLayerD,imgAttr,wlD,calD)
        print ('p',p)
        print ('recs',recs)

        
        recbands = [r[0] for r in recs]

        self.hedgeD = {}
        self.edgeD = {}
        for band in srcLayerD:
            self.hedgeD[band] = 0.001
            self.calD[band]['he'] = self.hedgeD[band]
        #If the band histograms are already done
        if all(band in recbands for band in self.srcLayerD):
            #All bands have dark edges defined
            for b in recs:
                band = b[0]
                for n,item in enumerate(self.paramL):
                    self.calD[band][item] = b[n]
            p = self._AnalyseDOS()
            if self.process.params.powfacmin < p < self.process.params.powfacmax:
                self._SaveAcceptedTuning(p,'rl')

            else:
                print ('        reading data and analysing histogram')
                for band in self.srcLayerD:
                    print (self.srcLayerD[band].FPN)
                SNULLE
                for band in self.srcLayerD:
                    #Calculate the cumulative histo
                    self._CumHisto(band)
                self._Tuning()
            
        else:     
            #no data on dark edges, 
            #get the histogram
            print ('        reading data and analysing histogram')
            for band in self.srcLayerD:
                if not os.path.isfile(self.srcLayerD[band].FPN):
                    self.session._UpdateSceneStatus({'column':'organized', 'status': 'N'})
                    self.session._UpdateSceneStatus({'column':'exploded', 'status': 'N'})


            for band in self.srcLayerD:
                #Calculate the cumulative histo
                self._CumHisto(band)
            self._Tuning()

        
    def _DOStoSRFI(self, sceneD, srcLayerD, calD, wlD, imgAttr):
        '''
        '''
        p,recs = self._SetParams(sceneD,srcLayerD,imgAttr,wlD,calD)
        recbands = [r[0] for r in recs]
        #If the band histograms are already done
        if all(band in self.srcLayerD for band in recbands):
            #All bands have dark edges defined
            for b in recs:
                band = b[0]
                for n,item in enumerate(self.paramL):
                    self.calD[band][item] = b[n]
                print (self.calD[band])
            p = self._AnalyseDOS()
            if self.process.params.powfacmin < p < self.process.params.powfacmax:
                p2 = p*0.8
                insertD = {'lsatprodid':self.lsatprodid,'p':p,'p2':p2}
                self.session._InsertSceneDos(insertD, self.process.overwrite, self.process.delete)
            else:
                self._CumHisto(band)
                self._Tuning()
            
        else:
            #no data on dark edges, 
            #get the histogram
            for band in self.srcLayerD:
                #Calculate the cumulative histo
                self._CumHisto(band)
                self._Tuning()
             
    def _SRFIfromDOS(self, sceneD, srcLayerD, dstLayerD, calD, wlD, imgAttr, suffix):
        '''
        '''
        self.suffix = suffix
        p,recs = self._SetParams(sceneD,srcLayerD,dstLayerD,imgAttr,wlD,calD)
        #print ('p',p)
        #print ('recs',recs)

        #self.dstLayerD = dstLayerD
        '''
        self.calD = calD
        self.wlD = wlD
        self.imgAttr = imgAttr
        self.lsatprodid = sceneD['lsatprodid']
        self.msfac = self.process.params.msfac
        self.cRL = self.process.params.icRL
        self.icRLm1 = self.cRL-1
        self._SunFactor()
        queryD = {'lsatprodid':self.lsatprodid}
        
        self.paramL =  ['rlp','multip']

        recs = self.session._SelectSceneDos(queryD,self.paramL)
        '''
        if p == None:
            RUNANALYSISONTHEFLY
        
        self._CreateSRFIfromDN(p, recs)
         
    def _CreateSRFIfromDN(self, p, recs):
            
        rlp, multip, method = p

        #Decide on which power factor to use
        if self.process.params.powfacdef == 'multi':
            powfac = multip
        elif self.process.params.powfacdef == 'rl':
            powfac = rlp
        elif self.process.params.powfacdef== 'chavez':
            powfac = 2.2714   
        elif self.process.params.powfacdef == 'min':
            powfac = min(multip,rlp)
        elif self.process.params.powfacdef == 'max':
            powfac = max(multip,rlp) 
        elif self.process.params.powfacdef == 'meanall':
            powfac = (multip+rlp+2.2714)/3  
        elif self.process.params.powfacdef == 'meanrlmulti':
            powfac = (multip+rlp)/2 
        else:
            exitstr ='Unknown powfacdef: %s' %(self.process.params.powfacdef)   
            print (exitstr) 
            BALLE 

        self._CalcFacC(powfac)
        '''
        self.paramL =  ['band','minhisto','maxhisto','he','dnhelo','dnhehi','toahelo',
                        'chavezpath','chavezdn','parispath','parisdn','rlfitpath','rlfitdn','multifitpath','multifitdn']

        
        recs = self.session._SelectBandDos(queryD,self.paramL)
        '''
        recD = {}
        for rec in recs:
            #print ('rec',rec)
            b = rec[0]
            recD[b] = dict(zip(self.paramL,rec))
            
        insertD = {'lsatprodid':self.lsatprodid,'suffix':self.suffix,'pvalue':powfac,
                   'pcode':self.process.params.powfacdef,'doscode':self.process.params.darkedgedef,
                   'icrl':self.process.params.icRL,'msfac':self.process.params.msfac,
                   'method':method,'proddate':Today()}
        '''
        lsatprodid varchar(64),  
            suffix varchar(32),
            proddate date,
            pvalue float,
            pcode varchar(16),
            doscode varchar(16),
            method char(2),    
            
            
        FISKSOPPA
        '''
        #self.session._InsertSceneDos(insertD, self.process.overwrite, self.process.delete)
        self.session._InsertDOStoSRFItrans(insertD, self.process.overwrite, self.process.delete)
        for band in self.srcLayerD:
            #Check if the band exists and if iverwrite is set
            if self.dstLayerD[band]._Exists() and not self.process.overwrite:
                printstr = '    SRFI band already exists: %s' %(self.dstLayerD[band].FPN)
                self.session._InsertLayer(self.dstLayerD[band],self.process.overwrite,self.process.delete)

                continue
            #band = b[0]

            for item in recD[band]:
                #print ('n,item',item)
                #print ('b',band)
                #print (recD[band][item])
                self.calD[band][item] = recD[band][item]

            maxi = self.calD[band]['maxhisto']
            maxip1 = maxi + 1

            #Decisde on which dark efdeg to use
            if self.process.params.darkedgedef == 'multi':
                darkedge = self.calD[band]['multifitpath']
            elif self.process.params.darkedgedef == 'rl':
                darkedge = self.calD[band]['rlfitpath']
            elif self.process.params.darkedgedef == 'dos':
                darkedge = self.calD[band]['toahelo']
            elif self.process.params.darkedgedef == 'paris':
                darkedge = self.calD[band]['parispath']
            elif self.process.params.darkedgedef == 'chavez':
                darkedge = self.calD[band]['chavezpath']
            elif self.process.params.darkedgedef == 'min':
                darkedge = min(self.calD[band]['mulitfitpath'],self.calD[band]['rlfitpath'],self.calD[band]['parispath'],self.calD[band]['chavezpath'])
            elif self.process.params.darkedgedef == 'max':
                darkedge = min(self.calD[band]['mulitfitpath'],self.calD[band]['rlfitpath'],self.calD[band]['parispath'],self.calD[band]['chavezpath'])
            elif self.process.params.darkedgedef == 'meanall':
                darkedge = sum(self.calD[band]['mulitfitpath'],self.calD[band]['rlfitpath'],self.calD[band]['parispath'],self.calD[band]['chavezpath'])/4
            elif self.process.params.darkedgedef == 'meanrlmulti':
                darkedge = sum(self.calD[band]['mulitfitpath'],self.calD[band]['rlfitpath'])/2
            else:
                exitstr ='Unknown powfacdef: %s' %(self.process.params.powfacdef)   
                print (exitstr) 
                BALLE

            self.calD[band]['tgv'] = arr.array('h',(0 for i in range(maxip1)))
            self.calD[band]['toav'] = arr.array('h',(0 for i in range(maxip1)))
            #array numeric vCB[maxip1]; array numeric vBL[maxip1];
            for i in range(maxip1):
                srftoa = self._MapTOAdn(band,i)
                self.calD[band]['toav'][i] = int(srftoa*self.process.params.factor)
                srfapc = srftoa - darkedge;
                srfsfc = srfapc * self.calD[band]['cfac'];
                srfi = round(srfsfc * self.process.params.factor);
                if (srfi < 1): 
                    srfi = 1
                self.calD[band]['tgv'][i] = srfi

            #Set the null
            self.calD[band]['tgv'][0] = -32768
            #for x,row in enumerate(self.calD[band]['tgv']):
            #    print (x,row,self.calD[band]['toav'][x])
            printstr = 'Transforming DN to SRIF for %(b)s: dos: %(d)1.3f, powfac: %(p)1.3f' %{'b':band,'d':darkedge,'p':powfac}
            print (printstr)
            self._CreateSRFIRaster(band)

        
    def _AnalyseDOS(self):
        #Update toahelo
        for band in self.srcLayerD:
            self._MapTOAReflectance(band, 'dnhelo')
        #Calcualte the SRFpath
        p = self._GetSRFPath()
        self._FitSRFPathToModel(p,'rlfitpath')
        return(p)
        
    def _HistoDOS(self):
        for band in self.srcLayerD:
            #Calculate dark and bright edges
            self._DarkEdge(band)
            self._BrightEdge(band)
            self._MapTOAReflectance(band, 'dnhelo')
            
    def _CalcFacC(self,p):
        for band in self.calD:
            
            c = 1+self.icRLm1 * math.pow(self.wlD['rl']['wl']/self.wlD[band]['wl'], p)
            if band == 'me': c *= 1.1
            if band == 'mf': c *= 1.5
            if band == 'mg': c *= 2.4
            c *= self.msfac
            self.calD[band]['cfac'] = c
 
    def _SunFactor(self):
        self.sunfactor = math.sin(math.radians(self.imgAttr['sunelev']))
           
    def _CreateSRFIRaster(self,band):
        '''
        '''
        self.srcLayerD[band].ReadRasterLayer()
        null =  int(self.srcLayerD[band].comp.cellnull)
        self.calD[band]['tgv'][null] = int(self.process.params.cellnull)
        
        srcBAND = self.srcLayerD[band].layer.NPBAND
        
        lookupArr = np.asarray(self.calD[band]['tgv'])
        dstBAND = lookupArr[srcBAND]
        
        #Create the dst layer
        self.dstLayerD[band].layer = lambda:None
        #Set the np array as the band
        self.dstLayerD[band].layer.NPBAND = dstBAND
                
        #copy the geoformat from the src layer
        self.dstLayerD[band].CopyGeoformatFromSrcLayer(self.srcLayerD[band].layer)
        #write the results
        self.dstLayerD[band].CreateDSWriteRasterArray()

        self.session._InsertLayer(self.dstLayerD[band],self.process.overwrite,self.process.delete)
        bandD = {'lsatprodid':self.lsatprodid,
                'folder':self.dstLayerD[band].comp.folder,
                'band':self.dstLayerD[band].comp.band,
                'prefix':self.dstLayerD[band].comp.prefix,
                'suffix':self.dstLayerD[band].comp.suffix} 

        self.session._InsertBand(bandD)
     
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

            if delta1 > self.hedgeD[band]:

                #self.calD[band]['histo'] = self.cumHistoD[band][jp1+self.calD[band]['offset']]
                self.calD[band]['histo'] = self.cumHistoD[band][jp1]
                dnhe = jp1
                break
        self.calD[band]['histohelo'] = self.cumHistoD[band][jp1]
        #Convert back to actual value by adding the offset
        dnhe += self.calD[band]['offset']
        print ('band',dnhe,self.calD[band]['offset'])
        self.calD[band]['dnhelo'] = dnhe
          
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
        
    def _MapTOAdn(self, band, dn):
        toa = self.calD[band]['reflgain']*dn+self.calD[band]['reflbias'] 
        toa /= self.sunfactor
        return toa

    def _MapDN(self,band,toa):
        toa = toa*self.sunfactor
        dn = (toa-self.calD[band]['reflbias'])/self.calD[band]['reflgain'] 
        return int(round(dn))
        
    def _Tuning(self):
        tuned = self._TunePilotRL()
        #Regardless of the the result the histograms are plotted
        method = 'rl'
        self._plothisto('rl')
        if not tuned:
            method = 'na'
            tuned = self._TunePilotNA('na')
            #Regardless of the the result the histograms are plotted
            self._plothisto('na')
            if not tuned:
                self.lsatscene._UpdateSceneStatus(self.session,{'column':'atmcal', 'status': 'F'})
                return False
        p = self._AnalyseDOS()

        self._SaveAcceptedTuning(p,method)
        return True


    def _SaveAcceptedTuning(self,p,method):
        pa = self._AdjustPathMbands(p)
        pa2 = pa*0.8
        for b in self.calD:
            print (self.calD[b])
        self._plotDOS(method,p,pa)
        p2 = self._SetSRFpaths(p,method)
        
        insertD = {'lsatprodid':self.lsatprodid,'rlp':p,'rlp2':p2,'multip':pa,'multip2':pa2,'method':method}
        self.session._InsertSceneDos(insertD, self.process.overwrite, self.process.delete)
        #Update the scene
        self.lsatscene._UpdateSceneStatus(self.session,{'column':'atmcal', 'status': 'Y'})
        #self.session._UpdateSceneStatus({'column':'atmcal', 'status': 'Y'})
        
    def _AdjustPathMbands(self,p):
        #Set p to average of 'rl' and one longer band (or chavez original)
            pL = []
            for b in self.pD:
                if b in ['ma','mb','mc']:
                    pL.append(self.pD[b])
            if len(pL) == 0:
                mp = 2.2714
            else:
                mp = sum(pL)/(len(pL))
            
            pa = (2*p + mp)/3

            pa2 = self._FitSRFPathToModel(pa,'multifitpath') 
            return (pa)  
                 
    def _TunePilotRL(self):
        tuned = self._TuneEdge()
        if tuned:
            p = self._AnalyseDOS()
            if self.process.params.powfacmin < p < self.process.params.powfacmax:
                p2 = self._PowVsDOS(p)
                return p,
            else:
                #try by increasing the dnhelo parameter in an outer loop
                bestp = p
                minhe = self.hedgeD['rl']               
                outerloop = 0
                while True:
                    if self.calD['rl']['he'] > self.process.params.maxdelta:
                        break
                    print ('outerloop',outerloop)  
                    outerloop += 1
                    for band in self.srcLayerD:
                        self.hedgeD[band] += 0.0005
                        self.calD[band]['he'] = self.hedgeD[band]
                    tuned = self._TuneEdge()
                    if not tuned:        
                        return 0
                    p = self._AnalyseDOS()
                    if self.process.params.powfacmin < p < self.process.params.powfacmax:
                        p2 = self._PowVsDOS(p)
                        return p
                    if p > self.process.params.powfacmax and p < bestp:
                        bestp = p
                        minhe = self.hedgeD['rl']
                    elif p < self.process.params.powfacmax and p > bestp:
                        bestp = p
                        minhe = self.hedgeD['rl']
                        
                print ('Trying with optimized p',p,bestp,minhe)
                #Check to see if adjustment causes p to be within limits
                for band in self.srcLayerD:
                    self.hedgeD[band] = minhe
                    self.calD[band]['he'] = self.hedgeD[band]
                tuned = self._TuneEdge()
                if not tuned:        
                    return 0
                p = self._AnalyseDOS()

                pa = self._AdjustPathMbands(p)

                if self.process.params.powfacmin < pa < self.process.params.powfacmax:
                    p2 = self._PowVsDOS(p)
                    return p
                
                return 0
        return 0
            
        
    def _TunePilotNA(self,NIR):
        '''
        '''

        checkBandL = ['bl','gl','rl']
        print ("Trying to find dark edge with NIR absolute DN value")
        self.calD[NIR]['histohelo'] = 0
        while True:
            self.calD[NIR]['histohelo'] += 0.05
            if self.calD[NIR]['histohelo'] > 3.0:
                break
            p = self._SetDarkEdgeFromNA(checkBandL)
            if self.process.params.powfacmin < p < self.process.params.powfacmax:
                print ('    Found p using NIR dark edge',p)
                p = self._AnalyseDOS()

                p2 = self._PowVsDOS(p)

                return p
        return 0
    
        
    
    def _TuneEdge(self, checkBandL = False):

        self.maxdelta = self.process.params.maxdelta
        self.max2delta = 0

        if not checkBandL:
            checkBandL = ['bl','gl','rl']
        loop = 0
        okflag = True
        histoheloRL = 0
        while True:
            
            self._HistoDOS()
            print ('innerloop:',loop)
            #
            loop += 1
            okflag,blerror,glerror = self._HeLoConsistency(checkBandL)
            
            for band in self.srcLayerD:
                self.hedgeD[band] += 0.001
                self.calD[band]['he'] = self.hedgeD[band]
            if self.hedgeD['rl'] > self.maxdelta:
                break
            
            if okflag:
                break
        '''    
        if not okflag:
            else:
                #Test alternative dark edge identification
                self._SetDarkEdgeFromNA(checkBandL)
                #Allow a maximum edge of 3 percent for NIR
                if self.calD[NIR]['histohelo'] > 3.0:
                    break
                if blerror or glerror:
                    if blerror:
                        self.hedgeD['bl'] += 0.001
                        self.calD['bl']['he'] = self.hedgeD['bl']
                        if self.hedgeD['bl'] >= (self.process.params.maxdelta-self.process.params.mindelta) and not self.max2delta:
                            self.maxdelta = self.process.params.max2delta
                    if glerror:
                        self.hedgeD['gl'] += 0.001
                        self.calD['gl']['he'] = self.hedgeD['gl']

                        if self.hedgeD['gl'] >= (self.process.params.maxdelta-self.process.params.mindelta) and not self.max2delta:
                            self.maxdelta = self.process.params.max2delta
                        
            if self.calD['rl']['histohelo']-histoheloRL > 2.0: #If higer up than 2 % on the histogram, force break
                print ('No histogram edge found below %(h)1.2f' %{'h':self.calD['rl']['histohelo']})
                okflag = False
                break
            
            if self.calD['rl']['histohelo'] > 3.0: #If higher up than 2 % on the histogram, force break
                print ('No histogram edge found below %(h)1.2f' %{'h':self.calD['rl']['histohelo']})
                okflag = False
                break
            '''        
        if not okflag:
            print('WARNING, this scene cannot be solved at the moment',self.lsatprodid)
            return False
        return True
    
    def _HeLoConsistency(self,checkBandL):
        okflag = True
        blerror = False
        glerror = False
        
        for b in checkBandL:
            if b in self.srcLayerD and self.calD[b]['toahelo'] < 0:
                okflag = False
                if self.hedgeD[b] >= (self.process.params.maxdelta-self.process.params.mindelta) and not self.max2delta:
                    self.maxdelta = self.process.params.max2delta

        if 'bl' in self.srcLayerD and self.calD['bl']['toahelo'] < self.calD['gl']['toahelo']:
            okflag = False
            blerror = True
        if self.calD['gl']['toahelo'] < self.calD['rl']['toahelo']:
            okflag = False
            glerror = True
        return (okflag,blerror,glerror)
                
    def _SetDarkEdgeFromNA(self,checkBandL):

        hv = self.calD['na']['histohelo']
        for band in self.srcLayerD:
            dnhe = 0
            nbins = len(self.cumHistoD[band])
             
            for j in range (nbins-2):
                jp1 = j+1
               
                if self.cumHistoD[band][j] <= hv and self.cumHistoD[band][jp1] >= hv:
                    #print (self.cumHistoD[band][j],hv,self.cumHistoD[band][jp1])
                    self.calD[band]['histo'] = self.cumHistoD[band][jp1+self.calD[band]['offset']]
                    dnhe = jp1
                    break

            #Convert back to actual value by adding the offset
            dnhe += self.calD[band]['offset']
    
            self.calD[band]['dnhelo'] = dnhe
            #print (band, dnhe)
            self._MapTOAReflectance(band, 'dnhelo')
        okflag = self._HeLoConsistency(checkBandL)[0]
        if okflag:
            p = self._AnalyseDOS()
            return p
        return 0
        
            
        

    def _GetSRFPath(self):
        '''
        '''
        self.pD = {}
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

    def _FitSRFPathToModel(self,p,label):
        p2 = p*0.8
        for b in self.srcLayerD:
            #Set SRFpath using the assigned p value
            if self.wlD[b]['wl'] <= self.wlD['gl']['wl']:
                fitpath = self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / self.wlD[b]['wl']),p)
            else:
                fitpath = self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / self.wlD[b]['wl']),p2)
            self.calD[b][label] = fitpath
            #Set corresponding dn
            dnlabel = label.replace('path','dn')
            dn = self._MapDN(b, fitpath)
            
            self.calD[b][dnlabel] = dn
            
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
            dn2 = self._MapDN(b,srfpath2)     

            self.calD[b]['chavezpath'] = srfpath2
            self.calD[b]['chavezdn'] = dn2
            self.calD[b]['parispath'] = srfpath
            self.calD[b]['parisdn'] = dnpath  
        return p2

    def _SetSRFpaths(self,p,method):
        '''
        '''
        p2 = self._PowVsDOS(p)
        #iterate over all bands
        queryL = ['minhisto','maxhisto','he','dnhelo','dnhehi','dospath','dosdn',
                  'chavezpath','chavezdn','parispath','parisdn','rlfitpath','rlfitdn','multifitpath','multifitdn']

        for b in self.srcLayerD:
            self.calD[b]['dospath'] = self.calD[b]['toahelo']
            self.calD[b]['dosdn'] = self.calD[b]['dnhelo']
            insertD = {'lsatprodid':self.lsatprodid,'band':b,'method':method}

            #queryL = ['minhisto','maxhisto','he','dnhelo','dnhehi','toahelo','chavez','srfpath','dnpath','fitpath','dnfit'] 
            
            #queryL = ['minhisto','he','dnhelo','toahelo','dospath','dosdn',
            #          'chavezpath','chavezdn','parispath','parisdn','rlfitpath','rlfitdn','multifitpath','multifitdn'] 
            
            for key in self.calD[b]:
                if key in queryL:
                    insertD[key] = self.calD[b][key]

   
            self.session._InsertBandDos(insertD, self.process.overwrite, self.process.delete)
        return p2

                        
    def _plotDOS(self, method, p=0, pa=0):
        
        A = np.linspace(0.450, 2.300, num=50)
        if p:
            p2 = p*0.8
            B = self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / A),p)
            C = self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / A),p2)
            MASK = (A > self.wlD['rl']['wl'])
            CHAVEZ = np.copy(B)
            CHAVEZ[MASK] = C[MASK]
            
        if pa:
            pa2 = pa*0.8
            B = self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / A),pa)
            C = self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / A),pa2)
            MASK = (A > self.wlD['rl']['wl'])
            CHAVEZ1 = np.copy(B)
            CHAVEZ1[MASK] = C[MASK]
        
        D = self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / A),2.2714)
        E = self.calD['rl']['toahelo'] * pow((self.wlD['rl']['wl'] / A),(2.2714*0.8))
        
        MASK = (A > self.wlD['rl']['wl'])
        CHAVEZ0 = np.copy(D)
        CHAVEZ0[MASK] = E[MASK]
        
        x = []
        y = []
        y0 = []
        y1 = []
        y2 = []
        for b in self.srcLayerD:
            x.append(self.wlD[b]['wl'])

            y0.append(self.calD[b]['toahelo'])
            if p:
                y.append(self.calD[b]['parispath'])
                y1.append(self.calD[b]['rlfitpath'])
            if pa:
                y2.append(self.calD[b]['multifitpath'])
            
        x = np.array(x)
        y = np.array(y)

        plt.plot(x,y,'mo', markersize=8,label='power law')
        #DOS to be plotted on top must come later 
        plt.plot(x,y0,'ko',markersize=6,label='DOS')
        if p:
            plt.plot(x,y1,'bo',markersize=4,label='fitted')
        if pa:
            plt.plot(x,y2,'yo',markersize=4,label='multifitted')
        plt.plot(A, CHAVEZ0, '-r', label='Chavez')
        if p:
            plt.plot(A, CHAVEZ, '-b', label='fitted')
        if pa:
            plt.plot(A, CHAVEZ1, '-y', label='multifitted')
        plt.legend(loc='upper right')
        if p:
            at = 'p(rl) = %(p)1.2f' %{'p':p}
            plt.annotate(at, xy=(1.0,0.04) )
        if pa:
            at = 'p(multi) = %(p)1.2f' %{'p':pa}
            plt.annotate(at, xy=(1.0,0.05) )
        plt.title(self.lsatprodid)
        if not os.path.exists(self.dstLayerD['dospath'].FP):
            os.makedirs(self.dstLayerD['dospath'].FP)
        #replace the suffix woth the methods used for getting the dark edge
        replaceStr = '%(m)s.png' %{'m':method}
        FPN = self.dstLayerD['dospath'].FPN.replace('0.png',replaceStr)
 
        
        plt.savefig(FPN)
        
        
        if self.process.params.showplot:
            plt.show()
        #clear the plot
        plt.clf()

        
    def _plothisto(self,method,showplot = False):
        #xmax = 0
        #yD = {}
        #xD = {}
        cD = {'bc': 'm','rl':'r','gl':'g','bl':'b','na':'y','mb':'c','mc':'m'}
        for band in self.srcLayerD:
            #xD[band] =  np.arange(len(self.cumHistoD[band]))
            #yD[band] = self.cumHistoD[band]
            dotlayout = '%so' %(cD[band])
            linelayout = '%s-' %(cD[band])
            #print (band,self.calD[band]['dnhelo'],self.calD[band]['histo'])
            plt.plot(self.calD[band]['dnhelo'],self.calD[band]['histo'],dotlayout,label=band)
            xA = np.arange(len(self.cumHistoD[band]))
            xA += self.calD[band]['minhisto']
            plt.plot(xA,self.cumHistoD[band],linelayout)
            
        plt.legend(loc='lower right')
        plt.title(self.lsatprodid)
        if not os.path.exists(self.dstLayerD['histogram'].FP):
            os.makedirs(self.dstLayerD['histogram'].FP)

        
        #replace the suffix woth the methods used for getting the dark edge
        replaceStr = '%(m)s.png' %{'m':method}
        FPN = self.dstLayerD['histogram'].FPN.replace('0.png',replaceStr)
        
        plt.savefig(FPN)

        if self.process.params.showplot or showplot:
            plt.show()
        #clear the plot
        plt.clf()


if __name__ == "__main__":
    old_array = np.asarray([0,1,0,1])
    lookups = [(0, -32768), (1,2)]
    idx, val = np.asarray(lookups).T
    lookup_array = np.zeros(idx.max() + 1)
    lookup_array[idx] = val
    
    print ('lookup',lookup_array)
    #When you get that, you can get your transformed array simply as:
    
    new_array = lookup_array[old_array]
    print ('new_array',new_array)


        