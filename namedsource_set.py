#!/usr/local/bin/python

# $Header$
# $Name$

#
# Program: namedsource_set.py
#
# Original Author: Lori Corbani
#
# Purpose:
#
#	To translate namedsource_set.py input files into input files
#	for the setload.py program.
#
# Requirements Satisfied by This Program:
#
# Usage:
#
#	namedsource_set.py
#
# Envvars:
#
# Inputs:
#
#       namedsource_set.txt.good, a tab-delimited file in the format:
#               field 1: Library Name
#		field 2: comma-separated list of Clone Sets to which the library belongs
#
# Outputs:
#
#       1 tab-delimited file:
#
#	cloneset.txt
#	
#       Error file
#
# Exit Codes:
#
# Assumes:
#
# Bugs:
#
# Implementation:
#

import sys
import os
import string

#globals

TAB = '\t'		# tab
CRT = '\n'		# carriage return/newline
NULL = ''

inSourceFile = ''	# file descriptor
setFile = ''		# file descriptor

inSourceFileName = 'namedsource_set.txt.good'
setFileName = 'cloneset.txt'
createdBy = os.environ['CREATEDBY']
mgiType = 'Source'

# Purpose: prints error message and exits
# Returns: nothing
# Assumes: nothing
# Effects: exits with exit status
# Throws: nothing

def exit(
    status,          # numeric exit status (integer)
    message = None   # exit message (string)
    ):

    if message is not None:
        sys.stderr.write('\n' + str(message) + '\n')
 
    sys.exit(status)
 
# Purpose: initialize
# Returns: nothing
# Assumes: nothing
# Effects: initializes global variables
#          exits if files cannot be opened
# Throws: nothing

def init():
    global inSourceFile
    global setFile
 
    try:
        inSourceFile = open(inSourceFileName, 'r')
    except:
        exit(1, 'Could not open file %s\n' % inSourceFileName)

    try:
        setFile = open(setFileName, 'w')
    except:
        exit(1, 'Could not open file %s\n' % setFileName)

    return

# Purpose:  processes data
# Returns:  nothing
# Assumes:  nothing
# Effects:  writes data to output files
# Throws:   nothing

def process():

    # For each line in the input file

    lineNum = 0
    for line in inSourceFile.readlines():

	lineNum = lineNum + 1

        # Split the line into tokens
        tokens = string.split(line[:-1], TAB)

        try:
	    library = tokens[0]
	    cloneSets = tokens[1]

        except:
            print 'Invalid Line (%d): %s\n' % (lineNum, line)

	if cloneSets == 'none':
	    continue

	for c in string.split(cloneSets, ', '):

	    setFile.write(c + TAB + \
	    mgiType + TAB + \
	    library + TAB + \
	    createdBy + CRT)

    # end of "for line in inSourceFile.readlines():"

#
# Main
#

init()
process()
exit(0)

# $Log$
#
