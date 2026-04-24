import streamlit as st
import mysql.connector
import pandas as pd
import io
import urllib.parse
from streamlit_mic_recorder import mic_recorder
from groq import Groq

# --- 1. KONFIGURASI HALAMAN (Wajib di Paling Atas) ---
st.set_page_config(page_title="Bumil Super-App", page_icon="🤰", layout="wide")

def inject_custom_css():
    st.markdown("""
        <link rel="stylesheet" href="https://unpkg.com/lucide-static@latest/font/lucide.css">
        
        <style>
        /* Font ala Notion */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Styling khusus untuk Ikon Lucide agar sejajar dengan teks */
        .lucide {
            vertical-align: middle;
            margin-right: 8px;
            width: 20px;
            height: 20px;
        }
        
        /* Membuat header lebih bersih ala Notion */
        .notion-header {
            font-size: 28px;
            font-weight: 700;
            color: #37352f;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
        }
        </style>
    """, unsafe_allow_html=True)

# Panggil di awal fungsi main()
inject_custom_css()

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

def register_user(username, password):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Cek apakah username sudah ada
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                conn.close()
                return "exists"
            
            # Insert user baru
            query = "INSERT INTO users (username, password, role) VALUES (%s, %s, 'user')"
            cursor.execute(query, (username, password))
            conn.commit()
            conn.close()
            return "success"
        except Exception as e:
            st.error(f"Error Registrasi: {e}")
            return "error"
    return "error"

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
# --- LOGIKA AUTHENTICATION ---
if 'user_info' not in st.session_state:
    st.subheader("🔐 Akses Bumil Project")
    
    # Membuat Tab untuk Login dan Registrasi
    tab_login, tab_regis = st.tabs(["Login", "Daftar Akun Baru"])
    
    with tab_login:
        u_input = st.text_input("Username", key="login_u")
        p_input = st.text_input("Password", type="password", key="login_p")
        if st.button("Masuk"):
            user = login_user(u_input, p_input)
            if user:
                st.session_state['user_info'] = user
                st.rerun()
            else:
                st.error("Username atau password salah.")
                
    with tab_regis:
        new_u = st.text_input("Buat Username", key="reg_u")
        new_p = st.text_input("Buat Password", type="password", key="reg_p")
        confirm_p = st.text_input("Konfirmasi Password", type="password", key="reg_cp")
        
        if st.button("Daftar Sekarang"):
            if new_p != confirm_p:
                st.warning("Password tidak cocok!")
            elif len(new_u) < 3 or len(new_p) < 3:
                st.warning("Username/Password terlalu pendek.")
            else:
                status = register_user(new_u, new_p)
                if status == "success":
                    st.success("Akun berhasil dibuat! Silakan login di tab sebelah.")
                elif status == "exists":
                    st.error("Username sudah terpakai, cari yang lain ya.")
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
        st.markdown('<div class="notion-header"><i class="lucide-book-open"></i> Jurnal Kehamilan</div>', unsafe_allow_html=True)
        st.caption("Ruang tenang untuk mencatat setiap momen berharga Bunda.")
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
        st.markdown('<div class="notion-header"><i class="lucide-pill"></i> Manajemen Obat & Vitamin</div>', unsafe_allow_html=True)
        st.caption("Pantau asupan suplemen dan obat rutin Bunda untuk kesehatan Si Kecil.")
        st.divider()
        
        # Form Obat
        col_input, col_info = st.columns() 
        with col_input:
            st.markdown('### <i class="lucide-plus-circle"></i> Tambah Jadwal Baru', unsafe_allow_html=True)
            with st.form("form_obat", clear_on_submit=True):

                nama_obat = st.text_input("Nama Obat", placeholder="misal: Folavit 400mcg")

            col1, col2 = st.columns(2)
            with col1: 
                dosis = st.text_input("Dosis", placeholder="1 x 1 tablet/hari")
            with col2:
                waktu = st.time_input("Jam konsumsi")
            
            submit_obat = st.form_submit_button("Simpan ke Jurnal")

            if submit_obat:
                if nama_obat: # Validasi sederhana agar tidak simpan data kosong
                    query = "INSERT INTO master_obat (nama_obat, dosis, waktu_konsumsi, user_id) VALUES (%s, %s, %s, %s)"
            if save_to_db(query, (nama_obat, dosis, str(waktu), uid)):
                # Gunakan toast agar tampilan tetap bersih (pop-up kecil)
                st.toast(f"✅ {nama_obat} berhasil dicatat!", icon='💊')
            else:
                st.error("Nama obat tidak boleh kosong ya, Bun.")

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
            
            # 1. Ambil Nomor Admin
            df_admin = pd.read_sql("SELECT nomor_wa FROM kontak_layanan WHERE tipe='Admin' LIMIT 1", conn)
            nomor_admin = df_admin['nomor_wa'].iloc[0] if not df_admin.empty else "628123456789"
            
            # 2. Ambil Data Obat & Kontrol
            # Gunakan params untuk keamanan database
            df_obat = pd.read_sql("SELECT nama_obat, dosis FROM master_obat WHERE user_id=%s", conn, params=(uid,))
            df_kontrol = pd.read_sql("SELECT nama_rs_klinik, tgl_kontrol, keperluan FROM jadwal_kontrol WHERE user_id=%s", conn, params=(uid,))
            
            # Visualisasi Tabel Obat
            st.markdown('### <i class="lucide-pill-bottle"></i> Daftar Konsumsi Obat', unsafe_allow_html=True)
            if not df_obat.empty:
                st.dataframe(df_obat, use_container_width=True, hide_index=True)
            else:
                st.info("Belum ada catatan obat hari ini.")
            
            # Visualisasi Tabel Kontrol
            st.markdown('### <i class="lucide-stethoscopes"></i> Jadwal Kontrol Mendatang', unsafe_allow_html=True)
            if not df_kontrol.empty:
                st.dataframe(df_kontrol, use_container_width=True, hide_index=True)
            else:
                st.info("Tidak ada jadwal kontrol yang terdaftar.")

            conn.close()

            st.divider()

            # 3. Logika Tombol WA agar tidak error jika data kosong
            if not df_kontrol.empty:
                # Ambil data kontrol terbaru untuk template pesan
                rs_terakhir = df_kontrol['nama_rs_klinik'].iloc[0]
                tujuan_terakhir = df_kontrol['keperluan'].iloc[0]
                pesan_wa = f"Halo Admin, saya mau daftar {tujuan_terakhir} di {rs_terakhir}"
            else:
                pesan_wa = "Halo Admin, saya ingin berkonsultasi mengenai jadwal kontrol."

            link = buat_link_wa(nomor_admin, pesan_wa)
            
            # Tombol pendaftaran dengan icon pesan
            st.markdown('<div style="text-align: center; margin-top: 20px;">', unsafe_allow_html=True)
            st.link_button("📲 Daftar via WA Admin", link, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Bagian Pengaturan
        with st.expander("⚙️ Pengaturan Nomor"):
            st.caption("Konfigurasi Nomor WA Admin untuk Bunda")
            n_baru = st.text_input("Ganti Nomor WA Admin", placeholder="Contoh: 628123456789")
            
            # Style Tombol
            if st.button("Update Nomor"):
                if save_to_db("UPDATE kontak_layanan SET nomor_wa=%s WHERE tipe='Admin'", (n_baru,)):
                    st.success("Berhasil disimpan untuk Bunda !", icon='✅')
                    st.rerun()

    # --- MENU 3: NUTRISI ---
    elif menu == "🥗 Cek Nutrisi":
        st.markdown('### <i class="lucide-apple"></i> Makanan terbaik untuk Bunda', unsafe_allow_html=True)
        st.write("Tanyakan apakah makanan tertentu aman atau cek kandungan gizinya untuk Bunda.")
        
        makanan = st.text_input("Bunda makan apa hari ini?", placeholder="Contoh: Sate kambing atau Ikan salmon panggang")
        
        if st.button("Analisis Nutrisi"):
            if makanan:
                with st.spinner("AI sedang menganalisis kandungan gizi..."):
                    try:
                        # Pemanggilan API Groq
                        res = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": "Kamu adalah ahli gizi spesialis kehamilan. Berikan jawaban yang edukatif, singkat, dan ramah."},
                                {"role": "user", "content": f"Apakah makanan ini aman untuk ibu hamil dan apa gizinya: {makanan}"}
                            ]
                        )
                        
                        # PERHATIKAN: Kita pakai di sini untuk mengambil jawaban pertama
                        hasil_ai = res.choices[0].message.content
                        
                        # Tampilkan hasil ke layar
                        st.markdown("---")
                        st.markdown(hasil_ai)
                        
                        # Simpan riwayat ke database (Gunakan UID agar tidak tertukar)
                        query_simpan = "INSERT INTO catatan_makanan (nama_makanan, catatan_nutrisi, user_id) VALUES (%s, %s, %s)"
                        save_to_db(query_simpan, (makanan, hasil_ai, uid))
                        st.success("Analisis berhasil disimpan ke riwayat Bunda!")
                        
                    except Exception as e:
                        st.error(f"Gagal menghubungi AI: {e}")
            else:
                st.warning("Silakan ketik nama makanannya dulu ya, Bun.")

        # Menampilkan riwayat makanan dari database
        with st.expander("📜 Lihat Riwayat Makan Bunda"):
            conn = get_db_connection()
            if conn:
                df_makan = pd.read_sql("SELECT tgl_catatan, nama_makanan FROM catatan_makanan WHERE user_id=%s ORDER BY tgl_catatan DESC", conn, params=(uid,))
                st.dataframe(df_makan, use_container_width=True)
                conn.close()

    # --- MENU 4: TANYA DOKTER ---
    elif menu == "👨‍⚕️ Tanya Dokter":
        st.header("👨‍⚕️ Tanya Dokter")
        st.info("Fitur Resume Jurnal sedang disiapkan.")