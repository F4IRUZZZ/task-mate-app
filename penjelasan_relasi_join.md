# Penjelasan Relasi & JOIN pada Aplikasi Taskmate

---

## 1. Struktur Database

Aplikasi Taskmate menggunakan database `taskmate_db` yang terdiri dari **4 tabel**:

| Tabel | Fungsi |
|---|---|
| `tugas` | Menyimpan semua data tugas (nama, deskripsi, status, deadline) |
| `kategori` | Menyimpan daftar kategori tugas (Dasprogli, Umum, dll.) |
| `prioritas` | Menyimpan tingkat prioritas tugas (Rendah, Sedang, Tinggi) |
| `riwayat_tugas` | Mencatat setiap perubahan status tugas |

---

## 2. Diagram Relasi Antar Tabel

```
┌─────────────┐        ┌──────────────────────────────┐        ┌──────────────────┐
│  prioritas  │        │            tugas             │        │  riwayat_tugas   │
│─────────────│        │──────────────────────────────│        │──────────────────│
│ id_prioritas│◄───────│ id_prioritas (FK)            │        │ id_riwayat (PK)  │
│ nama_       │  N:1   │ id_tugas (PK)                │──1:N──►│ id_tugas (FK)    │
│  prioritas  │        │ nama_tugas                   │        │ status_lama      │
│ tingkat_    │        │ deskripsi                    │        │ status_baru      │
│  prioritas  │        │ status                       │        │ diubah_pada      │
└─────────────┘        │ batas_waktu                  │        └──────────────────┘
                       │ id_kategori (FK) ◄───────────┼──────┐
                       └──────────────────────────────┘      │
                                                             N:1
                                                    ┌─────────────────┐
                                                    │    kategori     │
                                                    │─────────────────│
                                                    │ id_kategori (PK)│
                                                    │ nama_kategori   │
                                                    │ deskripsi       │
                                                    │ dibuat_pada     │
                                                    └─────────────────┘
```

### Penjelasan Relasi:

- **`tugas` → `kategori`** (Many-to-One): Banyak tugas dapat memiliki satu kategori yang sama. Kolom `id_kategori` di tabel `tugas` adalah Foreign Key yang merujuk ke `id_kategori` di tabel `kategori`.

- **`tugas` → `prioritas`** (Many-to-One): Banyak tugas dapat memiliki satu tingkat prioritas yang sama. Kolom `id_prioritas` di tabel `tugas` adalah Foreign Key yang merujuk ke `id_prioritas` di tabel `prioritas`.

- **`tugas` → `riwayat_tugas`** (One-to-Many): Satu tugas dapat memiliki banyak riwayat perubahan status. Kolom `id_tugas` di tabel `riwayat_tugas` adalah Foreign Key yang merujuk ke `id_tugas` di tabel `tugas`.

---

## 3. Definisi Foreign Key di SQL

```sql
-- Relasi tugas → kategori
ALTER TABLE `tugas`
  ADD CONSTRAINT `fk_tugas_kategori`
    FOREIGN KEY (`id_kategori`) REFERENCES `kategori` (`id_kategori`)
    ON UPDATE CASCADE;

-- Relasi tugas → prioritas
ALTER TABLE `tugas`
  ADD CONSTRAINT `fk_tugas_prioritas`
    FOREIGN KEY (`id_prioritas`) REFERENCES `prioritas` (`id_prioritas`)
    ON UPDATE CASCADE;

-- Relasi riwayat_tugas → tugas (CASCADE DELETE)
ALTER TABLE `riwayat_tugas`
  ADD CONSTRAINT `fk_riwayat_tugas`
    FOREIGN KEY (`id_tugas`) REFERENCES `tugas` (`id_tugas`)
    ON DELETE CASCADE ON UPDATE CASCADE;
```

> **ON UPDATE CASCADE** → jika `id_kategori` di tabel `kategori` diubah, maka semua baris di `tugas` yang merujuk ke id tersebut ikut diperbarui otomatis.
>
> **ON DELETE CASCADE** → jika sebuah tugas dihapus dari tabel `tugas`, maka semua riwayat perubahan status tugas tersebut di tabel `riwayat_tugas` ikut terhapus otomatis.

---

## 4. Query JOIN yang Digunakan

JOIN diimplementasikan di file `database.py` pada fungsi `ambil_semua_tugas()`.

### Query Lengkap:

