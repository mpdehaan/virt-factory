# Generated from gem_plugin-0.2.2.gem by gem2spec -*- rpm-spec -*-
%define gemdir %(ruby -rubygems -e 'puts Gem::dir' 2>/dev/null)
%define gemname gem_plugin
%define geminstdir %{gemdir}/gems/%{gemname}-%{version}

Summary: A plugin system based only on rubygems that uses dependencies only
Name: rubygem-%{gemname}

Version: 0.2.2
Release: 1%{?dist}
Group: Development/Libraries
License: Ruby License
URL: http://mongrel.rubyforge.org
Source0: http://rubyforge.org/frs/download.php/16607/%{gemname}-%{version}.gem
Source1: %{name}.spec.in
BuildRoot: %{_tmppath}/%{name}-%{version}-root-%(%{__id_u} -n)
Requires: rubygems
Requires: rubygem(rake) >= 0.7
BuildRequires: rubygems
BuildArch: noarch
Provides: rubygem(gem_plugin) = %{version}

%description
A plugin system based only on rubygems that uses dependencies only

%prep

%build

%install
%{__rm} -rf %{buildroot}
mkdir -p %{buildroot}%{gemdir}
gem install --local --install-dir %{buildroot}%{gemdir} --force --rdoc %{SOURCE0}
mkdir -p %{buildroot}/%{_bindir}
mv %{buildroot}%{gemdir}/bin/* %{buildroot}/%{_bindir}
rmdir %{buildroot}%{gemdir}/bin
find %{buildroot}%{geminstdir}/bin -type f | xargs chmod a+x

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root)
%{_bindir}/gpgen
%{gemdir}/gems/%{gemname}-%{version}/
%doc %{gemdir}/doc/%{gemname}-%{version}
%doc %{geminstdir}/README
%{gemdir}/cache/%{gemname}-%{version}.gem
%{gemdir}/specifications/%{gemname}-%{version}.gemspec

%changelog
* Tue Mar  6 2007  <sseago@redhat.com> - 0.2.2-1
- Initial packaging.

