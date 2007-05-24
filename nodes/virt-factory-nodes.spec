
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: Virt-factory web service server for use with virt-factory
Name: virt-factory-nodes
Source1: version
Version: %(echo `awk '{ print $1 }' %{SOURCE1}`)
Release: %(echo `awk '{ print $2 }' %{SOURCE1}`)%{?dist}
Source0: %{name}-%{version}.tar.gz
License: GPL
Group: Applications/System
Requires: python >= 2.3
Requires: koan >= 0.2.8
Requires: rhpl
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
%config(noreplace) /etc/virt-factory-nodes/node-settings
%dir %{python_sitelib}/virt-factory
%dir %{python_sitelib}/virt-factory/nodes
#%{python_sitelib}/virt-factory/*.py*
%{python_sitelib}/virt-factory/nodes/*.py*
%{python_sitelib}/virt-factory/nodes/modules/*.py*
%dir %{python_sitelib}/virt-factory/nodes/modules
%dir %{python_sitelib}/virt-factory/nodes/yaml
%{python_sitelib}/virt-factory/nodes/yaml/*.py*
%dir /var/log/virt-factory-nodes

%post
/sbin/chkconfig --add virt-factory-node-server
exit 0

%preun
if [ "$1" = 0 ] ; then
  /sbin/service virt-factory-node-server stop > /dev/null 2>&1
  /sbin/chkconfig --del virt-factory-node-server
fi

%changelog
* Thu May 2 2007 Adrian Likins <alikins@redhat.com> - 0.0.3-1
- change rpm spec to use version file

* Wed May 1 2007 Adrian Likins <alikins@redhat.com> - 0.0.2-1
- add chkconfig stuff to scripts
- rev to 0.0.2

* Mon Apr 23 2007 Adrian Likins <alikins@redhat.com> - 0.0.1-5
- fix module import problems

* Mon Apr 23 2007 Adrian Likins <alikins@redhat.com> - 0.0.1-4
- remove spurious %dir on module files

* Thu Mar 15 2007 Adrian Likins <alikins@redhat.com> - 0.0.1-3
- add init script

* Thu Mar 08 2007 Adrian Likins <alikins@redhat.com> - 0.0.1-1
- initial release
