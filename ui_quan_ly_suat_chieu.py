import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from ket_noi_db import ket_noi

FMT = "%Y-%m-%d %H:%M"


class ManHinhQuanLySuatChieu(tk.Frame):
    def __init__(self, master, user: dict | None = None):
        super().__init__(master)
        self.master = master
        self.user = user or {}

        self.suat_chieu_id = None

        # detect schema
        self.has_sc_trang_thai = self._has_column("suat_chieu", "trang_thai")

        self.ds_phim = self.lay_ds_phim()
        self.ds_phong = self.lay_ds_phong()

        # ===== FORM =====
        form = tk.LabelFrame(self, text="Tạo / cập nhật suất chiếu", padx=10, pady=10)
        form.pack(fill="x", padx=10, pady=10)

        tk.Label(form, text="Phim").grid(row=0, column=0, sticky="w")
        self.cb_phim = ttk.Combobox(
            form, state="readonly",
            values=[f"{p[0]} - {p[1]}" for p in self.ds_phim],
            width=35
        )
        if self.ds_phim:
            self.cb_phim.current(0)
        self.cb_phim.grid(row=0, column=1, sticky="ew", padx=8, pady=4)

        tk.Label(form, text="Phòng").grid(row=1, column=0, sticky="w")
        self.cb_phong = ttk.Combobox(
            form, state="readonly",
            values=[f"{r[0]} - {r[1]}" for r in self.ds_phong],
            width=35
        )
        if self.ds_phong:
            self.cb_phong.current(0)
        self.cb_phong.grid(row=1, column=1, sticky="ew", padx=8, pady=4)

        tk.Label(form, text="Giờ bắt đầu (YYYY-MM-DD HH:MM)").grid(row=0, column=2, sticky="w", padx=(12, 0))
        self.e_batdau = tk.Entry(form)
        self.e_batdau.grid(row=0, column=3, sticky="ew", padx=8, pady=4)

        tk.Label(form, text="Giá vé").grid(row=1, column=2, sticky="w", padx=(12, 0))
        self.e_gia = tk.Entry(form)
        self.e_gia.grid(row=1, column=3, sticky="ew", padx=8, pady=4)

        tk.Label(form, text="Giờ kết thúc (tự động tính)").grid(row=2, column=0, sticky="w")
        self.lbl_ketthuc = tk.Label(form, text="(chưa tính)")
        self.lbl_ketthuc.grid(row=2, column=1, sticky="w", padx=8, pady=4)

        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(3, weight=1)

        # ===== FILTER BAR =====
        bar = tk.Frame(self)
        bar.pack(fill="x", padx=10)

        username = self.user.get("username") or self.user.get("ten_dang_nhap") or ""
        role = self.user.get("role") or self.user.get("vai_tro") or ""
        tk.Label(bar, text=f"User: {username} | Vai trò: {role}", fg="gray").pack(side="left")

        tk.Label(bar, text="   Lọc:").pack(side="left", padx=(12, 0))
        self.cb_loc = ttk.Combobox(
            bar, state="readonly", width=18,
            values=(["tat_ca", "dang_ban", "ngung_ban"] if self.has_sc_trang_thai else ["tat_ca"])
        )
        self.cb_loc.current(0)
        self.cb_loc.pack(side="left", padx=6)
        self.cb_loc.bind("<<ComboboxSelected>>", lambda _e: self.tai_ds())

        tk.Button(bar, text="Tải lại", command=self.tai_ds).pack(side="right")

        # ===== BUTTONS =====
        btns = tk.Frame(self)
        btns.pack(fill="x", padx=10, pady=6)

        tk.Button(btns, text="Tính giờ kết thúc", command=self.tinh_gio_ket_thuc).pack(side="left")
        tk.Button(btns, text="Thêm suất chiếu", command=self.them).pack(side="left", padx=6)
        tk.Button(btns, text="Cập nhật", command=self.cap_nhat).pack(side="left")

        tk.Button(btns, text="Ngừng bán", command=self.ngung_ban).pack(side="left", padx=6)
        tk.Button(btns, text="Mở bán lại", command=self.mo_ban_lai).pack(side="left")

        tk.Button(btns, text="Xóa", command=self.xoa_suat_chieu).pack(side="left", padx=6)
        tk.Button(btns, text="Bỏ chọn", command=self.clear_select).pack(side="right")

        # ===== TABLE =====
        cols = [
            "suat_chieu_id", "phim_id", "ten_phim",
            "phong_id", "ten_phong",
            "gio_bat_dau", "gio_ket_thuc",
            "gia_ve"
        ]
        if self.has_sc_trang_thai:
            cols.append("trang_thai")

        self.cols = tuple(cols)

        self.tree = ttk.Treeview(self, columns=self.cols, show="headings", height=16)
        for c in self.cols:
            self.tree.heading(c, text=c)
            if c == "ten_phim":
                self.tree.column(c, width=220)
            elif c in ("gio_bat_dau", "gio_ket_thuc"):
                self.tree.column(c, width=160)
            elif c == "trang_thai":
                self.tree.column(c, width=110)
            else:
                self.tree.column(c, width=110)

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # default
        self.e_batdau.insert(0, datetime.now().strftime(FMT))
        self.e_gia.insert(0, "90000")

        self.tai_ds()

        # auto cleanup
        self._auto_cleanup_interval_ms = 60_000
        self._run_auto_cleanup()

    # ================= helpers =================
    def _mb_parent(self):
        try:
            return self.winfo_toplevel()
        except Exception:
            return None

    def _has_column(self, table: str, col: str) -> bool:
        conn = ket_noi()
        if conn is None:
            return False
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = %s
                  AND COLUMN_NAME = %s
            """, (table, col))
            return int(cur.fetchone()[0]) > 0
        finally:
            cur.close()
            conn.close()

    def clear_select(self):
        self.suat_chieu_id = None
        try:
            self.tree.selection_remove(self.tree.selection())
        except Exception:
            pass
        self.lbl_ketthuc.config(text="(chưa tính)")

    def parse_id(self, text):
        return int(text.split("-")[0].strip())

    # ================== DATA LOAD ==================
    def lay_ds_phim(self):
        conn = ket_noi()
        if conn is None:
            return []
        cur = conn.cursor()
        try:
            # lấy phim để chọn suất: ưu tiên đang chiếu
            cur.execute("SELECT phim_id, ten_phim, thoi_luong_phut FROM phim ORDER BY phim_id DESC;")
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def lay_ds_phong(self):
        conn = ket_noi()
        if conn is None:
            return []
        cur = conn.cursor()
        try:
            cur.execute("SELECT phong_id, ten_phong FROM phong_chieu ORDER BY phong_id DESC;")
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def _dem_ve_theo_suat(self, suat_chieu_id: int) -> int:
        # ✅ bảng vé trong DB bạn là "ve"
        conn = ket_noi()
        if conn is None:
            return 0
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM ve WHERE suat_chieu_id=%s", (suat_chieu_id,))
            return int(cur.fetchone()[0])
        finally:
            cur.close()
            conn.close()

    # ================== LOGIC ==================
    def tinh_gio_ket_thuc(self):
        if not self.ds_phim:
            messagebox.showwarning("Thiếu phim", "Bạn chưa có phim. Hãy thêm phim trước.", parent=self._mb_parent())
            return None
        try:
            batdau = datetime.strptime(self.e_batdau.get().strip(), FMT)
        except Exception:
            messagebox.showwarning("Sai định dạng", f"Giờ bắt đầu phải theo dạng: {FMT}", parent=self._mb_parent())
            return None

        phim_id = self.parse_id(self.cb_phim.get())
        tl = None
        for p in self.ds_phim:
            if p[0] == phim_id:
                tl = int(p[2])
                break
        if tl is None:
            messagebox.showerror("Lỗi", "Không tìm thấy thời lượng phim.", parent=self._mb_parent())
            return None

        ketthuc = batdau + timedelta(minutes=tl)
        self.lbl_ketthuc.config(text=ketthuc.strftime(FMT))
        return ketthuc

    def them(self):
        if not self.ds_phim or not self.ds_phong:
            messagebox.showwarning("Thiếu dữ liệu", "Cần có phim và phòng chiếu trước.", parent=self._mb_parent())
            return

        try:
            phim_id = self.parse_id(self.cb_phim.get())
            phong_id = self.parse_id(self.cb_phong.get())
            batdau = datetime.strptime(self.e_batdau.get().strip(), FMT)
            gia = float(self.e_gia.get().strip())
        except Exception as e:
            messagebox.showwarning("Sai dữ liệu", f"Kiểm tra giờ bắt đầu / giá vé.\n{e}", parent=self._mb_parent())
            return

        ketthuc = self.tinh_gio_ket_thuc()
        if not ketthuc:
            return

        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self._mb_parent())
            return

        cur = conn.cursor()
        try:
            if self.has_sc_trang_thai:
                cur.execute("""
                    INSERT INTO suat_chieu(phim_id, phong_id, gio_bat_dau, gio_ket_thuc, gia_ve, trang_thai)
                    VALUES (%s,%s,%s,%s,%s,'dang_ban')
                """, (phim_id, phong_id, batdau, ketthuc, gia))
            else:
                cur.execute("""
                    INSERT INTO suat_chieu(phim_id, phong_id, gio_bat_dau, gio_ket_thuc, gia_ve)
                    VALUES (%s,%s,%s,%s,%s)
                """, (phim_id, phong_id, batdau, ketthuc, gia))
            conn.commit()
            messagebox.showinfo("OK", "Đã thêm suất chiếu!", parent=self._mb_parent())
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Lỗi", str(e), parent=self._mb_parent())
        finally:
            cur.close()
            conn.close()

        self.tai_ds()

    def cap_nhat(self):
        if not self.suat_chieu_id:
            messagebox.showinfo("Chưa chọn", "Chọn 1 suất chiếu để cập nhật.", parent=self._mb_parent())
            return

        try:
            phim_id = self.parse_id(self.cb_phim.get())
            phong_id = self.parse_id(self.cb_phong.get())
            batdau = datetime.strptime(self.e_batdau.get().strip(), FMT)
            gia = float(self.e_gia.get().strip())
        except Exception as e:
            messagebox.showwarning("Sai dữ liệu", f"Kiểm tra giờ bắt đầu / giá vé.\n{e}", parent=self._mb_parent())
            return

        ketthuc = self.tinh_gio_ket_thuc()
        if not ketthuc:
            return

        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self._mb_parent())
            return

        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE suat_chieu
                SET phim_id=%s, phong_id=%s, gio_bat_dau=%s, gio_ket_thuc=%s, gia_ve=%s
                WHERE suat_chieu_id=%s
            """, (phim_id, phong_id, batdau, ketthuc, gia, self.suat_chieu_id))
            conn.commit()
            messagebox.showinfo("OK", "Đã cập nhật suất chiếu!", parent=self._mb_parent())
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Lỗi", str(e), parent=self._mb_parent())
        finally:
            cur.close()
            conn.close()

        self.tai_ds()

    def ngung_ban(self):
        if not self.suat_chieu_id:
            messagebox.showinfo("Chưa chọn", "Chọn 1 suất chiếu để ngừng bán.", parent=self._mb_parent())
            return

        if not self.has_sc_trang_thai:
            messagebox.showwarning(
                "DB không có cột trạng_thái",
                "Trong schema hiện tại, bảng suat_chieu không có cột 'trang_thai' nên không thể ngừng bán.\n"
                "Bạn chỉ có thể xóa suất chiếu nếu chưa có vé.",
                parent=self._mb_parent()
            )
            return

        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self._mb_parent())
            return

        cur = conn.cursor()
        try:
            cur.execute("UPDATE suat_chieu SET trang_thai='ngung_ban' WHERE suat_chieu_id=%s", (self.suat_chieu_id,))
            conn.commit()
            messagebox.showinfo("OK", "Đã ngừng bán suất chiếu!", parent=self._mb_parent())
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Lỗi", str(e), parent=self._mb_parent())
        finally:
            cur.close()
            conn.close()

        self.tai_ds()

    def mo_ban_lai(self):
        if not self.suat_chieu_id:
            messagebox.showinfo("Chưa chọn", "Chọn 1 suất chiếu để mở bán lại.", parent=self._mb_parent())
            return

        if not self.has_sc_trang_thai:
            messagebox.showwarning(
                "DB không có cột trạng_thái",
                "Bảng suat_chieu không có 'trang_thai' nên không thể mở bán lại.",
                parent=self._mb_parent()
            )
            return

        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self._mb_parent())
            return

        cur = conn.cursor()
        try:
            cur.execute("UPDATE suat_chieu SET trang_thai='dang_ban' WHERE suat_chieu_id=%s", (self.suat_chieu_id,))
            conn.commit()
            messagebox.showinfo("OK", "Đã mở bán lại!", parent=self._mb_parent())
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Lỗi", str(e), parent=self._mb_parent())
        finally:
            cur.close()
            conn.close()

        self.tai_ds()

    def xoa_suat_chieu(self):
        if not self.suat_chieu_id:
            messagebox.showinfo("Chưa chọn", "Chọn 1 suất chiếu để xóa.", parent=self._mb_parent())
            return

        sc_id = int(self.suat_chieu_id)
        ve_count = self._dem_ve_theo_suat(sc_id)

        # ✅ RULE: có vé thì KHÔNG DELETE (vì vướng FK chi_tiet_hoa_don -> ve)
        if ve_count > 0:
            # nếu có trạng_thái thì chuyển ngừng bán cho “biến mất” ở UI lọc
            if self.has_sc_trang_thai:
                conn = ket_noi()
                cur = conn.cursor()
                try:
                    cur.execute("UPDATE suat_chieu SET trang_thai='ngung_ban' WHERE suat_chieu_id=%s", (sc_id,))
                    conn.commit()
                finally:
                    cur.close()
                    conn.close()
                messagebox.showinfo("OK", f"Suất chiếu đã có {ve_count} vé → không xóa được → chuyển NGỪNG BÁN.", parent=self._mb_parent())
                self.clear_select()
                self.tai_ds()
                return

            messagebox.showerror(
                "Không thể xóa",
                f"Suất chiếu đã có {ve_count} vé nên KHÔNG thể DELETE (vướng FK).\n"
                "Nếu bạn muốn 'ẩn', hãy thêm cột trang_thai cho suat_chieu hoặc dùng lọc/archived.",
                parent=self._mb_parent()
            )
            return

        if not messagebox.askyesno("Xác nhận", f"Xóa suất chiếu ID={sc_id} (chưa có vé) ?", parent=self._mb_parent()):
            return

        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self._mb_parent())
            return

        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM suat_chieu WHERE suat_chieu_id=%s", (sc_id,))
            conn.commit()
            messagebox.showinfo("OK", "Đã xóa suất chiếu (chưa có vé).", parent=self._mb_parent())
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Lỗi", str(e), parent=self._mb_parent())
        finally:
            cur.close()
            conn.close()

        self.clear_select()
        self.tai_ds()

    # ================== AUTO CLEANUP ==================
    def _run_auto_cleanup(self):
        """
        - Hết giờ + có vé  -> nếu có trang_thai thì set ngung_ban (giữ lịch sử)
        - Hết giờ + không vé -> delete suất chiếu
        """
        conn = ket_noi()
        if conn is not None:
            cur = conn.cursor()
            try:
                cur.execute("""
                    SELECT suat_chieu_id
                    FROM suat_chieu
                    WHERE gio_ket_thuc <= NOW()
                """)
                expired_ids = [r[0] for r in cur.fetchall()]

                changed = False
                for sc_id in expired_ids:
                    # count tickets
                    cur.execute("SELECT COUNT(*) FROM ve WHERE suat_chieu_id=%s", (sc_id,))
                    cnt = int(cur.fetchone()[0])

                    if cnt == 0:
                        cur.execute("DELETE FROM suat_chieu WHERE suat_chieu_id=%s", (sc_id,))
                        changed = True
                    else:
                        if self.has_sc_trang_thai:
                            cur.execute("UPDATE suat_chieu SET trang_thai='ngung_ban' WHERE suat_chieu_id=%s", (sc_id,))
                            changed = True

                if changed:
                    conn.commit()
                    self.tai_ds()

            except Exception as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                print("auto_cleanup error:", e)
            finally:
                try:
                    cur.close()
                    conn.close()
                except Exception:
                    pass

        self.after(self._auto_cleanup_interval_ms, self._run_auto_cleanup)

    # ================== LOAD TABLE ==================
    def tai_ds(self):
        self.ds_phim = self.lay_ds_phim()
        self.ds_phong = self.lay_ds_phong()

        self.cb_phim["values"] = [f"{p[0]} - {p[1]}" for p in self.ds_phim]
        self.cb_phong["values"] = [f"{r[0]} - {r[1]}" for r in self.ds_phong]
        if self.ds_phim and self.cb_phim.current() == -1:
            self.cb_phim.current(0)
        if self.ds_phong and self.cb_phong.current() == -1:
            self.cb_phong.current(0)

        for i in self.tree.get_children():
            self.tree.delete(i)

        loc = self.cb_loc.get().strip()

        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self._mb_parent())
            return

        cur = conn.cursor()
        try:
            select_cols = """
                sc.suat_chieu_id, p.phim_id, p.ten_phim,
                r.phong_id, r.ten_phong,
                sc.gio_bat_dau, sc.gio_ket_thuc,
                sc.gia_ve
            """
            if self.has_sc_trang_thai:
                select_cols += ", sc.trang_thai"

            sql = f"""
                SELECT {select_cols}
                FROM suat_chieu sc
                JOIN phim p ON sc.phim_id = p.phim_id
                JOIN phong_chieu r ON sc.phong_id = r.phong_id
            """
            params = []

            # ✅ nếu có trang_thai thì lọc được
            if self.has_sc_trang_thai:
                if loc == "dang_ban":
                    sql += " WHERE sc.trang_thai=%s"
                    params.append("dang_ban")
                elif loc == "ngung_ban":
                    sql += " WHERE sc.trang_thai=%s"
                    params.append("ngung_ban")

            sql += " ORDER BY sc.suat_chieu_id DESC;"

            cur.execute(sql, params)
            for row in cur.fetchall():
                self.tree.insert("", "end", values=row)
        finally:
            cur.close()
            conn.close()

        self.suat_chieu_id = None

    # ================== SELECT ==================
    def on_select(self, _):
        sel = self.tree.selection()
        if not sel:
            return

        v = self.tree.item(sel[0], "values")
        self.suat_chieu_id = int(v[0])

        phim_id = int(v[1])
        phong_id = int(v[3])

        for i, p in enumerate(self.ds_phim):
            if p[0] == phim_id:
                self.cb_phim.current(i)
                break

        for i, r in enumerate(self.ds_phong):
            if r[0] == phong_id:
                self.cb_phong.current(i)
                break

        gb = v[5]
        gk = v[6]

        self.e_batdau.delete(0, "end")
        self.e_batdau.insert(0, str(gb)[:16])

        self.lbl_ketthuc.config(text=str(gk)[:16])

        self.e_gia.delete(0, "end")
        self.e_gia.insert(0, str(v[7]))
