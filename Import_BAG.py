#! /usr/bin/python

""" Template function """

# Soure of example: http://sebsauvage.net/python/gui

# standard library imports
import os
try:
    import h5py
except ImportError:
    raise ImportError,"The h5py module is required to run this program."
try:
    import xml.dom.minidom
except ImportError:
    raise ImportError,"The xml.dom.minidom module is required to run this program."

__author__="Terlien"
__date__ ="$9-okt-2009 11:50:05$"
__copyright__ = "Copyright 2009, ATLIS"

INPUT_FILE  = 'D:/Geodata/Netherlands/Bathymetry/BAG/100223_DR_BATH_MB_300_extract.bag'
#INPUT_FILE  = 'D:/Geodata/USA/Bathymetry/BAG/H11699_10m_MLLW_5of7.bag'
#INPUT_FILE  = 'D:/Geodata/USA/Bathymetry/BAG/H11639_MB_50cm_MLLW_1of1.bag'

if __name__ == "__main__":

    bag = h5py.File(INPUT_FILE)
    bag.values()
    bag.items()

    # Return root as dictionary object
    root = bag['/BAG_root']
    print "========================="
    print "root.keys (HDF5 datasets)"
    print "========================="      
    print root.keys()
    print "========================="
    print "root.values"
    print "========================="
    print root.values()
    print "========================="
    print "root.items"
    print "========================="
    print root.items()
    print "========================="

    metadata_xml = xml.dom.minidom.parseString(str(''.join(bag['/BAG_root/metadata'])))
    #print metadata_xml.toprettyxml()
    print 'westBoundLongitude: ' + str( metadata_xml.getElementsByTagName('westBoundLongitude')[0].childNodes[0].nodeValue )
    print 'eastBoundLongitude: ' + str( metadata_xml.getElementsByTagName('eastBoundLongitude')[0].childNodes[0].nodeValue )
    print 'southBoundLatitude: ' + str( metadata_xml.getElementsByTagName('southBoundLatitude')[0].childNodes[0].nodeValue )
    print 'northBoundLatitude: ' + str( metadata_xml.getElementsByTagName('northBoundLatitude')[0].childNodes[0].nodeValue )

    print metadata_xml.getElementsByTagName('smXML:MD_Dimension')[0].getElementsByTagName('dimensionName')[0].childNodes[0].nodeValue
    print 'rows: '   + str( metadata_xml.getElementsByTagName('smXML:MD_Dimension')[0].getElementsByTagName('dimensionSize')[0].childNodes[0].nodeValue )
    unit_y = float( metadata_xml.getElementsByTagName('smXML:MD_Dimension')[0].getElementsByTagName('resolution')[0].getElementsByTagName('smXML:Measure')[0].getElementsByTagName('smXML:value')[0].childNodes[0].nodeValue )
    print '--unit: ' + str( unit_y )
    print metadata_xml.getElementsByTagName('smXML:MD_Dimension')[1].getElementsByTagName('dimensionName')[0].childNodes[0].nodeValue
    print 'cols: '   + str( metadata_xml.getElementsByTagName('smXML:MD_Dimension')[1].getElementsByTagName('dimensionSize')[0].childNodes[0].nodeValue )
    unit_x = float( metadata_xml.getElementsByTagName('smXML:MD_Dimension')[1].getElementsByTagName('resolution')[0].getElementsByTagName('smXML:Measure')[0].getElementsByTagName('smXML:value')[0].childNodes[0].nodeValue )
    print '--unit: ' + str( unit_x )

    coordinates = str( metadata_xml.getElementsByTagName('gml:coordinates')[0].childNodes[0].nodeValue )
    print 'gml:coordinates: ' + str( coordinates )
    ll_x = float(coordinates.rstrip().split()[0].rstrip().split(',')[0])
    ll_y = float(coordinates.rstrip().split()[0].rstrip().split(',')[1])
    print ll_x
    print ll_y

    # Write metadata
    output_file = os.path.dirname( INPUT_FILE ) + "/" + os.path.basename( INPUT_FILE ).split(".")[0] + str(".txt")
    projection       = str( metadata_xml.getElementsByTagName('projection')[0].getElementsByTagName('smXML:RS_Identifier')[0].getElementsByTagName('code')[0].childNodes[0].nodeValue ) 
    zone             = str( metadata_xml.getElementsByTagName('smXML:MD_ProjectionParameters')[0].getElementsByTagName('zone')[0].childNodes[0].nodeValue ) 
    ellipsoid        = str( metadata_xml.getElementsByTagName('ellipsoid')[0].getElementsByTagName('smXML:RS_Identifier')[0].getElementsByTagName('code')[0].childNodes[0].nodeValue ) 
    horizontal_datum = str( metadata_xml.getElementsByTagName('datum')[0].getElementsByTagName('smXML:RS_Identifier')[0].getElementsByTagName('code')[0].childNodes[0].nodeValue )         
    vertical_datum   = str( metadata_xml.getElementsByTagName('datum')[1].getElementsByTagName('smXML:RS_Identifier')[0].getElementsByTagName('code')[0].childNodes[0].nodeValue )         
    
    print output_file
    fOut   = open( output_file, 'w')
    fOut.write( 'projection       : ' + projection + "\n" )
    fOut.write( 'zone             : ' + zone + "\n" )
    fOut.write( 'ellipsoid        : ' + ellipsoid + "\n" )
    fOut.write( 'horizontal datum : ' + horizontal_datum + "\n" )
    fOut.write( 'vertical  datum  : ' + vertical_datum + "\n" )
    fOut.close()
    
    print 'projection: '       + projection 
    print 'zone: '             + zone
    print 'ellipsoid: '        + ellipsoid
    print 'horizontal datum: ' + horizontal_datum 
    print 'vertical datum: '   + vertical_datum

    elevation   = bag['/BAG_root/elevation'].value
    print 'Grid dimensions elevation   : ' + str(elevation.shape)

    # Grid starts at 0,0
    # Ignore z values larger than 0
    output_file = os.path.dirname( INPUT_FILE ) + "/" + os.path.basename( INPUT_FILE ).split(".")[0] + str(".xyz")
    print output_file
    fOut   = open( output_file, 'w')
    i = 0
    for col in range(elevation.shape[0]):
        for row in range(elevation.shape[1]):
            z = float( elevation [ col, row ] )
            if z <= 100 : 
                x = ll_x + float(col) * unit_x
                y = ll_y + float(row) * unit_y
                i = i + 1
                output_line = str(x) + ' ' + str(y) + ' ' + str(z) + "\n"
                fOut.write( output_line )
    fOut.close()
    print 'nr of points: ' + str(i)
    



    
