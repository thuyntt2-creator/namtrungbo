with open(r'C:\Users\lap4all\Desktop\New folder\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(7130, 7155):
    print(f"{i+1}: {lines[i].rstrip()}")

