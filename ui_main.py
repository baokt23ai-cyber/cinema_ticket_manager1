import tkinter as tk
from ui_ban_ve import ManHinhBanVe
from ui_dashboard import ManHinhDashboard


class ManHinhChinh:
    def __init__(self, root, user: dict):
        self.root = root
        self.user = user

        for w in self.root.winfo_children():
            w.destroy()

        self.root.title("Màn hình chính")
        self.root.geometry("520x260")
        self.root.resizable(False, False)

        role = user.get("vai_tro", "nhan_vien")

        # ===== NHÂN VIÊN =====
        if role == "nhan_vien":
            ManHinhBanVe(
                self.root,
                user["id"],
                on_logout=self._logout
            )
            self.root.withdraw()
            return

        # ===== ADMIN =====
        tk.Label(
            self.root,
            text=f"Xin chào {user['username']} (Admin)",
            font=("Arial", 12, "bold")
        ).pack(pady=(18, 10))

        tk.Button(self.root, text="Bán vé", width=26,
                  command=self.open_ban_ve).pack(pady=6)
        tk.Button(self.root, text="Dashboard", width=26,
                  command=self.open_dashboard).pack(pady=6)
        tk.Button(self.root, text="Đổi tài khoản", width=26,
                  command=self._logout).pack(pady=10)

    def open_ban_ve(self):
        ManHinhBanVe(
            self.root,
            self.user["id"],
            on_logout=self._logout,
        )
        self.root.withdraw()

    def open_dashboard(self):
        ManHinhDashboard(self.root, self.user)

    def _back_to_menu(self):
        self.root.deiconify()
        ManHinhChinh(self.root, self.user)

    def _logout(self):
        for w in self.root.winfo_children():
            w.destroy()
        from ui_dang_nhap import ManHinhDangNhap
        ManHinhDangNhap(self.root)
