#!/bin/sh

sudo yum -y groupinstall "Development Tools"
sudo yum install memcached python-memcached  -y
sudo /etc/init.d/memcached start

cd ..
virtualenv mics_env
source mics_env/bin/activate
cd -
pip install -r pip-requires.txt
cp mics/snap-ci/snap-settings.py mics/localsettings.py
./manage.py syncdb --noinput
./manage.py migrate