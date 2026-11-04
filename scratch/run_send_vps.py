import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.82.27.107', username='root', password='T403kbek9E1r1nJy', timeout=15)

print("🚀 Đang chạy gửi cảnh báo thật sự tới các AM...")
stdin, stdout, stderr = ssh.exec_command('cd /root/auto-report && python3 gui_canh_bao_goidau_cod.py >> canh_bao_cod_8h45_$(date +%Y%m%d).log 2>&1 && tail -n 30 canh_bao_cod_8h45_$(date +%Y%m%d).log')
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')

print("OUT:\n", out)
if err:
    print("ERR:\n", err)

ssh.close()

