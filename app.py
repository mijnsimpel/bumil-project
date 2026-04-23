import streamlit as st
import mysql.connector
import pandas as pd
import io
from streamlit_mic_recorder import mic_recorder
from groq import Groq

# --- KONFIGURASI ai ---
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("GROQ_API_KEY tidak ditemukan di secrets. Harap konfigurasi di Streamlit Cloud.")
    st.stop()

# Fungsi untuk koneksi ke TiDB menggunakan Secrets
def get_connection():
    return mysql.connector.connect(
        host=st.secrets["DB_HOST"],
        port=st.secrets["DB_PORT"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        database=st.secrets["DB_NAME"],
        ssl_verify_cert=True # TiDB memerlukan koneksi aman (SSL)
    )

try:
    conn = get_connection()
    cursor = conn.cursor()
    st.success("Berhasil terhubung ke Buku Catatan Bunda di Awan! ☁️✅")
except Exception as e:
    st.error(f"Waduh, belum bisa lapor ke database: {e}")

    
# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Bumil Super-App", page_icon="🤰", layout="wide")

# --- CSS CUSTOM UNTUK UI LEBIH RAPI ---
st.markdown("""
    <style>
    .main { background-color: #fff5f7; }
    .stButton>button { width: 100%; border-radius: 20px; border: none; background-color: #ff4b6b; color: white; }
    .stTextInput>div>div>input { border-radius: 10px; }
    div[data-testid="stExpander"] { border: none; box-shadow: 0px 4px 12px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNGSI KONEKSI DATABASE ---
def get_connection():
    return mysql.connector.connect(
        host=st.secrets.get("DB_HOST", "127.0.0.1"),
        user="root",
        password="Home_0271", # PASSWORD MYSQL
        database="bumil_db",
        port=int(st.secrets.get("DB_PORT", 3307))
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
    st.title("📅 Kontrol & Reminder")
    st.info("Fitur ini akan membantu Bunda mengingat jadwal dokter dan rutin minum obat.")
    # Nanti kita tambahkan kalender interaktif di sini

# --- MENU 3: CEK NUTRISI ---
elif menu == "🥗 Cek Nutrisi":
        st.title("🥗 Analisis Nutrisi")
        st.write("Cek apakah makanan Bunda sudah memenuhi standar gizi kehamilan.")
        
        metode = st.radio("Pilih Cara Cek:", ["⌨️ Ketik Nama Makanan", "📸 Ambil Foto Makanan"], horizontal=True)
        
        if metode == "⌨️ Ketik Nama Makanan":
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
elif menu == "👨‍⚕️ Tanya Dokter":
    st.title("👨‍⚕️ Konsultasi Dokter")
    with st.container(border=True):
        col_a, col_b = st.columns(2)
        with col_a:
            nama_dr = st.text_input("Nama Dokter:", value="dr. Sarah, Sp.OG")
        with col_b:
            wa_dr = st.text_input("Nomor WhatsApp:", value="628123456789")
        
        if st.button("📲 Kirim Resume Jurnal ke WhatsApp"):
            st.toast("Menyiapkan ringkasan...", icon="⏳")
            st.write("Fitur integrasi WhatsApp sedang dikembangkan.")
