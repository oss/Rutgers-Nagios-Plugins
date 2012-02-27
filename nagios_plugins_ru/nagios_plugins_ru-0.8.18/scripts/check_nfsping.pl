#!/usr/bin/perl
use strict;
use warnings;
use Switch;

#constants
my $NAGIOS_EXIT_CODES = {"OK" => 0, "WARNING" =>1, "CRITICAL" =>2, "UNKNOWN" =>3};
my $PING_COMMAND = "/usr/local/bin/nfsping";

#if we don't have 1 argument, some is wrong
my $numArgs = $#ARGV +1;
if ($numArgs != 1){
	print "UNKNOWN: Script must be run with exactly one argument, the host to check\n";
	exit $NAGIOS_EXIT_CODES->{"UNKNOWN"};
}

my $host = $ARGV[0];

my $cmd = "$PING_COMMAND $host 2>&1";
my $result = `$cmd`;

#replace newlines with commas, so nagios output is all on one line
$result =~ s/\n/, /g;
#remove last comma
$result =~ s/, $//;

switch ($?){
	case 0 { 
		 print "OK: $result\n";
		 exit $NAGIOS_EXIT_CODES->{"OK"};
	}
	else { 
		print "CRITICAL: $result\n";
		exit $NAGIOS_EXIT_CODES->{"CRITICAL"};
	}

}
