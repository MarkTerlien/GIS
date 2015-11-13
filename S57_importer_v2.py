#!/usr/bin/env python

###################################################
#                                                 #
# Script to import S-57 data                      # 
#                                                 #
# Author: MTJ                                     #
# Date:   1-8-2012                                #
#                                                 #
###################################################

# standard library imports
import sys
import logging

# related third party imports
import cx_Oracle
from easygui import *
#import pylab
import uuid

# GDAL/OGR imports
import gdal
import ogr

# Global Parameters
MODULE               = "S57_importer"
DB_USER_SOURCE       = "DB_USER_SOURCE"
DB_PASSWORD_SOURCE   = "DB_PASSWORD_SOURCE"
DB_TNS_SOURCE        = "DB_TNS_SOURCE"
S57_FILE             = "S57 file"

# Database connection parameter values
PARAMETER_LIST_VALUE = {}
PARAMETER_LIST_VALUE [ DB_USER_SOURCE ]     = "sens"
PARAMETER_LIST_VALUE [ DB_PASSWORD_SOURCE ] = "senso"
PARAMETER_LIST_VALUE [ DB_TNS_SOURCE ]      = "localhost/test"
PARAMETER_LIST_VALUE [ S57_FILE ]           = "C:/projects/Python/US5NY52M.000"

# Feature selection options
C_FEATURE_TYPE = 'Based on feature type'
C_RECORD_ID    = 'Based on record ID'
C_SPATIAL      = 'Select spatial'

# Object classes (TO DO: Read from file: s57objectclasses.csv)
OBJECT_CLASS = {}
OBJECT_CLASS[ "C_AGGR" ] = 400
OBJECT_CLASS[ "C_ASSO" ] = 401

# Database parameters
SRID = 8307
GTYPE = {}
GTYPE [ "POINT" ]           = 2001
GTYPE [ "LINESTRING" ]      = 2002
GTYPE [ "POLYGON" ]         = 2003
GTYPE [ "MULTIPOINT" ]      = 2005
GTYPE [ "MULTILINESTRING" ] = 2006
GTYPE [ "MULTIPOLYGON" ]    = 2007

# Type of (spatial) feature type
VI   = 'IsolatedNode'
VC   = 'ConnectedNode'
VE   = 'Edge'
DSID = 'DSID'

# Attributes of features
RECORD_ID  = 'RCID'
LONG_NAME  = 'LNAM'
GEOMETRY   = 'GEOM'
START_VC   = 'NAME_RCID_0'
END_VC     = 'NAME_RCID_1'
START_ORNT = "ORNT_0"     
START_USAG = "USAG_0" 
START_TOPI = "TOPI_0" 
START_MASK = "MASK_0"
END_ORNT   = "ORNT_1"     
END_USAG   = "USAG_1" 
END_TOPI   = "TOPI_1" 
END_MASK   = "MASK_1"
OBJCL_ID   = "OBJL"
SPAT_FS    = "NAME_RCID"
ORNT_FS    = "ORNT"
USAG_FS    = "USAG"
MASK_FS    = "MASK"
FF_REL_REF = "LNAM_REFS"
FF_REL_TYP = "FFPT_RIND"
NOIN       = "DSSI_NOIN"
NOCN       = "DSSI_NOCN"
NOED       = "DSSI_NOED"
CELL_NAME  = "DSID_DSNM"
CELL_ID    = "DSID_RCID"

#########################################
#  Generic functions
#########################################

# Initialize logging to screen
def start_logging () :
    try: 
        logger = logging.getLogger(MODULE)
        logger.setLevel(level=logging.INFO)
        level_name = 'info'
        stream_hdlr = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        stream_hdlr.setFormatter(formatter)
        logger.addHandler(stream_hdlr)
        logger.info("Start")
        return logger
    except Exception, err:
        print "Start logging failed"
        raise

#########################################
#  Database Class
#########################################

