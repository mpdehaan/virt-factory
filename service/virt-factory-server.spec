
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: Virt-factory web service server for use with virt-factory
Name: virt-factory-server
Source1: version
Version: %(echo `awk '{ print $1 }' %{SOURCE1}`)
Release: %(echo `awk '{ print $2 }' %{SOURCE1}`)%{?dist}
Source0: %{name}-%{version}.tar.gz
License: GPL
Group: Applications/System
Requires: python >= 2.3
Requires: cobbler >= 0.4.7
Requires: koan >= 0.2.8
Requires: python-virtinst
Requires: puppet-server
Requires: python-sqlite2
Requires: m2crypto
Requires: rhpl
Requires: yum-utils
Requires: python-sqlalchemy
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
%{_bindir}/vf_upgrade_db
%{_bindir}/vf_config_firewall
%{_bindir}/vf_remove_firewall_rules
%{_bindir}/vf_gen_profile_stub
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
%{python_sitelib}/virt-factory/server/modules/*.py*
%dir %{python_sitelib}/virt-factory/server/yaml
%{python_sitelib}/virt-factory/server/yaml/*.py*
%dir %{python_sitelib}/virt-factory/server/db_upgrade
%{python_sitelib}/virt-factory/server/db_upgrade/*.py*
%dir /usr/share/virt-factory
%dir /usr/share/virt-factory/db_schema
/usr/share/virt-factory/db_schema/*.sql
%dir /usr/share/virt-factory/db_schema/upgrade
/usr/share/virt-factory/db_schema/upgrade/upgrades.conf
/usr/share/virt-factory/db_schema/upgrade/*.sql
%dir /usr/share/virt-factory/puppet-config
/etc/puppet/manifests/site.pp
/usr/share/virt-factory/puppet-config/puppetmaster
/usr/share/virt-factory/puppet-config/puppetd.conf
%dir /usr/share/virt-factory/profile-template
/etc/puppet/manifests/site.pp
/usr/share/virt-factory/profile-template/Makefile
/usr/share/virt-factory/profile-template/profile.xml.in
/usr/share/virt-factory/profile-template/vf-profile-template.spec
/usr/share/virt-factory/profile-template/init.pp
%dir /var/log/virt-factory


%post
/bin/cp /usr/share/virt-factory/puppet-config/puppetmaster /etc/sysconfig
/bin/cp /usr/share/virt-factory/puppet-config/puppetd.conf /etc/puppet
#if [ -f /var/lib/virt-factory/primary_db ]; then
#    /usr/bin/vf_upgrade_db
#else
#    /usr/bin/vf_create_db.sh
#fi
/sbin/chkconfig --add virt-factory-server
exit 0

%preun
if [ "$1" = 0 ] ; then
  /sbin/service virt-factory-server stop > /dev/null 2>&1
  /sbin/chkconfig --del virt-factory-server
fi


%changelog
* Tue May 29 2007 Adrian Likins <alikins@redhat.com> - 0.0.3-2
- remove db setup/upgrade stuff from rpms

* Wed May 1 2007 Adrian Likins <alikins@redhat.com> - 0.0.2-1
- add chkconfig stuff in scripts
- bump to 0.0.2

* Mon Apr 23 2007 Adrian Likins <alikins@redhat.com> - 0.0.1-8
- remove spurious %dir on module files

* Thu Apr 12 2007 Scott Seago <sseago@redhat.com> - 0.0.1-7
- moved db creation from service init script to rpm %post
- for rpm upgrades, perform schema upgrade
 
* Tue Apr 10 2007 Scott Seago <sseago@redhat.com> - 0.0.1-6
- add iptables config scripts
 
* Tue Mar 27 2007 Scott Seago <sseago@redhat.com> - 0.0.1-5
- add schema upgrade scripts
 
* Tue Mar 20 2007 Scott Seago <sseago@redhat.com> - 0.0.1-4
- add puppet config files
 
* Thu Mar 15 2007 Adrian Likins <alikins@redhat.com> - 0.0.1-3
- rename the init script

* Fri Mar 09 2007 Adrian Likins <alikins@redhat.com> - 0.0.1-2
- add schema to /usr/share/virt-factory
- add vf_create_db.sh to create db
- add vf_server init script

* Thu Mar 08 2007 Adrian Likins <alikins@redhat.com> - 0.0.1-1
- initial release
