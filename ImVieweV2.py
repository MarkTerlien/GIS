#! /usr/bin/python

""" Function to import survey into database
"""

# Standard library imports
import os
import sys
import math
import struct
import logging
import xml.dom.minidom

# Related third party imports
import numpy
import cx_Oracle
from easygui import *
from Scientific.IO.NetCDF import *
from CGAL.Alpha_shapes_2 import *
from CGAL.Kernel import *

# Matlib imports
import pylab
import matplotlib.patches as patches
from matplotlib.path import Path
from numpy import asarray, concatenate, ones

# Shapely imports
from shapely.wkb import loads

# GDAL/OGR imports
from osgeo import gdal
from osgeo import gdalconst
from osgeo import ogr
from osgeo import osr

# Module name
MODULE_NAME = "ImViewer"

# Settings
REGENERATE_HULL = False

# DB connect Parameters
DB_USER_SOURCE       = "DB_USER_SOURCE"
DB_PASSWORD_SOURCE   = "DB_PASSWORD_SOURCE"
DB_TNS_SOURCE        = "DB_TNS_SOURCE"
CM_ID                = "CM_ID"
DIRECTORY            = "DIRECTORY"
OBJECT_CLASS_ID      = "OBJECT_CLASS_ID"
OBJECT_INSTANCE_ID   = "OBJECT_INSTANCE_ID"
GEOM_COL             = "GEOM_COL"
GRIDSIZE             = "GRIDSIZE"
EMODNET_FILE         = "EMODNET_FILE"
ATTRIBUTE_NAME       = "ATTRIBUTE_NAME"
BLOB_FILE            = "BLOB_FILE"

# Database connection parameter values
PARAMETER_LIST_VALUE = {}
PARAMETER_LIST_VALUE [ DB_USER_SOURCE ]     = "sens"
PARAMETER_LIST_VALUE [ DB_PASSWORD_SOURCE ] = "senso"
PARAMETER_LIST_VALUE [ DB_TNS_SOURCE ]      = "10.20.0.49/sens11"
PARAMETER_LIST_VALUE [ CM_ID ]              = 82829
PARAMETER_LIST_VALUE [ OBJECT_CLASS_ID ]    = 236
PARAMETER_LIST_VALUE [ OBJECT_INSTANCE_ID ] = 86154
PARAMETER_LIST_VALUE [ GEOM_COL ]           = "SYS_GEOM001"
PARAMETER_LIST_VALUE [ GRIDSIZE ]           = 0.001
PARAMETER_LIST_VALUE [ ATTRIBUTE_NAME ]     = "SYS001"
PARAMETER_LIST_VALUE [ EMODNET_FILE ]       = "C:\\Geodata\\Europe\\Bathymetry\\EMODNET\\emodnet_belgium.grd"
PARAMETER_LIST_VALUE [ BLOB_FILE ]          = "T:\\EMODNET 1&2\\20 Specialist\\04 Data\\Release 2 (mei 2011)\\05 Downloadable Products\*"
PARAMETER_LIST_VALUE [ DIRECTORY ]          = "D:/Geodata"

# Menu options
SHOW_PARAMETERS   = "SHOW_PARAMETERS"
UPDATE_PARAMETERS = "UPDATE_PARAMETERS"
INVERT_XY         = "Invert XY"
PLOT_IM           = "Plot IM"
PLOT_CM           = "Plot CM"
PLOT_WORLD        = "Custom"
CONVERT_EMODNET   = "Convert EMODNET"
STORE_BLOB        = "Store BLOB"
IMPORT_HULL       = "IMPORT_HULL"
EXIT              = "Exit"

# Menu options dictionary
MENU_OPTIONS = {}
MENU_OPTIONS [ INVERT_XY ]         = "Invert XY coordinates"
MENU_OPTIONS [ PLOT_IM ]           = "Plot individual model"
MENU_OPTIONS [ EXIT ]              = "Exit"

# Plotting parameters
PLOT_GEOMETRY    = True
SHOW_IMAGE       = False
MAX_NR_OF_POINTS = 50000 

# EPSG code bases
EPSG_UTM_WGS84 = 32

# Logging levels
LOG_LEVEL = 'info'
LOGLEVELS = {'debug'   : logging.DEBUG,
             'info'    : logging.INFO,
             'warning' : logging.WARNING,
             'error'   : logging.ERROR,
             'critical': logging.CRITICAL}

# Defines for EMODNET
EMODNET_SEPARATOR     = ";"
EMODNET_GRIDSIZE      = float(0.00416667)
EMODNET_MISSING_VALUE = 0

# Defines for NetCDF
NETCDF_FLOAT                  = 'f'
NETCDF_DOUBLE_PRECISION_FLOAT = 'd'
NETCDF_INT                    = 'i'
NETCDF_LONG                   = 'l'
NETCDF_CHARACTER              = 'c'
NETCDF_BYTE                   = 'b'

# Defines for NetCDF CF convention
NETCDF_DIMENSION = 'area'

# CF dimensions
NETCDF_LON = 'position_long'
NETCDF_LAT = 'position_lat'
#NETCDF_LON = 'lon'
#NETCDF_LAT = 'lat'


# CF metadata attributes
NETCDF_VARIABLE_ATTRIBUTES = { 'units': 'units'
                               , 'standard_name' : 'standard_name'
                               , 'long_name' : 'long_name'
                               , '_FillValue' : '_FillValue'
                               , 'cell_methods' : 'cell_methods'
                               , 'start' : 'start'
                               , 'increment' : 'increment'
                               }

# CF global attributes
NETCDF_GLOBAL_ATTRIBUTES = { 'title': 'title'
                             , 'institution': 'institution'
                             , 'history': 'history'
                             , 'source': 'source'
                             , 'references': 'references'
                             , 'comment' : 'comment'
                             }

# CF cell methods
NETCDF_CELL_METHODS = { 'minimum': 'minimum'
                        , 'maximum': 'maximum'
                        , 'mean': 'mean'
                        , 'standard_deviation': 'standard_deviation'
                        , 'interpolations': 'interpolations'
                        , 'elementary_surfaces': 'elementary_surfaces'
                        , 'smoothed':  'smoothed'
                        , 'smoothed_offset': 'smoothed_offset'
                        }

# Database constants
INSERT_EDGES_STMT_ID = 8

# Geo constants
EARTH_PERIMETER = 40068000

# Shapely constants
MULTIPOLYGON = "MultiPolygon"
POLYGON      = "Polygon"



# Scalars
DEPTH     = "Depth"
AVG_DEPTH = "Average depth"
NR_DEPTHS = "Number of depths"
SCALARS   = [DEPTH, AVG_DEPTH, NR_DEPTHS]

#########################################
# GUI functions
#########################################

def gui_start () :
    while True :
        msg   = "What do you want?"
        options = [ MENU_OPTIONS [ PLOT_IM ], MENU_OPTIONS [ INVERT_XY ], MENU_OPTIONS [ EXIT ] ]
        reply=buttonbox(msg,None,options)
        if reply == MENU_OPTIONS [ PLOT_IM ] :
            plot_im ()
        elif reply == MENU_OPTIONS [ INVERT_XY ] :
            invert_xy ()
        elif reply == MENU_OPTIONS [ EXIT ] :
            break

def gui_show_parameters () :
    txt = ""
    for parameter in PARAMETER_LIST_VALUE :
        txt = txt + str(parameter) + ": " + str(PARAMETER_LIST_VALUE[parameter]) + "\n"
    title = "Parameters"
    msg  = "Parameter values"
    textbox(msg, title, txt, None)

def gui_parameter_import () :
    # Build gui for input
    while True :

        # Build GUI with parameters
        choices = []
        msg = ""
        for parameter in PARAMETER_LIST_VALUE :
            choices.append( str(parameter) )
            msg = msg + str(parameter) + ": " + str(PARAMETER_LIST_VALUE[parameter]) + "\n"
        reply=choicebox(msg,None,choices=choices)
        logger.info ( "Reply: " + str(reply) )

        # Set gui element for parameters
        diropenparameters  = ( )
        passwordparameters = ( )
        sensoparameters    = ( DB_TNS_SOURCE, DB_USER_SOURCE, DB_PASSWORD_SOURCE )
        enterboxparameters = ( GEOM_COL                                          )
        integerparameters  = ( OBJECT_CLASS_ID, OBJECT_INSTANCE_ID, CM_ID        )

        # Check on gui element and open correct gui element
        if str(reply) in diropenparameters :
            title = 'Parameter selection'
            msg   = 'Select ' + str(reply)
            dir   = diropenbox(msg, title, str(PARAMETER_LIST_VALUE[reply]) )
            PARAMETER_LIST_VALUE[reply] = str(dir)
        elif str(reply) in passwordparameters :
            title = 'Parameter selection'
            msg = "Enter password " + str(reply)
            password = passwordbox(msg,title,PARAMETER_LIST_VALUE[reply] )
            PARAMETER_LIST_VALUE[reply] = str(password)
        elif str(reply) in enterboxparameters :
            title = 'Parameter selection'
            msg   = "Enter value for " + str(reply)
            return_value = enterbox(msg,title,PARAMETER_LIST_VALUE[reply] )
            PARAMETER_LIST_VALUE[reply] = str(return_value)
        elif str(reply) in sensoparameters :
            title = 'Parameter selection'
            msg   = "Enter value for " + str(reply)
            field_names   = [ DB_TNS_SOURCE, DB_USER_SOURCE , DB_PASSWORD_SOURCE ]
            return_values = [ PARAMETER_LIST_VALUE [DB_TNS_SOURCE], PARAMETER_LIST_VALUE [DB_USER_SOURCE], PARAMETER_LIST_VALUE[DB_PASSWORD_SOURCE] ]
            return_values = multpasswordbox(msg,title, field_names, return_values)
            if return_values :
                PARAMETER_LIST_VALUE [DB_TNS_SOURCE]      = return_values[0]
                PARAMETER_LIST_VALUE [DB_USER_SOURCE]     = return_values[1]                
                PARAMETER_LIST_VALUE [DB_PASSWORD_SOURCE] = return_values[2]
        elif str(reply) in integerparameters :
            title = 'Parameter selection'
            msg   = "Enter value for " + str(reply)
            return_value = integerbox(msg, title, PARAMETER_LIST_VALUE [reply],0,9999999)
            PARAMETER_LIST_VALUE [reply] = int(return_value)
        else :
            break

#########################################
#  Store BLOB in database
#########################################

def gui_store_edition_blob() :
   
    logger.info( "Store BLOB in database")

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
    
    # Get Edition ID
    title = 'Edition ID'
    msg   = "Enter Edition ID "
    return_value = integerbox( msg, title, PARAMETER_LIST_VALUE [ OBJECT_INSTANCE_ID ],1,1000000)
    edition_id = int(return_value)

    # Get file to store
    title = 'File to import for edition '
    msg   = 'Enter file to import for edition '
    dir   = fileopenbox(msg, title, str(PARAMETER_LIST_VALUE [ BLOB_FILE ]) )
    blob_file_name_full = str(dir)
    blob_file_name      = os.path.basename ( blob_file_name_full )
    blob_attribute_name = 'SYS012'

    # Build database connection
    OracleConnection = DbConnectionClass ( PARAMETER_LIST_VALUE[ DB_USER_SOURCE ], PARAMETER_LIST_VALUE[ DB_PASSWORD_SOURCE ], PARAMETER_LIST_VALUE[ DB_TNS_SOURCE ], "MyGIS" )

    # Get ID of order from database
    order_id       = OracleConnection.get_order_id ( edition_id )
    order_class_id = 325

    # Plot parameters
    logger.info ( "Edition ID          = "  + str( edition_id )          )
    logger.info ( "Order class ID      = "  + str( order_class_id )      )
    logger.info ( "Order ID            = "  + str( order_id )            )
    logger.info ( "BLOB attribute name = "  + str( blob_attribute_name ) )
    logger.info ( "BLOB file name      = "  + str( blob_file_name )      )

    # Store BLOB
    OracleConnection.set_blob( order_class_id, order_id, blob_attribute_name, blob_file_name_full, blob_file_name )
    OracleConnection.commit_close()
    logger.info( str(blob_file_name) + " stored in database")

