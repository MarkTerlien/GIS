#! /usr/bin/python

""" Template function """

# standard library imports
import os


__author__="Terlien"
__date__ ="$9-okt-2009 11:50:05$"
__copyright__ = "Copyright 2009, ATLIS"

if __name__ == "__main__":

    print "Start"
    dir      = "W:\\3. SENS BATHY\\20. EMODNET\\SHOM French part of the Channel 100422"
    file_out = "c:\\temp\\Channel.xyz"
    fOut = open ( file_out, 'w' )
    for file_in in os.listdir(dir) :
        print file_in
        fIn = open ( dir + str("\\") + file_in, 'r' )
        for line in fIn :
            fOut.write(line)
        fIn.close()
    fOut.close()
