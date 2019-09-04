'''
Created on 14 feb 2012

@author: thomasg

'''
#imports
from __future__ import division
import sys
import os
import shutil
from xml.dom import minidom
import mj_datetime_v70 as mj_dt
import mj_gis_v70 as mj_gis
import mj_GDAL_v70 as mj_GDAL
import numpy as np
from mj_pandas_v71 import PandasTS
import mj_support_v70 as Support
import mj_html_v70 as mj_html

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
        
class UserProject():
    """class managing user projects.
    Most processing beyond viewing and creating map layouts of the view requires
    user registreration and for the most advanced processering the user must also
    own or have access the defined processes.
    """
    def __init__(self, userid, pswd, system, projectid = False): 
        """The constructor expects a userid and the associated password, project is optional."""
        self.userid = userid
        self.userpswd = pswd
        self.system = system
        self.projectid = projectid
        
    def SetSystemSession(self):
        self.regionid = self.regioncat = self.defregid = 'globe'
        
    def SetSession(self,tractid, siteid, plotid):
        """SetSession defines the project, or part of project, that the user has defined for the session."""
        self.CheckSetTractId(tractid,siteid,plotid)
        #Determine if the project session relates to tract,site or plot
        if plotid not in ['*','']:
            self.regioncat = 'plot'
            self.regionid = plotid
            self.plotid = plotid

        elif siteid not in ['*','']:
            self.plotid = False
            self.regioncat = 'site'
            self.regionid = siteid
            self.siteid = siteid
            rec = ConnRegions.SelectSiteDefregid(siteid)
            if rec == None:
                BALLE
            self.defregid, self.defregcat = rec
        else:
            self.plotid = False
            self.siteid = False
            self.tractid = tractid
            self.regioncat = 'tract'
            self.regionid = tractid
            rec = ConnRegions.SelectTractDefregid(tractid)
            if rec == None:
                BALLE
            self.defregid, self.defregcat = rec

            
    def CheckSetTractId(self,tractid,siteid,plotid):
        """Subprocess under SetSession that identifies the actual spatial region related to a project (i.e. if the user has selected to work with a subset caled site, or a single plot within the project)."""
        tractrec = ConnRegions.GetProjectTract(self,tractid,siteid,plotid)
        if tractrec == None:
            usertracts = ConnRegions.GetUserTracts(self)
            print 'usertracts for user %s: %s' %(self.userid, usertracts)
            BALLE
            sys.exit('no region/tract/site identified in CheckSetTractId')
            BALLE
        if plotid not in ['*','']:
            self.plotid, self.siteid, self.tractid, self.parentid = tractrec
        elif siteid not in ['*','']:
            self.siteid, self.tractid, self.parentid = tractrec
            plotid = False
        else: 
            self.tractid, self.parentid = tractrec
            plotid = siteid = False

class TimeSteps:
    """Periodicity sets the time span, seasonality and timestep to process data for."""   
    def __init__(self,timestep,periodD):
        """The constructor expects the following variables: int:timestep, date:startdate, date:enddate, [int:addons], [int:maxdaysaddons], [int:seasonstartDOY], [int:seasonendDOY]."""
        self.datumL = []
        self.timestep = timestep
        if timestep == 'static':
            self.SetStaticTimeStep()
        elif timestep == 'singledate':
            self.SingleDateTimeStep()
        elif timestep == 'singleyear':
            self.SingleYearTimeStep(periodD)
        elif timestep == 'staticmonthly':
            self.SingleStaticMonthlyStep(periodD)
        elif timestep == 'fiveyears':
            self.FiveYearStep(periodD)
        elif timestep == 'monthly':
            self.MonthlyTimeStep(periodD)
        elif timestep == 'monthlyday':
            self.MonthlyDayTimeStep(periodD)
        else:
            self.SetStartEndDates(periodD)
            if timestep == 'varying':
                self.Varying(periodD)
            elif timestep == 'allscenes':
                self.AllScenes(periodD)
            elif timestep == 'inperiod':
                self.InPeriod(periodD)
            elif timestep == 'ignore':
                self.Ignore(periodD)
            elif timestep == '8D':
                self.SetDstep(periodD)
            elif timestep == '16D':
                self.SetDstep(periodD)
            else:
                exitstr = 'Unrecognized timestep in class TimeSteps %s' %(timestep)
                print exitstr
                BALLE
                sys.exit(exitstr)
                
    def SetStartEndDates(self, periodD):
        self.startdate = mj_dt.IntYYYYMMDDDate(periodD['startyear'],periodD['startmonth'],periodD['startday'])       
        self.enddate = mj_dt.IntYYYYMMDDDate(periodD['endyear'],periodD['endmonth'],periodD['endday'])
        self.startdatestr = mj_dt.DateToStrDate(self.startdate)
        self.enddatestr = mj_dt.DateToStrDate(self.enddate)
        if self.enddate < self.startdate:
            exitstr = 'period starts after ending'
            sys.exit(exitstr)
   
    def SetStaticTimeStep(self):
        self.datumL.append({'acqdatestr':'0', 'timestep':'static'})
        
    def SingleYearTimeStep(self,periodD):
        if not periodD['startyear'] == periodD['endyear'] or periodD['startyear'] < 1000:
            print 'error in period: year'
            BALLE
            sys.exit()
        acqdatestr = '%(y)d' %{'y':periodD['startyear']}
        if not len(acqdatestr) == 4:
            BALLE
        self.datumL.append({'acqdatestr':acqdatestr, 'timestep':'singleyear'})
        
    def FiveYearStep(self,periodD):
        if not periodD['startyear'] < periodD['endyear'] or periodD['startyear'] < 1000 or periodD['endyear'] > 9999:
            BALLE
        for y in range(periodD['startyear'],periodD['endyear']+1,5):
            acqdatestr = '%(y)d' %{'y':y}
            if not len(acqdatestr) == 4:
                BALLE
            self.datumL.append({'acqdatestr':acqdatestr, 'timestep':'fiveyears'})

    def SingleStaticMonthlyStep(self,periodD):
        if periodD['endmonth'] < periodD['startmonth'] or periodD['startmonth'] > 12 or periodD['endmonth'] > 12:
            BALLE
        for m in range(periodD['startmonth'],periodD['endmonth']+1):
            if m < 10:
                mstr = '0%(m)d' %{'m':m}
            else:
                mstr = '%(m)d' %{'m':m} 
            self.datumL.append({'acqdatestr':mstr, 'timestep':'staticmonthly'})
            
    def MonthlyDayTimeStep(self,periodD):
        mstr = self.MonthToStr(periodD['startmonth'])
        yyyymmdd = '%(yyyy)s%(mm)s01' %{'yyyy':periodD['startyear'],'mm':mstr }
        startmonth = mj_dt.yyyymmddDate(yyyymmdd)
        mstr = self.MonthToStr(periodD['endmonth'])
        yyyymmdd = '%(yyyy)s%(mm)s01' %{'yyyy':periodD['endyear'],'mm':mstr }
        endmonth = mj_dt.yyyymmddDate(yyyymmdd)
        acqdatestr = mj_dt.DateToStrDate(startmonth)
        self.datumL.append({'acqdatestr':acqdatestr[0:6], 'timestep':'monthlyday'})
        monthday = startmonth
        while monthday < endmonth:
            monthday = mj_dt.AddMonth(monthday)
            acqdatestr = mj_dt.DateToStrDate(monthday)
            #Only set the month, for ile structure consistency
            self.datumL.append({'acqdatestr':acqdatestr[0:6], 'timestep':'monthlyday'})

    def SetDstep(self,periodD):
        pdTS = PandasTS(self)
        npTS = pdTS.SetDates(self)
        self.processDateL = []
        for d in range(npTS.shape[0]):
            acqdatestr = mj_dt.DateToStrDate(npTS[d])
            self.datumL.append({'acqdatestr':acqdatestr, 'timestep':self.timestep})
            self.processDateL.append(npTS[d].date())
                       
    def Varying(self,periodD):
        self.datumL.append({'acqdatestr':'varying', 'timestep':'varying'})
        
    def AllScenes(self,periodD):
        self.datumL.append({'acqdatestr':'allscenes', 'timestep':'allscenes'})
        
    def Ignore(self,periodD):
        self.datumL.append({'acqdatestr':'ignore', 'timestep':'ignore'})
        
    def InPeriod(self,periodD):
        self.datumL.append({'acqdatestr':'inperiod', 'timestep':'inperiod','startdate':self.startdate, 'enddate':self.enddate})
            
    def FindVaryingTimestep(self,path):
        if os.path.exists(path):
            folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
            self.datumL = []
            for f in folders:
                try:
                    int(f)
                    self.datumL.append({'acqdatestr':f, 'timestep':'varying'})
                except:
                    pass
                
    def MonthToStr(self,m):
        if m < 10:
            mstr = '0%(m)d' %{'m':m}
        else:
            mstr = '%(m)d' %{'m':m}
        return mstr

    def SetAcqDateDOY(self):
        for d in self.datumL:
            acqdate = mj_dt.yyyymmddDate(d['acqdatestr'])
            d['acqdatedaystr'] = mj_dt.DateToYYYYDOY( acqdate)
            
            
    def SetAcqDate(self):
        for d in self.datumL:
            d['acqdate'] = mj_dt.yyyymmddDate(d['acqdatestr'])
           
class Parameter:
    def __init__(self, parent,element,pD): 
        self.parent = parent
        self.element = element
        for key, value in pD.items():
            if not hasattr(self, key):
                setattr(self, key, value)

    def SetValues(self,setvalueL):
        self.setvalueL = setvalueL
        
    def MinMax(self,minmaxL):
        self.minmaxL = minmaxL 
        
    def MetaParams(self,aD): 
        for key, value in aD.items():
            if not hasattr(self, key):
                setattr(self, key, value)

class SrcTarPath:
    """SrcTarpath sets the local directory path and the file extension, as applicable.
        Expects a dictionary
        Usually retrieved from xml file, but can be set 
    """
    def __init__(self,pathD):
        """The constructor requires a dict {'mainpath','scenes/tiles','division','hdr','dat'}."""
        if 'mainpath' in pathD:
            self.mainpath = pathD['mainpath']
        else:
            self.mainpath = False
        if 'scenes' in pathD:
            self.scenes = pathD['scenes']
        elif 'tiles' in pathD:
            self.scenes = pathD['tiles']
        else:
            self.scenes = False
        if 'division' in pathD:
            self.division = pathD['division'] 
            if self.division in ['*','']:
                sys.exit('You have to set a division in the path')
        else:
            self.division = False 
        if 'hdrfiletype' in pathD:
            self.hdr = pathD['hdrfiletype']
   
            if self.hdr not in ['','*']:
                if not self.hdr in gdalofD:
                    exitstr = 'You have to add the hdr type "%s" (data type "%s") to gdalofD' %(self.hdr, pathD['datfiletype'])
                    sys.exit(exitstr)
                if gdalofD[self.hdr].lower() == 'none':
                    self.spatial = False
                else:
                    self.spatial = True
            else:
                self.spatial = False
        else:
            self.hdr = False
            self.spatial = False
        if 'datfiletype' in pathD:
            self.dat = pathD['datfiletype']
        else:
            self.dat = False
            
class Composition:
    """Compositions defines files with the same content but at different spatial or temporal positions to be defined.
        More details.
    """
    def __init__(self, *args, **kwargs): 
        if args is not None and len(args) > 0:
            self.source, self.product, self.folder, self.band, self.prefix, self.suffix = args
        if kwargs is not None:
            for key, value in kwargs.items():
                setattr(self, key, value)       
        if hasattr(self, 'folder'):
            self.folder = str(self.folder.lower()).replace(' ', '-') 
        if hasattr(self, 'band'):
            self.band = str(self.band.lower())
            self.compid = '%s_%s' %(self.folder, self.band)
        if hasattr(self, 'prefix'):
            self.prefix = str(self.prefix.lower()).replace(' ', '-')
        if hasattr(self, 'suffix'):
            if self.suffix[0] != '_' :
                self.suffix = '_%(s)s' %{'s':self.suffix}
        else:
            self.suffix = '_none'

            
    def SetPathParts(self,path):
        '''Transfers path to composition, because the path can change if it contains wildcards
        '''
        #TGTODO dondense
        self.mainpath = path.mainpath
        self.scenes = path.scenes
        self.division = path.division
        self.hdr = path.hdr
        self.dat = path.dat
        self.spatial = path.spatial 
        self.SetExt(path.hdr)
        
    def CompFormat(self, formdict):
        """Sets any attribute not already registered should include: measure, cellnull, celltype, calefac, offsetadd, dataunit, system, palette."""
        for key, value in formdict.items():
            if not hasattr(self, key):
                setattr(self, key, value)
        if not hasattr(self, 'palette'):
            self.palette = False
        elif not self.palette:
            pass
        elif not type(self.palette) is list:
            if self.palette.lower() in ['','n','false','none','na'] or len(self.palette) == 1:
                self.palette = False
            else:   
                self.palette = ConnLayout.SelectPalette(self.palette)

    def SetExt(self,ext):
        """Sets the layer extension, usually self.hdr but need explicit setting as self.hdr can be set to wildcards or change with zip."""
        if ext[0] == '.':
            self.ext = ext
        else:
            self.ext = '.%s' %(ext)
            
    def SetCompPath(self,region):
        self.FP = os.path.join(self.mainpath,self.source,self.division,self.folder)
        if region:
            self.FP = os.path.join(self.FP,region)
            
    def SetCompPathRowPath(self,path,row):
        self.FP = os.path.join(self.mainpath,self.source,self.division,self.folder)
        if path:
            self.FP = os.path.join(self.FP,path,row)

class AncilComposition(Composition): 
    def __init__(self,compD):
        """The constructor requires a dict {datadir, datafile, compyright,title,accessdate,theme,subtheme,label,version,
        dataset,product,datapath,metapath,dataurl,metaurl}.""" 
        for key, value in compD.items():
            if not hasattr(self, key):
                setattr(self, key, value) 

    def SetDataFiletype(self,filetype):
        self.datafiletype = filetype
   
    def SetPath(self,mainpath):
        self.FP = os.path.join(mainpath,self.datadir)
        
class Location: 
    def __init__(self, locationcat):
        self.locationcat = locationcat
        """The constructor is empty."""
       
    def Region(self,regionid, *args, **kwargs):
        if regionid:
            self.regionid = str(regionid.lower()).replace(' ', '-')
        if args is not None and len(args) > 0:
            self.regioncat = str(args[0].lower()).replace(' ', '-')
        if kwargs is not None:
            for key, value in kwargs.items():
                setattr(self, key, value)
            if hasattr(self, 'parentcat'):
                self.parentcat = str(self.parentcat.lower()).replace(' ', '-') 
            if hasattr(self, 'parentid'):
                self.parentid = str(self.parentid.lower()).replace(' ', '-') 
            if hasattr(self, 'regionname'):
                self.regionname = str(self.regionname)
                
    def LandsatScene(self,wrs,path,row):
        self.wrs = wrs 
        self.path = self.prInteger(p)
        self.row = self.prInteger(r)
        
    def MODISScene(self,p,r):
        self.path = self.prInteger(p)
        self.row = self.prInteger(r)
    
    def prInteger(self,pr): 
        try:       
            if pr[0].isdigit():
                return int(pr)
            else:
                return int(pr[1:len(pr)])
        except:
            return pr
                       
    def SetBounds(self,epsg,minx,miny,maxx,maxy):
        self.epsg = epsg
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        self.BoundsPtL = ( (minx,maxy),(maxx,maxy),(maxx,miny), (minx,miny) )
        
    def SetLonLatCorners(self, minlon,minlat,maxlon,maxlat):
        self.lonlatD = {'ullat':maxlat,'ullon':minlon,'urlat':maxlat,'urlon':maxlon,'lrlat':minlat,'lrlon':maxlon,'lllat':minlat,'lllon':minlon}
 
class AcqDate: 
    def __init__(self, datum, **kwargs): 
        self.acqdatestr,self.timestep = datum['acqdatestr'],datum['timestep']
        if kwargs is not None:
            for key, value in kwargs.items():
                setattr(self, key, value) 
        if hasattr(self, 'acqdate'):
            self.SetDOY()
            
    def SetDOY(self):
        self.doyStr = mj_dt.YYYYDOYStr(self.acqdate)
        self.doy = int(self.doyStr)
                     
class AncilDataSet:
    def __init__(self,pileD):
        """The constructor requires a dict {dsinst....}.""" 
        for key, value in pileD.items():
            setattr(self, key, value)
        version = pileD['dsversion'].replace('.','')
        version = version.replace('_','-')
        if len(version) == 0:
            version = 'none'
        if version[0].lower == 'v':
            version = '%s' %(version)
        else:
            version = 'v%s' %(version)
        self.version = version
        self.regionid = str(self.regionid.lower())
        self.regioncat = str(self.regioncat.lower())  
        self.dsid = self.pileid = '%(i)s.%(c)s.%(v)s.%(r)s' %{'i':self.dsinst,'c':self.dsname,'v':self.version,'r':self.regionid}
        self.dsplotid = '%(i)s.%(c)s.%(r)s' %{'i':self.dsinst,'c':self.dsname,'r':self.regionid}
   
    def Setparentid(self,parentid):
        self.parentid = parentid

class NonSpatialFile:
    """Layer is the parentid class for non-spatial files."""
    def __init__(self, comp, acqdate): 
        """The constructor expects an instance of the composition class."""
        self.comp = comp
        self.acqdate = acqdate
    
    def SetFilePath(self):
        """Sets the complete path to non spatial files"""
        #self.ext = self.comp.hdr

        if self.acqdate.acqdatestr == '0':
            self.FN = '%(prefix)s_%(prod)s%(suf)s%(e)s' %{'prefix':self.comp.prefix,'prod':self.comp.product,'suf':self.comp.suffix,'e':self.comp.ext}            
            self.FP = os.path.join(self.comp.mainpath,self.comp.source,self.comp.folder)
        else:
            self.FN = '%(prefix)s_%(prod)s_%(d)s%(suf)s%(e)s' %{'prefix':self.comp.prefix,'prod':self.comp.product,'d':self.acqdate.acqdatestr,'suf':self.comp.suffix,'e':self.comp.ext}            
            self.FP = os.path.join(self.comp.mainpath,self.comp.source,self.comp.folder)
        self.FPN = os.path.join(self.FP,self.FN)

class LandsatProd:  
    """Defines landsat product related stuff"""
    
    #TGTODO move to landsat
    def __init__(self, prodD): 
        """The constructor expects a dictionary."""
        for key, value in prodD.items():
            setattr(self, key, value)
        self.product = '%(sensat)s-%(l1type)s-%(coll)s%(tier)s' %{'sensat':self.sensat,'l1type':self.l1type,'coll':self.collection,'tier':self.tier}
        self.source = self.sensat
        
class Layer:
    """Layer is the parentid class for all spatial layers."""
    def __init__(self, comp, location, layerdate): 
        """The constructor expects an instance of the composition class."""
        self.comp = comp
        self.location = location
        self.acqdate = layerdate
        
    def CreateAttributeDef(self,fieldDD): 
        fieldDefD = {}
        self.fieldDefL =[]
        for key in fieldDD:
            fieldD = fieldDD[key]
            if 'width' in fieldD:
                width = fieldD['width']
            else:
                self.width = 8
            if 'precision' in fieldD:
                precision = fieldD['precision']
            else:
                precision = 0
            if 'keyfield' in fieldD:
                keyfield = fieldD['keyfield']
            elif 'field' in fieldD:
                keyfield = fieldD['field']
            else:
                keyfield = False
            fieldDefD[key] = {'type':fieldD['type'].lower(), 'width':width, 'precision': precision, 'transfer': fieldD['transfer'].lower(), 'source':fieldD['source'], 'keyfield':keyfield}      
        for key in fieldDefD:
            self.fieldDefL.append(mj_gis.FieldDef(key,fieldDefD[key]))
    
    def GetVectorProjection(self):
        self.spatialRef = mj_gis.GetVectorProjection(self.FPN)
        
    def GetRastermetadata(self):
        self.spatialRef, self.metadata = mj_gis.GetRasterMetaData(self.FPN)
        
    def SetGeoFormat(self,geoFormatD):
        """Sets the geoFormat
            Expects a dict with {['lins'],['cols'],['projection'],['geotrans'],['cellsize']}
        """ 
        for key, value in geoFormatD.items():
            setattr(self, key, value)
       
    def ReadRasterLayer(self,**kwargs):
        readD = {'mode':'edit','complete':True,'flatten':True}
        if kwargs is not None:
            for key, value in kwargs.items():
                readD[key] = value
                #setattr(self, key, value)
        self.BAND =  mj_gis.ReadRasterArray(self.FPN, readD)
        
    def WriteRasterLayer(self,**kwargs):
        writeD = {'complete':True,'flatten':True, 'of':'GTiff'}
        if kwargs is not None:
            for key, value in kwargs.items():
                writeD[key] = value
        mj_gis.WriteRasterArray(self, writeD)
     
    def RegisterLayer(self,system):
        ''' Register the composition and the layer to the db'''
        ConnComp.InsertCompDef(system,self.comp)
        ConnComp.InsertCompProd(system,system,self.comp)
        ConnComp.InsertLayer(system,self)
                
    def Exists(self):
        """checks if the layer file exists; creates the folder path to the layer if non-existant."""
        if os.path.isfile(self.FPN):
            self.exists = True
            return True
        else:
            if not os.path.isdir(self.FP):
                os.makedirs(self.FP)
            self.exists = False
            return False

class RegionLayer(Layer): 
    """layer class for arbitrary layers.""" 
    def __init__(self,comp, location, layerdate): 
        """The constructor expects an instance of the composition class."""
        Layer.__init__(self, comp, location, layerdate)
        self.layertype = 'region'
        
    def SetRegionPath(self):
        """Sets the complete path to region files"""
        self.FN = '%(prefix)s_%(prod)s_%(reg)s_%(d)s%(suf)s%(e)s' %{'prefix':self.comp.prefix,'prod':self.comp.product,'reg':self.location.regionid, 'd':self.acqdate.acqdatestr, 'suf':self.comp.suffix,'e':self.comp.ext}            
        self.FP = os.path.join(self.comp.mainpath, self.comp.source, self.comp.division, self.comp.folder, self.location.regionid, self.acqdate.acqdatestr)
        self.FPN = os.path.join(self.FP,self.FN)
        if ' ' in self.FPN:
            exitstr = 'EXITING region FPN contains space %s' %(self.FPN)
            sys.exit(exitstr)

class ROILayer(RegionLayer):
    'Common base class for mosaic and region processing'
    def __init__(self,compC, locationC, datum):
        RegionLayer.__init__(self, compC, locationC, datum)
        self.layertype = 'ROI'
        
class MODISLayer(Layer):
    def __init__(self,comp, location, datum): 
        """The constructor expects an instance of the composition class."""
        Layer.__init__(self, comp, location, datum)
        self.system = 'MODIS'
        self.layertype = 'MODIS'
        try:
            path = int(self.location.path)
            if path < 10:
                self.location.pathstr = 'h0%(h)d' %{'h':path}
            else:
                self.location.pathstr = 'h%(h)d' %{'h':path}    
        except:
            if len(self.location.path) == 3 and self.location.path[0] == 'h':
                self.location.pathstr = self.location.path
            else:
                sys.exit('Can not set MODIS h location')
        try:
            row = int(self.location.row)
            if row < 10:
                self.location.rowstr = 'v0%(v)d' %{'v':row}
            else:
                self.location.rowstr = 'v%(v)d' %{'v':row}    
        except:
            if len(self.location.row) == 3 and self.location.row[0] == 'v':
                self.location.rowstr = self.location.path
            else:
                sys.exit('Can not set MODIS v location')
                        
    def SetVersionTileId(self,version):
        #self.comp.SetVersion(version)
        hv = '%s%s' %(self.location.pathstr,self.location.rowstr)
        self.id = '%(prod)s-%(yyyydoy)s-%(hv)s' %{'prod':self.comp.product,'yyyydoy':self.acqdate.acqdatedoy,'hv':hv }
        
    def SetLayerPath(self):
        """Sets the complete path to landsat layer files"""
        if self.comp.scenes:
            self.FN = '%(prefix)s_%(prod)s_%(p)s%(r)s_%(d)s%(suf)s%(e)s' %{'prefix':self.comp.prefix,'prod':self.comp.product,'p':self.location.pathstr,'r':self.location.rowstr,'d':self.acqdate.acqdatedoy,'suf':self.comp.suffix,'e':self.comp.ext}            
            self.FP = os.path.join(self.comp.mainpath, self.comp.source, self.comp.division, self.comp.folder,self.location.pathstr,self.location.rowstr,self.acqdate.acqdatedoy)
        else:
            self.FN = '%(band)s_%(prod)s_%(r)s_%(d)s%(suf)s%(e)s' %{'band':self.comp.prefix,'prod':self.comp.product,'r':self.comp.region,'d':self.acqdate.acqdatedoy,'suf':self.comp.suffix,'e':self.comp.ext}            
            if self.wrsStr:
                self.FP = os.path.join(self.fp,self.wrsStr,self.division,self.folder,self.region,self.acqdate.acqdatedoy)
            else:
                self.FP = os.path.join(self.fp,self.division,self.folder,self.region,self.acqdate.acqdatedoy)
        self.FPN = os.path.join(self.FP,self.FN)

        
class MODISScene(MODISLayer): 
    """layer class for landsat scenes.""" 
    def __init__(self,comp,location,datum): 
        """The constructor expects an instance of the composition class and the wrs (1 or 2)."""
        MODISLayer.__init__(self, comp,location,datum) 
        
    def SetScenePath(self):
        self.FP = os.path.join(self.comp.mainpath, self.comp.source, self.comp.division, self.comp.folder, self.location.pathstr, self.location.rowstr, self.acqdate.acqdatedoy)
        self.FPN = os.path.join(self.FP,self.FN)
        
 
class LandsatLayer(Layer):
    """layer class for landsat derived layers.""" 
    def __init__(self,comp, location, datum): 
        """The constructor expects an instance of the composition class."""
        Layer.__init__(self, comp, location, datum)
        self.system = 'landsat'
        self.layertype = 'landsat'
        try:
            path = int(self.location.path)
            if path < 10:
                self.location.pathstr = 'p00%(p)d' %{'p':path}
            elif path < 100:
                self.location.pathstr = 'p0%(p)d' %{'p':path}
            else:
                self.location.pathstr = 'p%(p)d' %{'p':path}    
        except:
            if len(self.location.path) == 4 and self.location.path[0] == 'p':
                self.location.pathstr = self.location.path
            elif len(self.location.path) == 3 and self.location.path[0] != 'p':
                self.location.pathstr = 'p%s' %(self.location.path)
            else:
                sys.exit('Can not set landsat location')
        try:
            row = int(self.location.row)
            if row < 10:
                self.location.rowstr = 'r00%(r)d' %{'r':row}
            elif row < 100:
                self.location.rowstr = 'r0%(r)d' %{'r':row}
            else:
                self.location.rowstr = 'r%(r)d' %{'r':row}    
        except:
            if len(self.location.row) == 4 and self.location.row[0] == 'r':
                self.location.rowstr = self.location.path
            elif len(self.location.row) == 3 and self.location.row[0] != 'r':
                self.location.rowstr = 'r%s' %(self.location.row)
            else:
                sys.exit('Can not set landsat location')
        
        
    def SetLandsatProduct(self,lprod):
        self.lprod = lprod
            
    def SetPattern(self,pattern):
        """pattern is the search string of the filename in the downloaded zip file. 
        Only required for the method organizelandsat. Set from the templatelayers db table.
        """
        self.pattern = pattern
        
    def SetHdfGrid(self,hdfGrid):
        """hdfgrid is the hdf grid name of the layer. 
        Only required for the method organizelandsat. Set from the templatelayers db table.
        """
        self.hdfGrid = hdfGrid
        
    def SetFileCat(self,filecat):
        """filecat is either B (band), S (support), M (meta). 
        Only required for the method organizelandsat. Set from the templatelayers db table.
        """
        self.filecat = filecat
        
    def SetLayerPathOld(self):
        """Sets the complete path to landsat layer files"""
        if self.comp.scenes:
            self.FN = '%(prefix)s_%(prod)s_%(p)s%(r)s_%(d)s%(suf)s%(e)s' %{'prefix':self.comp.prefix,'prod':self.comp.product,'p':self.location.pathstr,'r':self.location.rowstr,'d':self.acqdate.acqdatestr,'suf':self.comp.suffix,'e':self.comp.ext}            
            self.FP = os.path.join(self.comp.mainpath, self.comp.source, self.comp.division, self.comp.folder,self.location.pathstr,self.location.rowstr,self.acqdate.acqdatestr)
        else:
            self.FN = '%(band)s_%(prod)s_%(r)s_%(d)s%(suf)s%(e)s' %{'band':self.comp.prefix,'prod':self.comp.product,'r':self.comp.region,'d':self.acqdate.acqdatestr,'suf':self.comp.suffix,'e':self.comp.ext}            
            if self.wrsStr:
                self.FP = os.path.join(self.fp,self.wrsStr,self.division,self.folder,self.region,self.acqdate.acqdatestr)
            else:
                self.FP = os.path.join(self.fp,self.division,self.folder,self.region,self.acqdate.acqdatestr)
        self.FPN = os.path.join(self.FP,self.FN)
        
    def SetSenSatCollTierL1(self,sensorid,satelnr,collection,tier,datatypel1):
        self.sensorid = sensorid
        self.satelnr = satelnr
        self.collection = collection
        self.sensorid = sensorid
        self.tier = tier
        self.datatypel1 = datatypel1
                         
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
   
