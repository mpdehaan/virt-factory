
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: Registration client for virt-factory
Name: virt-factory-register
Source1: version
Version: %(echo `awk '{ print $1 }' %{SOURCE1}`)
Release: %(echo `awk '{ print $2 }' %{SOURCE1}`)%{?dist}
Source0: %{name}-%{version}.tar.gz
License: GPL
Group: Applications/System
Requires: python >= 2.3
Requires: puppet
Requires: python-busrpc
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch
Url: http://virt-factory.et.redhat.com

%description

Virt-factory-register is a command line tool for registering a machine with a virt-factory server. This allows the virt-factory server to control the client machine.

%prep
%setup -q
%build
%{__python} setup.py build

%install
test "x$RPM_BUILD_ROOT" != "x" && rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --root=$RPM_BUILD_ROOT

%files
%{_bindir}/vf_register
%dir %{python_sitelib}/virt-factory
%dir %{python_sitelib}/virt-factory/register
%{python_sitelib}/virt-factory/register/*.py*
%dir /var/log/virt-factory-register


%changelog
* Fri Jul 20 2007 Scott Seago <sseago@redhat.com> - 0.3-2
- use qpid/busrpc for communication

* Thu May 2 2007 Adrian Likins <alikins@redhat.com> - 0.3-1
- change build stuff

* Wed May 1 2007 Adrian Likins <alikins@redhat.com> - 0.0.2-1
- bump to 0.0.2

* Fri Apr 13 2007 Scott Seago <sseago@redhat.com> - 0.0.1-3
- add logfile
 
* Tue Mar 27 2007 Scott Seago <sseago@redhat.com> - 0.0.1-2
- add puppet dependency
 
* Thu Mar 08 2007 Adrian Likins <alikins@redhat.com> - 0.0.1-1
- initial release
