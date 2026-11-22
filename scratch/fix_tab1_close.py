with open(r'C:\Users\lap4all\Desktop\New folder\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the boundary between Tab 1 and Tab 2
target = """</div>
<!-- ==================================================================== -->
<!-- TAB 2: SẢN LƯỢNG GIAO (FULL HÀNG & PHÂN KHÚC TTS) -->"""

replacement = """</div>
</div>
<!-- ==================================================================== -->
<!-- TAB 2: SẢN LƯỢNG GIAO (FULL HÀNG & PHÂN KHÚC TTS) -->"""

assert target in text, "Target boundary not found!"
text = text.replace(target, replacement, 1)

with open(r'C:\Users\lap4all\Desktop\New folder\index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated index.html with closing div for tab-overview.")

