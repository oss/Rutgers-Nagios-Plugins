#!/bin/sh

PGM=`basename $0`

printUsage() {
    echo "Usage: $PGM [<warnsecs>] [<critsecs>]\n
Note: If you want N seconds use N-.01 (ie, 2=1.99, 4=3.99)"
    exit 3
}

## Do we have 2 arguments?
[ $# -ne 2 ] && printUsage

[ "$1" = '' ] && printUsage
[ "$2" = '' ] && printUsage
[ "$1" -gt "$2" ] && printUsage

WARNSECS=$1
CRITSECS=$2
RESULT=`time -p /usr/local/sbin/testsaslauthd -u test0 -p \`cat /army/ldap/test0-kerberos-password\` -r STUDENTS.RUTGERS.EDU 2>&1`

if [ "$?" -eq "0" ]; then
    for arg in $RESULT
    do
        # Lets retrieve the "real" number on the next iteration
        if [ "$arg" = "real" ]; then
            flag=1
            continue
        fi

        # Did the command take too long?
        if [ "$flag" -eq "1" ]; then
            exitcode=0
            [ "$arg" -gt "$WARNSECS" ] && exitcode=1
            [ "$arg" -gt "$CRITSECS" ] && exitcode=2
            echo "Kerberos response took $arg seconds" && exit $exitcode
        fi
    done
elif [ "$?" -eq "126" ]; then
    echo "testsaslauthd was found but could not be invoked" && exit 3
elif [ "$?" -eq "127" ]; then
    echo "testsaslauthd could not be found" && exit 3
else
    echo $RESULT && exit 2
fi
