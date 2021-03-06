#
# Spec file for Qpid C++ packages: qpidc qpidc-devel, qpidd, qpidd-devel
#
%define qpidd qpidd

Name:           qpidc
Version:        0.2
Release:        5%{?dist}
Summary:        Libraries for Qpid C++ client applications
Group:          System Environment/Libraries
License:        Apache Software License
URL:            http://rhm.et.redhat.com/qpidc
Source0:        http://rhm.et.redhat.com/download/%{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires: apr-devel
BuildRequires: boost-devel
BuildRequires: cppunit-devel
BuildRequires: doxygen
BuildRequires: e2fsprogs-devel
BuildRequires: graphviz
BuildRequires: help2man
BuildRequires: libtool
BuildRequires: pkgconfig

Requires: boost
Requires: apr

Requires(post):/sbin/chkconfig
Requires(preun):/sbin/chkconfig
Requires(preun):/sbin/service
Requires(postun):/sbin/service

%description
Run-time libraries for AMQP client applications developed using Qpid
C++. Clients exchange messages with an AMQP message broker using
the AMQP protocol.

%package devel
Summary: Header files and documentation for developing Qpid C++ clients
Group: Development/System
Requires: %name = %version-%release
Requires: apr-devel
Requires: boost-devel
Requires: e2fsprogs-devel

%description devel
Libraries, header files and documentation for developing AMQP clients
in C++ using Qpid.  Qpid implements the AMQP messaging specification.

%package -n %{qpidd}
Summary: An AMQP message broker daemon
Group: System Environment/Daemons
Requires: %name = %version-%release

%description -n %{qpidd}
A message broker daemon that receives stores and routes messages using
the open AMQP messaging protocol.

%package -n %{qpidd}-devel
Summary: Libraries and header files for developing Qpid broker extensions
Group: Development/System
Requires: %name-devel = %version-%release
Requires: %{qpidd} = %version-%release

%description -n %{qpidd}-devel
Libraries and header files for developing extensions to the
Qpid broker daemon.

%prep
%setup -q

%build
%configure --disable-static
make %{?_smp_mflags}
# Remove this generated perl file, we don't need it and it upsets rpmlint.
rm docs/api/html/installdox

%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot}
install  -Dp -m0755 etc/qpidd %{buildroot}%{_initrddir}/qpidd
rm -f %{buildroot}%_libdir/*.a
rm -f %{buildroot}%_libdir/*.la

%clean
rm -rf %{buildroot}

%check
make check

%files
%defattr(-,root,root,-)
%doc LICENSE NOTICE README
%_libdir/libqpidcommon.so.0
%_libdir/libqpidcommon.so.0.1.0
%_libdir/libqpidclient.so.0
%_libdir/libqpidclient.so.0.1.0

%files devel
%defattr(-,root,root,-)
%_includedir/qpid/*.h
%_includedir/qpid/client
%_includedir/qpid/framing
%_includedir/qpid/sys
%_libdir/libqpidcommon.so
%_libdir/libqpidclient.so
%doc docs/api/html

%files -n %{qpidd}
%defattr(-,root,root,-)
%_libdir/libqpidbroker.so.0
%_libdir/libqpidbroker.so.0.1.0
%_sbindir/%{qpidd}
%{_initrddir}/%{qpidd}
%doc %_mandir/man1/%{qpidd}.*

%files -n %{qpidd}-devel
%defattr(-,root,root,-)
%doc rpm/README.qpidd-devel 
%defattr(-,root,root,-)
%_libdir/libqpidbroker.so
%_includedir/qpid/broker

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%post -n %{qpidd}
# This adds the proper /etc/rc*.d links for the script
/sbin/chkconfig --add qpidd
/sbin/ldconfig

%preun -n %{qpidd}
# Check that this is actual deinstallation, not just removing for upgrade.
if [ $1 = 0 ]; then
        /sbin/service qpidd stop >/dev/null 2>&1 || :
        /sbin/chkconfig --del qpidd
fi

%postun -n %{qpidd}
if [ "$1" -ge "1" ]; then
        /sbin/service qpidd condrestart >/dev/null 2>&1 || :
fi
/sbin/ldconfig

%changelog

* Tue Apr 17 2007 Alan Conway <aconway@redhat.com> - 0.2-5
- Add missing Requires: e2fsprogs-devel for qpidc-devel.

* Tue Apr 17 2007 Alan Conway <aconway@redhat.com> - 0.2-4
- longer broker_start timeout to avoid failures in plague builds.

* Tue Apr 17 2007 Alan Conway <aconway@redhat.com> - 0.2-3
- Add missing Requires: apr in qpidc.

* Mon Apr 16 2007 Alan Conway <aconway@redhat.com> - 0.2-2
- Bugfix for memory errors on x86_64.

* Thu Apr 12 2007 Alan Conway <aconway@redhat.com> - 0.2-1
- Bumped version number for rhm dependencies. 

* Wed Apr 11 2007 Alan Conway <aconway@redhat.com> - 0.1-5
- Add qpidd-devel sub-package.

* Mon Feb 19 2007 Jim Meyering <meyering@redhat.com> - 0.1-4
- Address http://bugzilla.redhat.com/220630:
- Remove redundant "cppunit" build-requires.
- Add --disable-static.

* Thu Jan 25 2007 Alan Conway <aconway@redhat.com> - 0.1-3
- Applied Jim Meyerings fixes from http://mail-archives.apache.org/mod_mbox/incubator-qpid-dev/200701.mbox/%3c87hcugzmyp.fsf@rho.meyering.net%3e

* Mon Dec 22 2006 Alan Conway <aconway@redhat.com> - 0.1-1
- Fixed all rpmlint complaints (with help from David Lutterkort)
- Added qpidd --daemon behaviour, fix init.rc scripts

* Fri Dec  8 2006 David Lutterkort <dlutter@redhat.com> - 0.1-1
- Initial version based on Jim Meyering's sketch and discussions with Alan
  Conway