def gui_store_blob() :
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
    # Object class ID
    title = 'Object class ID'
    msg   = "Enter object class ID "
    return_value = integerbox( msg, title, PARAMETER_LIST_VALUE [ OBJECT_CLASS_ID ],1,500)
    PARAMETER_LIST_VALUE [ OBJECT_CLASS_ID ] = int(return_value)
    # Object instance ID
    title = 'Object instance ID'
    msg   = "Enter object instance ID "
    return_value = integerbox( msg, title, PARAMETER_LIST_VALUE [ OBJECT_INSTANCE_ID ],1,1000000)
    PARAMETER_LIST_VALUE [ OBJECT_INSTANCE_ID ] = int(return_value)
    # Attribute name
    title = 'BLOB Attribute name'
    msg   = "Enter BLOB Attribute name "
    return_value = enterbox( msg,title,PARAMETER_LIST_VALUE[ ATTRIBUTE_NAME ] )
    PARAMETER_LIST_VALUE[ ATTRIBUTE_NAME ] = str(return_value)
    # Get file to store
    title = 'File to import '
    msg   = 'Enter file to import '
    dir   = fileopenbox(msg, title, str(PARAMETER_LIST_VALUE [ BLOB_FILE ]) )
    PARAMETER_LIST_VALUE [ BLOB_FILE ] = str(dir)
    blob_file_name = os.path.basename ( PARAMETER_LIST_VALUE [ BLOB_FILE ] )
    # Plot parameters
    logger.info ( str( OBJECT_CLASS_ID)    + " = "  + str( PARAMETER_LIST_VALUE [ OBJECT_CLASS_ID ] ) )
    logger.info ( str( OBJECT_INSTANCE_ID) + " = "  + str( PARAMETER_LIST_VALUE [ OBJECT_INSTANCE_ID ] ) )
    logger.info ( str( ATTRIBUTE_NAME)     + " = "  + str( PARAMETER_LIST_VALUE [ ATTRIBUTE_NAME ] ) )
    logger.info ( str( BLOB_FILE)          + " = "  + str( PARAMETER_LIST_VALUE [ BLOB_FILE ] ) )
    logger.info ( "BLOB file name = "               + str( blob_file_name ) )
    # Build database connection
    OracleConnection = DbConnectionClass ( PARAMETER_LIST_VALUE[ DB_USER_SOURCE ], PARAMETER_LIST_VALUE[ DB_PASSWORD_SOURCE ], PARAMETER_LIST_VALUE[ DB_TNS_SOURCE ], "MyGIS" )
    OracleConnection.set_blob( PARAMETER_LIST_VALUE [ OBJECT_CLASS_ID ], PARAMETER_LIST_VALUE [ OBJECT_INSTANCE_ID ], PARAMETER_LIST_VALUE[ ATTRIBUTE_NAME ], PARAMETER_LIST_VALUE [ BLOB_FILE ], blob_file_name )
    OracleConnection.commit_close()
    logger.info( str(blob_file_name) + " stored in database")

#########################################
#  Database Class
#########################################

class DbConnectionClass:
    """Connection class to Oracle database"""

    def __init__(self, DbUser, DbPass, DbConnect, parent_module):
        try :
            self.logger = logging.getLogger( parent_module + '.DbConnection')
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

    def get_order_id ( self, edition_id) :
        """Function to get ID of order to store edition BLOB"""
        try:
            resultset = self.oracle_cursor.execute("select id from sdb_productorder where sys018 = :EditionId", EditionId = edition_id)
            if resultset :
                for row in resultset :
                    order_id = int(row[0])
            return order_id
        except Exception, err:
            self.logger.critical("Getting order ID from database failed: ERROR: " + str(err))
            sys.exit("Execution stopped")

    def set_blob ( self, object_class_id, object_instance_id, attribute_name, blob_file, file_name ) :
        """Function to store BLOB"""
        try :
            self.logger.info("Store BLOB in database")
            inputs = []
            inputs.append(open(blob_file, 'rb'))
            for input in inputs:
                binary_data = input.read()
                blobfile = self.oracle_cursor.var(cx_Oracle.BLOB)
                blobfile.setvalue(0, binary_data)
                self.oracle_cursor.callproc("sdb_interface_pck.setBlob", [object_class_id, object_instance_id, attribute_name, file_name, blobfile ])
        except Exception, err:
            self.logger.critical("Store BLOB in database failed: ERROR: " + str(err))
            sys.exit("Execution stopped")

    def commit_close( self ) :
	"""Function to commit and close connection"""
        self.oracle_connection.commit()
        self.oracle_connection.close()

####################################################
# Convertor functions
####################################################

def convert_meters_to_decimal_degrees ( distance_meters, latitude ) :
    distance_degrees = ( float(distance_meters) / ( EARTH_PERIMETER * math.cos(math.radians(latitude)) ) ) * 360
    return distance_degrees

def calculate_distance_on_sphere (lon1, lat1 ,lon2, lat2):

    # Calculates the distance between two points given their (lat, lon) co-ordinates.
    # It uses the Spherical Law Of Cosines (http://en.wikipedia.org/wiki/Spherical_law_of_cosines):
    #
    # cos(c) = cos(a) * cos(b) + sin(a) * sin(b) * cos(C)                        (1)
    #
    # In this case:
    # a = lat1 in radians, b = lat2 in radians, C = (lon2 - lon1) in radians
    # and because the latitude range is  [-?/2, ?/2] instead of [0, ?]
    # and the longitude range is [-?, ?] instead of [0, 2?]
    # (1) transforms into:
    #
    #  x = cos(c) = sin(a) * sin(b) + cos(a) * cos(b) * cos(C)
    #
    # Finally the distance is arccos(x)

    nautical_miles_per_lat_degree = float(60)
    meters_in_a_mile              = float(1852)

    if ((lat1 == lat2) and (lon1 == lon2)):
           return 0
    else :
        delta = lon2 - lon1
        a = math.radians(lat1)
        b = math.radians(lat2)
        C = math.radians(delta)
        x = math.sin(a) * math.sin(b) + math.cos(a) * math.cos(b) * math.cos(C)
        distance = math.acos(x) # in radians
        distance  = math.degrees(distance) # in degrees
        distance  = distance * nautical_miles_per_lat_degree # 60 nautical miles / lat degree
        distance = distance * meters_in_a_mile # 1852conversion to meters
        distance  = distance
        return distance

####################################################
# Douglas-Peuker algorithm
# pts = coordinate list ([(0,0),(0.5,0.5),(1,0),(1.25,-0.25),(1.5,.5)])
####################################################

def douglas_peuker ( ogr_line_string, tolerance ) :

    logger.info ( "Start Douglas-Peuker")

    # Write coordinate to list
    pts =[]
    for i in range(ogr_line_string.GetPointCount()) :
        point = [float(ogr_line_string.GetX(i)), float(ogr_line_string.GetY(i))]
        pts.append(point)    
    logger.info( "Number of point before " + str(i) )

    # Start algorithm
    anchor  = 0
    floater = len(pts) - 1
    stack   = []
    keep    = set()
    stack.append((anchor, floater))
    while stack:
        anchor, floater = stack.pop()
      
        # initialize line segment
        if pts[floater] != pts[anchor]:
            anchorX = float(pts[floater][0] - pts[anchor][0])
            anchorY = float(pts[floater][1] - pts[anchor][1])
            seg_len = math.sqrt(anchorX ** 2 + anchorY ** 2)
            # get the unit vector
            anchorX /= seg_len
            anchorY /= seg_len
        else:
            anchorX = anchorY = seg_len = 0.0
    
        # inner loop:
        max_dist = 0.0
        farthest = anchor + 1
        for i in range(anchor + 1, floater):
            dist_to_seg = 0.0
            # compare to anchor
            vecX = float(pts[i][0] - pts[anchor][0])
            vecY = float(pts[i][1] - pts[anchor][1])
            seg_len = math.sqrt( vecX ** 2 + vecY ** 2 )
            # dot product:
            proj = vecX * anchorX + vecY * anchorY
            if proj < 0.0:
                dist_to_seg = seg_len
            else: 
                # compare to floater
                vecX = float(pts[i][0] - pts[floater][0])
                vecY = float(pts[i][1] - pts[floater][1])
                seg_len = math.sqrt( vecX ** 2 + vecY ** 2 )
                # dot product:
                proj = vecX * (-anchorX) + vecY * (-anchorY)
                if proj < 0.0:
                    dist_to_seg = seg_len
                else:  # calculate perpendicular distance to line (pythagorean theorem):
                    dist_to_seg = math.sqrt(abs(seg_len ** 2 - proj ** 2))
                if max_dist < dist_to_seg:
                    max_dist = dist_to_seg
                    farthest = i

        if max_dist <= tolerance: # use line segment
            keep.add(anchor)
            keep.add(floater)
        else:
            stack.append((anchor, farthest))
            stack.append((farthest, floater))

    keep = list(keep)
    keep.sort()

    # Convert back to linestring
    ogr_line_out  = ogr.Geometry(ogr.wkbLineString)
    for i in keep :
        point = pts[i]
        ogr_line_out.AddPoint(float(point[0]),float(point[1]))
    logger.info( "Number of points after " + str(ogr_line_out.GetPointCount()) )

    return ogr_line_out

####################################################
# CGAL function to regenerate hull
####################################################

def Point_2_str(self):
    return "Point_2"+str((self.x(), self.y()))
    # now we turn it into a member function
Point_2.__str__ = Point_2_str

def cgal_generate_hull_edges ( coordinate_list, link_distance ) :
    """Function to generate edges of hull using cgal"""
    try :
        logger.info("Generate edges of hull")

        # Construct TIN and generate alpha shape; ? is the squared radius of the carving spoon.
        logger.info("Start hull generation from TIN using link distance of " + str(link_distance) )
        radius = ( link_distance / 2.0 ) ** 2.0
        tin = Alpha_shape_2()
        tin.make_alpha_shape(coordinate_list)
        tin.set_mode(Alpha_shape_2.Mode.REGULARIZED)
        tin.set_alpha(radius)
        alpha_shape_edges = []
        for it in tin.alpha_shape_edges:
            alpha_shape_edges.append(tin.segment(it))
        nr_of_edges = len(alpha_shape_edges)
        logger.info( str(nr_of_edges) + " edges generated")

        # Extract edges from TIN
        logger.info("Extract edges from TIN")
        edges = []
        id = 0
        for it in tin.alpha_shape_edges:
            id = id + 1
            x_coor_start = tin.segment(it).vertex(0).x()
            y_coor_start = tin.segment(it).vertex(0).y()
            x_coor_end   = tin.segment(it).vertex(1).x()
            y_coor_end   = tin.segment(it).vertex(1).y()
            edges.append((id, x_coor_start, y_coor_start, x_coor_end, y_coor_end))

        # Return array with edges
        return edges

    except Exception, err:
        logger.critical( "Genereate hull edges failed:ERROR: %s\n" % str(err))
        os.sys.exit("Execution stopped")

