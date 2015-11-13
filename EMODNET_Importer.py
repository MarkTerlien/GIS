#! /usr/bin/python

""" Function to import survey into database
"""

# Standard library imports
import os
import sys
import time
import logging
import xml.dom.minidom

# Related third party imports
import cx_Oracle
import pylab
from easygui import *
from osgeo import ogr

# Module name
MODULE_NAME = "DTM Import"

# DB connect Parameters
DB_USER_SOURCE       = "DB_USER_SOURCE"
DB_PASSWORD_SOURCE   = "DB_PASSWORD_SOURCE"
DB_TNS_SOURCE        = "DB_TNS_SOURCE"

# Database connection parameter values
PARAMETER_LIST_VALUE = {}
PARAMETER_LIST_VALUE [ DB_USER_SOURCE ]     = "sens"
PARAMETER_LIST_VALUE [ DB_PASSWORD_SOURCE ] = "senso"
PARAMETER_LIST_VALUE [ DB_TNS_SOURCE ]      = "192.168.1.20/emodnet"

# Product types
CONTOURS       = "Contours (DEPCNT and DEPARE)"
SPOT_SOUNDINGS = "Spot soundings (SOUNDG)"

# Product type list
PRODUCT_TYPE_LIST = {}
PRODUCT_TYPE_LIST [ CONTOURS ]       = 811
PRODUCT_TYPE_LIST [ SPOT_SOUNDINGS ] = 812

# Menu options
IMPORT_DTM          = "Import DTM"
IMPORT_TILE         = "Import tile shape"
DEFINE_PRODUCT      = "Define product"
SHOW_PRODUCT_SERIES = "Show product series"
DEFINE_COVERAGE     = "Define coverage"
SUBMIT_ORDER        = "Submit order"
GET_PRODUCT_FILE    = "Get product file"
DELETE_PRODUCT_S    = "Delete product series"
IMPORT_EMODNETGRID  = "Import EMODNET grid"
IMPORT_IM           = "Import IM"
COMMIT              = "Commit"
ROLLBACK            = "Rollback"
EXIT                = "Exit"

# Menu options dictionary
MENU_OPTIONS = {}
MENU_OPTIONS [ IMPORT_DTM ]          = "Import DTM"
MENU_OPTIONS [ IMPORT_TILE ]         = "Import Tile shape"
MENU_OPTIONS [ DEFINE_PRODUCT ]      = "Define product series"
MENU_OPTIONS [ SHOW_PRODUCT_SERIES ] = "Show product series"
MENU_OPTIONS [ DEFINE_COVERAGE ]     = "Define coverage tiles"
MENU_OPTIONS [ SUBMIT_ORDER ]        = "Submit order"
MENU_OPTIONS [ GET_PRODUCT_FILE ]    = "Get product file"
MENU_OPTIONS [ DELETE_PRODUCT_S ]    = "Delete product series"
MENU_OPTIONS [ IMPORT_EMODNETGRID ]  = "Import EMODNET grid"
MENU_OPTIONS [ IMPORT_IM ]           = "Import IM"
MENU_OPTIONS [ COMMIT ]              = "Commit"
MENU_OPTIONS [ ROLLBACK ]            = "Rollback"
MENU_OPTIONS [ EXIT ]                = "Exit"

# Logging levels
LOG_LEVEL = 'info'
LOGLEVELS = {'debug'   : logging.DEBUG,
             'info'    : logging.INFO,
             'warning' : logging.WARNING,
             'error'   : logging.ERROR,
             'critical': logging.CRITICAL}

# Object class ID
AGENCY_CLASS_ID         = 214
IM_CLASS_ID             = 236
CM_CLASS_ID             = 263
USER_CLASS_ID           = 311
PRODUCT_SERIES_CLASS_ID = 321
PRODUCT_CLASS_ID        = 322
PROD_EDITION_CLASS_ID   = 324
PRODUCT_ORDER_CLASS_ID  = 325
PROD_DOWNLOAD_CLASS_ID  = 569
CM_SOURCE_CLASS_ID      = 806
IM_SOURCE_CLASS_ID      = 807
EXPORT_PARAM_CLASS_ID   = 808
CONTOURS_CLASS_ID       = 811
SPOTS_CLASS_ID          = 812
SHAPE_CLASS_ID          = 813
DTM_CLASS_ID            = 822
TILE_CLASS_ID           = 823
MB_CLASS_ID             = 825

# Dimensions
MINX = "minx"
MAXX = "maxx"
MINY = "miny"
MAXY = "maxy"
MINZ = "minz"
MAXZ = "maxz"
NOPS = "nrofpoints"

# Attributes
ID   = "Id"
NAME = "Name"

# Output file format
SHAPE = 814

# Geodetic parameters
WGS84 = 105044
LAT   = 86

# Product type export
PRODUCT_TYPE = 267731 # Export products (808)

# Product series sources
IM = "Individual model"
IM_SOURCE_TABLE = "SDB_INDIVIDUALMODEL"
IM_SOURCE_GEOM  = "SYS_GEOM001"
IM_SELECT_ID    = "ID"
CM = "Continuous model"
CM_SOURCE_TABLE = "SDB_COOKIE"
CM_SOURCE_GEOM  = "SYS_GEOM501"
CM_SELECT_ID    = "SYS502"
 
# Tile/coverage para,eters
TILE_NAME  = "Tile name"
LL_X       = "Lower left X (decimal degrees)"
LL_Y       = "Lower left Y (decimal degrees)"
TILE_SIZE  = "Tile size (degrees)"

# File column product order to store file
FILE_COL = "SYS012"

#########################################
# GUI functions
#########################################

def gui_start ( DbConnection ) :
    """Function to build gui"""
    logger.info("Build main GUI")
    while True :
        title = "Emodnet"
        msg   = "Make your choice"
        options = [ MENU_OPTIONS [ IMPORT_DTM ], MENU_OPTIONS [ IMPORT_TILE ], MENU_OPTIONS [ IMPORT_EMODNETGRID ], MENU_OPTIONS [ IMPORT_IM ] ,MENU_OPTIONS [ COMMIT ] , MENU_OPTIONS [ ROLLBACK ], MENU_OPTIONS [ EXIT ]  ]
        #reply=buttonbox(msg,title,options,image='PSV.gif')
        reply=buttonbox(msg,title,options)
        if reply == MENU_OPTIONS [ IMPORT_DTM ] :
            gui_import_dtm ( DbConnection )  
        if reply == MENU_OPTIONS [ IMPORT_TILE ] :
            gui_import_tile ( DbConnection )   
        if reply == MENU_OPTIONS [ IMPORT_EMODNETGRID ] :
            gui_import_emodnetgrid ( DbConnection )
        if reply == MENU_OPTIONS [ IMPORT_IM ] :
            gui_import_im ( DbConnection )              
        #if reply == MENU_OPTIONS [ DEFINE_PRODUCT ] :
            #gui_product_series_definition ( DbConnection )
        #if reply == MENU_OPTIONS [ SHOW_PRODUCT_SERIES ] :
            #gui_show_product_series ( DbConnection )
        #if reply == MENU_OPTIONS [ DEFINE_COVERAGE ] :
            #gui_store_coverage( DbConnection )
        #if reply == MENU_OPTIONS [ SUBMIT_ORDER ] :
            #gui_submit_order( DbConnection )
        #if reply == MENU_OPTIONS [ GET_PRODUCT_FILE ] :
            #gui_get_generated_product( DbConnection )
        #if reply == MENU_OPTIONS [ DELETE_PRODUCT_S ] :
            #gui_delete_product_series( DbConnection )
        if reply == MENU_OPTIONS [ COMMIT ]  :
            logger.info("Commit and close database connection")
            DbConnection.commit()
        if reply == MENU_OPTIONS [ ROLLBACK ]  :
            logger.info("Rollback and close database connection")
            DbConnection.rollback()
        if reply == MENU_OPTIONS [ EXIT ] :
            DbConnection.close()
            break


