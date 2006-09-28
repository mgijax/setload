#!/bin/csh -f

#
# Wrapper script to create & load new set definitions
#
# Usage:  setload.csh
#

setenv CONFIGFILE $1

source ${CONFIGFILE}

rm -rf ${SETLOG}
touch ${SETLOG}

date >& ${SETLOG}

${SETLOAD}/setload.py >>& ${SETLOG}

date >>& ${SETLOG}

