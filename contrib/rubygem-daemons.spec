# Generated from daemons-1.0.5.gem by gem2rpm -*- rpm-spec -*-
%define gemdir %(ruby -rubygems -e 'puts Gem::dir' 2>/dev/null)
%define gemname daemons
%define geminstdir %{gemdir}/gems/%{gemname}-%{version}

Summary: A toolkit to create and control daemons in different ways
Name: rubygem-%{gemname}

Version: 1.0.7
Release: 2%{?dist}
Group: Development/Languages
# The entire source code is MIT except daemonize.rb (GPLv2+ or Ruby)
License: MIT and (GPLv2+ or Ruby)
URL: http://daemons.rubyforge.org
Source0: http://gems.rubyforge.org/gems/%{gemname}-%{version}.gem
BuildRoot: %{_tmppath}/%{name}-%{version}-root-%(%{__id_u} -n)
Requires: rubygems
BuildRequires: rubygems
BuildArch: noarch
Provides: rubygem(%{gemname}) = %{version}

%description
Daemons provides an easy way to wrap existing ruby scripts (for example a
self-written server)  to be run as a daemon and to be controlled by simple
start/stop/restart commands.  You can also call blocks as daemons and control
them from the parent or just daemonize the current process.  Besides this
basic functionality, daemons offers many advanced features like exception 
backtracing and logging (in case your ruby script crashes) and monitoring and
automatic restarting of your processes if they crash.


%prep

%build

%install
%{__rm} -rf %{buildroot}
mkdir -p %{buildroot}%{gemdir}
gem install --local --install-dir %{buildroot}%{gemdir} \
            --force --rdoc %{SOURCE0}
chmod a+x %{buildroot}%{geminstdir}/examples/run/myserver.rb

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root)
%dir %{geminstdir}
%doc %{gemdir}/doc/%{gemname}-%{version}
%{geminstdir}/examples/
%{geminstdir}/lib/
%{geminstdir}/Rakefile
%{geminstdir}/setup.rb
%{geminstdir}/test/
%doc %{geminstdir}/LICENSE
%doc %{geminstdir}/README
%doc %{geminstdir}/Releases
%doc %{geminstdir}/TODO
%{gemdir}/cache/%{gemname}-%{version}.gem
%{gemdir}/specifications/%{gemname}-%{version}.gemspec

%changelog
* Fri Aug 24 2007  <sseago@redhat.com> - 1.0.7-2
- rpmlint fixes

* Thu Aug 23 2007  <sseago@redhat.com> - 1.0.7-1
- Updated gem to Version 1.0.7

* Tue Mar  6 2007  <sseago@redhat.com> - 1.0.5-1
- Initial packaging.
