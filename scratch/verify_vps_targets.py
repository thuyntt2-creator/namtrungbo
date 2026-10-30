import sys, paramiko
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.82.27.107', username='root', password='T403kbek9E1r1nJy')

stdin, stdout, stderr = ssh.exec_command('cat /root/auto_report/alert_targets.json')
print("Current /root/auto_report/alert_targets.json on VPS:")
print(stdout.read().decode('utf-8'))

ssh.close()