def regenerate_hull ( DbCursor, ogr_geom, link_distance, im_id ) :
    try :
        logger.info("Regenerate hull with higer level of detail")

        # TO DO:
        # For Multipolygon:
        # => Get each polygon:
        #   => For outer edge
        #      => Generate hull and get outer edge
        #   => For inner edge
        #      => Generate hull and get inner edge

        # Determine buffer
        logger.info("Determine buffer around hull")
        ogr_geom_boundary = ogr_geom.GetBoundary()
        boundary_type     = ogr_geom_boundary.GetGeometryName()
        logger.info ( "Geometry type boundary: " + str(boundary_type) )

        # Simplify boundary
        #ogr_geom_boundary = douglas_peuker ( ogr_geom_boundary, link_distance/2.0 )
        #ogr_geom_boundary = plot_geometry ( ogr_geom_boundary, None, None )

        distance         = link_distance
        ogr_geom_buffer  = ogr_geom_boundary.Buffer( distance )
        buffer_type      = ogr_geom_buffer.GetGeometryName()
        logger.info ( "Geometry type buffer: " + str(buffer_type) )

        #ogr_geom_out = plot_geometry ( ogr_geom_buffer, None, None )

        # Spatial query to get all points within boundary buffer and write to list
        logger.info("Get points in buffer from database")
        list_of_coordinates = []
        i                   = 0
        query_geom_wkt      = ogr_geom_buffer.ExportToWkt()
        db_wkt_geom         = DbCursor.var(cx_Oracle.CLOB)
        db_wkt_geom.setvalue(0, query_geom_wkt)
        select_clause       = "select hod.positie.sdo_point.x, hod.positie.sdo_point.y from sdb_hoogte_diepte hod "
        select_stmt         = select_clause + " where hod.wdg_id = :wdgId and sdo_anyinteract ( hod.positie, sdo_geometry( :polygon, 8307) ) = \'TRUE\' "
        DbCursor.arraysize  = 10000
        DbCursor.execute(select_stmt, wdgId = im_id, polygon = db_wkt_geom  )
        while True :
            coordinates = DbCursor.fetchmany()
            if not coordinates :
                break
            else :
                for coordinate in coordinates :
                    i = i + 1
                    x = float(coordinate[0])
                    y = float(coordinate[1])
                    list_of_coordinates.append(Point_2(x,y))
        logger.info ( str(i) + " points selected")

        # Generate hull edges
        logger.info ( "Generate new hull using TIN algorithm")
        DbCursor.prepare( DbCursor.callfunc("sdb_interface_pck.getclientdml", str, [INSERT_EDGES_STMT_ID]) )
        DbCursor.executemany(None, cgal_generate_hull_edges ( list_of_coordinates, link_distance ) )
        ogr_boundary_poly = ogr.CreateGeometryFromWkt( str(DbCursor.callfunc("sdb_envelope_pck.construct_geom_from_edges", cx_Oracle.CLOB ) ) )
        ogr_boundary_line = ogr_boundary_poly.GetBoundary()
        logger.info ( "Geometry type new boundary: " + str(ogr_boundary_line.GetGeometryName()) )
        logger.info ( "Number of linestrings     : " + str(ogr_boundary_line.GetGeometryCount()))
        ogr_geom_out = plot_geometry ( ogr_boundary_line, None, None )

        # TO DO:
        # => Merge inner and outer edges into multipolygon hull

    except Exception, err:
        logger.critical( "Regenerate hull with higer level of detail failed:ERROR: %s\n" % str(err))
        os.sys.exit("Execution stopped")


####################################################
# Function to check which GDAL create option to use
####################################################

def get_gdal_create_option ( driver_in ) :
    """Check which driver to use for GDAL"""
    metadata = driver_in.GetMetadata()
    if metadata.has_key(gdal.DCAP_CREATE) and metadata[gdal.DCAP_CREATE] == 'YES':
        message = 'Driver supports Create() method.'
    if metadata.has_key(gdal.DCAP_CREATECOPY) and metadata[gdal.DCAP_CREATECOPY] == 'YES':
        message = 'Driver supports CreateCopy() method.'
    return message

#########################################
#  Colormap functions
#########################################

def floatRgb(mag, cmin, cmax):
       """Return a tuple of floats between 0 and 1 for the red, green and blue amplitudes"""
       try:
              # normalize to [0,1]
              x = float(mag-cmin)/float(cmax-cmin)
       except:
              # cmax = cmin
              x = 0.5
       blue = min((max((4*(0.75-x), 0.)), 1.))
       red  = min((max((4*(x-0.25), 0.)), 1.))
       green= min((max((4*math.fabs(x-0.5)-1., 0.)), 1.))
       return (red, green, blue)

def range_to_rgb( **kwargs ):
       """Return a tuple of integers to be used in AWT/Java plots"""
       red, green, blue = floatRgb( kwargs["mag"], kwargs["cmin"], kwargs["cmax"] )
       return (int(red*255), int(green*255), int(blue*255))

def range_to_hex(mag, cmin, cmax):
       """Return a tuple of integers to be used in AWT/Java plots"""
       red, green, blue = range_to_rgb(mag, cmin, cmax)
       rgb = ( red, green, blue )
       hex_color = '#'+ str(struct.pack('BBB',*rgb).encode('hex'))
       return hex_color


#########################################
#  Polygon plot functions
#########################################

def invert_xy () :
    logger.info("Invert xy coordinates")
    default_location_in  = 'D:/Geodata/AsciiTest/ZSBVli2004_11RDNAP.txt'
    default_location_out = 'D:/Geodata/AsciiTest/MTJ_RD_file'
    file_in  = fileopenbox(msg="Select inputfile", title="File selection", default=default_location_in)
    file_out = filesavebox(msg="Save outputfile" , title="File save"     , default=default_location_out)

    # Read file
    separator = str(" ")
    zmin   = str(0)
    zmax   = str(10000)
    desc   = str("ignore")
    std    = str(0.1)
    nr     = str(10)
    zmulti = float(1)
    n = 0
    fIn  = open( file_in , 'r')
    fOut = open (file_out, 'w')
    for line in fIn :
        a = line.rstrip().split()
        if len(a) < 3 :
            logger.info("Can not process line " + str(a) )
        x = str(a[0])
        y = str(a[1])
        z = str(float(a[2])*zmulti)
        line_out = y + separator + x + separator + zmin + separator + zmax + separator + desc + separator + z + separator + std + separator + nr + "\n"
        #line_out = x + str(" ") + y + str(" ") + z + "\n"
        #line_out = x + str(" ") + y + str(" ") + z + str(" ") + z + str(" ") + z + "\n"
        fOut.write(line_out)
        n = n + 1
        if n % 100000 == 0 :
            logger.info( str(n) + " lines procesed" )
    fIn.close()
    fOut.close()
    logger.info( "Total number of lines processed: " + str(n) )

#########################################
#  Polygon plot functions
#########################################

# For plotting polygons with holes (from: http://sgillies.net/blog/1013/painting-punctured-polygons-with-matplotlib/)
def ring_coding(ob):
    # The codes will be all "LINETO" commands, except for "MOVETO"s at the
    # beginning of each subpath
    n = len(ob.coords)
    codes = ones(n, dtype=Path.code_type) * Path.LINETO
    codes[0] = Path.MOVETO
    return codes

def pathify(polygon):
    # Convert coordinates to path vertices. Objects produced by Shapely's
    # analytic methods have the proper coordinate order, no need to sort.
    # The underlying storage is made up of two parallel numpy arrays:
    # vertices: an Nx2 float array of vertices
    # codes: an N-length uint8 array of vertex types
    vertices = concatenate(
                    [asarray(polygon.exterior)]
                    + [asarray(r) for r in polygon.interiors])
    codes = concatenate(
                [ring_coding(polygon.exterior)]
                + [ring_coding(r) for r in polygon.interiors])
    return Path(vertices, codes)

#########################################
#  XML functions
#########################################

def build_xml ( object_instance_id, attribute_list ) :
               
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
        attribute = doc.createElement(str(attribute_key))
        row.appendChild(attribute)
        value = doc.createTextNode(str(attribute_list[attribute_key]))
        attribute.appendChild(value)
    
    # Get XML as string
    l_xml_document = doc.toxml()

    return l_xml_document

def write_xml_file ( file_name, xml_document ) :

    # Convert str to dom and write to file
    doc         = xml.dom.minidom.parseString(str(xml_document))
    file_object = open(file_name, "w")
    file_object.write (doc.toprettyxml())
    file_object.close()

#########################################
#  NetCDF Functions
#########################################

def convert_emodnet () :
    """Function to convert emodnetgrid to NETCDF"""

    logger.info( "Select EMODNET grid" )
    title        = 'Select EMODNET grid file'
    msg          = 'Select file'
    file         = fileopenbox(msg, title, str(PARAMETER_LIST_VALUE [ EMODNET_FILE ]))
    emodnet_file = str(file)
    (filepath, filename)   = os.path.split(emodnet_file)
    (shortname, extension) = os.path.splitext(filename)
    netcdf_file  = filepath + "\\" + shortname + ".nc"
    netcdf_generate_emodnet_grid ( emodnet_file, netcdf_file )

def netcdf_create_variable_array ( netcdf_file, CF_standard_name, dimension, data_type, canonical_unit, cell_method ) :

    """Function to create array for layer in NetCDF file"""
    logger.info ("Create NetCDF layer " + str(CF_standard_name))

    # Create variables for scalars
    variable  = netcdf_file.createVariable( CF_standard_name, data_type, dimension )

    # Add attributes to variable
    setattr(variable, NETCDF_VARIABLE_ATTRIBUTES['standard_name'] , CF_standard_name            )
    setattr(variable, NETCDF_VARIABLE_ATTRIBUTES['long_name']     , CF_standard_name            )
    setattr(variable, NETCDF_VARIABLE_ATTRIBUTES['units']         , canonical_unit              )
    setattr(variable, NETCDF_VARIABLE_ATTRIBUTES['cell_methods']  , 'area: ' + str(cell_method) )

    ## Initialize the new variable to missing value
    logger.info ("Populate array")
    variable_array = netcdf_file.variables[ CF_standard_name ]
    for i in range(variable.shape[0]):
        for j in range(variable.shape[1]):
            variable_array[int(i), int(j)] = EMODNET_MISSING_VALUE
    logger.info ("Array populated")

    return variable_array

