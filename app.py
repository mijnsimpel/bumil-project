import streamlit as st
import mysql.connector
import pandas as pd
import io
import urllib.parse
from streamlit_mic_recorder import mic_recorder
from groq import Groq

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Bumil Super-App", page_icon="🤰", layout="wide")

def inject_custom_css():
    st.markdown("""
        <link rel="stylesheet" href="https://unpkg.com/lucide-static@latest/font/lucide.css">
        <style>
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .lucide { vertical-align: middle; margin-right: 8px; width: 20px; height: 20px; }
        .notion-header { font-size: 28px; font-weight: 700; color: #37352f; margin-bottom: 10px; display: flex; align-items: center; }
        .main { background-color: #fff5f7; }
        .stButton>button { width: 100%; border-radius: 20px; background-color: #ff4b6b; color: white; }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- 2. VALIDASI SECRETS & INISIALISASI ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("Missing GROQ_API_KEY in secrets!")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 3. FUNGSI DATABASE ---
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
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        conn.close()
        return user
    return None

def register_user(username, password):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                conn.close()
                return "exists"
            cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, 'user')", (username, password))
            conn.commit()
            conn.close()
            return "success"
        except Exception as e:
            return "error"
    return "error"

# --- 4. LOGIKA AUTHENTICATION ---
if 'user_info' not in st.session_state:
    st.subheader("🔐 Akses Bumil Project")
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
            else:
                status = register_user(new_u, new_p)
                if status == "success":
                    st.success("Akun berhasil dibuat! Silakan login.")
                elif status == "exists":
                    st.error("Username sudah terpakai.")
else:
    # DEFINISI GLOBAL UID
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
        
        with st.form("form_jurnal"):
            kat = st.selectbox("Kategori", ["📝 Jurnal & Keluhan", "🦶 Milestone", "💖 Momen bahagia"])
            status = st.checkbox("Penting ⭐")
            catatan = st.text_area("Catatan:")
            if st.form_submit_button("Simpan"):
                if catatan:
                    query = "INSERT INTO jurnal_kehamilan (kategori, catatan, status_penting, user_id) VALUES (%s, %s, %s, %s)"
                    if save_to_db(query, (kat, catatan, status, uid)):
                        st.success("Tersimpan!")
                else:
                    st.warning("Isi catatan dulu.")

    # --- MENU 2: KONTROL & OBAT ---
    elif menu == "📅 Kontrol & Obat":
        st.markdown('<div class="notion-header"><i class="lucide-activity"></i> Manajemen Kesehatan Bunda</div>', unsafe_allow_html=True)
        st.caption("Kelola jadwal obat dan janji temu dokter dalam satu tempat yang tenang.")
        st.divider()

        col_input, col_info = st.columns([2, 1])

        with col_input:
            # FORM OBAT
            st.markdown('### <i class="lucide-pill"></i> Tambah Jadwal Obat', unsafe_allow_html=True)
            with st.form("form_obat", clear_on_submit=True):
                nama_obat = st.text_input("Nama Obat", placeholder="misal: Folavit")
                c1, c2 = st.columns(2)
                with c1: dosis = st.text_input("Dosis", placeholder="1 x 1")
                with c2: waktu = st.time_input("Jam")
                if st.form_submit_button("Simpan Obat"):
                    if nama_obat:
                        query = "INSERT INTO master_obat (nama_obat, dosis, waktu_konsumsi, user_id) VALUES (%s, %s, %s, %s)"
                        if save_to_db(query, (nama_obat, dosis, str(waktu), uid)):
                            st.toast(f"✅ {nama_obat} dicatat!")
                            st.rerun()

            # FORM DOKTER
            st.markdown('### <i class="lucide-calendar-plus"></i> Jadwal Kontrol Baru', unsafe_allow_html=True)
            with st.form("form_dokter", clear_on_submit=True):
                rs = st.text_input("Nama RS")
                c3, c4 = st.columns(2)
                with c3: tgl = st.date_input("Tanggal")
                with c4: tujuan = st.selectbox("Keperluan", ["USG", "Rutin", "Lab"])
                if st.form_submit_button("Simpan Jadwal"):
                    query = "INSERT INTO jadwal_kontrol (nama_rs_klinik, tgl_kontrol, keperluan, user_id) VALUES (%s, %s, %s, %s)"
                    if save_to_db(query, (rs, tgl, tujuan, uid)):
                        st.toast("Jadwal tersimpan!")
                        st.rerun()

        with col_info:
            st.markdown('### <i class="lucide-lightbulb"></i> Tips', unsafe_allow_html=True)
            st.info("Minum vitamin tepat waktu sangat penting untuk Si Kecil.")
            with st.expander("⚙️ Nomor Admin"):
                n_baru = st.text_input("Update Nomor")
                if st.button("Simpan Nomor"):
                    save_to_db("UPDATE kontak_layanan SET nomor_wa=%s WHERE tipe='Admin'", (n_baru,))
                    st.rerun()

        st.divider()
        conn = get_db_connection()
        if conn:
            # Tampilkan Tabel Obat
            st.markdown('### <i class="lucide-pill-bottle"></i> Daftar Obat', unsafe_allow_html=True)
            df_o = pd.read_sql("SELECT nama_obat, dosis FROM master_obat WHERE user_id=%s", conn, params=(uid,))
            if not df_o.empty:
                st.dataframe(df_o, use_container_width=True, hide_index=True)
            
            # Tampilkan Tabel Kontrol
            st.markdown('### <i class="lucide-stethoscope"></i> Jadwal Kontrol Mendatang', unsafe_allow_html=True)
            df_k = pd.read_sql("SELECT nama_rs_klinik, tgl_kontrol, keperluan FROM jadwal_kontrol WHERE user_id=%s ORDER BY tgl_kontrol ASC", conn, params=(uid,))
            
            if not df_k.empty:
                st.dataframe(df_k, use_container_width=True, hide_index=True)
                # Link WA
                df_a = pd.read_sql("SELECT nomor_wa FROM kontak_layanan WHERE tipe='Admin' LIMIT 1", conn)
                no_admin = df_a['nomor_wa'].iloc[0] if not df_a.empty else "62812"
                
                # Ambil detail kontrol terbaru
                rs_tujuan = df_k['nama_rs_klinik'].iloc[0]
                keperluan = df_k['keperluan'].iloc[0]
                
                pesan_wa = f"Halo Admin, saya mau daftar {keperluan} di {rs_tujuan}"
                link = buat_link_wa(no_admin, pesan_wa)
                
                st.write("") # Spacer kecil
                st.link_button("📲 Daftar via WA Admin", link, use_container_width=True)
            else:
                st.info("Tidak ada jadwal kontrol yang terdaftar.")
            
            conn.close()

    # --- MENU 3: NUTRISI ---
    elif menu == "🥗 Cek Nutrisi":
        st.markdown('<div class="notion-header"><i class="lucide-apple"></i> Nutrisi Bunda</div>', unsafe_allow_html=True)
        c_in, c_help = st.columns([2, 1])
        with c_in:
            makanan = st.text_input("Input makanan:")
            if st.button("Cek AI"):
                with st.spinner("Menganalisis..."):
                    res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": f"Keamanan & gizi {makanan} untuk bumil?"}]
                    )
                    ans = res.choices.message.content
                    st.markdown(ans)
                    save_to_db("INSERT INTO catatan_makanan (nama_makanan, catatan_nutrisi, user_id) VALUES (%s, %s, %s)", (makanan, ans, uid))
        with c_help:
            st.info("AI akan memberikan saran gizi.")

    # --- MENU 4: TANYA DOKTER ---
    elif menu == "👨‍⚕️ Tanya Dokter":
        st.markdown('<div class="notion-header"><i class="lucide-message-square"></i> Tanya Dokter</div>', unsafe_allow_html=True)
        st.info("Fitur resume otomatis sedang dikembangkan.")