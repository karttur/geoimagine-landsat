'''
Created on 14 feb 2012

@author: thomasg

'''
#imports


"""@package docstring
Doxygen documentation for this module

More details.
"""
_description = 'Script written by Thomas Gumbricht for reading XML files'
_programV="mj_XML_v30.py"
_copyright =""
_producer ="Thomas Gumbricht"
_contact ="thomas dot  gumbricht  at gmail.com"
_organization = "MapJourney"
_address = ""
_url ="www.mapjourney.com"
        
class LandsatProd:  
    """Defines landsat product related stuff"""  
    #TGTODO move to landsat
    def __init__(self, prodD): 
        """The constructor expects a dictionary."""
        for key, value in prodD.items():
            setattr(self, key, value)
        self.product = '%(sensat)s-%(l1type)s-%(coll)s%(tier)s' %{'sensat':self.sensat,'l1type':self.l1type,'coll':self.collection,'tier':self.tier}
        self.source = self.sensat
        
class LandsatScene(LandsatLayer): 
    """layer class for landsat scenes.""" 
    def __init__(self,comp,location,datum): 
        """The constructor expects an instance of the composition class and the wrs (1 or 2)."""
        LandsatLayer.__init__(self, comp,location,datum) 
          
    def SetStatus(self,status):
        """Status sets the status indicators to set for scene db search"""
        self.status = status
               
    def OrganiseScene(self,processC,tarFPN,updateD):
        """Moves downloaded landsat files to the defined path.
        Only used for organizing the downloaded zip files.
        """
        #check if there is an existing file
        existScenes = ConnLandsat.SelectSingleSceneOnId(self.sceneid)
        #sceneFiles = scenefilename, sceneID, product typeid, proddate, L1type,colelction,tier,dataunit, organized, extracted, redundant, deleted
        for scene in existScenes:
            if scene[0] == self.FN:
                if os.path.exists(tarFPN):
                    #check the sizes of the files
                    oldsize = os.path.getsize(tarFPN)
                    newsize = os.path.getsize(self.FPN)                    
                    if newsize > oldsize:
                        print 'Replacing the existing organized file with identically named file'
                        os.remove(tarFPN)
                        shutil.move(self.FPN, tarFPN)
                        return 
                    else:
                        os.remove(self.FPN)
                        return            
            else:
                #There is a scene registered, but not the same filename, check why
                #if this is urlscene, check if the expscene is there
                if os.path.exists(os.path.splitext(tarFPN)[0]):
                    print 'Replacing tar file with zipped tar file of same content'
                    os.remove(os.path.splitext(tarFPN)[0])
                    self.DbUpdateSceneFileName()
                    shutil.move(self.FPN, tarFPN)
                    return
                    #replace registered bands
                elif os.path.splitext(self.FN)[1] == '.tar':
                    gzFN = '%s.gz' %(tarFPN)
                    if os.path.exists(gzFN):
                        #The tar file can be deleted
                        os.remove(self.FPN)
                        return
                    else:
                        FOld = LandsatFile(self.comp,scene[0],self.wrs)
                        #FOld.SetSceneType(self.sceneid,self.typeid,self.L1type,self.collection,self.tier,self.proddate,self.filecat,self.scene,self.filetype,self.dataunit) 
                        chk = CheckOrder(self,FOld)
                        if chk in [1,2,3] and self.dataunit == FOld.dataunit:
                            print 'The old dataset is redundant'
                            sys.exit('The old dataset is redundant')
                        elif chk in [1,2,3] and FOld.dataunit.lower() == 'reflectance':
                            print 'The old dataset is in SRFI units, the old is not, keeping both'
                        elif chk == 0 and self.dataunit == FOld.dataunit:
                            print 'the new dataset is the same as the old'
                            os.remove(self.FPN)
                            return
                        elif chk == 4 and self.dataunit == FOld.dataunit:
                            print 'Same dataset, but later processing date'
                            if not processC.replaceold:
                                os.remove(self.FPN)
                                return
                            else:
                                sys.exit('FIXA')
                        else:
                            'Seems to be the same dataset'                       
        #if the script reaches here, the file is either not registerd or not in place, check that this new file is of a higher order, and then set the old ones to redundant     
        #insert scene in DB
        self.downloaded = 'Y'
        ConnLandsat.InsertScene(self)
        for key in updateD:
            ConnLandsat.UpdateSceneStatusOnFN(self.FN,key,updateD[key])
        if not os.path.exists(os.path.split(tarFPN)[0]):
            os.makedirs(os.path.split(tarFPN)[0])  
        shutil.move(self.FPN, tarFPN)                     
        
        ConnLandsat.UpdateSceneStatusOnFN(self.FN,'organized','Y')
           
    def DbUpdateSceneFileName(self):
        """For the special case where a non-zip file is replaced by a zip file.
        """
        ConnLandsat.UpdateSceneFileNameToZip(self)
       
