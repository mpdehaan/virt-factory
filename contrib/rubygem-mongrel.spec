# Generated from mongrel-1.0.1.gem by gem2rpm -*- rpm-spec -*-
%define gemdir %(ruby -rubygems -e 'puts Gem::dir' 2>/dev/null)
%define gemname mongrel
%define geminstdir %{gemdir}/gems/%{gemname}-%{version}
%define ruby_sitearch %(ruby -rrbconfig -e "puts Config::CONFIG['sitearchdir']")

Summary: A small fast HTTP library and server for Ruby apps
Name: rubygem-%{gemname}

Version: 1.0.1
Release: 5%{?dist}
Group: Development/Libraries
# The entire source code is (GPLv2+ or Ruby) except for the code in
# cgi_multipart_eof_fix-2.3.gem  which is AFL
License: (GPLv2+ or Ruby) and AFL
URL: http://mongrel.rubyforge.org
Source0: http://gems.rubyforge.org/gems/%{gemname}-%{version}.gem
Source1: http://gems.rubyforge.org/gems/cgi_multipart_eof_fix-2.3.gem
BuildRoot: %{_tmppath}/%{name}-%{version}-root-%(%{__id_u} -n)
Requires: rubygems
BuildRequires: ruby-devel
Requires: rubygem(daemons) >= 1.0.3
Requires: rubygem(fastthread) >= 0.6.2
Requires: rubygem(gem_plugin) >= 0.2.2
BuildRequires: rubygems
Provides: rubygem(%{gemname}) = %{version}

%description
A small fast HTTP library and server that runs Rails, Camping, Nitro and Iowa
apps.


%prep

%build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{gemdir}
gem install --local --install-dir %{buildroot}%{gemdir} \
            --force --rdoc %{SOURCE0}
gem install --local --install-dir %{buildroot}%{gemdir} \
            --force --rdoc %{SOURCE1}
install -d -m0755 %{buildroot}%{ruby_sitearch}
mv %{buildroot}%{geminstdir}/lib/http11.so %{buildroot}%{ruby_sitearch}
strip %{buildroot}%{ruby_sitearch}/http11.so
chmod 0755 %{buildroot}%{ruby_sitearch}/http11.so
rm -rf %{buildroot}%{geminstdir}/ext
mkdir -p %{buildroot}/%{_bindir}
mv %{buildroot}%{gemdir}/bin/* %{buildroot}/%{_bindir}
rmdir %{buildroot}%{gemdir}/bin
sed 's.#!/usr/local/bin/ruby.#!/usr/bin/env ruby.' -i %{buildroot}%{geminstdir}/examples/webrick_compare.rb
chmod a+x %{buildroot}%{geminstdir}/examples/webrick_compare.rb 
chmod a+x %{buildroot}%{geminstdir}/examples/camping/blog.rb 
chmod a+x %{buildroot}%{geminstdir}/examples/camping/tepee.rb
chmod a+x %{buildroot}%{gemdir}/gems/cgi_multipart_eof_fix-2.3/test/cgi_multipart_eof_fix_test.rb

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root)
%{_bindir}/mongrel_rails
%{ruby_sitearch}/http11.so
%dir %{geminstdir}
%doc %{gemdir}/doc/%{gemname}-%{version}
%{geminstdir}/bin/
%{geminstdir}/doc/
%{geminstdir}/examples/
%{geminstdir}/lib/
%{geminstdir}/Rakefile
%{geminstdir}/setup.rb
%{geminstdir}/test/
%{geminstdir}/tools/
%doc %{geminstdir}/README
%doc %{geminstdir}/LICENSE
%doc %{geminstdir}/COPYING
%{gemdir}/cache/%{gemname}-%{version}.gem
%{gemdir}/specifications/%{gemname}-%{version}.gemspec

%dir %{gemdir}/gems/cgi_multipart_eof_fix-2.3/
%{gemdir}/gems/cgi_multipart_eof_fix-2.3/lib/
%{gemdir}/gems/cgi_multipart_eof_fix-2.3/test/
%doc %{gemdir}/gems/cgi_multipart_eof_fix-2.3/CHANGELOG
%doc %{gemdir}/gems/cgi_multipart_eof_fix-2.3/LICENSE
%doc %{gemdir}/gems/cgi_multipart_eof_fix-2.3/Manifest
%doc %{gemdir}/gems/cgi_multipart_eof_fix-2.3/README
%doc %{gemdir}/gems/cgi_multipart_eof_fix-2.3/cgi_multipart_eof_fix.gemspec
%doc %{gemdir}/doc/cgi_multipart_eof_fix-2.3
%{gemdir}/cache/cgi_multipart_eof_fix-2.3.gem
%{gemdir}/specifications/cgi_multipart_eof_fix-2.3.gemspec

%changelog
* Mon Sep  1 2007 Scott Seago <sseago@redhat.com> - 1.0.1-5
- Include cgi multipart fix

* Fri Aug 24 2007 Scott Seago <sseago@redhat.com> - 1.0.1-4
- rpmlint fixes
- added Ruby >= 1.8.6 Requires

* Thu Aug 23 2007 Scott Seago <sseago@redhat.com> - 1.0.1-3
- Removed requirement for rubygem(cgi_multipart_eof_fix)
- Patched source to work without cgi_multipart_eof_fix

* Fri Aug  3 2007 David Lutterkort <dlutter@redhat.com> - 1.0.1-2
- Updated to latest Fedora guidelines
- BR ruby-devel

* Tue Mar  6 2007  <sseago@redhat.com> - 1.0.1-1
- Initial packaging.