class AncillaryLayer(RegionLayer):
    'Common base class for Ancillary spatial data of different formats'
    def __init__(self, comp, rawcomp, location, acqdate, ancilDS):
        self.comp = comp
        self.layertype = 'ancillary'
        self.ancilDS = ancilDS
        self.comp = comp
        self.rawcomp = rawcomp   
        self.acqdate = acqdate
        self.ancilid = '%(p)s.%(d)s' %{'p':self.ancilDS.dsid,'d':rawcomp.datalayer}  
        if rawcomp.datadir == '':
            datadir = self.ancilDS.datadir
        else:
            datadir = rawcomp.datadir
        self.datapath = datadir
        if rawcomp.metapath == '':
            metapath = ancilDS.metapath
        else:
            metapath = rawcomp.metapath
        if len(metapath) > 1:
            metapath = '../%(m)s' %{'m':metapath}
        else:
            metapath = ''
        self.metapath = rawcomp.metapath
        if len(rawcomp.accessdate) >= 4:
            self.accessdate = mj_dt.yyyymmddDate(rawcomp.accessdate) 
        else:
            self.accessdate = mj_dt.Today()
        self.createdate = mj_dt.Today()
        self.FPN = False
        if self.comp.hdr == 'ers':
            FN = '%(f)s.%(d)s.%(e)s' %{'f':self.rawcomp.datafile,'d':self.comp.dat,'e':self.comp.hdr}
        else:
            if len(self.comp.hdr) > 0:
                FN = '%(f)s.%(e)s' %{'f':self.rawcomp.datafile,'e':self.comp.hdr}
            elif len(self.dat) > 0:
                FN = '%(f)s.%(e)s' %{'f':self.rawcomp.datafile,'e':self.comp.dat}
            elif len(self.comp.hdr) == 0 and len(self.comp.dat) == 0:
                #The data is in a folder, e.g. ArcVew raster format
                FN = self.datafile
            else:
                print self.datafile,self.dat,self.hdr
                sys.exit('FN error in ancillary')
        #For some reason os.path.join does nt work here
        FP = '%s/%s' %(self.comp.mainpath,self.rawcomp.datadir)
        #FP = os.path.join(ancilC.mainpath,self.datadir)  
        FPN = os.path.join(FP,FN)
        self.FPN = FPN
        #add the path except for volume and mai folder + to add to db
        dbFP = os.path.join(self.rawcomp.datadir,FN)
        dbFP = '../%(d)s' %{'d':dbFP}
        self.dbFP = dbFP
        if self.comp.hdr in ['zip']:
            self.zip = 'zip'
        elif self.comp.hdr in ['tar.gz','tar']:
            self.zip = 'tar.gz'
        else:
            self.zip = False 
            
    def UnZip(self):
        import zipfile
        zipFP,zipFN = os.path.split(self.FPN)
        tempFP = os.path.join(zipFP,'ziptmp')
        self.tempFP = tempFP
        if not os.path.isdir(tempFP):
            os.makedirs(tempFP)
        zipF = zipfile.ZipFile(self.FPN, "r")
        self.FPN = False
        #compstr is the filetype to look for in the zipfile

        compstr = '.%(e)s' %{'e':self.comp.dat}
        for fname in zipF.namelist():
            fname = os.path.basename(fname) 
            # skip directories
            if not fname:
                continue
            #get the fname components
            stem,ext = os.path.splitext(fname)
            fnameout = '%(s)s%(e)s' %{'s':stem, 'e':ext.lower()}
            #check if thsi file is of the data type expected
            if ext.lower() == compstr:
                if self.FPN: 
                    exitstr = 'EXITING - ancullary zip archice %(s)s contains multiple data files, you must unzip and give data filenames' %{'s':zipFN}
                    sys.exit(exitstr)
                else:
                    #Change hdr type
                    self.comp.hdr = self.comp.dat
                    self.FPN = os.path.join(tempFP,fnameout)
            # copy file (taken from zipfile's extract)
            source = zipF.open(fname)
            target = file(os.path.join(tempFP, fnameout), "wb")
            with source, target:
                shutil.copyfileobj(source, target)
                print 'shutil.copyfileobj',source, target
        if not self.FPN:
            sys.exit('Exiting, no supported file type found in the zip file')
        if not os.path.isfile(self.FPN):
            sys.exit('Something wrong with the unzipping of ancillary data')
      
    def UnTar(self):
        import tarfile
        if self.hdr == 'tar.gz':
            tarFPN = os.path.splitext(self.FPN)[0]
            tarFP,tarFN = os.path.split(tarFPN)
            if not os.path.isfile(tarFPN):
                cmd = 'cd %(d)s; gunzip -dk %(s)s' %{'d':tarFP, 's':os.path.split(self.FPN)[1]}
                os.system(cmd)
        else:
            tarFPN = self.FPN   
        tempFP = os.path.join(tarFP,'tartmp')
        self.tempFP = tempFP
        if not os.path.isdir(tempFP):
            os.makedirs(tempFP) 
        #compstr is the filetype to look for in the zipfile
        compstr = '.%(e)s' %{'e':self.dat}
        tarF = tarfile.TarFile(tarFPN, "r")
        self.FPN = False
        for fname in tarF.getnames():
            fname = os.path.basename(fname) 
            # skip directories
            if not fname:
                continue
            #get the fname components
            ext = os.path.splitext(fname)[1]
            #check if this file is of the data type expected
            if ext.lower() == compstr:
                if self.FPN: 
                    exitstr = 'EXITING - ancillary zip archice %(s)s contains multiple data files, you must unzip and give data filenames' %{'s':tarFN}
                    sys.exit(exitstr)
                else:
                    #Change hdr type
                    self.hdr = self.dat
                    self.FPN = os.path.join(tempFP,fname)
            tarF.extract(fname, tempFP)
        if self.zip == 'tar.gz':
            #remove the tar file
            os.remove(tarFPN)
        if not os.path.isfile(self.FPN):
            sys.exit('Someting wrong with the unzipping of ancillary data')

class AncillaryImport():
    def __init__(self, process, Lin, Lout, ancilDS):
        self.GDALhdrL = ['ers','envi','img','rst','e00'] 
        self.Lin = Lin
        self.Lout = Lout
        self.Lout.ancilid = self.Lin.ancilid
        self.ancilDS = ancilDS
        self.process = process
               
    def AncilImportIni(self):
        #strip the extension from adf (directory) (Arc/Info Binary Grid (.adf))
        if os.path.splitext(self.Lin.FPN)[1] == '.adf':
            self.Lin.FPN = os.path.splitext(self.Lin.FPN)[0]
        if not os.path.exists(self.Lin.FPN):
            exitstr = 'EXITING - the ancillary input file/folder %(f)s is missing' %{'f':self.Lin.FPN}
            sys.exit(exitstr)
        else:
            if self.Lin.zip:
                if self.Lin.zip == 'zip':
                    self.Lin.UnZip()
                elif self.Lin.zip == "tar.gz" :
                    self.Lin.UnTar()   
            self.ImportLayer()
            if self.Lout.comp.hdr == 'shp':
                self.Lout.GetVectorProjection()
            else:
                self.Lout.GetRastermetadata()
            if self.Lout.spatialRef.proj_cs == '':
                sys.exit('Output layer from Ancillary import has no projection')
        return True,'ok'
    
    def ImportLayer(self):   
        #start with metadata
        #check if there is an xml file 
        metaxml = '%(s)s.xml' %{'s':self.Lin.FPN}
        if os.path.isfile(metaxml):
            tarmetaxml =  '%(s)s.xml' %{'s':self.Lout.FPN}
            cmd = 'mv %(src)s %(tar)s' %{'src':metaxml, 'tar':tarmetaxml}
            os.system(cmd)
        #get any palette
        if self.Lin.comp.hdr == 'shp':
            pass
        else:
            if self.Lout.comp.palette.lower() in ['none','n','false','']:
                palette = False
            else:
                palette = ConnLayout.SelectPalette(self.Lout.comp.palette)
        #then find any registered metadata
        if self.Lin.comp.hdr == 'shp':
            #check if the shape file is projected:
            self.Lin.GetVectorProjection()
            gdalcmd = '/Library/Frameworks/GDAL.framework/Versions/1.11/Programs/ogr2ogr -skipfailures'
            if not self.Lin.spatialRef.epsg:
                #mj_proj = mj_gis.MjProj()
                #mj_proj.SetFromEPSG(int(self.ancilDS.epsg))
                
                gdalcmd = ' %(s1)s -a_srs EPSG:%(epsg)d' %{'s1':gdalcmd, 'epsg': int(self.ancilDS.epsg)}
                DOUBLETRANTS #First set SRS then transform
            else:
                if self.Lin.spatialRef.epsg == 4326:
                    pass
                else:
                    gdalcmd = ' %(s1)s -t_srs EPSG:4326 ' %{'s1':gdalcmd}
                    #gdalcmd = ' %(s1)s -t_srs %(srs)s ' %{'s1':gdalcmd, 'srs': self.Lin.spatialRef.proj_cs}
                
            gdalcmd = ' %(s1)s %(dst)s %(src)s' %{'s1':gdalcmd, 'dst': self.Lout.FPN, 'src':self.Lin.FPN}
            print gdalcmd
            os.system(gdalcmd)

        elif self.Lin.comp.hdr == 'e00' and self.Lout.comp.hdr == 'shp':
            #cmd = '/Applications/e00compr-1.0.1/e00conv /Volumes/mjtrans/ANCILRAW/GRID-arendal/global-wild/glowil00/wilderness.e00 /Volumes/mjtrans/ANCILRAW/GRID-arendal/global-wild/glowil00/temp00'
            gdalcmd = '/Library/Frameworks/GDAL.framework/Versions/1.11/Programs/ogr2ogr -skipfailures'
            gdalcmd = ' %(s1)s %(dst)s %(src)s' %{'s1':gdalcmd, 'dst': self.Lout.FPN, 'src':self.Lin.FPN}
            os.system(gdalcmd)
            
        elif self.Lin.comp.hdr.lower() == 'lis':
            '''This is a very special format, only applies to gghydro'''
            from ancillary_import_v70 import GGHtranslate
            GGHtranslate(self.Lin.FPN,self.Lout.FPN,self.Lout.comp.celltype,self.Lout.comp.cellnull,palette)
            
        elif self.Lin.comp.dat.lower() == '1x1':
            '''This is a very special format, only applies to stillwell'''
            from ancillary_import_v70 import StillwellTranslate
            StillwellTranslate(self.Lin.FPN,self.Lout.FPN,self.Lout.comp.celltype,self.Lout.comp.cellnull,palette)
            
        elif self.Lin.comp.dat.lower() == 'trmm':
            '''This is a very special format, only applies to TRMM data with north to the right'''
            from ancillary_import_v70 import TRMMTranslate
            TRMMTranslate(self.Lout.comp, self.Lin.FPN,self.Lout.FPN,palette)

        elif self.Lin.comp.hdr.lower() == self.Lout.comp.hdr.lower():
            gdalcmd = '/Library/Frameworks/GDAL.framework/Versions/1.11/Programs/gdalmanage copy '
            gdalcmd = ' %(s1)s %(src)s %(tar)s\n' %{'s1':gdalcmd, 'src':self.Lin.FPN, 'tar':self.Lout.FPN}
            os.system(gdalcmd)
            mj_gis.ReplaceRasterDS(self.Lout.FPN,palette=palette)
            #Set null and palette
            
        elif self.Lin.comp.hdr.lower() in self.GDALhdrL:  
            self.Lin.filetype = self.Lin.comp.hdr.lower()
            self.Lin.FPN = self.Lin.FPN
            self.Lin.GetRastermetadata()
            gdalcmd = '/Library/Frameworks/GDAL.framework/Versions/1.11/Programs/gdal_translate '
            if self.Lin.spatialRef.epsg == None:
                self.Lout.TGprojection(self.pileC.epsg)
                gdalcmd = '%(s1)s -a_srs %(srs)s' %{'s1':gdalcmd, 'srs':self.Lout.projection} 
            gdalcmd = '%(s1)s %(src)s %(tar)s' %{'s1':gdalcmd, 'src':self.Lin.FPN, 'tar':self.Lout.FPN}
           
            os.system(gdalcmd)
            mj_gis.ReplaceRasterDS(self.Lout.FPN,palette=palette)

        elif self.Lin.comp.hdr.lower() in ['hdr','.hdr'] and self.Lin.comp.dat.lower() in ['bil','.bil']:
            ancilBilFPN = self.Lin.FPN.replace('.hdr','.bil')
            self.Lin.filetype = 'bil'
            self.Lin.FPN = ancilBilFPN
            self.Lin.GetRastermetadata()
            gdalcmd = '/Library/Frameworks/GDAL.framework/Versions/1.11/Programs/gdal_translate '
            if self.Lin.spatialRef.epsg == None:
                self.Lout.TGprojection(self.Lin.pileC.epsg)
                gdalcmd = '%(s1)s -a_srs %(srs)s' %{'s1':gdalcmd, 'srs':self.Lout.projection}
            gdalcmd = '%(s1)s %(src)s %(tar)s' %{'s1':gdalcmd, 'src':ancilBilFPN, 'tar':self.Lout.FPN} 
            os.system(gdalcmd)
            mj_gis.ReplaceRasterDS(self.Lout.FPN,palette=palette)
        
        elif os.path.isdir(self.Lin.FPN):
            self.Lin.GetRastermetadata()
            '''Data in folder, arcview raster format'''
            gdalcmd = '/Library/Frameworks/GDAL.framework/Versions/1.11/Programs/gdal_translate '
            #TGTODO handel all projections better
            if self.Lin.spatialRef.epsg == None:
                gdalcmd = '%(s1)s -a_srs EPSG:%(epsg)d' %{'s1':gdalcmd, 'epsg':int(self.Lin.ancilDS.epsg)}
            gdalcmd = '%(s1)s %(src)s %(tar)s' %{'s1':gdalcmd, 'src':self.Lin.FPN, 'tar':self.Lout.FPN} 
            os.system(gdalcmd)
            mj_gis.ReplaceRasterDS(self.Lout.FPN,palette=palette)
        
        else:
            exitstr = 'unknown file type in ImportLayer',self.Lin.comp.hdr
            sys.exit(exitstr)         
        #Check projection, and add if needed
        if self.Lin.zip:
            self.RemoveTemporary()
        
    def ImportCsv(self):
        if self.Lin.comp.hdr.lower() in ['csv','.csv']:
            print 'importing text file with positions'
            #print self.Lin.FPN, self.Lout.FPN
            shutil.copy(self.Lin.FPN, self.Lout.FPN)
        elif self.Lin.comp.hdr.lower() in ['pos','.pos']:
            f1 = open(self.Lin.FPN, 'r')
            f2 = open(self.Lout.FPN, 'w')
            for line in f1:
                f2.write(line.replace(' ', ','))
            f1.close()
            f2.close()
            
    def RemoveTemporary(self):
        shutil.rmtree(self.Lin.tempFP)   

    def UpdateDB(self, delete = False, overwrite = False):
        if self.process.proj.system == 'specimen':
            system = 'specimen'
        else:
            system = 'ancillary'
        ConnAncillary.ManageAncilDS(system,self.Lin.ancilDS,delete,overwrite)
        ConnComp.InsertCompDef(system, self.Lout.comp)
        ConnAncillary.LinkDsCompid(system,self.Lin.ancilDS.dsid,self.Lout.comp.compid, delete, overwrite)
        ConnComp.InsertCompProd(system,system, self.Lout.comp)
        #ConnAncillary.ManageAncilComp(self,delete,overwrite)
        #ConnAncillary.ManageAncilCompProd(self.Lout,delete,overwrite)
        if self.Lout.comp.hdr not in ['shp','.shp','csv','.csv']:
            ConnAncillary.ManageAncillGeo(self.Lout,delete,overwrite)
        ConnComp.InsertLayer(system, self.Lout)
        #ConnAncillary.ManageAncilLayer(self.Lout,delete,overwrite) 
        #ConnAncillary.ManageAncilMeta(self.Lin,delete,overwrite)

class ProcessProcess:  
    """"class for processes defining other processes"""  
    def __init__(self, processC,processElement): 
        """"The constroctur requires an instance of the main process, and the xml elements in the tags used for defining the particular process to run"""  
        self.process =  processC
        if self.process.processid == 'addrootproc':
            ConnProcess.ManageRootProcess(self.process)
        elif self.process.processid == 'addsubproc':
            self.AddSubProc(processElement)
        else:
            exitstr = 'subprocess %s not defined in manageprocess' %(self.process.processid)
            sys.exit(exitstr)
            
    def AddSubProc(self,processElement):
        """Method for defining, updating or deleting subprocesses
        Only accessible to super user.
        """         
        print '    Adding subprocess %s' %(self.process.subprocid) 
        nodeTags = processElement.getElementsByTagName('node')
        nodeAttrL = ConnProcess.SelectProcessTagAttr(self.process.processid,'process','node')
        paramCDL = []
        compoutFlag = False
        for nodeTag in nodeTags:
            paramD = {}
            nodeD = {}      
            aD = XMLelement(nodeTag,nodeAttrL,'nodeTag',self.process.processid)[0]
            if aD['element'] == 'compout':
                compoutFlag = True
            #Get the parentidelement
            parentid = XMLelement(nodeTag,nodeAttrL,aD['element'],self.process.processid)[0]
            parentid = parentid['element']
            #Get the subelement
            tagAttrL = ConnProcess.SelectProcessTagAttr(self.process.processid,'node','parameter') 
            #Get the paramter tags
            paramTags = nodeTag.getElementsByTagName('parameter')    
            for paramTag in paramTags:
                attrParamD = XMLelement(paramTag,tagAttrL,aD['element'],self.process.processid)[0]
                if self.process.subprocid == 'metafileparams' and parentid == 'node':
                    #special solution to get the parentid to be node instead of parameter for metafileparams
                    paramC = Parameter(parentid, paramTag.nodeName, attrParamD)
                elif self.process.subprocid == 'metafileparams' and parentid != 'node' and aD['element'] == 'parameter':
                    paramC = Parameter(processElement.nodeName, 'node', attrParamD)
                else:
                    paramC = Parameter(processElement.nodeName, aD['element'], attrParamD)
                #Get any SetValues
                setValueTags = paramTag.getElementsByTagName('setvalue')
                setValueL = []
                for setValueTag in setValueTags:
                    setValueL.append([setValueTag.getAttribute('value'), setValueTag.getAttribute('label')])
                paramC.SetValues(setValueL)
                #Get any minmax values
                minMaxTags = paramTag.getElementsByTagName('minmax')
                minMaxL = []
                for minMaxTag in minMaxTags:
                    minMaxL.append([minMaxTag.getAttribute('min'), minMaxTag.getAttribute('max')])
                paramC.MinMax(minMaxL)
                #put the parameter in the node dictionary 
                paramD[paramC.paramid] = paramC
            nodeD[aD['element']] = paramD
            #paramCDL becomes a list of dicts with all parameters
            paramCDL.append(nodeD)
        #To register a process, all spatial input and output compositions must be available in the compdef table, except for original data     
        if compoutFlag and self.process.subprocid not in ['organizelandsat','explodelandsatscene','organizeancillary','MODISregion']:
            #Only if the target is a spatial layer
            if hasattr(self.process, 'tarpath') and self.process.tarpath.spatial:
                ConnProcess.ManageCompDefs(self, procAttrParamD['version'], paramCDL)
        ConnProcess.ManageSubProcess(self.process,paramCDL) 

class ProcessAncillary: 
    'class for all ancillary related processes'   
    def __init__(self, processC,pileD): 
        self.process =  processC
        self.ancilDS = AncilDataSet(pileD)
        if self.process.processid == 'download':
            self.DownloadAncillary()
        elif self.process.processid == 'organizeancillary':
            self.OrganizeAncillary()
        else:
            sys.exit('Ancillary process not understood')
            
    def Import(self,Lin,Lout,pileC):
        Lout.Exists()
        if Lin.comp.hdr in ['csv','.csv','pos','.pos']:
            self.ImportCsv(Lin,Lout,pileC)
        else:
            self.ImportLayer(Lin,Lout,pileC)
            
    def ImportCsv(self,Lin,Lout,pileC):
        printstr = '    Importing %(in)s as\n         %(out)s' %{'in':Lin.FPN, 'out': Lout.FPN}
        print printstr
        AncilImport = AncillaryImport(self.process,Lin,Lout,pileC)
        AncilImport.ImportCsv()
        '''
        result = AncilImport.AncilImportIni() 
        if not result[0]:
            sys.exit( result[1] )
        '''
        AncilImport.UpdateDB()
           
    def ImportLayer(self,Lin,Lout,pileC):
        AncilImport = AncillaryImport(self.process,Lin,Lout,pileC)
        if Lout.Exists():
            if Lout.comp.hdr == 'shp':  
                AncilImport.Lout.GetVectorProjection()
            else:
                AncilImport.Lout.GetRastermetadata()
            if self.process.delete:
                if Lout.comp.hdr != 'shp':
                    BALLE
                    pass
                else:
                    os.remove(AncilImport.Lout.FPN)
                AncilImport.UpdateDB(True,False)
            elif self.process.overwrite:
                printstr = '    Importing by overwriting %(in)s \n as %(out)s' %{'in':Lin.FPN, 'out': Lout.FPN}
                result = AncilImport.AncilImportIni()
                if not result[0]:
                    sys.exit( result[1] )
                AncilImport.UpdateDB(False,True)
            else:
                AncilImport.UpdateDB()
        else:
            printstr = '    Importing %(in)s as\n         %(out)s' %{'in':Lin.FPN, 'out': Lout.FPN}
            print printstr
            result = AncilImport.AncilImportIni() 
            print 'result',result
            if not result[0]:
                sys.exit( result[1] )

            AncilImport.UpdateDB()
            
    def FileNameDateExtract(self,compstr,fstr,findstr,replacestr):
        import fnmatch
        test = fnmatch.fnmatch(fstr,compstr)
        if test:
            d = 0
            dateStrL = []
            while True:
                pos = compstr.find(findstr,d)
                if pos < 0:
                    break
                datestr = fstr[pos:pos+len(replacestr)]
                if 'yyyy' in replacestr:
                    yyyypos = replacestr.find('yyyy')
                    yearStr = datestr[yyyypos:yyyypos+4]
                else:
                    noyear
                if 'mm' in replacestr:
                    mmpos = replacestr.find('mm')
                    mmStr = datestr[mmpos:mmpos+2]
                else:
                    nomonth
                if 'dd' in replacestr:
                    ddpos = replacestr.find('dd')
                    ddStr = datestr[ddpos:ddpos+2]
                else:
                    noday
                dateStr = '%(y)s%(m)s%(d)s' %{'y':yearStr,'m':mmStr,'d':ddStr}
                dateStrL.append(dateStr)
                d += 1
            return dateStrL
        else:
            return False
                      
    def OrganizeAncillary(self):
        #check that the region exists, otherwise it must first be created
        rec = ConnRegions.SelectRegion(self.ancilDS)
        if rec == None:
            exitstr ='Organizing ancillary or specimen data requires an existing region: %s does not exist' %(self.ancilDS.regionid)
            sys.exit(exitstr) 
        region = Location(self.ancilDS.regionid)
        region.Region(self.ancilDS.regionid)
        for key in self.process.rawinD:
            for datum in self.process.period.datumL:
                acqdate = AcqDate(datum)
                compout = self.process.compoutD[key]
                compout.SetPathParts(self.process.tarpath)
                compout.SetExt(compout.hdr)
                compout.CompFormat({'title':self.process.rawinD[key].title, 'label':self.process.rawinD[key].label,'version':self.ancilDS.version,'system':'ancillary'})
                Lout = RegionLayer(compout, region, acqdate)
                Lout.SetRegionPath()
                #create an empty composition for compin
                compin = Composition()
                #compin only required the path attribute
                compin.SetPathParts(self.process.srcpath)
                rawcomp =  AncilComposition(self.process.rawcompD[key]) 
                if len(self.process.replaceD) > 0: 
                    if self.process.replaceD['replacetype'] == 'copydatum':
                        for attr in self.process.replaceCompInAttrL:
                            self.StringReplace(attr, rawcomp, self.process.replacestr, datum['acqdatestr']) 
                        ancilD = rawcomp
                        Lin = AncillaryLayer(compin, ancilD, region, acqdate, self.ancilDS)
                        self.Import(Lin, Lout, self.ancilDS)
                    elif self.process.replaceD['replacetype'] == 'datum':
                        for attr in self.process.replaceCompInAttrL:
                            self.StringReplace(attr, rawcomp, self.process.replacestr, self.process.compinreplaceD[datum['acqdatestr']]) 
                        ancilD = rawcomp
                        Lin = AncillaryLayer(compin, ancilD, region, acqdate, self.ancilDS)
                        self.Import(Lin, Lout, self.ancilDS)     
                    elif self.process.replaceD['replacetype'] == 'dual':
                        for r in self.process.compinreplaceD: 
                            #reset the compositions
                            rawcomp =  AncilComposition(self.process.rawcompD[key])
                            Lout = RegionLayer(compout, region, acqdate)
                            Lout.SetRegionPath() 
                            for attr in self.process.replaceCompInAttrL:
                                self.StringReplace(attr, rawcomp, self.process.replacestr, self.process.compinreplaceD[r])
                                self.StringReplace(attr, Lout.comp, self.process.replacestr, self.process.compoutreplaceD[r])
                                ancilD = rawcomp
                            ancilD = rawcomp
                            Lin = AncillaryLayer(compin, ancilD, region, acqdate, self.ancilDS)                          
                            self.Import(Lin, Lout, self.ancilDS)
                    elif self.process.replaceD['replacetype'] == 'filename-date':
                        #Search for files in the source foolder
                        rawcomp =  AncilComposition(self.process.rawcompD[key])
                        rawcomp.SetPath(compin.mainpath)
                        files = [f for f in os.listdir(rawcomp.FP) if f.endswith(compin.hdr)]
                        templatename = rawcomp.datafile
                        compFN = '%s.%s' %(templatename,compin.hdr)
                        for f in files:
                            r = self.process.compinreplaceD.items()[0][0]
                            result = self.FileNameDateExtract(compFN,f,self.process.compinreplaceD[r],self.process.compoutreplaceD[r])
                            if not result:
                                print 'not',f
                                pass
                            else:
                                if len(result) == 0:
                                    balle
                                elif len(result) == 1 or result[0] == result[1]:   
                                    rawcomp.datafile = os.path.splitext(f)[0]       
                                    Lin = AncillaryLayer(compin, rawcomp, region, acqdate, self.ancilDS)         
                                    if os.path.isfile(Lin.FPN):  
                                        datum = {'acqdatestr':result[0], 'timestep':'varying'}
                                        #Rawcomp datafile can not be changed
                                        acqdate = AcqDate(datum)     
                                        #create output
                                        Lout = RegionLayer(compout, region, acqdate)                
                                        Lout.SetRegionPath()
                                        self.Import(Lin, Lout, self.ancilDS)
                                else:
                                    SNULLE
                    else:
                        GULLE
                else:
                    Lin = AncillaryLayer(compin, rawcomp, region, acqdate, self.ancilDS)
                    self.Import(Lin, Lout, self.ancilDS)
                    
    def StringReplace(self,strObj,compo,searchStr,replaceStr):
        if strObj == 'folder' and hasattr(compo, 'folder'):
            compo.folder = compo.folder.replace(searchStr,replaceStr,1)
        if strObj == 'band' and hasattr(compo, 'band'):
            compo.band = compo.band.replace(searchStr,replaceStr,1)
        if strObj == 'prefix' and hasattr(compo, 'prefix'):
            compo.prefix = compo.prefix.replace(searchStr,replaceStr,1)
        if strObj == 'suffix' and hasattr(compo, 'suffix'):
            compo.suffix = compo.suffix.replace(searchStr,replaceStr,1)
        if strObj == 'yyyydoy' and hasattr(compo, 'yyyydoy'):
            compo.yyyydoy = compo.yyyydoy.replace(searchStr,replaceStr,1)
        if strObj == 'datadir' and hasattr(compo, 'datadir'):
            compo.datadir = compo.datadir.replace(searchStr,replaceStr,1)
        if strObj == 'datafile' and hasattr(compo, 'datafile'):
            compo.datafile = compo.datafile.replace(searchStr,replaceStr,1)
        if strObj == 'metapath' and hasattr(compo, 'metapath'):
            compo.metapath = compo.metapath.replace(searchStr,replaceStr,1)
        if strObj == 'dataurl' and hasattr(compo, 'dataurl'):
            compo.dataurl = compo.dataurl.replace(searchStr,replaceStr,1)
        if strObj == 'metaurl' and hasattr(compo, 'metaurl'):
            compo.metaurl = compo.metaurl.replace(searchStr,replaceStr,1)
        if strObj == 'dataset' and hasattr(compo, 'dataset'):
            compo.dataset = compo.dataset.replace(searchStr,replaceStr,1)
        if strObj == 'title' and hasattr(compo, 'title'):
            compo.title = compo.title.replace(searchStr,replaceStr,1)
        if strObj == 'label' and hasattr(compo, 'label'):
            compo.label = compo.label.replace(searchStr,replaceStr,1)

