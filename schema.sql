CREATE DATABASE IF NOT EXISTS quan_ly_ve_xem_phim
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE quan_ly_ve_xem_phim;

-- =========================
-- BẢNG NGƯỜI DÙNG
-- =========================
CREATE TABLE nguoi_dung (
  nguoi_dung_id INT AUTO_INCREMENT PRIMARY KEY,
  ten_dang_nhap VARCHAR(50) UNIQUE NOT NULL,
  mat_khau VARCHAR(255) NOT NULL,
  vai_tro ENUM('quan_tri','nhan_vien') NOT NULL,
  ho_ten VARCHAR(100),
  ngay_tao DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- BẢNG PHIM
-- =========================
CREATE TABLE phim (
  phim_id INT AUTO_INCREMENT PRIMARY KEY,
  ten_phim VARCHAR(200) NOT NULL,
  the_loai VARCHAR(100),
  thoi_luong_phut INT NOT NULL,
  do_tuoi VARCHAR(10),
  trang_thai ENUM('dang_chieu','sap_chieu','ngung_chieu')
    DEFAULT 'dang_chieu'
);

-- =========================
-- BẢNG PHÒNG CHIẾU
-- =========================
CREATE TABLE phong_chieu (
  phong_id INT AUTO_INCREMENT PRIMARY KEY,
  ten_phong VARCHAR(50) UNIQUE NOT NULL,
  so_hang INT NOT NULL,
  so_cot INT NOT NULL
);

-- =========================
-- BẢNG GHẾ
-- =========================
CREATE TABLE ghe (
  ghe_id INT AUTO_INCREMENT PRIMARY KEY,
  phong_id INT NOT NULL,
  ma_ghe VARCHAR(10) NOT NULL,
  loai_ghe ENUM('thuong','vip') DEFAULT 'thuong',
  UNIQUE(phong_id, ma_ghe),
  FOREIGN KEY (phong_id) REFERENCES phong_chieu(phong_id)
);

-- =========================
-- BẢNG SUẤT CHIẾU
-- =========================
CREATE TABLE suat_chieu (
  suat_chieu_id INT AUTO_INCREMENT PRIMARY KEY,
  phim_id INT NOT NULL,
  phong_id INT NOT NULL,
  gio_bat_dau DATETIME NOT NULL,
  gio_ket_thuc DATETIME NOT NULL,
  gia_ve DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (phim_id) REFERENCES phim(phim_id),
  FOREIGN KEY (phong_id) REFERENCES phong_chieu(phong_id)
);

-- =========================
-- BẢNG HÓA ĐƠN
-- =========================
CREATE TABLE hoa_don (
  hoa_don_id INT AUTO_INCREMENT PRIMARY KEY,
  nguoi_dung_id INT NOT NULL,
  ten_khach_hang VARCHAR(100),
  so_dien_thoai VARCHAR(20),
  tong_tien DECIMAL(12,2) DEFAULT 0,
  phuong_thuc_thanh_toan ENUM('tien_mat','chuyen_khoan','the')
    DEFAULT 'tien_mat',
  trang_thai ENUM('da_thanh_toan','da_huy')
    DEFAULT 'da_thanh_toan',
  ngay_tao DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (nguoi_dung_id) REFERENCES nguoi_dung(nguoi_dung_id)
);

-- =========================
-- BẢNG VÉ
-- =========================
CREATE TABLE ve (
  ve_id INT AUTO_INCREMENT PRIMARY KEY,
  suat_chieu_id INT NOT NULL,
  ghe_id INT NOT NULL,
  gia DECIMAL(10,2) NOT NULL,
  ma_ve VARCHAR(30) UNIQUE NOT NULL,
  trang_thai ENUM('da_ban','da_huy') DEFAULT 'da_ban',
  thoi_gian_ban DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (suat_chieu_id) REFERENCES suat_chieu(suat_chieu_id),
  FOREIGN KEY (ghe_id) REFERENCES ghe(ghe_id),
  UNIQUE(suat_chieu_id, ghe_id)
);

-- =========================
-- CHI TIẾT HÓA ĐƠN
-- =========================
CREATE TABLE chi_tiet_hoa_don (
  chi_tiet_id INT AUTO_INCREMENT PRIMARY KEY,
  hoa_don_id INT NOT NULL,
  ve_id INT NOT NULL,
  FOREIGN KEY (hoa_don_id) REFERENCES hoa_don(hoa_don_id),
  FOREIGN KEY (ve_id) REFERENCES ve(ve_id),
  UNIQUE(hoa_don_id, ve_id)
);

-- =========================
-- DỮ LIỆU MẪU
-- =========================
INSERT INTO nguoi_dung(ten_dang_nhap, mat_khau, vai_tro, ho_ten)
VALUES
('admin', 'admin123', 'quan_tri', 'Quản trị hệ thống'),
('staff', 'staff123', 'nhan_vien', 'Nhân viên bán vé');
