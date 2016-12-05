#!/usr/local/bin/python

#
# Program: setload.py
#
# Original Author: Lori Corbani
#
# Purpose:
#
#	To load new Set and Set Members into Set Structures:
#
#	MGI_Set
#	MGI_SetMember
#
# Requirements Satisfied by This Program:
#
# Envvars:
#
# Inputs:
#
#	Tab-delimited file with the following fields:
#	
#	field 1: Set Member
#	field 2: Set Label
#
# Outputs:
#
#       BCP files:
#
#	MGI_Set.bcp		Set records
#	MGI_SetMember.bcp	Set Member records
#
#       Diagnostics file of all input parameters and SQL commands
#       Error file
#
# Exit Codes:
#
# Assumes:
#
#	That no one else is adding Set records to the database.
#
# Bugs:
#
# Implementation:
#

import sys
import os
import string
import db
import mgi_utils
import loadlib

#globals

db.setTrace(True)
db.setAutoTranslate(False)
db.setAutoTranslateBE(False)

#
# from configuration file
#
user = os.environ['MGD_DBUSER']
passwordFileName = os.environ['MGD_DBPASSWORDFILE']
mode = os.environ['SETMODE']
inputFileName = os.environ['SETINPUTFILE']
setName = os.environ['SETNAME']
setType = os.environ['SETTYPE']
createdBy = os.environ['CREATEDBY']

DEBUG = 0		# if 0, not in debug mode
TAB = '\t'		# tab
CRT = '\n'		# carriage return/newline
bcpdelim = TAB		# bcp file delimiter

bcpon = 1		# can the bcp files be bcp-ed into the database?  default is yes.

diagFile = ''		# diagnostic file descriptor
errorFile = ''		# error file descriptor

# output files

outSetFile = ''		# file descriptor
outMemberFile = ''	# file descriptor
inputFile = ''		# file descriptor

setTable = 'MGI_Set'
memberTable = 'MGI_SetMember'
outputDir = os.environ['SETOUTPUTDIR']
outSetFileName = '%s.bcp' % setTable
outMemberFileName = '%s.bcp' % memberTable

diagFileName = ''	# diagnostic file name
errorFileName = ''	# error file name

# primary keys

setKey = 0		# MGI_Set._Set_key
setMemberKey = 0	# MGI_SetMember._SetMember_key
setLookup = {}

loaddate = loadlib.loaddate

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
 
    try:
        diagFile.write('\n\nEnd Date/Time: %s\n' % (mgi_utils.date()))
        errorFile.write('\n\nEnd Date/Time: %s\n' % (mgi_utils.date()))
        diagFile.close()
        errorFile.close()
    except:
        pass

    db.useOneConnection(0)
    sys.exit(status)
 
# Purpose: process command line options
# Returns: nothing
# Assumes: nothing
# Effects: initializes global variables
#          calls showUsage() if usage error
#          exits if files cannot be opened
# Throws: nothing