def netcdf_generate_emodnet_grid ( input_file, output_file ) :
    """Function to generate EMODNET NetCDF file"""

    logger.info ( "Convert EMODNET Ascii file to EMODNET NetCDF file " )

    i = 0
    gridsize = EMODNET_GRIDSIZE 
    fIn = open( input_file, "r")

    # Read file to find dimensions of generated EODNET grid
    for line in fIn :
        a = line.rstrip().split(EMODNET_SEPARATOR)
        position_long         = float(a[0])
        position_lat          = float(a[1])

        # Get dimensions in long and lat
        if i == 0 :
            long_min = position_long
            long_max = position_long
            lat_min  = position_lat
            lat_max  = position_lat
            i = i + 1
        else :
            if position_long < long_min :
                long_min = position_long
            if position_long > long_max :
                long_max = position_long
            if position_lat < lat_min :
                lat_min = position_lat
            if position_lat > lat_max :
                lat_max = position_lat
            i = i + 1

    # Close file
    fIn.close()

    logger.info (  "Nr of lines = " + str(i)     )
    logger.info (  "Long_min    = " + str(long_min) )
    logger.info (  "Long_max    = " + str(long_max) )
    logger.info (  "Lat_min     = " + str(lat_min)  )
    logger.info (  "Lat_max     = " + str(lat_max)  )

    # Calculate dimensions (number of rows and columns)
    nr_lons = int ( round ( ( long_max - long_min ) / float(gridsize) , 0 ) ) + 1
    nr_lats = int ( round ( ( lat_max  - lat_min  ) / float(gridsize) , 0 ) ) + 1

    logger.info( "Long (x) dimension calculated (columns) = " + str(nr_lons) )
    logger.info( "Lat  (y) dimension calculated (rows)    = " + str(nr_lats) )

    # Open the NetCDF file for first time
    if os.path.exists ( output_file ) :
        os.remove( output_file )
    fOut = NetCDFFile( output_file , 'w')

    # Create some global attribute using a constant
    setattr(fOut, NETCDF_GLOBAL_ATTRIBUTES[ 'title' ]      , 'title'       )
    setattr(fOut, NETCDF_GLOBAL_ATTRIBUTES[ 'institution' ], 'institution' )
    setattr(fOut, NETCDF_GLOBAL_ATTRIBUTES[ 'source' ]     , 'source'      )
    setattr(fOut, NETCDF_GLOBAL_ATTRIBUTES[ 'history' ]    , 'history'     )
    setattr(fOut, NETCDF_GLOBAL_ATTRIBUTES[ 'references' ] , 'references'  )
    setattr(fOut, NETCDF_GLOBAL_ATTRIBUTES[ 'comment' ]    , 'comment'     )

    # Create the lat and lon dimensions.
    #lat = 180
    #lon = 360
    #fOut.createDimension(NETCDF_LON,lon)
    #fOut.createDimension(NETCDF_LAT,lat)
    fOut.createDimension(NETCDF_LON,nr_lons)
    fOut.createDimension(NETCDF_LAT,nr_lats)
    long_dimension     = ( NETCDF_LON, )
    lat_dimension      = ( NETCDF_LAT, )
    variable_dimension = ( NETCDF_LAT, NETCDF_LON )

    # Add dimensions as variables
    longitude_var = fOut.createVariable( 'lon', NETCDF_FLOAT, long_dimension )
    setattr(longitude_var, NETCDF_VARIABLE_ATTRIBUTES['standard_name'], 'longitude'   )
    setattr(longitude_var, NETCDF_VARIABLE_ATTRIBUTES['long_name']    , 'longitude'   )
    setattr(longitude_var, NETCDF_VARIABLE_ATTRIBUTES['units']        , 'degrees_east')
    setattr(longitude_var, NETCDF_VARIABLE_ATTRIBUTES['start']        , str( long_min - 0.5 * EMODNET_GRIDSIZE) )
    setattr(longitude_var, NETCDF_VARIABLE_ATTRIBUTES['increment']    , str(EMODNET_GRIDSIZE) )
    latitude_var = fOut.createVariable( 'lat', NETCDF_FLOAT, lat_dimension  )
    setattr(latitude_var, NETCDF_VARIABLE_ATTRIBUTES['standard_name'] , 'latitude'     )
    setattr(latitude_var, NETCDF_VARIABLE_ATTRIBUTES['long_name']     , 'latitude'     )
    setattr(latitude_var, NETCDF_VARIABLE_ATTRIBUTES['units']         , 'degrees_north')
    setattr(latitude_var, NETCDF_VARIABLE_ATTRIBUTES['start']        , str( lat_min - 0.5 * EMODNET_GRIDSIZE) )
    setattr(latitude_var, NETCDF_VARIABLE_ATTRIBUTES['increment']    , str(EMODNET_GRIDSIZE) )

    # Close the netCDF file
    fOut.close()

    # Reopen the NetCDF file to append scalars
    fOut = NetCDFFile( output_file , 'a')

    # Init scalar arrays (arrays ara initialized on disk in NetcCDF file)
    depth_min_array             = netcdf_create_variable_array ( fOut, 'depth_min'            , variable_dimension, NETCDF_FLOAT     , 'm', NETCDF_CELL_METHODS['minimum'] )
    depth_max_array             = netcdf_create_variable_array ( fOut, 'depth_max'            , variable_dimension, NETCDF_FLOAT     , 'm', NETCDF_CELL_METHODS['maximum'] )
    depth_average_array         = netcdf_create_variable_array ( fOut, 'depth_average'        , variable_dimension, NETCDF_FLOAT     , 'm', NETCDF_CELL_METHODS['mean'] )
    depth_stDev_array           = netcdf_create_variable_array ( fOut, 'depth_stDev'          , variable_dimension, NETCDF_FLOAT     , 'm', NETCDF_CELL_METHODS['standard_deviation'] )
    interpolations_array        = netcdf_create_variable_array ( fOut, 'interpolations'       , variable_dimension, NETCDF_INT       , '' , NETCDF_CELL_METHODS['interpolations'] )
    elementary_surfaces_array   = netcdf_create_variable_array ( fOut, 'elementary_surfaces'  , variable_dimension, NETCDF_INT       , '' , NETCDF_CELL_METHODS['elementary_surfaces'] )
    depth_smoothed_array        = netcdf_create_variable_array ( fOut, 'depth_smoothed'       , variable_dimension, NETCDF_FLOAT     , 'm', NETCDF_CELL_METHODS['smoothed'] )
    depth_smoothed_offset_array = netcdf_create_variable_array ( fOut, 'depth_smoothed_offset', variable_dimension, NETCDF_FLOAT     , 'm', NETCDF_CELL_METHODS['smoothed_offset'] )
    CDI_ID_array                = netcdf_create_variable_array ( fOut, 'CDI_ID'               , variable_dimension, NETCDF_CHARACTER , '' , '')
    DTM_source_array            = netcdf_create_variable_array ( fOut, 'DTM_source'           , variable_dimension, NETCDF_CHARACTER , '' , '')

    # Read files and write values to array
    logger.info ("Read files and write values to array")
    i                  = 0
    long_max           = 0
    lat_max            = 0
    overwritten_values = 0
    fIn = open( input_file, "r")
    for line in fIn :
        try :
            # Process line
            i = i + 1
            # Get attributes from line
            a = line.rstrip().split(EMODNET_SEPARATOR)
            # Get row and column in array
            latitude_row  = int ( round ( ( float(a[1]) - lat_min  ) / float(gridsize) , 0 ) )
            longitude_col = int ( round ( ( float(a[0]) - long_min ) / float(gridsize) , 0 ) )
            # For debugging
            # if latitude_row == 1394 and longitude_col == 2412 :
            #    logger.warning ( "File row " + str(i) + " : Overwriting depth value " + str(a[4]) +  " in NetCDF grid on row " + str(latitude_row) + " ( y = " + str(a[1])  + ") and column " + str(longitude_col) + " ( x = " + str(a[0]) + " )" )
            # Check for duplicate depths in source
            if float(depth_average_array[latitude_row, longitude_col]) <> float(EMODNET_MISSING_VALUE) :
                overwritten_values = overwritten_values + 1
                logger.debug ( "File row " + str(i) + " : Overwriting depth value " + str(a[4]) +  " in NetCDF grid on row " + str(latitude_row) + " ( y = " + str(a[1])  + ") and column " + str(longitude_col) + " ( x = " + str(a[0]) + " )" )
            if int(latitude_row) == 0 :
                logger.debug("Row: " + str(a[1]) + " at line " + str(i) )
                logger.debug("Col: " + str(longitude_col) + ", Row " + str(latitude_row) )
            if int(longitude_col) == 0 :
                logger.debug("Col:"  + str(a[0]) + " at line " + str(i) )
                logger.debug("Row: " + str(latitude_row) + ", Col " + str(longitude_col) )
            # Write values to array
            if a[2] :
                depth_min_array[latitude_row, longitude_col] = float( a[2] )
            if a[3] :
                depth_max_array[latitude_row, longitude_col] = float( a[3] )
            if a[4] :
                depth_average_array[latitude_row, longitude_col] = float( a[4] )
            if a[5] :
                depth_stDev_array[latitude_row, longitude_col] = float( a[5] )
            if a[6] :
                interpolations_array[latitude_row, longitude_col] = int( a[6] )
            if a[7] :
                elementary_surfaces_array[latitude_row, longitude_col] = int( a[7] )
            if a[8] :
                depth_smoothed_array[latitude_row, longitude_col] = float( a[8] )
            if a[9] :
                depth_smoothed_offset_array[latitude_row, longitude_col] = float( a[9] )
            if a[10] :
                CDI_ID_array[latitude_row, longitude_col] = str( a[10] )[:1]
            if a[11] :
                DTM_source_array[latitude_row, longitude_col] = str( a[11] )[:1]
            if i % 50000 == 0 :
                logger.info( str(i) + " rows written to file" )
        except Exception, err:
            logger.critical( "Writing line " + str(i) + " to NetCDF array failed: ERROR: %s\n" % str(err))
            logger.critical( "Row:    " + str(latitude_row)  )
            logger.critical( "Column: " + str(longitude_col) )
            logger.critical( "Min depth: " + str(a[2]) )
            logger.critical( "Max depth: " + str(a[3]) )
            logger.critical( "Avg depth: " + str(a[4]) )
            logger.critical( "Std depth: " + str(a[5]) )
            logger.critical( "Interpola: " + str(a[6]) )
            logger.critical( "Elementar: " + str(a[7]) )
            logger.critical( "Smootharr: " + str(a[8]) )
            logger.critical( "Smoothoff: " + str(a[9]) )
            logger.critical( "CDI_ID_ar: " + str(a[10]) )
            logger.critical( "DTM_sourc: " + str(a[11]) )
            os.sys.exit("Execution stopped")

    # Close inputfile and NetCDF file
    logger.info( str(i) + " rows written to file")
    logger.info( str(overwritten_values) + " points overwritten")
    fIn.close()
    fOut.close()

#########################################
#  GIS Functions
#########################################

