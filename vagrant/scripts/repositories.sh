#!/bin/sh

# Install the EPEL repository
yum install -y epel-release
rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6

# Install the ELGIS repository
rpm -Uvh --replacepkgs http://elgis.argeo.org/repos/6/elgis-release-6-6_0.noarch.rpm
rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-ELGIS

# Install and enable the EOX repository
rpm -Uvh --replacepkgs http://yum.packages.eox.at/el/eox-release-6-2.noarch.rpm
rpm --import /etc/pki/rpm-gpg/eox-package-maintainers.gpg
sed -e 's/^enabled=0/enabled=1/' -i /etc/yum.repos.d/eox-testing.repo

# Ignore TU Vienna CentOS mirror
sed -e 's/^#exclude=.*/exclude=gd.tuwien.ac.at/' /etc/yum/pluginconf.d/fastestmirror.conf > /etc/yum/pluginconf.d/fastestmirror.conf

# Set includepkgs in EOX Stable
if ! grep -Fxq "includepkgs=gdal-eox-libtiff4 gdal-eox-libtiff4-python gdal-eox-libtiff4-libs gdal-eox-libtiff4-devel gdal-eox-libtiff4-java gdal-eox-driver-openjpeg2 openjpeg2 EOxServer mapserver mapserver-python mapcache libxml2 libxml2-python libxerces-c-3_1 libgeotiff-libtiff4" /etc/yum.repos.d/eox.repo ; then
    sed -e 's/^\[eox\]$/&\nincludepkgs=gdal-eox-libtiff4 gdal-eox-libtiff4-python gdal-eox-libtiff4-libs gdal-eox-libtiff4-devel gdal-eox-libtiff4-java gdal-eox-driver-openjpeg2 openjpeg2 EOxServer mapserver mapserver-python mapcache libxml2 libxml2-python libxerces-c-3_1 libgeotiff-libtiff4/' -i /etc/yum.repos.d/eox.repo
fi
if ! grep -Fxq "includepkgs=ngEO_Browse_Server" /etc/yum.repos.d/eox.repo ; then
    sed -e 's/^\[eox-noarch\]$/&\nincludepkgs=ngEO_Browse_Server/' -i /etc/yum.repos.d/eox.repo
fi
# Set includepkgs in EOX Testing
if ! grep -Fxq "includepkgs=EOxServer mapcache" /etc/yum.repos.d/eox-testing.repo ; then
    sed -e 's/^\[eox-testing\]$/&\nincludepkgs=EOxServer mapcache/' -i /etc/yum.repos.d/eox-testing.repo
fi
if ! grep -Fxq "includepkgs=ngEO_Browse_Server" /etc/yum.repos.d/eox-testing.repo ; then
    sed -e 's/^\[eox-testing-noarch\]$/&\nincludepkgs=ngEO_Browse_Server/' -i /etc/yum.repos.d/eox-testing.repo
fi

# Set exclude in CentOS-Base
if ! grep -Fxq "exclude=libxml2 libxml2-python" /etc/yum.repos.d/CentOS-Base.repo ; then
    sed -e 's/^\[base\]$/&\nexclude=libxml2 libxml2-python libxerces-c-3_1/' -i /etc/yum.repos.d/CentOS-Base.repo
    sed -e 's/^\[updates\]$/&\nexclude=libxml2 libxml2-python libxerces-c-3_1/' -i /etc/yum.repos.d/CentOS-Base.repo
fi

# Install Continuous Release (CR) repository
yum install -y centos-release-cr