def gui_import_dtm ( DbConnection ) :
    """Function to import DTM (metadata and hull) into database"""
    try :
        logger.info("Start import DTM GUI")
        logger.info("Input DTM metadata")

        # Input DTM name
        msg        = "Give name of DTM"
        title      = "DTM name"
        dtm_name   = str(enterbox(msg, title, default='', strip=True, image=None, root=None))
        logger.info( "DTM name: " + dtm_name )

        # Input DTM description
        msg               = "Give description of DTM"
        title             = "DTM description"
        dtm_description   = str(enterbox(msg, title, default='', strip=True, image=None, root=None))
        logger.info( "DTM description: " + dtm_description )
        
        # Select processing organisation
        msg     = "Select processing organisation"
        title   = "Processing organisation selection"
        processing_organisation_id = DbConnection.select_from_dropdown_list ( AGENCY_CLASS_ID, msg, title  )
        logger.info( "Processing organisation ID: " + str(processing_organisation_id) )

        # Website organisation
        msg         = "Give URL of website of processing organisation"
        title       = "Website URL"
        website_url = str(enterbox(msg, title, default='', strip=True, image=None, root=None))
        logger.info( "Website URL: " + str(website_url) )        

        # Date selection
        msg       = "Select year of DTM production"
        title     = "Date selection"
        year      = int(integerbox(msg, title, default=2012, lowerbound=1500, upperbound=2100))
        msg       = "Select month of DTM production"
        title     = "Date selection"
        month     = int(integerbox(msg, title, default=1, lowerbound=1, upperbound=12))   
        if month in (1,3,5,7,8,10,12) :
            upper_day = 31 
        elif month in (4,6,9,11) :
            upper_day = 30
        elif month == 2 :
            upper_day = 29
        msg       = "Select day of DTM production"
        title     = "Date selection"
        day       = int(integerbox(msg, title, default=1, lowerbound=1, upperbound=upper_day))  
        if len(str(month)) == 1 :
            month = str(0) + str(month)
        if len(str(day)) == 1 :
            day = str(0) + str(day)            
        dtm_date = str(year) + str(month) + str(day) + '000000'  
        logger.info("Date of DTM: " + str(dtm_date) )
        
        # Coordinate system
        coordinate_system_id = WGS84
        vertical_datum_id    = LAT
        logger.info( "Coordinate system: " + str(coordinate_system_id) )
        logger.info( "Vertical datum: " + str(vertical_datum_id) )
        
        # Select shapefile
        msg        = "Select shape file with DTM hull"
        title      = "File selection"
        shape_file = fileopenbox(msg, title, default='*', filetypes=[".shp"])
        logger.info("Shape file: " + str(shape_file))

        # Select SD file
        #msg     = "Select SD file of DTM"
        #title   = "File selection"
        #sd_file = fileopenbox(msg, title, default='*', filetypes=[".sd"])
        #sd_file_path, sd_file_name = os.path.split(sd_file)
        #logger.info("SD file: " + str(sd_file))    
        #logger.info("SD file path: " + str(sd_file_path))   
        #logger.info("SD file name: " + str(sd_file_name))   

        # Select XYZ file
        #msg      = "Select XYZ file of DTM"
        #title    = "File selection"
        #xyz_file = fileopenbox(msg, title, default='*', filetypes=[".xyz"])
        #msg         = "Give column separator"
        #title       = "File definition"
        #if len(str(enterbox(msg, title, default='', strip=True, image=None, root=None))) == 0 :
            #separator = ' ';
        #logger.info("XYZ file: " + str(xyz_file))  
        #logger.info("Separator: " + str(separator) )          

        # Now extract the hull from the shapefile
        hull_wkt = extract_hull_from_shapefile ( logger, shape_file ) 
        
        # The dimensions we need 
        #dimensions = get_dimensions ( xyz_file,separator )
        #logger.info(str(dimensions))
        # Date selection
        
        dimensions = {}
        msg       = "Minimum X"
        title     = "Dimensions"
        dimensions[MINX]      = float(enterbox(msg, title))
        msg       = "Maximum X"
        title     = "Dimensions"
        dimensions[MAXX]      = float(enterbox(msg, title))
        msg       = "Minimum Y"
        title     = "Dimensions"
        dimensions[MINY]      = float(enterbox(msg, title))
        msg       = "Maximum Y"
        title     = "Dimensions"
        dimensions[MAXY]      = float(enterbox(msg, title))
        msg       = "Minimum Z"
        title     = "Dimensions"
        dimensions[MINZ]      = float(enterbox(msg, title))
        msg       = "Maximum Z"
        title     = "Dimensions"
        dimensions[MAXZ]      = float(enterbox(msg, title))        
        msg       = "Number of points"
        title     = "Dimensions"
        dimensions[NOPS]      = int(integerbox(msg, title, default=1, lowerbound=1, upperbound=1000000000))        
        
        # Let's store the metadata
        attribute_list = {}
        attribute_list [ "NAME" ] = dtm_name
        attribute_list [ "DESCRIPTION" ] = dtm_description
        attribute_list [ "SYS001" ] = processing_organisation_id        
        attribute_list [ "SYS002" ] = website_url        
        attribute_list [ "SYS003" ] = dtm_date      
        attribute_list [ "SYS004" ] = coordinate_system_id 
        attribute_list [ "SYS005" ] = vertical_datum_id        
        attribute_list [ "SYS006" ] = dimensions[MINX] 
        attribute_list [ "SYS007" ] = dimensions[MAXX] 
        attribute_list [ "SYS008" ] = dimensions[MINY] 
        attribute_list [ "SYS009" ] = dimensions[MAXY] 
        attribute_list [ "SYS010" ] = dimensions[MINZ] 
        attribute_list [ "SYS011" ] = dimensions[MAXZ] 
        attribute_list [ "SYS012" ] = dimensions[NOPS]
        logger.info(str(attribute_list))
        dtm_id = int(DbConnection.ins_obj_attributes ( DTM_CLASS_ID, attribute_list ))   
        logger.info("ID of inserted DTM is: " + str(dtm_id))
        
        # Don't forget to store the hull
        DbConnection.store_hull ( DTM_CLASS_ID, dtm_id, hull_wkt )    
        
        # And don't forget to store the SD file
        # DbConnection.set_blob ( DTM_CLASS_ID, dtm_id, 'SYS013', sd_file, sd_file_name )        
        
        # Now we have to check if hull is inserted successfully
        resultset = DbConnection.get_geometries ( DbConnection.get_table_name(DTM_CLASS_ID), 'SYS_GEOM001', 'ID', dtm_id )
        if len(resultset) > 0 :
            for geom in resultset :
                plot_geometry ( ogr.CreateGeometryFromWkt( str(geom[0]) ), 'r', 'b' )    
                
        # Show plot
        show_plot()        
                
    except Exception, err:
        logger.critical("Import DTM failed: ERROR: " + str(err))
        sys.exit("Execution stopped")        

