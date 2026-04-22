import mysql.connector

try:
    # Hubungkan ke database di port 3307
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Home_0271",
        database="bumil_db",
        port=3307
    )

    if connection.is_connected():
        cursor = connection.cursor()
        # Masukkan data tes
        query = "INSERT INTO jurnal_kehamilan (kategori, catatan) VALUES (%s, %s)"
        val = ("Jurnal", "Tes Koneksi Berhasil: Istri tersenyum hari ini!")
        
        cursor.execute(query, val)
        connection.commit() # Penting: Untuk menyimpan perubahan secara permanen
        
        print("MANTAP! Data berhasil masuk ke MySQL via Python.")

except Exception as err:
    print(f"Error: {err}")

finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
