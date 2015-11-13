#! /usr/bin/python

""" Template function """

# standard library imports
import cx_Oracle
import os
from osgeo import ogr
from osgeo import osr

NAME = "Name"

__author__="Terlien"
__date__ ="$9-okt-2009 11:50:05$"
__copyright__ = "Copyright 2009, ATLIS"

if __name__ == "__main__":

    # Init structes to store label and polygons
    labels_dict = {}
    polygons_list = []
    
    # Set target
    driver = ogr.GetDriverByName('ESRI Shapefile')
    target_file = 'bladwijzer50d.shp'
    if os.path.exists(target_file) :
        driver.DeleteDataSource(str(target_file))    
    target = driver.CreateDataSource(target_file)
    target_srs = osr.SpatialReference()
    target_srs.ImportFromEPSG(int(28992))

    # Define polygon layer
    polygon_layer = target.CreateLayer("PolygonLayer", target_srs, ogr.wkbPolygon)    
    fieldDefn = ogr.FieldDefn(NAME, ogr.OFTString)   
    polygon_layer.CreateField(fieldDefn)
    featureDefn_polygon_layer = polygon_layer.GetLayerDefn()    
    
    # Define line layer
    line_layer = target.CreateLayer("Nederland", target_srs, ogr.wkbLineString)    
    fieldDefn = ogr.FieldDefn("ID", ogr.OFTInteger)
    line_layer.CreateField(fieldDefn)
    featureDefn_line_layer = line_layer.GetLayerDefn()     
    
    # Open source and write to target
    source = ogr.Open("T:/ggm/Ontwikkeling/Richard/bladwijzer50d.dgn") 
    layer = source.GetLayer(0)
    i = 0
    feature = layer.GetNextFeature()
    while feature :
        i = i + 1          
        geom = feature.GetGeometryRef()
        if int(geom.GetGeometryType()) == 1 :
            if feature.GetFieldCount() > 0 :
                label = feature.GetFieldAsString(feature.GetFieldIndex('Text'))
                labels_dict[ label ] = geom.ExportToWkt()
        if int(geom.GetGeometryType()) == 2 :
            if feature.GetFieldCount() > 0 :
                print feature.GetFieldAsString(feature.GetFieldIndex('Text'))            
                shape_feature_line = ogr.Feature(featureDefn_line_layer)
                shape_feature_line.SetGeometry(geom)
                shape_feature_line.SetFID(i)
                shape_feature_line.SetField("ID", i)
                line_layer.CreateFeature(shape_feature_line)              
        if int(geom.GetGeometryType()) == 3 :
            if feature.GetFieldCount() > 0 :    
                polygons_list.append(geom.ExportToWkt())
        feature = layer.GetNextFeature() 

    
    # Now link labels to polygons and store polygons in shape file
    i = 0
    for geometry in polygons_list :
        polygon = ogr.CreateGeometryFromWkt(geometry)        
        for label in labels_dict : 
            point = ogr.CreateGeometryFromWkt(labels_dict[label])
            if polygon.Contains ( point ) :
                i = i + 1
                shape_feature_polygon = ogr.Feature(featureDefn_polygon_layer)
                shape_feature_polygon.SetGeometry(polygon)
                shape_feature_polygon.SetFID(i)
                shape_feature_polygon.SetField(NAME, str(label))
                polygon_layer.CreateFeature(shape_feature_polygon)   
        
    # Close source and target    
    target.Destroy()
    source.Destroy()
