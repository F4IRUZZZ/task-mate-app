import mysql.connector

DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "database": "taskmate_db",
    "user":     "root",
    "password": "",
}

KATEGORI_TO_ID = {"Dasprogli": 1, "Umum": 2}
ID_TO_KATEGORI = {1: "Dasprogli", 2: "Umum"}
STATUS_TO_DB   = {"Pending": "Menunggu", "Completed": "Selesai", "All": None}
DB_TO_STATUS   = {"Menunggu": "Pending", "Selesai": "Completed"}


def _get_conn():
    return mysql.connector.connect(**DB_CONFIG)


def test_koneksi():
    try:
        con = _get_conn(); con.close()
        return True, "OK"
    except Exception as e:
        return False, str(e)


# ── Ambil semua kategori ──────────────────────────────────────────────────────
def ambil_semua_kategori():
    """Kembalikan list nama kategori dari database."""
    try:
        con = _get_conn(); cur = con.cursor()
        cur.execute("SELECT nama_kategori FROM kategori ORDER BY id_kategori")
        rows = [r[0] for r in cur.fetchall()]
        cur.close(); con.close()
        return rows
    except Exception:
        return ["Dasprogli", "Umum"]


# ── Tambah kategori baru jika belum ada ───────────────────────────────────────
def tambah_kategori_baru(nama_kategori):
    """
    Insert kategori baru ke tabel kategori jika belum ada.
    Kembalikan id_kategori yang bersesuaian.
    """
    try:
        con = _get_conn(); cur = con.cursor()
        # Cek apakah sudah ada
        cur.execute("SELECT id_kategori FROM kategori WHERE nama_kategori=%s",
                    (nama_kategori,))
        row = cur.fetchone()
        if row:
            cur.close(); con.close()
            return row[0]
        # Belum ada → insert
        cur.execute(
            "INSERT INTO kategori (nama_kategori) VALUES (%s)",
            (nama_kategori,))
        new_id = cur.lastrowid
        con.commit(); cur.close(); con.close()
        return new_id
    except Exception as e:
        raise RuntimeError(f"Gagal menambah kategori: {e}")


# ── Ambil semua tugas ─────────────────────────────────────────────────────────
def ambil_semua_tugas(filter_status="All"):
    try:
        con = _get_conn(); cur = con.cursor(dictionary=True)
        base  = """
            SELECT t.id_tugas    AS id,
                   t.nama_tugas  AS name,
                   t.deskripsi   AS description,
                   t.status,
                   t.batas_waktu AS deadline,
                   k.id_kategori,
                   k.nama_kategori
            FROM   tugas t
            LEFT JOIN kategori k ON t.id_kategori = k.id_kategori
        """
        order = (
            " ORDER BY"
            "  CASE t.status WHEN 'Selesai' THEN 2 ELSE 0 END ASC,"   # selesai paling bawah
            "  (t.batas_waktu IS NULL) ASC,"                           # tanpa deadline setelah yang ada deadline
            "  t.batas_waktu ASC"                                      # deadline terdekat paling atas
        )
        if filter_status == "All":
            cur.execute(base + order)
        else:
            db_s = STATUS_TO_DB.get(filter_status, "Menunggu")
            cur.execute(base + " WHERE t.status=%s" + order, (db_s,))
        rows = cur.fetchall(); cur.close(); con.close()
        result = []
        for r in rows:
            result.append({
                "id":          r["id"],
                "name":        r["name"],
                "description": r["description"] or "",
                "kategori":    r["nama_kategori"] or "Umum",
                "id_kategori": r["id_kategori"]   or 2,
                "status":      DB_TO_STATUS.get(r["status"], "Pending"),
                "deadline":    str(r["deadline"]) if r["deadline"] else "",
            })
        return result
    except Exception as e:
        raise RuntimeError(f"Gagal mengambil data: {e}")


def ambil_semua_nama_tugas():
    try:
        con = _get_conn(); cur = con.cursor()
        cur.execute("SELECT DISTINCT nama_tugas FROM tugas ORDER BY nama_tugas")
        rows = cur.fetchall(); cur.close(); con.close()
        return [r[0] for r in rows]
    except Exception:
        return []


# ── Tambah tugas ──────────────────────────────────────────────────────────────
def tambah_tugas(name, description, kategori, deadline):
    try:
        con = _get_conn(); cur = con.cursor()
        # Pastikan kategori ada (buat jika perlu)
        cur.execute("SELECT id_kategori FROM kategori WHERE nama_kategori=%s",
                    (kategori,))
        row = cur.fetchone()
        if row:
            id_kat = row[0]
        else:
            cur.execute("INSERT INTO kategori (nama_kategori) VALUES (%s)",
                        (kategori,))
            id_kat = cur.lastrowid

        dl = deadline if deadline else None
        cur.execute("""
            INSERT INTO tugas (nama_tugas, deskripsi, status, batas_waktu, id_prioritas, id_kategori)
            VALUES (%s, %s, 'Menunggu', %s, 2, %s)
        """, (name, description, dl, id_kat))
        new_id = cur.lastrowid
        cur.execute("""
            INSERT INTO riwayat_tugas (status_lama, status_baru, id_tugas)
            VALUES (NULL, 'Menunggu', %s)
        """, (new_id,))
        con.commit(); cur.close(); con.close()
    except Exception as e:
        raise RuntimeError(f"Gagal menambah tugas: {e}")


def perbarui_deadline(task_id, deadline):
    try:
        con = _get_conn(); cur = con.cursor()
        dl = deadline if deadline else None
        cur.execute("UPDATE tugas SET batas_waktu=%s WHERE id_tugas=%s", (dl, task_id))
        con.commit(); cur.close(); con.close()
    except Exception as e:
        raise RuntimeError(f"Gagal memperbarui deadline: {e}")


def hapus_tugas(task_id):
    try:
        con = _get_conn(); cur = con.cursor()
        cur.execute("DELETE FROM tugas WHERE id_tugas=%s", (task_id,))
        con.commit(); cur.close(); con.close()
    except Exception as e:
        raise RuntimeError(f"Gagal menghapus tugas: {e}")


def tandai_selesai(task_id):
    try:
        con = _get_conn(); cur = con.cursor()
        cur.execute("SELECT status FROM tugas WHERE id_tugas=%s", (task_id,))
        row = cur.fetchone(); old = row[0] if row else None
        cur.execute("UPDATE tugas SET status='Selesai' WHERE id_tugas=%s", (task_id,))
        cur.execute("""
            INSERT INTO riwayat_tugas (status_lama, status_baru, id_tugas)
            VALUES (%s, 'Selesai', %s)
        """, (old, task_id))
        con.commit(); cur.close(); con.close()
    except Exception as e:
        raise RuntimeError(f"Gagal menandai selesai: {e}")