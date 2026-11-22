import os

app_js_path = r'C:\Users\lap4all\Desktop\New folder\app.js'
with open(app_js_path, 'r', encoding='utf-8') as f:
    js = f.read()

target = """      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: { top: 20, bottom: 8 } },





  // --------------------------------------------------------------------------
  // TAB 12: BÁO CÁO TRUY THU KHỐI LƯỢNG & TICKET VI PHẠM (OE-IA)
  // --------------------------------------------------------------------------"""

replacement = """      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: { top: 20, bottom: 8 } },
        scales: {
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
  }

  // --------------------------------------------------------------------------
  // TAB 12: BÁO CÁO TRUY THU KHỐI LƯỢNG & TICKET VI PHẠM (OE-IA)
  // --------------------------------------------------------------------------"""

if target in js:
    js = js.replace(target, replacement)
    print("Fixed renderCodTmAmBar options closing.")
else:
    print("WARNING: target not found!")
    # regex fallback
    import re
    pat = r'layout: \{ padding: \{ top: 20, bottom: 8 \} \},[\s\S]*?// TAB 12: BÁO CÁO TRUY THU'
    rep = """layout: { padding: { top: 20, bottom: 8 } },
        scales: {
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
  }

  // --------------------------------------------------------------------------
  // TAB 12: BÁO CÁO TRUY THU"""
    js = re.sub(pat, rep, js)
    print("Applied regex fallback.")

with open(app_js_path, 'w', encoding='utf-8') as f:
    f.write(js)