class Process:
    """Main class for all processes
    everything the system is capable of is defined by processes """
    def __init__(self,rootprocessid, processid, version, overwrite, delete, upC, periodD, pathD): 
        """The constructor expects variables defining rootprocessid, processid, version, overwrite, delete and a user project.
            User project can be set to False, but then the number of processes that can be run is limited.
        """
        self.rootprocessid = rootprocessid
        self.processid = processid
        self.version = version
        self.overwrite = overwrite
        self.delete = delete
        self.proj = upC
        self.SetPeriod(periodD) 
        self.SetMainPaths(pathD)
  
    def XMLElement(self,processid,element,tag):
        """XMLelement is the method that reads the xml elements process elements to execute"""
        tagAttrL = ConnProcess.SelectProcessTagAttr(processid,'process',tag) 
        elements = element.getElementsByTagName(tag)
        if len(elements) == 0 and len(tagAttrL) > 0:
            exitStr = 'Error in XMLsoureTarget  <%s> missing in process %s, refine to add defaults' %(tag, processid)
            sys.exit(exitStr)
        elif len(elements) > 0:
            return XMLelement(elements[0],tagAttrL,tag,processid)
        else:
            return {},{}
        
    def SetPeriod(self,periodD):
        if not periodD:
            self.timestep = 'static'
        else:
            self.timestep = periodD['timestep']
        self.period = TimeSteps(self.timestep,periodD)
          
    def SetPaths(self,srcParamD,srctar): 
        """Sets the process path 
        The srcpath and tarpath are needed for all processes that use layers (data files).
        """ 
        if 'mainpath' in srcParamD:
            if not os.path.isdir(srcParamD['mainpath']):
                exitStr = 'EXITING: the path %s does not exists, for security it can not be created on the fly' %(srcParamD['mainpath'])
                sys.exit(exitStr)
        if srctar == 'src':       
            self.srcpath = SrcTarPath(srcParamD) 
        else:
            self.tarpath = SrcTarPath(srcParamD) 
         
    def SetMainPaths(self,pathD):
        self.roipath = pathD['roipath']
        self.ancilpathpath = pathD['ancilpath']
        self.userpath = pathD['userpath']
        self.landsatpath = pathD['landsatpath']
        self.modispath = pathD['modispath']
       
    def GetSetStandardEntries(self,processElement): 
        """ Reads the standard xml element entries for all processes, including scrpath, tarpath, srcperiod, tarperiod, compin and compout.
        The entries required for any particular processes is defined in db tables, and can be managed with the process 'subprocesses'.
        """
        #reads the xml and sets srcpath,tarpath,srcperiod,tarperiod, compin and comput, as applicable
        #srcpath
        tagAttrL = ConnProcess.SelectProcessTagAttr(self.processid,'process','srcpath')
        if len(tagAttrL) > 0:
            aD = self.XMLElement(self.processid,processElement, 'srcpath')[0]
            self.SetPaths(aD, 'src')   
        #tarpath
        tagAttrL = ConnProcess.SelectProcessTagAttr(self.processid,'process','tarpath')
        if len(tagAttrL) > 0:
            aD = self.XMLElement(self.processid, processElement, 'tarpath')[0]
            self.SetPaths(aD, 'tar')         
        #compIn
        compL = ConnProcess.SelectCompBands(self.processid,'process','compin')
        self.compinD = {}
        for x,comp in enumerate(compL):
            tagAttrL = ConnProcess.SelectProcessCompTagAttr(self.processid,'process','compin',comp[0])  
            CompInElements = processElement.getElementsByTagName('compin')

            if len(CompInElements) != len(compL):
                exitstr = 'Wrong number of compins (%s) does not correspond to db compins (%s) for process' %(len(CompInElements),len(compL))
                sys.exit(exitstr)
            aD = XMLelement(CompInElements[x],tagAttrL,'compin',self.processid)[0]
            self.AddComposition(aD,'in')
        #compOut    
        compL = ConnProcess.SelectCompBands(self.processid,'process','compout')
        self.compoutD = {}
        for x,comp in enumerate(compL):
            tagAttrL = ConnProcess.SelectProcessCompTagAttr(self.processid,'process','compout',comp[0]) 
            compoutElements = processElement.getElementsByTagName('compout')
            if len(compoutElements) != len(compL):
                if self.processid != 'organizeancillary':
                    exitstr = 'Wrong number of compouts does not correspond to db compouts for process: %s' %(self.processid)
                    sys.exit(exitstr)
            aD = XMLelement(compoutElements[x],tagAttrL,'compout',self.processid)[0]
            self.AddComposition(aD,'out')
        #comp - for processes that do not produce layers
        compL = ConnProcess.SelectCompBands(self.processid,'process','comp')
        self.compD = {}
        for x,comp in enumerate(compL):
            tagAttrL = ConnProcess.SelectProcessCompTagAttr(self.processid,'process','comp',comp[0]) 
            compElements = processElement.getElementsByTagName('comp')
            if len(compElements) != len(compL):
                    exitstr = 'Wrong number of comps does not correspond to db comps for process: %s' %(self.processid)
                    sys.exit(exitstr)
            aD = XMLelement(compElements[x],tagAttrL,'comp',self.processid)[0]
            self.AddComposition(aD,'comp')
          
    def SetProcessParams(self,procAttrParamD, tagAttrParamD):
        for key, value in procAttrParamD.items():
            setattr(self, key, value)
            print '    setting process param',key,value
        for key, value in tagAttrParamD.items():
            setattr(self, key, value)
            print '    setting process param',key,value
                    
    def AddComposition(self, aD,io):
        """Adds the compositions related to processes to dictionaries.
        The dictionaries are used for defining the composition of the actual layers
        """
        if io == 'in':
            if str(aD['band'].lower()) in self.compinD:
                sys.exit('Conflicting band name in compin')
            elif '*' in self.compinD:
                sys.exit('You can not use a wildcare plus named bands in compin')
            elif aD['band'] == '*' and len(self.compinD) > 0:
                sys.exit('You can not use a wildcare plus named bands in compin')
            #self.compinD[aD['band']] = Composition(aD)
            if not 'prefix' in aD: aD['prefix'] = aD['band']
            if not 'masked' in aD:
                aD['masked'] = 'Y'

            self.compinD[aD['band']] = Composition(aD['source'], aD['product'], aD['folder'], aD['band'], aD['prefix'],aD['suffix'], masked = aD['masked'])
            #Copy the path to the composition, not all comppins have a path - i..e if a db entry
            if hasattr(self, 'srcpath'):
                self.compinD[aD['band']].SetPathParts(self.srcpath)
        elif io == 'out':
            if str(aD['band'].lower()) in self.compoutD:
                exitstr = 'Conflicting band %s name in compout' %(aD['band'])
                sys.exit(exitstr)
            elif '*' in self.compoutD:
                sys.exit('You can not use a wildcare plus named bands in compout')
            elif aD['band'] == '*' and len(self.compoutD) > 0:
                sys.exit('You can not use a wildcare plus named bands in compout')

            if not 'prefix' in aD: aD['prefix'] = aD['band']
            self.compoutD[aD['band']] = Composition(aD['source'], aD['product'], aD['folder'], aD['band'], aD['prefix'],aD['suffix'])
            #Copy the path to the composition
            self.compoutD[aD['band']].SetPathParts(self.tarpath)
            #Set the output format AFTER the path to also check that file type is correct in path
            #if self.tarpath.spatial:
            self.compoutD[aD['band']].CompFormat(aD) 
        else:
            if str(aD['band'].lower()) in self.compD:
                exitstr = 'Conflicting band %s name in comp' %(aD['band'])
                sys.exit(exitstr)
            elif '*' in self.compD:
                sys.exit('You can not use a wildcare plus named bands in comp')
            elif aD['band'] == '*' and len(self.compD) > 0:
                sys.exit('You can not use a wildcare plus named bands in comp')

            if not 'prefix' in aD: aD['prefix'] = aD['band']
            self.compD[aD['band']] = Composition(aD['source'], aD['product'], self.proj.regionid, aD['band'], aD['prefix'],aD['suffix'])
            #Set the output format AFTER the path to also check that file type is correct in path
            #if self.tarpath.spatial:
            self.compD[aD['band']].CompFormat(aD)
   
    def GetAncillaryImportEntries(self,processElement,procAttrParamD):
        self.compoutD = {}
        self.rawcompD = {}
        self.rawinD = {}
        self.replaceD = {}
        compAttrL = ConnProcess.SelectProcessCompTagAttr(self.processid,'process','compout','False') 
        rawAttrL = ConnProcess.SelectProcessCompTagAttr(self.processid,'process','rawin','False')
        compoutElements = processElement.getElementsByTagName('compout')
        rawinElements = processElement.getElementsByTagName('rawin')
        if len(rawinElements) == 0: 
            print 'No rawin element - required'
            BALLE
        for x, element in enumerate(compoutElements):
            aD = XMLelement(element,compAttrL,'compout',self.processid)[0]
            rD = XMLelement(rawinElements[x],rawAttrL,'rawin',self.processid)[0] 
            self.AddComposition(aD,'out')
            self.AddRawIn(aD['band'],rD)  
            self.rawcompD[aD['band']] = rD


        if len(procAttrParamD['replacetag']) > 0:
            #Get the replacetag
            self.replacestr = procAttrParamD['replacestr']
            replacetag = procAttrParamD['replacetag']
            replaceElement = processElement.getElementsByTagName(replacetag)
            self.replaceD['replacetype'] = replaceElement[0].getAttribute("type")
            self.ReadReplace(replaceElement[0])  
            
    def AddRawIn(self,band,rD):
        self.rawinD[band] = AncilComposition(rD)
        self.rawinD[band].SetPathParts(self.srcpath)
        
    def ReadReplace(self,node):
        keyL = []; compinL = []; compoutL = []
        replaces = node.getElementsByTagName('replace')
        for replace in replaces:
            keyL.append(replace.getAttribute('key'))
            compinL.append(replace.getAttribute('compinreplace'))
            compoutL.append(replace.getAttribute('compoutreplace'))
        self.compinreplaceD = dict(zip(keyL, compinL))
        self.compoutreplaceD = dict(zip(keyL, compoutL))    
        self.replaceCompInAttrL = []
        self.strCutL = []
        attribs = node.getElementsByTagName('compinattribute')
        for attrib in attribs:
            self.replaceCompInAttrL.append(attrib.firstChild.nodeValue)
            strBegin = attrib.getAttribute('begin')
            if len(strBegin) == 0:
                self.strCutL.append( [False,False] )
            else:
                strEnd = attrib.getAttribute('end')
                self.strCutL.append( [int(strBegin),int(strEnd)] )
        self.replaceCompOutAttrL = []
        attribs = node.getElementsByTagName('compoutattribute')
        for attrib in attribs:
            self.replaceCompOutAttrL.append(attrib.firstChild.nodeValue)
  
class ProcessProject:
    '''class for all project management'''  
    def __init__(self, process):
        self.process = process
        #direct to subprocess
        if self.process.processid == 'createproj':
            ConnRegions.InsertProjTract(self.process,ConnUserLocale)
        elif self.process.processid == 'manageproj':
            ConnUserLocale.ManageProj(aD,tD)
        else:
            exitstr = 'No process %s under ProcessProject' %(self.process.processid)
            sys.exit(exitstr) 
            
class RegionCommon:
    '''class common for all regional dataset management (not layerprocesses)''' 
    def __init__(self, process):   
        self.process =  process
        
    def CreateRegionsLayer(self, comp, path, regionid, acqdate, roi = False):
        comp.SetPathParts(path)
        comp.SetExt(path.hdr)
        region = Location('region')
        region.Region(regionid)
        if roi:
            layer = ROI(comp,region,acqdate)
        else:
            layer = RegionLayer(comp,region,acqdate)
        layer.SetRegionPath()
        return region, layer
                        
class ProcessRegion(RegionCommon):
    '''class for all region management'''  
    def __init__(self, process):
        RegionCommon.__init__(self, process)
        #direct to subprocess
        if self.process.processid == 'regioncategories':
            self.InsertRegionCat()
        elif self.process.processid == 'defaultregion':
            self.DefaultRegion()
        elif self.process.processid == 'managetract':
            ConnUserLocale.ManageTract(self.process)
        elif self.process.processid == 'userregionfromcoord':   
            ConnUserLocale.UserRegionFromCoord(self.process)
            if self.process.system.lower() == 'modis':
                ConnMODIS.FIX()
        elif self.process.processid == 'defaultregionfromvector':
            self.DefaultRegFromVec()
        elif self.process.processid == 'createsite':
            ConnUserLocale.ManageUserSite(self.process)
        elif self.process.processid == 'linkregionswrs':
            if self.process.proj.projectid == "karttur" and self.process.proj.system == 'system': 
                self.LinkAllRegionsToWRS()
            else:
                sys.exit('Only superuser can link wrs to regions')
        elif self.process.processid == 'linkregionsmodtiles':
            if self.process.proj.projectid == "karttur" and self.process.proj.system == 'system': 
                self.LinkAllRegionsToMODIS('MODIS')
            else:
                sys.exit('Only superuser can link wrs to regions')
        else:
            exitstr = 'No process %s under Processregion' %(self.process.processid)
            sys.exit(exitstr)
        
    def InsertRegionCat(self): 
        region = Location('region')
        pp = self.process.params
        region.Region(False, pp.regioncat, parentcat=pp.parentcat, title=pp.title,label=pp.label, stratum=pp.stratum)
        ConnRegions.InsertRegionCat(self.process, region)
        
    def DefaultRegion(self):
        pp = self.process.params
        acqdate = AcqDate(self.process.period.datumL[0])
        keycomp = self.process.compoutD.items()[0][0]
        #create the comp
        comp = self.process.compoutD[keycomp]
        #Set the comp format - hardcoded for ROI
        comp.CompFormat({'measure':'N','cellnull':0,'celltype':'vector','scalefac':1,'offsetadd':0,'dataunit':'NA','system':'defreg','masked':'N'})
        #create the region and the layer
        region,roiLayer = self.CreateRegionsLayer(comp, self.process.tarpath, pp.regionid, acqdate, roi = True)
        #reset the region - TGTODO this is redundant and should be fixed with kwargs
        region.Region(pp.regionid, pp.regioncat, parentcat=pp.parentcat, regionname=pp.regionname, parentid=pp.parentid, version=pp.version,stratum=pp.stratum,title=pp.title, label=pp.label, masked='U')
        region.region.SetBounds(epsg,pp.minlon,pp.minlat,pp.maxlon,pp.maxlat)
        #Get the fields to write to datasets
        fieldDD = self.SetfieldD( region.regionid, region.regionname, region.regioncat, region.stratum, region.parentid, region.parentcat)
        roiLayer.CreateAttributeDef(fieldDD)
        #set projection
        projection = mj_gis.MjProj()
        projection.SetFromEPSG(epsg)
        if not roiLayer.Exists() or self.process.overwrite: #or overwrite
            mj_gis.CreateESRIPolygonPtL(roiLayer.FPN, roiLayer.fieldDefL, region.BoundsPtL, projection.proj_cs, region.regionid)
        #Get the bounds in the original projection
        boundsD = mj_gis.GetFeatureBounds(roiLayer.FPN,'REGIONID')
        #Set lonlat projection
        lonlatproj = mj_gis.MjProj()
        lonlatproj.SetFromEPSG(4326)
        #Get the corners in lonlat
        llD = mj_gis.ReprojectBounds(region.BoundsPtL,projection.proj_cs,lonlatproj.proj_cs)
        ConnRegions.InsertDefRegion('regions',roiLayer, boundsD[ regionid ],epsg,llD )
          
    def DefaultRegFromVec(self):
        pp = self.process.params
        acqdate = AcqDate(self.process.period.datumL[0])
        inkey = self.process.compinD.items()[0][0]
        outkey = self.process.compoutD.items()[0][0]
        #Get the input layer
        layer = ConnComp.SelectSingleLayerComposition(self.process.compinD[inkey], self.process.proj.system,acqdate.acqdatestr,acqdate.timestep)
        if layer == None:
            print 'layer',layer
            SLUT

        compid, source,product,folder,band,prefix,suffix,acqdatestr,masked,regionid = layer
        comp = Composition(source,product,folder,band,prefix,suffix, division='region')
        region, layerIn = CreateRegionsLayer(self, comp, self.process.srcpath, regionid, acqdate, roi = True)

        if not os.path.isfile(layerIn.FPN):
            print layerIn.FPN
            FLASKA
        fieldL = [pp.idcol, pp.namecol, pp.categorycol, pp.parentidcol, pp.parentcatcol, pp.stratumcol,pp.titlecol,pp.labelcol]
        fieldD = mj_gis.GetFeatureAttributeList(layerIn.FPN, fieldL, pp.idcol)
        if not fieldD:
            sys.exit('error in DefaultRegFromVec')
        else: 
            for key in fieldD:
                fieldDD = self.SetfieldD( str(fieldD[key][aD['idcol']]), str(fieldD[key][aD['namecol']]), str(fieldD[key][aD['categorycol']]), int(fieldD[key][aD['stratumcol']]), str(fieldD[key][aD['parentidcol']]),str(fieldD[key][aD['parentcatcol']]) )
                c = self.process.compoutD[outkey]
                #TGTODO better inherit self.process.compoutD[outkey], now it is reset
                compOut = Composition(c.source, c.product, c.folder, c.band, c.band, c.suffix, division='region')
                formatD = {'measure':'N','product':product,'suffix':suffix,'cellnull':0,'celltype':'vector','dataunit':'NA','system':'defreg','masked':'U'}
                compOut.CompFormat(formatD)
                roiRegion, roiLayer = CreateRegionsLayer(self, comp, self.process.tarpath, regionid, acqdate, roi = True)
                
                regionid, regioncat, parentid, name, parentcat = fieldD[key][pp.idcol],fieldD[key][pp.categorycol],fieldD[key][pp.parentidcol],fieldD[key][pp.namecol],fieldD[key][pp.parentcatcol]
                #reset the regionout SEE ABVOVE
                roiRegion.Region(pp.regionid, pp.regioncat, regionname=name, parentid=parentid, parentcat=parentcat, title=fieldD[key][pp.titlecol], label=fieldD[key][pp.labelcol],stratum=fieldD[key][pp.stratumcol])

                roiLayer.CreateAttributeDef(fieldDD)
                fieldname = pp.idcol
                valueLL = [[fieldD[key][pp.idcol]]]
                if not roiLayer.Exists() or self.process.overwrite: #or overwrite
                    mj_gis.ExtractFeaturesToNewDS(layerIn.FPN,roiLayer.FPN,fieldname,valueLL,roiLayer.fieldDefL)
                fieldname = 'REGIONID'
                #Get the epsg and bounds
                boundsD = mj_gis.GetFeatureBounds(roiLayer.FPN,fieldname) 
                if len(boundsD) != 1:
                    exitstr = 'Default regions must consist on only one (1) feature (polygon of multipolygon): %s' %(roiLayer.FPN)
                    sys.exit(exitstr)
                projection = mj_gis.GetVectorProjection(roiLayer.FPN)
                k = boundsD.keys()[0]
                region.SetBounds(projection.epsg,boundsD[k][0], boundsD[k][1], boundsD[k][2], boundsD[k][3])                    
                #Set lonlat projection
                lonlatproj = mj_gis.MjProj()
                lonlatproj.SetFromEPSG(4326)
                #Get the corners in lonlat
                llD = mj_gis.ReprojectBounds(region.BoundsPtL,projection.proj_cs,lonlatproj.proj_cs)
                #Add the defaultregion to the DB
                ConnRegions.InsertDefRegion('regions',roiLayer, boundsD[ fieldD[key][aD['idcol']] ],aD['epsg'], llD )
     
    def SetfieldD(self,regionid,regionname,regioncat,stratum,parentid,parentcat):
        #TGTODO SHOULD BE FROM DB
        fieldDD = {}
        fieldDD['REGIONID'] = {'name':'REGIONID', 'type':'string','width':32,'precision':0,'transfer':'constant','source':regionid }
        fieldDD['NAME'] = {'name':'NAME', 'type':'string','width':64,'precision':0,'transfer':'constant','source':regionname }
        fieldDD['CATEGORY'] = {'name':'CATEGORY', 'type':'string','width':32,'precision':0,'transfer':'constant','source':regioncat }
        fieldDD['STRATUM'] = {'name':'STRATUM', 'type':'integer','width':4,'precision':0,'transfer':'constant','source':stratum }
        fieldDD['PARENTID'] = {'name':'PARENTID', 'type':'string','width':32,'precision':0,'transfer':'constant','source':parentid }
        fieldDD['PARENTCAT'] = {'name':'PARENTCAT', 'type':'string','width':32,'precision':0,'transfer':'constant','source':parentcat }
        return fieldDD
    
    def LinkAllRegionsToWRS(self):
        self.wrs = self.process.wrs
        datum = self.process.period.datumL[0]
        key = self.process.compinD.items()[0][0]            
        layer = ConnAncillary.SelectSingleLayerComposition(self.process.compinD[key],self.process,datum['acqdatestr'],datum['timestep'])
        if layer == None:
            exitstr = 'EXITING, the wrs polygons can not be found in the db' ,self.process.compinD[key],self.process,datum['acqdatestr'],datum['timestep']                      
        source,product,folder,band,prefix,suffix,acqdatestr,regionid = layer[1:9]
        self.CreateRegionsLayer(self,source,product,folder,band,prefix,suffix,regionid,datum)
        if not os.path.isfile(self.layerIn.FPN):
            exitstr = 'Can not find wrs file: %s' %(self.layerIn.FPN)
            sys.exit(exitstr)
        #set the link class and the wrs poly file
        linkwrs = mj_gis.LinkRegionsToWRS(layerIn.FPN)
        recs = ConnRegions.SelectAllRegoinsWrs()
        for rec in recs:
            if rec[2].upper() == 'D':
                comp = ConnRegions.SelectRegionCompFromIdCat(rec[0],rec[1])
                if not len(comp) == 1:
                    print '    duplicates for',rec[0],rec[1]
                    for c in comp:
                        print '        ',c
                    continue
                source, product, folder, band, prefix, suffix, acqdatestr, regionid, regioncat, stratum = comp[0]
                datum = {'acqdatestr': acqdatestr, 'timestep': 'dummy'}
                parentcatid = ConnRegions.SelectParentRegion(regioncat,regionid)
                if parentcatid == None:
                    exitstr = 'No parent found for region %s' %(regionid)
                #parentid, parentcat = parentcatid
                parentid = parentcatid[0]
                mainpath = os.path.split(self.process.srcpath.mainpath)[0]
                csvFP = os.path.join(mainpath,'temp')
                if not os.path.exists(csvFP):
                    os.makedirs(csvFP)
                csvFPN = os.path.join(csvFP,'wrstemp.csv')
                mainpath = os.path.join(mainpath,'ROI')
                ALSOINSUBROUTINE
                comp = Composition(source,product,folder,band,prefix,suffix, division = 'region',mainpath = mainpath)
                comp.SetExt('shp')
                region = Location('region')
                #regionD = {'regionid':regionid,'regioncat':regioncat,'parentid':parentid}
                region.Region(regionid,regioncat, parentid=parentid)
                regionLayer = ROILayer(comp, region, datum)
                regionLayer.SetRegionPath() 
                if os.path.isfile(regionLayer.FPN):
                    print '        extracting wrs coverage for %s' %(regionLayer.FN)
                    #wrsLD = mj_gis.LinkRegionsToWRS(regionLayer.FPN, layerIn.FPN, 0.005)
                    #wrsLD = linkwrs.OverlayRegion(regionLayer.FPN, 0.005)
                    if stratum < 5:
                        #For subcontinental to global the smallest items are approximately 5 km
                        wrsLD = linkwrs.OverlayRegion(regionLayer.FPN, 0.05)
                    else:
                        #For countires and smaller the smallest items are approximately 0.5 km
                        wrsLD = linkwrs.OverlayRegion(regionLayer.FPN, 0.0005)
                    if not wrsLD:
                        continue
                    if len(wrsLD) == 0:  
                        #if not wrs scene location is found (small island regions) rerun with full resolution     
                        wrsLD = linkwrs.OverlayRegion(regionLayer.FPN, False)
                        #wrsLD = mj_gis.LinkRegionsToWRS(regionLayer.FPN, layerIn.FPN, False)                           
                    ConnRegions.InsertBULKRegionWRS(csvFPN,wrsLD,regionid,'D',aD['wrs'])
                else:
                    exitstr = 'default region layer missing: %s' %(regionLayer.FPN)
                    sys.exit(exitstr)
                    
    def LinkAllRegionsToMODIS(self,satsys):
        #self.wrs = aD['wrs']
        datum = self.process.period.datumL[0]
        key = self.process.compinD.items()[0][0]  
        #layer = ConnComp.SelectSingleLayerComposition(self.process.compinD[key], self.process.proj.system, acqdate.acqdatestr,acqdate.timestep)
          
        layer = ConnComp.SelectSingleLayerComposition(self.process.compinD[key],'ancillary',datum['acqdatestr'],datum['timestep'])
        print 'layer',layer
        if layer == None:
            exitstr = 'EXITING, the wrs polygons can not be found in the db' ,self.process,datum['acqdatestr'],datum['timestep']                      
            print exitstr
            STOP
        source,product,folder,band,prefix,suffix,acqdatestr,regionid = layer[1:9]
        comp = Composition(source,product,folder,band,prefix,suffix)

        acqdate = AcqDate(datum)
        region, layerIn = self.CreateRegionsLayer(comp, self.process.srcpath, self.process.proj.regionid, acqdate)
        
        
        #self.CreateRegionsLayer(self,source,product,folder,band,prefix,suffix,regionid,datum)
        if not os.path.isfile(layerIn.FPN):
            exitstr = 'Can not find polygon file: %s' %(layerIn.FPN)
            sys.exit(exitstr)
        
        if satsys == 'MODIS': 
            recs = ConnRegions.SelectAllRegoinsMODIS()
        elif satsys == 'landsat':
            #linkwrs = mj_gis.LinkRegionsToWRS(layerIn.FPN)
            recs = ConnRegions.SelectAllRegoinsWrs()
        #set the link class and the wrs poly file
        linkwrs = mj_gis.LinkRegions(layerIn.FPN,'htile','vtile')

        for rec in recs:
            if rec[2].upper() == 'D':
                print 'rec',rec
                comp = ConnRegions.SelectRegionCompFromIdCat(rec[0],rec[1])
                if not len(comp) == 1:
                    print '    duplicates for',rec[0],rec[1]
                    for c in comp:
                        print '        ',c
                    continue
                source, product, folder, band, prefix, suffix, acqdatestr, regionid, regioncat, stratum = comp[0]
                datum = AcqDate({'acqdatestr': acqdatestr, 'timestep': 'dummy'})
                
                parentcatid = ConnRegions.SelectParentRegion(regioncat,regionid)
                if parentcatid == None:
                    exitstr = 'No parent found for region %s' %(regionid)
                #parentid, parentcat = parentcatid
                parentid = parentcatid[0]
                mainpath = os.path.split(self.process.srcpath.mainpath)[0]
                csvFP = os.path.join(mainpath,'temp')
                if not os.path.exists(csvFP):
                    os.makedirs(csvFP)
                csvFPN = os.path.join(csvFP,'wrstemp.csv')
                mainpath = os.path.join(mainpath,'ROI')
                comp = Composition(source,product,folder,band,prefix,suffix, division = 'region',mainpath = mainpath)
                comp.SetExt('shp')
                region = Location('region')
                #regionD = {'regionid':regionid,'regioncat':regioncat,'parentid':parentid}
                region.Region(regionid,regioncat, parentid=parentid)
                #acqdate
                regionLayer = ROILayer(comp, region, datum)
                regionLayer.SetRegionPath() 
                if os.path.isfile(regionLayer.FPN):
                    print '        extracting wrs coverage for %s' %(regionLayer.FN)
                    #wrsLD = mj_gis.LinkRegionsToWRS(regionLayer.FPN, layerIn.FPN, 0.005)
                    #wrsLD = linkwrs.OverlayRegion(regionLayer.FPN, 0.005)
                    if stratum < 5:
                        #For subcontinental to global the smallest items are approximately 5 km
                        wrsLD = linkwrs.OverlayRegion(regionLayer.FPN, 0.05)
                    else:
                        #For countires and smaller the smallest items are approximately 0.5 km
                        wrsLD = linkwrs.OverlayRegion(regionLayer.FPN, 0.0005)
                    if not wrsLD:
                        continue
                    if len(wrsLD) == 0: 
                         
                        #if not wrs scene location is found (small island regions) rerun with full resolution     
                        wrsLD = linkwrs.OverlayRegion(regionLayer.FPN, False)
                        #wrsLD = mj_gis.LinkRegionsToWRS(regionLayer.FPN, layerIn.FPN, False)
                    print regionid, wrsLD 
                    if satsys == 'MODIS':
                        ConnRegions.InsertBULKRegionMODIS(csvFPN,wrsLD,regionid,'D')  
                    else:
                        MINGAL                        
                        ConnRegions.InsertBULKRegionWRS(csvFPN,wrsLD,regionid,'D',aD['wrs'])
                else:
                    exitstr = 'default region layer missing: %s' %(regionLayer.FPN)
                    sys.exit(exitstr)

class ProcessSqlDumps():
    'class for all Landsat specific processes'   
    def __init__(self, processC,aD):
        self.process = processC
        #direct to subprocess
        if self.process.processid == 'copysqldump':          
            #self.CopySqlDump(aD)
            ConnSqlDump.CopyTableData(self.process, aD['schema'], aD['table'], aD['datum'])
        elif self.process.processid == 'exportsqldump':
            ConnSqlDump.DumpTableData( self.process, aD['schema'], aD['table'])
        elif self.process.processid == 'dbdump':
            ConnSqlDump.DumpCompleteDB(self.process)
        elif self.process.processid == 'dbcopy':
            ConnSqlDump.CopyCompleteDB(self.process, aD)
        else:
            exitstr = 'Unrecognized process in ProcessSqlDumps: %s' %(self.process.processid)
            sys.exit(exitstr)
            
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
                    LOut.SetLayerPathOld()
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
                  
