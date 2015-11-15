#!/bin/sh

DESTPATH=/opt/nagios-scripts

cd "$(dirname $0)/.."
sd="$(pwd)"

mkdir -p $DESTPATH || exit 1

rsync -tiru etc scripts $DESTPATH/

