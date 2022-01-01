# code=ascii

import os
from fabric.contrib.files import sed, append
from fabric.api import env, local, run
from dotenv import load_dotenv

# use ssh .config
if env.ssh_config_path and os.path.isfile(os.path.expanduser(env.ssh_config_path)):
    env.use_ssh_config = True

# .env init
load_dotenv()
env.admin_options = '-m -G sudo -s /bin/bash -p \'{}\''.format(os.getenv('admin_pwd'))
env.app_options = '-m -s /bin/bash -p \'{}\''.format(os.getenv('app_pwd'))
env.app_user_keys = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    'ssh-keys',
    env.host_string+'_sshkey')
env.admin_user_keys = '/home/{}/.ssh/id_rsa'.format(env.admin_user)

def deploy():
    config_user(os.getenv('admin_user'), os.getenv('admin_group'), os.getenv('admin_name'), env.admin_options)
    config_user(os.getenv('app_user'), os.getenv('app_group'), os.getenv('app_name'), env.app_options)
    local('ssh-keygen -t rsa -b 4096 -f {0} -N ""'.format(env.app_user_keys))
    upload_keys(os.getenv('admin_user'), os.getenv('admin_group'), env.admin_user_keys)
    upload_keys(os.getenv('app_user'), os.getenv('app_group'), env.app_user_keys)
    config_ssh()
    run('systemctl reload sshd')
    upgrade_packages()
    config_ufw()
    config_fail2ban()
    run('reboot --reboot')

def config_user(user, group, name, options):
    run('groupadd -f {}'.format(group))
    run('useradd -c "{}" -g {} {} {}'.format(name, group, options, user))
    run('mkdir /home/{}/.ssh'.format(user))
    run('chown -R {} /home/{}/.ssh'.format(user, user))
    run('chgrp -R {} /home/{}/.ssh'.format(group, user))

def config_ssh():
    sed('/etc/ssh/sshd_config', '^UsePAM yes', 'UsePAM no')
    sed('/etc/ssh/sshd_config', '^PermitRootLogin yes', 'PermitRootLogin no')
    sed('/etc/ssh/sshd_config', '^#PasswordAuthentication yes', 'PasswordAuthentication no')
    append('/etc/ssh/sshd_config','AllowUsers {} {}'.format(os.getenv('admin_user'), os.getenv('app_user')))
    
def upload_keys(user, group, user_keys):
    local('scp {}.pub {}:/home/{}/.ssh/authorized_keys'.format(user_keys, env.host_string, user))
    run('chown -R {} /home/{}/.ssh'.format(user, user))
    run('chgrp -R {} /home/{}/.ssh'.format(group, user))

def upgrade_packages():
    run('apt update')
    run('apt -y upgrade')

def config_ufw():
    run('apt -y install ufw')
    sed('/etc/default/ufw', 'IPV6=no', 'IPV6=yes')
    append('/etc/default/ufw', 'IPV6=yes')
    run('ufw default allow outgoing')
    run('ufw default deny incoming')
    run('ufw allow ssh')
    run('ufw enable')

def config_fail2ban():
    run('apt -y install fail2ban')
    run('cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local')
    sed('/etc/fail2ban/jail.local', '^#ignoreip = 127.0.0.1/8 ::1', 'ignoreip = 127.0.0.1/8 ::1 {}'.format(os.getenv('admin_ips')))
    sed('/etc/fail2ban/jail.local', '^destemail.*', 'destemail = {}'.format(os.getenv('admin_mail')))
    sed('/etc/fail2ban/jail.local', '^sender.*', 'sender = {}'.format(os.getenv('admin_sender')))
    run('systemctl restart fail2ban')

# eof