```sql
SELECT t.id_tugas    AS id,
       t.nama_tugas  AS name,
       t.deskripsi   AS description,
       t.status,
       t.batas_waktu AS deadline,
       k.id_kategori,
       k.nama_kategori
FROM   tugas t
LEFT JOIN kategori k ON t.id_kategori = k.id_kategori
ORDER BY (t.batas_waktu IS NULL), t.batas_waktu ASC;
```

### Penjelasan Bagian per Bagian:

```
SELECT t.id_tugas, t.nama_tugas, ...   → Ambil kolom dari tabel tugas (alias: t)
       k.id_kategori, k.nama_kategori  → Ambil kolom dari tabel kategori (alias: k)

FROM tugas t                           → Tabel utama: tugas (diberi alias t)

LEFT JOIN kategori k                   → Gabungkan dengan tabel kategori (alias k)
  ON t.id_kategori = k.id_kategori     → Kondisi: id_kategori di kedua tabel harus sama

ORDER BY (t.batas_waktu IS NULL), t.batas_waktu ASC
                                       → Urutkan: tugas yang ada deadline tampil dulu,
                                         diurutkan dari deadline paling dekat
```

---

## 5. Jenis JOIN: LEFT JOIN

Aplikasi Taskmate menggunakan **LEFT JOIN** (bukan INNER JOIN).

```
Tabel tugas (t)              Tabel kategori (k)
┌────┬────────────┬──────┐   ┌─────┬───────────┐
│ id │ nama_tugas │ id_k │   │ id_k│ nama_kat  │
├────┼────────────┼──────┤   ├─────┼───────────┤
│  1 │ Desain UX  │  1   │   │  1  │ Dasprogli │
│  2 │ Setup DB   │  1   │   │  2  │ Umum      │
│  3 │ Testing    │  2   │   └─────┴───────────┘
│  4 │ Laporan    │  99  │ ← id_k = 99 tidak ada di kategori
└────┴────────────┴──────┘

Hasil LEFT JOIN:
┌────┬────────────┬───────────┐
│ id │ nama_tugas │ nama_kat  │
├────┼────────────┼───────────┤
│  1 │ Desain UX  │ Dasprogli │ ← cocok
│  2 │ Setup DB   │ Dasprogli │ ← cocok
│  3 │ Testing    │ Umum      │ ← cocok
│  4 │ Laporan    │ NULL      │ ← tidak cocok, tetap tampil dengan NULL
└────┴────────────┴───────────┘
```

**Perbedaan LEFT JOIN vs INNER JOIN:**

| | LEFT JOIN | INNER JOIN |
|---|---|---|
| Jika kategori tidak ditemukan | Tugas **tetap tampil**, kolom kategori = NULL | Tugas **tidak tampil** sama sekali |
| Keamanan data | Lebih aman, tidak ada tugas yang hilang | Berisiko tugas menghilang |

Karena menggunakan LEFT JOIN, ketika `nama_kategori` bernilai NULL, aplikasi memberikan nilai fallback `"Umum"`:

```python
# database.py — baris fallback jika JOIN menghasilkan NULL
"kategori": r["nama_kategori"] or "Umum",
```

---

## 6. Alur Kerja JOIN di Aplikasi

```
┌──────────────────────────────────────────────────────────────┐
│                        APLIKASI BERJALAN                     │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  app.py → _refresh_table()                                   │
│  Dipanggil saat: buka app / tambah / hapus / filter tugas    │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  database.py → ambil_semua_tugas()                           │
│  Membangun query SQL dengan LEFT JOIN                        │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  MySQL menjalankan query:                                    │
│  SELECT ... FROM tugas LEFT JOIN kategori ON id_kategori    │
│                                                              │
│  Hasil: setiap baris tugas sudah memiliki nama_kategori      │
│  yang diambil langsung dari tabel kategori                   │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  database.py memproses hasil query menjadi list dictionary   │
│  {id, name, description, kategori, status, deadline}        │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  app.py menampilkan data ke GridCanvas (tabel UI)            │
│  Kolom "Kategori" di tabel = hasil dari JOIN                 │
└──────────────────────────────────────────────────────────────┘
```

---

## 7. Implementasi di Kode Python (database.py)