class LandsatFile(LandsatScene): 
    """class for all downloaded landsat files"""  
    def __init__(self, *args, **kwargs): 
        if args is not None and len(args) > 0:
            comp, location, datum = args
            LandsatScene.__init__(self, comp, location, datum) 
        if kwargs is not None:
            for key, value in kwargs.items():
                setattr(self, key, value)

    def SetFileName(self,FN):
        self.FN = FN
        self.base,self.ext = os.path.splitext(self.FN)
        #Check if this is a zip file of some kind
        if self.ext.lower() in ('.gz','.tar','.zip','.gzip'):
            if '.tar.gz' in self.FN.lower():
                self.ziptype = 'tar.gz'
            elif self.ext.lower() in ['.gz','.gzip','.gunzip']:
                self.ziptype = 'gzip'
            elif self.ext.lower() == '.tar':
                self.ziptype = 'tar'
            else:
                self.ziptype = 'zip'       
        else: 
            self.ziptype = 'none'
    
    def SetFPN(self):            
        self.FP = os.path.join(self.comp.mainpath, self.comp.source, self.comp.division, self.comp.folder, self.location.pathstr, self.location.rowstr, self.acqdate.acqdatestr)
        self.FPN = os.path.join(self.FP,self.FN)

    def ExplodeFile(self,explodeL,filetype):
        """Explode layers and files from downloaded and organized landsat files.
        """
        #Checks and/or extracts the extractL of compressed archives, i.e. scenes and files downloaded from internet          
        if self.ziptype == 'zip':
            self.UnZip(explodeL)
        elif self.ziptype in ['gzip']:
            self.GunZip(explodeL)
        elif self.ziptype in ['tar.gz']:
            if filetype[0:7] in ['_LE7HDF','_LE5HDF' ]:
                self.UnTarGzHDF(explodeL)
            else:
                self.UnTarGz(explodeL)
        elif self.ziptype in ['tar']:
            self.UnTar(explodeL)
            
    def UnTarGz(self,explodeL):
        """Explodes layers from tar.gz files.
        """
        import tarfile
        #tarextractL = tarfile.open( self.orgFPN)
        print 'opening %(tar)s...' %{'tar':self.FN}
        with tarfile.open(self.FPN, 'r:*') as tarextractL:
            for member in tarextractL.getmembers():
                filename = os.path.basename(member.name)
                if not filename:
                    continue  
                extract = self.CreateLayerOut(filename,explodeL)
                if extract:
                    source = tarextractL.extractfile(member)
                    target = file(extract, "wb")
                    shutil.copyfileobj(source, target)
          
    def UnTarGzHDF(self,explodeL):
        """Explode layers from tar.gz files containing hdf layers.
        """
        import tarfile
        import time   
        for e in explodeL:
            print '    explodeL', e.FN,e.pattern
            if e.Exists():
                continue
            if 'lndcal' in e.pattern:     
                tempFPN = os.path.join(self.FP,'lndcal.hdf')
            elif 'lndsr' in e.pattern:
                tempFPN = os.path.join(self.FP,'lndsr.hdf')
            else:
                continue
            #copy the file to memory and extract the hdf straight from memory? 
            cmd = '/Library/Frameworks/GDAL.framework/Versions/1.11/Programs/gdal_translate '
            cmd = '%(cmd)s HDF4_EOS:EOS_GRID:"%(hdf)s"%(band)s %(tar)s' %{'cmd':cmd,'hdf':tempFPN,'band':e.hdfGrid, 'tar':e.FPN}
            print cmd
            os.system(cmd)
        print 'opening HDF %(tar)s...' %{'tar':self.FN}
        with tarfile.open(self.FPN, 'r:*') as tarexplodeL:
            for member in tarexplodeL.getmembers(): 
                filename = os.path.basename(member.name)
                if not member.isfile():
                    continue 
                print 'filename in zip', filename
                if os.path.splitext(filename)[1].lower() == '.hdf':
                    explodeLayerL = self.ListHDFLayersOut(filename,explodeL) 
                    if len(explodeLayerL) > 0:       
                        #create a temporary extraction of the hdf file and extract from the temporary file
                        #There are some issues with HDF implementation in GDAL/OGR for python
                        if 'lndcal' in filename:     
                            tempFPN = os.path.join(self.FP,'lndcal.hdf')
                        elif 'lndsr' in filename:
                            tempFPN = os.path.join(self.FP,'lndsr.hdf')
                        else:
                            print 'unknown hdf file', filename
                        if not os.path.isfile(tempFPN):
                            source = tarexplodeL.extractfile(member)
                            target = file(tempFPN, "wb")
                            shutil.copyfileobj(source, target) 
                            prevfilesize = 0 
                            while True:
                                time.sleep(1.0) # seconds
                                filesize = os.path.getsize(tempFPN)
                                print 'filesize',filesize
                                if prevfilesize == filesize:
                                    break
                                prevfilesize = filesize
                        for e in explodeLayerL:
                            if e.Exists():
                                continue
                            #copy the file to memory and extract the hdf straight from memory? 
                            cmd = '/Library/Frameworks/GDAL.framework/Versions/1.11/Programs/gdal_translate '
                            cmd = '%(cmd)s HDF4_EOS:EOS_GRID:"%(hdf)s"%(band)s %(tar)s' %{'cmd':cmd,'hdf':tempFPN,'band':e.hdfGrid, 'tar':e.FPN}
                            print cmd
                            os.system(cmd)
                            BALLE
                else: #non hdf extraction
                    extract = self.CreateLayerOut(filename,explodeL)
                    if extract:
                        source = tarexplodeL.extractfile(member)
                        target = file(extract, "wb")
                        shutil.copyfileobj(source, target)
                    
    def CreateLayerOut(self,aFN,explodeL):
        """Creates the target layer within the extractfile method - no public access
        """
        #Check which file this is
        layerok = False
        for explodeLayer in explodeL:
            if explodeLayer.pattern in aFN:
                layerok = True
                break     
        if layerok:
            if explodeLayer.Exists():
                return False
            else:
                print 'exploding',explodeLayer.FN
                #TGTODO, the band is registered as extracted before actually being done, but the scene is still registered as unextracted
                ConnLandsat.InsertSceneBands(explodeLayer,aFN,'exploded')
                return explodeLayer.FPN        
        else:
            pass
            #print 'WARNING %s not extracted' %(aFN)
         
    def ListHDFLayersOut(self,aFN,extractL):
        """Internal list process for the extraction of hdf files.
        """
        import fnmatch
        extractLayerL = []
        for extractLayer in extractL:
            if fnmatch.fnmatch(aFN,extractLayer.pattern):
                extractLayerL.append(extractLayer)
        if len(extractLayerL) == 0:
            pass
        return extractLayerL

