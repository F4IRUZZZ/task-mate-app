# 📋 Dokumentasi Aplikasi TaskMate

> Dokumentasi ini menjelaskan fungsi setiap bagian kode pada aplikasi **TaskMate**, penjelasan file `database.py`, serta relasi antar tabel di database.

---

## Daftar Isi

1. [Gambaran Umum Aplikasi](#1-gambaran-umum-aplikasi)
2. [Struktur File Proyek](#2-struktur-file-proyek)
3. [File `database.py`](#3-file-databasepy)
   - [Konfigurasi Koneksi](#31-konfigurasi-koneksi-db_config)
   - [Tabel Mapping](#32-tabel-mapping)
   - [Fungsi-Fungsi Database](#33-fungsi-fungsi-database)
4. [File `app.py`](#4-file-apppy)
   - [Import & Konfigurasi Tema](#41-import--konfigurasi-tema)
   - [Class `CustomCalendar`](#42-class-customcalendar)
   - [Class `TaskmateApp`](#43-class-taskmateapp)
   - [Metode Pembangun UI](#44-metode-pembangun-ui)
   - [Logika CRUD](#45-logika-crud)
   - [Fitur Autocomplete](#46-fitur-autocomplete)
   - [Fitur Kalender Popup](#47-fitur-kalender-popup)
   - [Refresh Tabel & Status Bar](#48-refresh-tabel--status-bar)
   - [Event Pemilihan Baris](#49-event-pemilihan-baris)
   - [Entry Point](#410-entry-point)
5. [File `taskmate_db.sql` — Skema Database](#5-file-taskmate_dbsql--skema-database)
   - [Tabel `prioritas`](#51-tabel-prioritas)
   - [Tabel `kategori`](#52-tabel-kategori)
   - [Tabel `tugas`](#53-tabel-tugas)
   - [Tabel `riwayat_tugas`](#54-tabel-riwayat_tugas)
6. [Relasi Antar Tabel](#6-relasi-antar-tabel)
7. [Alur Data Aplikasi](#7-alur-data-aplikasi)

---

## 1. Gambaran Umum Aplikasi

TaskMate adalah aplikasi manajemen tugas berbasis desktop yang dibangun menggunakan:

- **Python** sebagai bahasa pemrograman utama
- **CustomTkinter** untuk tampilan antarmuka (UI) modern bertema gelap
- **MySQL** sebagai sistem penyimpanan data (database)
- **mysql-connector-python** sebagai jembatan antara Python dan MySQL

Aplikasi ini memungkinkan pengguna menambah, memperbarui, menghapus, memfilter, dan menandai tugas sebagai selesai, dilengkapi fitur kalender popup dan autocomplete nama tugas.

---

## 2. Struktur File Proyek

```
TaskMate/
├── app.py            # File utama — antarmuka pengguna (UI)
├── database.py       # Modul koneksi dan operasi database
└── taskmate_db.sql   # Skema dan data awal database MySQL
```

---

## 3. File `database.py`

File ini adalah **lapisan data (data layer)** aplikasi. Semua komunikasi dengan database MySQL terpusat di sini, sehingga `app.py` tidak perlu menulis query SQL secara langsung.

---

### 3.1 Konfigurasi Koneksi (`DB_CONFIG`)

```python
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "database": "taskmate_db",
    "user":     "root",
    "password": "",
}
```

`DB_CONFIG` adalah dictionary Python yang menyimpan semua parameter koneksi ke server MySQL. Nilai-nilai ini diteruskan ke `mysql.connector.connect()` setiap kali aplikasi perlu mengakses database.

| Key | Keterangan |
|---|---|
| `host` | Alamat server MySQL (localhost = komputer sendiri) |
| `port` | Port MySQL standar (3306) |
| `database` | Nama database yang digunakan |
| `user` | Username MySQL |
| `password` | Password MySQL (kosong = tanpa password) |

---

### 3.2 Tabel Mapping

```python
PRIORITY_TO_ID = {"Low": 1, "Medium": 2, "High": 3}
ID_TO_PRIORITY = {1: "Low", 2: "Medium", 3: "High"}
STATUS_TO_DB   = {"Pending": "Menunggu", "Completed": "Selesai", "All": None}
DB_TO_STATUS   = {"Menunggu": "Pending", "Selesai": "Completed"}
```

Empat dictionary ini berfungsi sebagai **penerjemah dua arah** antara nilai yang ditampilkan di UI (Bahasa Inggris) dan nilai yang tersimpan di database (Bahasa Indonesia/ID angka).

- `PRIORITY_TO_ID` — mengubah label prioritas menjadi angka ID untuk disimpan ke kolom `id_prioritas`
- `ID_TO_PRIORITY` — kebalikannya, mengubah ID angka kembali menjadi label teks untuk ditampilkan
- `STATUS_TO_DB` — mengubah status UI menjadi nilai enum database (`"Menunggu"` / `"Selesai"`)
- `DB_TO_STATUS` — kebalikannya, untuk keperluan tampilan di tabel

---

### 3.3 Fungsi-Fungsi Database

#### `_get_conn()`

```python
def _get_conn():
    return mysql.connector.connect(**DB_CONFIG)
```

Fungsi **privat** (diawali `_`) yang membuat dan mengembalikan objek koneksi baru ke MySQL setiap kali dipanggil. Digunakan sebagai helper internal oleh semua fungsi database lainnya. Pola ini disebut *connection-per-operation* — koneksi dibuka saat dibutuhkan dan ditutup segera setelah selesai.

---

#### `test_koneksi()`

```python
def test_koneksi():
    try:
        con = _get_conn()
        con.close()
        return True, "OK"
    except Exception as e:
        return False, str(e)
```

Mencoba membuka koneksi ke database dan langsung menutupnya. Dipanggil saat aplikasi pertama kali dijalankan. Mengembalikan tuple `(True, "OK")` jika berhasil, atau `(False, pesan_error)` jika gagal. Jika gagal, aplikasi akan menampilkan dialog error dan berhenti.

---

#### `ambil_semua_tugas(filter_status="All")`

```python
def ambil_semua_tugas(filter_status="All"):
```

Mengambil seluruh data tugas dari tabel `tugas` di database, diurutkan dari ID terbesar ke terkecil (tugas terbaru tampil di atas). Mendukung parameter `filter_status`:

- `"All"` → ambil semua tugas tanpa filter
- `"Pending"` → hanya tugas berstatus `"Menunggu"`
- `"Completed"` → hanya tugas berstatus `"Selesai"`

Setiap baris hasil query diubah menjadi dictionary Python dengan key yang rapi (`id`, `name`, `description`, `priority`, `status`, `deadline`) menggunakan mapping yang sudah didefinisikan sebelumnya, sebelum dikembalikan ke `app.py`.

---

#### `ambil_semua_nama_tugas()`

```python
def ambil_semua_nama_tugas():
```

Mengambil seluruh nama tugas yang unik (`DISTINCT`) dari database, diurutkan secara alfabetis. Hasilnya digunakan sebagai **bank data autocomplete** di field "Task Name". Jika terjadi error, fungsi ini mengembalikan list kosong `[]` tanpa melempar exception, sehingga fitur autocomplete hanya tidak tampil (tidak crash).

---

#### `tambah_tugas(name, description, priority, deadline)`

```python
def tambah_tugas(name, description, priority, deadline):
```

Menyimpan tugas baru ke database dalam **satu transaksi** yang mencakup dua operasi INSERT:

1. INSERT ke tabel `tugas` — menyimpan data utama tugas dengan status awal `'Menunggu'`
2. INSERT ke tabel `riwayat_tugas` — mencatat perubahan status awal (`NULL → 'Menunggu'`) sebagai entri pertama di log riwayat

`con.commit()` dipanggil setelah kedua INSERT berhasil, memastikan data hanya tersimpan jika kedua operasi sukses (atomik).

---

#### `perbarui_tugas(task_id, name, description, priority, deadline)`

```python
def perbarui_tugas(task_id, task_id, name, description, priority, deadline):
```

Memperbarui data tugas yang sudah ada berdasarkan `task_id`. Kolom yang diperbarui adalah `nama_tugas`, `deskripsi`, `batas_waktu`, dan `id_prioritas`. Kolom `status` tidak diubah di sini — perubahan status ditangani oleh fungsi `tandai_selesai()` secara terpisah.

---

#### `hapus_tugas(task_id)`

```python
def hapus_tugas(task_id):
```

Menghapus satu baris tugas dari tabel `tugas` berdasarkan `id_tugas`. Karena ada constraint `ON DELETE CASCADE` antara `tugas` dan `riwayat_tugas`, semua entri riwayat yang terkait dengan tugas tersebut akan **terhapus otomatis** oleh MySQL.

---

#### `tandai_selesai(task_id)`

```python
def tandai_selesai(task_id):
```

Mengubah status tugas menjadi `'Selesai'` dalam satu transaksi dengan tiga langkah:

1. **SELECT** — membaca status tugas saat ini sebagai `status_lama`
2. **UPDATE** — mengubah kolom `status` menjadi `'Selesai'`
3. **INSERT** ke `riwayat_tugas` — mencatat perubahan status (misal: `'Menunggu' → 'Selesai'`) beserta timestamp otomatis

---

## 4. File `app.py`

File ini adalah **lapisan presentasi (presentation layer)** aplikasi — bertanggung jawab atas semua yang terlihat dan berinteraksi dengan pengguna.

---

### 4.1 Import & Konfigurasi Tema

```python
import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
from datetime import datetime
import calendar as _cal
import database as db
```

| Import | Fungsi |
|---|---|
| `customtkinter` | Library UI modern bertema gelap/terang |
| `tkinter.ttk` | Widget Treeview untuk tabel data |
| `tkinter.messagebox` | Dialog konfirmasi dan peringatan |
| `tkinter` | Widget dasar (Toplevel, Canvas, Listbox, dll.) |
| `datetime` | Validasi dan parsing format tanggal |
| `calendar` | Menghitung hari pertama & jumlah hari dalam sebulan untuk kalender |
| `database` | Modul koneksi database yang dibuat sendiri |

```python
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
```

Dua baris ini mengatur tema global aplikasi ke mode gelap dengan aksen warna biru. Dijalankan sekali saat modul dimuat.

```python
BG_COLOR = "#242424"
FRAME_COLOR = "#2B2B2B"
# ... dst
```

Konstanta warna hex yang mendefinisikan seluruh palet warna aplikasi. Menyimpan warna di satu tempat memudahkan perubahan tema secara konsisten di seluruh komponen.

---

### 4.2 Class `CustomCalendar`

```python
class CustomCalendar(tk.Toplevel):
```

Popup kalender kustom bertema gelap yang dibuat dari awal menggunakan `tk.Canvas`. Mewarisi `tk.Toplevel` sehingga tampil sebagai jendela mengambang di atas aplikasi utama.

#### Konstanta Kelas

| Konstanta | Keterangan |
|---|---|
| `CW = 46` | Lebar satu sel hari (pixel) |
| `CH = 42` | Tinggi satu sel hari (pixel) |
| `PAD = 14` | Padding horizontal kalender |
| `RADIUS = 18` | Radius lingkaran highlight hari yang dipilih |
| `DAYS_SHORT` | Label singkat nama hari (Mo, Tu, We, ...) |
| `MONTHS_ID` | Nama bulan dalam Bahasa Indonesia |

#### `__init__(...)`

Konstruktor yang menerima:
- `parent` — jendela induk
- `on_select` — fungsi callback yang dipanggil saat pengguna memilih tanggal
- `anchor_x, btn_top, btn_bottom` — koordinat tombol kalender, digunakan untuk menghitung posisi popup agar muncul tepat di bawah (atau di atas jika ruang tidak cukup) tombol
- `initial_date` — tanggal awal yang ditampilkan (opsional)

Konstruktor juga menangani penempatan popup agar tidak keluar dari batas layar (`screen_w`, `screen_h`) dan menutup diri saat tombol `Escape` ditekan.

#### `_build_ui()`

Membangun seluruh komponen visual kalender:
- **Header navigasi** — label bulan/tahun dan tombol panah `◀` / `▶`
- **Baris nama hari** — grid 7 kolom (Sen–Min) dengan warna berbeda untuk akhir pekan
- **Canvas kalender** — area gambar interaktif untuk grid tanggal
- **Footer** — tombol "Hari Ini" dan "Hapus tanggal"

#### `_draw()`

Fungsi inti rendering yang menggambar ulang seluruh grid tanggal di canvas setiap kali state berubah (hover, pilih, ganti bulan). Menggunakan `_cal.monthrange()` untuk mengetahui hari pertama bulan dan jumlah hari. Setiap sel memiliki tampilan visual yang berbeda berdasarkan kondisinya:

| Kondisi | Tampilan |
|---|---|
| Dipilih (`is_sel`) | Lingkaran solid biru + teks putih tebal |
| Hari ini (`is_today`) | Ring garis hijau + teks hijau tebal |
| Hover (`is_hovered`) | Lingkaran abu-abu gelap |
| Akhir pekan | Teks berwarna biru muda |
| Hari biasa | Teks abu-abu terang |

#### `_xy_to_cell(x, y)`

Mengkonversi koordinat piksel dari event mouse menjadi posisi baris dan kolom di grid kalender. Digunakan oleh event handler hover dan klik.

#### `_on_motion(event)`, `_on_leave(event)`, `_on_click(event)`

Event handler untuk interaksi mouse di canvas:
- `_on_motion` — mendeteksi sel yang sedang di-hover dan memicu redraw
- `_on_leave` — membersihkan state hover saat kursor keluar dari canvas
- `_on_click` — mencatat tanggal yang dipilih, memanggil callback `on_select`, lalu menutup popup setelah 150ms

#### `_change_month(delta)`

Menggeser tampilan bulan sebesar `delta` (+1 atau -1). Menangani perpindahan tahun secara otomatis (misal: Januari → Desember tahun sebelumnya).

#### `_go_today(event)` dan `_clear_date(event)`

- `_go_today` — melompat ke bulan saat ini dan memilih hari ini
- `_clear_date` — menghapus pilihan tanggal dan menutup popup

---

### 4.3 Class `TaskmateApp`

```python
class TaskmateApp(ctk.CTk):
```

Kelas utama aplikasi. Mewarisi `ctk.CTk` (jendela utama CustomTkinter).

#### `__init__()`

Inisialisasi aplikasi:
1. Mengatur judul, ukuran, dan warna latar jendela utama
2. **Mengecek koneksi database** — jika gagal, menampilkan dialog error dan menutup aplikasi
3. Menginisialisasi variabel state aplikasi:
   - `self.tasks` — list tugas yang sedang ditampilkan (diisi dari database)
   - `self.selected_id` — ID tugas yang sedang dipilih di tabel (`None` jika tidak ada)
   - `self.filter_mode` — mode filter aktif (`"All"`, `"Pending"`, `"Completed"`)
   - `self.all_task_names` — set nama tugas untuk keperluan autocomplete
   - `self.autocomplete_win` — referensi ke popup autocomplete aktif
   - `self._cal_popup` — referensi ke popup kalender aktif
4. Memanggil `_build_ui()` untuk membangun antarmuka
5. Memanggil `_refresh_table()` untuk memuat data pertama kali dari database

---

### 4.4 Metode Pembangun UI

#### `_build_ui()`

Mengatur grid utama jendela (2 baris: form di atas, tabel di bawah) lalu mendelegasikan pembangunan ke dua metode berikut.

#### `_build_form_frame()`

Membangun panel atas yang berisi formulir input tugas, terdiri dari:

- **Header** — ikon dan judul "Taskmate"
- **Garis pemisah** — dekoratif antara header dan form
- **Kolom Kiri:**
  - Field "Task Name" dengan wrapper khusus untuk posisi autocomplete
  - Label hint readonly (tersembunyi, muncul saat mode edit)
  - Field "Description" (textbox multiline)
- **Kolom Kanan:**
  - ComboBox "Priority" (Low / Medium / High, readonly)
  - Field "Deadline" dengan tombol 📅 di sampingnya
- **Baris Tombol:**
  - `Add Task` — menambah tugas baru
  - `Update Task` — memperbarui tugas yang dipilih
  - `Delete Task` — menghapus tugas yang dipilih
  - `Clear Form` — mengosongkan formulir

#### `_build_table_frame()`

Membangun panel bawah yang berisi tabel daftar tugas, terdiri dari:

- **Controls Bar:**
  - Label "Filter by Status"
  - `SegmentedButton` (All / Pending / Completed) — memfilter tabel secara langsung saat diklik
  - Tombol `Mark as Completed` — menandai tugas terpilih sebagai selesai
- **Treeview (Tabel)** — komponen dari `tkinter.ttk` yang menampilkan data dalam 5 kolom: ID, Task Name, Priority, Status, Deadline. Di-style ulang dengan tema gelap menggunakan `ttk.Style`. Dilengkapi scrollbar vertikal.
- **Tag Warna Baris:**
  - Baris genap/ganjil bergantian warna (zebra striping)
  - Tugas selesai — teks hijau muda
  - Prioritas High — teks merah muda
  - Prioritas Medium — teks kuning
  - Prioritas Low — teks hijau muda
- **Status Bar** — menampilkan jumlah total tugas dan ID tugas yang sedang dipilih

---

### 4.5 Logika CRUD

#### `_get_form_values()`

Helper yang membaca dan mengembalikan nilai keempat field form (`name`, `desc`, `priority`, `deadline`) sekaligus. Dipanggil oleh `_add_task()` dan `_update_task()`.

#### `_validate_deadline(deadline)`

Memvalidasi format string tanggal deadline menggunakan `datetime.strptime()`. Mengembalikan `True` jika format benar (`YYYY-MM-DD`) atau field kosong, `False` jika format salah.

#### `_add_task()`

Alur kerja menambah tugas baru:
1. Ambil nilai form via `_get_form_values()`
2. Validasi: nama tidak boleh kosong, format deadline harus benar
3. Panggil `db.tambah_tugas()` untuk menyimpan ke database
4. Jika berhasil: tambahkan nama ke bank autocomplete, kosongkan form, refresh tabel

#### `_update_task()`

Alur kerja memperbarui tugas:
1. Cek apakah ada tugas yang dipilih (`selected_id`)
2. Ambil dan validasi nilai form
3. Panggil `db.perbarui_tugas()` dengan ID tugas yang dipilih
4. Jika berhasil: kosongkan form, refresh tabel

#### `_delete_task()`

Alur kerja menghapus tugas:
1. Cek apakah ada tugas yang dipilih
2. Tampilkan dialog konfirmasi dengan nama tugas
3. Jika pengguna mengkonfirmasi: panggil `db.hapus_tugas()`
4. Jika berhasil: kosongkan form, refresh tabel

#### `_mark_completed()`

Alur kerja menandai selesai:
1. Cek apakah ada tugas yang dipilih
2. Panggil `db.tandai_selesai()` — status diubah dan riwayat dicatat di database
3. Reset `selected_id`, refresh tabel

#### `_clear_form()`

Mereset semua komponen form ke kondisi awal:
- Mengaktifkan kembali field name & description (jika terkunci)
- Menutup popup kalender jika terbuka
- Mengosongkan semua field input
- Menghapus seleksi baris di tabel
- Memperbarui status bar

#### `_disable_name_desc()` dan `_enable_name_desc()`

Sepasang metode untuk mengunci/membuka kembali field "Task Name" dan "Description":
- `_disable_name_desc()` — dipanggil saat pengguna memilih baris di tabel (mode edit). Field dikunci dan ditampilkan dengan warna abu-abu lebih gelap, disertai label hint peringatan `🔒 Tidak dapat diedit saat memilih task`
- `_enable_name_desc()` — dipanggil saat `_clear_form()` (mode tambah baru). Field dikembalikan ke tampilan dan state normal

---

### 4.6 Fitur Autocomplete

#### `_on_name_keyrelease(event)`

Event handler yang terpasang pada field "Task Name". Dipanggil setiap kali pengguna melepas tombol keyboard. Mengabaikan tombol navigasi (Up, Down, Enter, Escape, dll.) dan hanya memproses karakter teks. Jika keyword minimal 1 karakter, mencari kecocokan di `self.all_task_names` (case-insensitive) dan menampilkan popup.

#### `_show_autocomplete(matches)`

Membuat jendela popup `tk.Toplevel` yang mengandung `tk.Listbox` berisi daftar saran nama tugas. Popup diposisikan tepat di bawah field "Task Name" dengan lebar yang sama. Maksimal menampilkan 6 item sekaligus; jika lebih, scrollbar muncul otomatis. Saat item dipilih (klik atau Enter), nama dipasang ke field dan popup ditutup.

#### `_hide_autocomplete(event=None)`

Menutup dan menghancurkan popup autocomplete. Dipanggil saat field kehilangan fokus (dengan delay 150ms agar klik pada listbox sempat diproses), saat Escape ditekan, atau saat baris tabel dipilih.

#### `_autocomplete_focus_list(event=None)`

Memindahkan fokus keyboard dari field "Task Name" ke listbox autocomplete saat tombol panah bawah (`↓`) ditekan, sehingga pengguna bisa navigasi dengan keyboard tanpa menyentuh mouse.

---

### 4.7 Fitur Kalender Popup

#### `_open_calendar()`

Membuka popup `CustomCalendar`. Jika popup sudah terbuka, menekan tombol yang sama akan menutupnya (toggle). Menghitung posisi popup berdasarkan koordinat layar tombol 📅. Memasang event listener pada jendela utama untuk menutup popup saat pengguna klik di area luar popup.

Callback `on_date_selected` yang diteruskan ke `CustomCalendar` akan memasukkan tanggal yang dipilih (format `YYYY-MM-DD`) ke field "Deadline", atau mengosongkan field jika pengguna menekan "Hapus".

---

### 4.8 Refresh Tabel & Status Bar

#### `_refresh_table()`

Memperbarui seluruh isi tabel dengan data terkini dari database:
1. Hapus semua baris yang ada di tabel
2. Panggil `db.ambil_semua_tugas()` dengan filter yang aktif
3. Masukkan ulang setiap tugas ke tabel dengan tag warna yang sesuai (berdasarkan status dan prioritas)
4. Perbarui status bar

#### `_update_status_bar()`

Memperbarui teks di bagian bawah tabel dengan informasi: jumlah total tugas yang ditampilkan dan ID tugas yang sedang dipilih (atau "No task selected" jika tidak ada).

---

### 4.9 Event Pemilihan Baris

#### `_on_row_select(event)`

Event handler yang dipanggil setiap kali pengguna mengklik baris di tabel. Logikanya:

1. Ambil `task_id` dari baris yang dipilih
2. Jika `task_id` sama dengan yang sudah dipilih → **deselect** (klik baris yang sama = batalkan pilihan)
3. Jika berbeda → cari data tugas dari `self.tasks`
4. Isi semua field form dengan data tugas tersebut
5. **Kunci field name & description** (`_disable_name_desc()`) karena nama tugas tidak boleh diubah melalui form edit — hanya prioritas dan deadline yang bisa dimodifikasi
6. Perbarui status bar dengan ID tugas yang dipilih

---

### 4.10 Entry Point

```python
if __name__ == "__main__":
    app = TaskmateApp()
    app.mainloop()
```

Blok standar Python yang memastikan aplikasi hanya dijalankan saat file `app.py` dieksekusi langsung (bukan saat diimport oleh modul lain). `app.mainloop()` memulai event loop GUI yang terus berjalan hingga jendela ditutup.

---

## 5. File `taskmate_db.sql` — Skema Database

Database `taskmate_db` terdiri dari **4 tabel** yang saling terhubung.

---

### 5.1 Tabel `prioritas`

> Tabel referensi level prioritas tugas.

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id_prioritas` | `INT` AUTO_INCREMENT | Primary Key |
| `nama_prioritas` | `VARCHAR(20)` | Nama prioritas (`Rendah`, `Sedang`, `Tinggi`) |
| `tingkat_prioritas` | `TINYINT` | Angka urutan (1 = rendah, 3 = tinggi) |

**Data awal:**

| id | nama | tingkat |
|---|---|---|
| 1 | Rendah | 1 |
| 2 | Sedang | 2 |
| 3 | Tinggi | 3 |

---

### 5.2 Tabel `kategori`

> Tabel referensi kategori/jenis tugas.

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id_kategori` | `INT` AUTO_INCREMENT | Primary Key |
| `nama_kategori` | `VARCHAR(50)` UNIQUE | Nama kategori (unik) |
| `deskripsi` | `TEXT` | Penjelasan kategori (opsional) |
| `dibuat_pada` | `TIMESTAMP` | Waktu kategori dibuat (otomatis) |

**Data awal:** Pengembangan, Desain, Pengujian, Manajemen.

> Catatan: Tabel `kategori` saat ini belum digunakan di antarmuka `app.py`, namun tersedia di database untuk pengembangan fitur ke depan.

---

### 5.3 Tabel `tugas`

> Tabel inti yang menyimpan semua data tugas.

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id_tugas` | `INT` AUTO_INCREMENT | Primary Key |
| `nama_tugas` | `VARCHAR(255)` | Nama / judul tugas |
| `deskripsi` | `TEXT` | Keterangan detail tugas (opsional) |
| `status` | `ENUM('Menunggu','Selesai')` | Status tugas, default `'Menunggu'` |
| `batas_waktu` | `DATE` | Tanggal deadline (opsional) |
| `dibuat_pada` | `TIMESTAMP` | Waktu tugas dibuat (otomatis) |
| `diperbarui_pada` | `TIMESTAMP` | Waktu terakhir diperbarui (otomatis) |
| `id_prioritas` | `INT` | Foreign Key → `prioritas.id_prioritas` (wajib diisi) |
| `id_kategori` | `INT` | Foreign Key → `kategori.id_kategori` (opsional) |

---

### 5.4 Tabel `riwayat_tugas`

> Tabel log yang mencatat setiap perubahan status tugas.

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id_riwayat` | `INT` AUTO_INCREMENT | Primary Key |
| `status_lama` | `VARCHAR(20)` | Status sebelum perubahan (`NULL` jika tugas baru) |
| `status_baru` | `VARCHAR(20)` | Status setelah perubahan |
| `diubah_pada` | `TIMESTAMP` | Waktu perubahan terjadi (otomatis) |
| `id_tugas` | `INT` | Foreign Key → `tugas.id_tugas` |

Tabel ini berfungsi sebagai **audit trail** — setiap kali status tugas berubah (termasuk saat pertama dibuat), satu baris baru ditambahkan di sini.

---

## 6. Relasi Antar Tabel

```
┌─────────────┐       ┌────────────────────────────────────────┐
│  prioritas  │       │                 tugas                  │
│─────────────│       │────────────────────────────────────────│
│ id_prioritas│◄──┐   │ id_tugas         (PK, AUTO_INCREMENT)  │
│ nama_priors │   └───│ id_prioritas     (FK, NOT NULL)        │
│ tingkat_pri │       │ id_kategori      (FK, NULLABLE)        │
└─────────────┘       │ nama_tugas                             │
                      │ deskripsi                              │
┌─────────────┐       │ status           ENUM                  │
│  kategori   │       │ batas_waktu                            │
│─────────────│       │ dibuat_pada                            │
│ id_kategori │◄──────│ diperbarui_pada                        │
│ nama_kateg  │       └──────────────────┬─────────────────────┘
│ deskripsi   │                          │
│ dibuat_pada │                          │ (ON DELETE CASCADE)
└─────────────┘                          │
                                         ▼
                      ┌────────────────────────────────────────┐
                      │            riwayat_tugas               │
                      │────────────────────────────────────────│
                      │ id_riwayat       (PK, AUTO_INCREMENT)  │
                      │ id_tugas         (FK, NOT NULL)        │
                      │ status_lama      (NULLABLE)            │
                      │ status_baru                            │
                      │ diubah_pada                            │
                      └────────────────────────────────────────┘
```

### Penjelasan Relasi

#### 1. `prioritas` → `tugas` (One-to-Many)

- **Jenis:** Satu prioritas dapat dimiliki oleh banyak tugas
- **Foreign Key:** `tugas.id_prioritas` → `prioritas.id_prioritas`
- **Constraint:** `NOT NULL` — setiap tugas wajib memiliki prioritas
- **ON UPDATE CASCADE** — jika `id_prioritas` di tabel `prioritas` diubah, nilai FK di `tugas` ikut diperbarui otomatis
- **Contoh:** Semua tugas dengan prioritas "Tinggi" memiliki `id_prioritas = 3`

#### 2. `kategori` → `tugas` (One-to-Many)

- **Jenis:** Satu kategori dapat mencakup banyak tugas
- **Foreign Key:** `tugas.id_kategori` → `kategori.id_kategori`
- **Constraint:** `NULLABLE` — tugas boleh tidak memiliki kategori
- **ON DELETE SET NULL** — jika sebuah kategori dihapus, kolom `id_kategori` di tugas yang menggunakannya akan diset `NULL` (tugas tidak ikut terhapus)
- **ON UPDATE CASCADE** — perubahan ID kategori menyebar otomatis ke semua tugas terkait

#### 3. `tugas` → `riwayat_tugas` (One-to-Many)

- **Jenis:** Satu tugas dapat memiliki banyak entri riwayat
- **Foreign Key:** `riwayat_tugas.id_tugas` → `tugas.id_tugas`
- **ON DELETE CASCADE** — jika tugas dihapus, semua entri riwayatnya ikut terhapus otomatis
- **ON UPDATE CASCADE** — perubahan ID tugas menyebar ke riwayat terkait
- **Contoh alur riwayat satu tugas:**

| id_riwayat | status_lama | status_baru | diubah_pada |
|---|---|---|---|
| 1 | `NULL` | `Menunggu` | saat tugas dibuat |
| 2 | `Menunggu` | `Selesai` | saat ditandai selesai |

---

## 7. Alur Data Aplikasi

Berikut gambaran alur ketika pengguna melakukan operasi umum:

```
[Pengguna klik "Add Task"]
        │
        ▼
  app.py: _add_task()
        │  validasi input
        ▼
  database.py: tambah_tugas()
        │  INSERT INTO tugas ...
        │  INSERT INTO riwayat_tugas (NULL → 'Menunggu')
        │  con.commit()
        ▼
  app.py: _refresh_table()
        │  db.ambil_semua_tugas()
        │  SELECT dari tabel tugas
        ▼
  [Data tampil di Treeview]


[Pengguna klik "Mark as Completed"]
        │
        ▼
  app.py: _mark_completed()
        │
        ▼
  database.py: tandai_selesai()
        │  SELECT status lama
        │  UPDATE tugas SET status = 'Selesai'
        │  INSERT INTO riwayat_tugas ('Menunggu' → 'Selesai')
        │  con.commit()
        ▼
  app.py: _refresh_table()
        ▼
  [Baris tugas berubah warna hijau di tabel]
```

---

*Dokumentasi ini dibuat otomatis berdasarkan analisis kode sumber TaskMate versi terakhir (21 Mei 2026).*