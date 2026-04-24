import streamlit as st
import mysql.connector
import pandas as pd
import io
from streamlit_mic_recorder import mic_recorder
from groq import Groq


# 1. VALIDASI KESELURUHAN (Cek semua kunci di awal agar aman)
required_secrets = ["GROQ_API_KEY", "DB_HOST", "DB_USER", "DB_PASSWORD"]
missing_keys = [key for key in required_secrets if key not in st.secrets]

if missing_keys:
    st.error(f"Konfigurasi belum lengkap! Key berikut hilang di Secrets: {', '.join(missing_keys)}")
    st.stop()

# 2. INISIALISASI AI
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 3. FUNGSI KONEKSI DATABASE (Lebih aman & fleksibel)
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=st.secrets["DB_HOST"],
            port=st.secrets.get("DB_PORT", 4000),
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets.get("DB_NAME", "test"),
            ssl_disabled=False
        )
        return conn
    except Exception as e:
        st.error(f"Gagal menyambungkan ke TiDB Cloud: {e}")
        return None

# 4. CEK KONEKSI AWAL
db_conn = get_db_connection()
if db_conn and db_conn.is_connected():
    st.success("Sistem AI & Database Cloud siap digunakan! 🚀☁️")
    db_conn.close()


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
                    conn = get_db_connection()
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
                                conn = get_db_connection()
                                cursor = conn.cursor()
                                query = "INSERT INTO catatan_makanan (nama_makanan, catatan nutrisi) VALUES (%s, %s)"
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