def gui_import_im ( DbConnection ) :
    """Function to import IM into database"""
    try :
        logger.info("Start import IM")
        logger.info("Input IM metadata")

        # Input survey name
        msg       = "Give name of survey"
        title     = "Survey name"
        im_name   = str(enterbox(msg, title, default='', strip=True, image=None, root=None))
        logger.info( "IM name: " + im_name )

        # Input CDI record
        msg        = "Give CDI record of survey"
        title      = "CDI record"
        cdi_record = str(enterbox(msg, title, default='', strip=True, image=None, root=None))
        logger.info( "CDI record: " + cdi_record )

        # Input survey quality
        msg       = "Give quality of survey"
        title     = "Survey quality"
        im_qual   = int(integerbox(msg, title, default=3, lowerbound=1, upperbound=5))
        logger.info( "Survey quality: " + str(im_qual) )
        
        # Select processing organisation
        msg     = "Select responsible organisation"
        title   = "Responsible organisation selection"
        processing_organisation_id = DbConnection.select_from_dropdown_list ( AGENCY_CLASS_ID, msg, title  )
        logger.info( "Responsible organisation ID: " + str(processing_organisation_id) )      
        
        # Select MB sensor
        msg     = "Select MB sensor"
        title   = "MB Sensor selection"        
        mb_sensor_id = DbConnection.select_from_dropdown_list ( MB_CLASS_ID, msg, title  )
        logger.info( "MB sensor ID: " + str(mb_sensor_id) )  
        
        # Select survey owner
        msg     = "Select survey owner"
        title   = "Survey owner selection"        
        user_id = DbConnection.select_from_dropdown_list ( USER_CLASS_ID, msg, title  )
        logger.info( "Survey owner ID: " + str(user_id) )         
        
        # Date selection
        msg       = "Select year of survey"
        title     = "Date selection"
        year      = int(integerbox(msg, title, default=2012, lowerbound=1500, upperbound=2100))
        msg       = "Select month of survey"
        title     = "Date selection"
        month     = int(integerbox(msg, title, default=1, lowerbound=1, upperbound=12))   
        if month in (1,3,5,7,8,10,12) :
            upper_day = 31 
        elif month in (4,6,9,11) :
            upper_day = 30
        elif month == 2 :
            upper_day = 29
        msg       = "Select day of survey"
        title     = "Date selection"
        day       = int(integerbox(msg, title, default=1, lowerbound=1, upperbound=upper_day))  
        if len(str(month)) == 1 :
            month = str(0) + str(month)
        if len(str(day)) == 1 :
            day = str(0) + str(day)            
        im_date = str(year) + str(month) + str(day) + '000000'  
        logger.info("Date of survey: " + str(im_date) )

        # Select SD file
        msg     = "Select data file of IM"
        title   = "File selection"
        data_file = fileopenbox(msg, title, default='*', filetypes=[".sd"])
        data_file_path, data_file_name = os.path.split(data_file)
        logger.info("Data file: " + str(data_file))    
        logger.info("Data file path: " + str(data_file_path))   
        logger.info("Data file name: " + str(data_file_name))            
        
        # Let's store the metadata
        attribute_list = {}
        attribute_list [ "NAME" ] = im_name
        attribute_list [ "DESCRIPTION" ] = im_name
        attribute_list [ "SYS001" ] = im_date   
        attribute_list [ "SYS019" ] = 'T' 
        attribute_list [ "SYS033" ] = 'T'        
        attribute_list [ "SYS045" ] = 'T'      
        attribute_list [ "SYS117" ] = str(user_id)
        attribute_list [ "SYS118" ] = str(im_qual)        
        attribute_list [ "SYS119" ] = cdi_record 
        attribute_list [ "SYS120" ] = im_date 
        attribute_list [ "SYS121" ] = str(processing_organisation_id)
        attribute_list [ "SYS122" ] = str(mb_sensor_id)
        attribute_list [ "SYS123" ] = 'This is a test survey' 
        attribute_list [ "SYS124" ] = 'Titanic' 
        logger.info(str(attribute_list))
        im_id = int(DbConnection.ins_obj_attributes ( IM_CLASS_ID, attribute_list ))   
        logger.info("ID of inserted survey is: " + str(im_id))  
        
        # And don't forget to store the data file
        DbConnection.set_blob ( IM_CLASS_ID, im_id, 'SYS050', data_file, data_file_name )             
                
    except Exception, err:
        logger.critical("Import DTM failed: ERROR: " + str(err))
        sys.exit("Execution stopped")        



def gui_import_tile ( DbConnection ) :
    """Function to import tile (metadata and points according to EMODNET format) into database"""
    try :
        logger.info("Start import Tile GUI")
        logger.info("Input Tile metadata")
        
        ## Input DTM name
        #msg        = "Give name of Tile"
        #title      = "Tile name"
        #tile_name   = str(enterbox(msg, title, default='', strip=True, image=None, root=None))
        #logger.info( "Tile name: " + tile_name )

        ## Input Tile description
        #msg               = "Give description of Tile"
        #title             = "Tile description"
        #tile_description  = str(enterbox(msg, title, default='', strip=True, image=None, root=None))
        #logger.info( "Tile description: " + tile_description )
   
        # Select Emodnet grid
        #msg        = "Select Emodnet gridfile"
        #title      = "Emodnet gridfile selection"
        #grid_file  = fileopenbox(msg, title, default='*', filetypes=[".shp"])
        #logger.info("Emodent gridfile: " + str(grid_file))   
        
        # Select shapefile
        msg             = "Select shape file with Tiles"
        title           = "File selection"
        tile_shape_file = fileopenbox(msg, title, default='*', filetypes=[".shp"])
        logger.info("Shape file: " + str(tile_shape_file))

        # Read tiles from shapefile
        fIn        = ogr.Open ( str(tile_shape_file) )
        layer      = fIn.GetLayer(0)
        feature = layer.GetNextFeature()
        while feature:
            geom       = feature.GetGeometryRef()
            tile_wkt   = str(geom.ExportToWkt())   
            name       = feature.GetFieldAsString('NAME')
            print tile_wkt
            print name
        
            # Let's store the metadata
            attribute_list = {}
            attribute_list [ "NAME" ] = name
            logger.info(str(attribute_list))
            tile_id = int(DbConnection.ins_obj_attributes ( TILE_CLASS_ID, attribute_list ))   
            logger.info("ID of inserted tile is: " + str(tile_id))        

            # Don't forget to extract and store the tile boundaries
            DbConnection.store_hull ( TILE_CLASS_ID, tile_id, tile_wkt )  
            
            # Destroy feature and get next one
            feature.Destroy()
            feature = layer.GetNextFeature()              
        
        # Finally store grid in database
        #nr_of_points = DbConnection.write_points_to_db ( grid_file, tile_id, 12, ';' )  
        #logger.info("Number of points in tile: " + str(nr_of_points))   
        #attribute_list = {}
        #attribute_list [ "SYS001" ] = nr_of_points
        #tile_id = int(DbConnection.upd_obj_attributes( TILE_CLASS_ID, tile_id, attribute_list )) 
        
    except Exception, err:
        logger.critical("Import DTM failed: ERROR: " + str(err))
        sys.exit("Execution stopped")    


def gui_import_emodnetgrid ( DbConnection ) :
    """Function to EMODNET grid into database"""
    try :
        logger.info("Start import EMODNET grid")
        logger.info("Input Tile metadata")
   
        # Select Emodnet grid
        msg        = "Select Emodnet gridfile"
        title      = "Emodnet gridfile selection"
        grid_file  = fileopenbox(msg, title, default='*', filetypes=[".shp"])
        logger.info("Emodent gridfile: " + str(grid_file))    
        
        # Finally store grid in database
        nr_of_points = DbConnection.write_points_to_db ( grid_file, 12, ';' )  
        logger.info("Number of points in grid: " + str(nr_of_points))  
        
    except Exception, err:
        logger.critical("Import EMODNET grid failed: ERROR: " + str(err))
        sys.exit("Execution stopped") 
        
