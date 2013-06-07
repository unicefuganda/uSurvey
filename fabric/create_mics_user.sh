 #!/bin/bash
useradd -m mics
adduser mics sudo
usermod -s /bin/bash mics
echo 'mics ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers
echo "Please add your ssh keys to authorized_keys file"
echo "Also add your github rsa key"