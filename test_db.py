from ket_noi_db import ket_noi

conn = ket_noi()
print("OK" if conn else "FAIL")
if conn:
    conn.close()