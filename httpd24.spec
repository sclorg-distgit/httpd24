%global scl_name_base    httpd
%global scl_name_version 24
%global scl              %{scl_name_base}%{scl_name_version}
%scl_package %scl

# do not produce empty debuginfo package
%global debug_package %{nil}

%if 0%{?rhel} >= 7
%define use_system_apr 1
%else
%define use_system_apr 0
%endif

Summary:       Package that installs %scl
Name:          %scl_name
Version:       1.1
Release:       18%{?dist}
License:       GPLv2+
Group: Applications/File
Source0: README
Source1: LICENSE
Source2: README.7
Source3: macros-build

BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: scl-utils-build
# Temporary work-around
BuildRequires: iso-codes
BuildRequires: help2man

%if %{use_system_apr}
# Remove httpd24-apr and httpd24-apr-util from system.
# https://bugzilla.redhat.com/show_bug.cgi?id=1088194
Obsoletes: %{scl_prefix}apr
Obsoletes: %{scl_prefix}apr-devel
Obsoletes: %{scl_prefix}apr-util
Obsoletes: %{scl_prefix}apr-util-devel
Obsoletes: %{scl_prefix}apr-util-pgsql
Obsoletes: %{scl_prefix}apr-util-mysql
Obsoletes: %{scl_prefix}apr-util-sqlite
Obsoletes: %{scl_prefix}apr-util-odbc
Obsoletes: %{scl_prefix}apr-util-ldap
Obsoletes: %{scl_prefix}apr-util-openssl
Obsoletes: %{scl_prefix}apr-util-nss
%else
Requires: %{scl_prefix}apr
Requires: %{scl_prefix}apr-util
%endif
Requires: %{scl_prefix}httpd

%description
This is the main package for %scl Software Collection.

%package runtime
Summary:   Package that handles %scl Software Collection.
Requires:  scl-utils
Requires(post): policycoreutils-python

%description runtime
Package shipping essential scripts to work with %scl Software Collection.

%package build
Summary:   Package shipping basic build configuration
Requires:  scl-utils-build

%description build
Package shipping essential configuration macros to build %scl Software Collection.

%package scldevel
Summary:   Package shipping development files for %scl
Group:     Development/Languages

%description scldevel
Package shipping development files, especially usefull for development of
packages depending on %scl Software Collection.

%prep
%setup -c -T

# copy the license file so %%files section sees it
cp %{SOURCE0} .
cp %{SOURCE1} .
cp %{SOURCE2} .

expand_variables() {
    sed -i 's|%%{scl_name}|%{scl_name}|g' "$1"
    sed -i 's|%%{_scl_root}|%{_scl_root}|g' "$1"
    sed -i 's|%%{version}|%{version}|g' "$1"
%if 0%{?rhel} > 6
    sed -i 's|%%{start_command}|systemctl start %{scl_name}-httpd|g' "$1"
%else
    sed -i 's|%%{start_command}|service %{scl_name}-httpd start|g' "$1"
%endif
}

expand_variables README.7
expand_variables README

cat <<EOF | tee enable
export PATH=%{_bindir}:%{_sbindir}\${PATH:+:\${PATH}}
export MANPATH=%{_mandir}:\${MANPATH}
export PKG_CONFIG_PATH=%{_libdir}/pkgconfig\${PKG_CONFIG_PATH:+:\${PKG_CONFIG_PATH}}
export LIBRARY_PATH=%{_libdir}\${LIBRARY_PATH:+:\${LIBRARY_PATH}}
export LD_LIBRARY_PATH=%{_libdir}\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}
EOF

# generate rpm macros file for depended collections
cat << EOF | tee scldev
%%scl_%{scl_name_base}         %{scl}
%%scl_prefix_%{scl_name_base}  %{scl_prefix}
EOF

%build

%install
mkdir -p %{buildroot}%{_scl_scripts}/root
install -m 644 enable  %{buildroot}%{_scl_scripts}/enable
install -D -m 644 scldev %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel

# All directories used must be owned
mkdir -p %{buildroot}%{_mandir}/man{1,3,7,8}/
mkdir -p %{buildroot}%{_libdir}/pkgconfig/
mkdir -p %{buildroot}%{_datadir}/aclocal/
mkdir -p %{buildroot}%{_datadir}/zsh/
mkdir -p %{buildroot}%{_datadir}/licenses/

install -m 644 README.7 %{buildroot}%{_mandir}/man7/%{scl_name}.7

%scl_install

