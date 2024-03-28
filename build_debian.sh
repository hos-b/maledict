#!/bin/sh

set -e
set -x

rm -rf debian/
cp -r debian.template debian

# this requires dh-virtualenv [github/spotify/dh-virtualenv]
dpkg-buildpackage -us -uc -b

mkdir -p build/debian
mv ../maledict*.changes build/debian
mv ../maledict*.buildinfo build/debian
mv ../maledict*.deb build/debian
mv ../maledict*.ddeb build/debian