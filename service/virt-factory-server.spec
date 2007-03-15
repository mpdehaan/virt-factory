
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: Virt-factory web service server for use with virt-factory
Name: virt-factory-server
Version: 0.0.1
Release: 3%{?dist}
Source0: %{name}-%{version}.tar.gz
License: GPL
Group: Applications/System
Requires: python >= 2.3
Requires: cobbler >= 0.4.3
Requires: koan >= 0.2.7
Requires: python-virtinst
Requires: puppet-server
Requires: python-sqlite2
Requires: m2crypto
Requires: rhpl
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch
Url: http://virt-factory.et.redhat.com

%description

Virt-factory-server is a web service server for use with the virt-factory provisioning and management system
%prep
%setup -q
%build
%{__python} setup.py build

%install
test "x$RPM_BUILD_ROOT" != "x" && rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --root=$RPM_BUILD_ROOT

%files
%{_bindir}/vf_server
%{_bindir}/vf_taskatron
%{_bindir}/vf_import
%{_bindir}/vf_get_puppet_node
%{_bindir}/vf_create_db.sh
%{_bindir}/vf_nodecomm
/etc/init.d/virt-factory-server
%dir /var/lib/virt-factory
%config(noreplace) /etc/virt-factory/settings
# kickstart templaces
%config(noreplace) /var/lib/virt-factory/kick-fc6.ks
%dir %{python_sitelib}/virt-factory
%dir %{python_sitelib}/virt-factory/server
#%{python_sitelib}/virt-factory/*.py*
%{python_sitelib}/virt-factory/server/*.py*
%dir %{python_sitelib}/virt-factory/server/modules
%dir %{python_sitelib}/virt-factory/server/modules/*.py*
%dir %{python_sitelib}/virt-factory/server/yaml
%{python_sitelib}/virt-factory/server/yaml/*.py*
%dir /usr/share/virt-factory
%dir /usr/share/virt-factory/db_schema
/usr/share/virt-factory/db_schema/*.sql
%dir /var/log/virt-factory


%changelog
* Thu Mar 15 2007 Adrian Likins <alikins@redhat.com> - 0.0.1-3
- rename the init script

* Fri Mar 09 2007 Adrian Likins <alikins@redhat.com> - 0.0.1-2
- add schema to /usr/share/virt-factory
- add vf_create_db.sh to create db
- add vf_server init script

* Thu Mar 08 2007 Adrian Likins <alikins@redhat.com> - 0.0.1-1
- initial release