def plot_geometry ( ogr_geom_in, color_table, attribute_id ) :
    """Function to plot geometry"""
    ring_index   = 0
    poly_index   = 0
    mult_index   = 0
    if ogr_geom_in.GetGeometryName() == 'MULTILINESTRING' :
         for nr_line in range ( ogr_geom_in.GetGeometryCount() ):
             ogr_line        = ogr_geom_in.GetGeometryRef( nr_line )
             ogr_geom_out    = plot_geometry ( ogr_line, None, None )
    if ogr_geom_in.GetGeometryName() == 'POINT' :
        x = []
        y = []
        x.append(ogr_geom_in.GetX())
        y.append(ogr_geom_in.GetY())
        pylab.plot(x,y,'o',color='y')
        ogr_geom_out = ogr_geom_in
    if ogr_geom_in.GetGeometryName() == 'MULTIPOINT' :
        for i in range(ogr_geom_in.GetGeometryCount()):
            ogr_point = ogr_geom_in.GetGeometryRef( i )
            ogr_geom_out = plot_geometry ( ogr_point, None, None )
    if ogr_geom_in.GetGeometryName() == 'MULTILINESTRING' :
        for i in range(ogr_geom_in.GetGeometryCount()):
            ogr_line = ogr_geom_in.GetGeometryRef( i )
            ogr_geom_out = plot_geometry ( ogr_line, None, None )
    if ogr_geom_in.GetGeometryName() == 'LINESTRING' :
        x = []
        y = []
        for i in range(ogr_geom_in.GetPointCount()) :
            x.append(ogr_geom_in.GetX(i))
            y.append(ogr_geom_in.GetY(i))
        pylab.plot(x,y,'-',color='g')
        ogr_geom_out = ogr_geom_in
    if ogr_geom_in.GetGeometryName() == 'POLYGON' :
        polygon      = ogr_geom_in
        polygon_out  = ogr.Geometry(ogr.wkbPolygon)
        for nr_ring in range ( polygon.GetGeometryCount() ):
            ring        = polygon.GetGeometryRef( nr_ring )
            ring_out    = ogr.Geometry(ogr.wkbLinearRing)
            if PLOT_GEOMETRY :
                x =[ring.GetX(i) for i in range(ring.GetPointCount()) ]
                y =[ring.GetY(i) for i in range(ring.GetPointCount()) ]
                if not color_table :
                    if ring_index == 0 :
                        pylab.plot(x,y,'-',color='r', linewidth=2.0, hold=True)
                    else :
                        pylab.plot(x,y,'-',color='b', linewidth=2.0, hold=True)
                else :
                    pylab.fill(x,y, fc = color_table[int(attribute_id)],ec = '0.7',lw=0.5)
            for i in range(ring.GetPointCount()) :
                x = float(ring.GetX(i))
                y = float(ring.GetY(i))
                ring_out.AddPoint(x,y)
            ring_out.CloseRings()
            ring_index = ring_index + 1
            logger.debug( "  Ring " + str(ring_index) + " Area " + str(ring_out.GetArea()) )
            polygon_out.AddGeometry(ring_out)
        poly_index = poly_index + 1
        logger.debug( "Polygon " + str(poly_index) + "; Area " + str(polygon_out.GetArea()) + "; Number of rings = " + str(polygon_out.GetGeometryCount()) )
        ogr_geom_out = polygon_out
    if ogr_geom_in.GetGeometryName() == 'MULTIPOLYGON' :
        multipolygon_out = ogr.Geometry(ogr.wkbMultiPolygon)
        for nr_polygon in range ( ogr_geom_in.GetGeometryCount() ) :
            polygon      = ogr_geom_in.GetGeometryRef( nr_polygon )
            polygon_out  = ogr.Geometry(ogr.wkbPolygon)
            for nr_ring in range ( polygon.GetGeometryCount() ):
                ring        = polygon.GetGeometryRef( nr_ring )
                ring_out    = ogr.Geometry(ogr.wkbLinearRing)
                if PLOT_GEOMETRY :
                    x =[ring.GetX(i) for i in range(ring.GetPointCount()) ]
                    y =[ring.GetY(i) for i in range(ring.GetPointCount()) ]
                    if not color_table :
                        if ring_index == 0 :
                            pylab.plot(x,y,'-',color='r', linewidth=2.0, hold=True)
                        else :
                            pylab.plot(x,y,'-',color='b', linewidth=2.0, hold=True)
                    else :
                        pylab.fill(x,y, fc = color_table[int(attribute_id)],ec = '0.7',lw=0.5)
                for i in range(ring.GetPointCount()) :
                    x = float(ring.GetX(i))
                    y = float(ring.GetY(i))
                    ring_out.AddPoint(x,y)
                ring_out.CloseRings()
                ring_index = ring_index + 1
                logger.debug( "    Ring " + str(ring_index) + " Area " + str(ring_out.GetArea()) )            
                polygon_out.AddGeometry(ring_out)
            poly_index = poly_index + 1
            ring_index = 0
            logger.debug( "  Polygon " + str(poly_index) + "; Area " + str(polygon_out.GetArea()) + "; Number of rings = " + str(polygon_out.GetGeometryCount()) )
            multipolygon_out.AddGeometry(polygon_out)
        mult_index = mult_index + 1
        logger.debug( "MultiPolygon " + str(mult_index) + " Area " + str(multipolygon_out.GetArea()) )
        ogr_geom_out = multipolygon_out
    return ogr_geom_out

########################################
#  Read hull file and validate on DB
########################################

def getCoordTrans ( x_min, x_max, y_min, y_max, epsg_code_in ) :
    """"Function te get coordinate transformation to UTM"""

    # Determine UTM zone
    utm_zone = int ((((x_max + x_min)/2.0) + 180.0 ) / 6.0 )
    if int( (y_max + y_min)/2.0 ) >= int(0) :
        hemisphere         = "N"
        epsg_hemisphere_id = 6
    else :
        hemisphere         = "S"
        epsg_hemisphere_id = 7
    epsg_code_out = str(EPSG_UTM_WGS84) + str(epsg_hemisphere_id) + str(utm_zone)
    logger.info("UTM zone  = " + str(utm_zone) + str(hemisphere))
    logger.info("EPSG code = " + str(epsg_code_out))

    # Execute coordinate transformation
    source_srs       = osr.SpatialReference()
    source_srs.ImportFromEPSG(int(epsg_code_in))
    target_srs       = osr.SpatialReference()
    target_srs.ImportFromEPSG(int(epsg_code_out))
    coordinate_trans = osr.CoordinateTransformation(source_srs,target_srs)

    return coordinate_trans

def read_geometry_from_file() :
    """"Function to read hull from George"""
    coord_trans = getCoordTrans (2, 4, 50, 54 ,4326)
    remove_duplicate_vertices = "T"
    msg = "Select file"
    title = "File selection"
    PARAMETER_LIST_VALUE [ DIRECTORY ] = "P:/SENS Products/04. SENS Bathy/01. General/09. Developers manual/Test scenarios/Test hulls Triangle/"
    filename = fileopenbox ( msg, title, PARAMETER_LIST_VALUE [ DIRECTORY ] )
    input_file  = os.path.basename( filename )
    is_exterior = True
    nr_polygons    = 0
    nr_of_vertices = 0
    nr_rings       = 0
    # Init polygon
    first_polygon = True
    multipolygon = ogr.Geometry(ogr.wkbMultiPolygon)
    fIn = open( filename, 'r')
    # Process vertices ( x y ring_indicator)
    for line in fIn :
        if len(line.rstrip().split()) == 3 :
            # Process vertex
            nr_of_vertices = nr_of_vertices + 1
            x = float(line.rstrip().split()[0])
            y = float(line.rstrip().split()[1])
            i = int(line.rstrip().split()[2])
            if i == 1 :
                is_exterior = True
            if i == 0:
                is_exterior = False
            if is_exterior and nr_of_vertices == 1 and first_polygon == True :
                first_polygon = False
                polygon  = ogr.Geometry(ogr.wkbPolygon)
                nr_polygons = nr_polygons + 1
                print "First polygon number = " + str(nr_polygons)
                nr_rings = 0
                exterior = ogr.Geometry(ogr.wkbLinearRing)
                nr_rings = nr_rings + 1
                exterior.AddPoint(x,y)
                x_previous = x
                y_previous = y
            elif is_exterior and nr_of_vertices == 1 and first_polygon == False :
                multipolygon.AddGeometry(polygon)
                nr_rings = 0
                polygon  = ogr.Geometry(ogr.wkbPolygon)
                nr_polygons = nr_polygons + 1
                exterior = ogr.Geometry(ogr.wkbLinearRing)
                nr_rings = nr_rings + 1
                exterior.AddPoint(x,y)
                x_previous = x
                y_previous = y
            if is_exterior and nr_of_vertices > 1 :
                exterior.AddPoint(x,y)
            if not is_exterior and nr_of_vertices == 1 :
                interior = ogr.Geometry(ogr.wkbLinearRing)
                nr_rings = nr_rings + 1
                interior.AddPoint(x,y)
                x_previous = x
                y_previous = y
            if not is_exterior and nr_of_vertices > 1 :
                interior.AddPoint(x,y)
            # Calculate length between vertices
            if x <> x_previous and y <> y_previous :
                p1  = ogr.Geometry(ogr.wkbPoint)
                p2  = ogr.Geometry(ogr.wkbPoint)
                p1.AddPoint_2D (x,y)
                p2.AddPoint_2D (x_previous,y_previous)
                p1.Transform(coord_trans)
                p2.Transform(coord_trans)
                distance = float(p1.Distance(p2))
                if distance < float(0.1) :
                    print "Distance " + str(p1.Distance(p2)) + " polygon " + str(nr_polygons) + " ring " + str(nr_rings) + " vertex " + str(nr_of_vertices)
                x_previous = x
                y_previous = y
        else :
            # Close rings
            if is_exterior :
                exterior.CloseRings()
                polygon.AddGeometry(exterior)
                nr_of_vertices = 0
                print "Close exterior " + str(nr_polygons)
            if not is_exterior :
                interior.CloseRings()
                polygon.AddGeometry(interior)
                nr_of_vertices = 0
                print "Close interior " + str(nr_rings) + " of polygon " + str(nr_polygons)
    # Process last ring
#    if is_exterior :
#        print "Close last exterior " + str(nr_polygons)
#        exterior.CloseRings()
#        polygon.AddGeometry(exterior)
#    if not is_exterior :
#        print "Close last interior " + str(nr_rings) + " of polygon " + str(nr_polygons)
#        interior.CloseRings()
#        polygon.AddGeometry(interior)
    multipolygon.AddGeometry(polygon)
    fIn.close()
    multipolygon.FlattenTo2D()
    multipolygon_wkt = multipolygon.ExportToWkt()
    OracleConnection = cx_Oracle.connect ( PARAMETER_LIST_VALUE[ DB_USER_SOURCE ], PARAMETER_LIST_VALUE[ DB_PASSWORD_SOURCE ], PARAMETER_LIST_VALUE[ DB_TNS_SOURCE ] )
    DbCursor         = OracleConnection.cursor()
    epsg_code_db     = int(8307)
    geom_in          = DbCursor.var(cx_Oracle.CLOB)
    geom_in.setvalue(0, multipolygon_wkt)
    InsertCursor     = OracleConnection.cursor()
    InsertCursor.execute( "Delete from MTJ_FEATURE_OBJECT where feature_code = :1", { '1' : input_file, } )
    InsertCursor.execute( "insert into MTJ_FEATURE_OBJECT (feature_code,geometry) values ( :1, sdo_geometry( :2, :3 ) )", { '1' : input_file, '2' : geom_in, '3' : epsg_code_db, } )
    SelectCursor     = OracleConnection.cursor()
    if remove_duplicate_vertices == "T" :
        SelectCursor.execute( "select sdo_geom.validate_geometry_with_context( SDO_UTIL.REMOVE_DUPLICATE_VERTICES(f.geometry,0.05), 0.05  ) from mtj_feature_object f where feature_code = :1", { '1' : input_file,  } )
    else :
        SelectCursor.execute( "select sdo_geom.validate_geometry_with_context( f.geometry, 0.05  ) from mtj_feature_object f where feature_code = :1", { '1' : input_file,  } )
    resultset = SelectCursor.fetchall()
    if resultset :
        for row in resultset :
            validation_result = str(row[0])
    msgbox("Validation result is " + str(validation_result), ok_button="Close")
    msg   = "Do you want to store geometry in database?"
    title = "Database storage"
    if ccbox(msg, title):
        ProcedureCursor     = OracleConnection.cursor()
        ProcedureCursor.callproc("mtj_store_elements" , [input_file, remove_duplicate_vertices] )
        print "Elements stored in database"
        ProcedureCursor.callproc("mtj_store_vertices" , [input_file, remove_duplicate_vertices] )
        print "Vertices stored in database"
        OracleConnection.commit()
        OracleConnection.close()
        print "Import hull finished"
        print "Validation result is " + str(validation_result)
    else :
        OracleConnection.commit()
        OracleConnection.close()
    # select element_id, ring_id, geometry from mtj_geometry_elements where element_id = :1 and ring_id = :2
    # select element_id, ring_id, vertext_id, geometry from mtj_vertices where element_id = :1 and ring_id = :2

