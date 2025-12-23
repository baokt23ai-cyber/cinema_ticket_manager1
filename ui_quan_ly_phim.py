import tkinter as tk
from tkinter import ttk, messagebox
from ket_noi_db import ket_noi


class ManHinhQuanLyPhim(tk.Frame):
    """
    Quản lý phim FULL:
    - Danh sách phim (Treeview)
    - Form: tên_phim, thể_loại, thời_lượng_phút, độ_tuổi, trạng_thái
    - Thêm / Cập nhật
    - Ngừng chiếu (soft delete)
    - Xóa: chỉ xóa khi KHÔNG có suất chiếu (CÁCH 1 chống lỗi FK)
    """

    def __init__(self, master, user=None):
        super().__init__(master)
        self.user = user or {}

        self.phim_id = None

        # ====== TITLE ======
        tk.Label(self, text="QUẢN LÝ PHIM", font=("Arial", 16, "bold")).pack(pady=(10, 6))

        # ====== FORM ======
        form = tk.LabelFrame(self, text="Thông tin phim", padx=10, pady=10)
        form.pack(fill="x", padx=10, pady=8)

        tk.Label(form, text="Tên phim").grid(row=0, column=0, sticky="w")
        self.e_ten = tk.Entry(form)
        self.e_ten.grid(row=0, column=1, sticky="ew", padx=8, pady=4)

        tk.Label(form, text="Thể loại").grid(row=1, column=0, sticky="w")
        self.e_the_loai = tk.Entry(form)
        self.e_the_loai.grid(row=1, column=1, sticky="ew", padx=8, pady=4)

        tk.Label(form, text="Thời lượng (phút)").grid(row=2, column=0, sticky="w")
        self.e_thoi_luong = tk.Entry(form)
        self.e_thoi_luong.grid(row=2, column=1, sticky="ew", padx=8, pady=4)

        tk.Label(form, text="Độ tuổi").grid(row=0, column=2, sticky="w", padx=(12, 0))
        self.e_do_tuoi = tk.Entry(form)
        self.e_do_tuoi.grid(row=0, column=3, sticky="ew", padx=8, pady=4)

        tk.Label(form, text="Trạng thái").grid(row=1, column=2, sticky="w", padx=(12, 0))
        self.cb_trang_thai = ttk.Combobox(
            form, state="readonly",
            values=["dang_chieu", "ngung_chieu"],
            width=18
        )
        self.cb_trang_thai.current(0)
        self.cb_trang_thai.grid(row=1, column=3, sticky="ew", padx=8, pady=4)

        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(3, weight=1)

        # ====== BUTTONS ======
        btns = tk.Frame(self)
        btns.pack(fill="x", padx=10, pady=6)

        tk.Button(btns, text="Thêm", command=self.them_phim).pack(side="left")
        tk.Button(btns, text="Cập nhật", command=self.cap_nhat_phim).pack(side="left", padx=6)
        tk.Button(btns, text="Ngừng chiếu", command=self.ngung_chieu).pack(side="left")
        tk.Button(btns, text="Xóa", command=self.xoa_phim).pack(side="left", padx=6)

        tk.Button(btns, text="Tải lại", command=self.tai_ds).pack(side="right")
        tk.Button(btns, text="Bỏ chọn", command=self.clear_select).pack(side="right", padx=6)

        # ====== TABLE ======
        cols = ("phim_id", "ten_phim", "the_loai", "thoi_luong_phut", "do_tuoi", "trang_thai")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)

        for c in cols:
            self.tree.heading(c, text=c)
            if c == "ten_phim":
                self.tree.column(c, width=260)
            elif c in ("the_loai",):
                self.tree.column(c, width=160)
            elif c in ("trang_thai",):
                self.tree.column(c, width=120)
            else:
                self.tree.column(c, width=120)

        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.tai_ds()

    def _mb_parent(self):
        try:
            return self.winfo_toplevel()
        except Exception:
            return None

    def clear_select(self):
        self.phim_id = None
        try:
            self.tree.selection_remove(self.tree.selection())
        except Exception:
            pass

        self.e_ten.delete(0, "end")
        self.e_the_loai.delete(0, "end")
        self.e_thoi_luong.delete(0, "end")
        self.e_do_tuoi.delete(0, "end")
        self.cb_trang_thai.current(0)

    # ================= DB helpers =================
    def _count_suat_chieu_of_phim(self, phim_id: int) -> int:
        conn = ket_noi()
        if conn is None:
            return 0
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM suat_chieu WHERE phim_id=%s", (phim_id,))
            return int(cur.fetchone()[0])
        finally:
            cur.close()
            conn.close()

    # ================= CRUD =================
    def them_phim(self):
        ten = self.e_ten.get().strip()
        the_loai = self.e_the_loai.get().strip()
        thoi_luong = self.e_thoi_luong.get().strip()
        do_tuoi = self.e_do_tuoi.get().strip()
        trang_thai = self.cb_trang_thai.get().strip() or "dang_chieu"

        if not ten:
            messagebox.showwarning("Thiếu dữ liệu", "Tên phim không được để trống.", parent=self._mb_parent())
            return

        try:
            thoi_luong_int = int(thoi_luong) if thoi_luong else 0
            do_tuoi_int = int(do_tuoi) if do_tuoi else 0
        except Exception:
            messagebox.showwarning("Sai dữ liệu", "Thời lượng / Độ tuổi phải là số.", parent=self._mb_parent())
            return

        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self._mb_parent())
            return

        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO phim(ten_phim, the_loai, thoi_luong_phut, do_tuoi, trang_thai)
                VALUES (%s,%s,%s,%s,%s)
            """, (ten, the_loai, thoi_luong_int, do_tuoi_int, trang_thai))
            conn.commit()
            messagebox.showinfo("OK", "Đã thêm phim.", parent=self._mb_parent())
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Lỗi", str(e), parent=self._mb_parent())
        finally:
            cur.close()
            conn.close()

        self.tai_ds()
        self.clear_select()

    def cap_nhat_phim(self):
        if not self.phim_id:
            messagebox.showinfo("Chưa chọn", "Chọn 1 phim để cập nhật.", parent=self._mb_parent())
            return

        ten = self.e_ten.get().strip()
        the_loai = self.e_the_loai.get().strip()
        thoi_luong = self.e_thoi_luong.get().strip()
        do_tuoi = self.e_do_tuoi.get().strip()
        trang_thai = self.cb_trang_thai.get().strip() or "dang_chieu"

        if not ten:
            messagebox.showwarning("Thiếu dữ liệu", "Tên phim không được để trống.", parent=self._mb_parent())
            return

        try:
            thoi_luong_int = int(thoi_luong) if thoi_luong else 0
            do_tuoi_int = int(do_tuoi) if do_tuoi else 0
        except Exception:
            messagebox.showwarning("Sai dữ liệu", "Thời lượng / Độ tuổi phải là số.", parent=self._mb_parent())
            return

        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self._mb_parent())
            return

        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE phim
                SET ten_phim=%s, the_loai=%s, thoi_luong_phut=%s, do_tuoi=%s, trang_thai=%s
                WHERE phim_id=%s
            """, (ten, the_loai, thoi_luong_int, do_tuoi_int, trang_thai, self.phim_id))
            conn.commit()
            messagebox.showinfo("OK", "Đã cập nhật phim.", parent=self._mb_parent())
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Lỗi", str(e), parent=self._mb_parent())
        finally:
            cur.close()
            conn.close()

        self.tai_ds()

    def ngung_chieu(self):
        if not self.phim_id:
            messagebox.showinfo("Chưa chọn", "Chọn 1 phim để ngừng chiếu.", parent=self._mb_parent())
            return

        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self._mb_parent())
            return

        cur = conn.cursor()
        try:
            cur.execute("UPDATE phim SET trang_thai='ngung_chieu' WHERE phim_id=%s", (self.phim_id,))
            conn.commit()
            messagebox.showinfo("OK", "Đã ngừng chiếu phim.", parent=self._mb_parent())
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Lỗi", str(e), parent=self._mb_parent())
        finally:
            cur.close()
            conn.close()

        self.tai_ds()

    def xoa_phim(self):
        if not self.phim_id:
            messagebox.showinfo("Chưa chọn", "Chọn 1 phim để xóa.", parent=self._mb_parent())
            return

        # CÁCH 1: còn suất chiếu -> không delete, chuyển ngừng_chiếu
        cnt = self._count_suat_chieu_of_phim(self.phim_id)
        if cnt > 0:
            conn = ket_noi()
            cur = conn.cursor()
            try:
                cur.execute("UPDATE phim SET trang_thai='ngung_chieu' WHERE phim_id=%s", (self.phim_id,))
                conn.commit()
            finally:
                cur.close()
                conn.close()
            messagebox.showinfo(
                "Không thể xóa",
                f"Phim đang có {cnt} suất chiếu.\n"
                "Không xóa để tránh lỗi dữ liệu.\n"
                "→ Đã chuyển phim sang NGỪNG CHIẾU.",
                parent=self._mb_parent()
            )
            self.tai_ds()
            return

        if not messagebox.askyesno("Xác nhận", f"Xóa phim ID={self.phim_id} ?", parent=self._mb_parent()):
            return

        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self._mb_parent())
            return

        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM phim WHERE phim_id=%s", (self.phim_id,))
            conn.commit()
            messagebox.showinfo("OK", "Đã xóa phim.", parent=self._mb_parent())
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Lỗi", str(e), parent=self._mb_parent())
        finally:
            cur.close()
            conn.close()

        self.tai_ds()
        self.clear_select()

    # ================= LOAD =================
    def tai_ds(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self._mb_parent())
            return

        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT phim_id, ten_phim, the_loai, thoi_luong_phut, do_tuoi, trang_thai
                FROM phim
                ORDER BY phim_id DESC
            """)
            for row in cur.fetchall():
                self.tree.insert("", "end", values=row)
        finally:
            cur.close()
            conn.close()

    # ================= SELECT =================
    def on_select(self, _):
        sel = self.tree.selection()
        if not sel:
            return

        v = self.tree.item(sel[0], "values")
        self.phim_id = int(v[0])

        self.e_ten.delete(0, "end")
        self.e_ten.insert(0, v[1])

        self.e_the_loai.delete(0, "end")
        self.e_the_loai.insert(0, v[2])

        self.e_thoi_luong.delete(0, "end")
        self.e_thoi_luong.insert(0, str(v[3]))

        self.e_do_tuoi.delete(0, "end")
        self.e_do_tuoi.insert(0, str(v[4]))

        # set trạng thái combobox
        trang_thai = str(v[5])
        if trang_thai in self.cb_trang_thai["values"]:
            self.cb_trang_thai.set(trang_thai)
        else:
            self.cb_trang_thai.current(0)