# Oracle database connection
class DbConnectionClass:
    """Connection class to Oracle database"""

    def __init__(self, DbUser, DbPass, DbConnect, parent_module):

        try :

            # Build connection and get session_id
            self.logger = logging.getLogger( parent_module + '.DbConnection')
            self.logger.info("Setup database connection")
            self.oracle_connection = cx_Oracle.connect(DbUser, DbPass, DbConnect)
            self.oracle_cursor = self.oracle_connection.cursor()
            

            self.session_id = 1490782 # for testing only
            
        except Exception, err:
            self.logger.critical("Setup db connection failed: ERROR: " + str(err))
            raise

    def store_spatials ( self, spat_dict, spatial_type ) :

        # INSERT INTO ndb_spatial_object
        # ( spatial_code,
        # , hordat
        # , posacc
        # , quapos
        # , geometry
        # , tech_start_date
        # , tech_date_last_mutation
        # , tech_sess_last_mutation
        # )


        # For points a bulk insert is possible
        # Edges have to be inserted one-by-one
        try: 

            self.logger.info("Store " + spatial_type + "s")
            spat_list = []
            nr_spatials = 0

            if spatial_type == VE :

                # Write nodes to list
                for key in spat_dict :

                    # Write geometry to CLOB
                    spat = spat_dict[key]
                    geom = ogr.CreateGeometryFromWkt(str(spat[GEOMETRY]))
                    geom.FlattenTo2D()
                    geom_clob = self.oracle_cursor.var(cx_Oracle.CLOB)
                    geom_clob.setvalue(0, str(geom.ExportToWkt()))

                    # Now insert each edge one-by-one
                    stmt = "insert into ndb_spatial_object ( spatial_code, hordat, posacc, quapos, geometry, tech_start_date, tech_date_last_mutation, tech_sess_last_mutation ) "
                    stmt = stmt + " values ( :1, null, null, null, sdo_geometry( :2, " + str(SRID) + " ), sysdate, sysdate, " + str(self.session_id) + " ) "
                    self.oracle_cursor.execute( stmt, { '1' : str(spatial_type) + str(key), '2' : geom_clob } )
                    nr_spatials = nr_spatials + 1

            else :
            
                # Write nodes to list (multipoints are scripped)
                for key in spat_dict :

                    # Get x and y coordinate
                    spat = spat_dict[key]
                    geom = ogr.CreateGeometryFromWkt(spat[GEOMETRY])
                    if geom.GetGeometryType() == ogr.wkbPoint : 
                        # Add point to array to insert
                        spat_list.append ( (str(spatial_type) + str(key), geom.GetX(0), geom.GetY(0)  ) )
                        nr_spatials = nr_spatials + 1
                    else :
                        # Insert multipoint one-by-one
                        geom.FlattenTo2D()
                        geom_clob = self.oracle_cursor.var(cx_Oracle.CLOB)
                        geom_clob.setvalue(0, str(geom.ExportToWkt()))
                        stmt = "insert into ndb_spatial_object ( spatial_code, hordat, posacc, quapos, geometry, tech_start_date, tech_date_last_mutation, tech_sess_last_mutation ) "
                        stmt = stmt + " values ( :1, null, null, null, sdo_geometry( :2, " + str(SRID) + " ), sysdate, sysdate, " + str(self.session_id) + " ) "
