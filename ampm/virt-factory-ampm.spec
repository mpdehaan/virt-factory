
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: Command line client for virt-factory virtualization management platform
Name: virt-factory-ampm
Source1: version
Version: %(echo `awk '{ print $1 }' %{SOURCE1}`)
Release: %(echo `awk '{ print $2 }' %{SOURCE1}`)%{?dist}
Source0: %{name}-%{version}.tar.gz
License: GPL
Group: Applications/System
Requires: python >= 2.3
Requires: cobbler >= 0.4.7
Requires: koan >= 0.2.8
Requires: m2crypto
Requires: rhpl
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch
Url: http://virt-factory.et.redhat.com

%description

Command line client for virt-factory virtualization management platform
%prep
%setup -q
%build
%{__python} setup.py build

%install
test "x$RPM_BUILD_ROOT" != "x" && rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --root=$RPM_BUILD_ROOT

%files
%{_bindir}/ampm
%dir %{python_sitelib}/virt-factory
%dir %{python_sitelib}/virt-factory/ampm
%dir %{python_sitelib}/virt-factory/ampm/client
%{python_sitelib}/virt-factory/ampm/client/*.py*
%dir %{python_sitelib}/virt-factory/ampm/command_modules
%{python_sitelib}/virt-factory/ampm/command_modules/*.py*
%dir %{python_sitelib}/virt-factory/ampm/api_modules
%{python_sitelib}/virt-factory/ampm/api_modules/*.py*
%dir /var/log/virt-factory



%preun

%changelog
* Mon Jul 30 2007 Adrian Likins <alikins@redhat.com> - 0.0.4-1
- initial packaging