class ProcessMODIS():
    'class for all MODIS specific processes'   
    def __init__(self, processC,processElement):
        self.process = processC
        #direct to subprocess
        if self.process.processid == 'searchDataPool':
            self.SearchDataPool(processElement)
        elif self.process.processid == 'loadDataPool':
            self.LoadDataPool(processElement)
        elif self.process.processid == 'downloadDataPool':
            self.DownLoadDataPool()
        elif self.process.processid == 'explodemodisscene':
            self.ExplodeMODISScene()
        elif self.process.processid == 'checkmodisscenes':
            self.CheckMODISScenes()
        elif self.process.processid == 'checkMODISbands':
            self.CheckMODISbands(processElement)
            self.RefreshDBBands()
            self.self.RefreshDBTiles()
        elif self.process.processid == 'MODISregion':
            self.MODISregion()
        elif self.process.processid == 'MODIStileCoords':
            self.TileCoords()
        else:
            exitstr = 'Unrecognized MODIS process %s' %(self.process.processid)
            sys.exit(exitstr) 
            
    def TileCoords(self):
        SINproj = mj_gis.MjProj()
        SINproj.SetFromProj4('+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m +no_defs')
        LatLonproj = mj_gis.MjProj()
        LatLonproj.SetFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs +towgs84=0,0,0')
        ptL = []
        for lon in range(360):
            ptL.append((lon-180,90))
        for lat in range(180):
            ptL.append((180,-1*(lat-90)))
        for lon in range(360):
            ptL.append((-1*(lon-180),-90))
        for lat in range(180):
            ptL.append((-180,lat-90))
        #worldgeom = mj_gis.ShapelyPoygon('polygon',ptL) 
        worldgeom = mj_gis.ShapelyPolyGeom(ptL)
        worldgeom.ShapelyToOgrGeom()
        worldgeom.GeoTransform(LatLonproj,SINproj)
        worldgeom.OgrGeomToShapely()
        tarShpFP =  '/Users/thomasg/temp/global'
        if not os.path.exists(tarShpFP):
            os.makedirs(tarShpFP)
        tarShpFPN = '/Users/thomasg/temp/global/earthSIN.shp'
        fieldDefD = {'type':'string','transfer':'constant','source':'globe','width':8}
        fieldDefL = [mj_gis.FieldDef('name',fieldDefD)]
        mj_gis.CreateESRIPolygonGeom(tarShpFPN, fieldDefL, worldgeom, SINproj.proj_cs, 'globe')
        #create a region with all tiles
        tlen = 20015109.3539999984204769
        tlen /= 18
        regioncat = 'globe'
        regionid = 'globe'
        for h in range(36):
            minx = tlen*(18-36)+h*tlen
            maxx = minx+tlen
            for v in range(18):
                maxy = tlen*(9-18)+(18-v)*tlen
                miny = maxy-tlen
                ptL = [(minx,maxy),(maxx,miny),(maxx,maxy),(minx,miny)]
                #TGTODO MOVE TO mj_gis
                tilegeom = mj_gis.ShapelyMultiPointGeom(ptL)
                tilegeom.ShapelyToOgrGeom()
                tilegeom.GeoTransform(SINproj,LatLonproj)
                tilegeom.OgrGeomToShapely()
                coordL = []
                for point in [ptgeom for ptgeom in tilegeom.shapelyGeom]:
                    coordL.extend([list(point.coords)[0][0],list(point.coords)[0][1]])
                ullon, ullat, lrlon, lrlat, urlon, urlat, lllon, lllat = coordL    
                tilepoly = mj_gis.ShapelyPolyGeom([(minx, maxy), (maxx, maxy), (maxx, miny), (minx,miny)])
                #Test if this tile is inside the globe
                if tilepoly.shapelyGeom.intersects(worldgeom.shapelyGeom): 
                    if h < 10:
                        htile = 'h0%s' %(h)
                    else:
                        htile = 'h%s' %(h)
                    if v < 10:
                        vtile = 'v0%s' %(v)
                    else:
                        vtile = 'v%s' %(v)
                    hvtile = '%s%s' %(htile,vtile) 
                    ConnMODIS.InsertModisTileCoord(self.process,hvtile,h,v,minx,maxy,maxx,miny,ullat,ullon,lrlon,lrlat,urlon,urlat,lllon,lllat)
                    ConnMODIS.InsertModisRegionTile(self.process,regionid,regioncat,'D',h,v,hvtile) #'D' for default
         
    def LoadDataPool(self,processElement): 
        '''Load dotapool holdings to local db
            Does not utilize the layer class but take parameters directly from xml
        '''
        prodPath ='%s.%s' %(self.process.product, self.process.version)
        localPath = os.path.join(self.process.srcpath.mainpath,prodPath) 
        self.process.period.SetAcqDate()
        for date in self.process.period.datumL:
            print '    Loading',self.process.product, self.process.version, date['acqdate']
            dateStr = mj_dt.DateToStrPointDate(date['acqdate'])         
            localFPN = os.path.join(localPath,dateStr)
            tarFPN = os.path.join(localPath,'done',dateStr)
            if not os.path.exists(os.path.split(tarFPN)[0]):
                os.makedirs(os.path.split(tarFPN)[0])
            print 'localFPN',localFPN
            if os.path.exists(localFPN):     
                self.ReadMODIShtml(localFPN,tarFPN,date['acqdate'])
            else:
                print 'MODIS bulk flie missing', localFPN
                
    def ReadMODIShtml(self,FPN,tarFPN,acqdate):
        tmpFPN,headL = mj_html.ParseModisWgetHTML(FPN)
        ConnMODIS.LoadBulkTiles(self.process,acqdate,tmpFPN,headL)
        #move the done file to a subdir called done
        shutil.move(FPN,tarFPN)
      
    def SetSceneFromHDF(self,hdf):
        source,acqdatedoy,p,r,version,tileid,ext = Support.DisentangleMODIShdf(f)
        print source,acqdatedoy,p,r,version,tileid,ext
        acqdate = mj_dt.yyyydoyDate(acqdatedoy)
        acqdatestr = mj_dt.DateToStrDate(acqdate)
        acqdate = AcqDate({'acqdatestr':acqdatestr, 'timestep':self.process.period.timestep}, acqdate = acqdate,acqdatedoy=acqdatedoy)
        comp = Composition(product=product, folder=folder)
        comp.SetExt(ext)
        comp.SetPathParts(self.process.srcpath)
        location = Location('MODISscene')
        location.MODISScene(p, r)
        layer = MODISScene(comp, location, acqdate)
        layer.SetVersionTileId(version)
        '''       
        query = {'tileid':layer.id, 'tilefilename':f,'source':source,'product':product,
                 'version':version,'acqdate':layer.acqdate.acqdate, 'doy':layer.acqdate.doy, 'folder':folder, 'htile':layer.location.path,'vtile':layer.location.row}
        self.InsertMODIStile(query)
        '''

    def SetMODISLayer(self,compL,pathparts,h,v,acqdate,compFormat=False):
        comp = Composition(compL[0],compL[1],compL[2],compL[3],compL[4],compL[5]) 
        comp.SetExt(pathparts.hdr)
        comp.SetPathParts(pathparts)
        if compFormat:
            comp.CompFormat(compFormat)
        acqdatestr = mj_dt.DateToStrDate(acqdate)
        acqdatedoy = mj_dt.DateToYYYYDOY(acqdate)
        acqdate = AcqDate({'acqdatestr':acqdatestr, 'timestep':self.process.period.timestep}, acqdate = acqdate, acqdatedoy=acqdatedoy)
        location = Location('MODIStile')
        location.MODISScene(h,v)
        layer = MODISLayer(comp, location, acqdate)
        layer.SetLayerPath()
        return layer
        
    def SetMODISScene(self, tilefn, folder, dirpath):
        product,acqdatedoy,p,r,version,tileid,ext = Support.DisentangleMODIShdf(tilefn)
        source = '%(p)sv%(v)s' %{'p':product, 'v':version}
        acqdate = mj_dt.yyyydoyDate(acqdatedoy)
        acqdatestr = mj_dt.DateToStrDate(acqdate)
        acqdate = AcqDate({'acqdatestr':acqdatestr, 'timestep':self.process.period.timestep}, acqdate = acqdate, acqdatedoy=acqdatedoy)
        comp = Composition(source=source, product=product, folder=folder)
        comp.SetExt(ext)
        comp.SetPathParts(dirpath)
        location = Location('MODISscene')
        location.MODISScene(p, r)
        layer = MODISScene(comp, location, acqdate)
        layer.SetVersionTileId(version)
        layer.FN = tilefn
        layer.SetScenePath()  
        query = {'tileid':layer.id, 'tilefilename':tilefn,'source':source,'product':product,
                 'version':version,'acqdate':layer.acqdate.acqdate, 'doy':layer.acqdate.doy, 'folder':folder, 'htile':layer.location.path,'vtile':layer.location.row}
        return layer,query
    
    def CheckMODISScenes(self):
        #Loop over the source folder to get all MDOIS tiles 
        ext = '.%s' %(self.process.srcpath.hdr)
        key = self.process.compinD.keys()[0]
        dirpath = self.process.srcpath 
        localPath = os.path.join(self.process.srcpath.mainpath,self.process.compinD[key].product,self.process.srcpath.division,self.process.compinD[key].folder)   
        for subdir, dirs, files in os.walk(localPath):
            for f in files:
                if os.path.splitext(f)[1] == ext:
                    print 'checking', f
                    mainpath, product, division, folder, p, r, acqdateDOY = Support.DisentangleScenePath(subdir)                 
                    layer,query = self.SetMODISScene(f, folder,  dirpath)
                    '''             
                    acqdate = mj_dt.yyyydoyDate(acqdateDOY)
                    acqdatestr = mj_dt.DateToStrDate(acqdate)
                    acqdate = AcqDate({'acqdatestr':acqdatestr, 'timestep':self.process.period.timestep}, acqdate = acqdate,acqdatedoy=acqdatedoy)
                    comp = Composition(product=product, folder=folder)
                    comp.SetExt(ext)
                    comp.SetPathParts(self.process.srcpath)
                    location = Location('MODISscene')
                    location.MODISScene(p, r)
                    layer = MODISScene(comp, location, acqdate)
                    layer.SetVersionTileId(version)
                           
                    query = {'tileid':layer.id, 'tilefilename':f,'source':source,'product':product,
                             'version':version,'acqdate':layer.acqdate.acqdate, 'doy':layer.acqdate.doy, 'folder':folder, 'htile':layer.location.path,'vtile':layer.location.row}
                    '''

                    self.InsertMODIStile(query)
 
    def InsertMODIStile(self,query): 
        ConnMODIS.InsertMODIStile(query)
        ConnMODIS.UpdateTileStatusOnId(query['tileid'],'downloaded','Y') 
                
    def CheckMODISbands(self,processElement,locationL):
        #Set the parameters   
        '''
        self.redundant = procAttrParamD['redundant']
        self.checkdownload = procAttrParamD['download']
        self.checkorganized = procAttrParamD['organized']
        self.checkextract = procAttrParamD['extract']
        '''
        #Set the key to the only compin
        key = self.process.compinD.keys()[0]
        #get the source and the version
        source = self.process.compinD[key].source
        version = source[len(source)-3:len(source)] 
        product = self.process.compinD[key].product
        #Set the status to look for
        status = SceneTileStatus(redundant = self.redundant)
        #Get the layers associated with the source/product that is being checked
        modLayerL = psycopg2modis.SelectTemplateLayersOnSource(self.process.compinD[key].source)  
        BALLE
        #modLayerL: source, product, folder, band, prefix, suffix, fileext, timestep
        for location in locationL:
            #Get the dates associated with this location, product, source and timestep
            locationDates = psycopg2modis.SelectLocationProductDates(self,key,location)
            for datum in locationDates:
                layerDatum = LayerDate(datum[0])
 
                #Create a tile instance  
                tileC = MODISTile(self.process.compinD[key],location,layerDatum)
                tileC.SetStatus(status)
                tileC.SetVersionTileId(version)
                #Get the data on this tile from the modistiles table
                rec = psycopg2modis.SelectSingleTileOnId(tileC)

                tileid, tilefilename, source, product, path, row, acqdate, version, folder, downloaded, organized, exploded, deleted = rec
                #TGTODO check version, folder and product
                #Add tilefilename and set path to tilefile
                tileC.SetTileFN(tilefilename)
                tileC.SetTileFPN()
                
                #check db consistency
                if organized == 'Y' and downloaded == 'N':
                    warnstr = 'WARNING %s)\n     indicated as organized but not downloaded' %(tileid)
                    print warnstr
                if exploded == 'Y' and organized == 'N':
                    warnstr = 'WARNING %s\n     indicated as extracted but not organized' %(tileid)
                    print warnstr
                #Check if downloaded and organized
                if downloaded == organized == 'Y' and deleted == 'N':
                    if not os.path.isfile(tileC.FPN):
                        warnstr = '%s\n     indicated as organized but does not exist in its place' %(tileC.FPN)
                        print warnstr
                #Check if deleted
                if deleted == 'Y':
                    if os.path.isfile(tileC.FPN):
                        warnstr = '%s\n     indicated as deleted but exists in its place' %(tileC.FPN)
                        print warnstr

                #check if the file exists
                if os.path.isfile(tileC.FPN):
                    if downloaded == 'N':
                        psycopg2modis.UpdateTileStatus(tileC,'downloaded','Y') 
                    if organized == 'N':
                        psycopg2modis.UpdateTileStatus(tileC,'organized','Y')
                elif not os.path.isfile(tileC.FPN) and downloaded == 'Y':
                    psycopg2modis.UpdateTileStatus(tileC,'downloaded','N') 

                #Get the bands for this tile
                outLayers = psycopg2modis.SelectTileBandsOnId(tileC)
                
                #Set the key to the only compout
                key = self.process.compoutD.keys()[0]
                #get the source and the version
                source = self.process.compoutD[key].source
                version = source[len(source)-3:len(source)]

                explodeFlag = True
                for outLayer in outLayers:
                    #outLayer: folder, band, prefix, suffix, defaultext, status
                    comp = Composition({'source':source,'product':product, 'folder':outLayer[0], 'band':outLayer[1],'prefix':outLayer[2], 'suffix':outLayer[3]}) 
                    comp.SetExt(outLayer[4])
                    comp.SetPathParts(self.process.tarpath)

                    #create an instance of ModisLayer
                    L = MODISLayer(comp,location,layerDatum)
                    #Set version and generate tileid
                    L.SetVersionTileId(version)
                    #Create the path to the layer file
                    L.SetLayerPath()
                    #check if the file exists
                    if os.path.isfile(L.FPN) and outLayer[5] != 'E':
                        psycopg2modis.UpdateBandStatus(L,'E') 
                    elif not os.path.isfile(L.FPN) and outLayer[5] == 'E':
                        psycopg2modis.UpdateBandStatus(L.id,L.comp.band,'N') 
                        explodeFlag = False
                    #Get template
                    template = psycopg2modis.SelectTemplateLayerOnSourceBand(L)
                    if template == None:
                        exitstr = 'No template for MODIS %s %s' %(L.comp.source,L.comp.band)
                        sys.exit(exitstr)
                    source, product, folder, band, prefix, suffix, fileext, celltype, dataunit, compid,hdffolder,hdfgrid,timestep,scalefactor,offsetadd,cellnull = template
                    compdef = ConnProcess.SelectCompDef(self.process.proj.system,compid)
                    #thiscomp = [folder, band, scalefactor, offsetadd, dataunit]
                    if compdef == None:
                        ConnProcess.InsertCompDef(compid, 1.0, folder, band, prefix, timestep, self.process.proj.system)
                    compprod = ConnProcess.SelectCompProd(self.process.proj.system,compid, product, suffix)
                    #thiscomp = [folder, band, scalefactor, offsetadd, dataunit]
                    if compprod == None:
                        ConnProcess.InsertCompProd(compid, source, product, suffix, celltype, cellnull, self.process.proj.system)
                if explodeFlag and exploded == 'N' and len(outLayers) == len(modLayerL):
                    psycopg2modis.UpdateTileStatus(tileC,'exploded','Y')
                elif len(outLayers) < len(modLayerL) or not explodeFlag:
                    psycopg2modis.UpdateTileStatus(tileC,'exploded','N')          

    def DownLoadDataPool(self):
        #Get the tiles
        print self.process.proj.defregid
        tiles = ConnMODIS.SelectTilesToDownload(self.process)
        folder = 'original'
        ext = '.hdf'
        dirpath = self.process.tarpath
        dlL = [] #downloadList
        proddir = False
        for tile in tiles:
            source,product,version,h,v,hvtile,acqdate,tilefn = tile
            layer,query = self.SetMODISScene(tilefn, folder,  dirpath)
            #print 'query',query
            if layer.Exists():
                print 'exists'
            else:
                #Only get the dates that where set in the xml file (i.e. 8D or 16D)
                if acqdate in self.process.period.processDateL:
                    #print 'acqdate',acqdate
                    proddir = '%(p)s.%(v)s' %{'p':product,'v':version}
                    datedir = mj_dt.DateToStrPointDate(acqdate)
                    dlL.append({'datedir':datedir,'fn':tilefn,'localFPN':layer.FPN,'query':query})
        if proddir:            
            mj_html.AccessMODIS(dlL,proddir,ConnMODIS)
        
    def ExplodeHDF(self, hdfFPN, explodeD):
        #import time  
        nrExploded = 0 
        for band in explodeD:
            tarFPN = explodeD[band]['layer'].FPN
            hdffolder = explodeD[band]['layerhdf']['hdffolder']
            hdfgrid = explodeD[band]['layerhdf']['hdfgrid']
            #copy the file to memory and extract the hdf straight from memory? 
            cmd = '/Library/Frameworks/GDAL.framework/Versions/1.11/Programs/gdal_translate '
            cmd = '%(cmd)s HDF4_EOS:EOS_GRID:"%(hdf)s":%(folder)s:%(band)s %(tar)s' %{'cmd':cmd,'hdf':hdfFPN,'folder':hdffolder,'band':hdfgrid, 'tar':tarFPN}
            os.system(cmd)
            #register band
            if os.path.isfile(tarFPN):
                nrExploded += 1
                explodeD[band]['layer'].RegisterLayer(self.process.proj.system)
        return nrExploded
                  
    def ExplodeMODISScene(self):       
        key = self.process.compinD.keys()[0]
        print 'key', key
        #Get the layers associated with the source/product that is being checked
        modLayerL = ConnMODIS.SelectTemplateLayersOnSource(self.process.compinD[key].source)
        compD = {}; layerHdfD = {}; compFormatD ={}
        for layer in modLayerL:
            source, product, folder, band, prefix, suffix, celltype, dataunit, cellnull, scalefac, offsetadd, measure, palette, hdffolder, hdfgrid = layer
            #compD[band] = {'source':source,'product':product, 'folder':folder, 'band':band,'prefix':prefix, 'suffix':suffix}
            compD[band] = [source,product,folder,band,prefix,suffix]
            compFormatD[band] = {'cellnull':cellnull,'celltype':celltype,
                              'scalefac':scalefac,'offsetadd':offsetadd,
                              'dataunit':dataunit,'measure':measure,
                              'palette':palette}
            
            layerHdfD[band] = {'hdffolder':hdffolder, 'hdfgrid':hdfgrid}
        #Get the bands to explode
        statusD = {'downloaded':'Y','exploded':'N'}
        tiles = ConnMODIS.SelectTiles(self.process,self.process.compinD[key].source,statusD)
        statusD['regionid'] = 'id'
        tiles = ConnMODIS.SelectLocationTiles(self.process,self.process.compinD[key].source,statusD)
        #TGTDODO SSET ACTUAL DATE WITH PANDAS
        pathparts = self.process.tarpath
        for tile in tiles:
            tileid, tilefn, source, product, folder, htile, vtile, acqdate = tile
            hdffile = self.SetMODISScene(tilefn, folder, self.process.srcpath)[0]
            if os.path.isfile(hdffile.FPN):
                nrExploded = 0
                explodeD = {}
                for band in compD:   
                    layer = self.SetMODISLayer(compD[band],pathparts,htile,vtile,acqdate,compFormatD[band])

                    if not layer.Exists() or self.process.overwrite:
                        explodeD[band] = {'layer':layer,'layerhdf':layerHdfD[band]}
                    elif layer.Exists():
                        #explodeD[band] = {'layer':layer,'layerhdf':layerHdfD[band]}
                        nrExploded += 1   
                    #comp = {'source':source,'product':product, 'folder':folder, 'band':band,'prefix':prefix, 'suffix':suffix}
                nrExploded += self.ExplodeHDF(hdffile.FPN,explodeD)
                if nrExploded == len(compD):
                    ConnMODIS.UpdateTileStatusOnId(tileid,'organized','Y')
                    ConnMODIS.UpdateTileStatusOnId(tileid,'exploded','Y')

class ProcessUser:
    'class for processing users'   
    def __init__(self, processC,processElement):
        self.process = processC
        if self.process.processid == 'manageuser':
            ConnUserLocale.ManageUsers(processC)
 