#                        self.oracle_cursor.execute( stmt, { '1' : str(spatial_type) + str(key), '2' : geom_clob } )
                        nr_spatials = nr_spatials + 1       
                        self.logger.info("Multipoint inserted")

                # Now prepare and execute the insert
                if len(spat_list) > 0 :
                    stmt = "insert into ndb_spatial_object ( spatial_code, hordat, posacc, quapos, geometry, tech_start_date, tech_date_last_mutation, tech_sess_last_mutation ) "
                    stmt = stmt + " values ( :1, null, null, null, sdo_geometry( 2001, " + str(SRID) + ", null, sdo_elem_info_array(1,1,1), sdo_ordinate_array( :2, :3 ) ) , sysdate, sysdate, " + str(self.session_id) + " ) "
                    self.oracle_cursor.prepare( stmt )
                    self.oracle_cursor.executemany(None, spat_list)

            self.logger.info( str(nr_spatials) + " " + spatial_type + "s inserted" )
            
        except Exception, err:
            self.logger.critical("Store " + spatial_type + "s in db failed: ERROR: " + str(err))
            raise


    def store_features ( self, features_list ) :

        # INSERT INTO ndb_feature_object
        # ( feature_code
        # , ocl_id
        # , feature_gtype
        # , tech_start_date
        # , tech_date_last_mutation
        # , tech_sess_last_mutation
        # )

        # Insert features in database; attributes are concatenated into attribute string <attr1><value1>|<attr1><value1>|
        # List contains all feature types; For each feature type extract features, construct attribute string and add to insert list
        try:
            self.logger.info("Store features")
            feature_insert_list = []
            feat_spat_rel_list = []
            feat_feat_rel_list = []
            attribute_string_list = []
            nr_features = 0
            
            for feature_type_dict in features_list :
                for feature_id in feature_type_dict :
                    # Process feature instance and add to insert list
                    feature = feature_type_dict[feature_id]
                    attribute_string = ""
                    object_class_id = int(feature[OBJCL_ID])
                    # Get feature-spatial relations if object class has geometry
                    if feature.has_key(GEOMETRY) : #object_class_id not in ( OBJECT_CLASS[ "C_AGGR" ], OBJECT_CLASS[ "C_ASSO" ]) :
                        geom = ogr.CreateGeometryFromWkt(feature[GEOMETRY])
                        feature_gtype = GTYPE[ str(geom.GetGeometryName())]
                        feat_spat_rel_list.append( ( feature_id, feature[SPAT_FS], feature[ORNT_FS], feature[USAG_FS], feature[USAG_FS] ) )
                    # Get feature-feature relations if feature has relations with other features
                    if feature.has_key(FF_REL_REF) :
                        feat_feat_rel_list.append( ( feature_id, feature[FF_REL_REF], feature[FF_REL_TYP] ) )
                    # Get object class specific attributes
                    for attribute in feature :
                        attribute_value = feature[ attribute ]
                        if len(attribute) == 6 :
                            attribute_string = attribute_string + str(attribute) + str(attribute_value) + "|"
                    attribute_string_list.append( ( feature_id, object_class_id, attribute_string ) )
                    feature_insert_list.append( ( str(feature_id), object_class_id,  feature_gtype ) ) 
                    nr_features = nr_features + 1

            # Now prepare and execute the insert      
            print feature_insert_list
            stmt = "insert into ndb_feature_object ( feature_code, ocl_id, feature_gtype, tech_start_date, tech_date_last_mutation, tech_sess_last_mutation ) "
            stmt = stmt + " values ( :1, :2, :3, sysdate, sysdate, " + str(self.session_id) + " ) "
            self.oracle_cursor.prepare( stmt )
            self.logger.info("insert features NOW")            
            self.oracle_cursor.executemany(None, feature_insert_list)   

            self.logger.info(str(nr_features) + " features inserted")

            # TO DO: Update feature with attribute string
            self.logger.info("Attributes for features updated")
