
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: Virt-factory web service server for use with virt-factory
Name: virt-factory-nodes
Version: 0.0.1
Release: 3%{?dist}
Source0: %{name}-%{version}.tar.gz
License: GPL
Group: Applications/System
Requires: python >= 2.3
Requires: koan >= 0.2.8
Requires: m2crypto
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch
Url: http://virt-factory.et.redhat.com

%description

Virt-factory-node is a web service server for use with the virt-factory provisioning and management system
%prep
%setup -q
%build
%{__python} setup.py build

%install
test "x$RPM_BUILD_ROOT" != "x" && rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --root=$RPM_BUILD_ROOT

%files
%{_bindir}/vf_node_server
/etc/init.d/virt-factory-node-server
%dir /var/lib/virt-factory
%config(noreplace) /var/lib/virt-factory/node-settings
%dir %{python_sitelib}/virt-factory
%dir %{python_sitelib}/virt-factory/nodes
#%{python_sitelib}/virt-factory/*.py*
%{python_sitelib}/virt-factory/nodes/*.py*
%dir %{python_sitelib}/virt-factory/nodes/modules
%dir %{python_sitelib}/virt-factory/nodes/modules/*.py*
%dir %{python_sitelib}/virt-factory/nodes/yaml
%{python_sitelib}/virt-factory/nodes/yaml/*.py*
%dir /var/log/virt-factory


%changelog
* Thu Mar 15 2007 Adrian Likins <alikins@redhat.com> - 0.0.1-3
- add init script

* Thu Mar 08 2007 Adrian Likins <alikins@redhat.com> - 0.0.1-1
- initial release
