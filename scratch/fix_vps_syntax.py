import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.82.27.107', username='root', password='T403kbek9E1r1nJy', timeout=15)

# Fix missing comma on line 68
sftp = ssh.open_sftp()
with sftp.open('/root/auto-report/gui_canh_bao_goidau_cod.py', 'r') as f:
    content = f.read().decode('utf-8')

old_str = '"Phan Nguyễn Yến Nhi": "2105595062412402688"\n    "Trần Nguyễn Huyền Trang"'
new_str = '"Phan Nguyễn Yến Nhi": "2105595062412402688",\n    "Trần Nguyễn Huyền Trang"'

if old_str in content:
    content = content.replace(old_str, new_str)
    with sftp.open('/root/auto-report/gui_canh_bao_goidau_cod.py', 'w') as f:
        f.write(content.encode('utf-8'))
    print("Fixed via SFTP!")
else:
    print("Pattern not found, checking line by line...")
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '2105595062412402688' in line and not line.strip().endswith(','):
            lines[i] = line + ','
            print(f"Fixed line {i+1}: {lines[i]}")
    content = '\n'.join(lines)
    with sftp.open('/root/auto-report/gui_canh_bao_goidau_cod.py', 'w') as f:
        f.write(content.encode('utf-8'))

sftp.close()

# Test compilation
stdin, stdout, stderr = ssh.exec_command('python3 -m py_compile /root/auto-report/gui_canh_bao_goidau_cod.py')
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("COMPILE STDOUT:", out)
print("COMPILE STDERR:", err)

# Check dry run
print("--- TESTING DRY RUN ---")
stdin, stdout, stderr = ssh.exec_command('cd /root/auto-report && python3 gui_canh_bao_goidau_cod.py --dry-run')
print(stdout.read().decode('utf-8', errors='ignore'))
print(stderr.read().decode('utf-8', errors='ignore'))

ssh.close()