def write_geometry_to_file ( ogr_geom_in, fOut ) :
    """Function write coordinate of geometry to file"""
    if ogr_geom_in.GetGeometryName() == 'MULTILINESTRING' :
         for nr_line in range ( ogr_geom_in.GetGeometryCount() ):
             write_geometry_to_file ( ogr_geom_in.GetGeometryRef( nr_line ), fOut )
    if ogr_geom_in.GetGeometryName() == 'MULTIPOINT' :
        for i in range(ogr_geom_in.GetGeometryCount()):
            write_geometry_to_file ( ogr_geom_in.GetGeometryRef( i ), fOut )
    if ogr_geom_in.GetGeometryName() == 'MULTIPOLYGON' :
        for nr_polygon in range ( ogr_geom_in.GetGeometryCount() ) :
            write_geometry_to_file ( ogr_geom_in.GetGeometryRef( nr_polygon ), fOut )
    if ogr_geom_in.GetGeometryName() == 'POINT' :
        x = str(ogr_geom_in.GetX())
        y = str(ogr_geom_in.GetY())
        fOut.write( x + " " + y + "\n" )
        fOut.write( "\n" )
    if ogr_geom_in.GetGeometryName() == 'LINESTRING' :
        for i in range(ogr_geom_in.GetPointCount()) :
            x = str(ogr_geom_in.GetX(i))
            y = str(ogr_geom_in.GetY(i))
            fOut.write( x + " " + y + "\n" )
        fOut.write( "\n" )
    if ogr_geom_in.GetGeometryName() == 'POLYGON' :
        # exterior ring = 1
        # interior ring = 0
        polygon      = ogr_geom_in
        exterior     = str(1)
        for nr_ring in range ( polygon.GetGeometryCount() ):
            ring     = polygon.GetGeometryRef( nr_ring )
            for i in range(ring.GetPointCount()) :
                x = str(ring.GetX(i))
                y = str(ring.GetY(i))
                fOut.write( x + " " + y + " " + exterior  + "\n" )
            fOut.write( "\n" )
            exterior = str(0)
        #fOut.write( "-----------------------------------------\n" )

#########################################

def plot_depth_profile () :
    """ Get depth profile from database and plot"""

    logger.info( "Build database connection to " + str(PARAMETER_LIST_VALUE[ DB_USER_SOURCE ]) )
    DbConnection  = cx_Oracle.connect( PARAMETER_LIST_VALUE[ DB_USER_SOURCE ], PARAMETER_LIST_VALUE[ DB_PASSWORD_SOURCE ], PARAMETER_LIST_VALUE[ DB_TNS_SOURCE ])
    DbCursor      = DbConnection.cursor()
    cm_id         = 86271
    x_start       = -70.5
    y_start       = 42.9
    x_end         = -70.5
    y_end         = 43.0
    smooth_factor = 0
    logger.info("Get depth profile from database")
    depth_profile = DbCursor.callfunc( "sdb_interface_pck.getDepthProfile", str, [ cm_id, x_start, y_start, x_end, y_end, smooth_factor ] )
    x_z_list      = depth_profile.rstrip().split('|')
    print x_z_list
    x = []
    y = []
    for i in range(len(x_z_list)) :
        if i % 2 <> 0 and int(len(x_z_list[i])) > 0 :
            logger.info("Value from list: " + str(x_z_list[i]))
            x.append(float(x_z_list[i]))
        if i % 2 == 0 and int(len(x_z_list[i])) > 0 :
            logger.info("Value from list: " + str(x_z_list[i]))
            y.append(float(x_z_list[i]))
    DbConnection.close()
    logger.info("Plot depth profile")
    # x and y are inverted do not know why?
    pylab.plot(y,x,'-',color='y')
    pylab.xlabel("Distance along profile")
    pylab.ylabel("Depth")
    pylab.grid(True)
    pylab.title("Depth profile")
    pylab.show()


def plot_test_geometry () :
    """"Function to plot test geometry"""

    # Plot polygons for testing
    p1                     = 'POLYGON((2.0748 52.022,3.23284 52.022,3.23284 51.3995,2.0748 51.3995,2.0748 52.022))'
    p2                     = 'POLYGON ((2.2675283 51.5592343, 3.02570607 51.5592343, 3.02570607 51.8751554, 2.2675283 51.8751554, 2.2675283 51.5592343))'
    polygon                = 'POLYGON ((30 10, 10 20, 20 40, 40 40, 30 10))'
    polygon_with_hole      = 'POLYGON ((35 10, 10 20, 15 40, 45 45, 35 10),(20 30, 35 35, 30 20, 20 30))'
    multipolygon           = 'MULTIPOLYGON (((30 20, 10 40, 45 40, 30 20)),((15 5, 40 10, 10 20, 5 10, 15 5)))'
    multipolygon_with_hole = 'MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)),((20 35, 45 20, 30 5, 10 10, 10 30, 20 35),(30 20, 20 25, 20 15, 30 20)))'

    ogr_p1 = ogr.CreateGeometryFromWkt(p1)
    ogr_p2 = ogr.CreateGeometryFromWkt(p2)

    plot_geometry ( ogr_p1, None, None )
    plot_geometry ( ogr_p2, None, None )
 
    # Show map
    pylab.show()

#########################################

def plot_query () :

    logger.info ( "Plot geometries from query")

    # Add to wkt function to geometry column
#    query_in          = enterbox(msg='Enter query', title='Plot spatial query result', default='select sys_geom001 from sdb_individualmodel where id = 217870', strip=True)
#    query_elements    = query_in.rstrip().split()
#    query_elements[1] = 'sdo_util.to_wktgeometry(' + str(query_elements[1]) + ')'
#    query_out         = ''
#    for i in range(len(query_elements)) :
#        query_out = query_out + ' ' + str(query_elements[i])
#    logger.info ( "Select query is: " + str(query_out) )

    # Get IM hull
    im_id     = enterbox(msg='Enter IM ID', title='Individual model', default='234398', strip=True)
    query_out = 'select sdo_util.to_wktgeometry(sys_geom001) from sdb_individualmodel where id = ' + str(im_id)
    logger.info( "Build database connection to " + str(PARAMETER_LIST_VALUE[ DB_USER_SOURCE ]) )
    logger.info( "Get points")
    DbConnection       = cx_Oracle.connect( PARAMETER_LIST_VALUE[ DB_USER_SOURCE ], PARAMETER_LIST_VALUE[ DB_PASSWORD_SOURCE ], PARAMETER_LIST_VALUE[ DB_TNS_SOURCE ])
    DbCursor           = DbConnection.cursor()
    DbCursor.arraysize = 100000
    logger.info(query_out)
    DbCursor.execute( query_out )
    resultset = DbCursor.fetchall()
    if resultset :
        # Init plot
        fig = pylab.figure()
        ax  = fig.add_subplot(111)
        # get geometries and plot
        for row in resultset :
            #plot_geometry ( ogr.CreateGeometryFromWkt(str(row[0])), None, None )
            ogr_geom        = ogr.CreateGeometryFromWkt(str(row[0]))
            shapely_polygon = loads(ogr_geom.ExportToWkb())
            logger.info ( "Geometry type: " + str(shapely_polygon.geom_type) )
            if str(shapely_polygon.geom_type) == MULTIPOLYGON :
                for polygon_geom in list(shapely_polygon.geoms) :
                    polygon_path    = pathify(polygon_geom)
                    patch           = patches.PathPatch(polygon_path, facecolor='orange', lw=1)
                    ax.add_patch(patch)
            if str(shapely_polygon.geom_type) == POLYGON :
                polygon_path    = pathify(shapely_polygon)
                patch           = patches.PathPatch(polygon_path, facecolor='orange', lw=1)
                ax.add_patch(patch)
    DbConnection.close()

    # Write to file
    dir_name  = diropenbox('Output directory', 'Select output directory', 'P:/SENS Products/04. SENS Bathy/01. General/09. Developers manual/Test scenarios/Test hulls Triangle')
    file_name = dir_name + '/hull_'+ str(im_id) + '.txt'
    fOut = open ( file_name, 'w' )
    write_geometry_to_file ( ogr_geom, fOut )
    fOut.close()

    # Get points from IM
    query_out = 'select hod.positie.sdo_point.x, hod.positie.sdo_point.y, hod.depth from sdb_hoogte_diepte hod where hod.wdg_id = ' + str(im_id)
    logger.info( "Build database connection to " + str(PARAMETER_LIST_VALUE[ DB_USER_SOURCE ]) )
    logger.info( "Get points")
    file_name = dir_name + '/pnts_'+ str(im_id) + '.txt'
    fOut = open ( file_name, 'w' )
    DbConnection       = cx_Oracle.connect( PARAMETER_LIST_VALUE[ DB_USER_SOURCE ], PARAMETER_LIST_VALUE[ DB_PASSWORD_SOURCE ], PARAMETER_LIST_VALUE[ DB_TNS_SOURCE ])
    DbCursor           = DbConnection.cursor()
    DbCursor.arraysize = 100000
    DbCursor.execute( query_out )
    while True :
        resultset = DbCursor.fetchmany()
        if not resultset :
            break
        else :
            for result in resultset :
                fOut.write( str(result[0]) + " " + str(result[1]) + " "  + str(result[2]) +  "\n" )
    fOut.close()

    # Now plot the map
    ax.set_xlim((-180.0,180.0))
    ax.set_ylim((-90.0,90.0))
    pylab.xlabel("Longitud")
    pylab.ylabel("Latitud")
    pylab.grid(True)
    pylab.title("Selected geometries")
    pylab.show()
    
#########################################

