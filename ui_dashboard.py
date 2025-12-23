# ui_dashboard.py
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

from ket_noi_db import ket_noi

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ManHinhDashboard(tk.Toplevel):
    """
    Dashboard kiểu cửa sổ riêng (Toplevel) + sidebar trái + KPI + 2 chart.
    - KHÔNG warning ticklabels
    - Query theo schema: ve -> chi_tiet_hoa_don -> hoa_don (ve không có hoa_don_id)
    """

    def __init__(self, root, user: dict | None = None):
        super().__init__(root)
        self.root = root
        self.user = user or {}

        self.title("Dashboard báo cáo")
        self.geometry("1200x720")

        # ===== Layout trái / phải =====
        left = tk.Frame(self, width=220, bg="#f4f4f4")
        left.pack(side="left", fill="y")

        right = tk.Frame(self, bg="white")
        right.pack(side="right", fill="both", expand=True)

        # ===== Sidebar =====
        tk.Label(left, text="Bán vé", font=("Arial", 11, "bold"), bg="#f4f4f4").pack(
            anchor="w", padx=12, pady=(12, 6)
        )
        tk.Button(left, text="Mở màn hình bán vé", command=self.open_ban_ve).pack(
            fill="x", padx=12
        )

        tk.Label(left, text="Quản trị", font=("Arial", 11, "bold"), bg="#f4f4f4").pack(
            anchor="w", padx=12, pady=(16, 6)
        )
        tk.Button(left, text="Quản lý phim", command=self.open_quan_ly_phim).pack(
            fill="x", padx=12, pady=3
        )
        tk.Button(left, text="Quản lý phòng", command=self.open_quan_ly_phong).pack(
            fill="x", padx=12, pady=3
        )
        tk.Button(left, text="Quản lý suất chiếu", command=self.open_quan_ly_suat).pack(
            fill="x", padx=12, pady=3
        )

        # ===== Header =====
        header = tk.Frame(right, bg="white")
        header.pack(fill="x", padx=12, pady=10)

        tk.Label(header, text="DASHBOARD BÁO CÁO", font=("Arial", 15, "bold"), bg="white").pack(
            side="left"
        )

        username = self.user.get("username") or self.user.get("ten_dang_nhap") or "admin"
        role = self.user.get("role") or self.user.get("vai_tro") or "quan_tri"
        tk.Label(header, text=f"User: {username} | Vai trò: {role}", fg="gray", bg="white").pack(
            side="right"
        )

        # ===== Filter bar =====
        filt = tk.LabelFrame(right, text="Bộ lọc", bg="white", padx=10, pady=6)
        filt.pack(fill="x", padx=12, pady=(0, 10))

        tk.Label(filt, text="Từ ngày (YYYY-MM-DD)", bg="white").grid(row=0, column=0, sticky="w")
        self.e_from = tk.Entry(filt, width=14)
        self.e_from.grid(row=0, column=1, padx=6)

        tk.Label(filt, text="Đến ngày (YYYY-MM-DD)", bg="white").grid(
            row=0, column=2, sticky="w", padx=(10, 0)
        )
        self.e_to = tk.Entry(filt, width=14)
        self.e_to.grid(row=0, column=3, padx=6)

        tk.Button(filt, text="Làm mới", command=self.reload).grid(row=0, column=4, padx=10)

        today = datetime.now().date()
        self.e_from.insert(0, str(today))
        self.e_to.insert(0, str(today))

        # ===== KPI row =====
        kpi = tk.Frame(right, bg="white")
        kpi.pack(fill="x", padx=12, pady=(0, 10))

        self.lbl_rev = self._kpi_box(kpi, "Doanh thu", "0 đ")
        self.lbl_tickets = self._kpi_box(kpi, "Vé đã bán", "0")
        self.lbl_bills = self._kpi_box(kpi, "Hóa đơn", "0")
        self.lbl_avg = self._kpi_box(kpi, "TB / hóa đơn", "0 đ")

        # ===== Charts =====
        charts = tk.Frame(right, bg="white")
        charts.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.left_chart = tk.LabelFrame(charts, text="Doanh thu theo ngày", bg="white")
        self.left_chart.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.right_chart = tk.LabelFrame(charts, text="Top phim theo số vé", bg="white")
        self.right_chart.pack(side="right", fill="both", expand=True, padx=(8, 0))

        self.reload()

    # ================= KPI / Helpers =================
    def _kpi_box(self, parent, title, value):
        box = tk.LabelFrame(parent, text=title, bg="white", padx=10, pady=8)
        box.pack(side="left", fill="x", expand=True, padx=6)
        lbl = tk.Label(box, text=value, font=("Arial", 14, "bold"), bg="white")
        lbl.pack()
        return lbl

    def _parse_date(self, s: str):
        return datetime.strptime(s.strip(), "%Y-%m-%d").date()

    def reload(self):
        try:
            d1 = self._parse_date(self.e_from.get())
            d2 = self._parse_date(self.e_to.get())
            if d1 > d2:
                d1, d2 = d2, d1
        except Exception:
            messagebox.showwarning("Sai ngày", "Ngày phải theo dạng YYYY-MM-DD", parent=self)
            return

        data = self._fetch(d1, d2)
        if data is None:
            return

        total_rev, total_ticket, total_bill, rev_by_day, top_movies = data

        self.lbl_rev.config(text=f"{total_rev:,.0f} đ")
        self.lbl_tickets.config(text=f"{total_ticket:,}")
        self.lbl_bills.config(text=f"{total_bill:,}")
        avg = (total_rev / total_bill) if total_bill else 0
        self.lbl_avg.config(text=f"{avg:,.0f} đ")

        self._render_rev_by_day(rev_by_day)
        self._render_top_movies(top_movies)

    def _fetch(self, d1, d2):
        conn = ket_noi()
        if conn is None:
            messagebox.showerror("Lỗi DB", "Không kết nối được database.", parent=self)
            return None

        cur = conn.cursor()
        try:
            # KPI tổng: doanh thu + vé + hóa đơn
            cur.execute(
                """
                SELECT
                    COALESCE(SUM(v.gia), 0) AS doanh_thu,
                    COALESCE(COUNT(v.ve_id), 0) AS ve_da_ban,
                    COALESCE(COUNT(DISTINCT cthd.hoa_don_id), 0) AS so_hoa_don
                FROM ve v
                LEFT JOIN chi_tiet_hoa_don cthd ON cthd.ve_id = v.ve_id
                LEFT JOIN hoa_don hd ON hd.hoa_don_id = cthd.hoa_don_id
                WHERE DATE(v.thoi_gian_ban) BETWEEN %s AND %s
                  AND v.trang_thai='da_ban'
                  AND (hd.trang_thai IS NULL OR hd.trang_thai='da_thanh_toan')
                """,
                (d1, d2),
            )
            total_rev, total_ticket, total_bill = cur.fetchone()

            # doanh thu theo ngày
            cur.execute(
                """
                SELECT DATE(v.thoi_gian_ban) AS ngay,
                       COALESCE(SUM(v.gia), 0) AS doanh_thu
                FROM ve v
                LEFT JOIN chi_tiet_hoa_don cthd ON cthd.ve_id = v.ve_id
                LEFT JOIN hoa_don hd ON hd.hoa_don_id = cthd.hoa_don_id
                WHERE DATE(v.thoi_gian_ban) BETWEEN %s AND %s
                  AND v.trang_thai='da_ban'
                  AND (hd.trang_thai IS NULL OR hd.trang_thai='da_thanh_toan')
                GROUP BY DATE(v.thoi_gian_ban)
                ORDER BY ngay
                """,
                (d1, d2),
            )
            rev_by_day = cur.fetchall()

            # top phim theo số vé
            cur.execute(
                """
                SELECT p.ten_phim, COUNT(v.ve_id) AS so_ve
                FROM ve v
                JOIN suat_chieu sc ON v.suat_chieu_id = sc.suat_chieu_id
                JOIN phim p ON sc.phim_id = p.phim_id
                LEFT JOIN chi_tiet_hoa_don cthd ON cthd.ve_id = v.ve_id
                LEFT JOIN hoa_don hd ON hd.hoa_don_id = cthd.hoa_don_id
                WHERE DATE(v.thoi_gian_ban) BETWEEN %s AND %s
                  AND v.trang_thai='da_ban'
                  AND (hd.trang_thai IS NULL OR hd.trang_thai='da_thanh_toan')
                GROUP BY p.phim_id, p.ten_phim
                ORDER BY so_ve DESC
                LIMIT 10
                """,
                (d1, d2),
            )
            top_movies = cur.fetchall()

            return float(total_rev), int(total_ticket), int(total_bill), rev_by_day, top_movies

        except Exception as e:
            messagebox.showerror("Lỗi query", str(e), parent=self)
            return None
        finally:
            try:
                cur.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass

    def _clear_frame(self, frame: tk.Widget):
        for w in frame.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

    def _render_rev_by_day(self, rev_by_day):
        self._clear_frame(self.left_chart)

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)

        if rev_by_day:
            labels = [str(r[0]) for r in rev_by_day]
            y = [float(r[1]) for r in rev_by_day]
            x = list(range(len(labels)))

            ax.plot(x, y, marker="o")
            ax.set_xticks(x, labels)  # ✅ không warning
            for t in ax.get_xticklabels():
                t.set_rotation(45)
                t.set_ha("right")
        else:
            ax.text(0.5, 0.5, "Không có dữ liệu", ha="center", va="center")

        ax.set_title("Doanh thu theo ngày")
        ax.set_xlabel("Ngày")
        ax.set_ylabel("Doanh thu")

        canvas = FigureCanvasTkAgg(fig, master=self.left_chart)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    def _render_top_movies(self, top_movies):
        self._clear_frame(self.right_chart)

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)

        if top_movies:
            labels = [r[0] for r in top_movies]
            vals = [int(r[1]) for r in top_movies]
            x = list(range(len(labels)))

            ax.bar(x, vals)
            ax.set_xticks(x, labels)  # ✅ không warning
            for t in ax.get_xticklabels():
                t.set_rotation(20)
                t.set_ha("right")
        else:
            ax.text(0.5, 0.5, "Không có dữ liệu", ha="center", va="center")

        ax.set_title("Top phim theo số vé")
        ax.set_xlabel("Phim")
        ax.set_ylabel("Số vé")

        canvas = FigureCanvasTkAgg(fig, master=self.right_chart)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    # ================= Open screens =================
    def _safe_import(self, module_name: str, class_name: str):
        try:
            mod = __import__(module_name, fromlist=[class_name])
            return getattr(mod, class_name)
        except Exception as e:
            messagebox.showerror("Lỗi import", f"{module_name}.{class_name}\n\n{e}", parent=self)
            return None

    def _open_in_window(self, title: str, geom: str, FrameCls, uid=None):
        """
        Mở FrameCls vào Toplevel.
        Thử linh hoạt các kiểu __init__ phổ biến:
        - FrameCls(win, user=self.user)
        - FrameCls(win, self.user)
        - FrameCls(win, uid)
        - FrameCls(win)
        """
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry(geom)

        # 1) keyword user=
        try:
            w = FrameCls(win, user=self.user)
            if hasattr(w, "pack"):
                w.pack(fill="both", expand=True)
            return
        except TypeError:
            pass

        # 2) truyền user dict
        try:
            w = FrameCls(win, self.user)
            if hasattr(w, "pack"):
                w.pack(fill="both", expand=True)
            return
        except TypeError:
            pass

        # 3) truyền uid (nếu có)
        if uid is not None:
            try:
                w = FrameCls(win, uid)
                if hasattr(w, "pack"):
                    w.pack(fill="both", expand=True)
                return
            except TypeError:
                pass

        # 4) chỉ parent
        try:
            w = FrameCls(win)
            if hasattr(w, "pack"):
                w.pack(fill="both", expand=True)
            return
        except Exception as e:
            messagebox.showerror("Lỗi mở màn", str(e), parent=self)

    def open_quan_ly_phim(self):
        FrameCls = self._safe_import("ui_quan_ly_phim", "ManHinhQuanLyPhim")
        if FrameCls:
            self._open_in_window("Quản lý phim", "1000x600", FrameCls)

    def open_quan_ly_phong(self):
        FrameCls = self._safe_import("ui_quan_ly_phong", "ManHinhQuanLyPhong")
        if FrameCls:
            self._open_in_window("Quản lý phòng", "1000x600", FrameCls)

    def open_quan_ly_suat(self):
        FrameCls = self._safe_import("ui_quan_ly_suat_chieu", "ManHinhQuanLySuatChieu")
        if FrameCls:
            self._open_in_window("Quản lý suất chiếu", "1100x650", FrameCls)

    def open_ban_ve(self):
        """
        ✅ FIX CHẮC CHẮN:
        - Class ManHinhBanVe của bạn đang yêu cầu tham số bắt buộc: nguoi_dung_id
          (kiểu __init__(root, nguoi_dung_id))
        - Vì vậy phải lấy uid từ self.user và truyền vào.
        """
        FrameCls = self._safe_import("ui_ban_ve", "ManHinhBanVe")
        if not FrameCls:
            return

        # Lấy uid chắc chắn
        uid = self.user.get("nguoi_dung_id") or self.user.get("id") or self.user.get("user_id")
        if uid is None:
            messagebox.showwarning(
                "Thiếu người dùng",
                "Không tìm thấy nguoi_dung_id trong biến user.\n"
                "Mình sẽ dùng tạm uid=1 để mở màn bán vé (test).",
                parent=self,
            )
            uid = 1

        # Ưu tiên kiểu chuẩn bạn đang dùng: ManHinhBanVe(root, nguoi_dung_id) (tự tạo Toplevel)
        try:
            FrameCls(self.root, uid)
            return
        except Exception:
            pass

        # Nếu class là Frame, mở trong Toplevel và pack
        try:
            self._open_in_window("Bán vé", "1100x650", FrameCls, uid=uid)
        except Exception as e:
            messagebox.showerror("Lỗi mở bán vé", str(e), parent=self)
