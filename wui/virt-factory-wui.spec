%define pbuild %{_builddir}/%{name}-%{version}
%define app_root %{_datadir}/%{name}

Summary: Virt-Factory front end WUI
Name: virt-factory-wui
Source1: version
Version: %(echo `awk '{ print $1 }' %{SOURCE1}`)
Release: %(echo `awk '{ print $2 }' %{SOURCE1}`)%{?dist}
Source0: %{name}-%{version}.tar.gz
License: GPL
Group: Applications/System
Requires: ruby >= 1.8.1
Requires: ruby(abi) = 1.8
Requires: rubygem(rails) >= 1.2.2
Requires: rubygem(mongrel) >= 1.0.1
Requires: ruby-gettext-package
Requires: httpd >= 2.0
Requires(post):  /sbin/chkconfig
Requires(preun): /sbin/chkconfig
Requires(preun): /sbin/service
BuildRequires: ruby >= 1.8.1
BuildRequires: ruby-devel
BuildRequires: ruby-gettext-package
BuildRequires: rubygem(rake) >= 0.7
Provides: virt-factory-wui
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
URL: http://virt-factory.et.redhat.com

%description

The WUI client for the Virt-Factory XMLRPC server. Most Virt-Factory
tasks can be performed via this interface.

%prep
%setup -q

%build

%install
test "x$RPM_BUILD_ROOT" != "x" && rm -rf $RPM_BUILD_ROOT
mkdir %{buildroot}

%{__install} -d -m0755 %{buildroot}%{_sbindir}
%{__install} -d -m0755 %{buildroot}%{_initrddir}
%{__install} -d -m0755 %{buildroot}%{_sysconfdir}/httpd/conf.d
%{__install} -d -m0755 %{buildroot}%{_sysconfdir}/sysconfig/%{name}
%{__install} -d -m0755 %{buildroot}%{_localstatedir}/lib/%{name}
%{__install} -d -m0755 %{buildroot}%{_localstatedir}/log/%{name}
%{__install} -d -m0755 %{buildroot}%{_localstatedir}/run/%{name}
%{__install} -d -m0755 %{buildroot}%{app_root}

touch %{buildroot}%{_localstatedir}/log/%{name}/mongrel.log
touch %{buildroot}%{_localstatedir}/log/%{name}/rails.log
%{__install} -p -m0644 %{pbuild}/conf/%{name}.conf %{buildroot}%{_sysconfdir}/httpd/conf.d
%{__install} -Dp -m0755 %{pbuild}/conf/%{name} %{buildroot}%{_initrddir}
%{__install} -p -m0644 %{pbuild}/conf/server %{buildroot}%{_sysconfdir}/sysconfig/%{name}
%{__cp} -a %{pbuild}/src/* %{buildroot}%{app_root}
%{__rm} -rf %{buildroot}%{app_root}/tmp 
%{__mkdir} %{buildroot}%{_localstatedir}/lib/%{name}/tmp
%{__ln_s} %{_localstatedir}/lib/%{name}/tmp %{buildroot}%{app_root}/tmp
find %{buildroot}%{app_root} -type f -perm +ugo+x -print0 | xargs -0 -r %{__chmod} a-x

%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,0755)
%{_initrddir}/%{name}
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%dir /etc/sysconfig/%{name}
%config(noreplace) /etc/sysconfig/%{name}/server
%doc
%attr(-, virtfact, virtfact) %{_localstatedir}/lib/%{name}
%attr(-, virtfact, virtfact) %{_localstatedir}/run/%{name}
%attr(-, virtfact, virtfact) %{_localstatedir}/log/%{name}
%{app_root}

%pre
/usr/sbin/groupadd -r virtfact 2>/dev/null || :
/usr/sbin/useradd -g virtfact -c "Virt-Factory" \
    -s /sbin/nologin -r -d /var/virtfact virtfact 2> /dev/null || :

%post
/sbin/chkconfig --add virt-factory-wui
exit 0

%preun
if [ "$1" = 0 ] ; then
  /sbin/service virt-factory-wui stop > /dev/null 2>&1
  /sbin/chkconfig --del virt-factory-wui
fi
%changelog
* Wed May 1 2007 Adrian Likins <alikins@redhat.com> - 0.0.2-1
- bump to 0.0.2

* Thu Mar  1 2007  <sseago@redhat.com> - 0.1-1
- Initial build.

