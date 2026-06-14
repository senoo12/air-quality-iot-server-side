import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Baru setelah itu lakukan import seperti biasa
from app.infrastructure.database import Base, engine
from sqlalchemy import text

def reset_all_data():
    # Ambil semua nama tabel yang terdaftar di Metadata SQLAlchemy Anda
    table_names = ", ".join(Base.metadata.tables.keys())
    
    if not table_names:
        print("Tidak ada tabel yang terdeteksi.")
        return

    print(f"Mengosongkan data dari tabel: {table_names}")
    
    with engine.connect() as connection:
        trans = connection.begin()
        try:
            # Menggunakan TRUNCATE CASCADE untuk PostgreSQL/MySQL
            connection.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE;"))
            trans.commit()
            print("🚀 Semua data berhasil di-reset (tabel sekarang kosong)!")
        except Exception as e:
            trans.rollback()
            print(f"❌ Gagal mereset data: {e}")

if __name__ == "__main__":
    reset_all_data()