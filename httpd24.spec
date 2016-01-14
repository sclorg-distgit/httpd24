%global scl_name_base    httpd
%global scl_name_version 24
%global scl              %{scl_name_base}%{scl_name_version}
%scl_package %scl

# do not produce empty debuginfo package
%global debug_package %{nil}

%define use_system_apr 1

Summary:       Package that installs %scl
Name:          %scl_name
Version:       1.1
Release:       9%{?dist}
License:       GPLv2+
Group: Applications/File
Source0: README
Source1: LICENSE

BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: scl-utils-build
# Temporary work-around
BuildRequires: iso-codes
BuildRequires: help2man

%if ! %{use_system_apr}
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
# Remove httpd24-apr and httpd24-apr-util from system.
# https://bugzilla.redhat.com/show_bug.cgi?id=1088194
Obsoletes: %{scl_prefix}apr <= 1.5.1-1%{?dist}
Obsoletes: %{scl_prefix}apr-devel <= 1.5.1-1%{?dist}
Obsoletes: %{scl_prefix}apr-util <= 1.5.4-1%{?dist}
Obsoletes: %{scl_prefix}apr-util-devel <= 1.5.4-1%{?dist}
Obsoletes: %{scl_prefix}apr-util-pgsql <= 1.5.4-1%{?dist}
Obsoletes: %{scl_prefix}apr-util-mysql <= 1.5.4-1%{?dist}
Obsoletes: %{scl_prefix}apr-util-sqlite <= 1.5.4-1%{?dist}
Obsoletes: %{scl_prefix}apr-util-odbc <= 1.5.4-1%{?dist}
Obsoletes: %{scl_prefix}apr-util-ldap <= 1.5.4-1%{?dist}
Obsoletes: %{scl_prefix}apr-util-openssl <= 1.5.4-1%{?dist}
Obsoletes: %{scl_prefix}apr-util-nss <= 1.5.4-1%{?dist}

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

# This section generates README file from a template and creates man page
# from that file, expanding RPM macros in the template file.
cat >README <<'EOF'
%{expand:%(cat %{SOURCE0})}
EOF

# copy the license file so %%files section sees it
cp %{SOURCE1} .

# Not required for now
#export LIBRARY_PATH=%{_libdir}\${LIBRARY_PATH:+:\${LIBRARY_PATH}}
#export LD_LIBRARY_PATH=%{_libdir}\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}

cat <<EOF | tee enable
export PATH=%{_bindir}:%{_sbindir}\${PATH:+:\${PATH}}
export MANPATH=%{_mandir}:\${MANPATH}
export PKG_CONFIG_PATH=%{_libdir}/pkgconfig\${PKG_CONFIG_PATH:+:\${PKG_CONFIG_PATH}}
EOF

# generate rpm macros file for depended collections
cat << EOF | tee scldev
%%scl_%{scl_name_base}         %{scl}
%%scl_prefix_%{scl_name_base}  %{scl_prefix}
EOF

%build
# generate a helper script that will be used by help2man
cat >h2m_helper <<'EOF'
#!/bin/bash
[ "$1" == "--version" ] && echo "%{scl_name} %{version} Software Collection" || cat README
EOF
chmod a+x h2m_helper

# generate the man page
help2man -N --section 7 ./h2m_helper -o %{scl_name}.7


%install
mkdir -p %{buildroot}%{_scl_scripts}/root
install -m 644 enable  %{buildroot}%{_scl_scripts}/enable
install -D -m 644 scldev %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel

# install generated man page
mkdir -p %{buildroot}%{_mandir}/man1/
mkdir -p %{buildroot}%{_mandir}/man7/
mkdir -p %{buildroot}%{_mandir}/man8/
mkdir -p %{buildroot}%{_libdir}/pkgconfig/
mkdir -p %{buildroot}%{_datadir}/aclocal/
install -m 644 %{scl_name}.7 %{buildroot}%{_mandir}/man7/%{scl_name}.7

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

%post runtime
# Simple copy of context from system root to DSC root.
# In case new version needs some additional rules or context definition,
# it needs to be solved.
# Unfortunately, semanage does not have -e option in RHEL-5, so we have to
# have its own policy for collection
semanage fcontext -a -e / %{_scl_root} >/dev/null 2>&1 || :
restorecon -R %{_scl_root} >/dev/null 2>&1 || :
selinuxenabled && load_policy || :

%files

%files runtime
%defattr(-,root,root)
%doc README LICENSE
%scl_files
%dir %{_mandir}/man1
%dir %{_mandir}/man7
%dir %{_mandir}/man8
%dir %{_libdir}/pkgconfig
%dir %{_datadir}/aclocal
%{_mandir}/man7/%{scl_name}.*

%config(noreplace) %{_scl_scripts}/service-environment

%files build
%defattr(-,root,root)
%{_root_sysconfdir}/rpm/macros.%{scl}-config

%files scldevel
%defattr(-,root,root)
%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel

%changelog
* Tue Feb 03 2015 Jan Kaluza <jkaluza@redhat.com> - 1.1.9
- use httpd24-apr and httpd24-apr-util from system on RHEL7 (#1187646)

* Mon Feb 02 2015 Jan Kaluza <jkaluza@redhat.com> - 1.1.8
- use httpd24-apr and httpd24-apr-util even on RHEL7 (#1187646)

* Mon Jan 05 2015 Jan Kaluza <jkaluza@redhat.com> - 1.1-7
- obsolete httpd24-apr and http24-apr-util (#1088194)

* Mon Mar 31 2014 Honza Horak <hhorak@redhat.com> - 1.1-4
- Fix path typo in README
  Related: #1061446

* Tue Mar 25 2014 Jan Kaluza <jkaluza@redhat.com> - 1.1-3
- own all directories needed by httpd24 SCL (#1079912)

* Tue Feb 25 2014 Jan Kaluza <jkaluza@redhat.com> - 1.1-2
- add scldevel subpackage (#1067434)

* Wed Feb 12 2014 Jan Kaluza <jkaluza@redhat.com> - 1.1-1
- add README and LICENSE (#1061446)

* Mon Jan 20 2014 Jan Kaluza <jkaluza@redhat.com> - 1.10
- rebuild because of missing uucp user (#1054719)

* Wed Jan 15 2014 Jan Kaluza <jkaluza@redhat.com> - 1.9
- execute load_policy to load newly created SELinux policy (#1052935)

* Tue Nov 12 2013 Jan Kaluza <jkaluza@redhat.com> - 1.8
- add service-environment config file

* Wed Sep 25 2013 Jan Kaluza <jkaluza@redhat.com> - 1.7
- use system APR/APR-util

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
