import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# --- 1. AYARLAR VE CSS ---
st.set_page_config(
    page_title="BARAN-G | Gayrimenkul OS",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Profil Fotoğrafı (Varsayılan bir ikon koydum, linki değiştirebilirsin)
PROFIL_FOTO_URL = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png" 

st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 10px;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: bold;
        transition: 0.3s;
    }
    section[data-testid="stSidebar"] {
        background-color: #111;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. YARDIMCI FONKSİYONLAR (GÜÇLENDİRİLDİ) ---
def clean_currency(value):
    """Fiyat verilerini temizler."""
    try:
        if isinstance(value, str):
            clean_str = ''.join(filter(str.isdigit, value))
            return int(clean_str) if clean_str else 0
        return int(value)
    except:
        return 0

def clean_phone(value):
    """Telefon numaralarını temizler (Sayı veya String gelse de çalışır)."""
    try:
        # Gelen veri ne olursa olsun önce stringe çevir, sonra temizle
        val_str = str(value)
        clean_str = ''.join(filter(str.isdigit, val_str))
        return clean_str
    except:
        return ""

def clean_coordinates(value):
    """Koordinatları (Virgül/Nokta) temizler."""
    try:
        # Virgülü noktaya çevir ve float yap
        val_str = str(value).replace(',', '.')
        return float(val_str)
    except:
        return None

# --- 3. VERİTABANI BAĞLANTISI ---
@st.cache_resource(show_spinner=False)
def get_google_sheet_data(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = None
    try:
        # 1. Yerel Dosya
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    except FileNotFoundError:
        # 2. Cloud Secrets
        try:
            if "gcp_service_account" in st.secrets:
                creds_dict = st.secrets["gcp_service_account"]
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        except:
            return [], None

    if creds:
        try:
            client = gspread.authorize(creds)
            sheet = client.open("Remax_Veritabani").worksheet(sheet_name)
            data = sheet.get_all_records()
            return data, sheet
        except Exception as e:
            st.error(f"Veritabanı Hatası: {e}")
            return [], None
    return [], None

# --- 4. CRUD İŞLEMLERİ ---
def add_row_to_sheet(sheet_object, row_data):
    try:
        sheet_object.append_row(row_data)
        st.toast("✅ Kayıt Eklendi!", icon="🎉")
        time.sleep(1)
    except Exception as e:
        st.error(f"Hata: {e}")

def delete_row_from_sheet(sheet_object, title_to_delete):
    try:
        titles = sheet_object.col_values(2)
        if title_to_delete in titles:
            row_index = titles.index(title_to_delete) + 1
            sheet_object.delete_rows(row_index)
            st.toast(f"🗑️ '{title_to_delete}' silindi!", icon="✅")
            time.sleep(1)
            st.rerun()
        else:
            st.warning("Kayıt bulunamadı.")
    except Exception as e:
        st.error(f"Hata: {e}")

# --- 5. ANA UYGULAMA ---
def main():
    if 'secili_menü' not in st.session_state:
        st.session_state.secili_menü = "📊 Dashboard"

    def sayfa_degistir(hedef_sayfa):
        st.session_state.secili_menü = hedef_sayfa

    # --- YAN MENÜ ---
    with st.sidebar:
        c_img, c_txt = st.columns([1, 3])
        with c_img:
            st.image(PROFIL_FOTO_URL, width=60)
        with c_txt:
            st.write("**Baran Günek**")
            st.caption("Gayrimenkul Danışmanı")
        
        st.divider()
        menu = st.radio("Panel", ["📊 Dashboard", "🏠 Portföy Yönetimi", "🗺️ Harita & Analiz", "🤖 Akıllı Eşleşme", "👥 Müşteriler"], key="secili_menü")
        
        # Hedef Çubuğu (Hatasız)
        st.write("---")
        st.subheader("🎯 Ciro Hedefi")
        data_p, _ = get_google_sheet_data("Portfoy")
        mevcut_ciro = 0
        if data_p:
            df_temp = pd.DataFrame(data_p)
            if 'Fiyat' in df_temp.columns:
                 mevcut_ciro = sum([clean_currency(x) for x in df_temp['Fiyat']])
        progress = min(mevcut_ciro / 15000000, 1.0)
        st.progress(progress)
        st.caption(f"{(mevcut_ciro/1000000):.1f}M / 15.0M TL")

    # --- DASHBOARD ---
    if menu == "📊 Dashboard":
        st.title("Yönetim Paneli")
        data_p, _ = get_google_sheet_data("Portfoy")
        data_m, _ = get_google_sheet_data("Musteriler")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📦 İlanlar", len(data_p) if data_p else 0)
        c2.metric("👥 Müşteriler", len(data_m) if data_m else 0)
        c3.metric("💰 Beklenen Kazanç", f"{(mevcut_ciro * 0.02)/1000:,.0f}k ₺")
        c4.metric("📅 Randevu", "2", "Bugün")

        st.subheader("🚀 Hızlı İşlemler")
        b1, b2 = st.columns(2)
        with b1:
            st.button("➕ İlan Ekle", on_click=sayfa_degistir, args=("🏠 Portföy Yönetimi",), use_container_width=True)
        with b2:
            st.button("🔍 Eşleşme", on_click=sayfa_degistir, args=("🤖 Akıllı Eşleşme",), use_container_width=True)

    # --- PORTFÖY ---
    elif menu == "🏠 Portföy Yönetimi":
        st.title("Portföy Yönetimi")
        t1, t2, t3 = st.tabs(["📋 Liste", "➕ Ekle", "🗑️ Sil"])
        
        with t1:
            data_p, _ = get_google_sheet_data("Portfoy")
            if data_p:
                df = pd.DataFrame(data_p)
                gm = st.toggle("Galeri Görünümü", value=True)
                if gm:
                    cols = st.columns(3)
                    for index, row in df.iterrows():
                        with cols[index % 3]:
                            img = row.get('Gorsel', "")
                            if not str(img).startswith('http'): img = "https://via.placeholder.com/300x200"
                            st.image(img, use_container_width=True)
                            st.markdown(f"**{row.get('Baslik','-')}**")
                            st.caption(f"{row.get('Fiyat',0)} ₺ | {row.get('Konum','-')}")
                else:
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("Portföy boş.")

        with t2:
            with st.form("add_p", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    baslik = st.text_input("Başlık")
                    tip = st.selectbox("Tip", ["Daire", "Villa", "Arsa", "Ticari"])
                    fiyat = st.number_input("Fiyat", min_value=0)
                    konum = st.text_input("Konum")
                    gorsel = st.text_input("Görsel URL")
                with c2:
                    m2 = st.number_input("M2", min_value=0)
                    oda = st.selectbox("Oda", ["1+1", "2+1", "3+1", "4+1"])
                    durum = st.selectbox("Durum", ["Satılık", "Kiralık"])
                    e1, e2 = st.columns(2)
                    enlem = e1.number_input("Enlem (41.xxx)", format="%.5f", value=41.28)
                    boylam = e2.number_input("Boylam (36.xxx)", format="%.5f", value=36.33)
                
                if st.form_submit_button("Kaydet"):
                    d = [datetime.now().strftime("%Y-%m-%d"), baslik, tip, fiyat, konum, m2, oda, durum, gorsel, enlem, boylam]
                    _, s = get_google_sheet_data("Portfoy")
                    if s: add_row_to_sheet(s, d)

        with t3:
            data_p, sheet_p = get_google_sheet_data("Portfoy")
            if data_p:
                df_del = pd.DataFrame(data_p)
                sl = st.selectbox("Sil", df_del['Baslik'].tolist())
                if st.button("Sil"): delete_row_from_sheet(sheet_p, sl)

    # --- HARİTA (DÜZELTİLDİ) ---
    elif menu == "🗺️ Harita & Analiz":
        st.title("Harita Görünümü")
        data_p, _ = get_google_sheet_data("Portfoy")
        
        if data_p:
            df_map = pd.DataFrame(data_p)
            
            # --- KRİTİK DÜZELTME: Veri Temizliği ---
            # Enlem ve Boylam sütunlarını güvenli şekilde sayıya çeviriyoruz
            # Hatalı verileri (boş, harf vs.) siliyoruz (dropna)
            if 'Enlem' in df_map.columns and 'Boylam' in df_map.columns:
                try:
                    df_map['lat'] = df_map['Enlem'].apply(clean_coordinates)
                    df_map['lon'] = df_map['Boylam'].apply(clean_coordinates)
                    
                    # Koordinatı olmayan satırları harita için geçici olarak kaldır
                    df_map = df_map.dropna(subset=['lat', 'lon'])
                    
                    if not df_map.empty:
                        st.map(df_map, zoom=11, use_container_width=True)
                    else:
                        st.warning("Haritada gösterilecek geçerli koordinat verisi bulunamadı. Lütfen 'Portföy Yönetimi'nden enlem/boylam girdiğinizden emin olun.")
                except Exception as e:
                    st.error(f"Harita işlenirken hata oluştu: {e}")
            else:
                st.error("Google Sheets'te 'Enlem' ve 'Boylam' sütun başlıkları eksik.")
        else:
            st.info("Veri yok.")

    # --- EŞLEŞME ---
    elif menu == "🤖 Akıllı Eşleşme":
        st.title("Eşleşme")
        data_p, _ = get_google_sheet_data("Portfoy")
        data_m, _ = get_google_sheet_data("Musteriler")
        
        if data_p and data_m:
            df_p = pd.DataFrame(data_p)
            df_m = pd.DataFrame(data_m)
            mst = st.selectbox("Müşteri", df_m['Ad_Soyad'])
            talep = df_m[df_m['Ad_Soyad'] == mst].iloc[0].get('Talep', '')
            
            st.info(f"Aranan: {talep}")
            res = df_p[df_p['Durum'] == ('Satılık' if 'Satılık' in talep else 'Kiralık')]
            if not res.empty:
                st.dataframe(res[['Baslik','Fiyat','Konum']], use_container_width=True)
            else:
                st.warning("Eşleşme yok.")
        else:
            st.warning("Yetersiz veri.")

    # --- MÜŞTERİLER (DÜZELTİLDİ) ---
    elif menu == "👥 Müşteriler":
        st.title("Müşteri Listesi")
        t1, t2 = st.tabs(["📒 Liste", "➕ Ekle"])
        
        with t1:
            data_m, _ = get_google_sheet_data("Musteriler")
            if data_m:
                df_m = pd.DataFrame(data_m)
                
                # Sütun kontrolü (Hata vermemesi için)
                required_cols = ['Ad_Soyad', 'Telefon', 'Talep', 'Notlar', 'Butce']
                missing_cols = [c for c in required_cols if c not in df_m.columns]
                
                if not missing_cols:
                    for i, row in df_m.iterrows():
                        with st.expander(f"👤 {row['Ad_Soyad']} ({row['Talep']})"):
                            c1, c2 = st.columns([3, 1])
                            with c1:
                                st.write(f"📞 {row['Telefon']}")
                                st.write(f"📝 {row['Notlar']}")
                                st.write(f"💰 {row['Butce']}")
                            with c2:
                                # Telefon temizliği ve link oluşturma
                                raw_tel = clean_phone(row['Telefon'])
                                if raw_tel:
                                    # Başında 90 yoksa ekle (Türkiye için)
                                    if not raw_tel.startswith("90"):
                                        raw_tel = "90" + raw_tel
                                    
                                    msg = f"Merhaba {row['Ad_Soyad']} Bey/Hanım, REMAX'tan Baran ben."
                                    wa_link = f"https://wa.me/{raw_tel}?text={msg}"
                                    st.link_button("💬 WhatsApp", wa_link)
                                else:
                                    st.caption("No Tel")
                else:
                    st.error(f"Google Sheets başlıklarında eksik var: {missing_cols}")
            else:
                st.info("Müşteri yok.")

        with t2:
            with st.form("add_m"):
                ad = st.text_input("Ad Soyad")
                tel = st.text_input("Telefon")
                talep = st.selectbox("Talep", ["Satılık Daire", "Kiralık Daire", "Arsa"])
                butce = st.text_input("Bütçe")
                notlar = st.text_area("Notlar")
                if st.form_submit_button("Kaydet"):
                    d = [datetime.now().strftime("%Y-%m-%d"), ad, tel, talep, butce, notlar]
                    _, s = get_google_sheet_data("Musteriler")
                    if s: add_row_to_sheet(s, d)

if __name__ == "__main__":
    main()