def plot_cm () :
    """"Function to plot coookies of CM"""

    logger.info( "Plot continuous model" )

    # MBR coordinates
    x_ll = 2
    y_ll = 52
    x_ur = 3
    y_ur = 53

    # Initialize geometries
    mbr  = ogr.Geometry(ogr.wkbPolygon)
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(x_ll,y_ll)
    ring.AddPoint(x_ur,y_ll)
    ring.AddPoint(x_ur,y_ur)
    ring.AddPoint(x_ll,y_ur)
    ring.CloseRings()
    mbr.AddGeometry(ring)
    mbr_wkt = mbr.ExportToWkt() 

    # Build colormap
    im_type_colormap = {796:'#A6761D',797:'#E6AB02',798:'#66A61E',799:'#E7298A',800:'#7570B3',5135:'#D95F02'}

    # Build database connection
    logger.info( "Build database connection to " + str(PARAMETER_LIST_VALUE[ DB_USER_SOURCE ]) )
    DbConnection = cx_Oracle.connect( PARAMETER_LIST_VALUE[ DB_USER_SOURCE ], PARAMETER_LIST_VALUE[ DB_PASSWORD_SOURCE ], PARAMETER_LIST_VALUE[ DB_TNS_SOURCE ])
    DbCursor     = DbConnection.cursor()
    
    # Query to select cookies
    logger.info( "Query IM segments of individual model" )
    cm_id = PARAMETER_LIST_VALUE [ CM_ID ] 
    stmt  = 'select c.sys_geom501.Get_WKT(), i.sys009 from sdb_cookie c, sdb_individualmodel i where c.sys503 = i.id and c.sys502 = :CM_ID '
    DbCursor.arraysize = 100000
    DbCursor.execute( stmt, CM_ID = cm_id )
    resultset = DbCursor.fetchmany()
    if resultset :
        for row in resultset :
             ogr_geom_out = plot_geometry ( ogr.CreateGeometryFromWkt(str(row[0])), im_type_colormap, int(row[1]) ) 

    # Close database connection
    DbConnection.close()

    # Build legend
    p1 = pylab.Rectangle((0, 0), 1, 1, fc="#A6761D")
    p2 = pylab.Rectangle((0, 0), 1, 1, fc="#E6AB02")
    p3 = pylab.Rectangle((0, 0), 1, 1, fc="#66A61E")
    p4 = pylab.Rectangle((0, 0), 1, 1, fc="#E7298A")
    p5 = pylab.Rectangle((0, 0), 1, 1, fc="#7570B3")
    p6 = pylab.Rectangle((0, 0), 1, 1, fc="#D95F02")

    # Plot legend
    pylab.legend([p1,p2,p3,p4,p5,p6], ["Multibeam","Singlebeam","Laser altimetry","Track line","Model","Extracted model"], loc = 4)    

    # Now plot the map
    pylab.axis('equal')
    pylab.xlabel("Longitud")
    pylab.ylabel("Latitud")
    pylab.grid(True)
    pylab.title("Continuous model")
    pylab.show()                                              

    logger.info( "Plot continuous model completed" )

#########################################

