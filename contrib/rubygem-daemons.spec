# Generated from daemons-1.0.5.gem by gem2spec -*- rpm-spec -*-
%define gemdir %(ruby -rubygems -e 'puts Gem::dir' 2>/dev/null)
%define gemname daemons
%define geminstdir %{gemdir}/gems/%{gemname}-%{version}

Summary: A toolkit to create and control daemons in different ways
Name: rubygem-%{gemname}

Version: 1.0.5
Release: 1%{?dist}
Group: Development/Libraries
License: Ruby License
URL: http://daemons.rubyforge.org
Source0: http://rubyforge.org/frs/download.php/17811/%{gemname}-%{version}.gem
Source1: %{name}.spec.in
BuildRoot: %{_tmppath}/%{name}-%{version}-root-%(%{__id_u} -n)
Requires: rubygems
BuildRequires: rubygems
BuildArch: noarch
Provides: rubygem(daemons) = %{version}

%description
Daemons provides an easy way to wrap existing ruby scripts (for example a self-written server)  to be run as a daemon and to be controlled by simple start/stop/restart commands.  You can also call blocks as daemons and control them from the parent or just daemonize the current process.  Besides this basic functionality, daemons offers many advanced features like exception  backtracing and logging (in case your ruby script crashes) and monitoring and automatic restarting of your processes if they crash.

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
%doc %{geminstdir}/README
%doc %{geminstdir}/Releases
%doc %{geminstdir}/TODO
%{gemdir}/cache/%{gemname}-%{version}.gem
%{gemdir}/specifications/%{gemname}-%{version}.gemspec

%changelog
* Tue Mar  6 2007  <sseago@redhat.com> - 1.0.5-1
- Initial packaging.