class ProcessSpecimen(RegionCommon):      
    'class for all ancillary related processes'   
    def __init__(self, process, processElement): 
        #def __init__(self, process):
        RegionCommon.__init__(self, process)
        

        if self.process.processid == 'download':
            self.DownloadSpeciment()
        elif self.process.processid == 'specimentodb':
            self.SpecimenToDB(aD)
        elif self.process.processid == 'linkplotwrs':
            self.LinkPlotToWRS(aD)
        elif self.process.processid == 'noheadercsvtodb':
            self.NoHeaderCsvToDb(processElement)
        elif self.process.processid == 'specimentolayer':
            self.SpecimenToLayer()
        elif self.process.processid == 'specimensoillinePVIPBI':
            self.SpecimenSoilLinePVIPBI()
        elif self.process.processid == 'specimensoil':
            self.SpecimenSoil()
        elif self.process.processid == 'plotsoilline':
            self.PlotSoilline(processElement)
        elif self.process.processid == 'extractplotsrfi':
            self.ExtractPlotSRFI()
        else:
            exitstr = 'Specimen process not understood: %s' %(self.process.processid)
            sys.exit(exitstr)
            
    def SpecimenToDB(self,aD):
        import specimen_import_v70 as specimen_import
        #Set the file path
        acqdate = AcqDate(self.process.period.datumL[0])
        key = self.process.compinD.items()[0][0]
        layer = ConnComp.SelectSingleLayerComposition(self.process.compinD[key], self.process.proj.system, acqdate.acqdatestr,acqdate.timestep)
        if layer == None:
            BALLE                
        compid, source, product, folder, band, prefix, suffix, acqdatestr, masked, regionid = layer
        compC = Composition(source,product,folder,band,prefix,suffix)
        region, layerIn = CreateRegionsLayer(self, comp, self.process.srcpath, regionid, acqdate, roi = False)
        if not os.path.isfile(layerIn.FPN):
            exitstr = 'Can not find wrs file: %s' %(layerIn.FPN)
            sys.exit(exitstr)
        if not self.process.proj.siteid:
            sys.exit('Organizing specimen data requires that a siteid is given')
        dsid = ConnSpecimen.SelectDS(compid)
        if dsid == None:
            BALLE
        dsplotid = dsid[0]
        paramDL = specimen_import.OrganizeSpecimenStack(self.process.proj.projectid,layerIn.FPN,dsplotid,self.process.proj.siteid,self.process.proj.userid)
        ConnSpecimen.ManagePlotData(self.process,paramDL)

    def LinkPlotToWRS(self):
        self.wrs = self.process.params.wrs
        acqdate = AcqDate(self.process.period.datumL[0])
        key = self.process.compinD.items()[0][0]
        layer = ConnComp.SelectSingleLayerComposition(self.process.compinD[key],'ancillary',acqdate.acqdatestr,acqdate.timestep)
        compid, source, product, folder, band, prefix, suffix, acqdatestr, masked, regionid = layer
        compC = Composition(source,product,folder,band,prefix,suffix)
        region, layerIn = CreateRegionsLayer(self, comp, self.process.srcpath, regionid, acqdate, roi = False)
        if not os.path.isfile(layerIn.FPN):
            exitstr = 'Can not find wrs file: %s' %(layerIn.FPN)
            sys.exit(exitstr)
        #Get the plotpoints
        #TGTODO just select plots that are not linked unless overwrite
        plotrecs = ConnSpecimen.SelectPlotsNoWRS(self.process)
        if len(plotrecs) > 0:
            #Get the wrs positions for the default region
            wrsrecs = ConnRegions.SelectRegionWrs(self.process.proj.defregid, self.wrs)
            if len(wrsrecs) == 0:
                BALLE
            linkwrs = mj_gis.LinkRegionsToWRS(layerIn.FPN,wrsrecs)
            linkD = linkwrs.LinkPtToPoly(plotrecs) 
            ConnSpecimen.ManagePlotWrs(self.process, self.wrs, linkD)
        
    def NoHeaderCsvToDb(self,aD,processElement):
        import csv
        #Get the links from the xml file
        tagAttrL = ConnProcess.SelectProcessTagAttr(self.process.processid,'process','link')        
        nodes = processElement.getElementsByTagName('link')
        linkDL = []
        for node in nodes:
            pD = XMLelement(node,tagAttrL,'parameters',self.process.processid)[0]
            linkDL.append(pD)
        #Get the csv file
        for key in self.process.compinD:
            recs = ConnComp.SelectAllLayerComps('specimen',self.process.compinD[key])
            for rec in recs:          
                compid, source, product, folder, band, prefix, suffix, acqdatestr, regionid = rec
                compC = Composition(source,product,folder,band,prefix,suffix)
                region, layerIn = CreateRegionsLayer(self, comp, self.process.srcpath, regionid, acqdate, roi = False)

                if not os.path.isfile(LayerIn.FPN):
                    BALLE
                else:
                    dataDL = []
                    with open(LayerIn.FPN) as f:
                        print 'f',f
                        reader = csv.reader(f)
                        for row in reader:
                            allOK = True
                            #create a dict, always use compid that is used in all specimen data
                            dataD = {'compid':compid}
                            for linkD in linkDL:                                
                                if len(row[linkD['csvcolumn']]) > len(linkD['csvnodata']):
                                    nodata = row[linkD['csvcolumn']][0:len(linkD['csvnodata'])]
                                if linkD['csvaltcolumn'] > 0:
                                    if len( row[ linkD['csvaltcolumn'] ] ) > len( linkD['csvaltnodata'] ):
                                        altnodata = row[linkD['csvaltcolumn']][0:len(linkD['csvaltnodata'])] 
                                if nodata != linkD['csvnodata']:
                                    dataD[linkD['dbcolumn']] = self.FormatColumnData( linkD['dbcolumn'], row[linkD['csvcolumn']], linkD['format'] )                                                                 
                                elif linkD['csvaltcolumn'] > 0 and altnodata != linkD['csvaltnodata']:
                                    dataD[linkD['dbcolumn']] = self.FormatColumnData( linkD['dbcolumn'], row[linkD['csvaltcolumn']], linkD['format'])           
                                else:
                                    allOK = False
                            if allOK:
                                if not 'siteid' in dataD:
                                    if self.process.proj.siteid in ['','*']:
                                        exitstr = 'EXITING to enter plot data you must give an existing site'
                                        sys.exit(exitstr)

                                    dataD['siteid'] = self.process.proj.siteid
                                dataDL.append(dataD)
                    if len(dataDL) > 0:
                        if aD['schema'] == 'topography':
                            ConnTopo.ManageTopoData(self.process,dataDL,pp.table)
                        else:
                            DONOTKNOWWHY
                    for row in dataDL:
                        print row
                        break
        
    def FormatColumnData(self, dbcol, col, formatt):
        if formatt == '':
            return col
        elif dbcol == 'acqdate':
            if formatt == '20000101T000000':
                #format == seconds since 20000101T000000
                acqdate = mj_dt.DateTimeFromStartDate(2000, 1, 1, 0, 0, 0, int(col.split('.')[0]))[0]
                return mj_dt.DateToStrDate(acqdate)
            else:
                BULLE
        elif dbcol == 'acqtime':
            if formatt == '20000101T000000':
                return mj_dt.DateTimeFromStartDate(2000, 1, 1, 0, 0, 0, int(col.split('.')[0]))[1]
            else:
                print 'dbcol',dbcol
                print 'formatt',formatt
                SNULLE           
        else:
            print dbcol, col, formatt
            GULLE
               
    def SpecimenToLayer(self):
        startdate = self.process.period.datumL[0]['startdate']
        enddate = self.process.period.datumL[0]['enddate']
        #get the points
        bounds = False
        key = self.process.compinD.items()[0][0]
        compid =  self.process.compinD[key].compid
        ptL, headerL,tabFormat = ConnSpecimen.SelectSpecimenLonLat(self.process.params.theme, self.process, compid, startdate, enddate, bounds)
        #Set the target file
        datespan = '%s-%s' %(mj_dt.DateToStrDate(startdate), mj_dt.DateToStrDate(enddate))
        acqdate = AcqDate({'acqdatestr':datespan, 'timestep':'datespan'})
        key = self.process.compoutD.items()[0][0]
        #compC = Composition(source,product,folder,band,prefix,suffix)
        region, layerOut = CreateRegionsLayer(self, self.process.compoutD[key], self.process.srcpath, self.process.proj.defregid, acqdate, roi = False)

        if not os.path.exists(layerOut.FP):
            os.makedirs(layerOut.FP)
        mj_gis.SpecimenToLayer(layerOut.FPN, ptL, headerL, tabFormat, self.process.params.append, self.process.params.inregion)
               
    def SpecimenSoil(self):
        from soilline_v70 import SpecimenProximitySoil
        mainpath = self.process.compinD['pvi'].mainpath
        tempFP = os.path.join(mainpath,'temporaryfiles')
        metod = self.process.params.slmethod
        if not os.path.exists(tempFP):
            os.makedirs(tempFP)
        radius = aD['radius']
        plots = self.GetPlots()
        dateD = {'startdate':self.process.period.startdate,'enddate':self.process.period.enddate}
        for plot in plots:
            if self.process.proj.system.lower() == 'landsat':
                #scenes = self.GetLandsatScenes(plot[0])
                whereD = {}
                plotD = {'plotid':plot[0]}
                scenes = self.SelectLandsatScenes(whereD,plotD,dateD)
                for scene in scenes:
                    print 'scene',scene
                    self.SetPlotScene(scene)
                    #GET THE position of the point in the band
                    spatialRef,srcLayer = mj_gis.GetRasterMetaData(self.layerInD['rl'].FPN)
                    #point latlon
                    lon,lat = plot[1:3]
                    lin,col = mj_gis.LatLonPtToRasterLinCol((lon,lat),spatialRef.proj_cs,srcLayer.gt)
                    lin,col = int(round(lin)),int(round(col))
                    for key in self.layerInD:
                        if not os.path.isfile(self.layerInD[key].FPN):
                            KALLE
                        tarFN = '%(band)s.tif' %{'band':key}
                        tarFPN = os.path.join(tempFP,tarFN)
                        if os.path.isfile(tarFPN):
                            os.remove(tarFPN)
                        cellx,celly = mj_GDAL.GDALtranslatecutFromPt(self.layerInD[key].FPN,tarFPN,lin,col,srcLayer.lins,srcLayer.cols,radius)
                        #reset the filepath to the cut raster image
                        self.layerInD[key].FPN = tarFPN
                        self.layerInD[key].ReadRasterLayer(flatten = False)
                        self.layerInD[key].lins, self.layerInD[key].cols, self.layerInD[key].projection, self.layerInD[key].geotrans, self.layerInD[key].ext, self.layerInD[key].cellsize, self.layerInD[key].celltype, self.layerInD[key].cellnull, self.layerInD[key].epsg, self.layerInD[key].epsgunit = mj_gis.GetRasterInfo(self.layerInD[key].FPN)
                    #Set path to the soil line definition file
                    if aD['soilline'] == 'plot': 
                        bounds = plot[0]
                        NOTYET
                    elif aD['soilline'] == 'scene':
                        bounds = 'wholescene'
                        comp = self.layerInD['rl'].comp
                        band = prefix = '%(metod)s-%(folder)s-soilline' %{'metod':metod, 'folder':comp.folder}
                        csvsuffix = '%(suf)s-%(plot)s-scene' %{'suf':comp.suffix, 'plot':plot[0]}
                        compin = Composition(comp.source,comp.product,'endmember',band,prefix,comp.suffix, mainpath = mainpath, scenes = True, division = 'scenes')
                        #compin.SetExt('xml')
                    else:
                        bounds = 'global'
                        NOTYET
                    band = prefix = '%(metod)s-%(folder)s-soilspectra' %{'metod':metod, 'folder':comp.folder}
                    compout = Composition(comp.source, comp.product,'endmember', band, prefix, csvsuffix, mainpath = mainpath, scenes = True, division = 'plots')                      
                    compin.SetExt('xml') 
                    compout.SetExt('xml') 
                    if self.process.proj.system == 'landsat':
                        layerout = LandsatLayer(compout,self.location,self.acqdate)
                        layerout.SetLayerPathOld()
                        layerin = LandsatLayer(compin,self.location,self.acqdate)
                        layerin.SetLayerPathOld()
                    if os.path.isfile(layerout.FPN) and not self.process.overwrite:
                        continue 

                    if not os.path.isfile(layerin.FPN):
                        continue
                    
                    #ptLinCol = (cellx,celly)
                    soillineD = SpecimenProximitySoil(self.layerInD,layerin.FPN,layerout.FPN,aD['radius'],aD['maxsoillinestderr'],cellx,celly)

                    #TGOTODO change db to have additional key for bounds for soilsearch and redo tables
                    '''
                    if soilD:
                        ConnEndMember.InsertSearch('soilsearch',sceneD,soilD, self.process.overwrite,self.process.delete)
                    if vegD:
                        ConnEndMember.InsertSearch('vegsearch',sceneD,vegD, self.process.overwrite,self.process.delete)
                    '''

    def GetBands(self, processElement):
        self.bandL = []
        bandTags = processElement.getElementsByTagName('band')
        tagAttrL = ConnProcess.SelectProcessTagAttr(self.process.processid,'process','band') 
        for bandTag in bandTags:
            band = XMLelement(bandTag,tagAttrL,'band',self.process.processid)[0]
            self.bandL.append(band['bandid'])
            
    def PlotSoilline(self,processElement): 
        from soilline_v70 import SoillinePlotCSV
        key = self.process.compinD.keys()[0]
        mainpath = self.process.compinD[key].mainpath
        plots = self.GetPlots()
        self.GetBands(processElement)
        for plot in plots:
            if self.process.proj.system.lower() == 'landsat':
                scenes = self.GetLandsatScenes(plot[0])
                for scene in scenes:
                    self.SetPlotScene(scene)
                    if aD['soilline'] == 'plot': 
                        bounds = plot[0]
                        NOTYET
                        soillineComp = False
                    elif aD['soilline'] == 'scene':
                        bounds = 'wholescene'
                        comp = self.layerInD['rl'].comp
                        band = prefix = '%(metod)s-%(folder)s-soilline' %{'metod':self.process.params.metod, 'folder':comp.folder}
                        #csvsuffix = '%(suf)s-%(plot)s-scene' %{'suf':comp.suffix, 'plot':plot[0]}
                        slComp = Composition(comp.source,comp.product,'endmember',band,prefix,comp.suffix, mainpath = mainpath, scenes = True, division = 'scenes')
                        slLayersOutD = {}
                        alldone = True
                        for b in self.bandL:
                            band = prefix = '%(b)s-%(metod)s-%(folder)s-slplot' %{'b':b,'metod':self.process.params.metod, 'folder':comp.folder}
                            slCompCSV = Composition(comp.source,comp.product,'endmember',band,prefix,comp.suffix, mainpath = mainpath, scenes = True, division = 'scenes')
                            slCompCSV.SetExt('csv')
                            L = LandsatLayer(slCompCSV,self.location,self.acqdate)
                            L.SetLayerPathOld()
                            slLayersOutD[b] = L.FPN 
                            if not os.path.isfile(L.FPN):
                                alldone = False                       
                    else:
                        bounds = 'global'
                        NOTYET
                        soillineComp = False
                    slComp.SetExt('xml')
                    slxmlLayer = LandsatLayer(slComp,self.location,self.acqdate)
                    slxmlLayer.SetLayerPathOld()
                    if not os.path.isfile(slxmlLayer.FPN):
                        continue

                    if aD['candidates']:
                        if aD['soilline'] == 'plot': 
                            bounds = plot[0]
                            NOTYET
                            soillineComp = False
                        elif aD['soilline'] == 'scene':
                            candcomp = slComp
                            candcomp.SetExt('csv')
                            L = LandsatLayer(candcomp,self.location,self.acqdate)
                            L.SetLayerPathOld()
                            candxmlLayer = L.FPN
                            if not os.path.isfile(candxmlLayer):
                                SHOULDNOTBE
                            candLayersOutD = {}
                            for b in self.bandL:
                                candLayersOutD[b] = slLayersOutD[b].replace('slplot','candplot')
                                if not os.path.isfile(candLayersOutD[b]):
                                    alldone = False
                    else:
                        candxmlLayer = candLayersOutD = False

                    if self.process.params.specimensoil:
                        if self.process.params.soilline == 'plot': 
                            bounds = plot[0]
                            NOTYET
                            soillineComp = False
                        elif self.process.params.soilline == 'scene':
                            band = prefix = '%(metod)s-%(folder)s-soilspectra' %{'metod':self.process.params.metod, 'folder':comp.folder}
                            spectrasuffix = '%(suf)s-%(plot)s-scene' %{'suf':comp.suffix, 'plot':plot[0]}
                            speccomp = Composition(comp.source, comp.product,'endmember', band, prefix, spectrasuffix, mainpath = mainpath, scenes = True, division = 'plots')
                            speccomp.SetExt('xml')
                            L = LandsatLayer(speccomp,self.location,self.acqdate)
                            L.SetLayerPathOld()
                            specxmlLayer = L.FPN
                            print 'specxmlLayer',specxmlLayer
                            if not os.path.isfile(specxmlLayer):
                                specxmlLayer = specLayersOutD = False
                                continue
                            specLayersOutD = {}
                            for b in self.bandL:
                                band = prefix = '%(b)s-%(metod)s-%(folder)s-soilspectra' %{'b':b,'metod':self.process.params.metod, 'folder':comp.folder}
                                spCompCSV = Composition(comp.source,comp.product,'endmember',band,prefix,spectrasuffix, mainpath = mainpath, scenes = True, division = 'plots')
                                spCompCSV.SetExt('csv')
                                L = LandsatLayer(spCompCSV,self.location,self.acqdate)
                                L.SetLayerPathOld()
                                specLayersOutD[b] = L.FPN 
                                if not os.path.isfile(L.FPN):
                                    alldone = False 

                        else:
                            bounds = 'global'
                            NOTYET                        
                            pass
                    else:
                        specxmlLayer = specLayersOutD = False
                    macro = SoillinePlotCSV(slxmlLayer.FPN,slLayersOutD,candxmlLayer,candLayersOutD,specxmlLayer,specLayersOutD)
                    print macro
                    BALLE
                          
    def SetLayer(self,comp):
        BALLE
        #TGTODO SHOULD BE GENERALIZED TO ALL COMP
        source,product,folder,band,prefix,suffix,masked = comp
        compD = {'source':source, 'product':product, 'folder':folder,'band':band,'prefix':prefix,'suffix':suffix}
        compC = Composition(source, product, folder, band, prefix, suffix)
        compC.SetPathParts(self.process.srcpath)
        compC.SetExt(self.process.srcpath.hdr) 
        if self.process.proj.system.lower() == 'landsat':  
            self.layerInD[band] = LandsatLayer(compC,self.location,self.acqdate)
        else:
            STOP
        self.layerInD[band].SetLayerPathOld()
    
    def SetPlotScene(self,scene):
        sceneid,acqdate,path,row,wrs = scene
        #Set the target files
        self.layerInD = {}
        landsatbands = ConnLandsat.GetLandsatBandCompsFromSceneId(scene[0],'srfi')
        self.location = Location('Landsatscene')
        self.location.LandsatScene(wrs, path, row)
        acqdatestr = mj_dt.DateToStrDate(acqdate)
        source,product,folder,band,prefix,suffix,masked = landsatbands[0]
        self.acqdate = AcqDate({'acqdatestr':acqdatestr, 'timestep':'singledate'}, acqdate = acqdate)
        #TGTODO REPLACE SRFI TO tercor if that ever happend
        for landsatband in landsatbands:
            self.SetLayer(landsatband)
            
    def SetPlotMask(self,scene):
        sceneid,acqdate,path,row,wrs = scene
        #Set the target files
        masklayer = ConnLandsat.GetLandsatBandCompsFromSceneId(scene[0],'mask')
        self.location = Location('Landsatscene')
        self.location.LandsatScene(wrs, path, row)
        acqdatestr = mj_dt.DateToStrDate(acqdate)
        source,product,folder,band,prefix,suffix,masked = masklayer[0]
        #print source,product,folder,band,prefix,suffix,masked
        self.acqdate = AcqDate({'acqdatestr':acqdatestr, 'timestep':'singledate'}, acqdate = acqdate)
        self.SetLayer(masklayer[0])
        self.maskvals = ConnLandsat.GetMaskValOnSrcProd(source,product)
        '''
        #TGTODO REPLACE SRFI TO tercor if that ever happend
        for landsatband in landsatbands:
            self.SetLayer(landsatband)
        '''
                      
    def SpecimenSoilLinePVIPBI(self):
        from soilline_v71 import CandidateSoilLine, CandidateVIendmembers
        metod = 'pvipbidefault'
        #Get theplots to process
        mainpath = self.process.compinD['pvi'].mainpath
        tempFP = os.path.join(mainpath,'temporaryfiles')
        if not os.path.exists(tempFP):
            os.makedirs(tempFP)
        plots = self.GetPlots()
        dateD = {'startdate':self.process.period.startdate,'enddate':self.process.period.enddate}
        for plot in plots:
            print 'plot',plot
            self.process.bounds = plot[0]
            if self.process.proj.system.lower() == 'landsat':
                whereD = {}
                plotD = {'plotid':plot[0]}
                scenes = self.SelectLandsatScenes(whereD,plotD,dateD)
                
                for scene in scenes:
                    sceneid,acqdate,path,row,wrs = scene
                    #Set the target files
                    self.layerInD = {}
                    landsatbands = ConnLandsat.GetLandsatBandCompsFromSceneId(scene[0],'srfi')
                    self.location = Location('Landsatscene')
                    self.location.LandsatScene(wrs, path, row)
                    acqdatestr = mj_dt.DateToStrDate(acqdate)
                    source,product,folder,band,prefix,suffix,masked = landsatbands[0]
                    self.acqdate = AcqDate({'acqdatestr':acqdatestr, 'timestep':'singledate'}, acqdate = acqdate)
                    self.layerOutD = {}
                    folder = 'endmember'
                    csvsuffix = '%(suf)s-%(plot)s' %{'suf':suffix,'plot':plot[0]}
                    band = prefix = '%s-%s-soil' %(metod, folder)
                    soilcomp = Composition(source, product, folder, band, prefix, csvsuffix, mainpath = mainpath,scenes = True, division = 'plots')
                    band = prefix = '%s-%s-veg' %(metod, folder)
                    vegcomp = Composition(source, product, folder, band, prefix, csvsuffix, mainpath = mainpath,scenes = True, division = 'plots')
                    soilcomp.SetExt('csv')
                    vegcomp.SetExt('csv')
                    if self.process.proj.system == 'landsat':
                        self.layerOutD['soil'] = LandsatLayer(soilcomp,self.location,self.acqdate)
                        self.layerOutD['soil'].SetLayerPathOld()
                        self.layerOutD['veg'] = LandsatLayer(vegcomp,self.location,self.acqdate)
                        self.layerOutD['veg'].SetLayerPathOld()
                    if self.layerOutD['veg'].Exists() and self.layerOutD['soil'].Exists() and not self.process.overwrite:
                        done = True
                        continue
                    #Set the pvi band
                    folder,band,prefix = self.process.compinD['pvi'].folder,self.process.compinD['pvi'].band,self.process.compinD['pvi'].prefix
                    compD = {'source':source, 'product':product, 'folder':folder,'band':band,'prefix':prefix,'suffix':suffix}
                    compC = Composition(source, product, folder, band, prefix, suffix)
                    compC.SetPathParts(self.process.srcpath)
                    compC.SetExt(self.process.srcpath.hdr) 
                    self.layerInD['pvi'] = LandsatLayer(compC,self.location,self.acqdate)
                    self.layerInD['pvi'].SetLayerPathOld()
                    # set the 'pbi band
                    folder,band,prefix = self.process.compinD['pbi'].folder,self.process.compinD['pbi'].band,self.process.compinD['pbi'].prefix
                    compD = {'source':source, 'product':product, 'folder':folder,'band':band,'prefix':prefix,'suffix':suffix}
                    compC = Composition(source, product, folder, band, prefix, suffix)
                    compC.SetPathParts(self.process.srcpath)
                    compC.SetExt(self.process.srcpath.hdr) 
                    self.layerInD['pbi'] = LandsatLayer(compC,self.location,self.acqdate)
                    self.layerInD['pbi'].SetLayerPathOld()
                    
                    #GET THE position of the point in the band
                    spatialRef,srcLayer = mj_gis.GetRasterMetaData(self.layerInD['pvi'].FPN)
                    #point latlon
                    lon,lat = plot[1:3]
                    print plot,lon,lat
                    lin,col = mj_gis.LatLonPtToRasterLinCol((lon,lat),spatialRef.proj_cs,srcLayer.gt)
                    lin,col = int(round(lin)),int(round(col))
                    print lin,col
                    #TGTODO REPLACE SRFI TO tercor if that ever happend
                    for landsatband in landsatbands:
                        source,product,folder,band,prefix,suffix,masked = landsatband
                        compD = {'source':source, 'product':product, 'folder':folder,'band':band,'prefix':prefix,'suffix':suffix}
                        compC = Composition(source, product, folder, band, prefix, suffix)
                        compC.SetPathParts(self.process.srcpath)
                        compC.SetExt(self.process.srcpath.hdr)   
                        self.layerInD[band] = LandsatLayer(compC,self.location,self.acqdate)
                        self.layerInD[band].SetLayerPathOld() 
                    for key in self.layerInD:
                        if not os.path.isfile(self.layerInD[band].FPN):
                            KALLE
                        tarFN = '%(band)s.tif' %{'band':key}
                        tarFPN = os.path.join(tempFP,tarFN)
                        if os.path.isfile(tarFPN):
                            os.remove(tarFPN)
                        cellx,celly = mj_GDAL.GDALtranslatecutFromPt(self.layerInD[key].FPN,tarFPN,lin,col,srcLayer.lins,srcLayer.cols,self.process.radius)
                        #reset the filepath to the cut raster image
                        self.layerInD[key].FPN = tarFPN
                        print 'here',self.layerInD[key].FPN
                        self.layerInD[key].ReadRasterLayer(flatten = False)
                        self.layerInD[key].lins, self.layerInD[key].cols, self.layerInD[key].projection, self.layerInD[key].geotrans, self.layerInD[key].ext, self.layerInD[key].cellsize, self.layerInD[key].celltype, self.layerInD[key].cellnull, self.layerInD[key].epsg, self.layerInD[key].epsgunit = mj_gis.GetRasterInfo(self.layerInD[key].FPN)

                    sceneD,soilD,vegD = CandidateSoilLine(self,'pvipbidefault')
                    print 'sceneD',sceneD
                    print 'soilD',soilD
                    print 'vegD',vegD
                    #TGOTODO change db to have additional key for bounds for soilsearch and redo tables
                    '''
                    if soilD:
                        ConnEndMember.InsertSearch('soilsearch',sceneD,soilD, self.process.overwrite,self.process.delete)
                    if vegD:
                        ConnEndMember.InsertSearch('vegsearch',sceneD,vegD, self.process.overwrite,self.process.delete)
                    '''
     
    def GetPlots(self):
        plots = ConnSpecimen.SelectPlots(self.process.proj)
        return plots
    
    def SelectPlots(self,whereD):
        plots = ConnSpecimen.SelectPlotsWhere(self.process.proj,whereD)
        return plots
    
    def SelectPlotWRS(self):
        if self.process.proj.system.lower() == 'landsat':
            scenepos = ConnSpecimen.SelectPlotWRS(self.process.proj)
        return scenepos
    
    def GetLandsatScenesOld(self,plot):
        scenes = ConnSpecimen.SelectPlotLandsatScenes(plot)
        return scenes
    
    def SelectLandsatScenes(self,whereD,plotD,dateD):
        if self.process.proj.system.lower() == 'landsat':
            scenes = ConnSpecimen.SelectLandsatScenes(whereD,plotD,dateD)
        return scenes
    
    def SelectPlotsDone(self,sceneid):
        if self.process.proj.system.lower() == 'landsat':
            plotsdone = ConnSpecimen.SelectSRFIextractedPlots(sceneid)
        return plotsdone
                
    def ExtractPlotSRFI(self): 
        import mj_extractplotdata_v70 as mj_extractplot
        #Get the scene positions to process 
        scenepos = self.SelectPlotWRS()
        dateD = {'startdate':self.process.period.startdate,'enddate':self.process.period.enddate}
        plotD = {}
        #Loop over the scene positions
        for scenep in scenepos:
            #Get the plots belonging to this scene
            whereD = {'L.path':scenep[0],'L.row':scenep[1],'L.wrs':scenep[2]} 
            plots = self.SelectPlots(whereD) 
            plotD = {} 
            scenes = self.SelectLandsatScenes(whereD,plotD,dateD)
            for scene in scenes:
                print '    extracting scene',scene
                sceneplots = []
                if not self.process.overwrite:
                    #Get only the positions that require updating
                    plotsdone = self.SelectPlotsDone(scene[0])
                    plotDoneL = [item[0] for item in plotsdone]
                    #loop and only retain undone plots
                    for plot in plots:
                        if not plot[0] in plotDoneL:
                            sceneplots.append(plot)
                else:
                    sceneplots = plots
                print '    plots to extract and already done', len(sceneplots), len(plotDoneL)
                if len(sceneplots) > 0:
                    
                    #Get the scene
                    self.SetPlotScene(scene)
                    self.SetPlotMask(scene)
                    #set the scene data after any key
                    key = self.layerInD.keys()[0]
                    comp = self.layerInD[key].comp
                    key = self.process.compinD.keys()[0]
                    acqdatestr = mj_dt.DateToStrDate(scene[1])
                    sceneD = {'sceneid':scene[0],'source':comp.source,'product':comp.product,'folder':self.process.compinD[key].folder,'path':scenep[0],'row':scenep[1],'acqdatestr':acqdatestr}
                    for key in self.layerInD:
                        if not os.path.isfile(self.layerInD[key].FPN):
                            KALLE
                    plotD = mj_extractplot.GetStarted(self.layerInD,sceneplots,self.maskvals[1],self.maskvals[2])
                    print '    Saving to db'
                    ConnSpecimen.InsertPlotExtract(sceneD,plotD)