cat >> %{buildroot}%{_scl_scripts}/service-environment << EOF
# Services are started in a fresh environment without any influence of user's
# environment (like environment variable values). As a consequence,
# information of all enabled collections will be lost during service start up.
# If user needs to run a service under any software collection enabled, this
# collection has to be written into HTTPD24_HTTPD_SCLS_ENABLED variable in
# /opt/rh/sclname/service-environment.
HTTPD24_HTTPD_SCLS_ENABLED="%{scl}"
EOF

# Add the scl_package_override macro
sed -e 's/@SCL@/%{scl_name_base}%{scl_name_version}/g' %{SOURCE3} \
   >>%{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl}-config
cat  %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl}-config

%post runtime
# Simple copy of context from system root to DSC root.
# In case new version needs some additional rules or context definition,
# it needs to be solved.
# Unfortunately, semanage does not have -e option in RHEL-5, so we have to
# have its own policy for collection
semanage fcontext -a -e / %{_scl_root} >/dev/null 2>&1 || :
restorecon -R %{_scl_root} >/dev/null 2>&1 || :

%files

%files runtime
%defattr(-,root,root)
%doc README LICENSE
%scl_files
%dir %{_mandir}/man?
%dir %{_libdir}/pkgconfig
%dir %{_datadir}/aclocal
%dir %{_datadir}/licenses
%dir %{_datadir}/zsh
%{_mandir}/man7/%{scl_name}.*
%config(noreplace) %{_scl_scripts}/service-environment

%files build
%defattr(-,root,root)
%{_root_sysconfdir}/rpm/macros.%{scl}-config

%files scldevel
%defattr(-,root,root)
%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel

%changelog
* Tue Jun 06 2017 Luboš Uhliarik <luhliari@redhat.com> - 1.1-18
- rebuild
- Resolves: #1457316 - [RFE] please consider using scl_package_override

* Fri May 06 2016 Jan Kaluza <jkaluza@redhat.com> - 1.1-14
- Resolves:#1219112 - fix error in man page

* Fri May 06 2016 Jan Kaluza <jkaluza@redhat.com> - 1.1-13
- Resolves:#1219112 - fix nginx mentions in the man page

* Thu Apr 14 2016 Joe Orton <jorton@redhat.com> - 1.1-12
- own more directories (#1319968)

* Wed Feb 10 2016 Jan Kaluza <jkaluza@redhat.com> - 1.1-11
- bump the release to match the RHEL6 version of httpd24

* Wed Feb 10 2016 Jan Kaluza <jkaluza@redhat.com> - 1.1-7
- Obsolete all versions of httpd24-apr and httpd24-apr-util on RHEL7 (#1218271)
- Do not mention RHSCL version in README and man page (#1219112)
- Fix bad man page syntax (#1219511)

* Tue Feb 09 2016 Jan Kaluza <jkaluza@redhat.com> - 1.1-6
- use LD_LIBRARY_PATH in enable script

* Wed Jan 28 2015 Jan Kaluza <jkaluza@redhat.com> 1.1-5
- rebuild for rhscl-2.0

* Mon Mar 31 2014 Honza Horak <hhorak@redhat.com> - 1.1-4
- Fix path typo in README
  Related: #1061446

* Tue Mar 25 2014 Jan Kaluza <jkaluza@redhat.com> - 1.1-3
- own all directories needed by httpd24 SCL (#1079912)

* Tue Feb 25 2014 Jan Kaluza <jkaluza@redhat.com> - 1.1-2
- add scldevel subpackage (#1067434)

* Wed Feb 12 2014 Jan Kaluza <jkaluza@redhat.com> - 1.1-1
- add README and LICENSE (#1061446)

* Wed Jan 15 2014 Jan Kaluza <jkaluza@redhat.com> - 1.8
- add policycoreutils-python dependency (#1052933)

* Tue Nov 12 2013 Jan Kaluza <jkaluza@redhat.com> - 1.7
- add service-environment config file

* Fri Sep 20 2013 Jan Kaluza <jkaluza@redhat.com> - 1.6
- add prep section and cleanup spec file

* Fri Jul 26 2013 Jan Kaluza <jkaluza@redhat.com> - 1-5
- do not build httpd24 as noarch, fix export PATH

* Fri Jul 26 2013 Jan Kaluza <jkaluza@redhat.com> - 1-4
- add PKG_CONFIG_PATH to "enable" script

* Fri Apr 19 2013 Jan Kaluza <jkaluza@redhat.com> - 1-3
- handle selinux and manpath
- build with apr and apr-util from collection

* Tue Oct 02 2012 Jan Kaluza <jkaluza@redhat.com> - 1-2
- updated specfile according to latest guidelines
- require iso-codes

* Wed May 16 2012 Jan Kaluza <jkaluza@redhat.com> - 1-1
- initial packaging
