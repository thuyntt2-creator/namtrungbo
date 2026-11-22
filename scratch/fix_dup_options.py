import os

app_js_path = r'C:\Users\lap4all\Desktop\New folder\app.js'
with open(app_js_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Check lines 9450-9480
dup_target = """        scales: {
          x: { stacked: true },
          y: {
            stacked: true,
            ticks: { callback: v => fNum(v) + ' Tr' },
            title: { display: true, text: 'Tổng Tiền COD (Triệu VNĐ)', font: { weight: '700', size: 11 } }
          }
        },
        plugins: {
          legend: { position: 'top' },
          tooltip: {
            callbacks: {
              label: c => ` ${c.dataset.label}: ${fNum(c.parsed.y)} Triệu VNĐ`
            }
          }
        }
      }
    });
  }"""

content = "".join(lines)
if dup_target in content:
    content = content.replace(dup_target, "")
    print("Removed duplicate options block.")
else:
    print("WARNING: dup_target not found.")

with open(app_js_path, 'w', encoding='utf-8') as f:
    f.write(content)