#                print attribute_insert[0]
#                print attribute_insert[1]
#                print attribute_insert[2]

            # Now insert the feature spatial relations
            self.store_feature_spatial_relations ( feat_spat_rel_list )

            # Now insert the feature feature relations
            self.store_feature_feature_relations ( feat_feat_rel_list )            
            
        except Exception, err:
            self.logger.critical("Store features in db failed: ERROR: " + str(err))
            raise        


    def store_spatial_spatial_relations ( self, ve_dict ) :

        # INSERT INTO ndb_spat_spat_relation
        # ( id
        # , spat_code_from -- VE
        # , spat_code_to --VC
        # , pointer_index_nr
        # , ornt
        # , usag
        # , topi
        # , mask
        # , tech_start_date
        # , tech_date_last_mutation
        # , tech_sess_last_mutation
        # )        

        # Insert spatial-spatial relations from VE to start and end VC
        try :

            self.logger.info("Store spatial-spatial relations")
            spat_spat_rel_list = []
            nr_spat_spat_rel = 0
            
            # Write spat-spat (VE to start VC and to end VC) relations to list
            for key in ve_dict :
                ve = ve_dict[key]
                spat_spat_rel_list.append ( ( str(VE) + str(key), str(VC) + str(ve[START_VC]), str(ve[START_TOPI]), str(ve[START_ORNT]), str(ve[START_USAG]), str(ve[START_MASK]), str(ve[START_TOPI]) ) )
                spat_spat_rel_list.append ( ( str(VE) + str(key), str(VC) + str(ve[END_VC])  , str(ve[END_TOPI])  , str(ve[END_ORNT])  , str(ve[END_USAG])  , str(ve[END_MASK])  , str(ve[END_TOPI])     ) )
                nr_spat_spat_rel = nr_spat_spat_rel + 2

            # Now prepare and execute the insert                
            stmt = "insert into ndb_spat_spat_relation ( spat_code_from, spat_code_to, pointer_index_nr, ornt, usag, mask, topi, tech_start_date, tech_date_last_mutation, tech_sess_last_mutation ) "
            stmt = stmt + " values ( :1, :2, :3, :4, :5, :6, :7, sysdate, sysdate, " + str(self.session_id) + " ) "
            self.oracle_cursor.prepare( stmt )
            self.oracle_cursor.executemany(None, spat_spat_rel_list)                

            self.logger.info( str(nr_spat_spat_rel) + " spatial-spatial relations inserted" )

        except Exception, err:
            self.logger.critical("Store spatial-spatial relations in db failed: ERROR: " + str(err))
            raise


    def store_feature_spatial_relations ( self, feature_spatial_rel_list ) :


        # INSERT INTO ndb_feat_spat_relation
        # ( feat_code_from
        # , spat_code_to
        # , pointer_index_nr
        # , ornt
        # , usag
        # , mask
        # , tech_start_date
        # , tech_date_last_mutation
        # , tech_sess_last_mutation        
        # )

        # SPAT_FS: (8:834,878,995,996,761,823,709,713)
        # ORNT_FS: (8:2,2,1,1,2,2,2,1)
        # USAG_FS: (8:1,1,1,1,1,1,1,2)
        # MASK_FS: (8:2,2,2,2,2,2,2,2)

        # Store the feature spatial relations
        try:
            
            self.logger.info( "Store feature-spatial relations"  )
            feat_spat_rel_list = []
            nr_feat_spat_rel = 0

            # Loop over list with fs relations; get relation array and convert array to insert statement
            # In Python list index first element = 0; Pointer index nr starts at 1
            # Remove ) from last entry of list 
            for fs_relations in feature_spatial_rel_list :
                feature_id = fs_relations[0]
                spat_list = fs_relations[1].rstrip().split( ":" )[1][:-1].rstrip().split(",")
                ornt_list = fs_relations[2].rstrip().split( ":" )[1][:-1].rstrip().split(",")
                usag_list = fs_relations[3].rstrip().split( ":" )[1][:-1].rstrip().split(",")
                mask_list = fs_relations[4].rstrip().split( ":" )[1][:-1].rstrip().split(",")
                pointer_index_nr = 0
                while pointer_index_nr < len(spat_list) :
                    feat_spat_rel_list.append( ( feature_id, spat_list[pointer_index_nr], pointer_index_nr + 1, ornt_list[pointer_index_nr], usag_list[pointer_index_nr], mask_list[pointer_index_nr] ) )
                    pointer_index_nr = pointer_index_nr + 1
                    nr_feat_spat_rel = nr_feat_spat_rel + 1

            # Now prepare statement and insert feature-spatial relations
            stmt = "insert into ndb_feat_spat_relation ( feat_code_from, spat_code_to, pointer_index_nr, ornt, usag, mask, tech_start_date, tech_date_last_mutation, tech_sess_last_mutation ) "
            stmt = stmt + " values ( :1, :2, :3, :4, :5, :6, sysdate, sysdate, " + str(self.session_id) + " ) "
            self.oracle_cursor.prepare( stmt )
            self.oracle_cursor.executemany(None, feat_spat_rel_list)

            self.logger.info( str(nr_feat_spat_rel) + " feature-spatial relations inserted" )

        except Exception, err:
            self.logger.critical("Store feature-spatial relations in db failed: ERROR: " + str(err))
            raise        

    def store_feature_feature_relations ( self, feature_feature_rel_list ) :

        # insert into ndb_feat_feat_relation
        # ( feat_code_from
        # , feat_code_to
        # , relation_type
        # , tech_start_date
        # , tech_date_last_mutation
        # , tech_sess_last_mutation        
        # )

        # FF_REL_REF = (2:022631548D950001,0226243636EF0001)
        # FF_REL_TYP = (2:2,2)

        try :
            
            self.logger.info("Store feature-feature relations")
            feat_feat_rel_list = []
            nr_feat_feat_rel = 0

            # Loop over list with ff relations; get relation array and convert array to insert statement
            # In Python list index first element = 0; Pointer index nr starts at 1
            # Remove ) from last entry of list             
            for ff_relations in feature_feature_rel_list :
                feature_id = ff_relations[0]
                feat_list = ff_relations[1].rstrip().split( ":" )[1][:-1].rstrip().split(",")
                ftyp_list = ff_relations[2].rstrip().split( ":" )[1][:-1].rstrip().split(",")
                i = 0
                while i < len(feat_list) :
                    feat_feat_rel_list.append( ( feature_id, feat_list[i], ftyp_list[i] ) )
                    i = i + 1
                    nr_feat_feat_rel = nr_feat_feat_rel + 1

            # Now prepare statement and insert feature-spatial relations
            stmt = "insert into ndb_feat_feat_relation ( feat_code_from, feat_code_to, relation_type, tech_start_date, tech_date_last_mutation, tech_sess_last_mutation ) "
            stmt = stmt + " values ( :1, :2, :3, sysdate, sysdate, " + str(self.session_id) + " ) "
            self.oracle_cursor.prepare( stmt )
            self.oracle_cursor.executemany(None, feat_feat_rel_list)

            self.logger.info( str(nr_feat_feat_rel) + " feature-feature relations inserted" )

        except Exception, err:
            self.logger.critical("Store feature-feature relations in db failed: ERROR: " + str(err))
            raise 
            

    def rollback_close( self ) :
        """Function to rollback and close connection"""
        self.oracle_connection.rollback()
        self.oracle_connection.close()

    def commit_close( self ) :
        """Function to commit and close connection"""
        self.oracle_connection.commit()
        self.oracle_connection.close()

