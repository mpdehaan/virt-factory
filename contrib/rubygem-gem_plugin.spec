# Generated from gem_plugin-0.2.2.gem by gem2rpm -*- rpm-spec -*-
%define gemdir %(ruby -rubygems -e 'puts Gem::dir' 2>/dev/null)
%define gemname gem_plugin
%define geminstdir %{gemdir}/gems/%{gemname}-%{version}

Summary: A plugin system based only on rubygems that uses dependencies only
Name: rubygem-%{gemname}

Version: 0.2.2
Release: 2%{?dist}
Group: Development/Libraries
License: GPLv2+ or Ruby
URL: http://mongrel.rubyforge.org
Source0: http://gems.rubyforge.org/gems/%{gemname}-%{version}.gem
BuildRoot: %{_tmppath}/%{name}-%{version}-root-%(%{__id_u} -n)
Requires: rubygems
Requires: rubygem(rake) >= 0.7
BuildRequires: rubygems
BuildArch: noarch
Provides: rubygem(%{gemname}) = %{version}

%description
A plugin system based only on rubygems that uses dependencies only

%prep

%build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{gemdir}
gem install --local --install-dir %{buildroot}%{gemdir} \
            --force --rdoc %{SOURCE0}
mkdir -p %{buildroot}/%{_bindir}
mv %{buildroot}%{gemdir}/bin/* %{buildroot}/%{_bindir}
rmdir %{buildroot}%{gemdir}/bin

%clean
rm -rf %{buildroot}

%files
%defattr(-, root, root)
%{_bindir}/gpgen
%dir %{geminstdir}
%doc %{gemdir}/doc/%{gemname}-%{version}
%{geminstdir}/bin/
%{geminstdir}/doc/
%{geminstdir}/lib/
%{geminstdir}/Rakefile
%{geminstdir}/resources/
%{geminstdir}/test/
%{geminstdir}/tools/
%doc %{geminstdir}/README
%doc %{geminstdir}/LICENSE
%doc %{geminstdir}/COPYING
%{gemdir}/cache/%{gemname}-%{version}.gem
%{gemdir}/specifications/%{gemname}-%{version}.gemspec

%changelog
* Fri Aug 24 2007 Scott Seago <sseago@redhat.com> - 0.2.2-2
- rpmlint fixes
- added Ruby >= 1.8.6 Requires

* Tue Mar  6 2007  <sseago@redhat.com> - 0.2.2-1
- Initial packaging.

