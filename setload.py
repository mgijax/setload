#!/usr/local/bin/python

# $Header$
# $Name$

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
# Usage:
#	program.py
#	-S = database server
#	-D = database
#	-U = user
#	-P = password file
#	-M = mode
#	-I = input file
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
import getopt
import db
import mgi_utils
import loadlib

#globals

DEBUG = 0		# if 0, not in debug mode
TAB = '\t'		# tab
CRT = '\n'		# carriage return/newline
bcpdelim = TAB		# bcp file delimiter

bcpon = 1		# can the bcp files be bcp-ed into the database?  default is yes.

datadir = os.environ['SETLOADDATADIR']	# file which contains the data files

diagFile = ''		# diagnostic file descriptor
errorFile = ''		# error file descriptor

# output files

outSetFile = ''		# file descriptor
outMemberFile = ''	# file descriptor
inputFile = ''		# file descriptor

setTable = 'MGI_Set'
memberTable = 'MGI_SetMember'

outSetFileName = datadir + '/' + setTable + '.bcp'
outMemberFileName = datadir + '/' + memberTable + '.bcp'

diagFileName = ''	# diagnostic file name
errorFileName = ''	# error file name
passwordFileName = ''	# password file name

mode = ''		# processing mode (load, preview)

# primary keys

setKey = 0		# MGI_Set._Set_key
setMemberKey = 0	# MGI_SetMember._SetMember_key
setLookup = {}

loaddate = loadlib.loaddate

# Purpose: displays correct usage of this program
# Returns: nothing
# Assumes: nothing
# Effects: exits with status of 1
# Throws: nothing
 
def showUsage():
    usage = 'usage: %s -S server\n' % sys.argv[0] + \
        '-D database\n' + \
        '-U user\n' + \
        '-P password file\n' + \
        '-M mode\n' + \
	'-I input file\n'

    exit(1, usage)
 
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
    global diagFile, errorFile, inputFile, errorFileName, diagFileName, passwordFileName
    global mode
    global outSetFile, outMemberFile
 
    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'S:D:U:P:M:I:')
    except:
        showUsage()
 
    #
    # Set server, database, user, passwords depending on options specified
    #
 
    server = ''
    database = ''
    user = ''
    password = ''
    inputFileName = ''
 
    for opt in optlist:
        if opt[0] == '-S':
            server = opt[1]
        elif opt[0] == '-D':
            database = opt[1]
        elif opt[0] == '-U':
            user = opt[1]
        elif opt[0] == '-P':
            passwordFileName = opt[1]
        elif opt[0] == '-M':
            mode = opt[1]
        elif opt[0] == '-I':
            inputFileName = opt[1]
        else:
            showUsage()

    # User must specify Server, Database, User and Password
    password = string.strip(open(passwordFileName, 'r').readline())
    if server == '' or database == '' or user == '' or password == '' \
	or mode == '' or inputFileName == '':
        showUsage()

    # Initialize db.py DBMS parameters
    db.set_sqlLogin(user, password, server, database)
    db.useOneConnection(1)
 
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
    diagFile.write('Server: %s\n' % (server))
    diagFile.write('Database: %s\n' % (database))
    diagFile.write('User: %s\n' % (user))

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
	         str(userKey) + TAB + str(userKey) + TAB + \
	         loaddate + TAB + loaddate + CRT)

	    setKey = setKey + 1
	    sequenceNum = 1

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

# $Log$
#
