# Generated from mongrel-1.0.1.gem by gem2rpm -*- rpm-spec -*-
%define gemdir %(ruby -rubygems -e 'puts Gem::dir' 2>/dev/null)
%define gemname mongrel
%define geminstdir %{gemdir}/gems/%{gemname}-%{version}
%define ruby_sitearch %(ruby -rrbconfig -e "puts Config::CONFIG['sitearchdir']")

Summary: A small fast HTTP library and server
Name: rubygem-%{gemname}

Version: 1.0.1
Release: 3%{?dist}
Group: Development/Libraries
License: GPLv2+ or Ruby
URL: http://mongrel.rubyforge.org
Source0: http://gems.rubyforge.org/gems/%{gemname}-%{version}.gem
Patch0: remove-cgi-multipart-eof-fix-dep.patch
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
install -d -m0755 %{buildroot}%{ruby_sitearch}
mv %{buildroot}%{geminstdir}/lib/http11.so %{buildroot}%{ruby_sitearch}
strip %{buildroot}%{ruby_sitearch}/http11.so
chmod 0755 %{buildroot}%{ruby_sitearch}/http11.so
rm -rf %{buildroot}%{geminstdir}/ext
mkdir -p %{buildroot}/%{_bindir}
mv %{buildroot}%{gemdir}/bin/* %{buildroot}/%{_bindir}
rmdir %{buildroot}%{gemdir}/bin
find %{buildroot}%{geminstdir}/bin -type f | xargs chmod a+x
patch -p0 -d %{buildroot} < %{PATCH0}

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root)
%{_bindir}/mongrel_rails
%{ruby_sitearch}/http11.so
%{gemdir}/gems/%{gemname}-%{version}/
%doc %{gemdir}/doc/%{gemname}-%{version}
%doc %{geminstdir}/README
%{gemdir}/cache/%{gemname}-%{version}.gem
%{gemdir}/specifications/%{gemname}-%{version}.gemspec

%changelog
* Thu Aug 23 2007 Scott Seago <dlutter@redhat.com> - 1.0.1-3
- Removed requirement for rubygem(cgi_multipart_eof_fix)
- Patched source to work without cgi_multipart_eof_fix

* Fri Aug  3 2007 David Lutterkort <dlutter@redhat.com> - 1.0.1-2
- Updated to latest Fedora guidelines
- BR ruby-devel

* Tue Mar  6 2007  <sseago@redhat.com> - 1.0.1-1
- Initial packaging.

