with open(r'C:\Users\lap4all\Desktop\New folder\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

m = re.search(r'(<div class="tab-view" id="tab-gtc-tong">[\s\S]*?)(<div class="tab-view" id="tab-gtc-tts-ca1">)', text)
if m:
    content = m.group(1)
    print("Found tab-gtc-tong block, length:", len(content))
    open_d = content.count('<div')
    close_d = content.count('</div')
    print(f"Open divs: {open_d}, Close divs: {close_d}")
else:
    print("Could not match tab-gtc-tong block!")

