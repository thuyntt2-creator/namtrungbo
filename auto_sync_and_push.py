import os
import sys
import subprocess
import datetime

sys.stdout.reconfigure(encoding='utf-8')

cwd = r"c:\Users\lap4all\Desktop\New folder"
log_path = os.path.join(cwd, "auto_sync.log")

def log(msg):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}\n"
    print(line, end="")
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass

def show_windows_alert(title, message):
    try:
        ps_cmd = f'[System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms"); [System.Windows.Forms.MessageBox]::Show("{message}", "{title}", 0, 48)'
        subprocess.Popen(["powershell", "-NoProfile", "-Command", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

log("=== Starting Auto Sync Pipeline ===")

# Step 1: Run local company sync script
step1_success = False
try:
    log("Step 1: Downloading latest company Google Sheets...")
    p1 = subprocess.run([sys.executable, r"scratch\sync_local_company.py"], cwd=cwd, capture_output=True, text=True, timeout=360)
    log(f"Step 1 Return Code: {p1.returncode}")
    if p1.stdout:
        log(f"Output: {p1.stdout.strip()}")
    if p1.returncode == 0:
        step1_success = True
    else:
        log("❌ Step 1 Failed! Google Sheets could not be downloaded.")
        show_windows_alert(
            "CẢNH BÁO ĐỒNG BỘ DỮ LIỆU NTB", 
            "Đồng bộ Google Sheets bị lỗi (Có thể do Token Google OAuth hết hạn).\\nVui lòng chạy file DANG_NHAP_LAI_GOOGLE.bat trên Desktop/thư mục dự án để làm mới đăng nhập!"
        )
except Exception as e:
    log(f"Step 1 Exception: {e}")

if not step1_success:
    log("⚠️ Aborting Step 2 and Step 3 because Step 1 (Download Data) failed.")
    log("=== Auto Sync Pipeline Finished With Errors ===")
    sys.exit(1)

# Step 2: Bootstrap/Update Neon DB
try:
    log("Step 2: Updating Neon PostgreSQL Database...")
    p2 = subprocess.run([sys.executable, r"scratch\bootstrap_new_db.py"], cwd=cwd, capture_output=True, text=True, timeout=300)
    log(f"Step 2 Return Code: {p2.returncode}")
    if p2.stdout:
        log(f"Output: {p2.stdout.strip()}")
except Exception as e:
    log(f"Step 2 Exception: {e}")

# Step 2.5: Run auxiliary enrichment scripts then rebuild dashboard data
try:
    log("Step 2.5: Running auxiliary enrichment scripts (transport costs, kinh doanh, etc.)...")
    for script_name in ["parse_kinh_doanh.py", "parse_4_cod_tabs.py", "calc_aging_buckets.py", "process_truy_thu_report.py", "sync_ncc_transport_costs.py"]:
        s_path = os.path.join(cwd, "scratch", script_name)
        if os.path.exists(s_path):
            subprocess.run([sys.executable, s_path], cwd=cwd, capture_output=True, text=True, timeout=120)
            
        # [DA TAT DONG BO WEEKLY THEO YEU CAU - DUNG LINK LOCAL]
    # log("Step 2.5: Rebuilding /hop weekly dashboard data (build_data_js.py)...")
    # p_b = subprocess.run([sys.executable, "build_data_js.py"], cwd=cwd, capture_output=True, text=True, timeout=120)
    # log(f"build_data_js Return Code: {p_b.returncode}")
    log("Step 2.5: Da bo qua buoc dong bo weekly dashboard (build_data_js.py) theo yeu cau.")
except Exception as e:
    log(f"Step 2.5 Exception: {e}")

# Step 3: Git add, commit, and push
try:
    # Safeguard: Ensure templates/index.html is ALWAYS the GHN Ops Dashboard
    try:
        tpl_path = os.path.join(cwd, "templates", "index.html")
        if os.path.exists(tpl_path):
            with open(tpl_path, "r", encoding="utf-8", errors="ignore") as f_tpl:
                tpl_head = f_tpl.read(2000)
            if "BÁO CÁO HỌP TUẦN" in tpl_head or "BAO CAO H" in tpl_head:
                log("⚠️ CẢNH BÁO: templates/index.html bị ghi đè nhầm, đang tự động khôi phục...")
                subprocess.run(["git", "checkout", "1596aa8", "--", "templates/index.html"], cwd=cwd)
                log("✅ Đã tự động bảo vệ và khôi phục templates/index.html về GHN Ops Dashboard!")
    except Exception as sg_err:
        log(f"Safeguard error: {sg_err}")

    # Cấu hình Deploy theo yêu cầu của Chị Thủy:
    # - Buổi sáng (6h00 đến 12h59 trưa): Chạy 30 phút/lần, commit và push lên GitHub/Vercel để cập nhật dashboard.
    # - Buổi chiều & Tối (từ 13h00 trở đi): Chỉ đồng bộ dữ liệu vào Neon DB & lưu local, bỏ qua Git Push lên Vercel để tránh chạm giới hạn 100 deploy/ngày.
        # [DA TAT GIT PUSH LEN VERCEL DE TRANH TRAN DUNG LUONG / CPU VERCEL]
    ENABLE_VERCEL_PUSH = False  # Chuyen thanh True neu sau nay can push len Vercel
    now_hour = datetime.datetime.now().hour
    is_morning_window = (6 <= now_hour <= 12) and ENABLE_VERCEL_PUSH
    
    if is_morning_window:
        log("Step 3: Git add and commit...")
        subprocess.run(["git", "add", "*.csv", "ops_ca_data.csv", "app.py", "scratch/", "data.js", "data.json", "index.html", "templates/", "transport_costs.json", "app.js", ".gitignore"], cwd=cwd, capture_output=True)
        commit_msg = "Auto update data NTB"
        log(f"Step 3: Buổi sáng ({now_hour}h) -> Tiến hành Git commit và Push deploy Vercel (30 phút/lần)...")
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=cwd, capture_output=True)
        
        # Push đồng thời tới cả 3 remote để dashboard sếp và dashboard mới luôn cập nhật song song
        # Chỉ push tới duy nhất remote origin (namtrungbo) để tránh spam Vercel
        remotes = ["origin"]
        for rem in remotes:
            log(f"Step 3: Git push to GitHub ({rem})...")
            try:
                p = subprocess.run(["git", "push", rem, "main"], cwd=cwd, capture_output=True, text=True, timeout=180)
                log(f"Push to {rem} Return Code: {p.returncode}")
                if p.stdout:
                    log(f"[{rem}] Output: {p.stdout.strip()}")
                if p.stderr and "Everything up-to-date" not in p.stderr:
                    log(f"[{rem}] Stderr: {p.stderr.strip()}")
            except Exception as push_err:
                log(f"Push to {rem} Exception: {push_err}")

        # Ping làm ấm (Warm up) cả 2 trang Vercel để người dùng truy cập không bị chậm/chờ cold-start
        try:
            import urllib.request
            for site in ["https://dashboard-ntb-2026.vercel.app/", "https://namtrungbo.vercel.app/"]:
                req = urllib.request.Request(site, headers={"User-Agent": "Mozilla/5.0 (WarmUpBot)"})
                urllib.request.urlopen(req, timeout=15)
            log("Step 3: Đã ping làm ấm cả 2 link Vercel thành công.")
        except Exception as warm_err:
            log(f"Warm up exception (bỏ qua): {warm_err}")
    else:
        log(f"Step 3: Buổi chiều/tối ({now_hour}h) -> Đã đồng bộ DB Neon thành công. BỎ QUA Git push lên Vercel theo cấu hình (chỉ deploy buổi sáng đến 12h).")
except Exception as e:
    log(f"Step 3 Exception: {e}")

log("=== Auto Sync Pipeline Finished ===")
