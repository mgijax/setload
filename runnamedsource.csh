#!/bin/csh -f -x

#
# Load Clone Set
#
# Usage:
# 	runnamedsource.csh SCHEMADIR inputfile mode
#
#

setenv SCHEMADIR	$1
setenv INPUTFILE	$2
setenv MODE		$3

source ${SCHEMADIR}/Configuration
setenv CREATEDBY	jsam_load

setenv LOG	$0.log

echo 'Set Load' > $LOG
date >>& $LOG

set loaddir = `dirname $0`

# create the set file
${loaddir}/namedsource_set.py ${INPUTFILE}
sort -k1,1 cloneset.txt > cloneset.txt.sorted

# load the file
${loaddir}/setload.py -S${DBSERVER} -D${DBNAME} -U${DBUSER} -P${DBPASSWORDFILE} -M${MODE} -Icloneset.txt.sorted >>& $LOG

date >>& $LOG