class ProcessLandsat():
    'class for all Landsat specific processes'   
    def __init__(self, processC,processElement,locationD, wrs = 2):
        self.process = processC
        self.SetLandsatSource(aD['sensat'])
        self.wrs = wrs
        #direct to subprocess
        if self.process.processid == 'managebulkmetaurl':
            if tD['xmlurl'] == tD['csvgzurl'] == '':
                sys.exit('No url given for managebulkmetaurl')          
            ConnLandsat.ManageBulkMetaUrl(self)
        elif self.process.processid == 'landsatmetadb':
            self.LandsatMetaDB(processElement)    
        elif self.process.processid == 'downloadbulkmeta':
            self.DownLoadBulkMeta()  
            #elif self.process.processid == 'checkbulkparams':
            #self.CheckBulkParams(aD)   
        elif self.process.processid == 'insertbulkmeta':
            self.InsertBulkMeta()
            #self.OrganizeLandsat(processElement,aD)
        elif self.process.processid == 'organizelandsat':
            self.OrganizeLandsat(processElement)
        elif self.process.processid == 'explodelandsatscene':
            self.ExplodeLandsat(aD,locationD)
        elif self.process.processid == 'landsatscenetemplate':
            ConnLandsat.InsertTemplateScene(self.process)
        elif self.process.processid == 'landsatbandtemplate':
            self.LandsatBandTemplate(aD,tD,'B')
        elif self.process.processid == 'landsatsupporttemplate':
            self.LandsatBandTemplate(aD,tD,'S')
        elif self.process.processid == 'landsatmetatemplate':
            tD['celltype'] = 'NA'
            self.LandsatBandTemplate('M')
        elif self.process.processid == 'metafileparams':
            self.MetaFileParams(processElement)
        elif self.process.processid == 'checklandsat':
            self.CheckLandsat(processElement)
        else:
            exitstr = 'Unrecognised process under ProcessLandsat: %s' %(self.process.processid)
            sys.exit(exitstr)
    
    def LandsatBandTemplate(self, bandtype):
        pp = self.process.params
        comp = Composition(pp.sensat,pp.product,pp.folder,pp.band,pp.prefix,pp.typeid, 
                           dataunit = pp.dataunit, system='landsat',celltype=pp.celltype, measure= pp.measure, scalefac =pp.scalefac, offsetadd=pp.offsetadd) 
        ConnLandsat.ManageTemplateLayer(self.process,bandtype,comp)
        ConnComp.InsertTemplateLayer(self.process,'landsat',comp)
                
    def LandsatMetaDB(self, processElement):
            #Get the column tags
            colTags = processElement.getElementsByTagName('column')
            #Get the attributes to retrieve
            tagAttrL = ConnProcess.SelectProcessTagAttr(self.process.processid,'process','column') 
            colDL = []
            #Get all the data as a list of dicts
            for colTag in colTags:
                colDL.append(XMLelement(colTag,tagAttrL,'column',self.process.processid)[0])
            #manage the db
            ConnLandsat.ManageMetaDb(self,pp.sensor,colDL)
 
    def DownLoadBulkMeta(self):
        import urllib        
        bulkFileL = []
        for source in self.sourceL:
            recs = ConnLandsat.SelectBulkMetaUrl(aD,source)
            for rec in recs:
                if aD['filetype'] == 'csv':
                    if rec[1] == 'None' or rec[1] in bulkFileL:
                        continue
                    bulkFileL.append(rec[1])
                else:
                    if rec[0] == 'None' or rec[0] in bulkFileL:
                        continue
                    bulkFileL.append(rec[0])
        for metFileUrl in bulkFileL:
            tarFN = os.path.split(metFileUrl)[1]
            tarFN = os.path.splitext(tarFN)[0]
            tarFPN = os.path.join(self.process.tarpath.mainpath,tarFN)
            if os.path.isfile(tarFPN):
                #Get the date of the existing file
                t = os.path.getmtime(tarFPN) 
                filedate = mj_dt.DateFromTmTime(t) 
                today = mj_dt.Today()
                STOP #the old file must be renamed and then check via db
                daysOld = mj_dt.DateDiff(today,filedate)
                if daysOld == 0: #never update form the same day
                    printstr = '%s already downloaded earlier today' %(tarFN)
                    print printstr
                    continue
                if daysOld < pp.daysago:
                    printstr = 'Recent version of %s already exists' %(tarFN)
                    print printstr
                    continue
                #move and rename the existing file
                retiredFN = '%s_%s' %(mj_dt.DateToStrDate(filedate),tarFN)
                retiredFP = os.path.join(self.tarpath.mainpath,'retired')
                if not os.path.exists(retiredFP):
                    os.makedirs(retiredFP)
                retiredFPN = os.path.join(retiredFP,retiredFN)
                shutil.move(tarFPN,retiredFPN)
                printstr = 'downloading bulk meta file %s, will take a while...' %(tarFN)  
                print printstr      
                urllib.urlretrieve(metFileUrl, tarFPN)
            else: #file does not exist
                printstr = 'downloading bulk meta file %s, will take a while...' %(tarFN)  
                print printstr      
                urllib.urlretrieve(metFileUrl, tarFPN)
         
    def SetLandsatSource(self,sensat):
        #self.wrsD ['LM1':'','LM2','LM3','LM4','LM5']]
        if sensat == '*':
            self.sensor = self.satellite = '*'
        else:
            self.sensor, self.satellite = sensat[1:2], sensat[2:3]
        if '*' in sensat:
            self.sourceL = []
            if self.sensor == '*':
                sensorL = ['M','T','E','C','O','S']
            else:
                sensorL = [self.sensor]
            if self.satellite == '*':
                for sensor in sensorL:
                    if sensor == 'M': self.sourceL.extend(['LM1','LM2','LM3','LM4','LM5'])
                    elif sensor == 'T':self.sourceL.extend(['LT4','LT5'])
                    elif sensor == 'E':self.sourceL.append('LE7')
                    elif sensor == 'C':self.sourceL.append('LC8')
                    elif sensor == 'O':self.sourceL.append('LO8')
                    elif sensor == 'S':self.sourceL.append('LS8')
            else:
                for sensor in sensorL:
                    sensat = 'L%s%s' %(sensor,self.satellite)
                    self.sourceL.append([sensat])       
        else:
            self.sourceL = [sensat]
     
    def GetTier(self,browseURL):
        """GetTier disentangles the name of the browse file to identify collection and tier
        """
        try:
            sensat,data_type_l1,pathrow,acqdate,procdate,collection,tier,rest = os.path.split(browseURL)[1].split('_')
            productId = '%(s)s_%(d)s_%(pr)s_%(a)s_%(p)s_%(c)s_%(t)s' %{'s':sensat, 'd':data_type_l1,'pr':pathrow,'a':acqdate,'p':procdate,'c':collection,'t':tier}
        except:
            tier,productId = 'FF','FF'
        return (tier,productId)
     
    def CsvMetaHeader(self,headerL,paramTT):
        checkok = True
        lacking = 0
        self.seqL = []
        self.seqD = {}
        for paramT in paramTT:
            #Create the dfferent csv file names
            if paramT[1] not in self.csvFNL:
                self.attrHeaderD[paramT[1]] = ['sceneid']  
                #self.attrHeaderD[paramT[1]].append('sceneid')
                if paramT[1] == 'main':
                    self.attrHeaderD['main'].append('satelnr')
                    self.attrHeaderD['main'].append('sensorid')
                self.csvFNL.append(paramT[1])  
            self.attrHeaderD[paramT[1]].append(paramT[2])
            #check the parameters
            if paramT[0].lower() != 'false':                        
                if paramT[0] not in headerL:
                    lacking -= 1
                    if paramT[0] in self.altD:
                        if self.altD[paramT[0]] in headerL:
                            seq = headerL.index(self.altD[paramT[0]])
                            self.seqL.append(seq)
                        elif paramT[3].lower() == 'y':
                            printstr = 'FATAL Can not find required parameter %s' %(paramT[0])
                            print printstr
                            checkok = False
                        else:
                            printstr = 'Can not find  parameter %s setting it to default' %(paramT[0])
                            print printstr
                            self.seqL.append(lacking)                                               
                            self.seqD[lacking] = paramT
                    else:
                        if paramT[3].lower() == 'y':
                            printstr = 'FATAL Can not find required parameter %s' %(paramT[0])
                            print printstr
                            checkok = False
                        else:
                            printstr = 'Can not find  parameter %s setting it to default' %(paramT[0])
                            print printstr,paramT
                            self.seqL.append(lacking)                                               
                            self.seqD[lacking] = paramT
                else:     
                    seq = headerL.index(paramT[0])
                    self.seqL.append(seq) 
        return checkok
     
    def InsertBulkMeta(self,aD):
        #import fileinput
        import csv
        self.altD = {'imageQuality1':'IMAGE_QUALITY','imageQuality2':'IMAGE_QUALITY','GEOMETRIC_RMSE_MODEL':'GEOMETRIC_RMSE_MODEL_X'}
        recs = ConnLandsat.SelectAllBulkMetaUrl()
        for rec in recs:
            #rec: xmlurl, csvgzurl, latestdate, collection,xmllocal,csvlocal
            if rec[5]:
                srcFPN = os.path.join(self.process.srcpath.mainpath,rec[5])
                if os.path.isfile(srcFPN):
                    t = os.path.getmtime(srcFPN) 
                    filedate = mj_dt.DateFromTmTime(t)
                    self.csvFNL = []
                    #Dcit to hold attributes to load for each db table
                    self.attrHeaderD = {} 
                    checkok = True
                    print 'checking bulk meta from',srcFPN
                    #Get the collection etc
                    sensColl = ConnLandsat.SelectBulkMetaSensColl(os.path.split(srcFPN)[1])   
                    print 'sensColl',sensColl    
                    if sensColl == None:
                        sys.exit('Error in identifying bulk metatadafile')
                    #Get the parameters to extract for this particular sensor
                    sensor, collection = sensColl
                    paramTT = ConnLandsat.SelectCommonMeta('csv') 
                    with open(srcFPN) as f:
                        reader = csv.reader(f)
                        headerL = next(reader)
                        sceneIdindex = headerL.index('sceneID')
                        checkok = self.CsvMetaHeader(headerL,paramTT)
                        if not checkok:
                            exitstr = 'The required parameters for landsat bulk meta data not found in %s' %(srcFPN)
                            sys.exit(exitstr)
                        else:
                            print '    Landsat meta parameter check OK'
                            print '    loading bulk meta from',srcFPN
                            #add collection, tier regdate and prodIdUSGS to the correct tables
                            self.attrHeaderD['main'].append('collection') 
                            self.attrHeaderD['main'].append('tier')
                            self.attrHeaderD['main'].append('regdate')
                            self.attrHeaderD['sub'].append('prodIdUSGS')
                            #Dict to hold filepaths to csv files
                            csvFD = {}
                            metaFPND = {} 
                            #Set the filenames
                            for key in self.csvFNL:
                                FN = '%s.csv' %(key)
                                FPN = os.path.join(self.process.srcpath.mainpath,FN)
                                print 'FPN',FPN
                                metaFPND[key] = FPN
                            #open the files for writing
                            for key in metaFPND:    
                                F = open(metaFPND[key],'w')
                                csvFD[key] = F             
                                #wr = csv.writer(csvFD[key], quoting=csv.QUOTE_ALL)
                                wr = csv.writer(csvFD[key])
                                wr.writerow(self.attrHeaderD[key])
                            x = 0
                            for line in f:
                                valueL = line.rstrip().split(',')
                                sceneId = valueL[sceneIdindex]
                                satelnr = int(sceneId[2:3])
                                sensorId = sceneId[1:2]
                                paramD = dict([ ('main',[sceneId,satelnr,sensorId]), ('geo',[sceneId]), ('sub',[sceneId]), ('url',[sceneId])])
                                for i,s in enumerate(self.seqL):
                                    #Simplify and sort parameters
                                    if s < 0:
                                        #no data column in bulk file, use template data
                                        paramD[self.seqD[s][1]].append(self.seqD[s][4])     
                                    elif valueL[s]:
                                        if paramTT[i][2].lower() == 'ephemeris':
                                            paramD[paramTT[i][1]].append(valueL[s][0])
                                        elif paramTT[i][2].lower() == 'dayornight':
                                            paramD[paramTT[i][1]].append(valueL[s][0])
                                        elif paramTT[i][2].lower() == 'orientation':
                                            paramD[paramTT[i][1]].append(valueL[s][0])
                                        elif paramTT[i][2].lower() == 'cloudcov':
                                            paramD[paramTT[i][1]].append(int(round(float(valueL[s]))))
                                        else:  
                                            paramD[paramTT[i][1]].append(valueL[s])
                                    else:
                                        #Null data column in bulk file, use default
                                        paramD[paramTT[i][1]].append(paramTT[i][4])       
                                #Set collection to sub from filename
                                paramD['main'].append(collection)
                                if collection in ['01','02']:
                                    tier, productid = self.GetTier(paramD['url'][2])
                                    paramD['main'].append(tier)
                                    paramD['sub'].append(productid)
                                else:
                                    paramD['main'].append('FF')
                                    paramD['sub'].append('FF')
                                paramD['main'].append(filedate)
                                #write to file
                                for key in paramD:
                                    #wr = csv.writer(csvFD[key], quoting=csv.QUOTE_ALL)
                                    wr = csv.writer(csvFD[key])
                                    wr.writerow(paramD[key])        
                                #ConnLandsat.InsertBulkMetaItems(paramD,paramD['sceneId'][1],sensorid,sensorDbD[sensorid])                
                                x += 1
                                if x/100000 == int(x/100000):
                                    print x
                            for key in csvFD:
                                csvFD[key].close() 
 
                            ConnLandsat.ManageBulkMeta(metaFPND, srcFPN, filedate, collection)
        
    def IdentifyScene(self,standardFNs,standardBNs,FN,wrs,path):
        result = self.GetSceneType(standardFNs,standardBNs,FN,wrs)
        if not result:
            BALLE
            return False
        FIn, acqdate, updateD = result
        if not FIn.prodid.typeid:
            warnStr = 'WARNING Can not find scene of donwloaded file: %(s)s' %{'s':FN}
            sys.exit(warnStr)
        elif FIn.prodid.typeid[0:6] in ['LE7HDF','LE5HDF' ]:
            printstr = 'SKIPPING HDF file for now %s' %(FIn.FN)
            print printstr
            return False
        compOut = FIn.comp
        compOut.SetPathParts(path)
        #Create an instance of the output file
        FOut = LandsatFile(compOut, FIn.location, acqdate) 
        FOut.SetFileName(FN)
        FOut.SetFPN()
        return FIn,FOut, updateD
        
    def OrganizeLandsat(self,processElement,procAttrParamD):
        #Set the parameters   
        self.addredundant = procAttrParamD['redundant']
        self.replaceold = procAttrParamD['replaceold']
        self.dataunit = procAttrParamD['dataunit']
        #Get the templates for scenenames and bandnames
        standardFNs = ConnLandsat.GetDBscenetypes()
        standardBNs = ConnLandsat.GetDBbandtypes()
        #Get the files in the input mainpath
        FL = [ f for f in os.listdir(self.process.srcpath.mainpath) if os.path.isfile(os.path.join(self.process.srcpath.mainpath,f)) ]
        #FL = FileList(downloadFP)
        for FN in FL:
            #Skip all hidden system files
            if FN[0] == '.':
                continue             
            #keyIn = self.process.compinD.keys()[0]
            #Get the scene location and composition
            Fin, Fout, updateD =  self.IdentifyScene(standardFNs,standardBNs,FN,procAttrParamD['wrs'],self.process.tarpath)
            #copy the scene location also to the output file
            Fin.OrganiseScene(self,Fout.FPN,updateD)
            
    def GetSceneType(self,standardFNs,standardBNs,FN,wrs):
        """Compares the file name of downloaded files with filenames available in the template db"""
        import landsat_organize_v70 as landsat_organize
        result = landsat_organize.GetScene(FN,standardFNs,False, False, False)
        if not result:
            result = landsat_organize.GetScene(FN,standardFNs,True, False, False)
        if not result:
            result = landsat_organize.GetScene(FN,standardFNs,False,'.gz', False)
        if not result:
            result = landsat_organize.GetScene(FN,standardFNs,False, False, True)
        if result:
            typeid, sensat, L1type, path, row, acqdate, proddate, coll, tier, folder, filecat, dataunit, archive = result
        if not result:
            warnstr = 'WARNING, can not find template for landsat file: %s' %(FN)
            print warnstr
            return False
        else:  
            #typeid,sensat,L1type,path,row,acqdate,proddate,coll,tier,folder,filecat,dataunit,sceneBool,filetype,archive  = fInfo
            acqdatestr =  mj_dt.DateToStrDate(acqdate)
            doyStr = mj_dt.YYYYDOYStr(acqdate)
            acqYYYYDOYStr = '%s%s' %(acqdatestr[0:4],doyStr)
            sceneid = '%(s)s%(p)s%(r)s%(d)s' %{'s':sensat,'p':path,'r':row,'d':acqYYYYDOYStr}
            #Get the scene from the DB
            recs = ConnLandsat.FindSceneID(sceneid,sensat[1:2],sensat[2:3],int(path),int(row),acqdate)
            #sceneID,path,row,acquisitionDate,dateupdated,data_type_l1,collection,tier
            if len(recs) != 1:
                exitstr = 'Can not find scene in %s in CheckScene' %(sceneid)
                print exitstr
                BALLE
                sys.exit(exitstr)
            sceneid, dbpath, dbrow, dbacqdate, dbupdate, dbL1type, dbcoll, dbtier = recs[0]
            updateD = {'lupdate':'N','cupdate':'N','dupdate':'N','tupdate':'N' }
            if L1type == 'L1X':
                L1type = dbL1type 
            elif L1type != dbL1type:
                updateD['lupdate'] = 'Y'
            if not proddate:
                proddate = dbupdate
            if int(path) != dbpath:
                exitstr = 'Incorrect path %s %s' %(int(path), dbpath)
                sys.exit(exitstr)
            if int(row) != dbrow:
                exitstr = 'Incorrect path %s %s' %(int(row), dbrow)
                sys.exit(exitstr)
            if acqdate != dbacqdate:
                exitstr = 'Incorrect acquisition date %s %s' %(acqdate, dbacqdate)
                sys.exit(exitstr)
            #Check if the collection and tier are the latest, or in SRFI units
            if not coll:
                #warnstr = 'No collection defined, db indicates %s' %(rec[6])
                coll = 'FF'
                updateD['cupdate'] = 'Y' 
            elif coll != dbcoll:
                if dbcoll == 'PC' and coll != 'PC':
                    coll = 'PC'
                # warnstr = 'collection type differs %s %s' %(rec[6], self.collection)
                updateD['cupdate'] = 'Y'
            if not tier:
                #warnstr = 'No tier defined, db indicates %s' %(rec[7])
                updateD['tupdate'] = 'Y' 
            elif tier != dbtier:
                #warnstr = 'tier type differs %s %s' %(rec[7], self.tier)
                updateD['tupdate'] = 'Y'
            if proddate:
                if dbupdate > proddate:
                    #warnstr = 'Not latest update date %s %s' %(rec[4], self.proddate)
                    updateD['dupdate'] = 'Y'
            else:
                updateD['dupdate'] = 'U'    
            #Create an instance of SceneTile location
            SceneLocation = Location('landsatsence')
            SceneLocation.LandsatScene(wrs,path,row)
            #locationC = SceneTile('landsat', (wrs,path,row,wrs))
            #Create an instance of LayerDate
            
            #datumC = LayerDate(acqdate,self.process.period.timestep)
            #The composition for download 
            #Define the product
            #product = typeid, sensat, L1type, path, row, acqdate, proddate, coll, tier

            lprod = LandsatProd({'typeid':typeid, 'sensat':sensat, 'l1type':L1type, 'proddate':proddate, 'collection':coll, 'tier':tier, 'archive':archive})
            #comp = {'folder':folder,'source':lprod.source,'product':lprod.product}

            #self.source, self.product, self.folder, self.band, self.prefix, self.suffix
            comp = Composition(source = lprod.source, product = lprod.product, folder = folder, dataunit = dataunit)
            #cformat = {'dataunit':dataunit}
            #compC.CompFormat(cformat)
            acqdate = AcqDate({'acqdatestr':acqdatestr, 'timestep':'singledate'}, acqdate = acqdate)
            FIn = LandsatFile(comp, SceneLocation, acqdate, sceneid = sceneid, prodid=lprod, FN=FN)
            #FIn.SetLandsatProduct(lprod)
            #FIn.SetId(sceneid)
            #print FN
            #FIn.SetFileName(FN)
            FIn.FPN = os.path.join(self.process.srcpath.mainpath,FN)
         
            return FIn, acqdate, updateD
   
    def SceneTileStatus(self,item):
        if item:
            return 'Y'
        else:
            return 'N'
          
    def ExplodeScene(self,locDate):
        sceneid, sceneFN, source, product, folder, path, row, acqdate = locDate
        comp = Composition(source = source, product = product, folder = folder, mainpath = self.process.srcpath.mainpath)
        comp.SetPathParts(self.process.srcpath)
        SceneLocation = Location('Landsatscene')
        SceneLocation.LandsatScene(self.wrs, path, row)
        acqdatestr = mj_dt.DateToStrDate(acqdate)
        acqdate = AcqDate({'acqdatestr':acqdatestr, 'timestep':'singledate'}, acqdate = acqdate)
        FIn = LandsatFile(comp, SceneLocation, acqdate)
        FIn.SetFileName(sceneFN)
        FIn.sceneid = sceneid
        FIn.SetFPN()
        if not os.path.isfile(FIn.FPN):
            exitstr = 'Can not find file %s' %(FIn.FPN)
            sys.exit(exitstr)
        else:             
            #Get the bands to extract from this file via the filename
            layercomps = ConnLandsat.SelectSceneTemplateLayersOnFN(FIn.FN)
            if len(layercomps) == 0:
                exitStr = 'No templates found for file',FIn.FN
                print exitStr
                BALLE
                sys.exit(exitStr)
            requested = done = 0
            explodeL = []
            explodeD ={}
            requiredL = []
            metaD = {}
            #key = self.process.compoutD.keys()[0]
            for layercomp in layercomps:    
                senssat, source, product, folder, band, prefix, typeid, fileext, pattern, celltype, dataunit, filecat, typeid, hdfgrid, required, archive = layercomp
                if folder != 'no':
                    requested += 1                            
                    suffix = '_%s' %(typeid)
                    comp = Composition(source, product, folder, band, prefix, suffix)
                    comp.SetPathParts(self.process.tarpath)
                    #set the extension
                    comp.SetExt(fileext)
                    #outputformat is not necessary to set
                    LOut = LandsatLayer(comp, SceneLocation, acqdate)
                    #Set the search pattern for this layer to use when extracting the zip file
                    LOut.SetPattern(pattern)
                    #Set the file category
                    LOut.SetFileCat(filecat)
                    #LOut.SetId(datum[1])
                    LOut.typeid = typeid
                    LOut.sceneid = sceneid
                    #Set FPN
                    LOut.SetLayerPath()
                    #If filetype is HDF set the hdfgrid
                    if LOut.comp.suffix[0:7] in ['_LE7HDF','_LE5HDF' ]:
                        LOut.SetHdfGrid(hdfgrid)     
                    if required == 'Y' and filecat == 'M':
                        metaD[band] = LOut
                    elif filecat in ['B','S']:
                        explodeD[LOut.comp.band] = LOut
                    if os.path.exists(LOut.FPN):
                        done += 1
                        #register band
                        ConnLandsat.InsertSceneBands(LOut,FIn.FN,'exploded') 
                        if filecat in ['B','S']:
                            ConnLandsat.ManageLayer(LOut,self.process.delete,self.process.overwrite)
                    else:
                        explodeL.append(LOut)                                    
                        if required == 'Y':
                            requiredL.append(LOut)
            if LOut.comp.suffix[0:7] in ['_LE7HDF','_LE5HDF' ]:
                printstr = 'SKIPPING HDF file for now %s' %(FIn.FN)
                print printstr
                return
            print 'requested,done', requested, done
            if len(requiredL) == 0:
                print 'scene %(s)s is OK; %(d)d bands extracted ' %{'s':FIn.FN, 'd':done}                                      
            else:
                FIn.ExplodeFile(explodeL,LOut.comp.suffix)
                #Check that all required layers/files are extracted
                for item in requiredL:
                    if os.path.exists(item.FPN) and item.filecat in ['B','S']:
                        #ConnProcess.InsertCompLayer(LOut)
                        ConnLandsat.ManageLayer(LOut,self.process.delete,self.process.overwrite)
                    elif not os.path.exists(item.FPN):
                        exitstr = 'Explosion failed for %s \n    from %s' %(item.FPN, FIn.FN)
                        sys.exit(exitstr)
            #register file as extracted in db
            ConnLandsat.UpdateSceneStatusOnFN(FIn.FN,'exploded','Y') 
            #Accessmeta on the fly
            #procAttrParamD['archive'] = archive
            if 'xml' in metaD:
                metaLayer = metaD['xml']
            else:
                sys.exit('Can not get proper metafile in explode')
            self.AccessSingleMetaFile(LOut.comp,archive,metaLayer,explodeD)
            
    def ExplodeLandsat(self,procAttrParamD,locationL):       
        self.wrs = procAttrParamD['wrs']
        self.dataunit = procAttrParamD['dataunit']
        #self.SetLandsatSource(procAttrParamD['sensor'],procAttrParamD['satellite'])
        #key = self.process.compinD.keys()[0]
        #Hardcoded status of landsatscenes to search for 
        redundantStatus = self.SceneTileStatus(procAttrParamD['redundant'])
        explodedStatus = self.SceneTileStatus(procAttrParamD['exploded'])
        statusD = {'organized':'Y', 'exploded':explodedStatus, 'redundant':redundantStatus ,'deleted':'N', 'dataunit':self.dataunit,'wrs':self.wrs, 'tgnote':'ok'}
        if self.process.proj.regionid != 'globe':
            statusD['regionid'] = self.process.proj.regionid.lower()
        locationDates = ConnLandsat.SelectLocationScenes(self.process,statusD)
        for locDate in locationDates:
            self.ExplodeScene(locDate)
                    
    def AccessSingleMetaFile(self,comp,archive,metaLayer,layerD):
        if os.path.isfile(metaLayer.FPN):
            if archive in ['USGScollL1v2016']:
                globalD, bandDL = ReadEESceneXML(metaLayer.FPN)  
            else:
                exitstr = 'metadata archive not recognized: %s' %(archive) 
                sys.exit(exitstr)             
            bands = ConnLandsat.GetBandsFromTemplate(metaLayer.typeid)  
            #band,pattern,filecat,folder 
            for bandD in bandDL:
                bandin = False
                for band in bands:
                    if band[1] in bandD['bandfilename']:
                        bandin = band[0]
                        filecat = band[2]
                        break
                if bandin:
                    if bandD['offsetadd'] == '': bandD['offsetadd'] = 0
                    if bandD['scalefac'] == '': bandD['scalefac'] = 1
                    if bandD['cellnull'] == '': 
                        if 'fill' in bandD:
                            if bandD['fill'] != '': bandD['cellnull'] = bandD['fill']              
                    #ConnLandsat.UpdateBandMeta(metaLayer.id, bandin, metaLayer.comp.product, bandD['shortname'],bandD['longname'],bandD['cellnull'],bandD['celltype'],bandD['scalefac'],bandD['offsetadd'],bandD['dataunits'],bandD['proddate'],filecat)
                    ConnLandsat.UpdateBandMeta(bandD,layerD[bandin.lower()],filecat)
                    #create a simplified composition
                    comp.scalefac = float(bandD['scalefac'])
                    comp.offsetadd = bandD['offsetadd']
                    comp.cellnull = bandD['cellnull']
                    ConnComp.CheckCompDef('landsat', comp)
                    #ConnProcess.CheckCompDef(bandD, layerD[bandin.lower()], 'landsat','allscenes','1.0')         
                    #set lins and cols from RL,GL - always exists
                    if band[0].lower() in ['rl','gl']:
                        reflins = bandD['lins']
                        refcols = bandD['cols']
                    #manage the mask
                    if bandD['name'].lower() == 'cfmask':
                        mask = [int(bandD['snow']),int(bandD['cloud']),int(bandD['cloud_shadow'])]
                        folder = 'mask'
                        masks = ConnLandsat.GetLandsatBandCompsFromSceneId(metaLayer.sceneid,folder)
                        if len(masks) != 1:
                            print 'not 1 (but %s) masks for scene: %s' %(len(masks), metaLayer.sceneid)
                            print 'masks', masks
                            BALLE
                        source,product,folder,band,prefix,suffix,masked = masks[0]
                        ConnLandsat.InsertMaskData(source,product,int(bandD['cellnull']),int(bandD['water']),int(bandD['cloud_shadow']),int(bandD['snow']),int(bandD['cloud']),int(bandD['clear']),mask)
                        
            #TGTODO Set the wrs from globalD in landsatscenes
            globalD['reflins'] = reflins
            globalD['refcols'] = refcols
            ConnLandsat.InsertLandsatScenesGeo(metaLayer.sceneid,product,globalD)
            wrsOK = ConnLandsat.UpdateLandsatscenesMeta(metaLayer.sceneid,product,globalD)
            if not wrsOK:
                sys.exit('not correct wrs')
            #Register metacheck as done
            ConnLandsat.UpdateSceneStatus(metaLayer.sceneid,product,'metacheck','Y')
        else:
            exitstr = 'Can not find meta file %s' %(metaLayer.FN)
            sys.exit(exitstr)
        
    def CheckInDB(self, recL):
        for rec in recL:   
            #Create an instance of landsat file
            FIn = self.CreateFileInstance(rec)
            sceneid, scenefilename, source, product, path, row, acqdate, typeid, l1type, collection, tier, dataunit, proddate, folder, downloaded, organized, extracted, deleted, maskstatus, metacheck = rec
            #test, downloaded, organized, extracted, deleted,  maskstatus, metacheck = rec[13:20]
            #check db consistency
            if organized == 'Y' and downloaded == 'N':
                warnstr = 'WARNING %s (%s)\n     indicated as organized but not downloaded' %(FIn.FN, sceneid)
                print warnstr
            if extracted == 'Y' and organized == 'N':
                warnstr = 'WARNING %s (%s)\n     indicated as extracted but not organized' %(FIn.FN,sceneid)
                print warnstr
            if metacheck == 'Y' and extracted == 'N':
                warnstr = 'WARNING %s (%s)\n     indicated as metachecked but not extracted' %(FIn.FN, sceneid)
                print warnstr
            if maskstatus == 'Y' and metacheck == 'N':
                warnstr = 'WARNING %s (%s)\n     indicated as maskstatus OK but not metachecked' %(FIn.FN, sceneid)
                print warnstr    
                #check maskstatus
                maskdb = ConnLandsat.SelectMaskOnSceneId(sceneid,product)
                if maskdb == None:
                    ConnLandsat.UpdateSceneStatus(sceneid,product,'metachecked','N')
                    metachecked = 'N'
                else:
                    ConnLandsat.UpdateSceneStatus(sceneid,product,'maskstatus','Y')
                    maskstatus = 'Y'
            #Check scene file (the downloaded one)
            #Check if downloaded and organized
            if downloaded == organized == 'Y' and deleted == 'N':
                if not os.path.isfile(FIn.FPN):
                    warnstr = '%s\n     indicated as organized but does not exist in its place' %(FIn.FPN)
                    print warnstr
            #Check if deleted
            if deleted == 'Y':
                if os.path.isfile(FIn.FPN):
                    warnstr = '%s\n     indicated as deleted but exists in its place' %(FIn.FPN)
                    print warnstr
            #Check if extracted
            #Get all the layers that are supposed to be extracted
            allLayers = ConnLandsat.SelectSceneTemplateLayersOnFN(scenefilename)
            #convert to dict with band as key and required as value
            bandMissingD = {}
            for lyr in allLayers:
                if lyr[13] == 'Y':
                    bandMissingD[lyr[3]] = True
            #Get the layers for this file
            InLayers = ConnLandsat.SelectSceneLayers(FIn)
            for InLayer in InLayers:
                source, product, folder, band, prefix, suffix, masked, defaultext, filecat, cellnull, celltype, scalefac, offsetadd, dataunit, proddate, status, longname = InLayer
                comp = Composition({'source':source,'product':product, 'folder':folder, 'band':band,'prefix':prefix, 'suffix':suffix}) 
                comp.SetExt(defaultext)
                comp.SetPath(self.process.srcpath)
                L = self.process.CreateLandsatLayerInstance(comp, sceneid, self.wrs, path, row, acqdate, typeid)
                #L = self.CreateLandsatLayerInstance(comp, sceneid, path, row, acqdate, typeid)
                #Get the template information
                template = ConnLandsat.SelectSceneTemplateLayersOnFNBand(scenefilename,L.comp.band)
                if template == None:
                    warnstr = '%s band %s\n     could not be identified in template' %(L.FN, L.comp.band)
                    print warnstr
                    if os.path.isfile(L.FPN):
                        warnstr = '    but the file exists' 
                        print warnstr
                    else:
                        warnstr = '    and no file exists'            
                else: #template exists
                    tsenssat, tproduct, tfolder, tband, tprefix, ttypeid, tfileext, tpattern, tcelltype, tdataunit, tfilecat, ttypeid, thdfgrid, trequired = template
                    #check consistency between template and layer for spatial data
                    '''
                    if filecat != tfilecat:
                        warnstr = '    Filecat differs between metadata and template; %s : %s' %(filecat, tfilecat)
                        print warnstr
                    if filecat != 'M':
                        if celltype != tcelltype:
                            warnstr = '    Celltype differs between metadata and template; %s : %s' %(celltype, tcelltype)
                            print warnstr
                        if dataunit != tdataunit:
                            warnstr = '    Dataunit differs between metadata and template; %s : %s' %(dataunit, tdataunit)
                            print warnstr
                    '''
                    #Get the compdf
                    if filecat != 'M': 
                        compdef = ConnProcess.SelectCompDef(self.process.proj.system)
                        thiscomp = [folder, band, scalefac, offsetadd, dataunit]
                        if compdef == None:
                            print thiscomp
                            INSERTCOMPDEF
                        else: 
                            update = False  
                            comp = []                                 
                            for x,c in enumerate(compdef):
                                if c == None:
                                    comp.append(thiscomp[x])
                                else:
                                    update = True
                                    comp.append(c)
                                    if c != thiscomp[x]:
                                        warnstr = '    compdef definition differs; %s : %s' %(c, thiscomp[x])
                                        print warnstr
                                        update = False
                                        break
                            if update:
                                compD = {'folder':comp[0], 'band':comp[1],  'scalefac':comp[2], 'offsetadd':comp[3], 'dataunit':comp[4]}
                                ConnProcess.UpdateCompDef(compD)
                        compprod = ConnProcess.SelectCompProd(folder,band,product)
                        thiscomp = [product, cellnull, celltype]
                        if compprod == None:
                            compD = {'folder':folder, 'band':band,  'product':thiscomp[0], 'cellnull':thiscomp[1], 'celltype':thiscomp[2],'source':source,'suffix':suffix}
                            ConnProcess.InsertCompProd(compD)
                        else: 
                            update = False  
                            comp = []                                 
                            for x,c in enumerate(compprod):
                                if c == None:
                                    comp.append(thiscomp[x])
                                else:
                                    update = True
                                    comp.append(c)
                                    if c != thiscomp[x]:
                                        warnstr = '    compproduct definition differs; %s : %s' %(c, thiscomp[x])
                                        print warnstr
                                        update = False
                                        break
                            if update:
                                compD = {'folder':folder, 'band':band,  'product':comp[0], 'cellnull':comp[1], 'celltype':comp[2], 'masked':'N'}
                                ConnProcess.UpdateCompProd(compD)
                    if not os.path.isfile(L.FPN):
                        if trequired == 'Y':
                            bandMissingD[tband] = L.FPN
                        if extracted == 'Y':
                            if tfolder != 'no':
                                warnstr = '%s (%s)\n     should be extracted, but does not exist' %(L.FN,sceneid)
                                print warnstr
                            if status == 'extracted':
                                warnstr = '     and both scene and layer are registered as extracted'
                            else:
                                warnstr = '     and scene is registered as extracted'
                            print warnstr
                    else:     
                        if band in bandMissingD:
                            bandMissingD[band] = False 
                        #check that status is extracted for the layer
                        if not status == 'extracted':
                            warnstr = '%s (%s)\n     indicated as not extracted but exists in its place' %(L.FPN, sceneid)
                            print warnstr
                    allExtracted = True
            for key in bandMissingD:                 
                if bandMissingD[key]:
                    allExtracted = False
                    if extracted == 'Y':
                        warnstr = '%s band %s (%s)\n is required but does not exists in its place' %(bandMissingD[key], key, sceneid)
                        print warnstr   
                        warnstr = '    and scene is erronously recorded as extracted'
                        print warnstr
            if allExtracted and extracted == 'N':
                warnstr = '%s (%s)\n     indicated as not extracted but all required layers exist in place' %(FIn.FPN, sceneid)
                print warnstr
            #Check if metadata is extracted, by just checking if the scene is included in landsatscenegeo and maskdata
            geoData = ConnLandsat.SelectSceneGeo(FIn)
            maskData = ConnLandsat.SelectSceneMask(FIn)
            #check if the maskdata is in place
            if geoData == None and maskData:
                warnstr = '%s (%s)\n   maskdata ok, but not geodata' %(FIn.FN, sceneid)
                print warnstr
            elif maskData == None and geoData:
                warnstr = '%s (%s)\n   geodata ok, but not maskdata' %(FIn.FN, sceneid)
                print warnstr
            if geoData == None and metacheck == 'Y':
                warnstr = '%s (%s)\n   metacheck is erronously recorded as True, but is not done' %(FIn.FN, sceneid)
                print warnstr
            elif not allExtracted and metacheck == 'Y':
                warnstr = '%s (%s)\n   metacheck is erronously recorded as True, but all required bands and not extracted' %(FIn.FN, sceneid)
                print warnstr                      
            elif geoData and metacheck == 'N' and allExtracted:
                warnstr = '%s (%s)\n   metacheck is erronously recorded as False, but is done' %(FIn.FN, sceneid)
                print warnstr
    
    def RefreshDB(self,folder,sensat):
        standardFNs = ConnLandsat.GetDBscenetypes()
        standardBNs = ConnLandsat.GetDBbandtypes()
        key = self.process.compinD.items()[0][0]
        checkFP = os.path.join(self.process.compinD[key].mainpath,sensat,self.process.compinD[key].division, folder)
        if os.path.exists(checkFP):
            print '    checking path:',checkFP
            for subdir, dirs, files in os.walk(checkFP):
                for d in dirs:
                    if len(d) == 8 and d.isdigit():
                        dateFP = os.path.join(subdir,d)
                        fileL = [ f for f in os.listdir(dateFP) if os.path.isfile(os.path.join(dateFP,f)) ]
                        #Loop over the files and skip system files as well as delete quicklooks and display support
                        if len(fileL) > 0: 
                            popL = []
                            for x, FN in enumerate(fileL):
                                if FN[0] == '.':
                                    popL.append(x)
                                elif os.path.splitext(FN)[1].lower() in ['.jpg','.png','.prm','.gtf','.bup']:
                                    popL.append(x)
                                    os.remove(os.path.join(dateFP,FN))
                                elif FN == 'umdfilepath.txt':
                                    popL.append(x)
                                elif '.tif.aux.xml' in FN:
                                    popL.append(x)
                                    os.remove(os.path.join(dateFP,FN))
                            popL.reverse()
                            for p in popL:
                                fileL.pop(p)
                        if len(fileL) > 0:
                            #Get ehe path and row      
                            FP,iDate = os.path.split(dateFP)
                            FP,wrsrow = os.path.split(FP)
                            wrspath = os.path.split(FP)[1]
                            if len(fileL) > 0:
                                for FN in fileL:
                                    print '        filename',FN
                                    rec = ConnLandsat.SelectSceneOnFN(FN)
                                    acqdate = mj_dt.yyyymmddDate(iDate)
                                    path = int(wrspath[1:4])
                                    row = int(wrsrow[1:4])
                                    if rec == None:   
                                        #Set the full path to the file
                                        FPN = os.path.join(dateFP,FN)
                                        warnstr = '%s\n     is a non-registered scene' %(FN)
                                        print warnstr
                                        Fin, Fout, updateD = self.IdentifyScene(standardFNs,standardBNs,FN,2,self.process.srcpath)
                                        Fin.downloaded = 'Y'
                                        ConnLandsat.InsertScene(Fin)
                                        for key in updateD:
                                            ConnLandsat.UpdateSceneStatusOnFN(FN,key,updateD[key])
                                        #Explode the scene
                                        locDate = (Fin.sceneid, Fin.FN, Fin.comp.source, Fin.comp.product, folder, path, row, acqdate)
                                    else:
                                        #Get scene from filename
                                        locDate = ConnLandsat.SelectLocationDateFromFN(FN)
                                    self.ExplodeScene(locDate)
     
    def CheckLandsat(self,processElement,procAttrParamD):
        #Set the parameters   
        self.redundant = procAttrParamD['redundant']
        self.checkmeta = procAttrParamD['meta']
        self.checkdownload = procAttrParamD['download']
        self.checkorganized = procAttrParamD['organized']
        self.checkextract = procAttrParamD['extract']
        self.checkmask = procAttrParamD['mask']
        self.dataunit = procAttrParamD['dataunit']
        #self.SetLandsatSource(procAttrParamD['sensor'],procAttrParamD['satellite'])
        #Hardcoded bands for different sensors
        MSS = ['GL','RL','RE','NB']
        TM = ETM = ['BL','GL','RL','NA','MB','MC']
        OLI = ['CB','BL','GL','RL','NA','MB','MC']
        #Get all the template scenes
        recs = ConnLandsat.SelectDistinctTemplateLayers()
        for rec in recs:
            if rec[0] == 'LC8': bandL = OLI
            elif rec[0] == 'LE7': bandL = ETM
            elif rec[0] == 'LT4': bandL = TM
            elif rec[0] == 'LT5': bandL = TM
            else:
                exitstr = 'default band for template sensor %s not defined in script' %(rec[0])
                sys.exit()
            layers = ConnLandsat.SelectTemplateTypeLayers(rec)
            layerD = {}
            for layer in layers:
                if layer[2] == 'B':
                    layerD[layer[0]] = layer[1]
            for b in bandL:
                if b not in layerD:
                    exitstr = 'FATAL ERROR, band %(s) missing in template with typeid %(s)' %(b, rec[1])
                    sys.exit(exitstr)

        #status = SceneTileStatus(redundant = self.redundant, dataunit = self.dataunit)
        #TGTODO MOVE TO EARLIER
        if self.process.proj.regionid in ['globe','karttur']:
            landsatWRSL = ConnLandsat.SelectAllWRS()
        else:
            fisk
        for wrspr in landsatWRSL:
            for sensat in self.sourceL:
                pass
        #Reverse, and loop over all the files instead
        for sensat in self.sourceL:
            #JUST RUN ORIGINAL THAN RUN EXPLODE AGAIN = FASTER 
            print '    mainloop',sensat
            self.RefreshDB('original',sensat)
                  
