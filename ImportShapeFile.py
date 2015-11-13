#! /usr/bin/python

""" Template function """

# standard library imports
import cx_Oracle
from osgeo import ogr

__author__="Terlien"
__date__ ="$9-okt-2009 11:50:05$"
__copyright__ = "Copyright 2009, ATLIS"

if __name__ == "__main__":

    # Init Oracle connection
    DbUser = "sens"
    DbPass = "senso"
    DbConnect = "10.20.0.49/sens11"
    oracle_connection = cx_Oracle.connect(DbUser, DbPass, DbConnect)
    oracle_cursor     = oracle_connection.cursor()
    print "Connected to database"
    epsg_code = oracle_cursor.callfunc("sdb_interface_pck.getepsgcodedb", cx_Oracle.NUMBER)
    print epsg_code
    object_class_id    = 705
    geom_col           = "SYS_GEOM001"

    # MSL - ETRS89
    object_instance_id = 178749
    file               = "D:\Geodata\Separation models\ETRS-MSL.shp"
    fIn                = ogr.Open ( str(file) )
    layer              = fIn.GetLayer(0)
    feature            = layer.GetNextFeature()
    geom               = feature.GetGeometryRef()
    hull_wkt           = str(geom.ExportToWkt())
    print hull_wkt
    l_sdo_wkt          = oracle_cursor.var(cx_Oracle.CLOB)
    l_sdo_wkt.setvalue(0, hull_wkt)
    oracle_cursor.callproc("sdb_interface_pck.setGeom",[object_class_id, object_instance_id, geom_col, l_sdo_wkt, epsg_code, "T" ])

    # NAP - ETRS89
    object_instance_id = 178751
    file               = "D:\Geodata\Separation models\ETRS-NAP.shp"
    fIn                = ogr.Open ( str(file) )
    layer              = fIn.GetLayer(0)
    feature            = layer.GetNextFeature()
    geom               = feature.GetGeometryRef()
    hull_wkt           = str(geom.ExportToWkt())
    print hull_wkt
    l_sdo_wkt          = oracle_cursor.var(cx_Oracle.CLOB)
    l_sdo_wkt.setvalue(0, hull_wkt)
    oracle_cursor.callproc("sdb_interface_pck.setGeom",[object_class_id, object_instance_id, geom_col, l_sdo_wkt, epsg_code, "T" ])

    # Commit and close
    oracle_connection.commit()
    oracle_connection.close()