#!/bin/sh

sudo yum -y groupinstall "Development Tools"
sudo yum install memcached python-memcached  -y
wget https://launchpad.net/libmemcached/1.0/1.0.18/+download/libmemcached-1.0.18.tar.gz
tar -xvf libmemcached-1.0.18.tar.gz
cd libmemcached-1.0.18
sudo ./configure
sudo make
sudo make install

cd ..

sudo /etc/init.d/memcached start

cd ..
virtualenv mics_env
source mics_env/bin/activate
cd -
pip install -r pip-requires.txt
cp mics/snap-ci/snap-settings.py mics/localsettings.py
./manage.py syncdb --noinput
./manage.py migrate