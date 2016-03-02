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
#	field 3: Set Name
#	field 4: Set Type (ACC_MGIType.name)
#	field 5: Created By
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

outSetFileName = setTable + '.bcp'
outMemberFileName = memberTable + '.bcp'

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
 
    db.useOneConnection(1)
    db.set_sqlUser(user)
    db.set_sqlPasswordFromFile(passwordFileName)
 
    diagFileName = 'setload.diagnostics'
    errorFileName = 'setload.error'

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
        outSetFile = open(outSetFileName, 'w')
    except:
        exit(1, 'Could not open file %s\n' % outSetFileName)

    try:
        outMemberFile = open(outMemberFileName, 'w')
    except:
        exit(1, 'Could not open file %s\n' % outMemberFileName)

    # Log all SQL
    db.set_sqlLogFunction(db.sqlLogAll)

    diagFile.write('Start Date/Time: %s\n' % (mgi_utils.date()))
    diagFile.write('Server: %s\n' % (db.get_sqlServer()))
    diagFile.write('Database: %s\n' % (db.get_sqlDatabase()))
    errorFile.write('Start Date/Time: %s\n\n' % (mgi_utils.date()))

    return

# Purpose: verify processing mode
# Returns: nothing
# Assumes: nothing
# Effects: if the processing mode is not valid, exits.
#	   else, sets global variables DEBUG and bcpon
# Throws:  nothing

def verifyMode():

    global DEBUG

    if mode == 'preview':
        DEBUG = 1
        bcpon = 0
    elif mode != 'load':
        exit(1, 'Invalid Processing Mode:  %s\n' % (mode))

# Purpose:  sets global primary key variables
# Returns:  nothing
# Assumes:  nothing
# Effects:  sets global primary key variables
# Throws:   nothing

def setPrimaryKeys():

    global setKey, setMemberKey

    results = db.sql('select max(_Set_key) + 1 as maxKey from MGI_Set', 'auto')
    setKey = results[0]['maxKey']

    results = db.sql('select max(_SetMember_key) + 1 as maxKey from MGI_SetMember', 'auto')
    setMemberKey = results[0]['maxKey']

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
    currentDir = os.getcwd()

    bcp1 = '%s %s %s %s %s %s "\\t" "\\n" mgd' % \
        (bcpCommand, db.get_sqlServer(), db.get_sqlDatabase(), setTable, currentDir, outSetFileName)

    bcp2 = '%s %s %s %s %s %s "\\t" "\\n" mgd' % \
        (bcpCommand, db.get_sqlServer(), db.get_sqlDatabase(), memberTable, currentDir, outMemberFileName)

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

    global setKey, setMemberKey

    lineNum = 0
    sequenceNum = 1
    sequenceSetNum = 1

    for line in inputFile.readlines():

	error = 0
	lineNum = lineNum + 1

	tokens = string.split(line[:-1], TAB)

        try:
	    setMember = tokens[0]
	    setLabel = tokens[1]
	    setName = tokens[2]
	    setType = tokens[3]
	    createdBy = tokens[4]
	except:
	    exit(1, 'Invalid Line (%d): %s\n' % (lineNum, line))

        createdByKey = loadlib.verifyUser(createdBy, lineNum, errorFile)
	mgiTypeKey = loadlib.verifyMGIType(setType, lineNum, errorFile)
	objectKey = loadlib.verifyObject(setMember, mgiTypeKey, "", lineNum, errorFile)

	if createdByKey == 0 or mgiTypeKey == 0 or objectKey == 0:
	    error = 1

        if error:
	    continue

	if setLookup.has_key(setName):
	    useSetkey = setLookup[setName]
        else:
	    useSetKey = setKey
	    setLookup[setName] = useSetKey

	    outSetFile.write(str(useSetKey) + TAB + \
	         str(mgiTypeKey) + TAB + \
	         str(setName) + TAB + \
		 str(sequenceSetNum) + TAB + \
	         str(createdByKey) + TAB + str(createdByKey) + TAB + \
	         loaddate + TAB + loaddate + CRT)

	    setKey = setKey + 1
	    sequenceNum = 1
	    sequenceSetNum = sequenceSetNum + 1

	outMemberFile.write(str(setMemberKey) + TAB + \
	    str(useSetKey) + TAB + \
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
verifyMode()
setPrimaryKeys()
process()
bcpFiles()
exit(0)