def plot_im () :
    """Function to plot points of individual model"""

    logger.info( "Plot individual model points" )

    # Set coordinate system in and out and coordinate transformation
    epsg_code_in     = 4326
    source_srs       = osr.SpatialReference()
    source_srs.ImportFromEPSG(int(epsg_code_in))

    ############################
    # Build database connection
    ############################

    logger.info( "Build database connection to " + str(PARAMETER_LIST_VALUE[ DB_USER_SOURCE ]) )
    DbConnection = cx_Oracle.connect( PARAMETER_LIST_VALUE[ DB_USER_SOURCE ], PARAMETER_LIST_VALUE[ DB_PASSWORD_SOURCE ], PARAMETER_LIST_VALUE[ DB_TNS_SOURCE ])
    DbCursor     = DbConnection.cursor()

    ################################
    # Build IM list from database
    ################################

    # Get list of IDs from database
    im_name_list = []
    stmt  = "select i.name from sdb_individualmodel i, sdb_pointstore_info p where i.id = p.instanceid"
    DbCursor.arraysize = 100000
    DbCursor.execute(stmt)
    resultset = DbCursor.fetchmany()
    if resultset :
        for row in resultset :
            im_name_list.append(str(row[0]))

    # Popup select box
    msg     = "Select individual model"
    title   = "Individual model"
    im_name = choicebox(msg, title, im_name_list)

    stmt  = "select id, sys026 from sdb_individualmodel where name = :NAME"
    DbCursor.execute(stmt, NAME = im_name )
    resultset = DbCursor.fetchmany()
    if resultset :
        for row in resultset :
            PARAMETER_LIST_VALUE [ OBJECT_INSTANCE_ID ] = int(row[0])
            link_distance_meters = float(row[1])

    stmt  = "select  sdo_util.to_wktgeometry(sdo_aggr_centroid(SDOAGGRTYPE(sys_geom001,0.05))) from sdb_individualmodel where name = :NAME"
    DbCursor.execute(stmt, NAME = im_name )
    resultset = DbCursor.fetchmany()
    if resultset :
        for row in resultset :
            ogr_point            = ogr.CreateGeometryFromWkt(str(row[0]))
            avg_latitude         = ogr_point.GetY()

    ################################
    # Select scalar to display
    ################################

    logger.info("Select which scalar to display")
    msg    = "Which scalar do you want to display?"
    title  = "Scalar selection"
    scalar = choicebox(msg, title, SCALARS )

    ################################
    # Get hull of individual model
    ################################

    logger.info( "Get geometry for object instance " + str(PARAMETER_LIST_VALUE[OBJECT_INSTANCE_ID]) + " from object class " + str(PARAMETER_LIST_VALUE[OBJECT_CLASS_ID]) )  

    geom_cursor = DbCursor.callfunc("sdb_interface_pck.getGeomAsWkt", cx_Oracle.CURSOR, [ PARAMETER_LIST_VALUE[OBJECT_CLASS_ID], PARAMETER_LIST_VALUE[OBJECT_INSTANCE_ID], PARAMETER_LIST_VALUE[GEOM_COL] ])
    for geom in geom_cursor :
        geom_wkt = str(geom[1])
    ogr_geom_in = ogr.CreateGeometryFromWkt(geom_wkt)

    ####################
    # Process hull
    ####################

    logger.info( "Process geometry " + str(ogr_geom_in.GetGeometryName()) )

    ogr_geom_out = plot_geometry ( ogr_geom_in, None, None ) 

    logger.info ( "IM geometry processed and plotted" )

    #    message = "Do you want to smooth the hull?"
    #    title   = "Smooth hull"
    #
    #    if boolbox(message, title, ["Yes", "No"]) :
    #
    #        regenerate_hull ( DbCursor, ogr_geom_in, link_distance, PARAMETER_LIST_VALUE[OBJECT_INSTANCE_ID] )
    #
    #        logger.info("Run Douglas-Peuker on hull")
    #        link_distance     = convert_meters_to_decimal_degrees ( link_distance_meters, avg_latitude )
    #        ogr_geom_boundary = ogr_geom_in.GetBoundary()
    #        boundary_type     = ogr_geom_boundary.GetGeometryName()
    #        logger.info( "Link distance " + str(link_distance) )
    #        logger.info ( "Geometry type boundary: " + str(boundary_type) )
    #        ogr_line_smoothed =  douglas_peuker ( ogr_geom_boundary, link_distance/4.0 )
    #
    #        plot_geometry ( ogr_line_smoothed, None, None )

    ########################################################
    # Get shallowest and deepest point for IM from database
    ########################################################

    logger.info("Get shallowest and deepest point of IM from database")

    # Attributes to retrieve
    NR_OF_POINTS     = "SYS012"
    DEEPEST_POINT    = "SYS021"
    SHALLOWEST_POINT = "SYS022"

    # Build database connection
    OracleConnection = DbConnectionClass ( PARAMETER_LIST_VALUE[ DB_USER_SOURCE ], PARAMETER_LIST_VALUE[ DB_PASSWORD_SOURCE ], PARAMETER_LIST_VALUE[ DB_TNS_SOURCE ], "MyGIS" )

    # Get values from database
    attributes   = [ SHALLOWEST_POINT, DEEPEST_POINT, NR_OF_POINTS ]
    values       = OracleConnection.get_obj_attributes ( PARAMETER_LIST_VALUE [ OBJECT_CLASS_ID ], PARAMETER_LIST_VALUE [ OBJECT_INSTANCE_ID ], attributes )
    shallowest   = float(values[0])
    deepest      = float(values[1])
    nr_of_points = int(values[2])

    # Close DB connection
    OracleConnection.commit_close()

    depth_range = abs(deepest - shallowest)

    logger.info("Shallowest point of IM = " + str(shallowest))
    logger.info("Deepest point of IM    = " + str(deepest))
    logger.info("Depth range            = " + str(depth_range))
    logger.info("Number of points       = " + str(nr_of_points))

    ################################################
    # Get points for individualmodel from database
    ################################################

    logger.info( "Read points from database" )

    # Skip datapoints when file is too big to handle
    if int(nr_of_points) > int( MAX_NR_OF_POINTS ) :
        step = round(float(nr_of_points)/float(MAX_NR_OF_POINTS))
    else :
        step = 1

    # Get points from database
    x = []
    y = []
    z = []
    i = int(0)
    j = int(0)
    if scalar == DEPTH :
        stmt = 'select x, y, z from table ( sdb_pointstore_pck.readDepthsAsRecord ( :ID ) ) '
    if scalar == AVG_DEPTH or scalar == NR_DEPTHS :
        # Forst get grid properties
        stmt = "select min(row_nr), max(row_nr), min(col_nr), max(col_nr) from  sdb_pointstore where instance_id = :ID "
        DbCursor.execute(stmt, ID = PARAMETER_LIST_VALUE[OBJECT_INSTANCE_ID] )
        resultset = DbCursor.fetchmany()
        if resultset :
            for row in resultset :
                min_row_nr = int(row[0])
                max_row_nr = int(row[1])
                min_col_nr = int(row[2])
                max_col_nr = int(row[3])
        stmt = "select minx, maxx ,miny, maxy from sdb_pointstore_info where instanceid = :ID "
        DbCursor.execute(stmt, ID = PARAMETER_LIST_VALUE[OBJECT_INSTANCE_ID] )
        resultset = DbCursor.fetchmany()
        if resultset :
            for row in resultset :
                minx = float(row[0])
                maxx = float(row[1])
                miny = float(row[2])
                maxy = float(row[3])
        gridsize_x = float((maxx - minx)/max_col_nr)
        print gridsize_x
        gridsize_y = float((maxy - miny)/max_row_nr)
        print gridsize_y
        logger.info("Gridsize in x direction: " + str(gridsize_x))
        logger.info("Gridsize in y direction: " + str(gridsize_y))
        if scalar == AVG_DEPTH :
            scalar_column = "Z_AVG"
        if scalar == NR_DEPTHS :
            scalar_column = "NR_POINTS"
        stmt = 'select ' + str(minx) + ' + ' + str(gridsize_x) + '*col_nr, ' +  str(miny) + ' + ' + str(gridsize_y) + '*row_nr, ' + str(scalar_column) + ' from sdb_pointstore where instance_id = :ID '
        logger.info(stmt)
    DbCursor.arraysize = 100000
    DbCursor.arraysize = 100000
    DbCursor.execute(stmt, ID = PARAMETER_LIST_VALUE[OBJECT_INSTANCE_ID] )
    while 1 :
        resultset = DbCursor.fetchmany()
        if not resultset :
            break
        else :
            for row in resultset :
                if i % step == 0 :
                    x_v = float(row[0])
                    y_v = float(row[1])
                    z_v = float(row[2])
                    if i == 0 :
                        x_min = x_v
                        x_max = x_v
                        y_min = y_v
                        y_max = y_v
                        z_min = z_v
                        z_max = z_v
                        x.append(x_v)
                        y.append(y_v)
                        z.append(z_v)
                        j = j + 1
                    else :
                        if x_v < x_min :
                            x_min = x_v
                        if x_v > x_max :
                            x_max = x_v
                        if y_v < y_min :
                            y_min = y_v
                        if y_v > y_max :
                            y_max = y_v
                        if z_v < z_min :
                            z_min = z_v
                        if z_v > z_max :
                            z_max = z_v
                        x.append(x_v)
                        y.append(y_v)
                        z.append(z_v)
                        j = j + 1
                i = i + 1

    logger.info( str(j) + " points read from database" )

    # Plot points
    if PLOT_GEOMETRY :
        pylab.scatter(x,y,c=z,edgecolors='none',vmin=z_min,vmax=z_max)
        pylab.colorbar()

    message = "Do you want to export the IM?"
    title   = "Export IM"

    if boolbox(message, title, ["Yes", "No"]) :

        ##############################################
        # Write shapefile
        ##############################################

        logger.info( "Write geometry to shape file" )

        # Get driver
        driver     = ogr.GetDriverByName('ESRI Shapefile')

        # Create shapfile
        shape_file = str(im_name) + str(".shp")
        if os.path.exists(shape_file) :
            driver.DeleteDataSource(shape_file)
        shapeData      = driver.CreateDataSource(shape_file)

        # Create layer and feature definition
        layer          = shapeData.CreateLayer("Individual model", source_srs, ogr.wkbPolygon)
        fieldDefn      = ogr.FieldDefn('id', ogr.OFTInteger)
        layer.CreateField(fieldDefn)
        featureDefn    = layer.GetLayerDefn()

        # Create feature
        shape_feature = ogr.Feature(featureDefn)
        shape_feature.SetGeometry(ogr_geom_out)
        shape_feature.SetField('id', PARAMETER_LIST_VALUE[OBJECT_INSTANCE_ID] )

        # Write feature to file
        layer.CreateFeature(shape_feature)

        # Clean up
        shape_feature.Destroy()
        ogr_geom_out.Destroy()
        shapeData.Destroy()

        logger.info( "Creating shapefile completed" )

        ###################################
        # Coordinate transformation
        ###################################

        logger.info( "Coordinate transformation to UTM" )

        file_utm = str(im_name) + str("_utm.xyz")

        # Determine UTM zone
        utm_zone = int ((((x_max + x_min)/2.0) + 180.0 ) / 6.0 )
        if int( (y_max + y_min)/2.0 ) >= int(0) :
            hemisphere         = "N"
            epsg_hemisphere_id = 6
        else :
            hemisphere         = "S"
            epsg_hemisphere_id = 7
        epsg_code_out = str(EPSG_UTM_WGS84) + str(epsg_hemisphere_id) + str(utm_zone)
        logger.info("UTM zone  = " + str(utm_zone) + str(hemisphere))
        logger.info("EPSG code = " + str(epsg_code_out))

        # Execute coordinate transformation
        target_srs       = osr.SpatialReference()
        target_srs.ImportFromEPSG(int(epsg_code_out))
        coordinate_trans = osr.CoordinateTransformation(source_srs,target_srs)

        # Get points from array and tranform coordinates
        fileUtm = open( file_utm, 'w')
        for index in range(len(x)):
            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint_2D( float(x[index]), float(y[index]) )
            point.Transform(coordinate_trans)
            line_out = str(point.GetX()) + " " + str(point.GetY()) + " " + str(z[index]) + "\n"
            fileUtm.write(line_out)
        fileUtm.close()

        logger.info( "Coordinate transformation to UTM completed" )

        ################################################
        # Write XML file
        ################################################

        logger.info( "Write XML file" )

        xml_file = str(im_name) + str(".xml")
        attribute_list = {}
        attribute_list [ SHALLOWEST_POINT ] = str(shallowest)
        attribute_list [ DEEPEST_POINT    ] = str(deepest)
        xml_text = build_xml( PARAMETER_LIST_VALUE[OBJECT_INSTANCE_ID], attribute_list )
        write_xml_file ( xml_file, xml_text )

        logger.info( "Write XML file completed" )

        ###################################
        # Build memory array
        ###################################

        logger.info( "Build memory array" )

        # Correct for too many rows or columns
        gridsize        = PARAMETER_LIST_VALUE[ GRIDSIZE ]
        limit_rows_cols = 500
        if ( y_max - y_min ) > ( x_max - x_min ) :
            max_rows_cols = int( ( y_max - y_min ) / gridsize )
            if max_rows_cols > limit_rows_cols  :
                gridsize = ( y_max - y_min ) / float( limit_rows_cols )
        else :
            max_rows_cols = int( ( x_max - x_min ) / gridsize )
            if max_rows_cols > limit_rows_cols :
                gridsize = ( x_max - x_min ) / float( limit_rows_cols )

        logger.info( "Using gridsize "  + str(gridsize) )

        # Start building array
        NrRows        = int ( round ( ( y_max - y_min ) / gridsize , 0 ) ) + 1
        NrCols        = int ( round ( ( x_max - x_min ) / gridsize , 0 ) ) + 1
        gridsize      = float(gridsize)
        nodata_value  = int(-32767)
        sum_depths    = numpy.zeros((NrRows, NrCols), numpy.float32)
        sum_depths    = sum_depths + nodata_value
        count_depths  = numpy.zeros((NrRows, NrCols), numpy.int8)
        count_depths  = count_depths + 1

        logger.info( "Nr of rows in grid: " + str(NrRows) )
        logger.info( "Nr of cols in grid: " + str(NrCols) )

        logger.info("Start writing points to array")

        # Loop through coordinates
        for index in range(len(x)):

            # Get row and column in array
            latitude_row  = int ( round ( ( float(y[index]) - y_min  ) / gridsize , 0 ) )
            longitude_col = int ( round ( ( float(x[index]) - x_min  ) / gridsize , 0 ) )

            # Start counting rows from top
            latitude_row = NrRows - latitude_row - 1

            # Write values to array
            if int ( sum_depths [latitude_row , longitude_col ] ) == int ( nodata_value ) :
                sum_depths [latitude_row , longitude_col ]   = float(z[index])
                count_depths [latitude_row , longitude_col ] = int(1)
            else :
                sum_depths [latitude_row , longitude_col ]    = float( sum_depths [latitude_row , longitude_col ] ) + float(z[index])
                count_depths [latitude_row , longitude_col ]  = int ( count_depths [latitude_row , longitude_col ] ) + int(1)

        logger.info("Finish writing points to array")

        # Build raster array
        raster =  sum_depths / count_depths

        logger.info( "Building memory array completed" )

        ###################################
        # Esri ascii grid
        ###################################

        logger.info( "Generate Esri Ascii grid" )

        file_format = "AAIGrid"
        mem_format  = "MEM"

        # Write data array to memory
        file_out    = str(im_name) + str(".asc")
        driver      = gdal.GetDriverByName( mem_format )
        logger.info ( get_gdal_create_option ( driver ) )
        dst_ds      = driver.Create( file_out, NrCols, NrRows, 1, gdalconst.GDT_Float32)
        dst_ds.SetGeoTransform( [ x_min, gridsize, 0.0, y_max, 0.0, -gridsize ] )
        dst_ds.SetProjection( source_srs.ExportToWkt() )
        dst_ds.GetRasterBand(1).SetNoDataValue( nodata_value )
        dst_ds.GetRasterBand(1).WriteArray( raster )

        # Write memory array to grid
        driver     = gdal.GetDriverByName(file_format)
        dst_ds_new = driver.CreateCopy(file_out, dst_ds)
        dst_ds     = None
        dst_ds_new = None

        logger.info( "Generate Esri Ascii grid completed" )

        ###################################
        # Binary Geotif
        ###################################

        logger.info( "Generate binary geotif" )

        file_format    = "GTiff"
        file_out       = str(im_name) + ".tif"
        create_options = [ 'TFW=YES' ]

        # Write memory array to grid
        driver     = gdal.GetDriverByName( file_format )
        logger.info ( get_gdal_create_option ( driver ) )
        outDataset = driver.Create(file_out, NrCols, NrRows, 1, gdalconst.GDT_Float32, create_options )
        outDataset.SetGeoTransform( [ x_min, gridsize ,0.0, y_max, 0.0, -gridsize ] )
        outDataset.SetProjection( source_srs.ExportToWkt() )
        outBand = outDataset.GetRasterBand(1) # 1-based index
        outBand.WriteArray(raster, 0, 0)
        outBand.FlushCache()
        outDataset = None

        logger.info( "Generate binary geotif completed" )

        ###################################
        # RGBA Geotif
        ###################################

        logger.info( "Generate RGBA geotif" )

        file_format = "GTiff"
        file_out    = str(im_name) + "_RGBA.tif"

        # Define memory array to grid
        driver     = gdal.GetDriverByName( file_format )
        outDataset = driver.Create(file_out, NrCols, NrRows, 3, gdalconst.GDT_Byte)
        outDataset.SetGeoTransform( [ x_min, gridsize ,0.0, y_max, 0.0, -gridsize ] )
        outDataset.SetProjection( source_srs.ExportToWkt() )

        # Set RGBA value for raster bands
        band1 = numpy.zeros((NrRows, NrCols), numpy.int8)
        band2 = numpy.zeros((NrRows, NrCols), numpy.int8)
        band3 = numpy.zeros((NrRows, NrCols), numpy.int8)
        i = 0
        for row in range(NrRows):
            for col in range(NrCols):
                z_value = raster[ row, col ]
                #kwargs = {"mag": z_value, "cmin": z_min , "cmax": z_max}
                #red, green, blue = range_to_rgb( **kwargs )
                red, green, blue = range_to_rgb( mag=z_value, cmin=z_min, cmax=z_max )
                band1[ row, col ] = red
                band2[ row, col ] = green
                band3[ row, col ] = blue
                gdal.TermProgress_nocb( (float(i+1) / NrRows) )

        # Get and write each band out
        outBand1 = outDataset.GetRasterBand(1)
        outBand2 = outDataset.GetRasterBand(2)
        outBand3 = outDataset.GetRasterBand(3)
        outBand1.WriteArray(band1, 0, 0)
        outBand2.WriteArray(band2, 0, 0)
        outBand3.WriteArray(band3, 0, 0)
        outBand1.FlushCache()
        outBand2.FlushCache()
        outBand3.FlushCache()
        outDataset = None

        logger.info( "Generate RGBA geotif completed" )

    ###################################
    # Plot image
    ###################################    

    if PLOT_GEOMETRY :

        logger.info( "Plot image" )

#        if SHOW_IMAGE :
#            cmap = pylab.cm.get_cmap('jet', 512)
#            cmap.set_bad('w',nodata_value)
#            imgplot = pylab.imshow(raster, cmap=cmap, extent=[1,NrCols,1,NrRows], interpolation='nearest', aspect='auto')
#            pylab.colorbar()

        logger.info( "Add annotation" )
        
        pylab.axis('equal')
        pylab.xlabel("Longitud")
        pylab.ylabel("Latitud")
        pylab.grid(True)
        pylab.title("Individual model " + str(im_name) )
        pylab.show()
        

    # Finally close database connection
    DbConnection.close()

    logger.info( "Plot individual model points completed" )

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

    # Start gui
    gui_start ()
    
