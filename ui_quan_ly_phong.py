import tkinter as tk
from tkinter import ttk, messagebox
from ket_noi_db import ket_noi


def tao_danh_sach_ma_ghe(so_hang: int, so_cot: int):
    ds = []
    for r in range(so_hang):
        hang = chr(ord('A') + r)
        for c in range(1, so_cot + 1):
            ds.append(f"{hang}{c}")
    return ds


class ManHinhQuanLyPhong(tk.Frame):
    def __init__(self, master, user: dict | None = None):
        super().__init__(master, padx=12, pady=12)
        self.master = master
        self.user = user or {}

        self.phong_id = None
        self.so_hang = None
        self.so_cot = None

        self._build_ui()
        self.tai_ds()

    def _mb_parent(self):
        try:
            return self.winfo_toplevel()
        except Exception:
            return None

    def _build_ui(self):
        top = tk.Frame(self)
        top.pack(fill="x")

        # ✅ khớp user dict: username/role
        tk.Label(
            top,
            text=f"User: {self.user.get('username','')} | Vai trò: {self.user.get('role','')}",
            font=("Arial", 10, "bold")
        ).pack(side="left")

        tk.Button(top, text="Tải lại", command=self.tai_ds).pack(side="right")

        tk.Label(self, text="QUẢN LÝ PHÒNG CHIẾU", font=("Arial", 16, "bold")).pack(pady=(10, 8))

        form = tk.LabelFrame(self, text="Thông tin phòng", padx=10, pady=10)
        form.pack(fill="x")

        tk.Label(form, text="Tên phòng").grid(row=0, column=0, sticky="w")
        self.e_ten = tk.Entry(form)
        self.e_ten.grid(row=0, column=1, sticky="ew", padx=8, pady=4)

        tk.Label(form, text="Số hàng").grid(row=1, column=0, sticky="w")
        self.e_hang = tk.Entry(form)
        self.e_hang.grid(row=1, column=1, sticky="ew", padx=8, pady=4)

        tk.Label(form, text="Số cột").grid(row=2, column=0, sticky="w")
        self.e_cot = tk.Entry(form)
        self.e_cot.grid(row=2, column=1, sticky="ew", padx=8, pady=4)

        form.grid_columnconfigure(1, weight=1)

        btns = tk.Frame(self)
        btns.pack(fill="x", pady=8)

        tk.Button(btns, text="Thêm phòng", command=self.them_phong).pack(side="left")
        tk.Button(btns, text="Xóa phòng", command=self.xoa_phong).pack(side="left", padx=6)
        tk.Button(btns, text="Tạo ghế tự động", command=self.tao_ghe_tu_dong).pack(side="left")

        cols = ("phong_id", "ten_phong", "so_hang", "so_cot")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=140 if c != "ten_phong" else 260)
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def tai_ds(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self._mb_parent())
            return

        cur = conn.cursor()
        try:
            cur.execute("SELECT phong_id, ten_phong, so_hang, so_cot FROM phong_chieu ORDER BY phong_id DESC;")
            for row in cur.fetchall():
                self.tree.insert("", "end", values=row)
        finally:
            cur.close()
            conn.close()

        self.phong_id = None
        self.so_hang = None
        self.so_cot = None

        self.e_ten.delete(0, "end")
        self.e_hang.delete(0, "end")
        self.e_cot.delete(0, "end")

    def on_select(self, _):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        self.phong_id = int(values[0])
        self.so_hang = int(values[2])
        self.so_cot = int(values[3])

        self.e_ten.delete(0, "end"); self.e_ten.insert(0, values[1])
        self.e_hang.delete(0, "end"); self.e_hang.insert(0, values[2])
        self.e_cot.delete(0, "end"); self.e_cot.insert(0, values[3])

    def them_phong(self):
        ten = self.e_ten.get().strip()
        hang = self.e_hang.get().strip()
        cot = self.e_cot.get().strip()

        if not ten or not hang.isdigit() or not cot.isdigit():
            messagebox.showwarning("Sai dữ liệu", "Nhập tên phòng và số hàng/số cột là số.", parent=self._mb_parent())
            return

        hang = int(hang)
        cot = int(cot)
        if hang <= 0 or cot <= 0 or hang > 26:
            messagebox.showwarning("Sai dữ liệu", "Số hàng >0, số cột >0. Số hàng tối đa 26.", parent=self._mb_parent())
            return

        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self._mb_parent())
            return

        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO phong_chieu(ten_phong, so_hang, so_cot) VALUES (%s,%s,%s)",
                (ten, hang, cot)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Lỗi", str(e), parent=self._mb_parent())
        finally:
            cur.close()
            conn.close()

        self.tai_ds()

    def xoa_phong(self):
        if not self.phong_id:
            messagebox.showinfo("Chưa chọn", "Chọn 1 phòng để xóa.", parent=self._mb_parent())
            return

        if not messagebox.askyesno(
            "Xác nhận",
            "Xóa phòng sẽ mất dữ liệu ghế liên quan. Bạn chắc chắn?",
            parent=self._mb_parent()
        ):
            return

        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self._mb_parent())
            return

        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM ghe WHERE phong_id=%s", (self.phong_id,))
            cur.execute("DELETE FROM phong_chieu WHERE phong_id=%s", (self.phong_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Lỗi", str(e), parent=self._mb_parent())
        finally:
            cur.close()
            conn.close()

        self.tai_ds()

    def tao_ghe_tu_dong(self):
        if not self.phong_id:
            messagebox.showinfo("Chưa chọn", "Chọn 1 phòng để tạo ghế.", parent=self._mb_parent())
            return

        # nếu chưa chọn dòng mà chỉ nhập tay -> lấy từ ô nhập
        hang_txt = self.e_hang.get().strip()
        cot_txt = self.e_cot.get().strip()
        so_hang = self.so_hang if self.so_hang else (int(hang_txt) if hang_txt.isdigit() else None)
        so_cot = self.so_cot if self.so_cot else (int(cot_txt) if cot_txt.isdigit() else None)

        if not so_hang or not so_cot or so_hang <= 0 or so_cot <= 0 or so_hang > 26:
            messagebox.showwarning("Sai dữ liệu", "Số hàng/số cột không hợp lệ (hàng tối đa 26).", parent=self._mb_parent())
            return

        ds_ma = tao_danh_sach_ma_ghe(so_hang, so_cot)

        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self._mb_parent())
            return

        cur = conn.cursor()
        try:
            # xoá ghế cũ rồi tạo lại
            cur.execute("DELETE FROM ghe WHERE phong_id=%s", (self.phong_id,))
            for ma in ds_ma:
                cur.execute(
                    "INSERT INTO ghe(phong_id, ma_ghe, loai_ghe) VALUES (%s,%s,%s)",
                    (self.phong_id, ma, "thuong")
                )
            conn.commit()
            messagebox.showinfo("OK", f"Đã tạo {len(ds_ma)} ghế cho phòng {self.phong_id}.", parent=self._mb_parent())
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Lỗi", str(e), parent=self._mb_parent())
        finally:
            cur.close()
            conn.close()
