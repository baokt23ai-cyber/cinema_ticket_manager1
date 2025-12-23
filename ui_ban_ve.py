# ui_ban_ve.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import random, string
import os

from ket_noi_db import ket_noi

COLOR_AVAILABLE = "#2ecc71"
COLOR_SOLD = "#e74c3c"
COLOR_SELECTED = "#f1c40f"


def tao_ma_ve():
    return "VE" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def tao_file_ve(noi_dung: str) -> str:
    os.makedirs("ve_da_in", exist_ok=True)
    ten_file = os.path.join("ve_da_in", f"ve_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(ten_file, "w", encoding="utf-8") as f:
        f.write(noi_dung)
    return ten_file


class ManHinhBanVe:
    """
    Bán vé FULL:
    - Suất chiếu đang bán + lọc (keyword phim/phòng + ngày)
    - Sơ đồ ghế + legend màu
    - Thanh toán: tạo hóa đơn, vé, chi tiết hóa đơn, in vé txt
    - Mở 1 lần, lần 2 focus lại
    - Đóng (bấm X) KHÔNG thoát app
    - Có nút Đổi tài khoản (gọi callback on_logout)
    """
    _active_window = None

    def __init__(self, master, nguoi_dung_id: int, on_logout=None):
        self.master = master
        self.nguoi_dung_id = int(nguoi_dung_id)
        self.on_logout = on_logout

        # ===== nếu cửa sổ đang mở thì focus lại =====
        w = ManHinhBanVe._active_window
        if w is not None:
            try:
                if w.winfo_exists():
                    w.deiconify()
                    w.lift()
                    try:
                        w.attributes("-topmost", True)
                        w.attributes("-topmost", False)
                    except Exception:
                        pass
                    w.focus_force()
                    return
            except Exception:
                ManHinhBanVe._active_window = None

        # ===== tạo cửa sổ bán vé =====
        self.win = tk.Toplevel(master)
        ManHinhBanVe._active_window = self.win

        self.win.title("Bán vé xem phim")
        self.win.geometry("1100x680")
        self.win.resizable(True, True)

        self.win.protocol("WM_DELETE_WINDOW", self.on_close)
        self.win.bind("<Destroy>", self._on_destroy)

        self.ds_ghe_chon = {}   # {ghe_id: ma_ghe}
        self.gia_ve = 0.0
        self.ds_suat = []       # list tuples

        # ================== TOP (SỬA LAYOUT 2 DÒNG) ==================
        top = tk.Frame(self.win)
        top.pack(fill="x", padx=10, pady=8)

        # ----- ROW 1: suất chiếu + tải ghế + nút phải -----
        row1 = tk.Frame(top)
        row1.pack(fill="x")

        tk.Label(row1, text="Suất chiếu").pack(side="left")
        self.cb_suat = ttk.Combobox(row1, state="readonly", width=55)
        self.cb_suat.pack(side="left", padx=8)

        tk.Button(row1, text="Tải ghế", command=self.tai_ghe).pack(side="left", padx=(0, 6))
        tk.Button(row1, text="Bỏ chọn", command=self.bo_chon_tat_ca).pack(side="left")

        tk.Button(row1, text="Đóng", command=self.on_close).pack(side="right")
        tk.Button(row1, text="Đổi tài khoản", command=self.logout).pack(side="right", padx=(0, 6))

        # ----- ROW 2: lọc suất -----
        row2 = tk.Frame(top)
        row2.pack(fill="x", pady=(6, 0))

        tk.Label(row2, text="Từ khóa (phim/phòng):").pack(side="left")
        self.e_keyword = tk.Entry(row2, width=22)
        self.e_keyword.pack(side="left", padx=(6, 12))

        tk.Label(row2, text="Ngày (YYYY-MM-DD):").pack(side="left")
        self.e_ngay = tk.Entry(row2, width=12)
        self.e_ngay.pack(side="left", padx=(6, 12))

        tk.Button(row2, text="Áp dụng lọc", width=12, command=self.loc_suat).pack(side="left", padx=(0, 6))
        tk.Button(row2, text="Xóa lọc", width=10, command=self.load_suat).pack(side="left")

        self.win.bind("<Return>", lambda _e: self.loc_suat())

        # ===== MID =====
        mid = tk.Frame(self.win)
        mid.pack(fill="both", expand=True, padx=10, pady=10)

        # LEFT: seats
        self.fr_ghe = tk.LabelFrame(mid, text="Sơ đồ ghế", padx=10, pady=10)
        self.fr_ghe.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # RIGHT: invoice
        right = tk.LabelFrame(mid, text="Hóa đơn", padx=10, pady=10)
        right.pack(side="right", fill="y")

        tk.Label(right, text="Tên khách hàng").pack(anchor="w")
        self.e_ten = tk.Entry(right)
        self.e_ten.pack(fill="x", pady=4)

        tk.Label(right, text="Số điện thoại").pack(anchor="w")
        self.e_sdt = tk.Entry(right)
        self.e_sdt.pack(fill="x", pady=4)

        tk.Label(right, text="Ghế đã chọn").pack(anchor="w", pady=(10, 0))
        self.lb_ds = tk.Listbox(right, height=14)
        self.lb_ds.pack(fill="both", expand=True, pady=6)

        self.lbl_tong = tk.Label(right, text="Tổng tiền: 0 đ", font=("Arial", 11, "bold"))
        self.lbl_tong.pack(pady=6)

        self.btn_thanh_toan = tk.Button(right, text="Thanh toán", command=self.thanh_toan)
        self.btn_thanh_toan.pack(fill="x")

        # SCREEN + LEGEND
        self._build_screen_and_legend()

        # load suất
        self.load_suat()

        # bring front
        self.win.after(50, self._bring_to_front)

    # ================== WINDOW HELPERS ==================
    def _bring_to_front(self):
        try:
            self.win.deiconify()
            self.win.lift()
            try:
                self.win.attributes("-topmost", True)
                self.win.attributes("-topmost", False)
            except Exception:
                pass
            self.win.focus_force()
        except Exception:
            pass

    def _on_destroy(self, _e=None):
        try:
            if ManHinhBanVe._active_window == self.win:
                ManHinhBanVe._active_window = None
        except Exception:
            ManHinhBanVe._active_window = None

    def on_close(self):
        """Đóng bán vé, KHÔNG thoát app. Hiện lại root nếu đang bị withdraw."""
        try:
            if hasattr(self, "win") and self.win.winfo_exists():
                self.win.destroy()
        except Exception:
            pass
        finally:
            ManHinhBanVe._active_window = None

        # hiện lại root để không bị "mất app"
        try:
            self.master.deiconify()
        except Exception:
            pass

    def logout(self):
        """Đổi tài khoản: đóng bán vé rồi gọi callback để quay về login."""
        self.on_close()
        if callable(self.on_logout):
            self.on_logout()

    # ================== UI: SCREEN + LEGEND ==================
    def _build_screen_and_legend(self):
        fr_screen = tk.Frame(self.fr_ghe)
        fr_screen.grid(row=0, column=0, columnspan=30, sticky="ew", pady=(0, 8))
        tk.Label(
            fr_screen, text="MÀN HÌNH",
            bg="black", fg="white",
            font=("Arial", 11, "bold"), height=2
        ).pack(fill="x")

        fr_legend = tk.Frame(self.fr_ghe)
        fr_legend.grid(row=1, column=0, columnspan=30, sticky="w", pady=(0, 8))

        def chip(color, text):
            f = tk.Frame(fr_legend)
            f.pack(side="left", padx=(0, 14))
            tk.Label(f, bg=color, width=3, height=1, relief="ridge", bd=1).pack(side="left")
            tk.Label(f, text=" " + text).pack(side="left")

        chip(COLOR_AVAILABLE, "Ghế trống")
        chip(COLOR_SOLD, "Ghế đã bán")
        chip(COLOR_SELECTED, "Ghế đang chọn")

    # ================== LOAD / FILTER SUẤT ==================
    def _fill_cb_suat(self):
        self.cb_suat["values"] = [
            f"{s[0]} | {s[1]} | {s[2]} | {int(float(s[3])):,}đ"
            for s in self.ds_suat
        ]
        if self.ds_suat:
            self.cb_suat.current(0)
        else:
            self.cb_suat.set("")

    def load_suat(self):
        """Load tất cả suất đang bán (dang_ban)"""
        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self.win)
            return

        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT sc.suat_chieu_id, p.ten_phim, r.ten_phong, sc.gia_ve
                FROM suat_chieu sc
                JOIN phim p ON sc.phim_id = p.phim_id
                JOIN phong_chieu r ON sc.phong_id = r.phong_id
                WHERE sc.trang_thai='dang_ban'
                ORDER BY sc.suat_chieu_id DESC
            """)
            self.ds_suat = cur.fetchall()
        finally:
            try:
                cur.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass

        self._fill_cb_suat()

    def loc_suat(self):
        """Lọc suất đang bán theo keyword và ngày"""
        keyword = self.e_keyword.get().strip()
        ngay = self.e_ngay.get().strip()

        if ngay:
            try:
                datetime.strptime(ngay, "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("Sai định dạng", "Ngày phải YYYY-MM-DD", parent=self.win)
                return

        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self.win)
            return

        cur = conn.cursor()
        try:
            sql = """
                SELECT sc.suat_chieu_id, p.ten_phim, r.ten_phong, sc.gia_ve
                FROM suat_chieu sc
                JOIN phim p ON sc.phim_id = p.phim_id
                JOIN phong_chieu r ON sc.phong_id = r.phong_id
                WHERE sc.trang_thai='dang_ban'
            """
            params = []

            if keyword:
                sql += " AND (p.ten_phim LIKE %s OR r.ten_phong LIKE %s)"
                params.extend([f"%{keyword}%", f"%{keyword}%"])

            if ngay:
                sql += " AND DATE(sc.gio_bat_dau) = %s"
                params.append(ngay)

            sql += " ORDER BY sc.suat_chieu_id DESC"
            cur.execute(sql, params)
            self.ds_suat = cur.fetchall()
        finally:
            try:
                cur.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass

        self._fill_cb_suat()
        if not self.ds_suat:
            messagebox.showinfo("Không có", "Không tìm thấy suất phù hợp.", parent=self.win)

    # ================== HELPERS ==================
    def parse_suat_id(self):
        txt = self.cb_suat.get().strip()
        if not txt:
            return None
        return int(txt.split("|")[0].strip())

    def lay_gia_ve_theo_suat(self, suat_id: int):
        for s in self.ds_suat:
            if s[0] == suat_id:
                return float(s[3])
        return 0.0

    def cap_nhat_hoa_don(self):
        self.lb_ds.delete(0, "end")
        for ma in self.ds_ghe_chon.values():
            self.lb_ds.insert("end", ma)

        tong = len(self.ds_ghe_chon) * self.gia_ve
        self.lbl_tong.config(text=f"Tổng tiền: {int(tong):,} đ")

    def bo_chon_tat_ca(self):
        for w in self.fr_ghe.winfo_children():
            if isinstance(w, tk.Button) and w["state"] != "disabled":
                w.config(bg=COLOR_AVAILABLE)
        self.ds_ghe_chon.clear()
        self.cap_nhat_hoa_don()

    # ================== TẢI GHẾ ==================
    def tai_ghe(self):
        # xóa button ghế cũ (giữ screen + legend vì không phải Button)
        for w in self.fr_ghe.winfo_children():
            if isinstance(w, tk.Button):
                w.destroy()

        self.ds_ghe_chon.clear()
        self.lb_ds.delete(0, "end")
        self.lbl_tong.config(text="Tổng tiền: 0 đ")

        suat_id = self.parse_suat_id()
        if suat_id is None:
            messagebox.showwarning("Thiếu", "Vui lòng chọn suất chiếu.", parent=self.win)
            return

        self.gia_ve = self.lay_gia_ve_theo_suat(suat_id)

        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self.win)
            return

        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT g.ghe_id, g.ma_ghe,
                       CASE WHEN v.ve_id IS NULL THEN 0 ELSE 1 END AS da_ban
                FROM ghe g
                JOIN suat_chieu sc ON g.phong_id = sc.phong_id
                LEFT JOIN ve v
                    ON v.ghe_id = g.ghe_id
                   AND v.suat_chieu_id = sc.suat_chieu_id
                WHERE sc.suat_chieu_id = %s
                ORDER BY g.ma_ghe
            """, (suat_id,))
            ds_ghe = cur.fetchall()
        finally:
            try:
                cur.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass

        cols = 10
        start_row = 2  # 0: screen, 1: legend

        for i, (ghe_id, ma_ghe, da_ban) in enumerate(ds_ghe):
            btn = tk.Button(self.fr_ghe, text=ma_ghe, width=4)
            r, c = divmod(i, cols)
            btn.grid(row=start_row + r, column=c, padx=3, pady=3)

            if da_ban:
                btn.config(state="disabled", bg=COLOR_SOLD)
            else:
                btn.config(bg=COLOR_AVAILABLE)
                btn.config(command=lambda gid=ghe_id, ma=ma_ghe, b=btn: self.chon_ghe(gid, ma, b))

    def chon_ghe(self, ghe_id, ma_ghe, btn):
        if ghe_id in self.ds_ghe_chon:
            del self.ds_ghe_chon[ghe_id]
            btn.config(bg=COLOR_AVAILABLE)
        else:
            self.ds_ghe_chon[ghe_id] = ma_ghe
            btn.config(bg=COLOR_SELECTED)
        self.cap_nhat_hoa_don()

    # ================== THANH TOÁN ==================
    def thanh_toan(self):
        if not self.ds_ghe_chon:
            messagebox.showwarning("Thiếu ghế", "Vui lòng chọn ghế.", parent=self.win)
            return

        suat_id = self.parse_suat_id()
        if suat_id is None:
            messagebox.showwarning("Thiếu", "Vui lòng chọn suất chiếu.", parent=self.win)
            return

        self.btn_thanh_toan.config(state="disabled")

        ten = self.e_ten.get().strip()
        sdt = self.e_sdt.get().strip()

        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self.win)
            self.btn_thanh_toan.config(state="normal")
            return

        cur = conn.cursor()
        try:
            # check suất còn bán
            cur.execute("SELECT trang_thai FROM suat_chieu WHERE suat_chieu_id=%s", (suat_id,))
            row = cur.fetchone()
            if not row or row[0] != "dang_ban":
                raise Exception("Suất chiếu đã ngừng bán. Không thể thanh toán.")

            tong_tien = len(self.ds_ghe_chon) * self.gia_ve

            # tạo hóa đơn
            cur.execute("""
                INSERT INTO hoa_don(nguoi_dung_id, ten_khach_hang, so_dien_thoai, tong_tien)
                VALUES (%s,%s,%s,%s)
            """, (self.nguoi_dung_id, ten or None, sdt or None, tong_tien))
            hoa_don_id = cur.lastrowid

            noi_dung_ve = (
                f"HÓA ĐƠN #{hoa_don_id}\n"
                f"Khách: {ten}\n"
                f"SĐT: {sdt}\n"
                f"Suất chiếu ID: {suat_id}\n\n"
            )

            # tạo vé + chi tiết
            for ghe_id, ma_ghe in self.ds_ghe_chon.items():
                cur.execute("""
                    SELECT ve_id FROM ve
                    WHERE suat_chieu_id=%s AND ghe_id=%s
                    LIMIT 1
                """, (suat_id, ghe_id))
                if cur.fetchone():
                    raise Exception(f"Ghế {ma_ghe} đã được bán! Vui lòng tải ghế lại.")

                ma_ve = tao_ma_ve()
                cur.execute("""
                    INSERT INTO ve(suat_chieu_id, ghe_id, gia, ma_ve)
                    VALUES (%s,%s,%s,%s)
                """, (suat_id, ghe_id, self.gia_ve, ma_ve))
                ve_id = cur.lastrowid

                cur.execute("""
                    INSERT INTO chi_tiet_hoa_don(hoa_don_id, ve_id)
                    VALUES (%s,%s)
                """, (hoa_don_id, ve_id))

                noi_dung_ve += f"Vé {ma_ve} | Ghế {ma_ghe} | {int(self.gia_ve):,}đ\n"

            conn.commit()

            file_ve = tao_file_ve(noi_dung_ve)
            messagebox.showinfo("Thành công", f"Bán vé thành công!\nĐã in vé:\n{file_ve}", parent=self.win)

            self.load_suat()
            self.tai_ghe()

        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            messagebox.showerror("Lỗi", str(e), parent=self.win)
        finally:
            try:
                cur.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
            self.btn_thanh_toan.config(state="normal")
