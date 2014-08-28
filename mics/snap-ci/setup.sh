#!/bin/sh
sudo yum remove -y libmemcached libmemcached-devel
sudo wget http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
sudo wget http://rpms.famillecollet.com/enterprise/remi-release-6.rpm
sudo rpm -Uvh remi-release-6*.rpm epel-release-6*.rpm
sudo yum --enablerepo=remi install -y libmemcached-last libmemcached-last-devel

cd ..
virtualenv mics_env
source mics_env/bin/activate
cd -
pip install -r pip-requires.txt
pip install coveralls
cp mics/snap-ci/snap-settings.py mics/localsettings.py
./manage.py syncdb --noinput
./manage.py migrate