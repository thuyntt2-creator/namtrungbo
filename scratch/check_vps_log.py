import sys, paramiko
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.82.27.107', username='root', password='T403kbek9E1r1nJy')
stdin, stdout, stderr = ssh.exec_command('grep -A 35 "2026-10-29" /root/auto_report/cron_target.log')
print(stdout.read().decode('utf-8'))
ssh.close()

