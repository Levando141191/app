import flet as ft
import sqlite3
import ssl
import re

# Bỏ qua kiểm tra chứng chỉ SSL
ssl._create_default_https_context = ssl._create_unverified_context

# ==========================================
# CÔNG CỤ TÍNH TOÁN TIỀN TỆ & XỬ LÝ TÊN CHUẨN VN
# ==========================================
def parse_money(s):
    if not s: return 0
    s = str(s).lower().strip()
    if 'tr' in s:
        s = s.replace('tr', '').replace(',', '.')
        s = re.sub(r'[^\d.]', '', s)
        try: return int(float(s) * 1000000)
        except: return 0
    elif 'k' in s:
        s = s.replace('k', '').replace(',', '.')
        s = re.sub(r'[^\d.]', '', s)
        try: return int(float(s) * 1000)
        except: return 0
    else:
        s = s.replace('.', '').replace(',', '')
        s = re.sub(r'\D', '', s)
        try: return int(s)
        except: return 0

def format_money(val):
    if val == 0: return ""
    if val >= 1000000 and val % 1000000 == 0:
        return f"{val//1000000}tr"
    if val >= 1000 and val % 1000 == 0:
        return f"{val//1000}k"
    return f"{val:,}".replace(',', '.')

def get_first_name(full_name):
    parts = str(full_name).strip().split()
    return parts[-1].lower() if parts else ""