#########################################
#  GUI Functions
#########################################

def gui_db_parameters() :
    # Db connection
    title = 'Database connection parameters'
    msg   = "Enter database connection parameters "
    field_names   = [ DB_TNS_SOURCE, DB_USER_SOURCE , DB_PASSWORD_SOURCE ]
    return_values = [ PARAMETER_LIST_VALUE [DB_TNS_SOURCE], PARAMETER_LIST_VALUE [DB_USER_SOURCE], PARAMETER_LIST_VALUE[DB_PASSWORD_SOURCE] ]
    return_values = multpasswordbox( msg,title, field_names, return_values)
    if return_values :
        PARAMETER_LIST_VALUE [DB_TNS_SOURCE]      = return_values[0]
        PARAMETER_LIST_VALUE [DB_USER_SOURCE]     = return_values[1]
        PARAMETER_LIST_VALUE [DB_PASSWORD_SOURCE] = return_values[2]      

# Function to build gui for file selection
def gui_file_selection ( box_title, file_parameter ) :
    title = box_title
    msg   = 'Select file'
    file  = fileopenbox(msg, title, str(PARAMETER_LIST_VALUE[file_parameter]))
    PARAMETER_LIST_VALUE[S57_FILE] = str(file)

#########################################
#  GIS Functions
#########################################

def plot_feature_attributes ( feature ) :

    # Plot attributes and values of feature
    for j in range( feature.GetFieldCount() ) :
        if feature.IsFieldSet(j) :
            field_def  = feature.GetFieldDefnRef(j)
            field_name = field_def.GetName()
            logger.info("Field name    = " + str(field_name) + ": " + str(feature.GetFieldAsString(field_name)))    
       

def plot_geometry ( ogr_geom_in ) :
    
    # Plot point
    if ogr_geom_in.GetGeometryName() == 'POINT' :
        x = []
        y = []
        x.append(ogr_geom_in.GetX())
        y.append(ogr_geom_in.GetY())
        pylab.plot(x,y,'o',color='y')    
    
    # Plot linestring
    if ogr_geom_in.GetGeometryName() == 'LINESTRING' :
        x = []
        y = []
        for i in range(ogr_geom_in.GetPointCount()) :
            x.append(ogr_geom_in.GetX(i))
            y.append(ogr_geom_in.GetY(i))
        pylab.plot(x,y,'-',color='g')
    
    # Plot polygon
    if ogr_geom_in.GetGeometryName() == 'POLYGON' :
        for i_ring in range ( ogr_geom_in.GetGeometryCount() ):
            ring        = ogr_geom_in.GetGeometryRef( i_ring )
            x =[ring.GetX(i) for i in range(ring.GetPointCount()) ]
            y =[ring.GetY(i) for i in range(ring.GetPointCount()) ]
            if i_ring == 0 :
                pylab.plot(x,y,'-',color='r', linewidth=2.0, hold=True)
            else :
                pylab.plot(x,y,'-',color='b', linewidth=2.0, hold=True)

    # Plot multi geometry
    if ogr_geom_in.GetGeometryName() in ('MULTIPOINT', 'MULTILINESTRING', 'MULTILINESTRING')  :
        for i in range(ogr_geom_in.GetGeometryCount()):
            ogr_geom_out = plot_geometry ( ogr_geom_in.GetGeometryRef( i ) )   

