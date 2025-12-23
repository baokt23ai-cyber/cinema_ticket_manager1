from reportlab.lib.pagesizes import A6
from reportlab.pdfgen import canvas
from datetime import datetime

def in_ve_pdf(duong_dan_pdf, thong_tin):
    """
    thong_tin: dict chứa:
    - ten_phim, ten_phong, gio_bat_dau, ma_ghe, ma_ve, gia, ten_khach
    """
    c = canvas.Canvas(duong_dan_pdf, pagesize=A6)
    w, h = A6

    y = h - 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(15, y, "VE XEM PHIM")
    y -= 18

    c.setFont("Helvetica", 10)
    c.drawString(15, y, f"Phim: {thong_tin['ten_phim']}")
    y -= 14
    c.drawString(15, y, f"Phong: {thong_tin['ten_phong']}")
    y -= 14
    c.drawString(15, y, f"Gio: {thong_tin['gio_bat_dau']}")
    y -= 14
    c.drawString(15, y, f"Ghe: {thong_tin['ma_ghe']}")
    y -= 14
    c.drawString(15, y, f"Ma ve: {thong_tin['ma_ve']}")
    y -= 14
    c.drawString(15, y, f"Gia: {thong_tin['gia']}")
    y -= 14
    c.drawString(15, y, f"Khach: {thong_tin.get('ten_khach','')}")
    y -= 14

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(15, 12, f"In luc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.showPage()
    c.save()
