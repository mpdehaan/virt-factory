
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

#FIXME
Summary: message bus based rpc 
Name: busrpc
Source1: version
Version: %(echo `awk '{ print $1 }' %{SOURCE1}`)
Release: %(echo `awk '{ print $2 }' %{SOURCE1}`)%{?dist}
Source0: %{name}-%{version}.tar.gz
License: GPL
Group: Applications/System
Requires: python >= 2.3
Requires: python-simplejson
Requires: python-crypto
Requires: python-qpid
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch
Url: http://virt-factory.et.redhat.com

%description

FIXME: This is an module to communicate with busses.

%prep
%setup -q
%build
%{__python} setup.py build

%install
test "x$RPM_BUILD_ROOT" != "x" && rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --root=$RPM_BUILD_ROOT

%files
%{_bindir}/start-bridge
#%dir /var/lib/bus-rpc
%config(noreplace) /etc/qpid/amqp.0-8.xml
%config(noreplace) /etc/busrpc/test.conf
%dir %{python_sitelib}/busrpc
%{python_sitelib}/busrpc/*.py*
%dir /var/log/busrpc


%post
%preun

%changelog
* Fri July 20 2007 Scott Seago <sseago@redhat.com> - 0.0.1-3
- minor changes to get busrpc up and running

* Tue May 29 2007 Adrian Likins <alikins@redhat.com> - 0.0.1-2
- code got refactored, update spec

* Thu May 17 2007 Adrian Likins <alikins@redhat.com> - 0.0.1-1
- inital release

