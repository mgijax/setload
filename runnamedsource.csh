#!/bin/csh -f -x

#
# Load Clone Set
#
# Usage:
# 	runnamedsource.csh DBSERVER DBNAME inputfile mode
#
# Example:
#	runnamedsource.csh PROD_MGI mgd namedsource_set.txt full
#

setenv DBSERVER		$1
setenv DBNAME		$2
setenv INPUTFILE	$3
setenv MODE		$4

setenv DBUTILITIESPATH		/usr/local/mgi/dbutils/mgidbutilities
setenv DBUSER			mgd_dbo
setenv DBPASSWORDFILE		${DBUTILITIESPATH}/.mgd_dbo_password

setenv CREATEDBY "jsam_load"
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