```python
def ambil_semua_tugas(filter_status="All"):
    con = _get_conn()
    cur = con.cursor(dictionary=True)

    base = """
        SELECT t.id_tugas    AS id,
               t.nama_tugas  AS name,
               t.deskripsi   AS description,
               t.status,
               t.batas_waktu AS deadline,
               k.id_kategori,
               k.nama_kategori          # <-- data dari tabel kategori via JOIN
        FROM   tugas t
        LEFT JOIN kategori k            # <-- JOIN terjadi di sini
          ON t.id_kategori = k.id_kategori
    """

    order = " ORDER BY (t.batas_waktu IS NULL), t.batas_waktu ASC"
    cur.execute(base + order)
    rows = cur.fetchall()

    result = []
    for r in rows:
        result.append({
            "id":       r["id"],
            "name":     r["name"],
            "kategori": r["nama_kategori"] or "Umum",  # fallback jika NULL
            "status":   DB_TO_STATUS.get(r["status"], "Pending"),
            "deadline": str(r["deadline"]) if r["deadline"] else "",
        })
    return result
```

---

## 8. Mengapa JOIN Penting di Aplikasi Ini?

Tanpa JOIN, aplikasi hanya bisa menampilkan `id_kategori` (angka) bukan nama kategorinya:

```
Tanpa JOIN:              Dengan LEFT JOIN:
┌────┬────────────┬─────┐  ┌────┬────────────┬───────────┐
│ ID │ Task Name  │ Kat │  │ ID │ Task Name  │ Kategori  │
├────┼────────────┼─────┤  ├────┼────────────┼───────────┤
│  1 │ Desain UX  │  1  │  │  1 │ Desain UX  │ Dasprogli │
│  2 │ Setup DB   │  1  │  │  2 │ Setup DB   │ Dasprogli │
│  3 │ Testing    │  2  │  │  3 │ Testing    │ Umum      │
└────┴────────────┴─────┘  └────┴────────────┴───────────┘
   Tidak informatif              Informatif & mudah dibaca
```

JOIN menghubungkan data dari dua tabel berbeda sehingga aplikasi dapat menampilkan **informasi yang lengkap dan bermakna** kepada pengguna dalam satu query yang efisien.

---

*Taskmate — Aplikasi Task Manager berbasis Python (CustomTkinter) + MySQL*

---

---

# Penjelasan Tabel `prioritas` dan Relasinya

---

## 9. Tabel `prioritas` — Struktur dan Relasi

Tabel `prioritas` didefinisikan di database dengan struktur sebagai berikut:

```sql
CREATE TABLE `prioritas` (
  `id_prioritas`      INT(11)     NOT NULL AUTO_INCREMENT,
  `nama_prioritas`    VARCHAR(20) NOT NULL,
  `tingkat_prioritas` TINYINT(4)  NOT NULL,
  PRIMARY KEY (`id_prioritas`),
  UNIQUE KEY `nama_prioritas` (`nama_prioritas`)
) ENGINE=InnoDB;

-- Data isi tabel prioritas:
INSERT INTO `prioritas` VALUES
(1, 'Rendah',  1),
(2, 'Sedang',  2),
(3, 'Tinggi',  3);
```

Tabel ini berelasi dengan tabel `tugas` melalui kolom `id_prioritas`:

```sql
-- Kolom id_prioritas di tabel tugas sebagai Foreign Key
CREATE TABLE `tugas` (
  `id_tugas`     INT(11) NOT NULL AUTO_INCREMENT,
  ...
  `id_prioritas` INT(11) NOT NULL DEFAULT 2,   -- FK ke tabel prioritas
  `id_kategori`  INT(11) NOT NULL DEFAULT 2,   -- FK ke tabel kategori
  ...
);

-- Definisi Foreign Key:
ALTER TABLE `tugas`
  ADD CONSTRAINT `fk_tugas_prioritas`
    FOREIGN KEY (`id_prioritas`) REFERENCES `prioritas` (`id_prioritas`)
    ON UPDATE CASCADE;
```

---

## 10. Diagram Relasi Tabel `prioritas`

```
┌──────────────────────┐              ┌───────────────────────────────┐
│       prioritas      │              │             tugas             │
│──────────────────────│              │───────────────────────────────│
│ id_prioritas (PK)  ◄─┼──── N:1 ────┤ id_prioritas (FK)            │
│ nama_prioritas       │              │ id_tugas (PK)                 │
│ tingkat_prioritas    │              │ nama_tugas                    │
└──────────────────────┘              │ deskripsi                     │
                                      │ status                        │
                                      │ batas_waktu                   │
                                      │ id_kategori (FK)              │
                                      └───────────────────────────────┘

Jenis Relasi : Many-to-One (N:1)
Artinya      : Banyak tugas dapat memiliki satu tingkat prioritas yang sama
Contoh       : Tugas A, B, C semuanya bisa ber-prioritas "Sedang" (id=2)
```

---

## 11. Status Relasi `prioritas` di Aplikasi

