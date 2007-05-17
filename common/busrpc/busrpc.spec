
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
Requires: dbus-python
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
%config(noreplace) /etc/busrpc/system-local.conf
%config(noreplace) /etc/busrpc/amqp.0-8.xml
%config(noreplace) /etc/busrpc/test.conf
%dir %{python_sitelib}/busrpc
%dir %{python_sitelib}/busrpc/local
%dir %{python_sitelib}/busrpc/remote
%{python_sitelib}/busrpc/*.py*
%{python_sitelib}/busrpc/local/*.py*
%{python_sitelib}/busrpc/remote/*.py*
%dir /var/log/busrpc


%post
%preun

%changelog
* Thu May 17 2007 Adrian Likins <alikins@redhat.com> - 0.0.1-1
- inital release

