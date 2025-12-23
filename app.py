
import tkinter as tk
from ui_dang_nhap import ManHinhDangNhap

def main():
    root = tk.Tk()
    root.title("Cinema Ticket Manager")
    root.withdraw()  

    root.protocol("WM_DELETE_WINDOW", root.destroy)

    ManHinhDangNhap(root)
    root.mainloop()

if __name__ == "__main__":
    main()