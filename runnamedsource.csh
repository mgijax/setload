#!/bin/csh -f

#
# Wrapper script for loading data
#

cd `dirname $0` && source ./Configuration

setenv LOG $0.log
rm -rf $LOG
touch $LOG
 
date > $LOG
 
namedsource_set.py $1
sort -k1,1 cloneset.txt > cloneset.txt.sorted
setload.py -S${DBSERVER} -D${DBNAME} -U${DBUSER} -P${DBPASSWORDFILE} -M${LOADMODE} -Icloneset.txt.sorted >>& $LOG

date >> $LOG