#def gui_product_series_definition ( DbConnection ) :
    #"""Function to sore product series definition"""
    #try :
        #logger.info("Start product generation GUI")
        #logger.info("Select CM source")

        ## Select product type
        #msg             = "Select product type"
        #title           = "Product type selection"
        #product_type_id = int(PRODUCT_TYPE_LIST [ choicebox(msg, title, [ CONTOURS, SPOT_SOUNDINGS ]) ])
        #print product_type_id

        ## Input product series name
        #msg                 = "Give name of product series"
        #title               = "Product series name"
        #product_series_name = str(enterbox(msg, title, default='', strip=True, image=None, root=None))
        #logger.info( "Product series name: " + product_series_name )

        ## Popupsto select product series source
        #msg     = "Select product series source"
        #title   = "Product series source selection"
        #choices = [IM, CM]
        #source  = choicebox(msg, title, choices)
        #logger.info( "Product series source: " +  str(source) )
        #if source == CM :
            #msg     = "Select continuous model"
            #title   = "Continuous model selection"
            #source_name         = CM
            #instance_id         = int(DbConnection.get_cm_id ( choicebox(msg, title, DbConnection.get_cm_list() ) ))
            #object_class_source = CM_SOURCE_CLASS_ID
            #logger.info( "Continuous model ID: " +  str(instance_id) )
        #if source == IM :
            #msg     = "Select individual model"
            #title   = "Individual model selection"
            #source_name         = IM
            #instance_id         = int(DbConnection.get_im_id ( choicebox(msg, title, DbConnection.get_im_list() ) ))
            #object_class_source = IM_SOURCE_CLASS_ID
            #logger.info( "Individual model ID: " +  str(instance_id) )

        ## Input product type parameters
        #msg       = "Give map scale"
        #title     = "Map scale selection"
        #map_scale = int(integerbox(msg, title, default=10000, lowerbound=1, upperbound=1000000000))
        #search_distance = int(float(0.0005) * map_scale)
        #buffer_distance = int(float(0.0002) * map_scale)
        #logger.info( "Map scale: " +  str(map_scale) )
        #logger.info( "Search distance: " +  str(search_distance) )
        #logger.info( "Buffer distance: " +  str(buffer_distance) )

        ## Store source
        #attribute_list = {}
        #attribute_list [ "NAME" ]   =  source_name + " source product series " + product_series_name
        #attribute_list [ "SYS001" ] =  instance_id
        #object_source_id = int(DbConnection.ins_obj_attributes (object_class_source, attribute_list ))
        #logger.info( "Source ID: " +   str(object_source_id) )

        ## Store Product type parameters
        #if product_type_id == CONTOURS_CLASS_ID :
            #product_parameter_class_id = CONTOURS_CLASS_ID
            #attribute_list = {}
            #attribute_list [ "NAME" ]   =  "Parameter values for product series " + product_series_name
            #attribute_list [ "MAPSCALE" ]        = map_scale
            #attribute_list [ "CONTOURINTERVAL" ] = 86025
            #attribute_list [ "SEARCHDISTANCE" ]  = search_distance
            #attribute_list [ "DEPTHPRECISION" ]  = 2
            #attribute_list [ "SAMPLINGMETHOD" ]  = 14526
            #attribute_list [ "DEEPAREA" ]        = 25
            #attribute_list [ "SHALLOWAREA" ]     = 25
            #attribute_list [ "BUFFERDISTANCE" ]  =  buffer_distance
            #attribute_list [ "BUFFERRATIO" ]     =  0.95
        #if product_type_id == SPOTS_CLASS_ID :
            #product_parameter_class_id = SPOTS_CLASS_ID
            #attribute_list = {}
            #attribute_list [ "NAME" ]   =  "Parameter values for product series " + product_series_name
            #attribute_list [ "MAPSCALE" ]        = map_scale
            #attribute_list [ "DEPTHPRECISION" ]  = 2
        #product_parameter_values_id = int(DbConnection.ins_obj_attributes ( product_parameter_class_id, attribute_list ))
        #logger.info( "Product parameter values ID: " +  str(product_parameter_values_id) )

        ## Store  Output file parameters
        #attribute_list = {}
        #attribute_list [ "NAME" ]   =  "Output parameters product series " + product_series_name
        #output_parameter_values_id = int(DbConnection.ins_obj_attributes ( SHAPE_CLASS_ID, attribute_list ))
        #logger.info( "Output parameters values ID: " + str(output_parameter_values_id) )

        ## Store export product parameters
        #attribute_list = {}
        #attribute_list [ "NAME" ]   = "Export parameters product series " + product_series_name
        #attribute_list [ "SYS001" ] = object_class_source
        #attribute_list [ "SYS002" ] = object_source_id
        #attribute_list [ "SYS003" ] = product_parameter_class_id
        #attribute_list [ "SYS004" ] = product_parameter_values_id
        #attribute_list [ "SYS005" ] = SHAPE_CLASS_ID
        #attribute_list [ "SYS006" ] = output_parameter_values_id
        #attribute_list [ "SYS007" ] = 105044 # EPSG code WGS84 (4326)
        #attribute_list [ "SYS009" ] = 93     # Vertical datum MSL
        #attribute_list [ "SYS010" ] = -1     # Multiplication factor
        #attribute_list [ "SYS011" ] = 0      # Offset
        #export_parameter_values_id = int(DbConnection.ins_obj_attributes ( EXPORT_PARAM_CLASS_ID, attribute_list ))
        #logger.info( "Export parameters values ID: " + str(export_parameter_values_id) )

        ## Store product series
        #attribute_list = {}
        #attribute_list [ "NAME" ]   = product_series_name
        #attribute_list [ "SYS001" ] = PRODUCT_TYPE
        #attribute_list [ "SYS003" ] = export_parameter_values_id
        #product_series_id = int(DbConnection.ins_obj_attributes ( PRODUCT_SERIES_CLASS_ID, attribute_list ))
        #logger.info( "Product series ID: " + str(product_series_id) )

        #logger.info("Storing product series definition finished")

    #except Exception, err:
        #logger.critical("Product series definition failed: ERROR: " + str(err))
        #sys.exit("Execution stopped")

#def gui_show_product_series ( DbConnection ) :
    #"""Function to show source and tile/coverage"""

    #try :

        ## Select product series
        #msg     = "Select product series"
        #title   = "Product series selection"
        #product_series_id = DbConnection.select_from_dropdown_list ( PRODUCT_SERIES_CLASS_ID, msg, title  )
        #attributes = [ "SYS003"  ]
        #values     = DbConnection.get_obj_attributes ( PRODUCT_SERIES_CLASS_ID, product_series_id, attributes )
        #export_parameters_id  = int(values[0])

        ## Get source object class and instance
        #attributes = [ "SYS001", "SYS002"  ]
        #values     = DbConnection.get_obj_attributes ( EXPORT_PARAM_CLASS_ID, export_parameters_id, attributes )
        #p_source_class_id     = int(values[0])
        #p_source_instance_id  = int(values[1])
        #attributes  = [ "SYS001" ]
        #values      = DbConnection.get_obj_attributes ( p_source_class_id, p_source_instance_id, attributes )
        #if values[0] <> None :
            #source_instance_id = int(values[0])
            #if p_source_class_id == CM_SOURCE_CLASS_ID :
                #source_table    = CM_SOURCE_TABLE
                #source_geom_col = CM_SOURCE_GEOM
                #source_id_col   = CM_SELECT_ID
            #if p_source_class_id == IM_SOURCE_CLASS_ID :
                #source_table    = IM_SOURCE_TABLE
                #source_geom_col = IM_SOURCE_GEOM
                #source_id_col   = IM_SELECT_ID

            ## Get source geometries from database and plot
            #source_geometry_list = DbConnection.get_geometries ( source_table, source_geom_col, source_id_col, source_instance_id )
            #print len(source_geometry_list)
            #if len(source_geometry_list) > 0 :
                #for geom in source_geometry_list :
                    #plot_geometry ( ogr.CreateGeometryFromWkt( str(geom[0]) ), 'r', 'r' )

            ## Get tile geometries from database and plot
            #tile_geometry_list = DbConnection.get_geometries ( 'SDB_PRODUCT', 'SYS_GEOM001', 'SYS001', product_series_id )
            #if len(tile_geometry_list) :
                #for geom in tile_geometry_list :
                    #plot_geometry ( ogr.CreateGeometryFromWkt( str(geom[0]) ), 'b', 'b' )

            ## Show plot
            #show_plot()
        #else :
            #logger.info ("Source is deleted")

    #except Exception, err:
        #logger.critical("Show source and coverage failed: ERROR: " + str(err))
        #sys.exit("Execution stopped")


