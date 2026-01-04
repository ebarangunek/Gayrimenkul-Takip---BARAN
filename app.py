import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# --- 1. AYARLAR VE CSS (MODERN ARAYÜZ) ---
st.set_page_config(
    page_title="BARAN | Gayrimenkul OS",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Kendi Fotoğrafın İçin Ayar (Buraya resim linki veya dosya yolu yaz)
# Örnek: "assets/profil.jpg" veya internet linki.
PROFIL_FOTO_URL = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png" 

# Custom CSS ile Arayüzü Güzelleştirme
st.markdown("""
<style>
    /* Metrik Kartları */
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    /* Butonlar (Remax Kırmızısı) */
    .stButton>button {
        border-radius: 8px;
        font-weight: bold;
        transition: 0.3s;
    }
    /* Tablo Başlıkları */
    thead tr th:first-child {display:none}
    tbody th {display:none}
    
    /* Yan Menü İyileştirmesi */
    section[data-testid="stSidebar"] {
        background-color: #111;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. YARDIMCI FONKSİYONLAR ---
def clean_currency(value):
    """
    Fiyat verilerini (örn: '10.000.000 TL') temizleyip sayıya çevirir.
    Hata almamak için kritik fonksiyondur.
    """
    try:
        if isinstance(value, str):
            # Sadece rakamları bırak
            clean_str = ''.join(filter(str.isdigit, value))
            return int(clean_str) if clean_str else 0
        return int(value)
    except:
        return 0

# --- 3. VERİTABANI BAĞLANTISI (AKILLI SİSTEM) ---
@st.cache_resource(show_spinner=False) # Bağlantıyı önbelleğe alıp hızlandırıyoruz
def get_google_sheet_data(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = None
    
    try:
        # 1. VS Code (Yerel) Kontrolü
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    except FileNotFoundError:
        # 2. Cloud (Sunucu) Kontrolü
        try:
            if "gcp_service_account" in st.secrets:
                creds_dict = st.secrets["gcp_service_account"]
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        except Exception:
            return [], None

    if creds:
        try:
            client = gspread.authorize(creds)
            sheet = client.open("baran_gayrimenkul_veritabani").worksheet(sheet_name)
            data = sheet.get_all_records()
            return data, sheet
        except Exception as e:
            st.error(f"Veritabanına erişilemedi: {e}")
            return [], None
    return [], None

# --- 4. CRUD İŞLEMLERİ (EKLE/SİL) ---
def add_row_to_sheet(sheet_object, row_data):
    try:
        sheet_object.append_row(row_data)
        st.toast("✅ Kayıt Başarıyla Eklendi!", icon="🎉")
        time.sleep(1) # Kullanıcının mesajı görmesi için bekleme
    except Exception as e:
        st.error(f"Kayıt eklenirken hata: {e}")

def delete_row_from_sheet(sheet_object, title_to_delete):
    try:
        titles = sheet_object.col_values(2) # 2. Sütun Başlık sütunu
        if title_to_delete in titles:
            # Google Sheets 1'den başlar, Python 0'dan. +1 ekliyoruz.
            row_index = titles.index(title_to_delete) + 1
            sheet_object.delete_rows(row_index)
            st.toast(f"🗑️ '{title_to_delete}' silindi!", icon="✅")
            time.sleep(1)
            st.rerun()
        else:
            st.warning("Silinecek kayıt bulunamadı.")
    except Exception as e:
        st.error(f"Silme hatası: {e}")

# --- 5. ANA UYGULAMA MANTIĞI ---
def main():
    # Sayfa hafızası (Navigation State)
    if 'secili_menü' not in st.session_state:
        st.session_state.secili_menü = "📊 Dashboard"

    def sayfa_degistir(hedef_sayfa):
        st.session_state.secili_menü = hedef_sayfa

    # --- YAN MENÜ TASARIMI ---
    with st.sidebar:
        # Profil Alanı
        col_img, col_txt = st.columns([1, 2])
        with col_img:
            st.image(PROFIL_FOTO_URL, width=80)
        with col_txt:
            st.write("**Baran Günek**")
            st.caption("Gayrimenkul Danışmanı")
        
        st.divider()
        
        menu = st.radio(
            "Yönetim Paneli",
            ["📊 Dashboard", "🏠 Portföy Yönetimi", "🗺️ Harita & Analiz", "🤖 Akıllı Eşleşme", "👥 Müşteriler"],
            key="secili_menü"
        )
        
        st.write("---")
        
        # Gamification (Hedef Çubuğu)
        st.subheader("🎯 Mart Hedefi")
        hedef_ciro = 15000000 
        
        data_p, _ = get_google_sheet_data("Portfoy")
        mevcut_ciro = 0
        
        if data_p:
            df_temp = pd.DataFrame(data_p)
            if 'Fiyat' in df_temp.columns:
                 mevcut_ciro = sum([clean_currency(x) for x in df_temp['Fiyat']])
        
        progress = min(mevcut_ciro / hedef_ciro, 1.0) if hedef_ciro > 0 else 0
        st.progress(progress)
        st.caption(f"Portföy Değeri: {(mevcut_ciro/1000000):.1f}M / {(hedef_ciro/1000000):.1f}M TL")

    # --- SAYFA: DASHBOARD ---
    if menu == "📊 Dashboard":
        st.title("Hoş Geldin, Baran Bey 👋")
        st.markdown("_Günün özeti ve iş performansın aşağıdadır._")
        
        data_p, _ = get_google_sheet_data("Portfoy")
        data_m, _ = get_google_sheet_data("Musteriler")
        
        # Metrikler
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📦 Aktif İlan", len(data_p) if data_p else 0, "Adet")
        c2.metric("👥 Müşteri", len(data_m) if data_m else 0, "Kişi")
        
        hizmet_bedeli = mevcut_ciro * 0.02 # %2 Hizmet Bedeli
        c3.metric("💰 Beklenen Kazanç", f"{hizmet_bedeli/1000:,.0f}k ₺", "Potansiyel")
        c4.metric("📅 Randevular", "2", "Bugün")

        # Hatırlatıcılar
        st.write("")
        st.subheader("🔔 Ajanda")
        with st.container():
            st.info("📞 **Ahmet Yılmaz** (Yatırımcı) aranacak - Saat 14:30")
            st.warning("🔑 **Atakum Pearl** anahtar teslimi - Yarın 10:00")

        # Hızlı Aksiyonlar
        st.write("")
        st.subheader("🚀 Hızlı İşlemler")
        b1, b2 = st.columns(2)
        with b1:
            st.button("➕ Hızlı İlan Ekle", on_click=sayfa_degistir, args=("🏠 Portföy Yönetimi",), use_container_width=True)
        with b2:
            st.button("🔍 Eşleşme Bul", on_click=sayfa_degistir, args=("🤖 Akıllı Eşleşme",), use_container_width=True)

    # --- SAYFA: PORTFÖY YÖNETİMİ ---
    elif menu == "🏠 Portföy Yönetimi":
        st.title("Portföy Yönetimi")
        tab1, tab2, tab3 = st.tabs(["📋 Liste & Galeri", "➕ Yeni Ekle", "🗑️ İlan Sil"])
        
        with tab1:
            data_p, _ = get_google_sheet_data("Portfoy")
            if data_p:
                df = pd.DataFrame(data_p)
                
                # Görünüm Modu
                col_toggle, _ = st.columns([1, 4])
                galeri_modu = col_toggle.toggle("Galeri Modu", value=True)
                
                if galeri_modu:
                    cols = st.columns(3)
                    for index, row in df.iterrows():
                        with cols[index % 3]:
                            img_link = row.get('Gorsel', "")
                            if not str(img_link).startswith('http'):
                                img_link = "https://via.placeholder.com/300x200?text=Gorsel+Yok"
                            
                            with st.container():
                                st.image(img_link, use_container_width=True)
                                st.markdown(f"**{row['Baslik']}**")
                                st.caption(f"📍 {row['Konum']} | 🏠 {row['Oda']}")
                                st.markdown(f"#### {row['Fiyat']:,} ₺")
                                st.divider()
                else:
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("Henüz sisteme kayıtlı ilan yok.")

        with tab2:
            st.markdown("### Yeni Mülk Girişi")
            with st.form("yeni_ilan", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    baslik = st.text_input("İlan Başlığı")
                    tip = st.selectbox("Tip", ["Daire", "Villa", "Arsa", "Ticari"])
                    fiyat = st.number_input("Fiyat (TL)", min_value=0, step=1000)
                    konum = st.text_input("Konum (Mahalle)")
                    gorsel = st.text_input("Görsel URL (Sağ Tık -> Resim Adresini Kopyala)")
                with c2:
                    m2 = st.number_input("M2", min_value=0)
                    oda = st.selectbox("Oda", ["1+1", "2+1", "3+1", "4+1", "Diğer"])
                    durum = st.selectbox("Durum", ["Satılık", "Kiralık"])
                    e1, e2 = st.columns(2)
                    enlem = e1.number_input("Enlem", format="%.5f", value=41.28)
                    boylam = e2.number_input("Boylam", format="%.5f", value=36.33)

                btn = st.form_submit_button("Kaydet ve Yayınla")
                if btn:
                    tarih = datetime.now().strftime("%Y-%m-%d")
                    # Sütun sırasına dikkat: Tarih, Baslik, Tip, Fiyat, Konum, M2, Oda, Durum, Gorsel, Enlem, Boylam
                    new_data = [tarih, baslik, tip, fiyat, konum, m2, oda, durum, gorsel, enlem, boylam]
                    _, sheet = get_google_sheet_data("Portfoy")
                    if sheet:
                        add_row_to_sheet(sheet, new_data)

        with tab3:
            st.warning("⚠️ DİKKAT: Silinen ilan geri getirilemez.")
            data_p, sheet_p = get_google_sheet_data("Portfoy")
            if data_p:
                df_del = pd.DataFrame(data_p)
                silinecek = st.selectbox("Silinecek İlanı Seç", df_del['Baslik'].tolist())
                if st.button("Seçili İlanı Kalıcı Olarak Sil"):
                    delete_row_from_sheet(sheet_p, silinecek)

    # --- SAYFA: HARİTA ---
    elif menu == "🗺️ Harita & Analiz":
        st.title("Bölgesel Analiz")
        data_p, _ = get_google_sheet_data("Portfoy")
        
        col_map, col_stat = st.columns([3, 1])
        
        with col_map:
            if data_p:
                df_map = pd.DataFrame(data_p)
                try:
                    df_map['lat'] = pd.to_numeric(df_map['Enlem'])
                    df_map['lon'] = pd.to_numeric(df_map['Boylam'])
                    st.map(df_map, zoom=11, use_container_width=True)
                except:
                    st.warning("Harita verisi bozuk veya eksik.")
            else:
                st.write("Haritada gösterilecek veri yok.")

        with col_stat:
            st.markdown("### Pazar Durumu")
            st.info("ℹ️ Atakum bölgesinde 3+1 dairelerin ortalama m2 fiyatı artışta.")
            ort_fiyat = st.number_input("Bölge Ort. Fiyat", value=3000000)
            st.metric("Piyasa Trendi", "Yükselişte", "+%4.2")

    # --- SAYFA: AKILLI EŞLEŞME ---
    elif menu == "🤖 Akıllı Eşleşme":
        st.title("Smart Matchmaker")
        data_p, _ = get_google_sheet_data("Portfoy")
        data_m, _ = get_google_sheet_data("Musteriler")
        
        if data_p and data_m:
            df_p = pd.DataFrame(data_p)
            df_m = pd.DataFrame(data_m)
            
            musteri = st.selectbox("Müşteri Seçin", df_m['Ad_Soyad'])
            # Müşteri verisini al
            m_data = df_m[df_m['Ad_Soyad'] == musteri].iloc[0]
            talep = m_data.get('Talep', '')
            
            st.success(f"**{musteri}** isimli müşteriniz **{talep}** arıyor.")
            
            # Basit Filtreleme
            uygunlar = pd.DataFrame()
            if "Satılık" in talep:
                uygunlar = df_p[df_p['Durum'] == 'Satılık']
            elif "Kiralık" in talep:
                uygunlar = df_p[df_p['Durum'] == 'Kiralık']
            
            st.write("---")
            if not uygunlar.empty:
                st.subheader(f"🎉 {len(uygunlar)} Eşleşme Bulundu!")
                st.dataframe(uygunlar[['Baslik', 'Fiyat', 'Konum']], use_container_width=True)
            else:
                st.warning("Kriterlere uygun ilan bulunamadı.")
        else:
            st.error("Eşleşme yapmak için hem Müşteri hem Portföy verisi gerekli.")

    # --- SAYFA: MÜŞTERİLER (WHATSAPP EKLENDİ) ---
    elif menu == "👥 Müşteriler":
        st.title("Müşteri İlişkileri (CRM)")
        
        tab_m1, tab_m2 = st.tabs(["📒 Müşteri Listesi", "➕ Müşteri Ekle"])
        
        with tab_m1:
            data_m, _ = get_google_sheet_data("Musteriler")
            if data_m:
                df_m = pd.DataFrame(data_m)
                
                # Her satır için özel görünüm
                for i, row in df_m.iterrows():
                    with st.expander(f"👤 {row['Ad_Soyad']} - {row['Talep']}"):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.write(f"**Telefon:** {row['Telefon']}")
                            st.write(f"**Notlar:** {row['Notlar']}")
                            st.write(f"**Bütçe:** {row['Butce']}")
                        with c2:
                            # WhatsApp Linki Oluşturma
                            tel_temiz = ''.join(filter(str.isdigit, str(row['Telefon'])))
                            # Türkiye kodu ekle (90) yoksa
                            if not tel_temiz.startswith("90"):
                                tel_temiz = "90" + tel_temiz
                                
                            msg = f"Merhaba {row['Ad_Soyad']} Bey/Hanım, REMAX Park'tan Baran ben. Nasılsınız?"
                            wa_link = f"https://wa.me/{tel_temiz}?text={msg}"
                            
                            st.link_button("💬 WhatsApp", wa_link)
            else:
                st.info("Müşteri kaydı yok.")

        with tab_m2:
            with st.form("yeni_musteri"):
                ad = st.text_input("Ad Soyad")
                tel = st.text_input("Telefon (Başında 0 olmadan)")
                talep = st.selectbox("Talep", ["Satılık Daire", "Kiralık Daire", "Arsa", "Yatırımcı"])
                butce = st.text_input("Bütçe")
                notlar = st.text_area("Notlar")
                
                if st.form_submit_button("Müşteriyi Kaydet"):
                    tarih = datetime.now().strftime("%Y-%m-%d")
                    # Sütunlar: Tarih, Ad_Soyad, Telefon, Talep, Butce, Notlar
                    new_m = [tarih, ad, tel, talep, butce, notlar]
                    _, sheet_m = get_google_sheet_data("Musteriler")
                    if sheet_m:
                        add_row_to_sheet(sheet_m, new_m)

if __name__ == "__main__":
    main()
