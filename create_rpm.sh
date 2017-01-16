#!/bin/bash

# Stop on first error
set -e

PACKAGEVERSION=${PACKAGEVERSION:-$TRAVIS_BUILD_NUMBER}
export PACKAGEVERSION

if [ -z "$VERSION" ]; then
    echo "VERSION is missing"
    exit 1
fi

if [ -z "$PACKAGEVERSION" ]; then
    echo "PACKAGEVERSION is missing"
    exit 1
fi

# Prepare for rpm-build
mkdir -p rpm-build
pushd rpm-build
mkdir -p _build

# Create directories
mkdir -p opt/palette-insight-website
mkdir -p var/log/palette-insight-website
mkdir -p etc/supervisord.d
mkdir -p etc/nginx/conf.d
mkdir -p usr/local/bin/
mkdir -p etc/palette-insight-website

# Copy the package contents
cp ../insight-services.sh usr/local/bin/insight-services
cp ../nginx.site.conf etc/nginx/conf.d/palette-insight-website.conf
cp ../supervisor.conf etc/supervisord.d/palette-insight-website.ini
cp ../server.py opt/palette-insight-website
cp ../agent_installer.py opt/palette-insight-website
cp ../requirements.txt opt/palette-insight-website
cp -R ../static opt/palette-insight-website
cp -R ../templates opt/palette-insight-website

echo "BUILDING VERSION:v$VERSION"

# Build rpm package
rpmbuild -bb --buildroot $(pwd) --define "version $VERSION" --define "buildrelease $PACKAGEVERSION" --define "_rpmdir $(pwd)/_build" palette-insight-website.spec

popd