#def gui_store_coverage( DbConnection ) :
    #"""Function to store product tile/coverage"""
    #try:

        ## Select product series
        #msg     = "Select product series"
        #title   = "Product series selection"
        #product_series_id = DbConnection.select_from_dropdown_list ( PRODUCT_SERIES_CLASS_ID, msg, title  )
        #attributes = [ "NAME"  ]
        #values     = DbConnection.get_obj_attributes ( PRODUCT_SERIES_CLASS_ID, product_series_id, attributes )
        #product_series_name  = values[0]

        #logger.info("Store coverage for product series: " + str(product_series_name) + "( " + str(product_series_id) + " )" )

        ## Input product tile/coverage
        #msg    = "Give product coverage definition"
        #title  = "Product coverage definition"
        #tile_parameters = [TILE_NAME, LL_X, LL_Y, TILE_SIZE]
        #tile_values     = []
        #tile_values     = multenterbox(msg,title, tile_parameters)
        #tile_name       = str(tile_values[0])
        #logger.info("Tile/coverage definition " + str(tile_values) )

        ## Convert tile to wkt geometry and store tile
        #ll_x = float(tile_values[1])
        #ll_y = float(tile_values[2])
        #size = float(tile_values[3])
        #polygon = ogr.Geometry(ogr.wkbPolygon)
        #ring    = ogr.Geometry(ogr.wkbLinearRing)
        #ring.AddPoint(ll_x,ll_y)                # ll
        #ring.AddPoint(ll_x + size, ll_y)        # lr
        #ring.AddPoint(ll_x + size, ll_y + size) # ur
        #ring.AddPoint(ll_x,ll_y + size)         # ul
        #ring.CloseRings()
        #polygon.AddGeometry(ring)
        #polygon.FlattenTo2D()
        #tile_wkt = str(polygon.ExportToWkt())
        #DbConnection.store_tile ( product_series_id, tile_name, tile_wkt )

    #except Exception, err:
        #logger.critical("Store coverage failed: ERROR: " + str(err))
        #sys.exit("Execution stopped")

#def gui_submit_order( DbConnection ) :
    #"""Function to submit a product order for execution"""
    #try:

        ## Tile/product selection
        #msg     = "Select tile to produce"
        #title   = "Tile selection"
        #tile_id = int(DbConnection.get_id ( PRODUCT_CLASS_ID, choicebox(msg, title, DbConnection.get_flagged_tile_list() ) ))
        #logger.info("Tile to produce: " + str(tile_id) )

        ## Submit order
        #product_order_id = DbConnection.submit_order_for_new_edition ( tile_id )
        #logger.info("Product order submitted with ID: " + str(product_order_id) )

        ## Commit
        #DbConnection.commit()

        ## Monitor execution
        #while True :
            #order_status = DbConnection.get_order_status ( product_order_id )
            #if order_status in ( "Failed" , "Cancelled", "Finished" ) :
                #break
            #else :
                #logger.info("Product order status is " + str(order_status) )
            #time.sleep( 1 )
        #logger.info( "Product order status is " + str(DbConnection.get_order_status ( product_order_id )) )

    #except Exception, err:
        #logger.critical("Submit order failed: ERROR: " + str(err))
        #sys.exit("Execution stopped")

##def gui_show_task_progress()

#def gui_get_generated_product( DbConnection ) :
    #"""Function to download generated product from database"""
    #try:

        ## Tile/product selection
        #msg     = "Select tile to download"
        #title   = "Download tile selection"
        #tile_id = int(DbConnection.get_id ( PRODUCT_CLASS_ID, choicebox(msg, title, DbConnection.get_product_with_editions_list() ) ))
        #logger.info("Tile to download: " + str(tile_id) )

        ## Get product file
        #msg     = "Select file name and directory"
        #title   = "Save file"
        #l_blob_file = filesavebox(msg, title, default=None)
        #if '.zip' not in l_blob_file :
            #l_blob_file = l_blob_file + '.zip'
        #DbConnection.get_product_file (  tile_id, l_blob_file )
        #logger.info("Product file saved to: " + str(l_blob_file) )

    #except Exception, err:
        #logger.critical("Get generated product failed: ERROR: " + str(err))
        #sys.exit("Execution stopped")

#def gui_delete_product_series ( DbConnection ) :
    #"""Function delete product series"""
    #try :

        ## Select product series
        #msg     = "Select product series"
        #title   = "Product series selection"
        #product_series_id = DbConnection.select_from_dropdown_list ( PRODUCT_SERIES_CLASS_ID, msg, title  )
        #logger.info("Delete product series: " + str(product_series_id) )

        ## Delete product series
        #DbConnection.delete_product_series ( product_series_id )

    #except Exception, err:
        #logger.critical("Delete product series failed: ERROR: " + str(err))
        #sys.exit("Execution stopped")

def gui_db_connection_input () :
    logger.info("GUI database connection parameters")
    title = 'Database connection parameters'
    msg   = "Enter database connection parameters"
    field_names   = [ DB_TNS_SOURCE, DB_USER_SOURCE , DB_PASSWORD_SOURCE ]
    return_values = [ PARAMETER_LIST_VALUE [DB_TNS_SOURCE], PARAMETER_LIST_VALUE [DB_USER_SOURCE], PARAMETER_LIST_VALUE[DB_PASSWORD_SOURCE] ]
    return_values = multpasswordbox(msg,title, field_names, return_values)
    if return_values :
        PARAMETER_LIST_VALUE [DB_TNS_SOURCE]      = return_values[0]
        PARAMETER_LIST_VALUE [DB_USER_SOURCE]     = return_values[1]
        PARAMETER_LIST_VALUE [DB_PASSWORD_SOURCE] = return_values[2]

#########################################
#  GIS Functions
#########################################

def extract_hull_from_shapefile ( logger, shape_file ) :
    """Function to extract hull from shapefile"""
    try :
        logger.info ( "Extract hull from shapefile " + str(shape_file) ) 
        fIn        = ogr.Open ( str(shape_file) )
        layer      = fIn.GetLayer(0)
        feature    = layer.GetNextFeature()   
        geom       = feature.GetGeometryRef()
        hull_wkt   = str(geom.ExportToWkt())
        return hull_wkt
    except Exception, err:
        logger.critical("Extract hull from shapefile failed: ERROR: %s\n" % str(err))
        raise

def get_dimensions ( file_in, separator ) :
    """Function to extract dimensions from xyz file"""
    try :
        logger.info ( "Extract dimensions from xyz file " + str(file_in) ) 
        d = {}
        first_row = True
        d[NOPS] = 0
        file = open(file_in, 'r')
        for line in file :
            d[NOPS] = d[NOPS] + 1
            l = line.rstrip().split(separator)
            x = float(l[0])
            y = float(l[1])
            z = float(l[2])
            if first_row :
                d[MINX] = x
                d[MAXX] = x
                d[MINY] = y
                d[MAXY] = y
                d[MINZ] = z
                d[MAXZ] = z
                first_row = False
            else :
                if x < d[MINX] :
                    d[MINX] = x
                if x > d[MAXX] :
                    d[MAXX] = x                    
                if y < d[MINY] :
                    d[MINY] = y
                if y > d[MAXY] :
                    d[MAXY] = y              
                if z < d[MINZ] :
                    d[MINZ] = z
                if z > d[MAXZ] :
                    d[MAXZ] = z              
        file.close() 
        logger.info ('Now return')
        return d
    except Exception, err:
        logger.critical("Extract dimensions from xyz file failed: ERROR: %s\n" % str(err))
        raise    