def init():
    global diagFile, errorFile, inputFile, errorFileName, diagFileName
    global outSetFile, outMemberFile
    global setKey, setMemberKey, createdByKey, mgiTypeKey, useSetKey
    global DEBUG
 
    db.useOneConnection(1)
    db.set_sqlUser(user)
    db.set_sqlPasswordFromFile(passwordFileName)
 
    diagFileName = '%s/setload.diagnostics' % (outputDir)
    errorFileName = '%s/setload.error' % (outputDir)

    try:
        diagFile = open(diagFileName, 'w')
    except:
        exit(1, 'Could not open file %s\n' % diagFileName)
		
    try:
        errorFile = open(errorFileName, 'w')
    except:
        exit(1, 'Could not open file %s\n' % errorFileName)
		
    try:
        inputFile = open(inputFileName, 'r')
    except:
        exit(1, 'Could not open file %s\n' % inputFileName)
		
    # Output Files

    try:
	fullPathSetFile = '%s/%s' % (outputDir, outSetFileName)
        outSetFile = open(fullPathSetFile, 'w')
    except:
        exit(1, 'Could not open file %s\n' % fullPathSetFile)

    try:
	fullPathMemberFile  = '%s/%s' % (outputDir, outMemberFileName)
        outMemberFile = open(fullPathMemberFile, 'w')
    except:
        exit(1, 'Could not open file %s\n' % fullPathMemberFile)

    # Log all SQL
    db.set_sqlLogFunction(db.sqlLogAll)

    diagFile.write('Start Date/Time: %s\n' % (mgi_utils.date()))
    diagFile.write('Server: %s\n' % (db.get_sqlServer()))
    diagFile.write('Database: %s\n' % (db.get_sqlDatabase()))
    errorFile.write('Start Date/Time: %s\n\n' % (mgi_utils.date()))

    if mode == 'preview':
        DEBUG = 1
        bcpon = 0
    elif mode != 'load':
        exit(1, 'Invalid Processing Mode:  %s\n' % (mode))

    results = db.sql('select max(_Set_key) + 1 as maxKey from MGI_Set', 'auto')
    setKey = results[0]['maxKey']

    createdByKey = loadlib.verifyUser(createdBy, 0, errorFile)
    mgiTypeKey = loadlib.verifyMGIType(setType, 0, errorFile)

    #
    # use existing MGI_Set, or create a new one
    #
    results = db.sql('select _Set_key from MGI_Set where _MGIType_key = %s and name = \'%s\'' 
	% (mgiTypeKey, setName), 'auto')

    if len(results) > 0:
        for r in results:
            setKey = r['_Set_key']
	# delete/reload
	db.sql('delete from MGI_SetMember where _Set_key = %s' % (setKey), None)
    else:
        outSetFile.write(str(setKey) + TAB + \
	   str(mgiTypeKey) + TAB + \
	   str(setName) + TAB + \
	   '1' + TAB + \
	   str(createdByKey) + TAB + str(createdByKey) + TAB + \
	   loaddate + TAB + loaddate + CRT)

    results = db.sql('select max(_SetMember_key) + 1 as maxKey from MGI_SetMember', 'auto')
    setMemberKey = results[0]['maxKey']

    return

# Purpose:  BCPs the data into the database
# Returns:  nothing
# Assumes:  nothing
# Effects:  BCPs the data into the database
# Throws:   nothing

def bcpFiles():

    outSetFile.close()
    outMemberFile.close()

    db.commit()

    if DEBUG or not bcpon:
        return

    bcpCommand = os.environ['PG_DBUTILS'] + '/bin/bcpin.csh'

    bcp1 = '%s %s %s %s %s %s "\\t" "\\n" mgd' % \
        (bcpCommand, db.get_sqlServer(), db.get_sqlDatabase(), setTable, outputDir, outSetFileName)

    bcp2 = '%s %s %s %s %s %s "\\t" "\\n" mgd' % \
        (bcpCommand, db.get_sqlServer(), db.get_sqlDatabase(), memberTable, outputDir, outMemberFileName)

    for bcpCmd in [bcp1, bcp2]:
	diagFile.write('%s\n' % bcpCmd)
	os.system(bcpCmd)

    return

# Purpose:  processes input file
# Returns:  nothing
# Assumes:  nothing
# Effects:  reads in the input file and creates the output files
# Throws:   nothing

def process():

    global setKey, setMemberKey, setKey

    lineNum = 0
    sequenceNum = 1

    for line in inputFile.readlines():

	lineNum = lineNum + 1

	tokens = string.split(line[:-1], TAB)

        try:
	    setMember = tokens[0]
	    setLabel = tokens[1]
	except:
	    exit(1, 'Invalid Line (%d): %s\n' % (lineNum, line))

	objectKey = loadlib.verifyObject(setMember, mgiTypeKey, "", lineNum, errorFile)

	if objectKey == 0:
	    continue

	outMemberFile.write(str(setMemberKey) + TAB + \
	    str(setKey) + TAB + \
	    str(objectKey) + TAB + \
	    str(setLabel) + TAB + \
	    str(sequenceNum) + TAB + \
	    str(createdByKey) + TAB + str(createdByKey) + TAB + \
	    loaddate + TAB + loaddate + CRT)

        setMemberKey = setMemberKey + 1
	sequenceNum = sequenceNum + 1

    return

#
# Main
#

init()
process()
bcpFiles()
exit(0)

