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
#	field 1: Set Name
#	field 2: Set Type (ACC_MGIType.name)
#	field 3: Set Member
#	field 4: Created By
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
    db.set_sqlPassword(passwordFileName)
 
    fdate = mgi_utils.date('%m%d%Y')	# current date
    diagFileName = sys.argv[0] + '.' + fdate + '.diagnostics'
    errorFileName = sys.argv[0] + '.' + fdate + '.error'

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

    # Set Log File Descriptor
    db.set_sqlLogFD(diagFile)

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

    results = db.sql('select maxKey = max(_Set_key) + 1 from MGI_Set', 'auto')
    setKey = results[0]['maxKey']

    results = db.sql('select maxKey = max(_SetMember_key) + 1 from MGI_SetMember', 'auto')
    setMemberKey = results[0]['maxKey']

# Purpose:  BCPs the data into the database
# Returns:  nothing
# Assumes:  nothing
# Effects:  BCPs the data into the database
# Throws:   nothing

def bcpFiles():

    if DEBUG or not bcpon:
        return

    outSetFile.close()
    outMemberFile.close()

    bcpI = 'cat %s | bcp %s..' % (passwordFileName, db.get_sqlDatabase())
    bcpII = '-c -t\"%s' % (bcpdelim) + '" -S%s -U%s' % (db.get_sqlServer(), db.get_sqlUser())
    truncateDB = 'dump transaction %s with truncate_only' % (db.get_sqlDatabase())

    bcp1 = '%s%s in %s %s' % (bcpI, setTable, outSetFileName, bcpII)
    bcp2 = '%s%s in %s %s' % (bcpI, memberTable, outMemberFileName, bcpII)

    for bcpCmd in [bcp1, bcp2]:
	diagFile.write('%s\n' % bcpCmd)
	os.system(bcpCmd)
	db.sql(truncateDB, None)

    # update statistics
    db.sql('update statistics %s' % (setTable), None)
    db.sql('update statistics %s' % (memberTable), None)

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
	    setName = tokens[0]
	    setType = tokens[1]
	    setMember = tokens[2]
	    createdBy = tokens[3]
	except:
	    exit(1, 'Invalid Line (%d): %s\n' % (lineNum, line))

        userKey = loadlib.verifyUser(createdBy, lineNum, errorFile)
	mgiTypeKey = loadlib.verifyMGIType(setType, lineNum, errorFile)
	objectKey = loadlib.verifyObject("", mgiTypeKey, setMember, lineNum, errorFile)

	if userKey == 0 or mgiTypeKey == 0 or objectKey == 0:
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
	         str(userKey) + TAB + str(userKey) + TAB + \
	         loaddate + TAB + loaddate + CRT)

	    setKey = setKey + 1
	    sequenceNum = 1
	    sequenceSetNum = sequenceSetNum + 1

	outMemberFile.write(str(setMemberKey) + TAB + \
	    str(useSetKey) + TAB + \
	    str(objectKey) + TAB + \
	    str(sequenceNum) + TAB + \
	    str(userKey) + TAB + str(userKey) + TAB + \
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

