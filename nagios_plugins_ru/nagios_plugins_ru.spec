%define debug_package %{nil}
%define name 	nagios_plugins_ru
%define version 0.8.18
%define release 2.ru6
%ifarch i386
%define prefix /usr/local/lib/nagios/plugins
%else
%define prefix /usr/local/lib64/nagios/plugins
%endif

Summary:	Host/service/network monitoring program addons
Name:		%{name}
Version:	%{version}
Release:	%{release}
License:	GPL
Group:		Networking/Other
Source0:	%{name}-%{version}.tar.bz2
URL:		http://www.nagios.org
Distribution:   RU-Solaris
Vendor:         NBCS-OSS
BuildRoot: 	%{_tmppath}/%{name}-root

#check_clamav requires sed cut grep perl tr cat
Requires:	/usr/sbin/smartctl /usr/bin/ipmitool /usr/bin/sudo udev nagios-plugins nagios-plugins-disk nagios-plugins-dns nagios-plugins-dummy nagios-plugins-file_age nagios-plugins-ftp nagios-plugins-http nagios-plugins-imap nagios-plugins-jabber nagios-plugins-load nagios-plugins-users nagios-plugins-mailq nagios-plugins-mysql nagios-plugins-ping nagios-plugins-pop nagios-plugins-procs nagios-plugins-radius nagios-plugins-smtp nagios-plugins-ssh nagios-plugins-tcp nagios-plugins-ups nagios-plugins-swap nagios-plugins-ntp nagios-plugins-dig

Requires:       grep
Requires:       nc
Requires:      nfsping
Requires:     lsof 

%description
Nagios is a program that will monitor hosts and 
services on your network.

These plugins are home-grown at Rutgers. 
They require entries in sudoers, for instance. Be careful.

%prep
%setup -q

