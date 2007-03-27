
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: Registration client for virt-factory
Name: virt-factory-register
Version: 0.0.1
Release: 2%{?dist}
Source0: %{name}-%{version}.tar.gz
License: GPL
Group: Applications/System
Requires: python >= 2.3
Requires: puppet
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


%changelog
* Tue Mar 27 2007 Scott Seago <sseago@redhat.com> - 0.0.1-2
- add puppet dependency
 
* Thu Mar 08 2007 Adrian Likins <alikins@redhat.com> - 0.0.1-1
- initial release