class LayersToProcess:
    """class for all layer related processes""" 
    def __init__(self, process,statusD={}):   
        self.process =  process
        statusD ={}
        if self.process.proj.regionid not in ['globe','karttur']:
            statusD['regionid'] = self.process.proj.defregid.lower()
        self.SelectLocations(statusD)

        
    def SelectLocations(self,statusD):
        if self.process.proj.system == 'landsat':
            statusD['exploded'] = 'Y'; statusD['deleted'] = 'N'; statusD['tgnote'] = 'ok';  
            self.locationDates = ConnLandsat.SelectLocationScenes(self.process,statusD)
        elif self.process.proj.system == 'modis':
            key = self.process.compinD.items()[0][0]
            self.locationDates = ConnMODIS.SelectLocationTiles(self.process,self.process.compinD[key].source,statusD)
            
        else:
            NOTYET
                           
    def GetBandsIn(self,locDate): 
        #tgtodo SHOULD BE TRANSLATED TO COMPINS DUING STARTUP
        self.geoFormatD = False
        key = self.process.compinD.items()[0][0]
        compin = self.process.compinD[key]
        compInD = {'source':compin.source,'product':compin.product,'folder':compin.folder,'band':compin.band,'prefix':compin.prefix,'suffix':compin.suffix}
        compL = ['source','product','folder','band','prefix','suffix']  
        for band in self.bandInD:
            comp = []
            for c in compL:
                if c in self.bandInD[band]:
                    comp.append(self.bandInD[band][c])
                else:
                    comp.append(compInD[c])
            comp = Composition(comp[0], comp[1], comp[2], comp[3], comp[4], comp[5])
            comp.SetPathParts(self.process.srcpath)
            comp.SetExt(self.process.srcpath.hdr)
            if self.process.proj.system == 'modis':
                self.SetMODISLocDate(locDate)
                ok = self.SetMODISLayerIn(comp,band)
            else:
                BALLE
            if not ok:
                return False
        return self.geoFormatD
    
    def SetBandsOut(self,locDate):
        key = self.process.compoutD.items()[0][0]
        compin = self.process.compoutD[key]
        compOutD = {'source':compin.source,'product':compin.product,'folder':compin.folder,'band':compin.band,'prefix':compin.prefix,'suffix':compin.suffix}
        compL = ['source','product','folder','band','prefix','suffix']  
        for band in self.bandOutD:
            comp = []
            for c in compL:
                if c in self.bandOutD[band]:
                    comp.append(self.bandOutD[band][c])
                else:
                    comp.append(compOutD[c])
            comp = Composition(comp[0], comp[1], comp[2], comp[3], comp[4], comp[5])
            comp.CompFormat({'cellnull':self.process.compoutD[key].cellnull,'celltype':self.process.compoutD[key].celltype,
                              'scalefac':self.process.compoutD[key].scalefac,'offsetadd':self.process.compoutD[key].offsetadd,
                              'dataunit':self.process.compoutD[key].dataunit,'measure':self.process.compoutD[key].measure,
                              'palette':self.process.compoutD[key].palette})
            comp.SetPathParts(self.process.srcpath)
            comp.SetExt(self.process.srcpath.hdr)
            if self.process.proj.system == 'modis':
                self.SetMODISLocDate(locDate)
                self.SetMODISLayerOut(comp,band)
            else:
                BALLE
            self.layerOutD[band].SetGeoFormat(self.geoFormatD)

    def SetMODISLocDate(self,locDate):
        acqdate = locDate[7]
        self.location = Location('MODISTile')
        self.location.MODISScene(locDate[5],locDate[6])
        acqdatestr = mj_dt.DateToStrDate(acqdate)
        #self.acqdate = AcqDate({'acqdatestr':acqdatestr, 'timestep':self.process.period.timestep}, acqdate = acqdate)
        acqdatedoy = mj_dt.DateToYYYYDOY(acqdate)
        self.acqdate = AcqDate({'acqdatestr':acqdatestr, 'timestep':self.process.period.timestep}, acqdate = acqdate, acqdatedoy=acqdatedoy)
             
    def StandardLocationDates(self,locDate): 
        self.WhereWhen(locDate)
        self.layerInD = {}; self.layerOutD = {}; self.maskInD ={}; self.maskD = {}

        compD = self.GetLayersIn(locDate,'allscenes')
        if not compD:
            return False

        self.SetLayersOut(locDate,compD)
        #Input and output is set, check if output exists, and if overwrite or delete is set 
        #TGTODO CAN NOT REMEMBER NULCHECK
        self.nullcheck = False
        AllDone = True
        for key in self.layerOutD:
            if not self.layerOutD[key].Exists():
                AllDone = False
            elif not self.process.overwrite:
                print '    already done, registering',self.layerOutD[key].comp.band, self.layerOutD[key].FPN

        return True
    
    def EndMemberLocationDates(self,locDate): 
        self.skip = False
        self.WhereWhen(locDate)
        self.layerInD = {}
        for key in self.process.compinD:
            c = self.process.compinD[key] 
            sceneid,product = locDate[0],locDate[3]
            srcmethod, srcdata = c.prefix.split('-')[0:2]              
            endmembers = ConnEndMember.CheckSceneEndmember(sceneid,product,srcmethod,srcdata,bounds)
            if len(endmembers) >= 1 and not self.process.overwrite:
                self.skip = True
                return                
            comp = [c.source, c.product, c.folder, c.band, c.prefix, c.suffix ]
            if '*' in comp:
                s = self.systemcomp
                syscomp = [s.source, s.product, c.folder, c.band, c.prefix, c.suffix]  
                for x,i in enumerate(comp):
                    if i == '*':
                        comp[x] = syscomp[x]
                if comp[5] == '*':
                    comp[5] = '_%s' %(locDate[8])
            compin = Composition(comp[0],comp[1],comp[2],comp[3],comp[4],comp[5], mainpath = c.mainpath, scenes = True, division = 'scenes')
            compin.SetExt('csv')
            compout = Composition(comp[0],comp[1],comp[2],comp[3],comp[4],comp[5], mainpath = c.mainpath, scenes = True, division = 'scenes')
            compout.SetExt('xml')
            self.SetLayer(compin,self.location,self.acqdate,key)
            if not os.path.isfile(self.layerInD[key].FPN):
                self.skip = True              
                  
    def WhereWhen(self,locDate):
        if self.process.proj.system == 'landsat':
            self.sceneid, sceneFN, source, product, folder, path, row, acqdate, self.typeid = locDate
            self.systemcomp = Composition(source = source, product = product, folder = folder, mainpath = self.process.srcpath.mainpath)
            self.systemcomp.SetPathParts(self.process.srcpath)
            self.location = Location('Landsatscene')
            self.wrs = 2
            self.location.LandsatScene(self.wrs, path, row)
            acqdatestr = mj_dt.DateToStrDate(acqdate)
            self.acqdate = AcqDate({'acqdatestr':acqdatestr, 'timestep':'singledate'}, acqdate = acqdate)
        elif self.process.proj.system == 'modis':
            self.sceneid, sceneFN, source, product, folder, path, row, acqdate = locDate
            self.systemcomp = Composition(source = source, product = product, folder = folder, mainpath = self.process.srcpath.mainpath)
            self.systemcomp.SetPathParts(self.process.srcpath)
            self.location = Location('MODISTile')
            self.location.MODISScene(path,row)
            acqdatestr = mj_dt.DateToStrDate(acqdate)
            #self.acqdate = AcqDate({'acqdatestr':acqdatestr, 'timestep':self.process.period.timestep}, acqdate = acqdate)
            acqdatedoy = mj_dt.DateToYYYYDOY(acqdate)
            self.acqdate = AcqDate({'acqdatestr':acqdatestr, 'timestep':self.process.period.timestep}, acqdate = acqdate, acqdatedoy=acqdatedoy)


        else:
            NOTYET
    
    def SetComp(self,comp, path):
        comp.SetPathParts(path)
        comp.SetExt(path.hdr)
        
    def GetLayerMeta(self,band,comp):
        if os.path.isfile(self.layerInD[band].FPN):
            self.lins, self.cols, self.projection, self.geotrans, self.ext, self.cellsize, self.celltype, self.cellnull, self.epsg, self.epsgunit = mj_gis.GetRasterInfo(self.layerInD[band].FPN)
            self.layerInD[band].lins, self.layerInD[band].cols, self.layerInD[band].projection, self.layerInD[band].geotrans, self.layerInD[band].ext, self.layerInD[band].cellsize, self.layerInD[band].celltype, self.layerInD[band].cellnull, self.layerInD[band].epsg, self.layerInD[band].epsgunit = mj_gis.GetRasterInfo(self.layerInD[band].FPN)
            self.geoFormatD = {'lins':self.lins,'cols':self.cols,'projection':self.projection,'geotrans':self.geotrans,'cellsize':self.cellsize}
            #update composition with celltype and cellnull
            comp.CompFormat({'celltype':self.celltype,'cellnull':self.cellnull})
            print 'input file not found',self.layerInD[band].FPN
            return True
        else:
            print 'WARNING, input file not found',self.layerInD[band].FPN

            return False

        
    def SetLandsatLayer(self,comp, band):
        self.layerInD[band] = LandsatLayer(comp,self.location,self.acqdate)
        self.layerInD[band].SetLayerPathOld()
        return self.GetLayerMeta(band)
        
    def SetMODISLayerIn(self, comp, band):
        self.layerInD[band] = MODISLayer(comp,self.location,self.acqdate)
        self.layerInD[band].SetLayerPath()
        return self.GetLayerMeta(band,comp)
        
    def SetMODISLayerOut(self, comp, band):
        self.layerOutD[band] = MODISLayer(comp,self.location,self.acqdate)
        self.layerOutD[band].SetLayerPath()
    
    def SetRegionLayer(self):
        pass
    
    def SetSystemLayer(self,band,comp,io):
        if self.process.proj.system == 'landsat':
            self.SetLandsatLayer(comp, band)
        elif self.process.proj.system == 'ancillary':
            region
        elif self.process.proj.system == 'modis':
            if io == 'in':
                return self.SetMODISLayerIn(comp, band)
            else:
                self.SetMODISLayerOut(comp, band)
        else:
            annat
            
    def SetSystemMask(self,mask,comp):
        if self.process.proj.system == 'landsat':
            self.SetLandsatMask(comp, band)
        elif self.process.proj.system == 'ancillary':
            region
        elif self.process.proj.system == 'modis':
            modis
        else:
            annat
                
    def GetAllBands(self,comp):
        comp = Composition(comp[0], comp[1], comp[2], comp[3], comp[4], comp[5] )
        recs = ConnComp.SelectSceneBandsFromComp(comp, self.process.proj.system, self.location, self.acqdate.acqdatestr, 'any')
        for rec in recs:
            compid, source, product, folder, band, prefix, suffix, acqdatestr, masked, path, row = rec
            compD = {'source':source, 'product':product, 'folder':folder,'band':band,'prefix':prefix,'suffix':suffix}
            comp = Composition(source, product, folder, band, prefix, suffix)
            comp = self.SetComp(comp,self.process.srcpath.hdr)
            self.SetSystemLayer(comp)
        return compD

    def GetLayersIn(self,locDate,timestep,spatial = True): 
        self.layerInD = {}
        geoFormatD = False
        for key in self.process.compinD:
            #check that the comp is in the DB
            #reset any * in comp
            c = self.process.compinD[key]
            comp = [c.source, c.product, c.folder, c.band, c.prefix, c.suffix ]
            if '*' in comp:
                s = self.systemcomp
                syscomp = [s.source, s.product, c.folder, c.band, c.prefix, c.suffix]  
                for x,i in enumerate(comp):
                    if i == '*':
                        comp[x] = syscomp[x]
            compini = Composition(comp[0],comp[1],comp[2],comp[3],comp[4],comp[5]) 
            if c.band == 'allbands':
                compD = self.GetAllBands(comp)
            else:
                comp = ConnComp.SelectSingleLayerComposition(compini,self.process.proj.system,self.acqdate.acqdatestr,timestep)
                if comp == None:
                    STOP
                #compid, source, product, folder, band, prefix, suffix, acqdatestr, masked, path, row = comp
                compid, source, product, folder, band, prefix, suffix, acqdatestr = comp[0:8]
                compD = {'source':source, 'product':product, 'folder':folder,'band':band,'prefix':prefix,'suffix':suffix}
                comp = Composition(source, product, folder, band, prefix, suffix)
                self.SetComp(comp,self.process.srcpath)
                if not self.SetSystemLayer(key,comp,'in'):

                    return False
                print self.geoFormatD
                #if masked == 'N' and not self.process.compinD[key].masked:
                #    self.SetLayerMask(key)        
        return compD
            
    def SetSceneForEndMember(self,compin,srcmethod,srcdata,bounds):
        self.sceneD = {'source':compin.source, 'product':compin.product,'acqdatestr':self.acqdate.acqdatestr,'path':self.location.path,'row':self.location.row,'bounds':bounds}
        self.sceneD['srcmethod'] = srcmethod
        self.sceneD['srcdata'] = srcdata
  
    def SetLayersOut(self,locDate, compD):
        self.maskOutD = {}
        self.layerOutD = {}
        for key in self.process.compoutD:
            if self.process.compoutD[key].source in ['','*']:
                source = compD['source']
            else:
                source = self.process.compoutD[key].source
            if self.process.compoutD[key].product in ['','*']:
                product = compD['product']
            else:
                product = self.process.compoutD[key].product
            if self.process.compoutD[key].suffix in ['','*']:
                suffix = compD['suffix']
            else:
                suffix = self.process.compoutD[key].suffix
            #comp = source, product, self.process.compoutD[key].folder, self.process.compoutD[key].band, self.process.compoutD[key]. prefix, suffix}
            comp = Composition(source, product, self.process.compoutD[key].folder, self.process.compoutD[key].band, self.process.compoutD[key].prefix, suffix)
            self.SetComp(comp, self.process.tarpath)
            comp.CompFormat({'cellnull':self.process.compoutD[key].cellnull,'celltype':self.process.compoutD[key].celltype,
                              'scalefac':self.process.compoutD[key].scalefac,'offsetadd':self.process.compoutD[key].offsetadd,
                              'dataunit':self.process.compoutD[key].dataunit,'measure':self.process.compoutD[key].measure,
                              'palette':self.process.compoutD[key].palette})
            comp.CompFormat(self.process.compoutD)
            #Get the layer
            self.SetSystemLayer(key,comp,'out')
            #Set the geofromat
            self.layerOutD[key].SetGeoFormat(self.geoFormatD)
        
    def SetLayerMask(self,key):
        UPDATE
        if self.process.proj.system == 'landsat':
            maskcomp = ConnLandsat.GetLayerMask(self.layerInD[key])
            if maskcomp == None:
                BALLE
            self.maskD[key] = maskcomp
            source, product, folder, band, prefix, suffix = maskcomp[0:6]
            comp = Composition(source, product, folder, band, prefix, suffix)
            comp = self.SetComp(comp, self.process.srcpath)
            
            self.maskInD[key] = LandsatLayer(compC,self.location,self.acqdate)
            self.maskInD[key].SetLayerPathOld()
            if not os.path.exists(self.maskInD[key].FPN):
                print 'no mask', self.maskInD[key].FPN
                BALLE
            params = ['clear', 'cellnull', 'mask', 'cloud', 'cloudshadow', 'snow', 'water']
            self.maskD[key] = dict(zip(params,maskcomp[6:13]))
            #append mask with null
            nullmask = maskcomp[8]
            nullmask.append(maskcomp[7])
            self.maskD[key]['nullmask'] = nullmask

    def GetXMLBands(self, processElement):
        self.bandD = {}
        bandTags = processElement.getElementsByTagName('band')
        tagAttrL = ConnProcess.SelectProcessTagAttr(self.process.processid,'process','band') 
        for bandTag in bandTags:
            band = XMLelement(bandTag,tagAttrL,'band',self.process.processid)[0]
            self.bandD[band['bandid']] = band['order'] 
            
    def GetXMLBandsIn(self, processElement):
        #TGTODO, move to startup
        self.bandInD = {}
        bandTags = processElement.getElementsByTagName('bandin')
        tagAttrL = ConnProcess.SelectProcessTagAttr(self.process.processid,'process','bandin') 
        for bandTag in bandTags:
             band = XMLelement(bandTag,tagAttrL,'bandin',self.process.processid)[0]
             self.bandInD[band['band']] = band  
            
    def GetXMLBandsOut(self, processElement):
        #TGTODO, move to startup
        self.bandOutD = {}
        bandTags = processElement.getElementsByTagName('bandout')
        tagAttrL = ConnProcess.SelectProcessTagAttr(self.process.processid,'process','bandout') 
        for bandTag in bandTags:
             band = XMLelement(bandTag,tagAttrL,'bandout',self.process.processid)[0]
             self.bandOutD[band['band']] = band    
        
    def ProduceLayers(self):      
        for key in self.layerInD: 
            print '    reading raster', self.layerInD[key].FN
            self.layerInD[key].ReadRasterLayer(complete= True, flatten = False, mode='edit', structcode = arrctD)
        if self.process.processid == 'NDVI':
            print '    Calculating NDVI'
            self.numpyNDVI()
        elif self.process.processid == 'PVIPBI':
            print '    Calculating PVIPBI'
            self.numpyPVIPBI()
        elif self.process.processid == 'tasscap':
            print '    Calculating Tasseled Cap'
            self.NumpyTassCap()
        elif self.process.processid == 'inversetc':
            print '    Inverse Tasseled Cap'
            self.NumpyInverseTassCap()
        elif self.process.processid == 'inversetc':
            print '    Inverse Tasseled Cap'
            self.NumpyInverseTassCap()
        elif self.process.processid == 'inversetcvi':
            print '    Inverse Tasseled Cap'
            self.NumpyInverseTassCap()
        elif self.process.processid == 'exporttobyte':
            print '    Exporting to byte'
            self.NumpyExportToByte()
        elif self.process.processid == 'lineartransform':
            self.NumpyLinearTransform()
        elif self.process.processid == 'fgbg':
            self.NumpyFGBG()
        elif self.process.processid == 'twipercent':
            self.NumpyTWIpercent()
        else:
            exitstr = 'process %s not implemented in ' %(self.process.processid)
            sys.exit(exitstr)
        for key in self.layerOutD:
            print '    Registering',self.layerOutD[key].comp.band
            self.layerOutD[key].RegisterLayer(self.process.proj.system)
                                                                     
    def MaskOutput(self):
        #Check for null in input
        if self.nullcheck:
            for inkey in self.layerInD:
                if inkey == 'mask':
                    continue
                print 'checking for null'
                if self.layerInD[inkey].cellnull in self.layerInD[inkey].BAND:
                    MASK = self.layerInD[inkey].BAND
                    innull = self.layerInD[inkey].cellnull
                    for outkey in self.layerOutD:
                        BAND = self.layerOutD[outkey].BAND
                        outnull =  self.layerOutD[outkey].cellnull
                        BAND = map(lambda m,b: outnull if m ==innull else b, MASK, BAND)
                        #reset
                        self.layerOutD[outkey].BAND = BAND
            #Check for mask
        for mask in self.maskInD:
            maskid = 'nullmask'
            print 'maskD', self.maskD
            print self.maskD[mask]
            print self.maskD[mask][maskid]
            maskval = self.maskD[mask][maskid]
            
            print '    reading and flattening raster', self.maskInD[mask].FN
            self.maskInD[mask].ReadRasterLayer(complete= True, flatten = True, mode='edit', structcode = arrctD)
            print 'MASK', self.maskInD[mask].BAND[0:10]
            MASK  = self.maskInD[mask].BAND
            for outkey in self.layerOutD:
                BAND = self.layerOutD[outkey].BAND 
                outnull =  self.layerOutD[outkey].comp.cellnull
                if maskid in ['mask','nullmask']:
                    BAND = map(lambda m,b: outnull if m in maskval else b, MASK, BAND)
                else:
                    BAND = map(lambda m,b: outnull if m == maskval  else b, MASK, BAND)
                #reset the BAND
                self.layerOutD[outkey].BAND = BAND
              
    def ReadMask(self,maskid): 
        for mask in self.maskInD:         
            print '    reading mask raster', self.maskInD[mask].FN
            self.maskInD[mask].ReadRasterLayer(complete= True, flatten = False, mode='edit', structcode = arrctD)
            self.MASKRAW  = self.maskInD[mask].BAND
            self.maskkey = mask
            self.maskval = self.maskD[mask][maskid] 
            
    def SetMask(self,outnull,celltype,maskid,maskval): 
        #outnull =  self.layerOutD[outkey].comp.cellnull
        mD = {}
        if maskid in ['nullmask','mask']:
            for m in maskval:
                mD[m] = outnull   
        else:
            mD[maskval] = outnull                  
        dim = np.shape(self.MASKRAW)
        if celltype.lower() in ['byte','uint8']:
            mm = np.empty(dim, dtype=np.int8)
            np.copyto(mm,self.MASKRAW)     
        elif celltype.lower() == 'int16':  
            mm = np.empty(dim, dtype=np.int16)
            np.copyto(mm,self.MASKRAW)
        elif celltype.lower() == 'uint16': 
            mm = np.empty(dim, dtype=np.uint16)
            np.copyto(mm,self.MASKRAW)
        else:
            'print numpy type not defined',layer.comp.celltype
            sys.exit()   
        for k, v in mD.iteritems(): mm[mm==k] = outnull
        self.XMASK = mm
                             
    def numpyMaskOutput(self,outkey,maskid):
        '''
        for mask in self.maskInD:
            maskid = 'nullmask'
            maskval = self.maskD[mask][maskid]         
            print '    reading mask raster', self.maskInD[mask].FN
            self.maskInD[mask].ReadRasterLayer(complete= True, flatten = False, mode='edit', structcode = arrctD)
            MASK  = self.maskInD[mask].BAND
        
        for outkey in self.layerOutD:
        '''
        maskid = 'nullmask'      
        #maskval = self.maskDself.maskkey][maskid]
        maskval = self.maskD[self.maskkey][maskid] 
        self.ReadMask(maskid)
        outnull =  self.layerOutD[outkey].comp.cellnull
        mD = {}
        if maskid in ['nullmask','mask']:
            for m in maskval:
                mD[m] = outnull   
        else:
            mD[maskval] = outnull                  
        dim = np.shape(MASK)
        if self.layerOutD[outkey].comp.celltype.lower() in ['byte','uint8']:
            mm = np.empty(dim, dtype=np.int8)
            np.copyto(mm,MASK)     
        elif self.layerOutD[outkey].comp.celltype.lower() == 'int16':  
            mm = np.empty(dim, dtype=np.int16)
            np.copyto(mm,MASK)
        elif self.layerOutD[outkey].comp.celltype.lower() == 'uint16': 
            mm = np.empty(dim, dtype=np.uint16)
            np.copyto(mm,MASK)
        else:
            'print numpy type not defined',layer.comp.celltype
            sys.exit()   
        for k, v in mD.iteritems(): mm[mm==k] = outnull
        B = self.layerOutD[outkey].BAND 
        BAND = np.where(mm==outnull,mm,B)
        self.layerOutD[outkey].BAND = BAND
                  
    def numpyPVIPBI(self):       
        self.nullcheck = True #included in algorithm
        if 'NA' in self.layerInD:
            NIR = self.layerInD['NA'].BAND
            NIRnull = self.layerInD['NA'].comp.cellnull
        elif 'NB' in self.layerInD:
            NIR = self.layerInD['NB'].BAND
            NIRnull = self.layerInD['NB'].comp.cellnull
        else:
            print self.layerInD
            sys.exit('No NIR band given for calculating PVIPBI')
        Red = self.layerInD['RL'].BAND
        Rednull = self.layerInD['RL'].comp.cellnull
        outnull = self.layerOutD['PVI'].comp.cellnull
        #create the mask
        mask = np.logical_and(Red !=Rednull, NIR !=NIRnull)
        PVI = 1000 + 0.2723659*(-0.735633 * Red + (NIR-256)*0.6773793)
        PVI = PVI*mask
        PVI[PVI == 0] = outnull
        outnull = self.layerOutD['PBI'].comp.cellnull
        PBI = 100 + 0.2723659*(0.6773793 * Red - (NIR-256)*-0.735633)
        PBI = PBI*mask
        PBI[PBI == 0] = outnull
        self.layerOutD['PVI'].BAND = PVI
        self.layerOutD['PBI'].BAND = PBI
    
    def NumpyTassCap(self):
        key = self.layerInD.items()[0][0]
        self.SetLayerMask(key)
        for key in self.tascapD:
            print key,self.tascapD[key]
        eigenvectors = ConnEndMember.GetEigenVectors(self.tascapD)
        print eigenvectors
        spectraA = np.empty([ len(self.TCD), len(self.bandD)])
        if self.offset:
            offsetA = np.empty([len(self.bandD)])
        emL = []
        bandL = []
        for item in eigenvectors:
            if item[0] not in emL:
                emL.append(item[0])
            if item[1] not in bandL:
                bandL.append(item[1])
            if item[0] == self.tascapD['offsetem']:
                offsetA[self.bandD[item[1]]] = item[2]
            else:
                spectraA[ self.TCD[item[0]]['tcnr']-1,self.bandD[item[1]] ] = item[2]    
        if self.offset:
            for band in self.bandD:
                offset = offsetA[ self.bandD[band] ]
                
        key = self.layerOutD.items()[0][0]
        outNull = self.layerOutD[key].comp.cellnull
        cellType = self.layerOutD[key].comp.celltype
        maskA = np.empty([ self.layerOutD[key].lins, self.layerOutD[key].cols])
        for band in self.bandD:
            inNull = self.layerInD['rl'].comp.cellnull
            #factor = spectraA[ self.TCD[TC]['tcnr']-1,self.bandD[band] ]
            #OFFSET HERE NOT IN EIGENVECTOR TEST
            #print TC,band,factor,os.path.split(self.layerInD[band].FPN)[1],os.path.split(self.layerOutD[self.TCD[TC]['tcid']].FPN)[1]
            #maskA = np.add(factor*self.layerInD[band].BAND,tcA)
            maskA[(self.layerInD['rl'].BAND == inNull) | (maskA == outNull)] = outNull
        maskid = 'nullmask'
        self.ReadMask(maskid)
        #self.SetMask(outNull)
        maskid = 'nullmask'
        self.SetMask(outNull,cellType,maskid,self.maskval)
        maskA[(self.XMASK == outNull) | (maskA == outNull)] = outNull
        rasterbandD = {}
        for band in self.bandD:
            if self.offset:
                BALLE
                offset = offsetA[ self.bandD[band] ]
                rasterbandD[band] = self.layerInD[band].BAND-offset
            else:
                rasterbandD[band] = self.layerInD[band].BAND
    
        for TC in self.TCD:
            #create empty array
            tcA = np.empty([ self.layerOutD[self.TCD[TC]['tcid']].lins, self.layerOutD[self.TCD[TC]['tcid']].cols])
            for band in self.bandD:
                factor = spectraA[ self.TCD[TC]['tcnr']-1,self.bandD[band] ]
                #OFFSET HERE NOT IN EIGENVECTOR TEST
                #print TC,band,factor,os.path.split(self.layerInD[band].FPN)[1],os.path.split(self.layerOutD[self.TCD[TC]['tcid']].FPN)[1]
                tcA = np.add(factor*rasterbandD[band],tcA)

            tcA = tcA.astype(np.int32)
            tcA[maskA == outNull] = outNull
            #np.where instead???
            self.layerOutD[self.TCD[TC]['tcid']].BAND = tcA
            self.layerOutD[self.TCD[TC]['tcid']].WriteRaster(flatten = False)        
        
    def NumpyInverseTassCap(self):
        for band in self.bandD:
            print 'layerout',self.layerOutD[band].FPN
        eigenvectors = ConnEndMember.GetEigenVectors(self.tascapD)
        spectraA = np.zeros([ len(self.TCD), len(self.bandD)])
        offsetA = np.empty([len(self.bandD)])
        print 'spectraA shape',spectraA.shape
        if not spectraA.shape[0] == spectraA.shape[1]:
            NOTUNITARY
        print 'TCD',self.TCD
        emL = []
        bandL = []
        for item in eigenvectors:
            if item[0] not in emL:
                emL.append(item[0])
            if item[1] not in bandL:
                bandL.append(item[1])
            if item[0] == self.tascapD['offsetem']:
                offsetA[self.bandD[item[1]]] = item[2]
            else:
                if item[0] in self.TCD:
                    spectraA[ self.TCD[item[0]]['tcnr']-1,self.bandD[item[1]] ] = item[2]
                else:
                    print 'else',item

        transposeA = spectraA
        for TC in self.tcIdD:
            #create empty array

            for band in self.bandD:
                factor = transposeA[ self.tcIdD[TC]['tcnr']-1,self.bandD[band] ]
                print 'TC band factor',TC, band, factor
        BALLE
        
        print 'transposeA',transposeA
        band = self.layerOutD.items()[0][0]
        key = self.layerInD.items()[0][0]
        outNull = self.layerOutD[band].comp.cellnull
        inNull = int(self.layerInD[key].comp.cellnull)
        cellType = self.layerOutD[band].comp.celltype
        maskA = np.zeros([ self.layerOutD[band].lins, self.layerOutD[band].cols]) 
        maskA[self.layerInD[key].BAND == inNull] = outNull
        for band in self.bandD:  
            print 'band',band
            #create empty array
            bandA = np.empty([ self.layerOutD[band].lins, self.layerOutD[band].cols])
            for TC in self.tcIdD:
                print ' '
                print 'tc',TC, self.tcIdD[TC]['tcnr']-1
                factor = transposeA[ self.tcIdD[TC]['tcnr']-1,self.bandD[band] ]
                print 'factor', factor
                print 'band', band

                bandA = np.add(self.layerInD[TC].BAND*factor,bandA)
                print 'TC',self.layerInD[TC].BAND[5555,5555]
                print 'thisreversal', self.layerInD[TC].BAND[5555,5555]*factor
                print 'band',bandA[5555,5555]
                
            if self.offset and self.offsetinclude:
                offset = offsetA[ self.bandD[band] ]
                print 'adding offset',band,offset
                bandA = bandA+offset
            bandA = bandA.astype(np.int32)
            bandA[maskA == outNull] = outNull
            #np.where instead???
            self.layerOutD[band].BAND = bandA
            self.layerOutD[band].WriteRaster(flatten = False)
            BALLE
                
    def NumpyExportToByte(self):
        key = self.layerInD.keys()[0]
        Rin = self.layerInD[key].BAND
        nullIn = self.layerInD[key].cellnull
        Rout = (Rin+self.offset)*self.scalefac
        
        Rout[(Rout < self.minval)] = self.minval
        Rout[(Rout > self.maxval)] = self.maxval
        Rout[Rin == nullIn] = 255
        if self.two51 != -99:
            Rout[(Rin == self.two51)] = 251
        if self.two52 != -99:
            Rout[(Rin == self.two52)] = 252
        if self.two53 != -99:
            Rout[(Rin == self.two53)] = 253
        if self.two54 != -99:
            Rout[(Rin == self.two54)] = 254
        key = self.layerOutD.keys()[0]
        self.layerOutD[key].BAND = Rout
        self.layerOutD[key].WriteRaster(flatten = False)
        BALLE
          
    def NumpyLinearTransform(self):
        #create empty 2D array for the output
        band0 = self.layerInD.items()[0][0]
        outNullD = {}
        inNull = self.layerInD[band0].comp.cellnull
        print inNull

        for key in self.layerOutD:
            self.layerOutD[key].BAND = np.zeros([ self.layerOutD[key].lins, self.layerOutD[key].cols]) 
            outNullD[key] = self.layerOutD[key].comp.cellnull
            outNull = outNullD[key]
        #then run 
        for band in self.layerInD:
            for key in self.layerOutD:
                scalekey = '%(b)s%(k)s' %{'b':band,'k':key}
                #print 'offset', self.offsetD[band]
                #print 'scalekey',scalekey,self.scalefacD
                #print 'scalefac',self.scalefacD[scalekey]
                self.layerOutD[key].BAND += (self.layerInD[band].BAND + self.offsetD[band]['offset'])*self.scalefacD[scalekey]['scalefac']
   
        cellType = self.layerOutD[key].comp.celltype
        outNull = int(outNull)
        inNull = int(inNull)
        maskA = np.empty([ self.layerInD[band0].lins, self.layerInD[band0].cols])
        for band in self.layerInD:
            inNull = self.layerInD[band].comp.cellnull
            maskA[(self.layerInD[band].BAND == inNull) | (maskA == outNull)] = outNull
        '''
        for band in self.bandD:
            inNull = self.layerInD[band].comp.cellnull
            maskA[(self.layerInD[band].BAND == inNull) | (maskA == outNull)] = outNull
        '''
        for key in self.layerOutD:
            self.layerOutD[key].BAND[maskA == outNull] = outNull
            self.layerOutD[key].WriteRasterLayer(flatten = False) 

    def NumpyFGBG(self):
        band0 = self.layerInD.items()[0][0]
        x = self.layerInD[self.process.xband].BAND
        y = self.layerInD[self.process.yband].BAND
        FG = self.process.rescalefac * ((self.sinrang*(x+y-self.process.intercept) + self.cosrang*(-x+y-self.process.intercept)) / 
                             (self.sinrang*(x-y+self.process.intercept) + self.cosrang*( x+y-self.process.intercept) + self.process.calibfac ))
        #FG =  5942*( ( self.sinrang*(x+y+2080) + self.cosrang*(-x+y+2080) ) / ( self.sinrang*(x - y - 2080)+self.cosrang*(x+y+2080) + 7000 ) )
        #twi = 5942*( ( _sinrang*(x+y+2080) + _cosrang*(-x+y+2080) ) / ( _sinrang*(x - y - 2080)+_cosrang*(x+y+2080) + 7000 ) )

        #BG = self.process.rescalefac * ((self.sinrang*(x+y+self.process.intercept) + self.cosrang*(-x+y+self.process.intercept)) / 
        #                     (self.sinrang*(x-y-self.process.intercept) + self.cosrang*( x+y+self.process.intercept) + self.process.calibfac ))

        maskA = np.empty([ self.layerInD[band0].lins, self.layerInD[band0].cols])
        outNullD = {}
        for key in self.layerOutD:
            #self.layerOutD[key].BAND = np.zeros([ self.layerOutD[key].lins, self.layerOutD[key].cols]) 
            outNullD[key] = self.layerOutD[key].comp.cellnull
            outNull = outNullD[key]
        for band in self.layerInD:
            inNull = self.layerInD[self.process.xband].comp.cellnull
            maskA[(self.layerInD[self.process.xband].BAND == inNull) | (maskA == outNull)] = outNull

        
        for key in self.layerOutD:
    
            if key == self.process.fg:
                FG[maskA == outNull] = outNull
                self.layerOutD[key].BAND = FG
            else:
                BG[maskA == outNull] = outNull
                self.layerOutD[key].BAND = BG
            self.layerOutD[key].WriteRasterLayer(flatten = False)


    def NumpyTWIpercent(self):
        band0 = self.layerInD.items()[0][0]
        key = self.layerOutD.items()[0][0]

        B = self.layerInD[band0].BAND
        TWI = 2*((B+4300)/430+pow(1.067,(B+4300)*0.0086))#2 is the scalefac
        TWI[TWI > 200] = 200 #set amx to 200 (100 percent)
        maskA = np.empty([ self.layerInD[band0].lins, self.layerInD[band0].cols])
        outNullD = {}
        for key in self.layerOutD:
            self.layerOutD[key].BAND = np.zeros([ self.layerOutD[key].lins, self.layerOutD[key].cols]) 
            outNullD[key] = self.layerOutD[key].comp.cellnull
            outNull = outNullD[key]
        for band in self.layerInD:
            inNull = self.layerInD[band0].comp.cellnull
            maskA[(self.layerInD[band0].BAND == inNull) | (maskA == outNull)] = outNull
        TWI[maskA == outNull] = outNull
        self.layerOutD[key].BAND = TWI
        self.layerOutD[key].WriteRasterLayer(flatten = False)
                           
