import tkinter as tk
from ui_dashboard import ManHinhDashboard

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Dashboard báo cáo")
    root.geometry("1200x720")

    user = {"username": "admin", "role": "quan_tri"}  # hoặc user login thật của bạn
    ManHinhDashboard(root, user=user)

    root.mainloop()