def plot_geometry ( ogr_geom_in, exterior_color, interior_color ) :
    """Function to plot geometry"""
    if ogr_geom_in.GetGeometryName() == 'MULTIPOINT' or ogr_geom_in.GetGeometryName() == 'MULTILINESTRING' or ogr_geom_in.GetGeometryName() == 'MULTIPOLYGON' :
        for i in range(ogr_geom_in.GetGeometryCount()):
            plot_geometry ( ogr_geom_in.GetGeometryRef( i ), exterior_color, interior_color )
    if ogr_geom_in.GetGeometryName() == 'POINT' :
        x = []
        y = []
        x.append(ogr_geom_in.GetX())
        y.append(ogr_geom_in.GetY())
        pylab.plot(x,y,'o',color='y')
    if ogr_geom_in.GetGeometryName() == 'LINESTRING' :
        x = []
        y = []
        for i in range(ogr_geom_in.GetPointCount()) :
            x.append(ogr_geom_in.GetX(i))
            y.append(ogr_geom_in.GetY(i))
        pylab.plot(x,y,'-',color='g')
    if ogr_geom_in.GetGeometryName() == 'POLYGON' :
        polygon      = ogr_geom_in
        ring_index   = 0
        for nr_ring in range ( polygon.GetGeometryCount() ):
            ring        = polygon.GetGeometryRef( nr_ring )
            x =[ring.GetX(i) for i in range(ring.GetPointCount()) ]
            y =[ring.GetY(i) for i in range(ring.GetPointCount()) ]
            if ring_index == 0 :
                pylab.plot(x,y,'-',color=str(exterior_color), linewidth=2.0, hold=True)
            else :
                pylab.plot(x,y,'-',color=str(interior_color), linewidth=2.0, hold=True)
            ring_index = ring_index + 1

def show_plot() :
    """Function to show plot"""
    logger.info("Show plot")
    pylab.axis('equal')
    pylab.xlabel("Longitud")
    pylab.ylabel("Latitud")
    pylab.grid(True)
    pylab.title("Product tiles and product source")
    pylab.show()

##########################################
#  Database Class
##########################################

