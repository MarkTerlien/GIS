# standard library imports
import math


__author__="terlien"
__date__ ="$26-apr-2011 12:10:08$"

if __name__ == "__main__":
    EARTH_PERIMETER = 40068000
    y               = 55.0
    cell_size       = 266
    earth_perimeter = EARTH_PERIMETER * math.cos(math.radians(y))
    cell_size_new = ( float(cell_size) /earth_perimeter ) * 360
    print "Latitude     : " + str(y)
    print "Cell size(m) : " + str(cell_size)
    print "Cell size(d) : " + str(cell_size_new)
    l_gap_radius   = ( float(cell_size) / 2.0 )
    l_min_gap_area = ( ( l_gap_radius )  ** 2.0 ) * math.pi
    #print "Gap area     : " + str(l_min_gap_area)
    y                = 89.0
    cell_size_degree = 0.0041667
    cell_size_meter  = ( cell_size_degree / 360.0 ) * ( EARTH_PERIMETER * math.cos(math.radians(y)) )
    print "Latitude     : " + str(y)
    print "Cell size(d) : " + str(cell_size_degree)
    print "Cell size(m) : " + str(cell_size_meter)
    line = "23;-24;-45.8;;"
    c = line.rstrip().split(";")
    print "x " + str(float(c[0]))
    print "y " + str(float(c[1]))
    print "z " + str(float(c[2]))
    x = str(c[3])
    print "xmin " + str(x)
    #text = str(p)
    info = {"PHP":"17th May",
           "Perl":"15th June",
           "Java":"7th June",
           "Python":"26th May",
           "Tcl":"12th July",
           "MySQL":"24th May"}

    topics = info.keys()
    topics.sort()

    for topic in topics:
       print "Next",topic,"course starts",info[topic]


