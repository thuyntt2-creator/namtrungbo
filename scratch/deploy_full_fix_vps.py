import sys, paramiko
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.82.27.107', username='root', password='T403kbek9E1r1nJy')

# 1. SFTP upload calculate_daily_targets.py
sftp = ssh.open_sftp()
sftp.put('calculate_daily_targets.py', '/root/auto_report/calculate_daily_targets.py')
print("Uploaded calculate_daily_targets.py to VPS.")

# 2. Update run_auto_nangsuat.sh
run_sh_content = """#!/bin/bash
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
cd /root/auto_report

echo "==================================================" >> /root/auto_report/cron_nangsuat.log
echo "🚀 [$(date '+%Y-%m-%d %H:%M:%S')] Bắt đầu chạy tự động Báo cáo Năng Suất NVPTT (Group Thật)..." >> /root/auto_report/cron_nangsuat.log

# Tự động cập nhật Target thoát bể mới nhất từ tab hàng về trước mỗi ca chạy báo cáo
/usr/bin/python3 calculate_daily_targets.py --no-send >> /root/auto_report/cron_nangsuat.log 2>&1

/usr/bin/python3 report_nangsuat_direct.py --real >> /root/auto_report/cron_nangsuat.log 2>&1

echo "✅ [$(date '+%Y-%m-%d %H:%M:%S')] Hoàn tất chu trình báo cáo năng suất!" >> /root/auto_report/cron_nangsuat.log
"""

with sftp.open('/root/auto_report/run_auto_nangsuat.sh', 'w') as f:
    f.write(run_sh_content)
sftp.chmod('/root/auto_report/run_auto_nangsuat.sh', 0o755)
sftp.close()
print("Updated /root/auto_report/run_auto_nangsuat.sh on VPS.")

# 3. Test running calculate_daily_targets.py --no-send
stdin, stdout, stderr = ssh.exec_command('cd /root/auto_report && /usr/bin/python3 calculate_daily_targets.py --no-send')
print("Output:", stdout.read().decode('utf-8'))
err = stderr.read().decode('utf-8')
if err:
    print("Stderr:", err)

# 4. Check alert_targets.json
stdin, stdout, stderr = ssh.exec_command('cat /root/auto_report/alert_targets.json')
print("\nFinal alert_targets.json on VPS:")
print(stdout.read().decode('utf-8'))

ssh.close()

