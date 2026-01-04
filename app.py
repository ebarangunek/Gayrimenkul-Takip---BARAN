import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# --- 1. AYARLAR VE TASARIM ---
st.set_page_config(
    page_title="BARAN | Gayrimenkul Danışmanı",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Profil Fotoğrafı
PROFIL_FOTO_URL = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png" 

# CSS Tasarımı
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at top left, #1b202b, #0e1117);
    }
    
    /* Metrik Kartları */
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
        color: white;
    }
    .stButton>button:hover {
        box-shadow: 0 6px 20px rgba(220, 53, 69, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# --- 2. TEMİZLİK FONKSİYONLARI ---
def clean_currency(value):
    """Fiyatı temizler (10.000 TL -> 10000)"""
    try:
        if isinstance(value, str):
            clean_str = ''.join(filter(str.isdigit, value))
            return int(clean_str) if clean_str else 0
        return int(value)
    except: return 0

def clean_phone(value):
    """Telefonu temizler"""
    try:
        val_str = str(value)
        return ''.join(filter(str.isdigit, val_str))
    except: return ""

def clean_coordinates(value):
    """Koordinatı temizler (41,28 -> 41.28)"""
    try:
        val_str = str(value).replace(',', '.')
        return float(val_str)
    except: return None

# --- 3. VERİTABANI BAĞLANTISI (GÜNCELLENDİ) ---
@st.cache_resource(show_spinner=False)
def get_google_sheet_data(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = None
    
    # 1. Kimlik Doğrulama
    try:
        # Önce Yerel Dosya
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    except FileNotFoundError:
        # Sonra Cloud Secrets
        try:
            if "gcp_service_account" in st.secrets:
                creds_dict = st.secrets["gcp_service_account"]
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        except: return [], None

    # 2. Dosya Açma
    if creds:
        try:
            client = gspread.authorize(creds)
            # BURASI GÜNCELLENDİ: Senin verdiğin yeni isim
            db_name = "baran_gayrimenkul_veritabani" 
            
            # Sayfayı açmaya çalış, yoksa hata döndür ama çökme
            try:
                sheet = client.open(db_name).worksheet(sheet_name)
                return sheet.get_all_records(), sheet
            except gspread.WorksheetNotFound:
                # Sayfa bulunamadıysa boş dön
                return [], None
            except gspread.SpreadsheetNotFound:
                st.error(f"HATA: '{db_name}' isimli Google Sheet bulunamadı! Lütfen ismini kontrol edin.")
                return [], None
        except Exception as e:
            st.error(f"Bağlantı Hatası: {e}")
            return [], None
    return [], None

# --- 4. EKLEME VE SİLME İŞLEMLERİ ---
def add_row_to_sheet(sheet_object, row_data):
    try:
        sheet_object.append_row(row_data)
        st.toast("✅ Başarıyla Kaydedildi!", icon="🚀")
        time.sleep(1)
    except Exception as e: st.error(f"Kayıt Hatası: {e}")

def delete_row_from_sheet(sheet_object, col_val, col_index=2):
    try:
        # col_index=2 -> Portföyde 'Baslik' sütunu
        # col_index=3 -> Ajandada 'Gorev' sütunu
        vals = sheet_object.col_values(col_index)
        if col_val in vals:
            r_idx = vals.index(col_val) + 1
            sheet_object.delete_rows(r_idx)
            st.toast("🗑️ Silindi!", icon="✅")
            time.sleep(1)
            st.rerun()
        else: st.warning("Kayıt bulunamadı.")
    except Exception as e: st.error(f"Silme Hatası: {e}")

# --- 5. ANA UYGULAMA MANTIĞI ---
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
        
        menu = st.radio(
            "Menü", 
            ["📊 Dashboard", "📅 Ajanda & Görevler", "🏠 Portföy", "👥 Müşteriler", "🗺️ Harita", "🤖 Eşleşme"],
            key="secili_menü"
        )
        
        # Hedef Çubuğu
        st.write("---")
        st.subheader("🎯 Mart Hedefi")
        data_p, _ = get_google_sheet_data("Portfoy")
        mevcut_ciro = 0
        if data_p:
            df_t = pd.DataFrame(data_p)
            if 'Fiyat' in df_t.columns:
                mevcut_ciro = sum([clean_currency(x) for x in df_t['Fiyat']])
        
        hedef = 20000000
        prog = min(mevcut_ciro / hedef, 1.0) if hedef > 0 else 0
        st.progress(prog)
        st.caption(f"{(mevcut_ciro/1000000):.1f}M / {(hedef/1000000):.1f}M TL")

    # --- SAYFA: DASHBOARD ---
    if menu == "📊 Dashboard":
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1e2530 0%, #161b22 100%); padding: 25px; border-radius: 15px; border-left: 5px solid #DC3545; margin-bottom: 20px;">
            <h2 style="margin:0; color:white;">Merhaba, Baran 👋</h2>
            <p style="margin:5px 0 0 0; color:#aaa;">Veritabanın: <b>baran_gayrimenkul_veritabani</b> aktif durumda.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Verileri Çek
        data_p, _ = get_google_sheet_data("Portfoy")
        data_m, _ = get_google_sheet_data("Musteriler")
        data_a, _ = get_google_sheet_data("Ajanda")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📦 İlanlar", len(data_p) if data_p else 0)
        c2.metric("👥 Müşteriler", len(data_m) if data_m else 0)
        
        # Ajanda Kontrolü
        gorev_sayisi = 0
        if data_a:
            df_a = pd.DataFrame(data_a)
            if 'Durum' in df_a.columns:
                gorev_sayisi = len(df_a[df_a['Durum'] == 'Bekliyor'])
        
        c3.metric("📝 Bekleyen İş", gorev_sayisi)
        c4.metric("💰 Portföy", f"{(mevcut_ciro/1000000):.1f}M ₺")

        # Günlük Özet
        st.subheader("📅 Günün Özeti")
        if data_a:
            df_a = pd.DataFrame(data_a)
            if not df_a.empty and 'Durum' in df_a.columns:
                df_bekleyen = df_a[df_a['Durum'] == 'Bekliyor'].tail(5)
                if not df_bekleyen.empty:
                    for i, row in df_bekleyen.iterrows():
                        oncelik = row.get('Oncelik', 'Normal')
                        icon = "🔴" if oncelik == 'Yüksek' else "🔵"
                        st.info(f"{icon} **{row.get('Saat','-')}** : {row.get('Gorev','-')} ({row.get('Tarih')})")
                else:
                    st.write("Bekleyen görev yok.")
            else:
                st.warning("Ajanda verisi okunamadı. Sütun başlıklarını kontrol et: Tarih, Saat, Gorev, Durum, Oncelik")
        else:
            st.info("Ajanda verisi bulunamadı. Veritabanına 'Ajanda' sayfası eklediğinden emin ol.")

    # --- SAYFA: AJANDA ---
    elif menu == "📅 Ajanda & Görevler":
        st.title("Ajanda Yönetimi")
        t1, t2 = st.tabs(["📋 Görevler", "➕ Yeni Ekle"])
        
        with t1:
            data_a, sheet_a = get_google_sheet_data("Ajanda")
            if data_a:
                df_a = pd.DataFrame(data_a)
                st.dataframe(df_a, use_container_width=True)
                
                st.write("---")
                # Silme İşlemi
                if 'Gorev' in df_a.columns:
                    silinecek = st.selectbox("Silinecek Görevi Seç", df_a['Gorev'].tolist())
                    if st.button("Görevi Sil"):
                        delete_row_from_sheet(sheet_a, silinecek, col_index=3) # 3. sütun Gorev
            else:
                st.info("Ajanda boş veya sayfa bulunamadı.")
        
        with t2:
            st.markdown("### Yeni Görev")
            with st.form("new_task"):
                c1, c2 = st.columns(2)
                with c1:
                    tarih = st.date_input("Tarih")
                    saat = st.time_input("Saat")
                with c2:
                    gorev = st.text_input("Görev")
                    oncelik = st.selectbox("Öncelik", ["Normal", "Yüksek"])
                
                if st.form_submit_button("Ekle"):
                    row = [tarih.strftime("%Y-%m-%d"), saat.strftime("%H:%M"), gorev, "Bekliyor", oncelik]
                    _, sa = get_google_sheet_data("Ajanda")
                    if sa: add_row_to_sheet(sa, row)
                    else: st.error("Ajanda sayfasına erişilemedi.")

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
                        if not str(img).startswith('http'): img = "https://via.placeholder.com/300x200?text=Resim+Yok"
                        st.image(img, use_container_width=True)
                        st.markdown(f"**{row.get('Baslik', '-')}**")
                        st.caption(f"{row.get('Konum','-')} | {row.get('Fiyat',0)} ₺")
            else: st.info("Portföy boş.")
            
        with t2:
            with st.form("add_p"):
                c1, c2 = st.columns(2)
                with c1:
                    baslik = st.text_input("Başlık")
                    tip = st.selectbox("Tip", ["Daire", "Villa", "Ticari", "Arsa"])
                    fiyat = st.number_input("Fiyat", min_value=0)
                    konum = st.text_input("Konum")
                    gorsel = st.text_input("Görsel URL")
                with c2:
                    m2 = st.number_input("M2", min_value=0)
                    oda = st.selectbox("Oda", ["1+1","2+1","3+1","4+1"])
                    durum = st.selectbox("Durum", ["Satılık", "Kiralık"])
                    e1,e2 = st.columns(2)
                    enlem = e1.number_input("Enlem", format="%.5f", value=41.28)
                    boylam = e2.number_input("Boylam", format="%.5f", value=36.33)
                
                if st.form_submit_button("Kaydet"):
                    d = [datetime.now().strftime("%Y-%m-%d"), baslik, tip, fiyat, konum, m2, oda, durum, gorsel, enlem, boylam]
                    _, sp = get_google_sheet_data("Portfoy")
                    if sp: add_row_to_sheet(sp, d)
        
        with t3:
            data_p, sp = get_google_sheet_data("Portfoy")
            if data_p:
                df_p = pd.DataFrame(data_p)
                if 'Baslik' in df_p.columns:
                    sl = st.selectbox("Silinecek İlan", df_p['Baslik'].tolist())
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
                    with st.expander(f"{r.get('Ad_Soyad','-')} ({r.get('Talep','-')})"):
                        c1, c2 = st.columns([3,1])
                        c1.write(f"📞 {r.get('Telefon')} | 📝 {r.get('Notlar')}")
                        raw = clean_phone(r.get('Telefon'))
                        if raw:
                            if not raw.startswith("90"): raw = "90"+raw
                            c2.link_button("WhatsApp", f"https://wa.me/{raw}")
        with t2:
            with st.form("add_m"):
                ad = st.text_input("Ad Soyad")
                tel = st.text_input("Telefon")
                talep = st.selectbox("Talep", ["Satılık Daire", "Kiralık Daire"])
                butce = st.text_input("Bütçe")
                notlar = st.text_area("Notlar")
                if st.form_submit_button("Kaydet"):
                    d = [datetime.now().strftime("%Y-%m-%d"), ad, tel, talep, butce, notlar]
                    _, sm = get_google_sheet_data("Musteriler")
                    if sm: add_row_to_sheet(sm, d)

    # --- SAYFA: HARİTA ---
    elif menu == "🗺️ Harita":
        st.title("Portföy Haritası")
        data_p, _ = get_google_sheet_data("Portfoy")
        if data_p:
            df = pd.DataFrame(data_p)
            if 'Enlem' in df.columns and 'Boylam' in df.columns:
                try:
                    df['lat'] = df['Enlem'].apply(clean_coordinates)
                    df['lon'] = df['Boylam'].apply(clean_coordinates)
                    # Boş veya hatalı koordinatları filtrele
                    df_map = df.dropna(subset=['lat', 'lon'])
                    st.map(df_map, zoom=11)
                except: st.warning("Koordinat verilerinde hata var.")
            else: st.warning("Enlem/Boylam sütunları bulunamadı.")
        else: st.info("Veri yok.")

    # --- SAYFA: EŞLEŞME ---
    elif menu == "🤖 Eşleşme":
        st.title("Akıllı Eşleşme")
        data_p, _ = get_google_sheet_data("Portfoy")
        data_m, _ = get_google_sheet_data("Musteriler")
        
        if data_p and data_m:
            df_p, df_m = pd.DataFrame(data_p), pd.DataFrame(data_m)
            mst = st.selectbox("Müşteri", df_m['Ad_Soyad'].unique())
            
            row_m = df_m[df_m['Ad_Soyad']==mst].iloc[0]
            talep = row_m.get('Talep','')
            
            st.info(f"Aranan: {talep}")
            
            filt = 'Satılık' if 'Satılık' in talep else 'Kiralık'
            res = df_p[df_p['Durum']==filt]
            
            if not res.empty: st.dataframe(res[['Baslik','Fiyat','Konum']], use_container_width=True)
            else: st.warning("Uygun ilan yok.")
        else: st.warning("Yeterli veri yok.")

if __name__ == "__main__":
    main()
