import sys, paramiko
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.82.27.107', username='root', password='T403kbek9E1r1nJy')

stdin, stdout, stderr = ssh.exec_command('grep -A 30 "def load_alert_hubs_map" /root/auto_report/report_nangsuat_direct.py')
print(stdout.read().decode('utf-8'))
ssh.close()