class ProcessLayers(LayersToProcess):
    def __init__(self,process,processElement,locationL): 
        """The constructor expects an instance of the composition class and the wrs (1 or 2)."""
        LayersToProcess.__init__(self, process)
        self.layerInD = {}; self.layerOutD = {}; self.maskInD ={}; self.maskD = {}
        elementNodes = processElement.childNodes[:]
        elementNodes = [x.nodeName for x in elementNodes]
        bandinFlag = False; bandoutFlag = False
        if 'bandin' in elementNodes:
            bandinFlag = True
            self.GetXMLBandsIn(processElement)
        if 'bandout' in elementNodes:
            bandoutFlag = True
            self.GetXMLBandsOut(processElement)
        for locDate in self.locationDates:
            print 'locDate',locDate
            if bandinFlag:
                #self.BandInLocationDates(locDate)
                ok = self.GetBandsIn(locDate)
                if ok and bandoutFlag:
                    self.SetBandsOut(locDate)
                elif ok:
                    STOP
            else:
                ok = self.StandardLocationDates(locDate)
            if not ok:
                continue
            AllDone = True   
            for key in self.layerOutD:
                if not self.layerOutD[key].Exists():
                    AllDone = False
                else:
                    print '    already done, registering',self.layerOutD[key].comp.band, self.layerOutD[key].FPN
                    self.layerOutD[key].RegisterLayer(self.process.proj.system)
            if not AllDone or self.process.overwrite:
                if self.process.processid == 'tasscap':
                    self.SetTassCapProcessing(processElement,locDate, geoFormatD, compD,aD)
                elif self.process.processid == 'inversetc':
                    self.SetInverseTCProcessing(processElement,locDate, geoFormatD, compD,aD)
                elif self.process.processid == 'exporttobyte':
                    self.SetExportToByte(processElement,locDate, geoFormatD, compD, aD)
                elif self.process.processid == 'lineartransform':
                    self.SetLinearTransform(processElement)
                elif self.process.processid == 'fgbg':
                    self.SetFGBG()
                elif self.process.processid == 'twipercent':
                    self.ProduceLayers()
                else: 
                    exitstr = 'process not defined in ProcessLayers %s'  %( self.process.processid)
                    sys.exit(exitstr)            
    
    def SetFGBG(self): 
        #TGTODO ASSEMBEL ALL PARAMETERS IN A SEPARATE CLASS
        from math import atan, sin, cos
        print self.process.xband
        print self.process.yband
        print self.layerInD[self.process.xband].FPN
        print self.layerInD[self.process.yband].FPN
        


        #Do the rotation
        angrad = -atan(self.process.slope)
        rangdeg = 180 * angrad / 3.1415
        rangdeg += 45
        #Convert degrees to radians
        rangrad = 3.1415 * rangdeg / 180
        #Get the sin and cos angles
        self.sinrang = sin(rangrad) 
        self.cosrang = cos(rangrad)
        print 'self.sinrang, self.cosrang', self.sinrang, self.cosrang

        #twi = map(mapGlobalTWITrig,x,y)
        self.ProduceLayers()
        for key in self.layerOutD:
            print '     registering',self.layerOutD[key].comp.band, self.layerOutD[key].FPN
            self.layerOutD[key].RegisterLayer(self.process.proj.system)
             
    def SetLinearTransform(self,processElement):
        self.GetOffset(processElement)
        self.GetScalefac(processElement)
        self.ProduceLayers()
        for key in self.layerOutD:
            print '     registering',self.layerOutD[key].comp.band, self.layerOutD[key].FPN
            self.layerOutD[key].RegisterLayer(self.process.proj.system)
           
    def SetInverseTCProcessing(self,processElement,locDate, geoFormatD, compD):
        from copy import deepcopy
        self.offset = False
        self.GetBands(processElement)
        self.GetTCs(processElement)
        self.imageendmember = False
        self.offsetinclude = True
        self.tascapD = {'bounds':self.process.params.bounds,'source':compD['source'],'product':compD['product'],'srcmethod':self.process.params.srcmethod,'srcdata':self.process.params.srcdata}
        self.tascapD['sceneid'] = self.sceneid
        for key in self.TCD:
            if not self.TCD[key]['libendmember']:
                self.imageendmember = True      
        if self.process.params.offset:
            self.GetOffset(processElement)
            for key in self.offsetD:
                self.tascapD['offsetem'] = key
                print 'offset',key,self.offsetD[key]['libendmember']
                if not self.offsetD[key]['libendmember']:
                    self.imageendmember = True
                self.offsetinclude = self.offsetD[key]['include']
        else:
            self.offsetD = False
            self.tascapD['offsetem'] = 'none'          
        #Clean the tc inputs
        tcIdD = {}
        for TC in self.TCD:
            tcid = self.TCD[TC]['tcid']
            tcnr = self.TCD[TC]['tcnr']
            bandname = 'tc%s-%s' %(tcnr,tcid)
            tcIdD[bandname] = {'tcid':TC,'tcnr':tcnr}

        popL = []
        self.tcIdD = tcIdD
        for x,tc in enumerate(self.layerInD):
            if not tc in tcIdD:
                if tc[0:2] == 'tc':
                    popL.append(tc)
                    #bandname = self.layerInD[tc].comp.band
                    nid = 'flipflop%s' %(x)
                    self.TCD[nid] = {'tcid':nid,'tcnr':-99}
                else:
                    self.vi = tc
        print self.tcIdD.keys() 
        print self.layerInD.keys() 
  
        for tc in popL:
            self.layerInD.pop(tc, None) 
        #copy the original compid
        origcompoutD = deepcopy(self.process.compoutD) 

        #Create the outputbnads
        compoutD = {}
        for band in self.bandD:
            prefix = band
            if self.offset and not self.offsetinclude:
                prefix = '%s-%s' %(prefix,'tc0')
            for item in popL:
                prefix = '%s-%s' %(prefix,item.split('-')[0])

            compoutD[band] = deepcopy(self.process.compoutD['*'])
            compoutD[band].band = band
            compoutD[band].prefix = prefix

        self.process.compoutD = compoutD
        self.SetLayersOut(locDate, geoFormatD, compD)
        for band in self.bandD:
            print self.layerOutD[band].FPN
        AllDone = True   
        for key in self.layerOutD:
            if not self.layerOutD[key].Exists():
                AllDone = False
            else:
                print '    already done, registering',self.layerOutD[key].comp.band, self.layerOutD[key].FPN
                self.layerOutD[key].RegisterLayer(self.process.proj.system)
        if not AllDone or self.process.overwrite:
            asnp = True
            self.ProduceLayers()
            for key in self.layerOutD:
                print '     registering',self.layerOutD[key].comp.band, self.layerOutD[key].FPN
                self.layerOutD[key].RegisterLayer(self.process.proj.system)
        #reset the original compoutD
        self.process.compoutD = origcompoutD

    def SetTassCapProcessing(self,processElement,locDate, geoFormatD, compD):
        from copy import deepcopy 
        self.offset = False
        self.GetBands(processElement)
        self.GetTCs(processElement)
        self.imageendmember = False
        self.tascapD = {'bounds':self.process.params.bounds,'source':compD['source'],'product':compD['product'],'srcmethod':self.process.params.srcmethod,'srcdata':self.process.params.srcdata}
        self.tascapD['sceneid'] = self.sceneid
        for key in self.TCD:
            if not self.TCD[key]['libendmember']:
                self.imageendmember = True      
        if self.process.params.offset:
            self.GetOffset(processElement)
            for key in self.offsetD:
                self.tascapD['offsetem'] = key
                if not self.offsetD[key]['libendmember']:
                    self.imageendmember = True
        else:
            self.offsetD = False
            self.tascapD['offsetem'] = 'none'
        #Clean the input names
        popL = []
        for band in self.layerInD:
            if not band in self.bandD:
                popL.append(band)
        for band in popL:
            self.layerInD.pop(band, None) 
        #copy the original compid
        origcompoutD = deepcopy(self.process.compoutD)       
        #Create the outputbands
        compoutD = {}
        for TC in self.TCD:
            tcid = self.TCD[TC]['tcid']
            tcnr = self.TCD[TC]['tcnr']
            compoutD[tcid] = deepcopy(self.process.compoutD['*'])
            compoutD[tcid].band = 'TC%s-%s' %(tcnr,tcid)
            compoutD[tcid].prefix = 'TC%s-%s' %(tcnr,tcid)
            if self.process.params.offset:
                compoutD[tcid].suffix = '%s-%s-%s-%s' %(compD['suffix'],self.process.params.srcmethod,self.process.params.srcdata,self.offset)
            else:
                compoutD[tcid].suffix = '%s-%s-%s-%s' %(compD['suffix'],self.process.params.srcmethod,self.process.params.srcdata,'none')
        self.process.compoutD = compoutD
        self.SetLayersOut(locDate, geoFormatD, compD)
        AllDone = True   
        for key in self.layerOutD:
            if not self.layerOutD[key].Exists():
                AllDone = False
            else:
                print '    already done, registering',self.layerOutD[key].comp.band, self.layerOutD[key].FPN
                self.layerOutD[key].RegisterLayer(self.process.proj.system)
        if not AllDone or self.process.overwrite:
            asnp = True
            self.ProduceLayers()
            for key in self.layerOutD:
                print '     registering',self.layerOutD[key].comp.band, self.layerOutD[key].FPN
                self.layerOutD[key].RegisterLayer(self.process.proj.system)
        #reset the original compoutD
        self.process.compoutD = origcompoutD
                                      
    def GetTCs(self, processElement):
        #Get the trim tags
        self.TCD = {}
        TCTags = processElement.getElementsByTagName('tc')
        #Get the attributes to retrieve
        tagAttrL = ConnProcess.SelectProcessTagAttr(self.process.processid,'process','tc') 
        #Get all the data as a list of dicts
        for TCTag in TCTags:
            TC = XMLelement(TCTag,tagAttrL,'tc',self.process.processid)[0]
            self.TCD[TC['endmember']] = {'tcnr':TC['tcnr'],'tcid':TC['tcid'],'libendmember':TC['libendmember']}
            
    def GetOffset(self, processElement):
        #Get the trim tags
        self.offsetD = {}
        offsetTags = processElement.getElementsByTagName('offset')
        #Get the attributes to retrieve
        tagAttrL = ConnProcess.SelectProcessTagAttr(self.process.processid,'process','offset') 
        for offsetTag in offsetTags:
             band = XMLelement(offsetTag,tagAttrL,'offset',self.process.processid)[0]
             self.offsetD[band['band']] = band
             
    def GetScalefac(self, processElement):
        #Get the trim tags
        self.scalefacD = {}
        scaleTags = processElement.getElementsByTagName('scalefac')
        #Get the attributes to retrieve
        tagAttrL = ConnProcess.SelectProcessTagAttr(self.process.processid,'process','scalefac') 
        for scaleTag in scaleTags:
             band = XMLelement(scaleTag,tagAttrL,'scalefac',self.process.processid)[0]
             self.scalefacD[band['band']] = band
             
        '''     
        offset = XMLelement(offsetTags[0],tagAttrL,'offset',self.process.processid)[0]
        
        
        self.offsetD[offset['endmember']] = {'libendmember':offset['libendmember']}
        if 'include' in offset:
            self.offsetD[offset['endmember']]['include'] = offset['include']
        self.offset = offset['endmember']
        '''
      
    def SetExportToByte(self,processElement,locDate, geoFormatD, compD):
        pp = self.process.params
        #check the palette
        key = self.layerOutD.keys()[0]
        print self.layerOutD[key].comp.palette
        if pp.scalefac:
            pp.maxval =  250 
            pp.minval =  0   
        elif pp.dstmax:
            if pp.dstmax > 250:
                sys.exit('dstmax can not be higher than 250')
            if pp.dstmin < 0:
                sys.exit('dstmin can not be higher than 250')       
            pp.offset = -1*(pp.srcmin)
            pp.scalefac = (pp.dstmax-pp.dstmin)/(pp.srcmax-pp.srcmin) 
            if pp.dstmin > 0:
                pp.offset += pp.dstmin/pp.scalefac
        else:
            sys.exit('exporttobyte requires either scale and offset or min and max')        
        self.ProduceLayers()
                  
class ExtractLayers(LayersToProcess):
    def __init__(self,process,processElement,aD,tD,locationL): 
        """The constructor expects an instance of the composition class and the wrs (1 or 2)."""
        #TGTODO NO CHECK ON PROCESS ESISTING
        LayersToProcess.__init__(self, process) 
        
        for locDate in self.locationDates:
            self.StandardLocationDates()
            done = False
            for key in self.layerInD:
                if not os.path.isfile(self.layerInD[key].FPN):
                    errorstr = 'MISSING layer, skipping extractiong: %s' %(self.layerInD[key].FPN)
                    print errorstr
                    return   
            if self.process.processid in ['extractsoillinePVIPBI','extractsoillineVI']:
                if self.process.processid ==  'extractsoillinePVIPBI': 
                    c = self.layerInD['pbi'].comp
                    metod = 'pvipbidefault'
                    vi = 'pvi'
                elif self.process.processid == 'extractsoillineVI':
                    for key in self.layerInD:
                        if 'vi' in key.lower():
                            vi = key
                    c = self.layerInD[vi].comp
                    metod = processC.compinD.items()[0][0].lower()
                folder = 'endmember'
                band = prefix = '%s-%s-soil' %(metod, self.layerInD['rl'].comp.folder)
                soilcomp = Composition(c.source, c.product, folder, band, prefix, c.suffix, mainpath = c.mainpath,scenes = True, division = 'scenes')
                band = prefix = '%s-%s-veg' %(metod, self.layerInD['rl'].comp.folder)
                vegcomp = Composition(c.source, c.product, folder, band, prefix, c.suffix, mainpath = c.mainpath,scenes = True, division = 'scenes')
                soilcomp.SetExt('csv')
                vegcomp.SetExt('csv')
                KOLLASUFFIX
                self.layerOutD['soil'] = self.SetSystemLayer('soil', soilcomp)
                self.layerOutD['veg'] = self.SetSystemLayer('veg', soilcomp)
                if self.layerOutD['veg'].Exists() and self.layerOutD['soil'].Exists() and not self.process.overwrite:
                    done = True
            if done:
                continue
            print ''
            infostr = '    Extracting soil and veg pixels for %(s)s: path: %(p)d; row: %(r)d; date %(dat)s' %{'s':locDate[2], 'p':locDate[5],'r':locDate[6],'dat':self.acqdate.acqdatestr}
            print infostr
            #read the input data
            for key in self.layerInD: 
                self.layerInD[key].ReadRasterLayer(complete= True, flatten = False, mode='edit', structcode = arrctD)  
            if self.process.processid in ['extractsoillinePVIPBI','extractsoillineVI']:       
                self.ExtractSoilVegCand(aD,vi,metod)
            else:
                exitstr = 'process not defined in ExtractLayers %s',   self.process.processid
                sys.exit(exitstr)
        
    def ExtractSoilVegCand(self,vi,metod):
        from soilline_v70 import CandidateSoilLine, CandidateVIendmembers 
        if self.process.processid == 'extractsoillinePVIPBI':
            sceneD,soilD,vegD = CandidateSoilLine(self,'pvipbidefault')
        elif self.process.processid == 'extractsoillineVI':
            sceneD,soilD,vegD = CandidateVIendmembers(self,vi,metod)
        if soilD:
            ConnEndMember.InsertSearch('soilsearch',sceneD,soilD, self.process.overwrite,self.process.delete)
        if vegD:
            ConnEndMember.InsertSearch('vegsearch',sceneD,vegD, self.process.overwrite,self.process.delete)
        elif self.process.processid == 'extractsoillinePVIPBI':
            ConnEndMember.UnusableScene(sceneD,'toocloudy')
 
class RetrieveEndMembers(LayersToProcess):
    def __init__(self,processC,processElement): 
        """The constructor expects an instance of the composition class and the wrs (1 or 2)."""
        LayersToProcess.__init__(self, processC) 
        from soilline_v70 import RetrivesoilvegEM
        if self.process.processid == 'examinsoillines':
            self.ExamineSoiLines(locationDates)
            return
        #bounds = aD['bounds'] 
        key = processC.compinD.items()[0][0]
        for locDate in self.locationDates: 
            #TGTODO check the LocationDates below
            self.EndMemberLocationDates(self,locDate)  
            if self.skip:
                continue
            self.GetTrimming(processElement)
            print ''
            infostr = '    Extracting spectral endmembers for %(s)s: path: %(p)d; row: %(r)d; date %(dat)s; type:%(t)s' %{'s':locDate[2], 'p':locDate[5],'r':locDate[6],'dat':self.acqdate.acqdatestr,'t':srcmethod}
            print infostr
            FP,FN = os.path.split(self.layerInD['veg'].FPN)
            xmlFN = FN.replace('.csv','.xml')
            emxmlFN = xmlFN.replace('-veg','-endmembers')
            slxmlFN = xmlFN.replace('-veg','-soil')
            emxmlFPN = os.path.join(FP,emxmlFN)
            slxmlFPN = os.path.join(FP,slxmlFN)
            if self.process.processid == 'soilvegendmembersdelete':
                print sceneid,product,srcmethod, srcdata
                pixels = ConnEndMember.CheckSlPixels(sceneid, product,srcmethod,srcdata, aD['slnpixels'])
                print pixels
                BALLE
                if os.path.isfile(emxmlFPN):
                    BALLE
            if os.path.isfile(emxmlFPN) and os.path.isfile(slxmlFPN) and not self.process.overwrite:
                continue
            soilvegEM = RetrivesoilvegEM(self.layerInD['soil'].FPN, self.layerInD['veg'].FPN, aD, self.trimD, self.process.overwrite)
            if soilvegEM:
                soillineD,emparamD,emD, emsampleD, trimD = soilvegEM
                self.SetSceneForEndMember(compin,srcmethod,srcdata,self.process.params.bounds)
                ConnEndMember.InsertSoilLine(self.sceneD,'soilline', soillineD, self.process.overwrite, self.process.delete)
                if trimD:
                    ConnEndMember.InsertSoilLine(self.sceneD,'trimming', trimD, self.process.overwrite, self.process.delete)   
                ConnEndMember.InsertEndMember(self.sceneD, emD, emsampleD, emparamD, self.process.overwrite, self.process.delete)
                
    def GetTrimming(self, processElement):
        trimTags = processElement.getElementsByTagName('trim')
        tagAttrL = ConnProcess.SelectProcessTagAttr(self.process.processid,'process','trim') 
        self.trimD = {}
        for trimTag in trimTags:
            trim = XMLelement(trimTag,tagAttrL,'trim',self.process.processid)[0]
            self.trimD[ trim['bandid'] ] = {'min':trim['min'],'max':trim['max'] }
                
    def ExamineSoiLines(self,locationDates, aD):
        for locDate in locationDates:
            ConnEndMember.ExamineSoilLine(locDate, aD)
            
class Orthogonalize(LayersToProcess):
    def __init__(self,processC,processElement,aD,tD): 
        """The constructor expects an instance of the composition class and the wrs (1 or 2)."""
        LayersToProcess.__init__(self, processC) 
        from soilline_v70 import GramSchmidtTransform
        #bounds = aD['bounds']
        key = processC.compinD.items()[0][0]
        for locDate in self.locationDates:
            self.EndMemberLocationDates(self,locDate)
            if self.skip:
                continue
            DEVELOP

            '''
            skip = False
            self.WhereWhen(locDate)
            self.layerInD = {}
            for key in self.process.compinD:
                c = self.process.compinD[key] 
                sceneid,product = locDate[0],locDate[3]
                srcmethod, srcdata = c.prefix.split('-')[0:2]
                                
                endmembers = ConnEndMember.CheckSceneEndmember(sceneid,product,srcmethod,srcdata,bounds)
                if len(endmembers) == 0:
                    continue                
                comp = [c.source, c.product, c.folder, c.band, c.prefix, c.suffix ]
                if '*' in comp:
                    s = self.systemcomp
                    syscomp = [s.source, s.product, c.folder, c.band, c.prefix, c.suffix]  
                    for x,i in enumerate(comp):
                        if i == '*':
                            comp[x] = syscomp[x]
                    if comp[5] == '*':
                        comp[5] = '_%s' %(locDate[8])
                #TGTODO scenes should not be hardcoded
                compin = Composition(comp[0],comp[1],comp[2],comp[3],comp[4],comp[5], mainpath = c.mainpath, scenes = True, division = 'scenes')
                compin.SetExt('xml')
                emL = self.GetEndMembers(processElement,comp[0])
                #combine the image endmembers and the speclib endmembers
                skipL = []
                for x,row in enumerate(endmembers):
                    for item in emL:
                        if item[0] == row[0] and item[1] == row[1]:
                            skipL.append(x)
                            TEST
                            break
                for x,row in enumerate(endmembers):
                    if not x in skipL:
                        emL.append(row)
                self.GetBands(processElement)
                #Clean the endmembers to only contain the desired items
                tL = []
                for item in emL:
                    if item[0] in self.emD and item[1] in self.bandD:
                        tL.append(item)
                self.SetLayer(compin,self.location,self.acqdate,key)
                if not os.path.isfile(self.layerInD[key].FPN):
                    skip = True
                else:
                    skip = False
                    band = 'eigenvector'
                    if aD['offset']:
                        for key in self.emD:
                            if self.emD[key] == 0:
                                rstr = 'eigen-%s' %(key) 
                                offsetem = key 
                        prefix = comp[4].replace('endmembers',rstr)
                    else:
                        prefix = comp[4].replace('endmembers','eigen')
                        offsetem = False
                    band = 'eigenvector'
                    compout = Composition(comp[0],comp[1],comp[2],band,prefix,comp[5], mainpath = c.mainpath, scenes = True, division = 'scenes')
                    compout.SetExt('xml')
                    layerOut = LandsatLayer(compout,self.location,self.acqdate)
                    layerOut.SetLayerPathOld()                        
                    offsetD, eigenD = GramSchmidtTransform(tL,offsetem,self.emD,self.bandD,layerOut.FPN)
                    if eigenD:
                        self.SetSceneForEndMember(compin,srcmethod,srcdata,bounds)
                        ConnEndMember.InsertEigen(self.sceneD, offsetD, eigenD, self.process.overwrite, self.process.delete)
        '''
                   
    def GetEndMembers(self, processElement,sensor):
        self.emD = {}
        emTags = processElement.getElementsByTagName('endmember')
        tagAttrL = ConnProcess.SelectProcessTagAttr(self.process.processid,'process','endmember') 
        emL =[]
        for emTag in emTags:
            em = XMLelement(emTag,tagAttrL,'endmember',self.process.processid)[0]
            self.emD[em['emid']] = em['order']
            if em['speclib']:
                emT = ConnEndMember.GetEmSpecLib(sensor,em['emid'])
                for em in emT:
                    emL.append(em)
        return emL

class ProcessSpatial(RegionCommon):
    def __init__(self,processC,processElement): 
        """The constructor expects an instance of the composition class and the wrs (1 or 2)."""
        RegionCommon.__init__(self, processC) 
        if self.process.processid == 'convertoshape':
            self.ConvertToShape(processElement)
        else:
            exitstr = 'Unidefined process in ProcessSpatial %s' %(self.process.processid)
            sys.exit() 
                        
    def ConvertToShape(self,processElement):
        #Get the coordinates
        if self.process.ogrtype == 'polygon':
            self.GetPolyFields(processElement)
        else:
            self.GetPtFields(processElement)
        self.GetFieldDefs(processElement)
        self.SelectCoords()
        self.TarLayer()
      
    def GetPolyFields(self,processElement):
        fieldTags = processElement.getElementsByTagName('poly')
        tagAttrL = ConnProcess.SelectProcessTagAttr(self.process.processid,'process','poly') 
        for fieldTag in fieldTags:
            self.fieldD = XMLelement(fieldTag,tagAttrL,'poly',self.process.processid)[0]
            
    def GetFieldDefs(self,processElement):
        self.fielddefL = []
        fieldTags = processElement.getElementsByTagName('fielddef')
        tagAttrL = ConnProcess.SelectProcessTagAttr(self.process.processid,'process','fielddef') 
        for fieldTag in fieldTags:
            self.fielddefL.append(XMLelement(fieldTag,tagAttrL,'fielddef',self.process.processid)[0])
             
    def SelectCoords(self):
        self.recL,self.colL,self.boundsPtL = ConnSpatial.SelectCoords(self.process,self.fieldD,self.fielddefL,ConnRegions)
        
    def TarLayer(self): 
        #pp = self.process.params
        acqdate = AcqDate(self.process.period.datumL[0])
        keycomp = self.process.compoutD.items()[0][0]
        #create the comp
        comp = self.process.compoutD[keycomp]
        #Set the comp format - hardcoded for ROI
        comp.CompFormat({'measure':'N','cellnull':0,'celltype':'vector','scalefac':1,'offsetadd':0,'dataunit':'NA','system':'defreg','masked':'N'})
        #create the region and the layer
        region,layer = self.CreateRegionsLayer(comp, self.process.tarpath, self.process.proj.regionid, acqdate, roi = False)
        #reset the region - TGTODO this is redundant and should be fixed with kwargs
        region.Region(self.process.proj.regionid, self.process.proj.regioncat, masked='U')
        
        #region.Region(self.process.proj.regionid, self.process.proj.regioncat, parentcat=pp.parentcat, regionname=pp.regionname, parentid=pp.parentid, version=pp.version,stratum=pp.stratum,title=pp.title, label=pp.label, masked='U')
        if not layer.Exists() or self.process.overwrite: #or overwrite
            #set projection
            fieldD = {}
            for f in self.fielddefL:
                fieldD[f['name']] = {'name':f['name'], 'type':f['type'],'width':f['width'],'precision':f['precision'],'transfer':f['transfer'],'source':f['source'] }
            layer.CreateAttributeDef(fieldD)
            projection = mj_gis.MjProj()
            projection.SetFromEPSG(4326)
            esriDS, esriLayer = mj_gis.CreateEmptyVectorDS(layer.FPN, layer.fieldDefL, projection.proj_cs, self.process.proj.regionid, self.process.ogrtype) 
            for rec in self.recL:
                fieldDD = {}
                fD = dict(zip(self.colL,rec))
                for f in self.fielddefL:
                    #Create the fielddef for this feature         
                    fieldDD[f['name']] = {'name':f['name'], 'type':f['type'],'width':f['width'],'precision':f['precision'],'transfer':f['transfer'],'source':fD[f['source']] }
                    #fieldDL.append({'name':f['name'],'transfer':f['transfer'],'source':fD[f['source']] })
                fL = []
                for key in fieldDD:
                    fL.append(mj_gis.FieldDef(key,fieldDD[key]))
                #check for crossing the timezone
                if fD['ulx'] > fD['urx'] or fD['llx'] > fD['lrx'] or fD['ulx'] > fD['lrx'] or fD['llx'] > fD['urx']:
                    #determine if the poly belongs to the eastern or westen hemisphere
                    #cheating for now, only for modis
                    if fD['h'] < 18:
                        if fD['ulx'] > 0: fD['ulx'] = self.boundsPtL[0][0]
                        if fD['urx'] > 0: fD['urx'] = self.boundsPtL[0][0]
                        if fD['lrx'] > 0: fD['lrx'] = self.boundsPtL[3][0]
                        if fD['llx'] > 0: fD['llx'] = self.boundsPtL[3][0]
                    else:
                        if fD['ulx'] < 0: fD['ulx'] = self.boundsPtL[1][0]
                        if fD['urx'] < 0: fD['urx'] = self.boundsPtL[1][0]
                        if fD['lrx'] < 0: fD['lrx'] = self.boundsPtL[2][0]
                        if fD['llx'] < 0: fD['llx'] = self.boundsPtL[2][0]
                ptL = ( (fD['ulx'],fD['uly']),(fD['urx'],fD['ury']),(fD['lrx'],fD['lry']), (fD['llx'],fD['lly']) )
                #create geometry
                geom = mj_gis.ShapelyPolyGeom(ptL)
                geom.ShapelyToOgrGeom()
                #create the feature
                feature = mj_gis.ogrFeature(esriLayer)
                feature.CreateOgrFeature(geom, fL)
            #close the dataset
            esriDS.CloseDS()
            layer.RegisterLayer('ancillary')
 
class ProcessVector(RegionCommon):
    def __init__(self,processC,processElement): 
        """The constructor expects an instance of the composition class and the wrs (1 or 2)."""
        RegionCommon.__init__(self, processC) 
        if self.process.processid == 'clipvectortoregion':
            self.ClipVector()
        else:
            exitstr = 'Unidefined process in ProcessSpatial %s' %(self.process.processid)
            sys.exit() 
                        
    def ClipVector(self):
        key = self.process.compinD.items()[0][0]
        acqdate = AcqDate(self.process.period.datumL[0])
        srcregion,srclayer = self.CreateRegionsLayer(self.process.compinD[key], self.process.srcpath, self.process.srcregion, acqdate, roi = False)
        print srclayer.FPN
        if os.path.isfile(srclayer.FPN):
            tarregion,tarlayer = self.CreateRegionsLayer(self.process.compinD[key], self.process.srcpath, self.process.proj.regionid, acqdate, roi = False)
            if not tarlayer.Exists():
                ullat, ullon, urlat, urlon, lrlat, lrlon, lllat, lllon = ConnRegions.SelectRegionExtent(self.process.proj.regionid)
                clip = [min(ullon,lllon), min(lllat,lrlat), max(urlon,lrlon), max(ullat,urlat)]
                gdalcmd = '/Library/Frameworks/GDAL.framework/Versions/1.11/Programs/ogr2ogr -skipfailures'
                gdalcmd = '%(cmd)s -clipsrc %(xmin)f %(ymin)f %(xmax)f %(ymax)f' %{'cmd':gdalcmd, 'xmin': clip[0], 'ymin':clip[1] , 'xmax':clip[2] , 'ymax':clip[3]}
                gdalcmd = '%(cmd)s %(tar)s %(src)s' %{'cmd':gdalcmd, 'tar':tarlayer.FPN, 'src':srclayer.FPN }
                os.system(gdalcmd)
                    
