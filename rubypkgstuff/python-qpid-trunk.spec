Name:           python-qpid
Version:        0.1
Release:        2_SNAPSHOT_TRUNK
Summary:        Python language client for AMQP

Group:          Development/Python
License:        Apache Software License
URL:            http://incubator.apache.org/qpid
Source0:        %{name}.tar.gz
# svn export http://svn.apache.org/repos/asf/incubator/qpid/trunk/qpid/python \
#  python-qpid
# tar czf python-qpid.tar.gz python-qpid
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch

BuildRequires:  python
BuildRequires:  python-devel

Requires:       python
Requires:       amqp

%description
The Apache Qpid project's Python language client for AMQP.

%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

%prep
%setup -q -n %{name}
# to silence warnings:
sed -e 1d -e 2d -i setup.py
sed -e 1d -e 2d -i qpid/codec.py
#sed -e 1d -e 2d -i qpid/reference.py
chmod 0644 LICENSE.txt
echo "\n" > cpp_failing_0-8.txt

%build
#empty

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT%{python_sitelib}/qpid
install -d $RPM_BUILD_ROOT%{python_sitelib}/mllib
#install -d $RPM_BUILD_ROOT%{python_sitelib}/qpid/tests_0-8
#install -d $RPM_BUILD_ROOT%{python_sitelib}/qpid/tests_0-9
install -d $RPM_BUILD_ROOT%{python_sitelib}/qpid/doc
install -pm 0644 *.* qpid/* $RPM_BUILD_ROOT%{python_sitelib}/qpid
install -pm 0644 mllib/* $RPM_BUILD_ROOT%{python_sitelib}/mllib
#install -pm 0644 tests_0-8/*.* $RPM_BUILD_ROOT%{python_sitelib}/qpid/tests_0-8
#install -pm 0644 tests_0-9/*.* $RPM_BUILD_ROOT%{python_sitelib}/qpid/tests_0-9
install -pm 0644 doc/*.* $RPM_BUILD_ROOT%{python_sitelib}/qpid/doc

%clean
rm -rf $RPM_BUILD_ROOT

%files 
%defattr(-,root,root,-)
%{python_sitelib}/qpid/
%{python_sitelib}/mllib/
%doc LICENSE.txt NOTICE.txt README.txt doc/test-requirements.txt

%changelog
* Thu Mar 22 2007 Rafael Schloming <rafaels@redhat.com> - 0.1-1
- Initial build.
- Comply with Fedora packaging guidelines
