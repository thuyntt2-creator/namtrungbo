import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.82.27.107', username='root', password='T403kbek9E1r1nJy')

# SFTP upload
sftp = ssh.open_sftp()
sftp.put('calculate_daily_targets.py', '/root/auto_report/calculate_daily_targets.py')
sftp.close()
print("Uploaded calculate_daily_targets.py to VPS successfully.")

# Run on VPS
stdin, stdout, stderr = ssh.exec_command('cd /root/auto_report && /usr/bin/python3 calculate_daily_targets.py')
print(stdout.read().decode('utf-8'))
err = stderr.read().decode('utf-8')
if err:
    print("Stderr:", err)

# Check VPS alert_targets.json
stdin, stdout, stderr = ssh.exec_command('cat /root/auto_report/alert_targets.json')
print("\nNew /root/auto_report/alert_targets.json:")
print(stdout.read().decode('utf-8'))

ssh.close()

