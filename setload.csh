#!/bin/csh -f -x

#
# Usage:
# 	setload.csh DBSERVER DBNAME inputfile mode
#

setenv SCHEMADIR	$1
setenv INPUTFILE	$2
setenv MODE		$3

source ${SCHEMADIR}/Configuration

setenv LOG	$0.log

echo 'Set Load' > $LOG
date >>& $LOG

set loaddir = `dirname $0`

# load the file
${loaddir}/setload.py -S${DBSERVER} -D${DBNAME} -U${DBUSER} -P${DBPASSWORDFILE} -M${MODE} -I${INPUTFILE} >>& $LOG

date >>& $LOG

