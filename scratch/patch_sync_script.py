with open('auto_sync_and_push.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'remotes = ["origin", "db_2026", "boss"]' in line:
        new_lines.append('        # Chỉ push tới duy nhất remote origin (namtrungbo) để tránh spam Vercel\n')
        new_lines.append('        remotes = ["origin"]\n')
    else:
        new_lines.append(line)

with open('auto_sync_and_push.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Successfully patched auto_sync_and_push.py!")

