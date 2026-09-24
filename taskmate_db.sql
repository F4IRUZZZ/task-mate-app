-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: May 19, 2026 at 01:58 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `taskmate_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `kategori`
--

CREATE TABLE `kategori` (
  `id_kategori` int(11) NOT NULL,
  `nama_kategori` varchar(50) NOT NULL,
  `deskripsi` text DEFAULT NULL,
  `dibuat_pada` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `kategori`
-- 3 data dummy kategori
--

INSERT INTO `kategori` (`id_kategori`, `nama_kategori`, `deskripsi`, `dibuat_pada`) VALUES
(1, 'Pengembangan', 'Tugas terkait pengembangan dan coding', '2026-05-19 11:44:10'),
(2, 'Desain',       'Tugas terkait UI/UX dan desain grafis',  '2026-05-19 11:44:10'),
(3, 'Pengujian',    'Tugas terkait pengujian dan QA',         '2026-05-19 11:44:10');

-- --------------------------------------------------------

--
-- Table structure for table `prioritas`
--

CREATE TABLE `prioritas` (
  `id_prioritas` int(11) NOT NULL,
  `nama_prioritas` varchar(20) NOT NULL,
  `tingkat_prioritas` tinyint(4) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `prioritas`
--

INSERT INTO `prioritas` (`id_prioritas`, `nama_prioritas`, `tingkat_prioritas`) VALUES
(1, 'Rendah', 1),
(2, 'Sedang', 2),
(3, 'Tinggi', 3);

-- --------------------------------------------------------

--
-- Table structure for table `riwayat_tugas`
--

CREATE TABLE `riwayat_tugas` (
  `id_riwayat` int(11) NOT NULL,
  `status_lama` varchar(20) DEFAULT NULL,
  `status_baru` varchar(20) NOT NULL,
  `diubah_pada` timestamp NOT NULL DEFAULT current_timestamp(),
  `id_tugas` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `riwayat_tugas`
--

INSERT INTO `riwayat_tugas` (`id_riwayat`, `status_lama`, `status_baru`, `diubah_pada`, `id_tugas`) VALUES
(1, NULL, 'Menunggu', '2026-05-19 11:44:10', 1),
(2, NULL, 'Menunggu', '2026-05-19 11:44:10', 2),
(3, 'Menunggu', 'Selesai', '2026-05-19 11:44:10', 2),
(4, NULL, 'Menunggu', '2026-05-19 11:44:10', 3),
(5, NULL, 'Menunggu', '2026-05-19 11:44:10', 4),
(6, NULL, 'Menunggu', '2026-05-19 11:44:10', 5);

-- --------------------------------------------------------

--
-- Table structure for table `tugas`
--

CREATE TABLE `tugas` (
  `id_tugas` int(11) NOT NULL,
  `nama_tugas` varchar(255) NOT NULL,
  `deskripsi` text DEFAULT NULL,
  `status` enum('Menunggu','Selesai') NOT NULL DEFAULT 'Menunggu',
  `batas_waktu` date DEFAULT NULL,
  `dibuat_pada` timestamp NOT NULL DEFAULT current_timestamp(),
  `diperbarui_pada` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `id_prioritas` int(11) NOT NULL,
  `id_kategori` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `tugas`
-- (tugas id=5 yang sebelumnya pakai id_kategori=4/Manajemen, diubah ke id_kategori=3/Pengujian)
--

INSERT INTO `tugas` (`id_tugas`, `nama_tugas`, `deskripsi`, `status`, `batas_waktu`, `dibuat_pada`, `diperbarui_pada`, `id_prioritas`, `id_kategori`) VALUES
(1, 'Desain UI/UX',            'Membuat wireframe dan mockup aplikasi',          'Menunggu', '2026-05-25', '2026-05-19 11:44:10', '2026-05-19 11:44:10', 3, 2),
(2, 'Setup MySQL',             'Membuat skema database',                         'Selesai',  '2026-05-22', '2026-05-19 11:44:10', '2026-05-19 11:44:10', 3, 1),
(3, 'Integrasi CustomTkinter', 'Menghubungkan UI dengan logika Python',          'Menunggu', '2026-05-30', '2026-05-19 11:44:10', '2026-05-19 11:44:10', 2, 1),
(4, 'Pengujian Modul CRUD',    'Menulis test case untuk semua operasi CRUD',     'Menunggu', '2026-06-05', '2026-05-19 11:44:10', '2026-05-19 11:44:10', 2, 3),
(5, 'Dokumentasi Aplikasi',    'Membuat laporan dan manual pengguna',            'Menunggu', '2026-06-10', '2026-05-19 11:44:10', '2026-05-19 11:44:10', 1, 3);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `kategori`
--
ALTER TABLE `kategori`
  ADD PRIMARY KEY (`id_kategori`),
  ADD UNIQUE KEY `nama_kategori` (`nama_kategori`);

--
-- Indexes for table `prioritas`
--
ALTER TABLE `prioritas`
  ADD PRIMARY KEY (`id_prioritas`),
  ADD UNIQUE KEY `nama_prioritas` (`nama_prioritas`);

--
-- Indexes for table `riwayat_tugas`
--
ALTER TABLE `riwayat_tugas`
  ADD PRIMARY KEY (`id_riwayat`),
  ADD KEY `fk_riwayat_tugas` (`id_tugas`);

--
-- Indexes for table `tugas`
--
ALTER TABLE `tugas`
  ADD PRIMARY KEY (`id_tugas`),
  ADD KEY `fk_tugas_prioritas` (`id_prioritas`),
  ADD KEY `fk_tugas_kategori` (`id_kategori`);

--
-- AUTO_INCREMENT for dumped tables
--

ALTER TABLE `kategori`
  MODIFY `id_kategori` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

ALTER TABLE `prioritas`
  MODIFY `id_prioritas` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

ALTER TABLE `riwayat_tugas`
  MODIFY `id_riwayat` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

ALTER TABLE `tugas`
  MODIFY `id_tugas` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- Constraints for dumped tables
--

ALTER TABLE `riwayat_tugas`
  ADD CONSTRAINT `fk_riwayat_tugas` FOREIGN KEY (`id_tugas`) REFERENCES `tugas` (`id_tugas`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `tugas`
  ADD CONSTRAINT `fk_tugas_kategori` FOREIGN KEY (`id_kategori`) REFERENCES `kategori` (`id_kategori`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_tugas_prioritas` FOREIGN KEY (`id_prioritas`) REFERENCES `prioritas` (`id_prioritas`) ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
