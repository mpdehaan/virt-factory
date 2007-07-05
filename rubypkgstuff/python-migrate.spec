
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?python_version: %define python_version %(%{__python} -c "from distutils.sysconfig import get_python_version; print get_python_version()")}

Summary: Database schema migration for SQLAlchemy
Name: python-migrate
Version: 0.2.2
Release: 1%{?dist}
Source0: migrate-%{version}.tar.gz
Patch0: remove-egg-deps.patch
License: MIT
Group: Applications/System
Requires: python >= 2.3
Requires: python-sqlalchemy >= 0.3
BuildRequires: python-setuptools
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch
Url: http://erosson.com/migrate/

%description

Inspired by Ruby on Rails' migrations, Migrate provides a way to deal with database schema changes in SQLAlchemy projects.
%prep
%setup -q -n migrate-%{version}
%patch0 -p1

%build
%{__python} setup.py build

%install
test "x$RPM_BUILD_ROOT" != "x" && rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --root=$RPM_BUILD_ROOT --single-version-externally-managed

%files
%{_bindir}/migrate
%dir %{python_sitelib}/migrate
%{python_sitelib}/migrate/*.py*
%dir %{python_sitelib}/migrate/changeset
%{python_sitelib}/migrate/changeset/*.py*
%dir %{python_sitelib}/migrate/changeset/databases
%{python_sitelib}/migrate/changeset/databases/*.py*
%dir %{python_sitelib}/migrate/versioning
%{python_sitelib}/migrate/versioning/*.py*
%dir %{python_sitelib}/migrate/versioning/base
%{python_sitelib}/migrate/versioning/base/*.py*
%dir %{python_sitelib}/migrate/versioning/script
%{python_sitelib}/migrate/versioning/script/*.py*
%dir %{python_sitelib}/migrate/versioning/templates
%{python_sitelib}/migrate/versioning/templates/*.py*
%dir %{python_sitelib}/migrate/versioning/templates/repository
%{python_sitelib}/migrate/versioning/templates/repository/*.py*
%dir %{python_sitelib}/migrate/versioning/templates/repository/default
%{python_sitelib}/migrate/versioning/templates/repository/default/*.py*
%{python_sitelib}/migrate/versioning/templates/repository/default/README
%{python_sitelib}/migrate/versioning/templates/repository/default/migrate.cfg
%dir %{python_sitelib}/migrate/versioning/templates/repository/default/versions
%{python_sitelib}/migrate/versioning/templates/repository/default/versions/*.py*
%dir %{python_sitelib}/migrate/versioning/templates/script
%{python_sitelib}/migrate/versioning/templates/script/*.py*
%{python_sitelib}/migrate-0.2.2-py%{python_version}.egg-info

%changelog
* Tue May 29 2007 Adrian Likins <alikins@redhat.com> - 0.2.2-1
- Initial RPM packaging