### Di Level Database — Relasi AKTIF ✅

Relasi antara `tugas` dan `prioritas` **terdefinisi dan aktif** di database. Setiap tugas yang ditambahkan selalu memiliki nilai `id_prioritas`, dan Foreign Key constraint memastikan nilai tersebut valid:

```
Tabel prioritas:          Tabel tugas:
┌─────┬──────────┬───────┐  ┌─────┬──────────────────┬──────────────┐
│ id  │ nama     │tingkat│  │ id  │ nama_tugas       │ id_prioritas │
├─────┼──────────┼───────┤  ├─────┼──────────────────┼──────────────┤
│  1  │ Rendah   │   1   │  │  1  │ Desain UI/UX     │      3       │◄── Tinggi
│  2  │ Sedang   │   2   │  │  2  │ Setup MySQL      │      3       │◄── Tinggi
│  3  │ Tinggi   │   3   │  │  3  │ Integrasi CTk    │      2       │◄── Sedang
└─────┴──────────┴───────┘  │  4  │ Pengujian CRUD   │      2       │◄── Sedang
                             │  5  │ Dokumentasi      │      1       │◄── Rendah
                             └─────┴──────────────────┴──────────────┘
```

### Di Level Aplikasi — Fungsionalitas TIDAK AKTIF ⚠️

Meskipun relasi database aktif, fitur prioritas **tidak ditampilkan di antarmuka pengguna** karena pada proses pengembangan aplikasi fitur ini digantikan oleh **Kategori** yang dinilai lebih relevan dengan kebutuhan pengguna (mahasiswa):

| Aspek | Keterangan |
|---|---|
| Kolom di tabel UI | Tidak ada kolom "Prioritas" |
| Form input | Tidak ada pilihan input prioritas |
| Filter | Tidak ada filter berdasarkan prioritas |
| Query SQL | `id_prioritas` di-hardcode ke nilai `2` (Sedang) |

Bukti di kode `database.py` fungsi `tambah_tugas()`:

```python
def tambah_tugas(name, description, kategori, deadline):
    cur.execute("""
        INSERT INTO tugas (nama_tugas, deskripsi, status, batas_waktu, id_prioritas, id_kategori)
        VALUES (%s, %s, 'Menunggu', %s, 2, %s)
    """, (name, description, dl, id_kat))
    #                              ↑
    #              id_prioritas selalu = 2 (Sedang), tidak dari input user
```

---

## 12. Mengapa Tabel `prioritas` Tetap Dipertahankan?

Meskipun tidak aktif digunakan di antarmuka, tabel `prioritas` tetap dipertahankan karena beberapa alasan:

**1. Integritas Relasi Database**
Menghapus tabel `prioritas` memerlukan penghapusan kolom `id_prioritas` dari tabel `tugas` dan constraint FK-nya. Proses ini berisiko merusak struktur database yang sudah berjalan.

**2. Bukti Desain Database yang Terencana**
Keberadaan tabel `prioritas` menunjukkan bahwa database dirancang dengan mempertimbangkan fitur masa depan. Ini adalah praktik desain database yang baik (*forward-thinking design*).

**3. Potensi Pengembangan Selanjutnya**
Fitur prioritas dapat diaktifkan kembali di versi berikutnya tanpa perlu mengubah struktur database — cukup menambahkan form input dan kolom di UI.

```
Versi Saat Ini:           Potensi Versi Berikutnya:
┌──────────────────┐      ┌──────────────────────────┐
│ Form Input:      │      │ Form Input:              │
│  - Task Name     │      │  - Task Name             │
│  - Description   │      │  - Description           │
│  - Kategori      │      │  - Kategori              │
│  - Deadline      │      │  - Deadline              │
│                  │      │  - Prioritas  ← AKTIF    │
└──────────────────┘      └──────────────────────────┘
```

---

## 13. Ringkasan Seluruh Relasi Database Taskmate

| Relasi | Tabel Asal | Tabel Tujuan | Jenis | Status di Aplikasi |
|---|---|---|---|---|
| `fk_tugas_kategori` | `tugas` | `kategori` | Many-to-One | ✅ Aktif (JOIN digunakan) |
| `fk_tugas_prioritas` | `tugas` | `prioritas` | Many-to-One | ⚠️ Ada di DB, tidak di UI |
| `fk_riwayat_tugas` | `riwayat_tugas` | `tugas` | Many-to-One | ✅ Aktif (CASCADE DELETE) |

---

*Taskmate — Aplikasi Task Manager berbasis Python (CustomTkinter) + MySQL*