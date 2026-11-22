with open(r'C:\Users\lap4all\Desktop\New folder\data.js', 'r', encoding='utf-8') as f:
    text = f.read()

print("Char 684730 to 684780:")
print(repr(text[684730:684780]))
print("End of text:")
print(repr(text[-200:]))