def EEsceneNodes(topNode,topAttrL,mainNodeL,subNodeL,inputParamL,attrParamL): 
    #topNode = gNode[0]
    valL = []
    paramL = []
    for x,attr in enumerate(topAttrL):
        valL.append(topNode.getAttribute(attr))
        paramL.append(attrParamL[x])
        
    for x,node in enumerate(mainNodeL):
        keyNodes = topNode.getElementsByTagName(node)
        for keyNode in keyNodes:
            if not subNodeL[x]:
                #node = keyNode[0].getElementsByTagName(item)
                valL.append(keyNode.firstChild.nodeValue)    
                paramL.append(inputParamL[x])
            else:
                if len(subNodeL[x][0]) > 0:
                    #get the attributes
                    for a,attr in enumerate(subNodeL[x][0]):                        
                        if inputParamL[x][0][0] == 'self':
                            param = '%(a)s%(p)s' %{'a':keyNode.getAttribute(subNodeL[x][0][0]),'p':inputParamL[x][0][a]}
                            paramL.append(param)
                            valL.append(keyNode.getAttribute(attr))
                        elif inputParamL[x][0][0] == 'node':   
                            param = keyNode.firstChild.nodeValue
                            paramL.append(param.replace(' ', ''))                            
                            valL.append(keyNode.getAttribute(subNodeL[x][0][1]))
                            break
                        else:
                            paramL.append(inputParamL[x][0][a])
                            valL.append(keyNode.getAttribute(attr))
                if len(subNodeL[x][1]) > 0:
                    for n,nodename in enumerate(subNodeL[x][1]):
                        nodes = keyNode.getElementsByTagName(nodename)
                        for node in nodes:
                            valL.append(node.firstChild.nodeValue)
                            paramL.append(inputParamL[x][1][n])
    return paramL,valL
        
