# ui_dang_nhap.py
import tkinter as tk
from tkinter import messagebox
from ket_noi_db import ket_noi


class ManHinhDangNhap:
    def __init__(self, root):
        self.root = root

        # Ẩn root, chỉ hiện login
        try:
            self.root.withdraw()
        except Exception:
            pass

        self.win = tk.Toplevel(root)
        self.win.title("Quản lý vé xem phim")
        self.win.geometry("560x300")
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self.thoat)

        tk.Label(self.win, text="ĐĂNG NHẬP HỆ THỐNG", font=("Arial", 18, "bold")).pack(pady=(25, 18))

        form = tk.Frame(self.win)
        form.pack(pady=8)

        tk.Label(form, text="Tên đăng nhập", width=14, anchor="w").grid(row=0, column=0, padx=10, pady=8)
        self.e_user = tk.Entry(form, width=30)
        self.e_user.grid(row=0, column=1, padx=10, pady=8)

        tk.Label(form, text="Mật khẩu", width=14, anchor="w").grid(row=1, column=0, padx=10, pady=8)
        self.e_pass = tk.Entry(form, width=30, show="*")
        self.e_pass.grid(row=1, column=1, padx=10, pady=8)

        btns = tk.Frame(self.win)
        btns.pack(pady=18)

        tk.Button(btns, text="Đăng nhập", width=16, command=self.login).pack(side="left", padx=12)
        tk.Button(btns, text="Thoát", width=16, command=self.thoat).pack(side="left", padx=12)

        self.win.bind("<Return>", lambda _e: self.login())
        self.e_user.focus_set()

    def thoat(self):
        try:
            self.win.destroy()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

    def login(self):
        ten_dn = self.e_user.get().strip()
        mat_khau = self.e_pass.get().strip()

        if not ten_dn or not mat_khau:
            messagebox.showwarning("Thiếu", "Vui lòng nhập đủ tài khoản và mật khẩu.", parent=self.win)
            return

        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self.win)
            return

        cur = None
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT nguoi_dung_id, ten_dang_nhap, vai_tro
                FROM nguoi_dung
                WHERE ten_dang_nhap=%s AND mat_khau=%s
                LIMIT 1
            """, (ten_dn, mat_khau))

            u = cur.fetchone()
            if not u:
                messagebox.showerror("Sai", "Sai tài khoản hoặc mật khẩu.", parent=self.win)
                return

            user = {
                "id": int(u["nguoi_dung_id"]),
                "username": u["ten_dang_nhap"],
                "vai_tro": u["vai_tro"],  # 'quan_tri' / 'nhan_vien'
            }

            # Đóng login
            self.win.destroy()

            # Luôn đi qua màn chính (menu)
            from ui_main import ManHinhChinh

            try:
                self.root.deiconify()
            except Exception:
                pass

            ManHinhChinh(self.root, user)

        except Exception as ex:
            messagebox.showerror("Lỗi", str(ex), parent=self.win)
        finally:
            try:
                if cur:
                    cur.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
