import streamlit as st
import mysql.connector
import pandas as pd
from streamlit_mic_recorder import mic_recorder
from groq import Groq

# --- KONFIGURASI ai ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Bumil Super-App", page_icon="🤰", layout="wide")

# --- 2. FUNGSI KONEKSI DATABASE ---
def get_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="Home_0271", # PASSWORD MYSQL
        database="bumil_db",
        port=3307
    )

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🤰 Bumil Care")
    st.markdown("---")
    menu = st.radio(
        "Pilih Layanan:",
        ["📝 Jurnal & Suara", "📅 Kontrol & Obat", "🥗 Cek Nutrisi", "👨‍⚕️ Tanya Dokter"]
    )
    st.markdown("---")
    st.info("Log: Database Connected ✅")

# --- 4. LOGIKA MENU ---

# --- MENU 1: JURNAL & SUARA ---
if menu == "📝 Jurnal & Suara":
    st.header("📝 Jurnal Harian Bunda")
    st.write("Ceritakan apa yang Bunda rasakan hari ini.")

    # Bagian Rekam Suara
    st.subheader("🎤 Rekam Suara")
    audio = mic_recorder(
        start_prompt="Mulai Rekam 🎙️",
        stop_prompt="Selesai & Simpan ✅",
        key='recorder'
    )

    if audio:
        st.audio(audio['bytes'])
        st.success("Suara berhasil direkam! (AI sedang memproses teks...)")

    st.divider()

    # Bagian Form Input Manual
    with st.form("form_jurnal"):
        col1, col2 = st.columns(2)
        with col1:
            kat = st.selectbox("Kategori", [
                "📝 Jurnal & Keluhan", 
                "🦶 Milestone (Tendangan, dll)", 
                "💊 Obat & Vitamin", 
                "🥗 Nutrisi Makanan", 
                "📅 Jadwal Kontrol Dokter"
            ])
        with col2:
            status = st.checkbox("Tandai sebagai Kejadian Penting ⭐")
        
        catatan = st.text_area("Catatan Detail:", placeholder="Tulis keluhan atau momen bahagia di sini...")
        submit = st.form_submit_button("Simpan ke Jurnal")

        if submit:
            if catatan:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    query = "INSERT INTO jurnal_kehamilan (kategori, catatan, status_penting) VALUES (%s, %s, %s)"
                    cursor.execute(query, (kat, catatan, status))
                    conn.commit()
                    st.success("Catatan berhasil disimpan ke database!")
                    conn.close()
                except Exception as e:
                    st.error(f"Gagal menyimpan: {e}")
            else:
                st.warning("Catatan tidak boleh kosong, Bun!")

# --- MENU 2: KONTROL & OBAT ---
elif menu == "📅 Kontrol & Obat":
    st.header("📅 Kontrol & Reminder")
    st.info("Fitur ini akan membantu Bunda mengingat jadwal dokter dan minum obat.")
    # Nanti kita tambahkan kalender interaktif di sini

# --- MENU 3: CEK NUTRISI ---
elif menu == "🥗 Cek Nutrisi":
        st.header("🥗 Analisis Nutrisi Makanan")
        st.write("Cek apakah makanan Bunda sudah memenuhi standar gizi kehamilan.")
        
        metode = st.radio("Metode Input:", ["Ketik Nama Makanan", "Ambil Foto Makanan"])
        
        if metode == "Ketik Nama Makanan":
            makanan_input = st.text_input("Bunda makan apa hari ini?", placeholder="Contoh: Pecel lele pake nasi")
            
            if st.button("Analisis Nutrisi"):
                if makanan_input:
                    with st.spinner(f"Tunggu sebentar sedang menganalisis gizi {makanan_input}..."):
                        prompt = f"""
                        Kamu adalah ahli gizi khusus ibu hamil. Analisis menu ini secara singkat & padat: {makanan_input}.
                        Analisis dalam bahasa Indonesia yang ramah, suportif, dan panggil 'Bunda':
                        1. Apa saja Nutrisi utama?
                        2. Manfaat untuk ibu hamil dan janin?
                        3. Apa saran tambahan nutrisi tambahan?
                        """
                        try:
                            # --- PROSES AI ---
                            completion = client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[
                                    {"role": "system", "content": "Kamu adalah ahli gizi ibu hamil yang ramah."},
                                    {"role": "user", "content": prompt}
                                ]
                            )

                            # Perhatikan di bawah ini, ini penting agar tidak error
                            hasil_ai = completion.choices[0].message.content
                        
                            st.markdown(f"### 📋 Hasil Analisis untuk: {makanan_input}")
                            st.markdown(hasil_ai)

                            # --- PROSES DATABASE ---
                            try:
                                conn = get_connection()
                                cursor = conn.cursor()
                                query = "INSERT INTO jurnal_kehamilan (kategori, catatan, metadata_ai) VALUES (%s, %s, %s)"
                                cursor.execute(query, ("🥗 Nutrisi Makanan", f"Makan: {makanan_input}", hasil_ai))
                                conn.commit()
                                conn.close()
                            except Exception as db_error:
                                st.error(f"Gagal simpan ke database: {db_error}")
                        
                        except Exception as ai_error:
                            st.error(f"Gagal menghubungi AI: {ai_error}")
                else:
                    st.warning("Isi dulu nama makanannya ya, Bun.")
        
        else:
            st.camera_input("Ambil Foto Makanan")
            st.caption("Gunakan kamera untuk mendeteksi nutrisi secara otomatis.")

# --- MENU 4: TANYA DOKTER ---

# --- MENU 4: TANYA DOKTER ---
elif menu == "👨‍⚕️ Tanya Dokter":
    st.header("👨‍⚕️ Konsultasi Dokter")
    col_a, col_b = st.columns(2)
    with col_a:
        nama_dr = st.text_input("Nama Dokter:", value="dr. Sarah, Sp.OG")
    with col_b:
        wa_dr = st.text_input("Nomor WhatsApp:", value="628123456789")
    
    if st.button("📲 Kirim Resume Jurnal ke WhatsApp"):
        st.write("Sedang menyiapkan ringkasan keluhan Bunda...")