class DbConnection:
    """Connection class to Oracle database"""

    def __init__(self, DbUser, DbPass, DbConnect):
        try :
            self.logger = logging.getLogger( MODULE_NAME +'.DbConnection' )
            self.logger.info("Setup database connection")
            self.oracle_connection = cx_Oracle.connect(DbUser, DbPass, DbConnect)
            self.oracle_cursor = self.oracle_connection.cursor()
            self.oracle_cursor.execute("select 'established' from dual")
        except Exception, err:
            self.logger.critical("Setup database connection failed: ERROR: " + str(err))
            sys.exit("Execution stopped")

    def get_obj_attributes ( self, object_class_id, object_instance_id, attribute_list ) :
        """Function to get value of attribute for object instance"""
        try :
            self.logger.info("Query on database")
            l_query_xml = "<Filter><And><PropertyIsEqualTo><PropertyName>ID</PropertyName><Literal>" + str(object_instance_id) + "</Literal></PropertyIsEqualTo></And></Filter>"
            l_result_xml = self.oracle_cursor.callfunc("sdb_interface_pck.getObject", cx_Oracle.CLOB, [object_class_id, l_query_xml ])
            l_result_dom = xml.dom.minidom.parseString(str(l_result_xml))
            values = []
            for attribute in attribute_list :
                l_domain_value_tag = l_result_dom.getElementsByTagName(attribute)[0]
                # If attribute has no value catch exception and set value to None
                try :
                    l_value = l_domain_value_tag.childNodes[0].nodeValue
                except :
                    l_value = None
                values.append(l_value)
            return values
        except Exception, err:
            self.logger.critical("Query on database failed: ERROR: " + str(err))
            sys.exit("Execution stopped")

    def ins_obj_attributes ( self, object_class_id, attribute_list ) :
        """Function to set value of attribute for object instance"""
        try :
            self.logger.info( "Insert attributes in database" )

            # Build DOM
            doc = xml.dom.minidom.Document()
            rowset = doc.createElement("ROWSET")
            doc.appendChild(rowset)
            row = doc.createElement("ROW")
            rowset.appendChild(row)            

            # Add attributes
            attribute_keys = attribute_list.keys()
            for attribute_key in attribute_keys :
                attribute = doc.createElement(attribute_key)
                row.appendChild(attribute)
                value = doc.createTextNode(str(attribute_list[attribute_key]))
                attribute.appendChild(value)
                
            # Get XML as string
            l_mut_xml = doc.toxml()
                
                #l_mut_xml = "<ROWSET><ROW>"
            #l_attribute_keys = attribute_list.keys()
            #for l_attribute_key in l_attribute_keys :
                #l_mut_xml = l_mut_xml + "<" + l_attribute_key + ">" + str(attribute_list[l_attribute_key]) + "</" + l_attribute_key + ">"
            #l_mut_xml = l_mut_xml + "</ROW></ROWSET>"
            
            # Insert attributes
            l_obj_id = self.oracle_cursor.callfunc("sdb_interface_pck.setObject", cx_Oracle.NUMBER, [object_class_id, 'I', l_mut_xml ])
            
            return l_obj_id
        
        except Exception, err:
            self.logger.critical( "Insert attributes in database failed:ERROR: %s\n" % str(err))
            raise

    def upd_obj_attributes ( self, object_class_id, object_instance_id, attribute_list ) :
        """Function to set value of attribute for object instance"""
        try :
            self.logger.info( "Update attributes in database" )

            # Build DOM
            doc = xml.dom.minidom.Document()
            rowset = doc.createElement("ROWSET")
            doc.appendChild(rowset)
            row = doc.createElement("ROW")
            rowset.appendChild(row) 
            
            # Add ID attribute
            attribute = doc.createElement("ID")
            row.appendChild(attribute)
            value = doc.createTextNode(str(object_instance_id))
            attribute.appendChild(value)

            # Add attributes
            attribute_keys = attribute_list.keys()
            for attribute_key in attribute_keys :
                attribute = doc.createElement(attribute_key)
                row.appendChild(attribute)
                value = doc.createTextNode(str(attribute_list[attribute_key]))
                attribute.appendChild(value)
            
            # Get XML as string
            l_mut_xml = doc.toxml()

            # Update attributes
            self.logger.info("Update attributes")
            l_obj_id = self.oracle_cursor.callfunc("sdb_interface_pck.setObject", cx_Oracle.NUMBER, [object_class_id, 'U', l_mut_xml ])
            
            return l_obj_id

        except Exception, err:
            self.logger.critical( "Store attributes in database failed:ERROR: %s\n" % str(err))
            raise


    def write_points_to_db ( self, import_file, nr_columns, separator ) :
        """Function write points to database"""
        try :
            self.logger.info( "Write points to database")
            
            # Determine insert statement based on number of columns (3 of 12)
            self.logger.info ( "Build insert statememt" )            
            if int(nr_columns) == int(3) :
                insert_stmt = 'insert into sdb_im_import_temp ( x, y, z ) values ( :1, :2, :3 )'    
            if int(nr_columns) == int(12) :
                insert_stmt = 'insert into sdb_im_import_temp ( x, y, z, '
                insert_stmt = insert_stmt + ' customattribute0, customattribute1, customattribute2, customattribute3, customattribute4, '
                insert_stmt = insert_stmt + ' customattribute5, customattribute6, customattribute7, customattribute8 ) '                
                insert_stmt = insert_stmt + ' values ( :1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12 )'
          
            # Count number of points
            self.logger.info ( "Count number of points in grid" )
            file = open(import_file,'r')
            nr_of_lines = 0
            for line in file :
                nr_of_lines = nr_of_lines + 1
                if nr_of_lines % 10000000 == 0 :
                    self.logger.info(str(nr_of_lines) + " counted")
            file.close()
            self.logger.info("Total number of points in grid: " + str(nr_of_lines))               
            
            # Now read points from file and insert into array
            self.logger.info ( "Start inserting points into database" )
            skipped_file = 'c:/emodnet/skipped_rows.txt'
            depths = []
            i = 0
            j = 0
            fIn = open(import_file,'r')  
            fOut = open(skipped_file,'w')  
            
            # Loop through file
            for line in fIn : 

                # Split line into columns
                c = line.rstrip().split(separator)

                # Write columns to array type(i) is float
                try :
                    if nr_columns == 3 :
                        depths.append( ( float(c[0]), float(c[1]), float(c[2]) ) )
                        i = i + 1
                    if nr_columns == 4 :
                        depths.append( ( float(c[0]), float(c[1]), float(c[2]), str(c[3]) ) )
                        i = i + 1
                    if nr_columns == 5 :
                        depths.append( ( float(c[0]), float(c[1]), float(c[2]), str(c[3]), str(c[4]) ) )
                        i = i + 1
                    if nr_columns == 6 :
                        depths.append( ( float(c[0]), float(c[1]), float(c[2]), str(c[3]), str(c[4]), str(c[5]) ) )
                        i = i + 1
                    if nr_columns == 7 :
                        depths.append( ( float(c[0]), float(c[1]), float(c[2]), str(c[3]), str(c[4]), str(c[5]), str(c[6]) ) )
                        i = i + 1
                    if nr_columns == 8 :
                        depths.append( ( float(c[0]), float(c[1]), float(c[2]), str(c[3]), str(c[4]), str(c[5]), str(c[6]), str(c[7]) ) )
                        i = i + 1
                    if nr_columns == 9 :
                        depths.append( ( float(c[0]), float(c[1]), float(c[2]), str(c[3]), str(c[4]), str(c[5]), str(c[6]), str(c[7]), str(c[8]) ) )
                        i = i + 1
                    if nr_columns == 10 :
                        depths.append( ( float(c[0]), float(c[1]), float(c[2]), str(c[3]), str(c[4]), str(c[5]), str(c[6]), str(c[7]), str(c[8]), str(c[9]) ) )
                        i = i + 1
                    if nr_columns == 11 :
                        depths.append( ( float(c[0]), float(c[1]), float(c[2]), str(c[3]), str(c[4]), str(c[5]), str(c[6]), str(c[7]), str(c[8]), str(c[9]), str(c[10]) ) )
                        i = i + 1
                    if nr_columns == 12 :
                        depths.append( ( float(c[0]), float(c[1]), float(c[4]), str(c[3]), str(c[2]), str(c[5]), str(c[6]), str(c[7]), str(c[8]), str(c[9]), str(c[10]), str(c[11]) ) )
                        i = i + 1
                    if nr_columns == 13 :
                        depths.append( ( float(c[0]), float(c[1]), float(c[2]), str(c[3]), str(c[4]), str(c[5]), str(c[6]), str(c[7]), str(c[8]), str(c[9]), str(c[10]), str(c[11]), str(c[12]) ) )
                        i = i + 1
                except Exception, err :
                    fOut.write(line + '\n')
                    j = j + 1
                
                if i % 1000000 == 0 or i == int(nr_of_lines):
                    self.oracle_cursor.prepare( insert_stmt )
                    self.oracle_cursor.executemany(None, depths)                    
                    self.logger.info(str(i) + " points written to database")
                    depths = []
            self.logger.info(str(j) + " points skipped")
                
            # Close file when all points are inserted and create spatial index on database
            fIn.close()
            fOut.close()
            
            self.logger.info("Generate HH codes and spatial index on database")
            self.oracle_cursor.callproc("sdb_load_data_pck.load_emodnetgrid", [ 0 ]) 
           
            return i
            
        except Exception, err:
            self.logger.critical( "Write points to database failed:ERROR: %s\n" % str(err))
            raise
        
    def get_geometries ( self, object_class_table, spatial_column, select_column, select_id ) :
        """Function to get geometries from database"""
        stmt = 'select sdo_util.to_wktgeometry(' + str(spatial_column) + ') from ' + str(object_class_table) + ' where ' + str(select_column) + ' = ' + str(select_id)
        self.oracle_cursor.execute( stmt )
        resultset = self.oracle_cursor.fetchall()
        return resultset

    def del_obj_instance ( self, object_class_id, object_instance_id ) :
        """Function to set value of attribute for object instance"""

        # Build DOM
        doc = xml.dom.minidom.Document()
        rowset = doc.createElement("ROWSET")
        doc.appendChild(rowset)
        row = doc.createElement("ROW")
        rowset.appendChild(row)

        # Add ID attribute
        attribute = doc.createElement("ID")
        row.appendChild(attribute)
        value = doc.createTextNode(str(object_instance_id))
        attribute.appendChild(value)

        # Get XML as string
        l_mut_xml = doc.toxml()

        # Delete instance
        l_obj_id = self.oracle_cursor.callfunc("sdb_interface_pck.setObject", cx_Oracle.NUMBER, [object_class_id, 'D', l_mut_xml ])
        l_obj_id = l_obj_id

    def store_hull ( self, object_class_id, object_instance_id, wkt_geom ) :
        geom = self.oracle_cursor.var(cx_Oracle.CLOB)
        geom.setvalue(0, wkt_geom)
        geom_col = 'SYS_GEOM001'
        self.oracle_cursor.callproc("sdb_interface_pck.setGeom",[object_class_id, object_instance_id, geom_col, geom])        

    def set_blob ( self, object_class_id, object_instance_id, attribute_name, blob_file, file_name ) :
        """Function to store BLOB"""
        try :
            inputs = []
            inputs.append(open(blob_file, 'rb'))
            for input in inputs:
                binary_data = input.read()
                blobfile = self.oracle_cursor.var(cx_Oracle.BLOB)
                blobfile.setvalue(0, binary_data)
                self.oracle_cursor.callproc("sdb_interface_pck.setBlob", [object_class_id, object_instance_id, attribute_name, file_name, blobfile ])
        except Exception, err:
            print "Error storing BLOB: ERROR: " + str(err)
            raise        
        
    def store_tile ( self, product_series_id, tile_name, wkt_geom ) :
        attribute_list = {}
        attribute_list [ "NAME" ]   =  "Tile " + str(tile_name) +  " product series " + str(product_series_id)
        attribute_list [ "SYS001" ] = product_series_id # Product series ID
        attribute_list [ "SYS006" ] = 'F'               # Auto publish
        attribute_list [ "SYS007" ] = 'F'               # Auto generate
        l_tile_id = int(DbConnection.ins_obj_attributes ( PRODUCT_CLASS_ID, attribute_list ))
        l_geom = self.oracle_cursor.var(cx_Oracle.CLOB)
        l_geom.setvalue(0, wkt_geom)
        l_geom_col = 'SYS_GEOM001'
        self.oracle_cursor.callproc("sdb_interface_pck.setGeom",[PRODUCT_CLASS_ID, l_tile_id, l_geom_col, l_geom])
        logger.info( "Tile with ID " +  str(l_tile_id) + " sucessfully stored" )

    def get_flagged_tile_list ( self ) :
        """Function to get list of flagged tiles"""
        tile_list = []
        stmt = "select name from sdb_product where sys003 =\'T\'"
        self.oracle_cursor.arraysize = 100000
        self.oracle_cursor.execute(stmt)
        resultset = self.oracle_cursor.fetchmany()
        if resultset :
            for row in resultset :
                tile_list.append(str(row[0]))
        return tile_list

    def get_product_with_editions_list ( self ) :
        """Function to get list of tiles with editions"""
        tile_list = []
        stmt = "select p.name from sdb_productedition e, sdb_product p where e.sys003 = 4319 and e.sys001 = p.id"
        self.oracle_cursor.arraysize = 100000
        self.oracle_cursor.execute(stmt)
        resultset = self.oracle_cursor.fetchmany()
        if resultset :
            for row in resultset :
                tile_list.append(str(row[0]))
        return tile_list

    def get_cm_list ( self ) :
        """Function to get list of activated CM's"""
        cm_name_list = []
        stmt = "select name from sdb_continuousmodel where sys002 =\'T\'"
        self.oracle_cursor.arraysize = 100000
        self.oracle_cursor.execute(stmt)
        resultset = self.oracle_cursor.fetchmany()
        if resultset :
            for row in resultset :
                cm_name_list.append(str(row[0]))
        return cm_name_list

    def get_cm_id ( self, cm_name ) :
        stmt  = "select id from sdb_continuousmodel where name = :NAME"
        self.oracle_cursor.execute(stmt, NAME = cm_name )
        resultset = self.oracle_cursor.fetchmany()
        if resultset :
            for row in resultset :
                cm_id = int(row[0])
        return cm_id

    def get_im_list ( self ) :
        """Function to get list of activated CM's"""
        im_name_list = []
        stmt = "select name from sdb_individualmodel where sys004 in (9,10)"
        self.oracle_cursor.arraysize = 100000
        self.oracle_cursor.execute(stmt)
        resultset = self.oracle_cursor.fetchmany()
        if resultset :
            for row in resultset :
                im_name_list.append(str(row[0]))
        return im_name_list

    def get_im_id ( self, im_name ) :
        stmt  = "select id from sdb_individualmodel where name = :NAME"
        self.oracle_cursor.execute(stmt, NAME = im_name )
        resultset = self.oracle_cursor.fetchmany()
        if resultset :
            for row in resultset :
                im_id = int(row[0])
        return im_id

    def get_list ( self, object_class_id ) :
        """Function to get list"""
        name_list = []
        stmt = "select name from " + self.get_table_name ( object_class_id )
        self.oracle_cursor.arraysize = 100000
        self.oracle_cursor.execute(stmt)
        resultset = self.oracle_cursor.fetchmany()
        if resultset :
            for row in resultset :
                name_list.append(str(row[0]))
        return name_list

    def get_id ( self, object_class_id, object_class_name ) :
        stmt  = "select id from " + self.get_table_name ( object_class_id ) + " where name = :NAME"
        self.oracle_cursor.execute(stmt, NAME = object_class_name )
        resultset = self.oracle_cursor.fetchmany()
        if resultset :
            for row in resultset :
                id = int(row[0])
        return id

    def get_table_name ( self, object_class_id ) :
        stmt  = "select object_class_table from sdb_object_class where id = :ID"
        self.oracle_cursor.execute(stmt, ID = object_class_id )
        resultset = self.oracle_cursor.fetchmany()
        if resultset :
            for row in resultset :
                object_class_name = str(row[0])
        return object_class_name

    def select_from_dropdown_list ( self, object_class_id, msg, title ) :
        return int(self.get_id ( object_class_id, choicebox(msg, title, self.get_list( object_class_id ) ) ) )

    def submit_order_for_new_edition ( self, product_tile_id ) :
        return self.oracle_cursor.callfunc("sdb_object_bl_pck.submitOrderForNewEdition", cx_Oracle.NUMBER, [ product_tile_id  ])

    def get_product_file ( self, tile_id, blob_file ) :

        # Get product edition id
        stmt  = "select e.id from sdb_productedition e where e.sys001 = :ID and e.id = ( select max(t.id) from sdb_productedition t where t.sys001 = :ID )"
        self.oracle_cursor.execute(stmt, ID = tile_id )
        resultset = self.oracle_cursor.fetchmany()
        if resultset :
            for row in resultset :
                product_edition_id = str(row[0])

        # Get order id from database
        stmt  = "select id from sdb_productorder where sys017 = 324 and sys018 = :PRODUCT_EDITION_ID"
        self.oracle_cursor.execute(stmt, PRODUCT_EDITION_ID  = product_edition_id )
        resultset = self.oracle_cursor.fetchmany()
        if resultset :
            for row in resultset :
                product_order_id = str(row[0])

        # Get BLOB: First open file, then get blob from database and then write to file
        fBlob  = open(blob_file, 'wb')
        blob = self.oracle_cursor.callfunc("sdb_interface_pck.getBlob", cx_Oracle.BLOB, [ PRODUCT_ORDER_CLASS_ID, product_order_id, FILE_COL ])
        blob_data = blob.read()
        fBlob.write( blob_data )
        fBlob.close()

    def delete_product_series ( self, product_series_id ) :
        """Function to delete product series"""

        # Delete product downloads
        stmt = "select o.id from sdb_productdownload o,  sdb_productedition e, sdb_product p, sdb_productserie s where o.sys001 = e.id and e.sys001 = p.id and p.sys001 = s.id and s.id = :ID"
        self.oracle_cursor.execute(stmt, ID = product_series_id )
        resultset = self.oracle_cursor.fetchmany()
        if resultset :
            for row in resultset :
                self.del_obj_instance ( PROD_DOWNLOAD_CLASS_ID, int(row[0]) )

        # Delete product editions
        stmt = "select e.id from sdb_productedition e, sdb_product p, sdb_productserie s where e.sys001 = p.id and p.sys001 = s.id and s.id = :ID"
        self.oracle_cursor.execute(stmt, ID = product_series_id )
        resultset = self.oracle_cursor.fetchmany()
        if resultset :
            for row in resultset :
                self.del_obj_instance ( PROD_EDITION_CLASS_ID, int(row[0]) )

        # Delete products
        stmt = "select p.id from sdb_product p, sdb_productserie s where p.sys001 = s.id and s.id = :ID"
        self.oracle_cursor.execute(stmt, ID = product_series_id )
        resultset = self.oracle_cursor.fetchmany()
        if resultset :
            for row in resultset :
                self.del_obj_instance ( PRODUCT_CLASS_ID, int(row[0]) )

        # Get product parameter ID of product series
        stmt = "select s.sys003 from sdb_productserie s where s.id = :ID"
        self.oracle_cursor.execute(stmt, ID = product_series_id )
        resultset = self.oracle_cursor.fetchmany()
        if resultset :
            for row in resultset :
                export_parameters_id = int(row[0])

        # Delete product series
        self.del_obj_instance ( PRODUCT_SERIES_CLASS_ID, product_series_id )

        # Get export parameter values
        stmt = "select s.sys001, s.sys002, s.sys003, s.sys004, s.sys005, s.sys006 from sdb_exportparameters s where s.id = :ID"
        self.oracle_cursor.execute(stmt, ID = export_parameters_id )
        resultset = self.oracle_cursor.fetchmany()
        if resultset :
            for row in resultset :
                source_class_id = int(row[0])
                source_inst_id  = int(row[1])
                prod_class_id   = int(row[2])
                prod_inst_id    = int(row[3])
                output_class_id = int(row[4])
                output_inst_id  = int(row[5])

        print output_class_id
        print output_inst_id

        # Delete export parameters
        self.del_obj_instance ( source_class_id, source_inst_id )
        self.del_obj_instance ( prod_class_id, prod_inst_id   )
        self.del_obj_instance ( output_class_id, output_inst_id )
        self.del_obj_instance ( EXPORT_PARAM_CLASS_ID, export_parameters_id )

    def get_order_status ( self, order_id ) :
        # Get order status
        stmt = "select s.name from sdb_productorder o, sdb_productorderstatus s where o.sys004 = s.id and o.id = :ID"
        self.oracle_cursor.execute(stmt, ID = order_id )
        resultset = self.oracle_cursor.fetchmany()
        if resultset :
            for row in resultset :
                order_status = str(row[0])
        return order_status

    def commit( self ) :
        """Function to commit and close connection"""
        self.oracle_connection.commit()

    def rollback ( self ) :
        self.oracle_connection.rollback()

    def close ( self ) :
        self.oracle_connection.close()

####################################
# Start main program
####################################

if __name__ == "__main__":

    # Initialize logger
    logger      = logging.getLogger(MODULE_NAME)
    level       = LOGLEVELS.get(LOG_LEVEL, logging.NOTSET)
    logger.setLevel( level )
    stream_hdlr = logging.StreamHandler()
    formatter   = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    stream_hdlr.setFormatter(formatter)
    logger.addHandler(stream_hdlr)

    ############################
    # Database connection
    ############################

    # Ask for database connection parameters
    gui_db_connection_input ()

    logger.info( "Build database connection to " + str(PARAMETER_LIST_VALUE[ DB_USER_SOURCE ]) )
    DbConnection = DbConnection( PARAMETER_LIST_VALUE[ DB_USER_SOURCE ], PARAMETER_LIST_VALUE[ DB_PASSWORD_SOURCE ], PARAMETER_LIST_VALUE[ DB_TNS_SOURCE ])

    # Start gui
    try :
        gui_start ( DbConnection )
    except Exception, err:
        try :
            DbConnection.rollback_close()
        except Exception, err:
            null
        logger.critical( "Execution failed:ERROR: %s\n" % str(err))
        raise

