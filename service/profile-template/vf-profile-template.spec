%define pbuild %{_builddir}/%{name}-%{version}
%define profile_name %(echo `awk '{ print $1 }' %{SOURCE1}`)
%define app_root %{_localstatedir}/lib/virt-factory/profiles/%{profile_name}

Summary: 
Source1: version
Name: vf-profile-%{profile_name}
Version: %(echo `awk '{ print $2 }' %{SOURCE1}`)
Release: %(echo `awk '{ print $3 }' %{SOURCE1}`)%{?dist}
License: GPL
Group: Applications/System
Requires: virt-factory-server >= 0.0.3
URL: http://virt-factory.et.redhat.com
Source0: %{name}-%{version}.tar.gz
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

%description



%prep
%setup -q

%build

%install
rm -rf $RPM_BUILD_ROOT
%{__install} -d -m0755 %{buildroot}%{app_root}
%{__cp} -a %{pbuild}/manifests %{buildroot}%{app_root}
%{__cp} -a %{pbuild}/files %{buildroot}%{app_root}
%{__cp} -a %{pbuild}/templates %{buildroot}%{app_root}
%{__cp} -a %{pbuild}/profile.xml %{buildroot}%{app_root}

%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc
%attr(-, virtfact, virtfact) %{app_root}/profile.xml
%attr(-, virtfact, virtfact) %{app_root}/manifests
%attr(-, virtfact, virtfact) %{app_root}/files
%attr(-, virtfact, virtfact) %{app_root}/templates

%post
vf_import %{profile_name}

%changelog

