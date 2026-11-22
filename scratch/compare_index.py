import os

p1 = r'C:\Users\lap4all\Desktop\New folder\index.html'
p2 = r'C:\Users\lap4all\Desktop\New folder\templates\index.html'

t1 = open(p1, 'r', encoding='utf-8').read()
t2 = open(p2, 'r', encoding='utf-8').read()

print('Lengths:', len(t1), len(t2))
print('Identical:', t1 == t2)
if t1 != t2:
    print('Diff in size:', len(t1) - len(t2))

