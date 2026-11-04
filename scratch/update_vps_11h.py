# -*- coding: utf-8 -*-
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.82.27.107', username='root', password='T403kbek9E1r1nJy')

script_content = """#!/bin/bash
export TZ="Asia/Ho_Chi_Minh"
export PYTHONIOENCODING="utf-8"
cd /root/auto-report
/usr/bin/python3 push_don_tts_am.py --send >> /root/auto-report/canh_bao_qua_han_11h_$(date +%Y%m%d).log 2>&1
"""

sftp = ssh.open_sftp()
with sftp.open('/root/auto-report/run_canh_bao_shopee_11h00.sh', 'w') as f:
    f.write(script_content)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('chmod +x /root/auto-report/run_canh_bao_shopee_11h00.sh && cat /root/auto-report/run_canh_bao_shopee_11h00.sh')
print(stdout.read().decode('utf-8'))
ssh.close()

