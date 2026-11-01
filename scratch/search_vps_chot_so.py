import sys, paramiko
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.82.27.107', username='root', password='T403kbek9E1r1nJy')

stdin, stdout, stderr = ssh.exec_command('grep -rn "Hàng ca 1 + Hàng tồn" /root/auto_report/ /root/auto-report/ 2>/dev/null')
print(stdout.read().decode('utf-8'))

stdin, stdout, stderr = ssh.exec_command('grep -A 10 "2026-10-28 09:00:02" /root/auto_report/cron_target.log')
print("\nLog on 28/10:")
print(stdout.read().decode('utf-8'))

ssh.close()

