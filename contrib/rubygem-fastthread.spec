# Generated from fastthread-0.6.4.1.gem by gem2rpm -*- rpm-spec -*-
%define gemdir %(ruby -rubygems -e 'puts Gem::dir' 2>/dev/null)
%define gemname fastthread
%define geminstdir %{gemdir}/gems/%{gemname}-%{version}
%define ruby_sitearch %(ruby -rrbconfig -e "puts Config::CONFIG['sitearchdir']")
%define _enable_debug_packages 0

Summary: Optimized replacement for thread.rb primitives
Name: rubygem-%{gemname}

Version: 1.0
Release: 1%{?dist}
Group: Development/Languages
License: GPLv2+ or Ruby
URL: http://mongrel.rubyforge.org
Source0: http://gems.rubyforge.org/gems/%{gemname}-%{version}.gem
BuildRoot: %{_tmppath}/%{name}-%{version}-root-%(%{__id_u} -n)
Requires: rubygems
BuildRequires: rubygems
BuildRequires: ruby-devel
Provides: rubygem(%{gemname}) = %{version}

%description
Optimized replacement for thread.rb primitives

%prep

%build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{gemdir}
gem install --local --install-dir %{buildroot}%{gemdir} --force %{SOURCE0}
install -d -m0755 %{buildroot}%{ruby_sitearch}
mv %{buildroot}%{geminstdir}/lib/fastthread.so %{buildroot}%{ruby_sitearch}
chmod 0755 %{buildroot}%{ruby_sitearch}/fastthread.so
rm -rf %{buildroot}%{geminstdir}/ext
strip %{buildroot}%{ruby_sitearch}/fastthread.so

%clean
rm -rf %{buildroot}

%files
%defattr(-, root, root)
%{ruby_sitearch}/fastthread.so
%{gemdir}/gems/%{gemname}-%{version}/
%{gemdir}/cache/%{gemname}-%{version}.gem
%{gemdir}/specifications/%{gemname}-%{version}.gemspec

%changelog
* Thu Aug 23 2007  <sseago@redhat.com> - 1.0-1
- Updated gem to Version 1.0

* Tue Mar  6 2007  <sseago@redhat.com> - 0.6.4.1-1
- Initial packaging.