#########################################
#  Show S57 Functions
#########################################

def show_s57_file ( file_name ) :
    
    # Clear S57 options if set or our results will be messed up.
    gdal.SetConfigOption( 'OGR_S57_OPTIONS', '' )
    #gdal.SetConfigOption( 'OGR_S57_OPTIONS', 'RETURN_PRIMITIVES:ON' )
    gdal.SetConfigOption( 'OGR_S57_OPTIONS', 'RETURN_LINKAGES:ON' )
    print logger.info("GDAL options: " + str(gdal.GetConfigOption( 'OGR_S57_OPTIONS')))
    
    # Open s57 FILE
    ds = ogr.Open( PARAMETER_LIST_VALUE [ S57_FILE ] )

    #
    choice = choicebox('How do you want to select features','Feature selection',[ C_FEATURE_TYPE, C_RECORD_ID, C_SPATIAL ])

    if choice == C_FEATURE_TYPE :

        # Popup select box for feature types
        msg               = "Select feature type"
        title             = "Feature type"
        feat_type_list    = [ ds.GetLayer(i).GetName() for i in xrange(ds.GetLayerCount()) ]
        feature_type_list = multchoicebox(msg, title, feat_type_list)

        # Get features from file
        if len(feature_type_list) > 0 :
            for feature_type in feature_type_list :
                src_features   = ds.GetLayerByName( feature_type )
                feature        = src_features.GetNextFeature()
                nr_features    = 0
                nr_points      = 0
                while feature is not None:
                    nr_features   = nr_features + 1
                    ogr_geom      = feature.GetGeometryRef()
                    if ogr_geom is not None :
                        plot_geometry ( ogr_geom )
                    plot_feature_attributes ( feature )
                    feature = src_features.GetNextFeature()
                    logger.info("=================================================")

    if choice == C_RECORD_ID :

        # Ask for record ID to look for
        record_id = str(integerbox('Give record ID', 'Record ID input', 1, 0, 99999))        

        # Loop over features
        for feat_type in (ds.GetLayer(i).GetName() for i in xrange(ds.GetLayerCount())) :
            src_features   = ds.GetLayerByName( feat_type )
            feature        = src_features.GetNextFeature()
            while feature is not None:
                for j in range( feature.GetFieldCount() ) :
                    if feature.IsFieldSet(j) :
                        field_def  = feature.GetFieldDefnRef(j)
                        field_name = field_def.GetName()
                        if str(field_name) == 'RCID' and str(feature.GetFieldAsString(field_name)) == record_id :
                            ogr_geom      = feature.GetGeometryRef()
                            if ogr_geom is not None :
                                plot_geometry ( ogr_geom )
                            plot_feature_attributes ( feature )                                
                feature = src_features.GetNextFeature()

    if choice == C_SPATIAL :

        # Ask for which type of spatial
        spatial_type = choicebox('How do you want to select features','Feature selection',[ VI, VC, VE ])

        # Ask for record ID to look for
        record_id = str(integerbox('Give record ID', 'Record ID input', 1, 0, 99999))
        
        # Find layer and feature
        src_features   = ds.GetLayerByName( spatial_type )
        feature        = src_features.GetNextFeature()
        while feature is not None:
            for j in range( feature.GetFieldCount() ) :
                if feature.IsFieldSet(j) :
                    field_def  = feature.GetFieldDefnRef(j)
                    field_name = field_def.GetName()
                    if str(field_name) == 'RCID' and ( str(feature.GetFieldAsString(field_name)) == record_id ) :
                        ogr_geom      = feature.GetGeometryRef()
                        if ogr_geom is not None :
                            plot_geometry ( ogr_geom )
                        plot_feature_attributes ( feature )                                
            feature = src_features.GetNextFeature()        
        
    ds.Destroy()
    
    # Show to plotted objects
    pylab.show()    

