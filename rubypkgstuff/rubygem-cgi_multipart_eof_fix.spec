# Generated from cgi_multipart_eof_fix-2.1.gem by gem2spec -*- rpm-spec -*-
%define gemdir %(ruby -rubygems -e 'puts Gem::dir' 2>/dev/null)
%define gemname cgi_multipart_eof_fix
%define geminstdir %{gemdir}/gems/%{gemname}-%{version}

Summary: Fix an exploitable bug in CGI multipart parsing which affects Ruby <= 1.8.5 when multipart boundary attribute contains a non-halting regular expression string.
Name: rubygem-%{gemname}

Version: 2.1
Release: 1%{?dist}
Group: Development/Libraries
License: Academic Free License (AFL) v. 3.0
URL: http://blog.evanweaver.com
Source0: http://rubyforge.org/frs/download.php/17197/%{gemname}-%{version}.gem
Source1: %{name}.spec.in
BuildRoot: %{_tmppath}/%{name}-%{version}-root-%(%{__id_u} -n)
Requires: rubygems
BuildRequires: rubygems
BuildArch: noarch
Provides: rubygem(cgi_multipart_eof_fix) = %{version}

%description
Fix an exploitable bug in CGI multipart parsing which affects Ruby <= 1.8.5 when multipart boundary attribute contains a non-halting regular expression string.

%prep

%build

%install
%{__rm} -rf %{buildroot}
mkdir -p %{buildroot}%{gemdir}
gem install --local --install-dir %{buildroot}%{gemdir} --force --rdoc %{SOURCE0}

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root)
%{gemdir}/gems/%{gemname}-%{version}/
%doc %{gemdir}/doc/%{gemname}-%{version}
%{gemdir}/cache/%{gemname}-%{version}.gem
%{gemdir}/specifications/%{gemname}-%{version}.gemspec

%changelog
* Tue Mar  6 2007  <sseago@redhat.com> - 2.1-1
- Initial packaging.

