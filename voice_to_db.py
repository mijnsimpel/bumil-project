import speech_recognition as sr
import mysql.connector

def save_to_db(text):
    try:
        conn = mysql.connector.connect(
            host="localhost", user="root", password="PasswordKamu",
            database="bumil_db", port=3307
        )
        cursor = conn.cursor()
        query = "INSERT INTO jurnal_kehamilan (kategori, catatan) VALUES (%s, %s)"
        cursor.execute(query, ("Jurnal Suara", text))
        conn.commit()
        print("✅ Berhasil menyimpan curhatan ke database!")
    except Exception as e:
        print(f"❌ Gagal simpan: {e}")

def recognize_voice(audio_file):
    r = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio_data = r.record(source)
        try:
            # Menggunakan Google Speech Recognition (Gratis)
            text = r.recognize_google(audio_data, language="id-ID")
            print(f"🗣️ Istri bilang: {text}")
            save_to_db(text)
        except Exception as e:
            print(f"🤔 Maaf, suara tidak jelas: {e}")

# Nama file audio yang ingin diproses (pastikan filenya ada di folder yang sama)
file_target = "rekaman_istri.wav" 
recognize_voice(file_target)