class ProcessLayout:
    '''class for all layout management'''  
    def __init__(self, processC, element, aD):
        self.process = processC
        #direct to subprocess
        if self.process.processid == 'addrasterpalette':
            self.AddRasterPalette(element,aD)
        elif self.process.processid == 'updaterastermeta':
            self.UpdateRasterMeta(aD,locationL)
        else:
            exitstr = 'No process %s under ProcessLayout' %(self.process.processid)
            sys.exit(exitstr) 
    
    def UpdateRasterMeta(self,aD,locationL):
        kwargD = {}       
        if aD['cellnull'] != 5555: kwargD['cellnull'] = aD['cellnull']
        if aD['celltype'] != '': kwargD['celltype'] = aD['celltype']        
        for datum in self.process.period.datumL:
            for compinkey in self.process.compinD:
                comp = self.process.compinD[compinkey]
                comp.SetExt(self.process.tarpath.hdr)
                if aD['palette'] != '': 
                    palette = ConnLayout.SelectPalette(aD['palette'])
                    if len(palette) == 0:
                        exitstr = 'no color entries found for palette: %s' %(aD['palette'])
                        sys.exit(exitstr)
                    #Check that the palette passes
                    testpalette = mj_gis.RasterPalette()
                    testpalette.SetTuplePalette(palette)
                    kwargD['palette'] = palette
                for location in locationL:
                    if not self.process.compinD[compinkey].scenes:
                        region = Location('region')
                        print 'vars',vars(self.process.proj)
                        region.Region(location)
                        layerIn = RegionLayer(comp,region,datum)
                        layerIn.SetRegionPath()
                        if os.path.exists(layerIn.FPN): 
                            mj_gis.ReplaceRasterDS(layerIn.FPN,self.process.tarpath.hdr,**kwargD)
                    else:
                        TILESORSCENES
           
    def AddRasterPalette(self,processElement,aD): 
        colorTags = processElement.getElementsByTagName('setcolor')
        nodeAttrL = ConnProcess.SelectProcessTagAttr(self.process.processid,'process','setcolor')
        cDL = []
        for colorTag in colorTags:      
            cDL.append(XMLelement(colorTag,nodeAttrL,'setcolor',self.process.processid)[0])
        ConnLayout.ManageRasterPalette(self.process,aD['palette'], cDL)
                                                                                                                                             
def BoolTag(item):
    if item == '': 
        return False #i.e. no item given, assume False
    if item[0].lower() == 'n' or item.lower() == 'false':
        return False
    elif item[0].lower() == 'y' or item.lower() == 'true':
        return True
    else:
        exitstr = 'Can not resolve boolean node %(s)s' %{'s':item}
        sys.exit(exitstr)

def BoolTagNumerical(item):
    if item == None or item == '':
        return False
    if item == '-99' or item[0].lower() == 'n' or item.lower() == 'false':
        return False
    else:
        return int(item)    
    
def XMLUserProject(tag):        
    userid = tag.getAttribute('userid')
    pswd = tag.getAttribute('pswd')
    projectid = tag.getAttribute('projectid')
    tractid = tag.getAttribute('tractid').lower()
    siteid = tag.getAttribute('siteid').lower()
    plotid = tag.getAttribute('plotid').lower()
    system = tag.getAttribute('system').lower()
    upC = UserProject(userid,pswd,system,projectid)
    return upC,tractid,siteid,plotid

def XMLelement(element,tagAttrL,itemStr,processid):
    '''The main XMLelement reader for all db defined elements
    '''
    attrValueL = []; attrParamL = []; tagValueL = []; tagParamL = []
    for tagAttr in tagAttrL:
        #tagAttr: tagorattr, parameter, paramtyp, required, defaultvalue  
        if tagAttr[0][0].upper() == 'A':
            value = element.getAttribute(tagAttr[1])
            if value == '' and tagAttr[3].upper() == 'Y':
                if not processid == 'addsubproc':
                    print processid
                    exitstr = 'The required attribute "%s" is missing in the <%s> element for process %s' %(tagAttr[1], itemStr ,processid)
                    sys.exit(exitstr)
            elif value == '' and tagAttr[4] != '':
                value = tagAttr[4]
            if tagAttr[2][0:3].lower() in ['tex','str']:
                if value == '':
                    value = ''
                else: value = str(value)
            elif tagAttr[2][0:3].lower() == 'int':
                try:
                    value = int(value)
                except:
                    try:
                        value = int(float(value))
                    except:
                        errorstr = 'The attribute "%s" must be an integer, got a string %s' %(tagAttr[1], value, )
                        sys.exit(errorstr)
            elif tagAttr[2][0:5].lower() in ['float','real']:                           
                try:
                    value = float(value)
                except:
                    errorstr = 'The attribute "%s" must be a real number, got a string %s' %(tagAttr[1], value)
                    sys.exit(errorstr)
            elif tagAttr[2][0:4].lower() == 'bool':
                if value[0].lower() == 'n' or value.lower() == 'false':
                    value = False
                elif value[0].lower() == 'y' or value.lower() == 'true':
                    value = True
                else:
                    errorstr = 'The attribute "%s" must be boolean (y/n or true/false), got something else %s' %(tagAttr[1], value)
                    sys.exit(errorstr)                
            attrParamL.append(tagAttr[1].lower()) 
            attrValueL.append(value)             
        else:
            tags = element.getElementsByTagName(tagAttr[1])
            if len(tags) == 0 and tagAttr[3].lower() == 'y':
                exitstr = 'The required tag element <%s> is missing in <%s>' %(tagAttr[1],processid)
                sys.exit(exitstr)
            elif len(tags) == 0: #use default value, even if empty
                tagParamL.append(tagAttr[1].lower())
                tagValueL.append(tagAttr[4])              
            elif len(tags) >= 1:
                tagParamL.append(tagAttr[1].lower())
                tagValueL.append(tags[0].firstChild.nodeValue)   
    #zip params and values to a dict
    attrParamD = dict(zip(attrParamL,attrValueL))
    tagParamD = dict(zip(tagParamL,tagValueL))
    return attrParamD,tagParamD
             
def XMLprocessElement(processTag):
    #Reads the default process parameters at start
    processId = processTag.getAttribute('processid')
    version = processTag.getAttribute('version')
    overwriteTag = processTag.getElementsByTagName('overwrite')
    if len(overwriteTag) == 0:
        overwrite = False
    else:
        overwrite = BoolTag(overwriteTag[0].firstChild.nodeValue )
    deleteTag = processTag.getElementsByTagName('delete')
    if len(deleteTag) == 0:
        delete = False
    else:
        delete = BoolTag(deleteTag[0].firstChild.nodeValue )
    return version, processId, overwrite, delete 

def XMLperiodElement(parentidNode):
    periodElements = parentidNode.getElementsByTagName('period')
    if len(periodElements) > 0:
        #This is fake, the parrent is not process, but dom, but it has no effect as the period node only exists at startup
        tagAttrL = ConnProcess.SelectProcessTagAttr('periodicity','process','period')
        return XMLelement(periodElements[0],tagAttrL,'period','dom')[0]
        #Get the processing tags
    else:
        return False
                    
def ReadXML(xmlFN): 
    locationL = []  
    printstr = '    xmlFN: %s' %(xmlFN)
    print printstr
    dom = minidom.parse(xmlFN)   
    #get the userproject tag     
    upTag = dom.getElementsByTagName('userproject')
    if len(upTag) > 0:
        upC,tractid,siteid,plotid = XMLUserProject(upTag[0]) #always only 1 tag , but also the tractid,siteid,plotid need to be set      
        if upC.system == 'system':
            locationL = ['globe']; 
            upC.SetSystemSession()
            
        else:
            upC.SetSession(tractid,siteid,plotid)
    else:
        upC = False; 
        locationL = []
    #Set the path
    pathElements = dom.getElementsByTagName('path')
    if len(pathElements) > 0:
        tagAttrL = ConnProcess.SelectProcessTagAttr('path','process','path')
        pathD = XMLelement(pathElements[0],tagAttrL,'period','dom')[0]
    
    #Get the period setting for the whole process
    periodD = XMLperiodElement(dom)
    
    processElements = dom.getElementsByTagName('process')
    #Loop over the processes
    for processElement in processElements:  
        #Get the process elements common stuff for all processes
        version, processId, overwrite, delete = XMLprocessElement(processElement)        
        #Set the rootprocessid
        rootrec = ConnProcess.SelectRootProcess(processId) 
        if rootrec == None:
            exitstr = 'Process: %s, does not exist' %(processId)
            sys.exit(exitstr)
        printstr = '    Process: %s (%s)' %(processId, rootrec[0]) 
        print printstr
        if not rootrec:
            exitStr = 'Subprocess %s is not defined in db' %(processId)
            sys.exit(exitStr)
        #reset period if a periodicity is set for this particular process
        periodElements = processElement.getElementsByTagName('srcperiod')
        if len(periodElements) > 0:
            #The AttributeList if the same as for the overall period 
            perAttrL = ConnProcess.SelectProcessTagAttr('periodicity','process','period')
            if len(perAttrL) == 0:
                sys.exit('The period must be set')
            procPeriodD = XMLelement(periodElements[0],perAttrL,'period','dom')[0]
        else:
            procPeriodD = periodD
        processC = Process(rootrec[0],processId,version, overwrite, delete, upC, procPeriodD, pathD)
        #Get and set the standard entries 
        processC.GetSetStandardEntries(processElement)
        #Get the process parameters for this process
        tagAttrL = ConnProcess.SelectProcessTagAttr(processId,'process','parameters') 
        if len(tagAttrL) > 0:
            #Get the parameter tag - must exist in all processes
            paramTags = processElement.getElementsByTagName('parameters')
            if len (paramTags) == 0:
                exitstr = 'EXITING: No parameter tag fround for process: %s' %(processId)
                print exitstr
            #Get the parameters for this process
            procAttrParamD,tagAttrParamD = XMLelement(paramTags[0],tagAttrL,'parameters',processId)
        else:
            procAttrParamD = tagAttrParamD = {}
        processC.SetProcessParams(procAttrParamD, tagAttrParamD)
        if processC.period.datumL[0]['acqdatestr'] in ['varying','allscenes']:
            if len(processC.compinD) > 0 and hasattr(processC, 'srcpath'):
                key = processC.compinD.items()[0][0]
                processC.compinD[key].SetCompPath(processC.proj.defregid)
                processC.period.FindVaryingTimestep( processC.compinD[key].FP )
                processC.compinD[key].FP

        if rootrec[0] == 'manageprocess':
            ProcessProcess(processC,processElement)   
        elif rootrec[0] == 'ManageUser':
            ProcessUser(processC,processElement)
        elif rootrec[0] == 'ManageRegion':
            ProcessRegion(processC)
        elif rootrec[0] == 'Ancillary':
            processC.GetAncillaryImportEntries(processElement,procAttrParamD)
            ProcessAncillary(processC,procAttrParamD)
        elif rootrec[0] == 'ManageProject':
            ProcessProject(processC)
        elif rootrec[0] == 'LayoutProc':
            ProcessLayout(processC, processElement)
        elif rootrec[0] in ['MultiToSingle','VegetationIndex','ExtractLayerData','LandsatProc']:
            if rootrec[0] == 'LandsatProc':
                ProcessLandsat(processC,processElement,locationL)
            elif rootrec[0] == 'ExtractLayerData':
                #procAttrParamD['bounds'] = 'wholescene'
                ExtractLayers(processC,processElement,locationL)
            else:
                ProcessLayers(processC,processElement,locationL)
        elif rootrec[0] == 'RetrieveEndMembers':
            RetrieveEndMembers(processC,processElement)
            
        elif rootrec[0] == 'Orthogonalize':
            Orthogonalize(processC,processElement)
            
        elif rootrec[0] == 'MODISProc':
            #ProcessMODIS(processC,processElement,locationL) 
            ProcessMODIS(processC,processElement)    
        elif rootrec[0] == 'specimen':
            if processId == 'importspecimen':
                processC.GetAncillaryImportEntries(processElement)
            ProcessSpecimen(processC,processElement)
            
        elif rootrec[0] == 'ManageSqlDumps':
            ProcessSqlDumps(processC)
        elif rootrec[0] == 'Spectral':
            ProcessLayers(processC,processElement,locationL)
        elif rootrec[0] == 'Export':
            ProcessLayers(processC,processElement,locationL)
        elif rootrec[0] == 'SpatialDB':
            ProcessSpatial(processC,processElement)
        elif rootrec[0] == 'VectorProcess':
            ProcessVector(processC,processElement)
        elif rootrec[0] == 'MapCalc':
            ProcessLayers(processC,processElement,locationL)
        else:
            exitstr = 'Root process not defined in script %s' %(rootrec[0])
            sys.exit(exitstr)

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
  
def StartUp():
    global ConnPostGres, ConnProcess, ConnUserLocale, ConnLandsat, ConnRegions, ConnMODIS, ConnAncillary, ConnSpecimen, ConnUserLocale, ConnLayout, ConnSqlDump, ConnTopo, ConnComp, ConnEndMember, ConnSpatial, arrctD, npctD, usgsctRevD, gdalofD
    import psycopg2_process_v71 as psycopg2process
    import psycopg2_landsat_v70 as psycopg2landsat
    import psycopg2_modis_v71 as psycopg2modis
    import psycopg2_ancillary_v70 as psycopg2ancillary
    import psycopg2_userlocale_v71 as psycopg2userlocale
    import psycopg2_specimen_v70 as psycopg2specimen
    import psycopg2_regions_v71 as psycopg2region
    import psycopg2_layout_v70 as psycopg2layout
    import psycopg2_sqldump_v70 as psycopg2sqldump
    import psycopg2_topography_v70 as psychopg2topo
    import psycopg2_comps_v70 as psychopg2comp
    import psycopg2_endmember_v70 as psycopg2endmember
    import psycopg2_spatial_v70 as psycopg2spatial
    ConnSpatial = psycopg2spatial.Connect('spatial')
    ConnEndMember = psycopg2endmember.Connect('endmember')
    ConnProcess = psycopg2process.Connect('process')
    ConnLandsat = psycopg2landsat.Connect('landsat')
    ConnMODIS = psycopg2modis.Connect('modis')
    #ConnUserLocale = psycopg2project.Connect()
    ConnAncillary = psycopg2ancillary.Connect('ancillary')
    ConnUserLocale = psycopg2userlocale.Connect('userlocale')
    ConnSpecimen = psycopg2specimen.Connect('specimen')
    ConnRegions = psycopg2region.Connect('regions')
    ConnLayout = psycopg2layout.Connect('layout') 
    ConnSqlDump = psycopg2sqldump.Connect('layout')
    ConnTopo = psychopg2topo.Connect('topography')
    ConnComp = psychopg2comp.Connect('')

    arrctD = {}; npctD = {}; usgsctRevD = {}; gdalofD = {}
    celltypes = ConnProcess.SelectCellTypes()
    for ct in celltypes:
        arrctD[ct[0]] = ct[1]
        npctD[ct[0]] = ct[1]
        usgsctRevD[ct[3]] = ct[0]   
    gdalofs = ConnProcess.SelectGDALof()
    for of in gdalofs:
        gdalofD[of[0]] = of[2]

def InstallSetUp():
    '''Installs all the process definition 
    '''
    '''General''' 
    '''Installs the periodicity and path readining interfaces'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/general/xml/periodicity_v70.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/general/xml/path_v70.xml')
    
    '''UserLocale '''
    '''Installs the user management readining interface'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/userlocale/xml/manageuser_v70.xml')
    '''Installs the project management readining interface'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/userlocale/xml/manage_project_v70.xml')
    '''Installs the region management readining interface'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/userlocale/xml/manageregion_v70.xml')
    
    '''Ancillary'''
    '''Installs the ancillary data management readining interface'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/ancillary/xml/ancillaryprocess_v70.xml')
    
    '''Landsat'''
    '''Installs the landsat management readining interface'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/landsat/xml/landsatprocess_v70.xml')
    '''Installs the landsat template scenes to the db - any new kind of scene must be added'''
    
    '''MODIS'''
    '''Install all the MODIS specific processing '''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/modis/xml/modisProcess_v70.xml')
    '''Insert all the records for the MODIS tile coords using math'''
    
    '''Define entries for specimen imports'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/specimen/xml/specimenprocess_v70.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/specimen/xml/specimen-csv-process_v70.xml')

    '''managesqldumps_vXX_sql.xml adds the process for exporting and importing sql dumps'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/sqldumps/managesqldumps_v70.xml')
    
    '''vegindexprocesses_vXX.xml installs the interface to basin soil and veg indexing'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/soilvegindex/xml/vegindexprocesses_v70.xml')
    
    ''' endmember_processes_vXX.xml installs the interface for retrieving spectral end members from soil line and veg index'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/endmember/xml/endmember_processes_v70.xml')
    
    ''' spectral_vXX.xml installs the interface for some spectral processes'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/spectral/xml/spectralprocess_v70.xml')
    
    '''palettes'''
    '''Define entries for layout definitions'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/layout/xml/layoutprocess_v70.xml') 
    
    '''
    MORE:
    #Create landsat and MODIS regions for default regions
    load MODIS datapool
    loop over existing MODIS
    loop over existing LANDSAt
    loop over existing ancillay
    loop over regions and connected scenes
    WRS data as ancillary
    '''
      
def InsertRecodsSetUp():

    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/landsat/xml/templatescenes_v70.xml')
    '''Installs the landsat template bands to the db - any new kind of band must be added'''

    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/landsat/xml/templatebands_v70.xml')
    '''Landsat bulk meta links'''

    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/landsat/xml/managebulkmetaurl_v70.xml')
    '''Define entries for the landsat bulk meta files'''

    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/landsat/xml/definebulkmetaurl_v70.xml')
    
    '''Default regions - must be done before importing ancillary'''

    '''Adds region categrories to the db'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/region/xml/add_region_categories_v70.xml')

    '''Adds global default region categrories to the db'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/region/xml/add_arbitrary_default_regions_v70.xml')

    '''Import default ROI - must be done before setting regions from vector data'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/ancillary/xml/ancillary-import-kartturROI_2014.xml')

    '''Adds countries, subregions and continents to the db'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/region/xml/add_default_regions_from-vector_v70.xml')
    
    '''Enter the defualt palettes'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/layout/xml/createpalettes_v70.xml')
    
    #MOVE OR JUST INCLUDE AS DEFAULT AND SKIP AS PROCESS
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/modis/xml/modisTileCoords_v70.xml')
    
def Initialize():
    import mj_initialize_v70 as mj_ini
    xmlIniL = []
    
    '''schema_vXX_sql.xml installs the default database schemas'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/general/sql/schema_v70_sql.xml')
    
    '''general_processes_vXX_sql.xml installs the tables for handling paths and processes and the core process 
    handling all other process definitions'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/general/sql/general_processes_v70_sql.xml')
    
    '''general_GDAL_vXX_sql.xml installs the tables that defines the different cell types and file types that the system can handle'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/general/sql/general_GDAL_v70_sql.xml')
    
    '''compositions_vXX_sql.xml installs the table that define all layers, called compositions'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/general/sql/compositions_v70_sql.xml')
    
    '''usersvXX_sql.xml installs the table that hold all the sytem users'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/userlocale/sql/users_v70_sql.xml')
    
    '''userlocale_vXX_sql.xml installs the table that hold all the sytem regions'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/region/sql/regions_v70_sql.xml')
    
    '''uprojects_vXX_sql.xml installs the table that defines user projects and project types'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/userlocale/sql/projects_v70_sql.xml')
    
    '''ancillary_vXX_sql.xml installs the table that defines ancillary data sources (piles), compositons and layers etc'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/ancillary/sql/ancillary_v70_sql.xml')
    
    '''landsat_scenes_bands_vXX_sql.xml installs the tables for landsat scenes, bands and masks'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/landsat/sql/landsat_scenes_bands_v70_sql.xml')
    
    '''landsat_templates_vXX_sql.xml installs the landsat template table'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/landsat/sql/landsat_templates_v70_sql.xml')
    
    '''usgs_landsat_meta_vXX_sql.xml installs the core landsat meta tables, the columns are installed later'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/landsat/sql/usgs_landsat_meta_v70_sql.xml')
    
    '''modis_template_vXX_sql.xml installs the modis template table, and adds all records for the MODIS products in use'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/modis/sql/modis_template_v70_sql.xml')
    
    ''' modis_scenes_bands_vXX_sql.xml adds both the table for holding all scenes available at the datapool as well as the tables
    for local modis data tile holdings'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/modis/sql/modis_scenes_bands_v70_sql.xml')
    
    '''modis_regions_vXX_sql.xml adds the table for linking modis tiles to tracts and sites'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/modis/sql/modis_regions_v70_sql.xml')
    
    '''modis_regions_vXX_sql.xml adds the table for modis tile coordinates'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/modis/sql/modistilecoords_v70_sql.xml')
    
    '''specimen_vXX_sql.xml adds the table for ground sampled data'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/specimen/sql/specimen_v70_sql.xml')
    '''specimen_satdata_vXX_sql.xml adds the table for linking sat data to sample points'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/specimen/sql/specimen_satdata_v70_sql.xml')
    
    '''layout_vXX_sql.xml adds the table for layout'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/layout/sql/layout_v70_sql.xml')
    
    '''topo_vXX_sql.xml adds the db for point elevation data'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/topography/sql/topo_v70_sql.xml')

    '''tsoilline_vXX_sql.xml adds the db for spectral endmembers and soil lines'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/endmember/sql/endmember_v70_sql.xml')
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/endmember/sql/speclib_v70_sql.xml')
    
    '''superuserprojs_vXX_sql.xml adds the superusers of the system,
    NOTE - THE XML FILE MUST BE EDITED TO SET THE PREFERRED SUPER USERS'''
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/userlocale/sql/superuserprojs_v70_sql.xml')
    ''' Same as above but as strand alone'''
    
    
    #xmlIniL = ['/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/soilline/sql/speclib_v70_sql.xml']
    xmlIniL = []
    
    #xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/specimen/sql/specimen_satdata_v70_sql.xml')
    xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/modis/sql/modis_template_v70_sql.xml')
    #xmlIniL.append('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/general/sql/compositions_v70_sql.xml')
    psycopg2ini = mj_ini.Connect()
    #Create the processchain schema
    #psycopg2ini.CreateSchema('process')
    #Insert the tables of the schem process
    for xml in xmlIniL:
        psycopg2ini.ReadSqxXml(xml)
  
def ImportAncillary():
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-GLWD.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-gghydro.xml')

    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-stillwellmonthly.xml')
    
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-stillwellannual.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-matthews-fung.xml')

    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-worldclim_v20.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-worldclim_v14.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-GSHHS.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-GPWv3.xml')

    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-GPWv3_2000-2015.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-GPWv4.xml')
    
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-GlcShare.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-ESA-GlobCover.xml')
    ##e00 - not complete yet
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-olson-veg.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-unep-wilderness.xml')
    
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-IUCN.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-download-CHIRPS.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-ShareGeo-political.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-USGS-WRS.xml')
    #TRMM 
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-3B43v7_1998-1999.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-3B43v7_2000-2010.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-3B43v7_2010-2016.xml')
    #OSM
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/ancillary/xml/ancillary-import-OSM.xml')
     
def AddUserProject():
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/userlocale/xml/add_user.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/userlocale/xml/add_user_project-region.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/userlocale/xml/add_user_project-region_tg.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/userlocale/xml/add_userproject.xml')
    '''Not public
    '''
    '''CzechTerra data'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/specimen/xml/specimen-import-CZterra2.xml')  
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/specimen/xml/specimen-todb-CZterra.xml')
    
    '''DTU topographic data'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/topography/xml/topo-import-DTU-CryoSat.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/topography/xml/DTUtopocsvtodb_v70.xml') 
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/topography/xml/topo-to-spatial_DTUtcryosat.xml')
     
def BackupDB(complete, regionswrs,landsatmeta):
    if complete:
        ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/sqldumps/backup_db_sqldump_v70.xml')  
    else:
        if regionswrs:
            ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/sqldumps/backup_regionswrs_sqldump_v70.xml')
        if landsatmeta:
            ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/sqldumps/backup_landsat-meta_sqldump_v70.xml') 
  
def CopyDBfromBackup(complete, regionswrs,landsatmeta):
    if complete:
        ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/sqldumps/copy_db_sqldump_v70.xml')
    else:
        if regionswrs:
            ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/sqldumps/copy_regionswrs_sqldump_v70.xml')
        if landsatmeta:
            ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/sqldumps/copy_landsat-meta_sqldump_v70.xml')

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
    '''
    The very first time the Initialize() command below must be run to set up the postgres db and install the process that
    handles all the process setup, as well as some default stuff.
    '''
    #Initialize() #Only use at first startup - creates the db and the core process that handles all other process definitions

    StartUp() #Link all the python scripts and some default databases for format translations, must be run at stratup each time
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/userlocale/xml/add_user_project-region_karttur.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/vector/xml/vectorprocess_v70.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/vector/xml/clip_coastline_trmm_v70.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/modis/xml/explodelmodis_v70.xml')
    #BALLE
    #InstallSetUp() #Only use at first startup - installs the process interfaces
    #InsertRecodsSetUp() #Only use at first startup - Fills the database with basic information,
    #ImportAncillary() #Only use at first startup - imports some open source ancillary datasets
    #CopyDBfromBackup(False, True, True) #Installs the db records for regionswrs and landsatmeta
    #AddUserProject() 

    #LandsatData() #Landsat Data organizes and explodes any downloaded landsat data and then checks the entire lakdsat library
    #TGTODO include LandsatDB in the above, use args, kwargs to steer
    #LandsatDB()
    
    ''' userlocale'''
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/userlocale/xml/add_user_project-region_tg.xml')
    ''' temp'''
    '''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/specimen/xml/specimenprocess_v70.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/specimen/xml/SpecimenSRFI_XML_v70.xml')

    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/specimen/xml/SpecimenSoilLineXML_v70.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/specimen/xml/SpecimenSoil_v70.xml')
    BALLE
    '''
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/userlocale/xml/add_user_project-region_karttur.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/region/xml/add_arbitrary_default_regions_v70.xml')
    
    '''end temp '''

    '''Backup - backs up either the complete db, or selected parts, later the backups can be used to restore the db'''
    #BackupDB(True, False, False)
    #TGTODO change to kwargs

    '''PROCESSES'''
    '''UserLocale '''

    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/userlocale/xml/add_user_rasterregions.xml')    
    
    '''LAYOUT'''
    '''Update lyaout (cellnull and color ramp) for selected datasets'''
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/layout/xml/updaterasterlayout_v70.xml')

    '''landsat'''
    
    #Download specified bulkmeta files to specified path
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/landsat/downloadbulkmetaurl_v70.xml')
       
    '''MODIS processing'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/mapcalc/xml/mapcalcprocesses_v70.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/imagecalc/xml/image_fgbg_transform_v70.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/imagecalc/xml/image_TWI_percent_v70.xml')
    FJUN
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/imagecalc/xml/image_linear_transform_v70.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/imagecalc/xml/image_fgbg_transform_v70.xml')
    STOP
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/imagecalc/xml/image_linear_transform_v70.xml')
    STOP
    
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/modis/xml/modisProcess_v70.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/modis/xml/checkmodisscenes_v70.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/modis/xml/downloaddatapool_pe_v70.xml')
    STOP
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/modis/xml/explodelmodis_v70.xml')
    #MODIS specific processes
    
    #Load tile data downloaded from the USGS Data pool
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/modis/xml/loadMOD8dayDataPoolXML_v70.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/modis/xml/loadMYD8dayDataPoolXML_v70.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/modis/xml/loadMCD8dayDataPoolXML_v70.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/spatialdb/xml/spataldb_process_v70.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/spatialdb/xml/modistile_to_shape_v70.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/userlocale/xml/manageregion_v70.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/region/xml/regions-modtiles_v70.xml')

    BALLE
    
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/modis/xml/modisProcess_v70.xml')
    #
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/modis/xml/checkMODISbands_v70.xml')
    STOP
    #ReadXML('/Users/thomasg/Dropbox/projects/modis2017/xml/loadMYD8dayDataPoolXML_v70.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/modis2017/xml/loadMCD8dayDataPoolXML_v70.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/modis2017/xml/loadMOD44BDataPoolXML_v70.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/modis2017/xml/loadMCD12Q1DataPoolXML_v70.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/modis2017/xml/downloadMCD8dayDataPoolXML_v70.xml')
    
    #Check MODIS data
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/modis/checkmodis_v70.xml')
    #ReadXML('//Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/modis/modisregion_v70.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/modis2017/xml/checkMODIS_v70.xml')
 
    #ReadXML('/Users/thomasg/processXML/metadefXML_v70.xml')
    #ReadXML('/Users/thomasg/processXML/templateXML_v70.xml')
    #ReadXML('/Users/thomasg/processXML/projectXML_v70.xml')
    #ReadXML('/Users/thomasg/processXML/LandsatAccessXML_v70.xml')
    #ReadXML('/Users/thomasg/processXML/orglandsatXML_v70.xml')
    #ReadXML('/Users/thomasg/processXML/userXML_v70.xml')
    #ReadXML('/Users/thomasg/processXML/NDVIXML_v70.xml')
    
    '''Vegetation processing''' 
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/vegindex/landsatPVIPBIXML_v70.xml')
    
    '''Ensmember processing'''
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/endmember/xml/LandsatSoilLineXML_v70.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/endmember/xml/Endmember_OrthogonalizationXML_v70.xml')

    ''' Spectral processing'''
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/spectral/xml/spectralprocess_v70.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/spectral/TassCap_v70.xml')
    #ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/spectral/InverseTassCap_v70.xml')

    '''Export Processing'''
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/layout/xml/createpalettes_v70.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/setup/export/xml/ExportToByte_v70.xml')
    ReadXML('/Users/thomasg/Dropbox/projects/karttur_gis_v70/processes/export/ExportTCToByte_v70.xml')

    
    STOP
    
    '''Ancillary Processing'''
    
    '''MORE THINGS TO BE DONE
    Create psql routines for complete saving and recreation of complete database
    ROUTINE FOR IMPORTING SPECIMEN DATASTER  TO USER AND REGION LIKE ANCILLARY SEPARATE FROM ORGANSIZEANCILLARY
    ORGANIZE vs IMPORT vs toDB is unclear
    '''