with open(r'C:\Users\lap4all\Desktop\New folder\templates\index.html', 'r', encoding='utf-8') as f:
    t = f.read()

print('Title in templates/index.html:', t[t.find('<title>'):t.find('</title>')+8])
print('Head length:', len(t))
print('Does templates/index.html have hop content?:', 'tab-overview' in t)

