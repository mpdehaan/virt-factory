	# Generated from fastthread-0.6.4.1.gem by gem2spec -*- rpm-spec -*-
%define gemdir %(ruby -rubygems -e 'puts Gem::dir' 2>/dev/null)
%define gemname fastthread
%define geminstdir %{gemdir}/gems/%{gemname}-%{version}
%{!?ruby_sitearch: %define ruby_sitearch %(ruby -rrbconfig -e "puts Config::CONFIG['sitearchdir']")}

Summary: Optimized replacement for thread.rb primitives
Name: rubygem-%{gemname}

Version: 0.6.4.1
Release: 1%{?dist}
Group: Development/Libraries
License: Ruby License
URL: http://mongrel.rubyforge.org
Source0: http://rubyforge.org/frs/download.php/17526/%{gemname}-%{version}.gem
Source1: %{name}.spec.in
BuildRoot: %{_tmppath}/%{name}-%{version}-root-%(%{__id_u} -n)
Requires: rubygems
BuildRequires: rubygems
BuildRequires: ruby-devel
Provides: rubygem(fastthread) = %{version}

%description


%prep

%build

%install
%{__rm} -rf %{buildroot}
mkdir -p %{buildroot}%{gemdir}
gem install --local --install-dir %{buildroot}%{gemdir} --force %{SOURCE0}
%{__install} -d -m0755 %{buildroot}%{ruby_sitearch}
#move any .so files to the proper arch-specific dir
mv %{buildroot}%{geminstdir}/lib/fastthread.so %{buildroot}%{ruby_sitearch}
%{__chmod} 0755 %{buildroot}%{ruby_sitearch}/fastthread.so
rm -rf %{buildroot}%{geminstdir}/ext

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root)
#arch-specific libs here
%{ruby_sitearch}/fastthread.so
%{gemdir}/gems/%{gemname}-%{version}/
%{gemdir}/cache/%{gemname}-%{version}.gem
%{gemdir}/specifications/%{gemname}-%{version}.gemspec

%changelog
* Tue Mar  6 2007  <sseago@redhat.com> - 0.6.4.1-1
- Initial packaging.