#########################################
#  Import S57 Functions
#########################################
    
def import_s57_file ( file_name ) :
    
    # Read S57 file options:
    # RETURN_PRIMITIVES => VI, VE and VC layers as features
    # RETURN_LINKAGES   => FS relations are included as attribute of feature
    # LNAM_REF          => FF relations are included as sttribute of feature

    # Open S57 file to read spatials with SS relations
    logger.info("Open S57 file to read spatials with SS relations")
    gdal.SetConfigOption( 'OGR_S57_OPTIONS', '' )
    gdal.SetConfigOption( 'OGR_S57_OPTIONS', 'RETURN_PRIMITIVES:ON' )   
   
    # Open s57 FILE
    ds = ogr.Open( PARAMETER_LIST_VALUE [ S57_FILE ] )

    # Write cell header to dictionary
    logger.info("Write cell header to dictionary")
    dsid_dict = write_cell_header_dict ( ds.GetLayerByName( DSID ) )

    # Show cell charactertics
    uuid_cell = uuid.uuid1()
    logger.info("UUID of cell: " + str(uuid_cell))
    logger.info("Name of cell to import: " + str(dsid_dict[CELL_NAME]))
    logger.info("Number of isolated nodes in file: " + str(dsid_dict[NOIN])) 
    logger.info("Number of connected nodes in file: " + str(dsid_dict[NOCN]))   
    logger.info("Number of edges in file: " + str(dsid_dict[NOED]))
    
    # Write VI to dictionary
    logger.info("Read isolated nodes from file")
    vi_dict = write_features_to_dict ( ds.GetLayerByName( VI ), RECORD_ID )

    # Write VC to dictionary
    logger.info("Read connected nodes from file")
    vc_dict = write_features_to_dict ( ds.GetLayerByName( VC ), RECORD_ID )

    # Write VE to dictionary
    logger.info("Read edges from file")
    ve_dict = write_features_to_dict ( ds.GetLayerByName( VE ), RECORD_ID )

    # Test if dictionaries are correct 
    #print "VI: " + str(vi_dict[1170])
    #print "VC start: " + str(vc_dict[7054])
    #print "VC end: " + str(vc_dict[7072])
    #print "VE before: " + str(ve_dict[9700])

    # Add connected nodes to edge
    logger.info("Add start and end connected node to edge")
    ve_dict = add_vc_to_ve ( ve_dict, vc_dict )

    #print "VE updated: " + str(ve_dict[9700])    

    # Store spatials in database
    logger.info("Store spatials in db") 
    OracleConnection.store_spatials ( vi_dict, VI )   
    OracleConnection.store_spatials ( vc_dict, VC )   
    OracleConnection.store_spatials ( ve_dict, VE )                                                 

    # Store SS relations in database
    logger.info("Store spatial-spatial relations in db")     
    OracleConnection.store_spatial_spatial_relations ( ve_dict ) 
    
    # Close file
    ds.Destroy()

    logger.info("Spatials and spatial-spatial relations stored in db") 

    # Open S57 file to read features with FS relations
    logger.info("Open S57 file to read features with FS relations")
    gdal.SetConfigOption( 'OGR_S57_OPTIONS', '' )
    gdal.SetConfigOption( 'OGR_S57_OPTIONS', 'RETURN_LINKAGES:ON'  )  

    # Open s57 FILE
    ds = ogr.Open( PARAMETER_LIST_VALUE [ S57_FILE ] )    

    # Write features to list
    logger.info("Read features from file")
    fe_list = write_features_to_list ( ds )

    # Write features to db
    logger.info("Store features in db")
    OracleConnection.store_features ( fe_list ) 
                         
    # Close file
    ds.Destroy()


def write_features_to_list ( s57_file ) :

    feature_type_list = []

    # Loop over feature types in file
    for i in xrange(s57_file.GetLayerCount()) :
        src_features = s57_file.GetLayerByName( s57_file.GetLayer(i).GetName() )        
        if str(s57_file.GetLayer(i).GetName())<> DSID : 
            feature_type_list.append( write_features_to_dict( src_features, LONG_NAME )) 
    logger.info(str(i-1) + " feature types read from file")
    return feature_type_list     


