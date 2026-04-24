import streamlit as st
import mysql.connector
import pandas as pd
import io
import urllib.parse
from streamlit_mic_recorder import mic_recorder
from groq import Groq

# --- 1. KONFIGURASI HALAMAN (Wajib di Paling Atas) ---
st.set_page_config(page_title="Bumil Super-App", page_icon="🤰", layout="wide")

# --- 2. VALIDASI SECRETS ---
required_secrets = ["GROQ_API_KEY", "DB_HOST", "DB_USER", "DB_PASSWORD"]
missing_keys = [key for key in required_secrets if key not in st.secrets]
if missing_keys:
    st.error(f"Missing Keys: {', '.join(missing_keys)}")
    st.stop()

# --- 3. INISIALISASI AI & CSS ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
st.markdown("""
    <style>
    .main { background-color: #fff5f7; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #ff4b6b; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. FUNGSI DATABASE & HELPER ---
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=st.secrets["DB_HOST"],
            port=st.secrets.get("DB_PORT", 4000),
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets.get("DB_NAME", "test")
        )
    except Exception as e:
        st.error(f"Koneksi Gagal: {e}")
        return None

def save_to_db(query, params):
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return True
    except Exception as e:
        st.error(f"Database Error: {e}")
    return False

def buat_link_wa(nomor, pesan):
    return f"https://wa.me/{nomor}?text={urllib.parse.quote(pesan)}"

def login_user(username, password):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        conn.close()
        return user
    return None

# --- 5. LOGIKA AUTHENTICATION & GLOBAL UID (PILIHAN B) ---
if 'user_info' not in st.session_state:
    st.subheader("🔐 Login Bumil Project")
    u_input = st.text_input("Username")
    p_input = st.text_input("Password", type="password")
    if st.button("Login"):
        user = login_user(u_input, p_input)
        if user:
            st.session_state['user_info'] = user
            st.rerun()
        else:
            st.error("Login Gagal.")
else:
    # DEFINISI GLOBAL UID (PILIHAN B)
    uid = st.session_state['user_info']['id']
    username = st.session_state['user_info']['username']

    with st.sidebar:
        st.title("🤰 Bumil Care")
        st.write(f"Logged in: **{username}**")
        menu = st.radio("Layanan:", ["📝 Jurnal", "📅 Kontrol & Obat", "🥗 Cek Nutrisi", "👨‍⚕️ Tanya Dokter"])
        if st.button("Log Out"):
            del st.session_state['user_info']
            st.rerun()

    # --- MENU 1: JURNAL ---
    if menu == "📝 Jurnal":
        st.header("📝 Jurnal Harian")
        audio = mic_recorder(start_prompt="Rekam Suara 🎙️", stop_prompt="Simpan ✅", key='recorder')
        
        with st.form("form_jurnal"):
            kat = st.selectbox("Kategori", ["📝 Jurnal & Keluhan", "🦶 Milestone", "💖 Momen bahagia"])
            status = st.checkbox("Penting ⭐")
            catatan = st.text_area("Catatan:")
            if st.form_submit_button("Simpan"):
                if catatan:
                    # TAMBAHKAN user_id (uid) di sini!
                    query = "INSERT INTO jurnal_kehamilan (kategori, catatan, status_penting, user_id) VALUES (%s, %s, %s, %s)"
                    if save_to_db(query, (kat, catatan, status, uid)):
                        st.success("Tersimpan!")
                else:
                    st.warning("Isi catatan dulu.")

    # --- MENU 2: KONTROL & OBAT ---
    elif menu == "📅 Kontrol & Obat":
        st.header("📅 Kontrol & Obat")
        
        # Form Obat
        with st.form("form_obat"):
            nama_obat = st.text_input("Nama Obat")
            dosis = st.text_input("Dosis")
            waktu = st.time_input("Jam")
            if st.form_submit_button("Simpan Obat"):
                query = "INSERT INTO master_obat (nama_obat, dosis, waktu_konsumsi, user_id) VALUES (%s, %s, %s, %s)"
                if save_to_db(query, (nama_obat, dosis, str(waktu), uid)):
                    st.success("Obat Tersimpan!")

        # Form Dokter
        with st.form("form_dokter"):
            rs = st.text_input("Nama RS")
            tgl = st.date_input("Tanggal")
            tujuan = st.selectbox("Tujuan", ["USG", "Rutin", "Lab"])
            if st.form_submit_button("Simpan Jadwal"):
                query = "INSERT INTO jadwal_kontrol (nama_rs_klinik, tgl_kontrol, keperluan, user_id) VALUES (%s, %s, %s, %s)"
                if save_to_db(query, (rs, tgl, tujuan, uid)):
                    st.success("Jadwal Tersimpan!")

        # Tampilkan Data (Filtered by UID)
        conn = get_db_connection()
        if conn:
            st.subheader("📋 Daftar Rencana Bunda")
            # Ambil Nomor Admin
            df_admin = pd.read_sql("SELECT nomor_wa FROM kontak_layanan WHERE tipe='Admin' LIMIT 1", conn)
            nomor_admin = df_admin['nomor_wa'].iloc if not df_admin.empty else "628123456789"
            
            # Tabel filtered by UID
            st.dataframe(pd.read_sql(f"SELECT nama_obat, dosis FROM master_obat WHERE user_id={uid}", conn))
            st.dataframe(pd.read_sql(f"SELECT nama_rs_klinik, tgl_kontrol FROM jadwal_kontrol WHERE user_id={uid}", conn))
            conn.close()

            # Tombol WA
            link = buat_link_wa(nomor_admin, f"Halo, saya mau daftar {tujuan} di {rs}")
            st.link_button("Daftar via WA 📲", link)

        # Bagian Pengaturan
        with st.expander("⚙️ Pengaturan Nomor"):
            n_baru = st.text_input("Ganti Nomor WA Admin")
            if st.button("Update"):
                if save_to_db("UPDATE kontak_layanan SET nomor_wa=%s WHERE tipe='Admin'", (n_baru,)):
                    st.success("Updated!")
                    st.rerun()

    # --- MENU 3: NUTRISI ---
    elif menu == "🥗 Cek Nutrisi":
        st.header("🥗 Cek Nutrisi AI")
        makanan = st.text_input("Bunda makan apa?")
        if st.button("Analisis"):
            with st.spinner("AI sedang berpikir..."):
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"Analisis gizi makanan bumil: {makanan}"}]
                )
                hasil = res.choices.message.content
                st.markdown(hasil)
                # Simpan ke DB dengan UID
                save_to_db("INSERT INTO catatan_makanan (nama_makanan, catatan_nutrisi, user_id) VALUES (%s, %s, %s)", (makanan, hasil, uid))

    # --- MENU 4: TANYA DOKTER ---
    elif menu == "👨‍⚕️ Tanya Dokter":
        st.header("👨‍⚕️ Tanya Dokter")
        st.info("Fitur Resume Jurnal sedang disiapkan.")