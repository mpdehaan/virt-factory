Name:           amqp
Version:        0.8
Release:        3rhm.1%{?dist}
Epoch:          0
Summary:        The AMQP specification

Group:          Development/Java
License:        AMQP
URL:            http://www.amqp.org
Source0:        %{name}.tar.gz
# mkdir amqp
# svn cat \
# http://svn.apache.org/repos/asf/incubator/qpid/trunk/qpid/specs/amqp.0-8.xml \
# > amqp/amqp.0-8.xml
# tar czf amqp.tar.gz amqp

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch

%description
The AMQP (advanced message queuing protocol) specification in XML format.

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d -m0755 $RPM_BUILD_ROOT%{_datadir}/%{name}
install -p -m0644 amqp*.xml $RPM_BUILD_ROOT%{_datadir}/%{name}

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{_datadir}/%{name}



%changelog
* Thu Mar 22 2007 Nuno Santos <nsantos@redhat.com> - 0.8-2rhm.1
- Comply with Fedora packaging guidelines

* Wed Dec 20 2006 Rafael Schloming <rafaels@redhat.com> - 0.8-2rhm
- Bumped the release.

* Wed Dec 20 2006 Rafael Schloming <rafaels@redhat.com> - 0.8-1
- Initial build.
