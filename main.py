import tkinter as tk
from ui_dashboard import ManHinhDashboard

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # ✅ Ẩn cửa sổ root trắng

    user = {"id": 1, "username": "admin", "vai_tro": "quan_tri"}  # ✅ đồng bộ key (vai_tro)
    ManHinhDashboard(root, user=user)

    root.mainloop()
