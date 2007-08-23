# Generated from cgi_multipart_eof_fix-2.1.gem by gem2rpm -*- rpm-spec -*-
%define gemdir %(ruby -rubygems -e 'puts Gem::dir' 2>/dev/null)
%define gemname cgi_multipart_eof_fix
%define geminstdir %{gemdir}/gems/%{gemname}-%{version}

Summary: Fix an exploitable bug in CGI multipart parsing
Name: rubygem-%{gemname}

Version: 2.3
Release: 1%{?dist}
Group: Development/Libraries
License: AFL
URL: http://blog.evanweaver.com
Source0: http://gems.rubyforge.org/gems/%{gemname}-%{version}.gem
BuildRoot: %{_tmppath}/%{name}-%{version}-root-%(%{__id_u} -n)
Requires: rubygems
BuildRequires: rubygems
BuildArch: noarch
Provides: rubygem(%{gemname}) = %{version}

%description
Fix an exploitable bug in CGI multipart parsing which affects Ruby <= 1.8.5
when multipart boundary attribute contains a non-halting regular expression
string.


%prep

%build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{gemdir}
gem install --local --install-dir %{buildroot}%{gemdir} \
            --force --rdoc %{SOURCE0}

%clean
rm -rf %{buildroot}

%files
%defattr(-, root, root)
%{gemdir}/gems/%{gemname}-%{version}/
%doc %{gemdir}/doc/%{gemname}-%{version}
%{gemdir}/cache/%{gemname}-%{version}.gem
%{gemdir}/specifications/%{gemname}-%{version}.gemspec

%changelog
* Thu Aug 23 2007  <sseago@redhat.com> - 2.3-1
- Updated gem to Version 2.3

* Tue Mar  6 2007  <sseago@redhat.com> - 2.1-1
- Initial packaging.

