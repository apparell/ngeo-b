#!/bin/sh -e

# Adjust document root in /etc/httpd/conf/httpd.conf
sed -e 's/^DocumentRoot "\/var\/www\/html"$/DocumentRoot "\/var\/ngeob_autotest"/' -i /etc/httpd/conf/httpd.conf
sed -e 's/^<Directory "\/var\/www\/html">$/<Directory "\/var\/ngeob_autotest">/' -i /etc/httpd/conf/httpd.conf

# Adjust server name in /etc/httpd/conf/httpd.conf
sed -e 's/^#ServerName www.example.com:80$/ServerName ngeob-vagrant/' -i /etc/httpd/conf/httpd.conf

# Adjust user and group in /etc/httpd/conf/httpd.conf
sed -e 's/^User apache$/User vagrant/' -i /etc/httpd/conf/httpd.conf
sed -e 's/^Group apache$/Group vagrant/' -i /etc/httpd/conf/httpd.conf

# Adjust timeout in /etc/httpd/conf/httpd.conf
sed -e 's/^Timeout .*$/Timeout 1800/' -i /etc/httpd/conf/httpd.conf

# Adjust owner of httpd run directory to the same user
chown -f vagrant /var/run/httpd

# Turn off some caching to resolve issues with files from shares
sed -e 's/^#EnableMMAP off$/EnableMMAP off/' -i /etc/httpd/conf/httpd.conf
sed -e 's/^#EnableSendfile off$/EnableSendfile off/' -i /etc/httpd/conf/httpd.conf

# Permanently start memcached, prior to apache
chkconfig memcached on
service memcached restart

# Permanently start Apache
chkconfig httpd on
# Reload Apache
service httpd restart

# Restart Apache after boot hopefully after all shares are available.
if ! grep -Fxq "service httpd restart" /etc/rc.d/rc.local ; then
    cat << EOF >> /etc/rc.d/rc.local

# Restart Apache after boot hopefully after all shares are available.
sleep 15
service httpd restart
EOF
fi

chown vagrant:vagrant /var/run/httpd/