# Prefix might be different on different systems
sed -i 's|/usr/local|%{_prefix}|' scripts/*

#we need to change the paths for 32bit machines
%ifarch i386
for i in scripts/*
do
   sed -i 's,/usr/local/lib64,/usr/local/lib,g' $i
done
%endif

%build
pushd src
gcc $RPM_OPT_FLAGS check_em01.c -o check_em01

%install
pushd scripts
mkdir -m 0755 -p $RPM_BUILD_ROOT%{prefix}/rutgers
mkdir -m 0755 -p $RPM_BUILD_ROOT%{prefix}/rutgers/etc
install -pm 0755 check_dhcp_helpers $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_ipmi $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_ipmi_chassis_remote $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_ipmi_remote $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_smartctl $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_dhcp_helpers_internal $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_ldap_clearbind $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_ldap_reader $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 ldapSynchCheck.py $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_ldap_sync $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_clamav $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_clamav_defs.py $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_file_contents $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_imap_auth $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_tftp $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_ldap_namingcontexts $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_ldap_readeverything $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_xenvm $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 kerbtest.sh $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_mailman_qfiles $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_ldapsubmitter $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_nfsping.pl $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 check_directors $RPM_BUILD_ROOT%{prefix}/rutgers
mkdir -m 0755 -p $RPM_BUILD_ROOT/etc/udev/permissions.d
install -m 0755 70-nagios-ipmi.permissions $RPM_BUILD_ROOT/etc/udev/permissions.d
popd

pushd src
install -pm 0755 check_em01 $RPM_BUILD_ROOT%{prefix}/rutgers
# WARNING: check_by_http is compiled separately in the nagios-plugins rpm but is
# packaged separated here. In the future, this will be built here when check_by_http
# has been rewritten so that it does not need to be built agains nagios-plugins
%ifarch i386
install -m 0755 check_by_http-i386 $RPM_BUILD_ROOT%{prefix}/rutgers/check_by_http
%else
install -m 0755 check_by_http-x86_64 $RPM_BUILD_ROOT%{prefix}/rutgers/check_by_http
%endif
popd

%clean
rm -rf $RPM_BUILD_ROOT

%files
%doc scripts/config.sample
%defattr(-,root,root,-)
%dir %{prefix}/rutgers
%{prefix}/rutgers/*
%attr(0644, root, root) /etc/udev/permissions.d/70-nagios-ipmi.permissions

%changelog
* Fri Feb 10 2012 Josh Matthews <jam761@nbcs.rutgers.edu> - 0.8.18-2.ru6
- updated to install in /usr/local/lib64/nagios instead of /usr/lib64/nagios

* Thu Feb 09 2012 Phillip Quiza <pquiza@nbcs.rutgers.edu> - 0.8.18-1.ru6
- Initial build for CentOS 6 
* Tue Apr 19 2011 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.8.18-1
- added check_directors
- added lsof to requires
* Thu Apr 14 2011 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.8.17-2
- added check_nfsping.pl
- added nfsping to requires
* Thu Mar 10 2011 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.8.16-1
- updated check_smartctl
* Wed Mar 09 2011 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.8.15-1
- updated check_smartctl
* Thu Feb 03 2011 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.8.14-1
- removed check_threshold, its a different package now
* Mon Jan 31 2011 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.8.13-1
- updated check_thresholy.py
- added MySQL-python dependecy (for check_threshold)
* Mon Nov 29 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.8.12-1
- update check_smartctl

* Mon Nov 3 2010 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 1.8.11-2
- remembered to include check_threshold config file...
* Mon Nov 3 2010 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 1.8.11-1
- added check_threshold
* Fri Oct 29 2010 Russ Frank <rfranknj@nbcs.rutgers.edu> - 0.8.10-1
- updated check_smartctl

* Tue Oct 19 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.8.9-1
- update check_ipmi

* Wed Sep 29 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.8.8.6-2
- include the correct check_ldapsubmitter

* Tue Sep 28 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.8.8.6-1
- bump to 0.8.8.6 (add check_ldapsubmitter)

* Mon Mar 25 2010 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.8.8.5-1
- bump to 0.8.8.5 
* Mon Mar 15 2010 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.8.8.4-1
- bump to 0.8.8.4 (check_clamav_defs.py update)
* Thu Mar 04 2010 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.8.8.1-1
-bugfix release
* Thu Mar 04 2010 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.8.8-1
-Version bump (Check_clamav_defs.py updated)

* Tue Feb 23 2010 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.8.7-1
- added check_clamav_defs.py, added config.sample to doc

* Fri Feb 19 2010 Jarek Sedlacek < jarek@nbcs.rutgers.edu> - 0.8.6-18 
- removed OpenIPMI-tools dependency 

* Thu Jan 21 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.8.6-17
- Merge the accidental fork of this package

* Wed Jan 20 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.8.6-16
- Fix check_ipmi_*remote scripts for prefix

* Tue Jan 19 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.8.6-15
- Update check_em01 with new source

* Wed Dec 23 2009 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.8.6-14
- Add check_mailman_qfiles

* Mon Nov 16 2009 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.8.6-13
- Add check_em01
- Build only on x86_64 as per request

* Mon Nov 02 2009 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.8.6-12
- Fix typo in check_clamav script

* Tue Jul 28 2009 Naveen Gavini <ngavini@nbcs.rutgers.edu> - 0.8.6-10
- Updates to ldapSynchCHeck.py
* Wed Feb 25 2009 David Diffenbaugh <davediff@nbcs.rutgers.edu> - 0.8.6-9
- updated to check_clamav-2.0.7 
- updates to check_file_contents
* Mon Feb 16 2009 Naveen Gavini <ngavini@nbcs.rutgers.edu> - 0.8.6-7
- Added config directory, new required new check_ipmi, tftp, xenvm, removed check_ipmi_chassis ipmi_noshutdown ipmi_shutdown.
* Tue Jan 27 2009 Naveen Gavini <ngavini@nbcs.rutgers.edu> - 0.8.6-6
- Added, check_ipmi symlink. 
* Wed Jan 14 2009 Naveen Gavini <ngavini@nbcs.rutgers.edu> - 0.8.6-3
- Added, removed and updated scripts.
* Tue Nov 18 2008 David Diffenbaugh <davediff@nbcs.rutgers.edu> - 0.8.6-2
- updates to check_backups script, bumped release number
* Wed Oct 15 2008 Brian Schubert <schubert@nbcs.rutgers.edu> - 0.8.6-1
- Added check_backups script, bumped version to 0.8.6
* Mon Sep 15 2008 David Diffenbaugh <davediff@nbcs.rutgers.edu> - 0.8.5-3
- update to check_clamav script (added PATH variable)
* Thu Aug 28 2008 David Diffenbaugh <davediff@nbcs.rutgers.edu> - 0.8.5-2
- added ifarch so that path is correct in i386
* Wed Aug 20 2008 David Diffenbaugh <davediff@nbcs.rutgers.edu> - 0.8.5-1
- changed to UNKNOWN when check_clamav times out
* Tue Jul 1 2008 David Diffenbaugh <davediff@nbcs.rutgers.edu> - 0.8.4-1
- fixed argument handling in check_clamav script, bumped to 0.8.4
* Tue Jun 24 2008 David Diffenbaugh <davediff@nbcs.rutgers.edu> - 0.8.3-1
- made changes to check_clamav script, bumped version to 0.8.3
* Fri Jun 06 2008 David Diffenbaugh <davediff@nbcs.rutgers.edu> - 0.8.2-1
- added check_clamav script, bumped version number to 0.8.2 
