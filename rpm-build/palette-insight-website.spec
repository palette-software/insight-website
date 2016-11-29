%define serviceuser insight
%define servicehome /etc/palette-insight-website


# Disable the stupid stuff rpm distros include in the build process by default:
#   Disable any prep shell actions. replace them with simply 'true'
%define __spec_prep_post true
%define __spec_prep_pre true
#   Disable any build shell actions. replace them with simply 'true'
%define __spec_build_post true
%define __spec_build_pre true
#   Disable any install shell actions. replace them with simply 'true'
%define __spec_install_post true
%define __spec_install_pre true
#   Disable any clean shell actions. replace them with simply 'true'
%define __spec_clean_post true
%define __spec_clean_pre true
# Disable checking for unpackaged files ?
#%undefine __check_files

# Use md5 file digest method.
# The first macro is the one used in RPM v4.9.1.1
%define _binary_filedigest_algorithm 1
# This is the macro I find on OSX when Homebrew provides rpmbuild (rpm v5.4.14)
%define _build_binary_file_digest_algo 1

# Use bzip2 payload compression
%define _binary_payload w9.bzdio


Name: palette-insight-website
Version: %version
Epoch: 400
Release: %buildrelease
Summary: Palette Insight Website
AutoReqProv: no
# Seems specifying BuildRoot is required on older rpmbuild (like on CentOS 5)
# fpm passes '--define buildroot ...' on the commandline, so just reuse that.
#BuildRoot: %buildroot
# Add prefix, must not end with / except for root (/)

Prefix: /

Group: default
License: commercial
Vendor: palette-software.net
URL: http://www.palette-software.com
Packager: Palette Developers <developers@palette-software.com>

# Add the user for the service & setup SELinux
# ============================================

#Requires(pre): /usr/sbin/useradd, /usr/bin/getent

Requires: nginx
Requires: system-config-firewall-base

# Travis will fill in the exact version during deploy
Requires: palette-supervisor
Requires: palette-insight-toolkit

%pre
# noop

%post
# palette-insight-toolkit installs python3
pip3 install -r /opt/palette-insight-website/requirements.txt

# Enable the http/s services on the firewall
lokkit --service=http
lokkit --service=https

# Palette Insight Website uses the root so default must be disabled
mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.original
# Reload the nginx configuration so it forwards the http root to the palette-insight-website
service nginx reload
if [ $? -ne 0 ]; then
    service nginx restart
fi

# Make sure that the old version of insight website is no longer registered
rm -rf /opt/insight-services-webui/
rm -rf /var/log/insight-services
rm -rf /etc/insight-services
rm -f /etc/supervisord.d/insight-services-webui.ini

# Detect new service
supervisorctl reread
supervisorctl update

# (Re)start palette-insight-website via supervisord
supervisorctl restart palette-insight-website

%description
Palette Insight Website
- Status and Control

%prep
# noop

%build
# noop

%install
# noop

%clean
# noop

%files
%defattr(-,insight,insight,-)

# Reject config files already listed or parent directories, then prefix files
# with "/", then make sure paths with spaces are quoted.
# /usr/local/bin/palette-insight-server
/opt/palette-insight-website
%dir /var/log/palette-insight-website
%attr(664, root root) /etc/supervisord.d/palette-insight-website.ini
%attr(664, root root) /etc/nginx/conf.d/palette-insight-website.conf

%attr(755, root root) /usr/local/bin/insight-services
%dir /etc/palette-insight-website

# config files can be defined according to this
# http://www-uxsup.csx.cam.ac.uk/~jw35/docs/rpm_config.html
#%%config /etc/palette-insight-server/server.config

%changelog