def write_cell_header_dict ( features ) :
    
    # Write cll header fields to dictionary
    feature  = features.GetNextFeature()
    if feature is not None :
        fields_dict = {}
        for j in range( feature.GetFieldCount() ) :
            if feature.IsFieldSet(j) :
                field_def = feature.GetFieldDefnRef(j)
                field_name = field_def.GetName()
                fields_dict[str(field_name)] = str(feature.GetFieldAsString(field_name))
    return fields_dict    

def write_features_to_dict ( features, unique_identifier ) :

    # Loop over features and write to dictionary
    features_dict = {}
    feature       = features.GetNextFeature()
    while feature is not None:
        fields_dict = {}
        for j in range( feature.GetFieldCount() ) :
            if feature.IsFieldSet(j) :
                field_def = feature.GetFieldDefnRef(j)
                field_name = field_def.GetName()
                if str(field_name) == str(unique_identifier) :
                    if str.isdigit(str(feature.GetFieldAsString(field_name))):
                        record_id = int(feature.GetFieldAsString(field_name))
                    else :
                        record_id = str(feature.GetFieldAsString(field_name))
                else :
                    fields_dict[str(field_name)] = str(feature.GetFieldAsString(field_name))
        if feature.GetGeometryRef() is not None :
            fields_dict[GEOMETRY] = feature.GetGeometryRef().ExportToWkt()
        features_dict[record_id] = fields_dict            
        feature = features.GetNextFeature()
    return features_dict

    
def add_vc_to_ve ( ve_dict, vc_dict ) :

    # Loop over ve, get start and end vc, update ve geometry and add to dictionary
    for key in ve_dict :

        # Get start and end vc and ve geometries
        ve = ve_dict[key]
        start_vc = vc_dict [ int(ve[START_VC]) ] 
        end_vc = vc_dict [ int(ve[END_VC]) ] 
        start_vc_geom = ogr.CreateGeometryFromWkt(start_vc[GEOMETRY])
        end_vc_geom = ogr.CreateGeometryFromWkt(end_vc[GEOMETRY])
        ve_geom = ogr.CreateGeometryFromWkt(ve[GEOMETRY])

        # Init new ve and add vertices
        new_ve_geom = ogr.Geometry(ogr.wkbLineString)
        new_ve_geom.AddPoint(start_vc_geom.GetX(0),start_vc_geom.GetY(0))
        for i in range(ve_geom.GetPointCount()) :
            new_ve_geom.AddPoint(ve_geom.GetX(i),ve_geom.GetY(i))
        new_ve_geom.AddPoint(end_vc_geom.GetX(0),end_vc_geom.GetY(0))

        # Add updated ve to ve dictionanry
        ve[GEOMETRY] = new_ve_geom.ExportToWkt() 
        ve_dict[key] = ve

    # Return ve dictionaty with updated ve geoemtries
    return ve_dict

    

#########################################
# Start main program
#########################################
        
if __name__ == "__main__":
    try:
        # Start logging framework
        logger = start_logging()

        # TO DO: Set SYSDATE as GLOBAL
        
        # Get database connection parameters
        logger.info("Get database connection parameters")
        gui_db_parameters()
        
        # Build database connection
        logger.info("Open database connection")
        OracleConnection = DbConnectionClass ( PARAMETER_LIST_VALUE[ DB_USER_SOURCE ], PARAMETER_LIST_VALUE[ DB_PASSWORD_SOURCE ], PARAMETER_LIST_VALUE[ DB_TNS_SOURCE ], MODULE )       
        
        # Select S57 file
        logger.info("Select S57 file")
        gui_file_selection ( "Select S57 file", S57_FILE )
        logger.info ( "S57 file " + str(PARAMETER_LIST_VALUE [ S57_FILE ]) + " selected")
        
        # Show S57 file
        logger.info ( "import selected S57 file" )
        #show_s57_file ( PARAMETER_LIST_VALUE [ S57_FILE ] )

        # Show S57 file
        logger.info ( "import selected S57 file" )
        import_s57_file ( PARAMETER_LIST_VALUE [ S57_FILE ] )         
        
        # Close database connection
        logger.info ("Close database connection")
        OracleConnection.rollback_close()
        
    except Exception, err:
        print "Installation failed: ERROR: %s\n" % str(err)
        sys.exit(1)

        