def ReadEESceneXML(xmlFN):
    #THis is not the complete xml, only stuff I can not get from the eartexplorer bulk metadata download (and some overlap to confirm)
    globalNodeL = ['data_provider','satellite','instrument','acquisition_date','level1_production_date','solar_angles','earth_sun_distance','wrs','corner','bounding_coordinates','projection_information','corner_point','utm_proj_params']   
    globalSubNodeL = [False,False,False,False,False,[['zenith','azimuth','units'],[]],False,[['system','path','row'],[]],[['location','longitude','latitude'],[]],[[],['west','east','north','south']],[ ['projection','datum','units'],[] ],[['location','x','y'],[]],[[],['zone_code']]] 
    globalParamL = ['data_provider','satellite','sensor','acqdate','L1proddate',[['sunzenith','sunazimuth','sunangleunits'],[]],'esundist',[['wrs','path','row'],[]],[['self','longitude','latitude'],[]],[[],['west','east','north','south']],[ ['projection','datum','units'],[] ],[['self','x','y'],[]],[[],['utmzone']]] 
    attrL = []
    dom = minidom.parse(xmlFN) 
    #Read global data
    gNode = dom.getElementsByTagName('global_metadata') 
    paramL,valL = EEsceneNodes(gNode[0],attrL,globalNodeL,globalSubNodeL,globalParamL,attrL)
    globalD = dict(zip(paramL,valL))
       
    bandAttrL = ['product','source','name','category','data_type', 'nlines', 'nsamps','fill_value','saturate_value', 'scale_factor' ,'add_offset']
    attrParamL = ['product','source','name','category','celltype', 'lins', 'cols','cellnull','saturationval', 'scalefac' ,'offsetadd']

    bandNodeL = ['short_name','long_name','file_name','pixel_size','data_units','class','app_version','production_date']
    bandSubNodeL = [False,False,False,[['x','y','units'],[]],False,[['node','num'],[]],False,False]
    bandParamL =['shortname','longname','bandfilename',[['xresol','yresol','sizeunits'],[]],'dataunits',[['node','num'],[]],'appversion','proddate']
    #bandparamL = ['product','source','name',[['x''y','units'],[]],False,[[],['node','num'],[]],'appversion','proddate']
    #Read band data
    bandDL = []
    bandsTopNode = dom.getElementsByTagName('bands') 
    bandsNode =  bandsTopNode[0].getElementsByTagName('band')
    for bandNode in bandsNode:
        paramL,valL = EEsceneNodes(bandNode,bandAttrL,bandNodeL,bandSubNodeL,bandParamL,attrParamL)
        bandD = dict(zip(paramL,valL))
        #split proddate into date and time
        if 'T' in bandD['proddate']:
            bandD['proddate'] = bandD['proddate'].split('T')[0]
        bandDL.append(bandD)
        #convert celltype to GDAL format'
        if 'celltype' in bandD:
            bandD['celltype'] = usgsctRevD[bandD['celltype']]
    #split L1proddate into date and time
    if 'T' in globalD['L1proddate']:
        globalD['proddate'] = globalD['L1proddate'].split('T')[0]
    return globalD, bandDL

