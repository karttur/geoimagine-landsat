# geoimagine-landsat

Karttur Geoimagine landsat python project

## Introduction

Karttur's GeoImagine Framework is an attempt for semi-automated processing of spatial data. 
The Landsat package contains the processing for handling landsat specific processing (search, download, explode, organize etc).

- \_\_init.py\_\_
- landsat.py
- version.py

### landsat.py

gis.py is an older version, but that is still called by some other GeoImagine Framework packages.

#### GeoImagine dependencies

geoimagine.gis.mj\_gis\_v80
geoimagine.zipper.explode
geoimagine.support.karttur_dt
geoimagine.kartturmain
geoimagine.sentinel.gml\_transform

#### Classes

- LandsatComposition
- LandsatTile(LayerCommon)
- ProcessLandsat