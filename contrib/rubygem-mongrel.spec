# Generated from mongrel-1.0.1.gem by gem2spec -*- rpm-spec -*-
%define gemdir %(ruby -rubygems -e 'puts Gem::dir' 2>/dev/null)
%define gemname mongrel
%define geminstdir %{gemdir}/gems/%{gemname}-%{version}
%{!?ruby_sitearch: %define ruby_sitearch %(ruby -rrbconfig -e "puts Config::CONFIG['sitearchdir']")}

Summary: A small fast HTTP library and server that runs Rails, Camping, Nitro and Iowa apps.
Name: rubygem-%{gemname}

Version: 1.0.1
Release: 1%{?dist}
Group: Development/Libraries
License: Ruby License
URL: http://mongrel.rubyforge.org
Source0: http://rubyforge.org/frs/download.php/16719/%{gemname}-%{version}.gem
Source1: %{name}.spec.in
BuildRoot: %{_tmppath}/%{name}-%{version}-root-%(%{__id_u} -n)
Requires: rubygems
Requires: rubygem(daemons) >= 1.0.3
Requires: rubygem(fastthread) >= 0.6.2
Requires: rubygem(gem_plugin) >= 0.2.2
Requires: rubygem(cgi_multipart_eof_fix) >= 1.0.0
BuildRequires: rubygems
Provides: rubygem(mongrel) = %{version}

%description
A small fast HTTP library and server that runs Rails, Camping, Nitro and Iowa apps.

%prep

%build

%install
%{__rm} -rf %{buildroot}
mkdir -p %{buildroot}%{gemdir}
gem install --local --install-dir %{buildroot}%{gemdir} --force --rdoc %{SOURCE0}
%{__install} -d -m0755 %{buildroot}%{ruby_sitearch}
#move any .so files to the proper arch-specific dir
mv %{buildroot}%{geminstdir}/lib/http11.so %{buildroot}%{ruby_sitearch}
%{__chmod} 0755 %{buildroot}%{ruby_sitearch}/http11.so
rm -rf %{buildroot}%{geminstdir}/ext
mkdir -p %{buildroot}/%{_bindir}
mv %{buildroot}%{gemdir}/bin/* %{buildroot}/%{_bindir}
rmdir %{buildroot}%{gemdir}/bin
find %{buildroot}%{geminstdir}/bin -type f | xargs chmod a+x

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root)
%{_bindir}/mongrel_rails
#arch-specific libs here
%{ruby_sitearch}/http11.so
%{gemdir}/gems/%{gemname}-%{version}/
%doc %{gemdir}/doc/%{gemname}-%{version}
%doc %{geminstdir}/README
%{gemdir}/cache/%{gemname}-%{version}.gem
%{gemdir}/specifications/%{gemname}-%{version}.gemspec

%changelog
* Tue Mar  6 2007  <sseago@redhat.com> - 1.0.1-1
- Initial packaging.

