import sys, paramiko
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.82.27.107', username='root', password='T403kbek9E1r1nJy')

# SFTP upload calculate_daily_targets.py
sftp = ssh.open_sftp()
sftp.put('calculate_daily_targets.py', '/root/auto_report/calculate_daily_targets.py')
print("Uploaded calculate_daily_targets.py to VPS.")

# In run_auto_nangsuat.sh, call calculate_daily_targets.py --no-send --no-chot so it doesn't overwrite 9h locked chot so
run_sh_content = """#!/bin/bash
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
cd /root/auto_report

echo "==================================================" >> /root/auto_report/cron_nangsuat.log
echo "🚀 [$(date '+%Y-%m-%d %H:%M:%S')] Bắt đầu chạy tự động Báo cáo Năng Suất NVPTT (Group Thật)..." >> /root/auto_report/cron_nangsuat.log

# Đồng bộ Target thoát bể từ tab hàng về đã chốt sổ lúc 9h sáng
/usr/bin/python3 calculate_daily_targets.py --no-send --no-chot >> /root/auto_report/cron_nangsuat.log 2>&1

/usr/bin/python3 report_nangsuat_direct.py --real >> /root/auto_report/cron_nangsuat.log 2>&1

echo "✅ [$(date '+%Y-%m-%d %H:%M:%S')] Hoàn tất chu trình báo cáo năng suất!" >> /root/auto_report/cron_nangsuat.log
"""

with sftp.open('/root/auto_report/run_auto_nangsuat.sh', 'w') as f:
    f.write(run_sh_content)
sftp.chmod('/root/auto_report/run_auto_nangsuat.sh', 0o755)
sftp.close()
print("Updated /root/auto_report/run_auto_nangsuat.sh on VPS.")

# Test run with --no-send on VPS
stdin, stdout, stderr = ssh.exec_command('cd /root/auto_report && /usr/bin/python3 calculate_daily_targets.py --no-send --no-chot')
print(stdout.read().decode('utf-8'))

ssh.close()

