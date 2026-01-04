import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# --- 1. AYARLAR VE HİBRİT TASARIM (KURUMSAL + MOBİL) ---
st.set_page_config(
    page_title="BARAN | Gayrimenkul Takip",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Profil Fotoğrafın
PROFIL_FOTO_URL = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png" 

# --- CSS SİHRİ (KARANLIK MOD + CAM EFEKTİ) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at top left, #1b202b, #0e1117);
    }
    
    /* Metrik Kartları (Glassmorphism) */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 15px;
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: scale(1.02);
        border-color: #DC3545;
    }
    
    /* Yan Menü */
    section[data-testid="stSidebar"] {
        background-color: #0b0d11;
        border-right: 1px solid #21262d;
    }
    
    /* Butonlar */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        height: 3em;
        background: linear-gradient(135deg, #DC3545 0%, #a71d2a 100%);
        border: none;
        box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3);
    }
    .stButton>button:hover {
        box-shadow: 0 6px 20px rgba(220, 53, 69, 0.5);
    }
    
    /* Tablolar */
    div[data-testid="stDataFrame"] {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 10px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. YARDIMCI FONKSİYONLAR ---
def clean_currency(value):
    try:
        if isinstance(value, str):
            clean_str = ''.join(filter(str.isdigit, value))
            return int(clean_str) if clean_str else 0
        return int(value)
    except: return 0

def clean_phone(value):
    try:
        val_str = str(value)
        return ''.join(filter(str.isdigit, val_str))
    except: return ""

def clean_coordinates(value):
    try:
        return float(str(value).replace(',', '.'))
    except: return None

# --- 3. VERİTABANI BAĞLANTISI ---
@st.cache_resource(show_spinner=False)
def get_google_sheet_data(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = None
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    except FileNotFoundError:
        try:
            if "gcp_service_account" in st.secrets:
                creds_dict = st.secrets["gcp_service_account"]
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        except: return [], None

    if creds:
        try:
            client = gspread.authorize(creds)
            # Eğer Ajanda sayfası yoksa hata vermemesi için try-except
            try:
                sheet = client.open("baran_gayrimenkul_veritabani").worksheet(sheet_name)
                return sheet.get_all_records(), sheet
            except:
                return [], None
        except: return [], None
    return [], None

# --- 4. CRUD İŞLEMLERİ ---
def add_row_to_sheet(sheet_object, row_data):
    try:
        sheet_object.append_row(row_data)
        st.toast("✅ İşlem Başarılı!", icon="🚀")
        time.sleep(1)
    except Exception as e: st.error(f"Hata: {e}")

def delete_row_from_sheet(sheet_object, col_val, col_index=2):
    try:
        vals = sheet_object.col_values(col_index)
        if col_val in vals:
            r_idx = vals.index(col_val) + 1
            sheet_object.delete_rows(r_idx)
            st.toast("🗑️ Silindi!", icon="✅")
            time.sleep(1)
            st.rerun()
        else: st.warning("Kayıt bulunamadı.")
    except Exception as e: st.error(f"Hata: {e}")

# --- 5. ANA UYGULAMA ---
def main():
    if 'secili_menü' not in st.session_state:
        st.session_state.secili_menü = "📊 Dashboard"

    def sayfa_degistir(hedef_sayfa):
        st.session_state.secili_menü = hedef_sayfa

    # --- YAN MENÜ ---
    with st.sidebar:
        c1, c2 = st.columns([1, 2])
        with c1: st.image(PROFIL_FOTO_URL, width=70)
        with c2: 
            st.write("**Baran Günek**")
            st.caption("REMAX/Park")
        
        st.divider()
        
        # Menü İkonlu
        menu = st.radio(
            "Navigasyon", 
            ["📊 Dashboard", "📅 Ajanda & Görevler", "🏠 Portföy", "👥 Müşteriler", "🗺️ Harita", "🤖 Eşleşme"],
            key="secili_menü"
        )
        
        # Ciro Hedefi
        st.write("---")
        st.subheader("🎯 Mart Hedefi")
        data_p, _ = get_google_sheet_data("Portfoy")
        mevcut_ciro = 0
        if data_p:
            df_t = pd.DataFrame(data_p)
            if 'Fiyat' in df_t.columns:
                mevcut_ciro = sum([clean_currency(x) for x in df_t['Fiyat']])
        
        hedef = 20000000
        prog = min(mevcut_ciro / hedef, 1.0)
        st.progress(prog)
        st.caption(f"{(mevcut_ciro/1000000):.1f}M / {(hedef/1000000):.1f}M TL")

    # --- SAYFA: DASHBOARD ---
    if menu == "📊 Dashboard":
        # Hoşgeldin Bannerı
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1e2530 0%, #161b22 100%); padding: 25px; border-radius: 15px; border-left: 5px solid #DC3545; margin-bottom: 20px;">
            <h2 style="margin:0; color:white;">Merhaba, Baran 👋</h2>
            <p style="margin:5px 0 0 0; color:#aaa;">Bugün işleri büyütmek için harika bir gün. Ajandanda bekleyen görevlerin var.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Metrikler
        data_p, _ = get_google_sheet_data("Portfoy")
        data_m, _ = get_google_sheet_data("Musteriler")
        data_a, _ = get_google_sheet_data("Ajanda")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 İlanlar", len(data_p) if data_p else 0)
        col2.metric("👥 Müşteriler", len(data_m) if data_m else 0)
        
        # Ajanda Sayısı
        gorev_sayisi = 0
        if data_a:
            df_a = pd.DataFrame(data_a)
            # Sadece "Bekliyor" olanları say
            if 'Durum' in df_a.columns:
                gorev_sayisi = len(df_a[df_a['Durum'] == 'Bekliyor'])
        
        col3.metric("📝 Bekleyen Görev", gorev_sayisi, "Önemli")
        col4.metric("💰 Portföy Değeri", f"{(mevcut_ciro/1000000):.1f}M ₺")

        # AJANDA ÖZETİ (Anasayfada Görünen)
        st.subheader("📅 Günün Ajandası")
        if data_a:
            df_a = pd.DataFrame(data_a)
            # Tarihe göre sırala
            if not df_a.empty:
                 # Sadece Bekleyenleri Göster
                df_bekleyen = df_a[df_a['Durum'] == 'Bekliyor'].tail(5) # Son 5 görev
                
                for i, row in df_bekleyen.iterrows():
                    oncelik_renk = "🔴" if row.get('Oncelik') == 'Yüksek' else "🔵"
                    st.info(f"{oncelik_renk} **{row.get('Saat', '-')}** - {row.get('Gorev', '')} ({row.get('Tarih')})")
            else:
                st.write("Planlanmış görev yok.")
        else:
            st.info("Ajandanız boş. 'Ajanda' menüsünden ekleyebilirsiniz.")

    # --- SAYFA: AJANDA & GÖREVLER (YENİ) ---
    elif menu == "📅 Ajanda & Görevler":
        st.title("Kişisel Asistanım")
        t1, t2 = st.tabs(["📋 Tüm Görevler", "➕ Yeni Görev Ekle"])
        
        with t1:
            data_a, sheet_a = get_google_sheet_data("Ajanda")
            if data_a:
                df_a = pd.DataFrame(data_a)
                
                # Tabloyu Düzenlenebilir Yap (Status değiştirmek için)
                st.dataframe(df_a, use_container_width=True)
                
                # Görev Silme / Tamamlama
                st.write("---")
                c_del, _ = st.columns([1,3])
                with c_del:
                    gorevler = df_a['Gorev'].tolist()
                    silinecek = st.selectbox("Silinecek/Tamamlanan Görevi Seç", gorevler)
                    if st.button("Görevi Sil / Arşivle"):
                        delete_row_from_sheet(sheet_a, silinecek, col_index=3) # 3. Sütun 'Gorev'
            else:
                st.info("Henüz kayıtlı görev yok.")
        
        with t2:
            st.markdown("### Yeni Hatırlatıcı Oluştur")
            with st.form("yeni_gorev"):
                c1, c2 = st.columns(2)
                with c1:
                    tarih = st.date_input("Tarih")
                    saat = st.time_input("Saat")
                with c2:
                    gorev = st.text_input("Görev / Hatırlatma Başlığı")
                    oncelik = st.selectbox("Öncelik", ["Normal", "Yüksek", "Düşük"])
                
                if st.form_submit_button("Ajandaya Ekle"):
                    t_str = tarih.strftime("%Y-%m-%d")
                    s_str = saat.strftime("%H:%M")
                    # Sütunlar: Tarih, Saat, Gorev, Durum, Oncelik
                    row = [t_str, s_str, gorev, "Bekliyor", oncelik]
                    _, sheet_a = get_google_sheet_data("Ajanda")
                    if sheet_a: add_row_to_sheet(sheet_a, row)

    # --- SAYFA: PORTFÖY ---
    elif menu == "🏠 Portföy":
        st.title("Portföy Yönetimi")
        t1, t2, t3 = st.tabs(["Galeri", "Ekle", "Sil"])
        with t1:
            data_p, _ = get_google_sheet_data("Portfoy")
            if data_p:
                df = pd.DataFrame(data_p)
                cols = st.columns(3)
                for index, row in df.iterrows():
                    with cols[index % 3]:
                        img = row.get('Gorsel', "")
                        if not str(img).startswith('http'): img = "https://via.placeholder.com/300x200"
                        st.image(img, use_container_width=True)
                        st.markdown(f"**{row.get('Baslik','-')}**")
                        st.caption(f"{row.get('Konum','-')} | {row.get('Fiyat',0)} ₺")
        with t2:
            with st.form("add_p"):
                c1, c2 = st.columns(2)
                with c1:
                    baslik = st.text_input("Başlık")
                    tip = st.selectbox("Tip", ["Daire", "Villa", "Ticari"])
                    fiyat = st.number_input("Fiyat", min_value=0)
                    konum = st.text_input("Konum")
                    gorsel = st.text_input("Görsel URL")
                with c2:
                    m2 = st.number_input("M2", min_value=0)
                    oda = st.selectbox("Oda", ["1+1","2+1","3+1","4+1"])
                    durum = st.selectbox("Durum", ["Satılık", "Kiralık"])
                    e1,e2=st.columns(2)
                    enlem = e1.number_input("Enlem", format="%.5f", value=41.28)
                    boylam = e2.number_input("Boylam", format="%.5f", value=36.33)
                if st.form_submit_button("Kaydet"):
                    d = [datetime.now().strftime("%Y-%m-%d"), baslik, tip, fiyat, konum, m2, oda, durum, gorsel, enlem, boylam]
                    _, s = get_google_sheet_data("Portfoy")
                    if s: add_row_to_sheet(s, d)
        with t3:
            data_p, sp = get_google_sheet_data("Portfoy")
            if data_p:
                sl = st.selectbox("Sil", pd.DataFrame(data_p)['Baslik'].tolist())
                if st.button("Sil"): delete_row_from_sheet(sp, sl, 2)

    # --- SAYFA: MÜŞTERİLER ---
    elif menu == "👥 Müşteriler":
        st.title("Müşteri Listesi")
        t1, t2 = st.tabs(["Liste", "Ekle"])
        with t1:
            data_m, _ = get_google_sheet_data("Musteriler")
            if data_m:
                df = pd.DataFrame(data_m)
                for i, r in df.iterrows():
                    with st.expander(f"{r['Ad_Soyad']} ({r.get('Talep','-')})"):
                        c1, c2 = st.columns([3,1])
                        c1.write(f"📞 {r.get('Telefon')} | 📝 {r.get('Notlar')}")
                        raw = clean_phone(r.get('Telefon'))
                        if raw: 
                            if not raw.startswith("90"): raw = "90"+raw
                            c2.link_button("Whatsapp", f"https://wa.me/{raw}")
        with t2:
            with st.form("add_m"):
                ad = st.text_input("Ad Soyad")
                tel = st.text_input("Telefon")
                talep = st.selectbox("Talep", ["Satılık Daire", "Kiralık Daire", "Arsa"])
                butce = st.text_input("Bütçe")
                notlar = st.text_area("Notlar")
                if st.form_submit_button("Kaydet"):
                    d = [datetime.now().strftime("%Y-%m-%d"), ad, tel, talep, butce, notlar]
                    _, sm = get_google_sheet_data("Musteriler")
                    if sm: add_row_to_sheet(sm, d)

    # --- HARİTA & EŞLEŞME (AYNI) ---
    elif menu == "🗺️ Harita":
        st.title("Harita")
        data_p, _ = get_google_sheet_data("Portfoy")
        if data_p:
            df = pd.DataFrame(data_p)
            try:
                df['lat'] = df['Enlem'].apply(clean_coordinates)
                df['lon'] = df['Boylam'].apply(clean_coordinates)
                st.map(df.dropna(subset=['lat','lon']), zoom=11)
            except: st.warning("Veri hatası")
            
    elif menu == "🤖 Eşleşme":
        st.title("Akıllı Eşleşme")
        data_p, _ = get_google_sheet_data("Portfoy")
        data_m, _ = get_google_sheet_data("Musteriler")
        if data_p and data_m:
            df_p, df_m = pd.DataFrame(data_p), pd.DataFrame(data_m)
            mst = st.selectbox("Müşteri", df_m['Ad_Soyad'])
            talep = df_m[df_m['Ad_Soyad']==mst].iloc[0].get('Talep','')
            st.info(f"Aranan: {talep}")
            res = df_p[df_p['Durum']==('Satılık' if 'Satılık' in talep else 'Kiralık')]
            if not res.empty: st.dataframe(res[['Baslik','Fiyat','Konum']], use_container_width=True)
            else: st.warning("Eşleşme yok")

if __name__ == "__main__":
    main()