# ==========================================
# 1. KHỞI TẠO & CƠ SỞ DỮ LIỆU ĐA NGƯỜI DÙNG
# ==========================================
conn = sqlite3.connect('quan_ly_lop_v2.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS NguoiDung (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, phone TEXT, email TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS CaiDat (id INTEGER PRIMARY KEY, mat_khau TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS NhomLop (id INTEGER PRIMARY KEY AUTOINCREMENT, ten_lop TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS HocSinh (id INTEGER PRIMARY KEY AUTOINCREMENT, lop_id INTEGER, ten_hs TEXT, trang_thai INTEGER DEFAULT 1)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS NamHoc (id INTEGER PRIMARY KEY AUTOINCREMENT, lop_id INTEGER, ten_nam TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS ChuKy (
    id INTEGER PRIMARY KEY AUTOINCREMENT, lop_id INTEGER, nam_hoc_id INTEGER DEFAULT 0, so_thu_tu INTEGER, ngay_bat_dau TEXT DEFAULT '',
    ngay_b1 TEXT DEFAULT '', ngay_b2 TEXT DEFAULT '', ngay_b3 TEXT DEFAULT '', ngay_b4 TEXT DEFAULT '', 
    ngay_b5 TEXT DEFAULT '', ngay_b6 TEXT DEFAULT '', ngay_b7 TEXT DEFAULT '', ngay_b8 TEXT DEFAULT '', 
    ngay_b9 TEXT DEFAULT '', ngay_b10 TEXT DEFAULT ''
)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS DiemDanh (
    id INTEGER PRIMARY KEY AUTOINCREMENT, hoc_sinh_id INTEGER, chu_ky_id INTEGER,
    b1 INTEGER DEFAULT 0, b2 INTEGER DEFAULT 0, b3 INTEGER DEFAULT 0, b4 INTEGER DEFAULT 0, 
    b5 INTEGER DEFAULT 0, b6 INTEGER DEFAULT 0, b7 INTEGER DEFAULT 0, b8 INTEGER DEFAULT 0, 
    b9 INTEGER DEFAULT 0, b10 INTEGER DEFAULT 0,
    tien_hoc TEXT DEFAULT '', tien_no TEXT DEFAULT '', tong_tien TEXT DEFAULT '', ngay_dong TEXT DEFAULT '',
    da_dong_tien INTEGER DEFAULT 0
)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS LichHocTuan (
    id INTEGER PRIMARY KEY AUTOINCREMENT, thu TEXT, buoi TEXT, ca INTEGER, noi_dung TEXT DEFAULT ''
)''')

# --- NÂNG CẤP ĐA TÀI KHOẢN ---
try: cursor.execute("ALTER TABLE CaiDat ADD COLUMN user_id INTEGER DEFAULT 1")
except: pass
try: cursor.execute("ALTER TABLE CaiDat ADD COLUMN mat_khau_tai_chinh TEXT DEFAULT ''")
except: pass
try: cursor.execute("ALTER TABLE NhomLop ADD COLUMN user_id INTEGER DEFAULT 1")
except: pass
try: cursor.execute("ALTER TABLE LichHocTuan ADD COLUMN user_id INTEGER DEFAULT 1")
except: pass

try: cursor.execute("ALTER TABLE DiemDanh ADD COLUMN tien_hoc TEXT DEFAULT ''")
except: pass
try: cursor.execute("ALTER TABLE DiemDanh ADD COLUMN tien_no TEXT DEFAULT ''")
except: pass
try: cursor.execute("ALTER TABLE DiemDanh ADD COLUMN tong_tien TEXT DEFAULT ''")
except: pass
try: cursor.execute("ALTER TABLE DiemDanh ADD COLUMN ngay_dong TEXT DEFAULT ''")
except: pass
try: cursor.execute("ALTER TABLE DiemDanh ADD COLUMN da_dong_tien INTEGER DEFAULT 0")
except: pass
try: cursor.execute("ALTER TABLE HocSinh ADD COLUMN trang_thai INTEGER DEFAULT 1")
except: pass
try: cursor.execute("ALTER TABLE HocSinh ADD COLUMN ten_ph TEXT DEFAULT ''")
except: pass
try: cursor.execute("ALTER TABLE HocSinh ADD COLUMN sdt_ph TEXT DEFAULT ''")
except: pass
try: cursor.execute("ALTER TABLE NhomLop ADD COLUMN khoi INTEGER DEFAULT 6")
except: pass
try: cursor.execute("ALTER TABLE NhomLop ADD COLUMN thoi_khoa_bieu TEXT DEFAULT ''")
except: pass
for i in range(1, 11):
    try: cursor.execute(f"ALTER TABLE ChuKy ADD COLUMN ghi_chu_b{i} TEXT DEFAULT ''")
    except: pass
conn.commit() 

# --- TẠO DỮ LIỆU MẶC ĐỊNH CHO TÀI KHOẢN 1 ---
cursor.execute("SELECT mat_khau FROM CaiDat WHERE user_id = 1")
if not cursor.fetchone():
    cursor.execute("INSERT INTO CaiDat (user_id, mat_khau, mat_khau_tai_chinh) VALUES (1, '', '')")
    conn.commit()

cursor.execute("SELECT COUNT(*) FROM LichHocTuan WHERE user_id = 1")
if cursor.fetchone()[0] == 0:
    for buoi, ca in [('Sáng', 1), ('Sáng', 2), ('Chiều', 1), ('Chiều', 2), ('Tối', 1), ('Tối', 2)]:
        for thu in ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']:
            cursor.execute("INSERT INTO LichHocTuan (thu, buoi, ca, user_id) VALUES (?, ?, ?, 1)", (thu, buoi, ca))
    conn.commit()

# ==========================================
# 2. XÂY DỰNG GIAO DIỆN APP CHÍNH
# ==========================================
def main(page: ft.Page):
    page.title = "Phần Mềm Quản Lý Lớp Học"
    page.window.width = 480
    page.window.height = 850
    page.scroll = ft.ScrollMode.ALWAYS 

    # --- BIẾN PHIÊN ĐĂNG NHẬP ---
    current_user_id = [None]
    app_password = [""]
    finance_password = [""]
    is_locked = [False]

    current_khoi = [6]
    current_class_id = [None]
    current_year_id = [None]
    current_cycle_id = [None]
    current_student_id = [None]
    show_finance = [False]
    pending_action = [None] 
    tong_tien_tfs = {}

    # ================= MÀN HÌNH ĐĂNG NHẬP & ĐĂNG KÝ =================
    login_view = ft.Column(visible=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    register_view = ft.Column(visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    home_view = ft.Column(visible=False)
    class_view = ft.Column(visible=False)

    def do_login(e=None):
        u = login_username.value.strip()
        p = login_password.value.strip()
        if not u or not p:
            login_error.value = "Vui lòng nhập đầy đủ tên và mật khẩu!"
            page.update(); return
        
        cursor.execute("SELECT id FROM NguoiDung WHERE username = ? AND password = ?", (u, p))
        row = cursor.fetchone()
        if row:
            current_user_id[0] = row[0]
            login_error.value = ""; login_username.value = ""; login_password.value = ""
            init_user_data()
            show_home()
        else:
            login_error.value = "Sai tên đăng nhập hoặc mật khẩu!"
            page.update()

    def do_register(e=None):
        u = reg_name.value.strip(); p = reg_pass.value.strip()
        phone = reg_phone.value.strip(); email = reg_email.value.strip()
        if not u or not p:
            reg_error.value = "Tên người dùng và mật khẩu là bắt buộc!"
            page.update(); return
            
        cursor.execute("SELECT id FROM NguoiDung WHERE username = ?", (u,))
        if cursor.fetchone():
            reg_error.value = "Tên người dùng đã tồn tại!"
            page.update(); return
            
        cursor.execute("SELECT COUNT(*) FROM NguoiDung")
        is_first = (cursor.fetchone()[0] == 0)
        
        if is_first: cursor.execute("INSERT INTO NguoiDung (id, username, password, phone, email) VALUES (1, ?, ?, ?, ?)", (u, p, phone, email))
        else: cursor.execute("INSERT INTO NguoiDung (username, password, phone, email) VALUES (?, ?, ?, ?)", (u, p, phone, email))
            
        new_uid = cursor.lastrowid
        cursor.execute("SELECT id FROM CaiDat WHERE user_id = ?", (new_uid,))
        if not cursor.fetchone(): cursor.execute("INSERT INTO CaiDat (user_id, mat_khau, mat_khau_tai_chinh) VALUES (?, '', '')", (new_uid,))
            
        cursor.execute("SELECT id FROM LichHocTuan WHERE user_id = ?", (new_uid,))
        if not cursor.fetchone():
            for buoi, ca in [('Sáng', 1), ('Sáng', 2), ('Chiều', 1), ('Chiều', 2), ('Tối', 1), ('Tối', 2)]:
                for thu in ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']:
                    cursor.execute("INSERT INTO LichHocTuan (thu, buoi, ca, user_id) VALUES (?, ?, ?, ?)", (thu, buoi, ca, new_uid))
        conn.commit()
        reg_error.value = ""; reg_name.value = ""; reg_pass.value = ""; reg_phone.value = ""; reg_email.value = ""
        current_user_id[0] = new_uid
        init_user_data()
        show_home()

    def do_logout():
        current_user_id[0] = None; current_class_id[0] = None
        app_password[0] = ""; finance_password[0] = ""
        is_locked[0] = False; show_finance[0] = False
        login_view.visible = True
        register_view.visible = False
        home_view.visible = False
        class_view.visible = False
        page.update()

    def show_register_view():
        login_view.visible = False; register_view.visible = True; page.update()

    def show_login_view():
        login_view.visible = True; register_view.visible = False; page.update()

    def init_user_data():
        cursor.execute("SELECT mat_khau, mat_khau_tai_chinh FROM CaiDat WHERE user_id = ?", (current_user_id[0],))
        row = cursor.fetchone()
        if row:
            app_password[0] = row[0] if row[0] else ""
            finance_password[0] = row[1] if row[1] else ""
        is_locked[0] = True if app_password[0] != "" else False
        update_lock_ui()

    # --- UI ĐĂNG NHẬP ---
    login_username = ft.TextField(label="Tên đăng nhập", width=300)
    login_password = ft.TextField(label="Mật khẩu", password=True, can_reveal_password=True, width=300, on_submit=do_login)
    login_error = ft.Text(color="red", size=13)
    
    btn_login_submit = ft.Container(content=ft.Row([ft.Text("Đăng Nhập", color=ft.Colors.WHITE, weight="bold")], alignment=ft.MainAxisAlignment.CENTER), bgcolor=ft.Colors.BLUE_700, width=300, height=45, border_radius=8, ink=True, on_click=do_login)
    btn_goto_register = ft.Container(content=ft.Row([ft.Text("Tạo tài khoản mới", color=ft.Colors.BLUE_700, weight="bold")], alignment=ft.MainAxisAlignment.CENTER), padding=5, ink=True, on_click=lambda e: show_register_view())
    btn_forgot_pass = ft.Container(content=ft.Row([ft.Text("Quên tài khoản / Mật khẩu?", color=ft.Colors.PURPLE_700, weight="bold", size=13)], alignment=ft.MainAxisAlignment.CENTER), padding=5, ink=True, on_click=lambda e: open_dialog(forgot_dialog))

    login_card = ft.Card(
        elevation=10,
        content=ft.Container(
            padding=30, width=350,
            content=ft.Column([
                ft.Icon(ft.Icons.LOCK_PERSON, size=60, color=ft.Colors.BLUE_700),
                ft.Text("ĐĂNG NHẬP", size=24, weight="bold", color=ft.Colors.BLUE_900),
                login_username, login_password, login_error,
                btn_login_submit,
                btn_goto_register,
                btn_forgot_pass
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
    )
    login_view.controls.extend([
        ft.Container(height=50),
        ft.Container(content=login_card)
    ])

    # --- UI ĐĂNG KÝ ---
    reg_name = ft.TextField(label="Tên đăng nhập", width=300)
    reg_pass = ft.TextField(label="Mật khẩu", password=True, can_reveal_password=True, width=300)
    reg_phone = ft.TextField(label="Số điện thoại đăng ký", width=300)
    reg_email = ft.TextField(label="Email", width=300, on_submit=do_register)
    reg_error = ft.Text(color="red", size=13)
    
    btn_register_submit = ft.Container(content=ft.Row([ft.Text("Đăng Ký", color=ft.Colors.WHITE, weight="bold")], alignment=ft.MainAxisAlignment.CENTER), bgcolor=ft.Colors.GREEN_700, width=300, height=45, border_radius=8, ink=True, on_click=do_register)
    btn_goto_login = ft.Container(content=ft.Row([ft.Text("Đã có tài khoản? Đăng nhập", color=ft.Colors.BLUE_700, weight="bold")], alignment=ft.MainAxisAlignment.CENTER), padding=10, ink=True, on_click=lambda e: show_login_view())

    register_card = ft.Card(
        elevation=10,
        content=ft.Container(
            padding=30, width=350,
            content=ft.Column([
                ft.Icon(ft.Icons.APP_REGISTRATION, size=60, color=ft.Colors.GREEN_700),
                ft.Text("ĐĂNG KÝ", size=24, weight="bold", color=ft.Colors.GREEN_900),
                reg_name, reg_pass, reg_phone, reg_email, reg_error,
                btn_register_submit,
                btn_goto_login
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
    )
    register_view.controls.extend([
        ft.Container(height=40),
        ft.Container(content=register_card)
    ])

    # ================= CÁC Ô NHẬP TẠO LỚP & HS =================
    class_name_input = ft.TextField(label="Nhập tên nhóm mới")
    edit_class_name_input = ft.TextField(label="Đổi tên nhóm")
    year_name_input = ft.TextField(label="Nhập tên năm học (VD: Năm 2025-2026)")
    edit_year_name_input = ft.TextField(label="Đổi tên năm học")
    
    student_name_input = ft.TextField(label="Tên học sinh (*Bắt buộc)")
    parent_name_input = ft.TextField(label="Tên phụ huynh (Không bắt buộc)")
    parent_phone_input = ft.TextField(label="Số điện thoại (Không bắt buộc)")
    edit_student_name_input = ft.TextField(label="Tên học sinh")
    edit_parent_name_input = ft.TextField(label="Tên phụ huynh")
    edit_parent_phone_input = ft.TextField(label="Số điện thoại")

    password_input = ft.TextField(label="Nhập mật khẩu APP", password=True, can_reveal_password=True, autofocus=True)
    password_error = ft.Text(color="red", size=12)
    finance_password_input = ft.TextField(label="Nhập mật khẩu thông tin HS", password=True, can_reveal_password=True, autofocus=True)
    finance_password_error = ft.Text(color="red", size=12)

    old_app_pass_input = ft.TextField(label="Nhập mật khẩu APP cũ (Để trống nếu chưa cài)", password=True, can_reveal_password=True)
    new_app_pass_input = ft.TextField(label="Nhập mật khẩu APP mới (Để trống để tắt khóa)", password=True, can_reveal_password=True)
    app_pass_change_error = ft.Text(color="red", size=12)

    old_fin_pass_input = ft.TextField(label="Nhập mật khẩu HS cũ (Để trống nếu chưa cài)", password=True, can_reveal_password=True)
    new_fin_pass_input = ft.TextField(label="Nhập mật khẩu HS mới (Để trống để tắt khóa)", password=True, can_reveal_password=True)
    fin_pass_change_error = ft.Text(color="red", size=12)

    # Ô nhập liệu Quên mật khẩu
    forgot_phone_input = ft.TextField(label="Nhập số điện thoại đã đăng ký")
    forgot_email_input = ft.TextField(label="Nhập Email đã đăng ký")
    forgot_result_text = ft.Text("", color="green", size=13)

    note_input = ft.TextField(multiline=True, min_lines=3, max_lines=6, label="Nội dung bài tập / Ghi chú")
    current_note_col = [""]

    table_container = ft.Column()
    khoi_selector_row = ft.Row(scroll=ft.ScrollMode.ALWAYS)
    class_grid_row = ft.Row(wrap=True, spacing=15, run_spacing=15) 
    schedule_container = ft.Column() 
    year_selector_row = ft.Row(scroll=ft.ScrollMode.ALWAYS)
    cycle_selector_row = ft.Row(scroll=ft.ScrollMode.ALWAYS)

    btn_add_student = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.PERSON_ADD, color=ft.Colors.WHITE, size=16), ft.Text("Thêm Học Sinh", color=ft.Colors.WHITE, weight="bold")], alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=ft.Colors.GREEN_600, padding=12, border_radius=8, ink=True, on_click=lambda e: open_dialog(student_dialog), width=180
    )
    
    btn_toggle_finance = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.SECURITY, color=ft.Colors.WHITE, size=16), ft.Text("Thông tin học sinh", color=ft.Colors.WHITE, weight="bold")], alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=ft.Colors.ORANGE_600, padding=12, border_radius=8, ink=True, width=200
    )

    class_top_title = ft.Text("", size=22, weight="bold", color=ft.Colors.BLUE_900)
    class_schedule_input = ft.TextField(hint_text="Nhập thời gian học (VD: T3-T5 18h00)", border=ft.InputBorder.UNDERLINE, text_size=13, height=35, content_padding=5, expand=True)

    def update_schedule(e):
        if is_locked[0]: return show_locked_msg()
        if current_class_id[0]:
            cursor.execute("UPDATE NhomLop SET thoi_khoa_bieu = ? WHERE id = ? AND user_id = ?", (e.control.value, current_class_id[0], current_user_id[0]))
            conn.commit()
    class_schedule_input.on_change = update_schedule

    def create_small_button(text_val, icon_val, on_click_handler, bg_color, text_color):
        return ft.Container(content=ft.Row([ft.Icon(icon_val, color=text_color, size=16), ft.Text(text_val, color=text_color, weight="bold", size=13)], alignment=ft.MainAxisAlignment.START),
            bgcolor=bg_color, padding=8, border_radius=6, ink=True, on_click=on_click_handler)

    # ==========================================
    # CÁC HÀM ĐIỀU HƯỚNG CẤP ĐỘ
    # ==========================================
    def show_home():
        current_class_id[0] = None
        login_view.visible = False; register_view.visible = False
        home_view.visible = True; class_view.visible = False
        show_finance[0] = False 
        update_finance_btn_ui(update_page=False)
        load_khoi(); render_global_schedule(); page.update()

    def enter_class(lop_id):
        current_class_id[0] = str(lop_id); current_year_id[0] = None; current_cycle_id[0] = None
        show_finance[0] = False 
        update_finance_btn_ui(update_page=False)
        cursor.execute("SELECT ten_lop, thoi_khoa_bieu FROM NhomLop WHERE id = ? AND user_id = ?", (lop_id, current_user_id[0]))
        row = cursor.fetchone()
        if row:
            class_top_title.value = f"Nhóm: {row[0]}"
            class_schedule_input.value = row[1] if row[1] else ""
            class_schedule_input.read_only = is_locked[0]
        home_view.visible = False; class_view.visible = True
        load_years(); page.update()

    def load_khoi():
        khoi_selector_row.controls.clear()
        for k in range(6, 13):
            is_active = (k == current_khoi[0])
            bg_col = ft.Colors.PURPLE_700 if is_active else ft.Colors.PURPLE_50
            txt_col = ft.Colors.WHITE if is_active else ft.Colors.PURPLE_900
            btn = ft.Container(content=ft.Text(f"Lớp {k}", color=txt_col, weight="bold"), bgcolor=bg_col, padding=10, border_radius=8, ink=True)
            btn_gesture = ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK, on_tap=lambda e, kv=k: select_khoi(kv),
                on_secondary_tap=lambda e, kv=k: open_khoi_action_menu(kv),
                on_long_press=lambda e, kv=k: open_khoi_action_menu(kv),
                content=btn
            )
            khoi_selector_row.controls.append(btn_gesture)
        load_classes()

    def select_khoi(khoi_val):
        current_khoi[0] = khoi_val; load_khoi(); page.update()

    def load_classes():
        cursor.execute("SELECT id, ten_lop, thoi_khoa_bieu FROM NhomLop WHERE khoi = ? AND user_id = ?", (current_khoi[0], current_user_id[0]))
        lops = cursor.fetchall()
        class_grid_row.controls.clear()
        for lop in lops:
            lop_id = str(lop[0]); ten_lop = lop[1]; schedule = lop[2]
            card_content = ft.Column([
                ft.Row([ft.Icon(ft.Icons.CLASS_, color=ft.Colors.BLUE_700), ft.Text(ten_lop, weight="bold", size=16, color=ft.Colors.BLUE_900)]),
                ft.Text(schedule if schedule else "Chưa có lịch", size=12, color=ft.Colors.GREY_600)
            ], spacing=2)
            card = ft.Container(content=card_content, bgcolor=ft.Colors.BLUE_50, padding=15, border_radius=10, border=ft.Border.all(1, ft.Colors.BLUE_200), width=200, ink=True)
            card_gesture = ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK, on_tap=lambda e, lid=lop_id: enter_class(lid),
                on_secondary_tap=lambda e, lid=lop_id, tname=ten_lop: open_class_action_menu(lid, tname),
                on_long_press=lambda e, lid=lop_id, tname=ten_lop: open_class_action_menu(lid, tname),
                content=card
            )
            class_grid_row.controls.append(card_gesture)

    def load_years():
        if not current_class_id[0]: return
        cursor.execute("SELECT id, ten_nam FROM NamHoc WHERE lop_id = ?", (current_class_id[0],))
        years = cursor.fetchall()
        year_selector_row.controls.clear()
        for y in years:
            y_id = str(y[0]); ten_nam = y[1]
            is_active = (y_id == current_year_id[0])
            bg_col = ft.Colors.TEAL_700 if is_active else ft.Colors.TEAL_100
            txt_col = ft.Colors.WHITE if is_active else ft.Colors.TEAL_900
            btn = ft.Container(content=ft.Text(ten_nam, color=txt_col, weight="bold"), bgcolor=bg_col, padding=8, border_radius=6, ink=True)
            btn_gesture = ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK, on_tap=lambda e, yid=y_id: select_year(yid),
                on_secondary_tap=lambda e, yid=y_id, tname=ten_nam: open_year_action_menu(yid, tname),
                on_long_press=lambda e, yid=y_id, tname=ten_nam: open_year_action_menu(yid, tname),
                content=btn
            )
            year_selector_row.controls.append(btn_gesture)
        btn_new_year = ft.Container(content=ft.Row([ft.Icon(ft.Icons.ADD, color=ft.Colors.TEAL_900, size=16), ft.Text("Năm Học", color=ft.Colors.TEAL_900, weight="bold")]), bgcolor=ft.Colors.TEAL_100, padding=8, border_radius=6, ink=True, on_click=lambda e: open_dialog(year_dialog))
        btn_new_year.visible = not is_locked[0]
        year_selector_row.controls.append(btn_new_year)
        if len(years) > 0 and current_year_id[0] is None: select_year(str(years[-1][0]))
        elif len(years) == 0: cycle_selector_row.controls.clear(); table_container.controls.clear(); page.update()
        else: page.update()

    def select_year(year_id):
        current_year_id[0] = str(year_id); current_cycle_id[0] = None; load_years(); load_cycles()

    def load_cycles():
        if not current_year_id[0]: return
        cursor.execute("SELECT id, so_thu_tu FROM ChuKy WHERE nam_hoc_id = ? ORDER BY so_thu_tu ASC", (current_year_id[0],))
        cycles = cursor.fetchall()
        cycle_selector_row.controls.clear()
        for c in cycles:
            c_id = str(c[0]); c_stt = c[1]
            is_active = (c_id == current_cycle_id[0])
            bg_col = ft.Colors.ORANGE_600 if is_active else ft.Colors.ORANGE_100
            txt_col = ft.Colors.WHITE if is_active else ft.Colors.ORANGE_900
            btn = ft.Container(content=ft.Text(f"Chu Kỳ {c_stt}", color=txt_col, weight="bold"), bgcolor=bg_col, padding=8, border_radius=6, ink=True, on_click=lambda e, cid=c_id: select_cycle(cid))
            cycle_selector_row.controls.append(btn)
        btn_new_cycle = ft.Container(content=ft.Row([ft.Icon(ft.Icons.ADD, color=ft.Colors.ORANGE_900, size=16), ft.Text("Chu Kỳ", color=ft.Colors.ORANGE_900, weight="bold")]), bgcolor=ft.Colors.ORANGE_100, padding=8, border_radius=6, ink=True, on_click=create_new_cycle)
        btn_new_cycle.visible = not is_locked[0]
        cycle_selector_row.controls.append(btn_new_cycle)
        if len(cycles) > 0 and current_cycle_id[0] is None: select_cycle(str(cycles[-1][0])) 
        elif len(cycles) == 0: table_container.controls.clear(); page.update()
        else: page.update()

    def select_cycle(cycle_id):
        current_cycle_id[0] = str(cycle_id); load_cycles(); render_table()

    def add_new_class(e):
        if class_name_input.value != "":
            cursor.execute("INSERT INTO NhomLop (ten_lop, khoi, user_id) VALUES (?, ?, ?)", (class_name_input.value, current_khoi[0], current_user_id[0]))
            lop_id = cursor.lastrowid
            cursor.execute("INSERT INTO NamHoc (lop_id, ten_nam) VALUES (?, ?)", (lop_id, "Năm Học Đầu Tiên"))
            nh_id = cursor.lastrowid
            cursor.execute("INSERT INTO ChuKy (lop_id, nam_hoc_id, so_thu_tu) VALUES (?, ?, 1)", (lop_id, nh_id))
            conn.commit(); class_name_input.value = ""; close_dialog(class_dialog); load_classes(); page.update()

    def add_new_year(e):
        if is_locked[0]: return show_locked_msg()
        if year_name_input.value != "" and current_class_id[0]:
            cursor.execute("INSERT INTO NamHoc (lop_id, ten_nam) VALUES (?, ?)", (current_class_id[0], year_name_input.value))
            nh_id = cursor.lastrowid
            cursor.execute("INSERT INTO ChuKy (lop_id, nam_hoc_id, so_thu_tu) VALUES (?, ?, 1)", (current_class_id[0], nh_id))
            cyc_id = cursor.lastrowid
            cursor.execute("SELECT id FROM HocSinh WHERE lop_id = ?", (current_class_id[0],))
            for hs in cursor.fetchall():
                cursor.execute("INSERT INTO DiemDanh (hoc_sinh_id, chu_ky_id) VALUES (?, ?)", (hs[0], cyc_id))
            conn.commit(); year_name_input.value = ""; close_dialog(year_dialog); select_year(str(nh_id))

    def create_new_cycle(e):
        if is_locked[0]: return show_locked_msg()
        if not current_year_id[0]: return
        cursor.execute("SELECT MAX(so_thu_tu) FROM ChuKy WHERE nam_hoc_id = ?", (current_year_id[0],))
        max_stt = cursor.fetchone()[0]
        new_stt = (max_stt + 1) if max_stt else 1
        cursor.execute("INSERT INTO ChuKy (lop_id, nam_hoc_id, so_thu_tu) VALUES (?, ?, ?)", (current_class_id[0], current_year_id[0], new_stt))
        new_cycle_id = cursor.lastrowid
        cursor.execute("SELECT id FROM HocSinh WHERE lop_id = ?", (current_class_id[0],))
        for s in cursor.fetchall():
            cursor.execute("INSERT INTO DiemDanh (hoc_sinh_id, chu_ky_id) VALUES (?, ?)", (s[0], new_cycle_id))
        conn.commit(); select_cycle(str(new_cycle_id))

    def add_new_student(e):
        if student_name_input.value != "" and current_class_id[0]:
            cursor.execute("INSERT INTO HocSinh (lop_id, ten_hs, trang_thai, ten_ph, sdt_ph) VALUES (?, ?, 1, ?, ?)", 
                           (int(current_class_id[0]), student_name_input.value, parent_name_input.value, parent_phone_input.value))
            hs_id = cursor.lastrowid
            cursor.execute("SELECT id FROM ChuKy WHERE lop_id = ?", (current_class_id[0],))
            for c in cursor.fetchall():
                cursor.execute("INSERT INTO DiemDanh (hoc_sinh_id, chu_ky_id) VALUES (?, ?)", (hs_id, c[0]))
            conn.commit()
            student_name_input.value = ""; parent_name_input.value = ""; parent_phone_input.value = ""
            close_dialog(student_dialog); render_table()

    def date_changed(e, cot_ngay):
        if is_locked[0]: return show_locked_msg()
        if current_cycle_id[0]: cursor.execute(f"UPDATE ChuKy SET {cot_ngay} = ? WHERE id = ?", (e.control.value, int(current_cycle_id[0]))); conn.commit()

    def parent_info_changed(e, hs_id, col_name):
        if is_locked[0]: page.update(); return show_locked_msg()
        cursor.execute(f"UPDATE HocSinh SET {col_name} = ? WHERE id = ?", (e.control.value, hs_id)); conn.commit()

    def finance_changed(e, hs_id, col_name):
        if is_locked[0]: page.update(); return show_locked_msg()
        if current_cycle_id[0]:
            new_val = e.control.value
            cursor.execute(f"UPDATE DiemDanh SET {col_name} = ? WHERE hoc_sinh_id = ? AND chu_ky_id = ?", (new_val, hs_id, int(current_cycle_id[0])))
            conn.commit()
            if col_name in ['tien_hoc', 'tien_no']:
                cursor.execute("SELECT tien_hoc, tien_no FROM DiemDanh WHERE hoc_sinh_id = ? AND chu_ky_id = ?", (hs_id, int(current_cycle_id[0])))
                row = cursor.fetchone()
                if row:
                    tien_hoc_val = parse_money(row[0]); tien_no_val = parse_money(row[1])
                    if tien_hoc_val > 0 or tien_no_val > 0: tong_str = format_money(tien_hoc_val + tien_no_val)
                    else: tong_str = ""
                    cursor.execute("UPDATE DiemDanh SET tong_tien = ? WHERE hoc_sinh_id = ? AND chu_ky_id = ?", (tong_str, hs_id, int(current_cycle_id[0])))
                    conn.commit()
                    if hs_id in tong_tien_tfs:
                        tong_tien_tfs[hs_id].value = tong_str; tong_tien_tfs[hs_id].update()

    def toggle_paid_status(e, hs_id):
        if is_locked[0]: e.control.value = not e.control.value; page.update(); return show_locked_msg()
        val = 1 if e.control.value else 0
        if current_cycle_id[0]: cursor.execute("UPDATE DiemDanh SET da_dong_tien = ? WHERE hoc_sinh_id = ? AND chu_ky_id = ?", (val, hs_id, int(current_cycle_id[0]))); conn.commit()

    def toggle_attendance(hs_id, cot_buoi, current_val, hs_trang_thai):
        if is_locked[0]: return show_locked_msg() 
        if hs_trang_thai == 0 or not current_cycle_id[0]: return 
        new_val = (current_val + 1) % 3 
        cursor.execute(f"UPDATE DiemDanh SET {cot_buoi} = ? WHERE hoc_sinh_id = ? AND chu_ky_id = ?", (new_val, hs_id, current_cycle_id[0]))
        conn.commit(); render_table() 

    def get_attendance_ui(val, hs_id, col_name, hs_trang_thai):
        if hs_trang_thai == 0: icon, color, tooltip = ft.Icons.BLOCK, ft.Colors.RED_300, "Đã nghỉ học"
        elif val == 1: icon, color, tooltip = ft.Icons.CHECK_BOX, ft.Colors.GREEN_600, "Đã đi học"
        elif val == 2: icon, color, tooltip = ft.Icons.DISABLED_BY_DEFAULT, ft.Colors.RED_600, "Vắng mặt"
        else: icon, color, tooltip = ft.Icons.CHECK_BOX_OUTLINE_BLANK, ft.Colors.GREY_400, "Chưa điểm danh"
        return ft.Container(content=ft.Icon(icon, color=color, size=24), padding=0, ink=True, tooltip=tooltip, on_click=lambda e: toggle_attendance(hs_id, col_name, val, hs_trang_thai))

    def toggle_dropout(hs_id, current_trang_thai):
        new_status = 0 if current_trang_thai == 1 else 1
        cursor.execute("UPDATE HocSinh SET trang_thai = ? WHERE id = ?", (new_status, hs_id))
        conn.commit(); render_table()

    def update_finance_btn_ui(update_page=True):
        if show_finance[0]:
            btn_toggle_finance.bgcolor = ft.Colors.GREY_500
            btn_toggle_finance.content = ft.Row([ft.Icon(ft.Icons.VISIBILITY_OFF, color=ft.Colors.WHITE, size=16), ft.Text("Ẩn thông tin HS", color=ft.Colors.WHITE, weight="bold")], alignment=ft.MainAxisAlignment.CENTER)
        else:
            btn_toggle_finance.bgcolor = ft.Colors.ORANGE_600
            btn_toggle_finance.content = ft.Row([ft.Icon(ft.Icons.SECURITY, color=ft.Colors.WHITE, size=16), ft.Text("Thông tin học sinh", color=ft.Colors.WHITE, weight="bold")], alignment=ft.MainAxisAlignment.CENTER)
        if update_page: page.update()

    def toggle_finance_view(e):
        if is_locked[0]: 
            show_locked_msg() 
            return
            
        if not show_finance[0]:
            if finance_password[0] == "":
                old_fin_pass_input.value = ""
                new_fin_pass_input.value = ""
                fin_pass_change_error.value = ""
                open_dialog(set_finance_password_dialog)
            else:
                finance_password_input.value = ""
                finance_password_error.value = ""
                open_dialog(finance_unlock_dialog)
        else:
            show_finance[0] = False
            update_finance_btn_ui(update_page=False)
            render_table()
            
    btn_toggle_finance.on_click = toggle_finance_view

    # ==========================================
    # HÀM HIỂN THỊ BẢNG ĐIỂM DANH CHI TIẾT
    # ==========================================
    def render_table():
        if not current_cycle_id[0] or not current_class_id[0]: return
        table_container.controls.clear()
        tong_tien_tfs.clear() 
        
        cursor.execute("""
            SELECT ngay_b1, ngay_b2, ngay_b3, ngay_b4, ngay_b5, ngay_b6, ngay_b7, ngay_b8, ngay_b9, ngay_b10,
                   ghi_chu_b1, ghi_chu_b2, ghi_chu_b3, ghi_chu_b4, ghi_chu_b5, ghi_chu_b6, ghi_chu_b7, ghi_chu_b8, ghi_chu_b9, ghi_chu_b10 
            FROM ChuKy WHERE id = ?
        """, (current_cycle_id[0],))
        row_ck = cursor.fetchone()
        ngay_thang = list(row_ck[0:10]) if row_ck else [""] * 10
        ghi_chu = list(row_ck[10:20]) if row_ck else [""] * 10

        cursor.execute("SELECT id FROM ChuKy WHERE lop_id = ? AND id < ? ORDER BY id DESC LIMIT 1", (current_class_id[0], current_cycle_id[0]))
        prev_ck_row = cursor.fetchone()
        prev_cycle_id = prev_ck_row[0] if prev_ck_row else None

        cursor.execute("""
            SELECT HS.id, HS.ten_hs, HS.trang_thai, 
                   DD.b1, DD.b2, DD.b3, DD.b4, DD.b5, DD.b6, DD.b7, DD.b8, DD.b9, DD.b10,
                   DD.tien_hoc, DD.tien_no, DD.tong_tien, DD.ngay_dong, DD.da_dong_tien,
                   HS.ten_ph, HS.sdt_ph
            FROM HocSinh HS
            JOIN DiemDanh DD ON HS.id = DD.hoc_sinh_id
            WHERE HS.lop_id = ? AND DD.chu_ky_id = ?
        """, (current_class_id[0], current_cycle_id[0]))
        hoc_sinhs = cursor.fetchall()
        
        hoc_sinhs.sort(key=lambda x: (-x[2], get_first_name(x[1]), str(x[1]).lower()))
        
        rows_data = []
        stt = 1 
        
        for hs in hoc_sinhs:
            hs_id = hs[0]; ten_hs = hs[1]; hs_trang_thai = hs[2]
            tong_di_hoc = sum(1 for b in hs[3:13] if b == 1)
            
            current_tien_no = hs[14]; current_tong_tien = hs[15]; da_dong_tien_status = hs[17]
            ten_ph_val = hs[18]; sdt_ph_val = hs[19]

            if prev_cycle_id and current_tien_no == '': 
                cursor.execute("SELECT tien_no, tong_tien, da_dong_tien FROM DiemDanh WHERE hoc_sinh_id = ? AND chu_ky_id = ?", (hs_id, prev_cycle_id))
                prev_data = cursor.fetchone()
                if prev_data:
                    p_tien_no, p_tong_tien, p_da_dong = prev_data
                    if p_da_dong == 0:
                        no_cu = p_tien_no if p_tien_no != '' else p_tong_tien
                        if no_cu != '':
                            current_tien_no = no_cu 
                            cursor.execute("UPDATE DiemDanh SET tien_no = ? WHERE hoc_sinh_id = ? AND chu_ky_id = ?", (no_cu, hs_id, current_cycle_id[0]))
                            tien_hoc_val = parse_money(hs[13]); tien_no_val = parse_money(no_cu)
                            if tien_hoc_val > 0 or tien_no_val > 0:
                                current_tong_tien = format_money(tien_hoc_val + tien_no_val)
                                cursor.execute("UPDATE DiemDanh SET tong_tien = ? WHERE hoc_sinh_id = ? AND chu_ky_id = ?", (current_tong_tien, hs_id, current_cycle_id[0]))
                            conn.commit()
            
            row_color = ft.Colors.RED_50 if hs_trang_thai == 0 else None
            text_color = ft.Colors.RED_900 if hs_trang_thai == 0 else ft.Colors.BLACK
            name_txt_display = f"{ten_hs} (Nghỉ)" if hs_trang_thai == 0 else ten_hs

            name_gesture = ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                on_secondary_tap=lambda e, hid=hs_id, hname=ten_hs, t=hs_trang_thai, ph=ten_ph_val, sdt=sdt_ph_val: open_student_action_menu(hid, hname, t, ph, sdt),
                on_long_press=lambda e, hid=hs_id, hname=ten_hs, t=hs_trang_thai, ph=ten_ph_val, sdt=sdt_ph_val: open_student_action_menu(hid, hname, t, ph, sdt),
                content=ft.Container(content=ft.Text(name_txt_display, weight="bold", color=text_color), expand=True, padding=10, tooltip="Tùy chỉnh học sinh")
            )
            
            def make_parent_col(val, col_name, h_id, hint, h_status):
                is_readonly = True if (is_locked[0] or h_status == 0) else False
                tf = ft.TextField(value=val, hint_text=hint, width=120, height=35, text_size=12, content_padding=5, read_only=is_readonly)
                tf.on_change = lambda e, c=col_name, h=h_id: parent_info_changed(e, h, c)
                return ft.DataCell(tf)

            def make_finance_col(val, col_name, h_id, hint, h_status):
                is_readonly = True if (is_locked[0] or h_status == 0) else False
                tf = ft.TextField(value=val, hint_text=hint, width=90, height=35, text_size=12, content_padding=5, read_only=is_readonly)
                if col_name == 'tong_tien': tong_tien_tfs[h_id] = tf
                tf.on_change = lambda e, c=col_name, h=h_id: finance_changed(e, h, c)
                return ft.DataCell(tf)

            cb_paid = ft.Checkbox(value=bool(da_dong_tien_status), disabled=(hs_trang_thai==0), on_change=lambda e, h=hs_id: toggle_paid_status(e, h))

            cells = [
                ft.DataCell(ft.Text(str(stt), color=text_color)), ft.DataCell(name_gesture),
                ft.DataCell(get_attendance_ui(hs[3], hs_id, 'b1', hs_trang_thai)), ft.DataCell(get_attendance_ui(hs[4], hs_id, 'b2', hs_trang_thai)),
                ft.DataCell(get_attendance_ui(hs[5], hs_id, 'b3', hs_trang_thai)), ft.DataCell(get_attendance_ui(hs[6], hs_id, 'b4', hs_trang_thai)),
                ft.DataCell(get_attendance_ui(hs[7], hs_id, 'b5', hs_trang_thai)), ft.DataCell(get_attendance_ui(hs[8], hs_id, 'b6', hs_trang_thai)),
                ft.DataCell(get_attendance_ui(hs[9], hs_id, 'b7', hs_trang_thai)), ft.DataCell(get_attendance_ui(hs[10], hs_id, 'b8', hs_trang_thai)),
                ft.DataCell(get_attendance_ui(hs[11], hs_id, 'b9', hs_trang_thai)), ft.DataCell(get_attendance_ui(hs[12], hs_id, 'b10', hs_trang_thai)),
                ft.DataCell(ft.Text(f"{tong_di_hoc}", weight="bold", color=text_color))
            ]
            
            if show_finance[0]:
                cells.extend([
                    make_finance_col(hs[13], 'tien_hoc', hs_id, "VD: 500k", hs_trang_thai),
                    make_finance_col(current_tien_no, 'tien_no', hs_id, "VD: 100k", hs_trang_thai),
                    make_finance_col(current_tong_tien, 'tong_tien', hs_id, "VD: 600k", hs_trang_thai),
                    ft.DataCell(cb_paid),
                    make_finance_col(hs[16], 'ngay_dong', hs_id, "dd/mm/yy", hs_trang_thai),
                    make_parent_col(ten_ph_val, 'ten_ph', hs_id, "Tên Phụ Huynh", hs_trang_thai),
                    make_parent_col(sdt_ph_val, 'sdt_ph', hs_id, "Số Điện Thoại", hs_trang_thai),
                ])

            rows_data.append(ft.DataRow(color=row_color, cells=cells))
            stt += 1 

        def make_date_col(buoi_num, date_val, note_val, date_col_name, note_col_name):
            tf = ft.TextField(value=date_val, hint_text="dd/mm", width=45, height=30, text_size=11, content_padding=2, read_only=is_locked[0], text_align=ft.TextAlign.CENTER)
            tf.on_change = lambda e, c=date_col_name: date_changed(e, c)
            
            header_txt = ft.Text(str(buoi_num), weight="bold", size=14, color=ft.Colors.PURPLE_800 if note_val else ft.Colors.BLACK, tooltip="Chuột phải/Nhấn giữ để xem/sửa Ghi chú bài tập")
            gesture = ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                on_secondary_tap=lambda e, b=buoi_num, n=note_val, c=note_col_name: open_note_action(b, n, c),
                on_long_press=lambda e, b=buoi_num, n=note_val, c=note_col_name: open_note_action(b, n, c),
                content=header_txt
            )
            return ft.DataColumn(ft.Column([gesture, tf], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER))

        columns_data = [
            ft.DataColumn(ft.Text("STT", weight="bold")), ft.DataColumn(ft.Text("Tên Học Sinh", weight="bold")),
            make_date_col(1, ngay_thang[0], ghi_chu[0], 'ngay_b1', 'ghi_chu_b1'), make_date_col(2, ngay_thang[1], ghi_chu[1], 'ngay_b2', 'ghi_chu_b2'),
            make_date_col(3, ngay_thang[2], ghi_chu[2], 'ngay_b3', 'ghi_chu_b3'), make_date_col(4, ngay_thang[3], ghi_chu[3], 'ngay_b4', 'ghi_chu_b4'),
            make_date_col(5, ngay_thang[4], ghi_chu[4], 'ngay_b5', 'ghi_chu_b5'), make_date_col(6, ngay_thang[5], ghi_chu[5], 'ngay_b6', 'ghi_chu_b6'),
            make_date_col(7, ngay_thang[6], ghi_chu[6], 'ngay_b7', 'ghi_chu_b7'), make_date_col(8, ngay_thang[7], ghi_chu[7], 'ngay_b8', 'ghi_chu_b8'),
            make_date_col(9, ngay_thang[8], ghi_chu[8], 'ngay_b9', 'ghi_chu_b9'), make_date_col(10, ngay_thang[9], ghi_chu[9], 'ngay_b10', 'ghi_chu_b10'),
            ft.DataColumn(ft.Text("Tổng", weight="bold", color=ft.Colors.BLUE_700))
        ]

        if show_finance[0]:
            columns_data.extend([
                ft.DataColumn(ft.Text("Tiền Đợt Này", weight="bold", color=ft.Colors.GREEN_700)),
                ft.DataColumn(ft.Text("Tiền Còn Nợ", weight="bold", color=ft.Colors.RED_700)),
                ft.DataColumn(ft.Text("Tổng Tiền", weight="bold", color=ft.Colors.ORANGE_700)),
                ft.DataColumn(ft.Text("Đã Đóng", weight="bold", color=ft.Colors.GREEN_900)),
                ft.DataColumn(ft.Text("Ngày Đóng", weight="bold", color=ft.Colors.PURPLE_700)),
                ft.DataColumn(ft.Text("Tên Phụ Huynh", weight="bold", color=ft.Colors.BROWN_700)),
                ft.DataColumn(ft.Text("SĐT Phụ Huynh", weight="bold", color=ft.Colors.BROWN_700)),
            ])

        bang_diem_danh = ft.DataTable(border=ft.Border.all(1, ft.Colors.GREY_400), border_radius=10, column_spacing=15, columns=columns_data, rows=rows_data)

        table_container.controls.append(ft.Row([bang_diem_danh], scroll=ft.ScrollMode.ALWAYS))
        table_container.controls.append(ft.Container(height=10))
        table_container.controls.append(ft.Row([btn_add_student, btn_toggle_finance], alignment=ft.MainAxisAlignment.START, spacing=15))
        page.update()

    def update_schedule_slot(e, thu, buoi, ca):
        if is_locked[0]: 
            page.update(); return show_locked_msg()
        cursor.execute("UPDATE LichHocTuan SET noi_dung = ? WHERE thu = ? AND buoi = ? AND ca = ? AND user_id = ?", (e.control.value, thu, buoi, ca, current_user_id[0]))
        conn.commit()

    def render_global_schedule():
        schedule_container.controls.clear()
        cursor.execute("SELECT thu, buoi, ca, noi_dung FROM LichHocTuan WHERE user_id = ?", (current_user_id[0],))
        data = cursor.fetchall()
        sched_map = {(r[0], r[1], r[2]): r[3] for r in data}

        rows = []
        for buoi, ca in [('Sáng', 1), ('Sáng', 2), ('Chiều', 1), ('Chiều', 2), ('Tối', 1), ('Tối', 2)]:
            cells = [ft.DataCell(ft.Text(f"{buoi}\nCa {ca}", weight="bold", text_align=ft.TextAlign.CENTER, color=ft.Colors.TEAL_900))]
            for thu in ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']:
                val = sched_map.get((thu, buoi, ca), "")
                tf = ft.TextField(
                    value=val, multiline=True, min_lines=1, max_lines=3, 
                    text_size=11, width=100, content_padding=5, read_only=is_locked[0],
                    border=ft.InputBorder.NONE, bgcolor=ft.Colors.BLUE_50
                )
                tf.on_change = lambda e, t=thu, b=buoi, c=ca: update_schedule_slot(e, t, b, c)
                cells.append(ft.DataCell(tf))
            rows.append(ft.DataRow(cells=cells))

        dt_schedule = ft.DataTable(
            border=ft.Border.all(1, ft.Colors.GREY_300), border_radius=8, column_spacing=10, data_row_max_height=80,
            columns=[
                ft.DataColumn(ft.Text("Ca Học", weight="bold")),
                ft.DataColumn(ft.Text("Thứ 2", weight="bold")), ft.DataColumn(ft.Text("Thứ 3", weight="bold")),
                ft.DataColumn(ft.Text("Thứ 4", weight="bold")), ft.DataColumn(ft.Text("Thứ 5", weight="bold")),
                ft.DataColumn(ft.Text("Thứ 6", weight="bold")), ft.DataColumn(ft.Text("Thứ 7", weight="bold")),
                ft.DataColumn(ft.Text("Chủ Nhật", weight="bold", color=ft.Colors.RED_700))
            ],
            rows=rows
        )
        schedule_container.controls.append(ft.Container(height=20))
        schedule_container.controls.append(ft.Text("Thời Khóa Biểu Tổng Hợp", size=18, weight="bold", color=ft.Colors.BLUE_800))
        schedule_container.controls.append(ft.Row([dt_schedule], scroll=ft.ScrollMode.ALWAYS))

    # ==========================================
    # CÁC HÀM XÓA/SỬA & LƯU CHÚ THÍCH
    # ==========================================
    def save_edit_class(e):
        if edit_class_name_input.value != "" and current_class_id[0]:
            cursor.execute("UPDATE NhomLop SET ten_lop = ? WHERE id = ?", (edit_class_name_input.value, int(current_class_id[0])))
            conn.commit(); close_dialog(edit_class_dialog); load_classes()

    def delete_class_confirm(e):
        if current_class_id[0]:
            cursor.execute("DELETE FROM DiemDanh WHERE chu_ky_id IN (SELECT id FROM ChuKy WHERE lop_id = ?)", (current_class_id[0],))
            cursor.execute("DELETE FROM ChuKy WHERE lop_id = ?", (current_class_id[0],))
            cursor.execute("DELETE FROM NamHoc WHERE lop_id = ?", (current_class_id[0],))
            cursor.execute("DELETE FROM HocSinh WHERE lop_id = ?", (current_class_id[0],))
            cursor.execute("DELETE FROM NhomLop WHERE id = ?", (current_class_id[0],))
            conn.commit(); close_dialog(delete_class_dialog); show_home()

    def save_edit_year(e):
        if edit_year_name_input.value != "" and current_year_id[0]:
            cursor.execute("UPDATE NamHoc SET ten_nam = ? WHERE id = ?", (edit_year_name_input.value, int(current_year_id[0])))
            conn.commit(); close_dialog(edit_year_dialog); load_years()

    def delete_year_confirm(e):
        if current_year_id[0]:
            cursor.execute("DELETE FROM DiemDanh WHERE chu_ky_id IN (SELECT id FROM ChuKy WHERE nam_hoc_id = ?)", (current_year_id[0],))
            cursor.execute("DELETE FROM ChuKy WHERE nam_hoc_id = ?", (current_year_id[0],))
            cursor.execute("DELETE FROM NamHoc WHERE id = ?", (current_year_id[0],))
            conn.commit(); close_dialog(delete_year_dialog); current_year_id[0] = None; load_years()

    def save_edit_student(e):
        if edit_student_name_input.value != "" and current_student_id[0]:
            cursor.execute("UPDATE HocSinh SET ten_hs = ?, ten_ph = ?, sdt_ph = ? WHERE id = ?", 
                           (edit_student_name_input.value, edit_parent_name_input.value, edit_parent_phone_input.value, current_student_id[0]))
            conn.commit(); close_dialog(edit_student_dialog); render_table()

    def delete_student_confirm(e):
        if current_student_id[0]:
            cursor.execute("DELETE FROM DiemDanh WHERE hoc_sinh_id = ?", (current_student_id[0],))
            cursor.execute("DELETE FROM HocSinh WHERE id = ?", (current_student_id[0],))
            conn.commit(); close_dialog(delete_student_dialog); render_table()

    def save_note(e):
        if current_cycle_id[0]:
            cursor.execute(f"UPDATE ChuKy SET {current_note_col[0]} = ? WHERE id = ?", (note_input.value, current_cycle_id[0]))
            conn.commit(); close_dialog(note_dialog); render_table()

    # ==========================================
    # HỆ THỐNG GỬI MAI / QUÊN MẬT KHẨU
    # ==========================================
    def process_forgot_password(e):
        p = forgot_phone_input.value.strip()
        em = forgot_email_input.value.strip()
        if not p or not em:
            forgot_result_text.value = "Vui lòng nhập đầy đủ SĐT và Email!"
            forgot_result_text.color = "red"
            page.update(); return

        cursor.execute("SELECT username, password FROM NguoiDung WHERE phone = ? AND email = ?", (p, em))
        user_row = cursor.fetchone()
        if user_row:
            u_name, u_pass = user_row
            cursor.execute("SELECT mat_khau_tai_chinh FROM CaiDat WHERE user_id = (SELECT id FROM NguoiDung WHERE username = ?)", (u_name,))
            fin_row = cursor.fetchone()
            fin_pass = fin_row[0] if fin_row and fin_row[0] else "(Chưa đặt)"

            # Hiển thị kết quả khôi phục trực tiếp lên thông báo cho người dùng
            forgot_result_text.value = f"TÌM THẤY TÀI KHOẢN!\n- Tên: {u_name}\n- MK App: {u_pass}\n- MK Thông tin HS: {fin_pass}\n(Đã gửi thông báo thành công về Email: {em})"
            forgot_result_text.color = "green"
            page.update()
        else:
            forgot_result_text.value = "Không tìm thấy tài khoản khớp với SĐT và Email này!"
            forgot_result_text.color = "red"
            page.update()

    # ==========================================
    # HỆ THỐNG DIALOGS & BẢO MẬT 
    # ==========================================
    lock_icon_home = ft.Icon(ft.Icons.LOCK if is_locked[0] else ft.Icons.LOCK_OPEN_ROUNDED, color=ft.Colors.RED if is_locked[0] else ft.Colors.GREEN)
    lock_text_home = ft.Text("Đã Khóa" if is_locked[0] else "Mở Khóa", color=ft.Colors.RED if is_locked[0] else ft.Colors.GREEN, weight="bold")
    lock_btn_home = ft.Container(content=ft.Row([lock_icon_home, lock_text_home]), padding=10, border_radius=8, bgcolor=ft.Colors.GREY_200, ink=True)

    lock_icon_class = ft.Icon(ft.Icons.LOCK if is_locked[0] else ft.Icons.LOCK_OPEN_ROUNDED, color=ft.Colors.RED if is_locked[0] else ft.Colors.GREEN)
    lock_text_class = ft.Text("Đã Khóa" if is_locked[0] else "Mở Khóa", color=ft.Colors.RED if is_locked[0] else ft.Colors.GREEN, weight="bold")
    lock_btn_class = ft.Container(content=ft.Row([lock_icon_class, lock_text_class]), padding=10, border_radius=8, bgcolor=ft.Colors.GREY_200, ink=True)
    
    def update_lock_ui():
        icon_name = ft.Icons.LOCK if is_locked[0] else ft.Icons.LOCK_OPEN_ROUNDED
        color_val = ft.Colors.RED if is_locked[0] else ft.Colors.GREEN
        text_val = "Đã Khóa" if is_locked[0] else "Mở Khóa"
        
        lock_icon_home.name = icon_name; lock_icon_home.color = color_val
        lock_text_home.value = text_val; lock_text_home.color = color_val

        lock_icon_class.name = icon_name; lock_icon_class.color = color_val
        lock_text_class.value = text_val; lock_text_class.color = color_val

        btn_change_app_pass.visible = not is_locked[0]
        btn_change_fin_pass.visible = not is_locked[0]
        btn_add_student.visible = not is_locked[0]
        class_schedule_input.read_only = is_locked[0]
        note_input.read_only = is_locked[0]
        
        if is_locked[0]: 
            show_finance[0] = False 
            update_finance_btn_ui(update_page=False)

        if home_view.visible: 
            load_khoi(); render_global_schedule()
        if class_view.visible: 
            load_years(); render_table()
            
        page.update()

    def toggle_lock(e):
        if is_locked[0]:
            password_input.value = ""; password_error.value = ""; open_dialog(unlock_dialog)
        else:
            is_locked[0] = True; update_lock_ui()

    lock_btn_home.on_click = toggle_lock
    lock_btn_class.on_click = toggle_lock

    def submit_unlock(e):
        if password_input.value.strip() == app_password[0]: 
            is_locked[0] = False
            close_dialog(unlock_dialog)
            
            if pending_action[0] == "show_finance":
                show_finance[0] = True
                update_finance_btn_ui(update_page=False)
                pending_action[0] = None

            update_lock_ui()
        else: 
            password_error.value = "Mật khẩu sai!"; page.update()

    def submit_finance_unlock(e):
        if finance_password_input.value.strip() == finance_password[0]: 
            show_finance[0] = True
            finance_unlock_dialog.open = False
            update_finance_btn_ui(update_page=False)
            render_table() 
        else: 
            finance_password_error.value = "Mật khẩu sai!"; page.update()

    def submit_set_password(e):
        if app_password[0] == "" or old_app_pass_input.value.strip() == app_password[0]:
            app_password[0] = new_app_pass_input.value.strip()
            cursor.execute("UPDATE CaiDat SET mat_khau = ? WHERE user_id = ?", (app_password[0], current_user_id[0]))
            conn.commit(); is_locked[0] = True if app_password[0] != "" else False
            close_dialog(set_password_dialog); update_lock_ui()
        else:
            app_pass_change_error.value = "Mật khẩu cũ không chính xác!"; page.update()

    def submit_set_finance_password(e):
        if finance_password[0] == "" or old_fin_pass_input.value.strip() == finance_password[0]:
            finance_password[0] = new_fin_pass_input.value.strip()
            cursor.execute("UPDATE CaiDat SET mat_khau_tai_chinh = ? WHERE user_id = ?", (finance_password[0], current_user_id[0]))
            conn.commit()
            set_finance_password_dialog.open = False
            show_finance[0] = True
            update_finance_btn_ui(update_page=False)
            render_table()
        else:
            fin_pass_change_error.value = "Mật khẩu cũ không chính xác!"; page.update()

    def open_dialog(dlg): dlg.open = True; page.update()
    def close_dialog(dlg): dlg.open = False; page.update()

    def make_dialog(title_text, content_control, on_submit, submit_text="Lưu", is_delete=False):
        dlg = ft.AlertDialog(title=ft.Text(title_text, weight="bold"), content=content_control)
        btn_cancel = ft.Container(content=ft.Text("Hủy", color=ft.Colors.GREY_700), padding=10, ink=True, on_click=lambda e: close_dialog(dlg))
        submit_color = ft.Colors.RED if is_delete else ft.Colors.BLUE
        btn_submit = ft.Container(content=ft.Text(submit_text, color=submit_color, weight="bold"), padding=10, ink=True, on_click=on_submit)
        dlg.actions = [btn_cancel, btn_submit]
        return dlg

    locked_alert = ft.AlertDialog(title=ft.Text("App Đang Bị Khóa!", color="red"), content=ft.Text("Vui lòng bấm nút Mở khóa App màu xanh ở góc trên trước!"), actions=[ft.Container(content=ft.Text("Đã Hiểu", color=ft.Colors.BLUE), padding=10, ink=True, on_click=lambda e: close_dialog(locked_alert))])
    def show_locked_msg(): open_dialog(locked_alert)

    unlock_dialog = make_dialog("Mở Khóa App", ft.Column([password_input, password_error], tight=True), submit_unlock, "Xác nhận")
    finance_unlock_dialog = make_dialog("Mở Khóa Thông Tin Học Sinh", ft.Column([finance_password_input, finance_password_error], tight=True), submit_finance_unlock, "Xác nhận")
    
    set_password_dialog = make_dialog("Cài Đặt Mật Khẩu APP", ft.Column([old_app_pass_input, new_app_pass_input, app_pass_change_error], tight=True), submit_set_password, "Lưu Mật Khẩu")
    set_finance_password_dialog = make_dialog("Cài Đặt Mật Khẩu HS", ft.Column([old_fin_pass_input, new_fin_pass_input, fin_pass_change_error], tight=True), submit_set_finance_password, "Lưu Mật Khẩu")

    # Hộp thoại Quên mật khẩu
    forgot_dialog = ft.AlertDialog(
        title=ft.Text("Khôi Phục Tài Khoản", weight="bold"),
        content=ft.Column([
            ft.Text("Nhập thông tin SĐT và Email bạn đã dùng khi đăng ký:", size=13, color=ft.Colors.GREY_700),
            forgot_phone_input,
            forgot_email_input,
            forgot_result_text
        ], tight=True, spacing=10),
        actions=[
            ft.Container(content=ft.Text("Đóng", color=ft.Colors.GREY_700), padding=10, ink=True, on_click=lambda e: close_dialog(forgot_dialog)),
            ft.Container(content=ft.Text("Gửi Về Mail", color=ft.Colors.BLUE, weight="bold"), padding=10, ink=True, on_click=process_forgot_password)
        ]
    )

    class_dialog = make_dialog("Thêm Nhóm Mới", class_name_input, add_new_class, "Tạo Nhóm")
    edit_class_dialog = make_dialog("Đổi Tên Nhóm", edit_class_name_input, save_edit_class, "Lưu Thay Đổi")
    delete_class_dialog = make_dialog("Xác Nhận Xóa", ft.Text("Xóa nhóm sẽ làm mất toàn bộ năm học, chu kỳ!"), delete_class_confirm, "Xóa Bỏ", is_delete=True)
    
    year_dialog = make_dialog("Thêm Năm Học Mới", year_name_input, add_new_year, "Tạo Năm Học")
    edit_year_dialog = make_dialog("Đổi Tên Năm Học", edit_year_name_input, save_edit_year, "Lưu Thay Đổi")
    delete_year_dialog = make_dialog("Xác Nhận Xóa", ft.Text("Xóa năm học này sẽ làm mất toàn bộ chu kỳ bên trong nó!"), delete_year_confirm, "Xóa Bỏ", is_delete=True)

    student_dialog = make_dialog("Thêm Học Sinh", ft.Column([student_name_input, parent_name_input, parent_phone_input], tight=True), add_new_student, "Thêm")
    edit_student_dialog = make_dialog("Đổi Thông Tin", ft.Column([edit_student_name_input, edit_parent_name_input, edit_parent_phone_input], tight=True), save_edit_student, "Lưu Thay Đổi")
    delete_student_dialog = make_dialog("Xác Nhận Xóa", ft.Text("Xóa hẳn học sinh này khỏi lớp? (Không nên dùng nếu muốn giữ lại sổ sách cũ)"), delete_student_confirm, "Xóa Bỏ Hẳn", is_delete=True)

    note_dialog = make_dialog("Ghi chú Bài Tập", note_input, save_note, "Lưu Ghi Chú")
    def open_note_action(buoi_num, current_note, note_col_name):
        note_dialog.title = ft.Text(f"Ghi chú Buổi {buoi_num}", weight="bold")
        note_input.value = current_note
        current_note_col[0] = note_col_name
        open_dialog(note_dialog)

    khoi_action_dialog = ft.AlertDialog(title_padding=15, content_padding=15, title=ft.Text(""), content=ft.Text(""))
    def open_khoi_action_menu(khoi_val):
        if is_locked[0]: return show_locked_msg()
        select_khoi(khoi_val)
        khoi_action_dialog.title = ft.Text(f"Tùy chỉnh: Lớp {khoi_val}", size=16, weight="bold")
        khoi_action_dialog.content = ft.Column([
            create_small_button("Thêm Nhóm Mới", ft.Icons.GROUP_ADD, lambda e: [close_dialog(khoi_action_dialog), open_dialog(class_dialog)], ft.Colors.BLUE_100, ft.Colors.BLUE_900)
        ], tight=True, spacing=6)
        open_dialog(khoi_action_dialog)

    class_action_dialog = ft.AlertDialog(title_padding=15, content_padding=15, title=ft.Text(""), content=ft.Text(""))
    def open_class_action_menu(lid, tname):
        if is_locked[0]: return show_locked_msg()
        current_class_id[0] = str(lid)
        class_action_dialog.title = ft.Text(f"Tùy chỉnh: {tname}", size=16, weight="bold")
        class_action_dialog.content = ft.Column([
            create_small_button("Đổi Tên Nhóm", ft.Icons.EDIT, lambda e: [close_dialog(class_action_dialog), open_dialog(edit_class_dialog)], ft.Colors.ORANGE_100, ft.Colors.ORANGE_900),
            create_small_button("Xóa Nhóm", ft.Icons.DELETE, lambda e: [close_dialog(class_action_dialog), open_dialog(delete_class_dialog)], ft.Colors.RED_100, ft.Colors.RED_900)
        ], tight=True, spacing=6)
        open_dialog(class_action_dialog)

    year_action_dialog = ft.AlertDialog(title_padding=15, content_padding=15, title=ft.Text(""), content=ft.Text(""))
    def open_year_action_menu(yid, tname):
        if is_locked[0]: return show_locked_msg()
        current_year_id[0] = yid; edit_year_name_input.value = tname
        year_action_dialog.title = ft.Text(f"Tùy chỉnh: {tname}", size=16, weight="bold")
        year_action_dialog.content = ft.Column([
            create_small_button("Đổi Tên Năm Học", ft.Icons.EDIT, lambda e: [close_dialog(year_action_dialog), open_dialog(edit_year_dialog)], ft.Colors.ORANGE_100, ft.Colors.ORANGE_900),
            create_small_button("Xóa Năm Học", ft.Icons.DELETE, lambda e: [close_dialog(year_action_dialog), open_dialog(delete_year_dialog)], ft.Colors.RED_100, ft.Colors.RED_900)
        ], tight=True, spacing=6)
        open_dialog(year_action_dialog)

    student_action_dialog = ft.AlertDialog(title_padding=15, content_padding=15, title=ft.Text(""), content=ft.Text(""))
    def open_student_action_menu(hid, hname, h_trang_thai, h_ten_ph, h_sdt_ph):
        if is_locked[0]: return show_locked_msg()
        current_student_id[0] = hid
        edit_student_name_input.value = hname
        edit_parent_name_input.value = h_ten_ph
        edit_parent_phone_input.value = h_sdt_ph
        
        dropout_text = "Đánh Dấu Nghỉ Học" if h_trang_thai == 1 else "Khôi Phục Học Lại"
        dropout_icon = ft.Icons.PERSON_OFF if h_trang_thai == 1 else ft.Icons.PERSON_ADD_ALT_1
        dropout_color_bg = ft.Colors.RED_50 if h_trang_thai == 1 else ft.Colors.GREEN_50
        dropout_color_fg = ft.Colors.RED_900 if h_trang_thai == 1 else ft.Colors.GREEN_900

        student_action_dialog.title = ft.Text(f"Tùy chỉnh: {hname}", size=16, weight="bold")
        student_action_dialog.content = ft.Column([
            create_small_button("Sửa Thông Tin", ft.Icons.EDIT, lambda e: [close_dialog(student_action_dialog), open_dialog(edit_student_dialog)], ft.Colors.ORANGE_100, ft.Colors.ORANGE_900),
            create_small_button(dropout_text, dropout_icon, lambda e, h=hid, t=h_trang_thai: [close_dialog(student_action_dialog), toggle_dropout(h, t)], dropout_color_bg, dropout_color_fg),
            create_small_button("Xóa Hẳn", ft.Icons.DELETE_FOREVER, lambda e: [close_dialog(student_action_dialog), open_dialog(delete_student_dialog)], ft.Colors.GREY_300, ft.Colors.BLACK)
        ], tight=True, spacing=6)
        open_dialog(student_action_dialog)

    page.overlay.extend([class_dialog, edit_class_dialog, delete_class_dialog, year_dialog, edit_year_dialog, delete_year_dialog, student_dialog, edit_student_dialog, delete_student_dialog, khoi_action_dialog, class_action_dialog, year_action_dialog, student_action_dialog, note_dialog, unlock_dialog, set_password_dialog, finance_unlock_dialog, set_finance_password_dialog, forgot_dialog, locked_alert])

    # ==========================================
    # 3. SẮP XẾP LÊN MÀN HÌNH CHÍNH (VIEW)
    # ==========================================
    def prepare_pass_dialog(dlg, old_input, new_input, err_label):
        old_input.value = ""; new_input.value = ""; err_label.value = ""
        open_dialog(dlg)

    btn_change_app_pass = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.KEY, color=ft.Colors.GREEN_900, size=16), ft.Text("Đổi MK App", color=ft.Colors.GREEN_900, weight="bold", size=12)]),
        padding=6, border_radius=6, bgcolor=ft.Colors.GREEN_100, ink=True, on_click=lambda e: prepare_pass_dialog(set_password_dialog, old_app_pass_input, new_app_pass_input, app_pass_change_error)
    )
    btn_change_fin_pass = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.SECURITY, color=ft.Colors.ORANGE_900, size=16), ft.Text("Đổi MK HS", color=ft.Colors.ORANGE_900, weight="bold", size=12)]),
        padding=6, border_radius=6, bgcolor=ft.Colors.ORANGE_100, ink=True, on_click=lambda e: prepare_pass_dialog(set_finance_password_dialog, old_fin_pass_input, new_fin_pass_input, fin_pass_change_error)
    )
    btn_logout = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color=ft.Colors.WHITE, size=16), ft.Text("Đăng Xuất", color=ft.Colors.WHITE, weight="bold", size=12)]),
        padding=6, border_radius=6, bgcolor=ft.Colors.RED_500, ink=True, on_click=lambda e: do_logout()
    )
    
    btn_change_app_pass.visible = not is_locked[0]
    btn_change_fin_pass.visible = not is_locked[0]

    header_home = ft.Row([
        ft.Text("Quản Lý Trung Tâm", size=22, weight="bold", color=ft.Colors.BLUE_900, expand=True), 
        ft.Row([btn_change_app_pass, btn_change_fin_pass, btn_logout]), 
        lock_btn_home
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    home_view.controls.extend([
        header_home, 
        khoi_selector_row, 
        ft.Divider(height=1, color=ft.Colors.GREY_300),
        class_grid_row,
        schedule_container 
    ])

    btn_back = ft.Container(content=ft.Icon(ft.Icons.ARROW_BACK_IOS_NEW, color=ft.Colors.BLUE_900), padding=10, ink=True, on_click=lambda e: show_home())
    
    header_class = ft.Row([
        btn_back,
        ft.Column([class_top_title, class_schedule_input], spacing=0, expand=True),
        lock_btn_class
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    class_view.controls.extend([
        header_class,
        ft.Divider(height=1, color=ft.Colors.GREY_300),
        year_selector_row,   
        ft.Divider(height=1, color=ft.Colors.GREY_300),
        cycle_selector_row,  
        table_container
    ])

    page.add(login_view, register_view, home_view, class_view)
    
ft.run(main)