def LandsatData():
    #Organize any downloaded landsat data
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/landsat/organizelandsat_v70.xml')
    #Explode downloaded landsat data
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/landsat/explodelandsat_v70.xml')
    #check the entire landsat library
    #To recheck meta, use explode and set exploded to Y - not tested
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/landsat/checklandsat_v70.xml')
            
def LandsatDB():
    '''regions-landsat-wrs_vXX.xml loops all default regions and extracts the wrs (descending = daytime) sccenes covering
    each region, it takes a long time and should be done AFTER copy_regionswrs_sqldump_v70 of into its table '''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/region/xml/regions-landsat-wrs_v70.xml')
    
    ''' Insert the complete landsat library meta data'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/landsat/insertbulkmeta_v70.xml')


def LandsatData():
    #Organize any downloaded landsat data
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/landsat/organizelandsat_v70.xml')
    #Explode downloaded landsat data
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/landsat/explodelandsat_v70.xml')
    #check the entire landsat library
    #To recheck meta, use explode and set exploded to Y - not tested
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/landsat/checklandsat_v70.xml')
            
def LandsatDB():
    '''regions-landsat-wrs_vXX.xml loops all default regions and extracts the wrs (descending = daytime) sccenes covering
    each region, it takes a long time and should be done AFTER copy_regionswrs_sqldump_v70 of into its table '''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/region/xml/regions-landsat-wrs_v70.xml')
    
    ''' Insert the complete landsat library meta data'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/landsat/insertbulkmeta_v70.xml')
                   
def UpdateLandsatScene():
    allScenes = ConnLandsat.SelectAllScenes()
    for rec in allScenes:
        ConnLandsat.UpdateScene(rec[0],rec[1],rec[2])
                                             
if __name__ == "__main__":
   
    StartUp() #Link all the python scripts and some default databases for format translations, must be run at stratup each time
    
 