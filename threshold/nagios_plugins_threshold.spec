%define name 	nagios_plugins_threshold
%define version 0.0.2
%define release 2%{?dist}
%ifarch i386
%define prefix /usr/local/lib/nagios/plugins
%else
%define prefix /usr/local/lib64/nagios/plugins
%endif

Summary:	Host/service/network monitoring program addon. This checks cacti thresholds, and reports them to nagios
Name:		%{name}
Version:	%{version}
Release:	%{release}
License:	GPL
Group:		Networking/Other
Source0:	%{name}-%{version}.tar.bz2
URL:		http://www.nagios.org
Distribution:   RU-Solaris
Vendor:         NBCS-OSS
BuildRoot: 	%{_tmppath}/%{name}-rootsdasd
BuildArch:	x86_64
Conflicts:	nagios_plugins_ru<0.8.14

#check_threshold requires python bindings for mysql and submit_check_result from nagios_addons_ru
Requires:	nagios_addons_ru MySQL-python

%description
Nagios is a program that will monitor hosts and 
services on your network.
This plugins was writting by OSS to check Cacti thresholds and report them to nagios.


%prep
%setup -q -n threshold

%build

%install
mkdir -m 0755 -p $RPM_BUILD_ROOT%{prefix}/rutgers
mkdir -m 0755 -p $RPM_BUILD_ROOT%{prefix}/rutgers/etc
install -pm 0755 check_threshold.py $RPM_BUILD_ROOT%{prefix}/rutgers
install -pm 0755 threshold.cfg $RPM_BUILD_ROOT%{prefix}/rutgers/etc

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{prefix}/rutgers/check_threshold.py*
%config %{prefix}/rutgers/etc/threshold.cfg

%changelog
* Tue Nov 08 2011 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0..0.2-2.ru
- changed prefix to /usr/local/
* Wed Feb 16 2011 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.0.2-1.ru
- Version bump
* Mon Feb 07 2011 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.0.1-3.ru
- cleaned up Requires
* Thu Feb 03 2011 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.0.1-2.ru
Added conflicts with old versions of nagios_plugins_ru, they have their own versions of threshold
* Thu Feb 03 2011 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.0.1-1.ru
-Initial build, broke check_threshold off from nagios_plugins_ru
