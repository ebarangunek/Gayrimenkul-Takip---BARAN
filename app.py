import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- 1. SAYFA AYARLARI (Modern Görünüm İçin İlk Adım) ---
st.set_page_config(
    page_title="REMAX/Park - Pro CRM",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS (Tasarım Sihri) ---
# Burası uygulamanın "Makyaj" kısmıdır.
def local_css():
    st.markdown("""
    <style>
        /* Ana Arkaplan Rengi */
        .stApp {
            background-color: #0E1117;
        }
        /* Buton Tasarımları (Remax Kırmızısı) */
        .stButton>button {
            background-color: #DC3545;
            color: white;
            border-radius: 12px;
            border: none;
            padding: 10px 24px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #bb2d3b;
            box-shadow: 0 4px 8px rgba(220, 53, 69, 0.3);
        }
        /* Metrik Kartları */
        div[data-testid="stMetric"] {
            background-color: #262730;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #004085; /* Remax Mavisi Çizgi */
        }
        /* Tablo Başlıkları */
        thead tr th:first-child {display:none}
        tbody th {display:none}
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- 3. VERİTABANI BAĞLANTISI (Hatasız Versiyon) ---
def get_google_sheet_data(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        # Cloud Secrets veya Yerel Dosya Kontrolü
        if "gcp_service_account" in st.secrets:
            creds_dict = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
            
        client = gspread.authorize(creds)
        sheet = client.open("baran_gayrimenkul_veritabani").worksheet(sheet_name)
        data = sheet.get_all_records()
        return data, sheet
    except Exception as e:
        st.error(f"Bağlantı Hatası: {e}")
        return [], None

def add_row_to_sheet(sheet_object, row_data):
    try:
        sheet_object.append_row(row_data)
        st.toast("✅ Kayıt Başarıyla Eklendi!", icon="🎉") # Modern bildirim
    except Exception as e:
        st.error(f"Hata: {e}")

# --- 4. ANA ARAYÜZ (DÜZELTİLMİŞ & HATASIZ) ---
# --- 4. ANA ARAYÜZ (CALLBACK İLE DÜZELTİLMİŞ) ---
def main():
    # Sayfa hafızasını başlat
    if 'secili_menü' not in st.session_state:
        st.session_state.secili_menü = "📊 Dashboard"

    # --- YARDIMCI FONKSİYON (CALLBACK) ---
    # Bu fonksiyon butonlara basıldığında çalışacak
    def sayfa_degistir(hedef_sayfa):
        st.session_state.secili_menü = hedef_sayfa

    # Yan Menü Tasarımı
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Remax_logo.svg/2560px-Remax_logo.svg.png", width=200)
        st.write("---")
        st.title("Danışman Paneli")
        
        # Menü widget'ı session_state'e bağlı çalışır
        menu = st.radio(
            "Navigasyon",
            ["📊 Dashboard", "🏠 Portföy Yönetimi", "👥 Müşteri İlişkileri"],
            key="secili_menü"
        )
        st.write("---")
        st.info("💡 **İpucu:** Telefondan girerken 'Ana Ekrana Ekle' demeyi unutma.")

    # --- SAYFA: DASHBOARD ---
    if menu == "📊 Dashboard":
        st.title("Hoş Geldin, Baran Günek 👋")
        st.markdown("Bugünün özeti ve performans durumu.")
        
        data_p, _ = get_google_sheet_data("Portfoy")
        data_m, _ = get_google_sheet_data("Musteriler")
        
        df_p = pd.DataFrame(data_p) if data_p else pd.DataFrame()
        
        # Hesaplamalar
        toplam_portfoy = len(data_p)
        toplam_musteri = len(data_m)
        toplam_deger = 0
        if not df_p.empty and 'Fiyat' in df_p.columns:
             try:
                 temiz_fiyat = df_p['Fiyat'].astype(str).str.replace('₺', '').str.replace('.', '').str.replace(',', '')
                 toplam_deger = pd.to_numeric(temiz_fiyat, errors='coerce').sum()
             except:
                 toplam_deger = 0

        # Metrikler
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📦 Toplam Portföy", f"{toplam_portfoy} Adet", delta="Aktif")
        with col2:
            st.metric("👥 Kayıtlı Müşteri", f"{toplam_musteri} Kişi", delta="+Yeni")
        with col3:
            milyon_deger = toplam_deger / 1_000_000 if toplam_deger else 0
            st.metric("💰 Portföy Değeri", f"{milyon_deger:.1f} M₺", delta="Tahmini")

        # --- HIZLI İŞLEMLER (BURASI DEĞİŞTİ) ---
        st.write("---")
        st.subheader("🚀 Hızlı İşlemler")
        c1, c2 = st.columns(2)
        with c1:
            # on_click parametresi ile fonksiyonu çağırıyoruz
            st.button(
                "➕ Hızlı Portföy Ekle", 
                use_container_width=True,
                on_click=sayfa_degistir, 
                args=("🏠 Portföy Yönetimi",) # Fonksiyona gidecek parametre
            )
        with c2:
             st.button(
                 "🔍 Müşteri Ara", 
                 use_container_width=True,
                 on_click=sayfa_degistir,
                 args=("👥 Müşteri İlişkileri",)
             )

    # --- SAYFA: PORTFÖY YÖNETİMİ ---
    elif menu == "🏠 Portföy Yönetimi":
        st.title("Portföy Yönetimi")
        tab1, tab2 = st.tabs(["📋 Portföy Listesi", "➕ Yeni Ekle"])
        
        with tab1:
            data_p, _ = get_google_sheet_data("Portfoy")
            if data_p:
                df = pd.DataFrame(data_p)
                st.data_editor(
                    df,
                    column_config={
                        "Fiyat": st.column_config.NumberColumn("Fiyat (TL)", format="%d ₺"),
                        "Tip": st.column_config.SelectboxColumn("Tip", options=["Daire", "Villa", "Arsa", "Ticari"], required=True),
                        "Durum": st.column_config.SelectboxColumn("Durum", options=["Satılık", "Kiralık"], width="small", required=True),
                        "M2": st.column_config.ProgressColumn("Büyüklük (m2)", format="%f m²", min_value=0, max_value=500),
                    },
                    hide_index=True,
                    use_container_width=True,
                    num_rows="dynamic"
                )
            else:
                st.info("Henüz portföy yok.")

        with tab2:
            st.subheader("Yeni Portföy Oluştur")
            with st.form("portfoy_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    baslik = st.text_input("İlan Başlığı")
                    tip = st.selectbox("Mülk Tipi", ["Daire", "Villa", "Arsa", "Ticari"])
                    fiyat = st.number_input("Fiyat", min_value=0, step=1000)
                    konum = st.text_input("Konum")
                with c2:
                    m2 = st.number_input("M2", min_value=0)
                    oda = st.selectbox("Oda", ["1+1", "2+1", "3+1", "4+1", "Villa", "Diğer"])
                    durum = st.selectbox("Durum", ["Satılık", "Kiralık"])
                
                if st.form_submit_button("Kaydet ve Yayınla"):
                    tarih = datetime.now().strftime("%Y-%m-%d")
                    new_data = [tarih, baslik, tip, fiyat, konum, m2, oda, durum]
                    _, sheet = get_google_sheet_data("Portfoy")
                    add_row_to_sheet(sheet, new_data)

    # --- SAYFA: MÜŞTERİ İLİŞKİLERİ ---
    elif menu == "👥 Müşteri İlişkileri":
        st.title("Müşteri Veritabanı")
        tab_m1, tab_m2 = st.tabs(["🔍 Müşteri Bul", "busts_in_silhouette Müşteri Ekle"])
        
        with tab_m1:
            data_m, _ = get_google_sheet_data("Musteriler")
            if data_m:
                df_m = pd.DataFrame(data_m)
                search_term = st.text_input("🔍 İsim veya Telefon ile ara:", "")
                if search_term:
                    filtered_df = df_m[
                        df_m['Ad_Soyad'].str.contains(search_term, case=False) | 
                        df_m['Telefon'].str.contains(search_term, case=False)
                    ]
                    st.dataframe(filtered_df, use_container_width=True)
                else:
                    st.dataframe(df_m, use_container_width=True)
            else:
                st.warning("Müşteri listeniz boş.")

        with tab_m2:
            st.markdown("### 📝 Yeni Müşteri Kartı")
            with st.form("musteri_form", clear_on_submit=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    ad = st.text_input("Ad Soyad")
                    tel = st.text_input("Telefon")
                    talep = st.selectbox("Talep", ["Satılık Daire", "Kiralık Daire", "Arsa/Yatırım", "Satıcı"])
                with col_b:
                    butce = st.text_input("Bütçe Aralığı")
                    notlar = st.text_area("Müşteri Notları")
                
                if st.form_submit_button("Müşteriyi Sisteme İşle"):
                    tarih = datetime.now().strftime("%Y-%m-%d")
                    new_cust = [tarih, ad, tel, talep, butce, notlar]
                    _, sheet_m = get_google_sheet_data("Musteriler")
                    add_row_to_sheet(sheet_m, new_cust)
                    
    # --- SAYFA: PORTFÖY YÖNETİMİ ---
    elif menu == "🏠 Portföy Yönetimi":
        st.title("Portföy Yönetimi")
        tab1, tab2 = st.tabs(["📋 Portföy Listesi", "➕ Yeni Ekle"])
        
        with tab1:
            data_p, _ = get_google_sheet_data("Portfoy")
            if data_p:
                df = pd.DataFrame(data_p)
                st.data_editor(
                    df,
                    column_config={
                        "Fiyat": st.column_config.NumberColumn("Fiyat (TL)", format="%d ₺"),
                        "Tip": st.column_config.SelectboxColumn("Tip", options=["Daire", "Villa", "Arsa", "Ticari"], required=True),
                        "Durum": st.column_config.SelectboxColumn("Durum", options=["Satılık", "Kiralık"], width="small", required=True),
                        "M2": st.column_config.ProgressColumn("Büyüklük (m2)", format="%f m²", min_value=0, max_value=500),
                    },
                    hide_index=True,
                    use_container_width=True,
                    num_rows="dynamic"
                )
            else:
                st.info("Henüz portföy yok.")

        with tab2:
            st.subheader("Yeni Portföy Oluştur")
            with st.form("portfoy_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    baslik = st.text_input("İlan Başlığı")
                    tip = st.selectbox("Mülk Tipi", ["Daire", "Villa", "Arsa", "Ticari"])
                    fiyat = st.number_input("Fiyat", min_value=0, step=1000)
                    konum = st.text_input("Konum")
                with c2:
                    m2 = st.number_input("M2", min_value=0)
                    oda = st.selectbox("Oda", ["1+1", "2+1", "3+1", "4+1", "Villa", "Diğer"])
                    durum = st.selectbox("Durum", ["Satılık", "Kiralık"])
                
                if st.form_submit_button("Kaydet ve Yayınla"):
                    tarih = datetime.now().strftime("%Y-%m-%d")
                    new_data = [tarih, baslik, tip, fiyat, konum, m2, oda, durum]
                    _, sheet = get_google_sheet_data("Portfoy")
                    add_row_to_sheet(sheet, new_data)

    # --- SAYFA: MÜŞTERİ İLİŞKİLERİ ---
    elif menu == "👥 Müşteri İlişkileri":
        st.title("Müşteri Veritabanı")
        tab_m1, tab_m2 = st.tabs(["🔍 Müşteri Bul", "busts_in_silhouette Müşteri Ekle"])
        
        with tab_m1:
            data_m, _ = get_google_sheet_data("Musteriler")
            if data_m:
                df_m = pd.DataFrame(data_m)
                search_term = st.text_input("🔍 İsim veya Telefon ile ara:", "")
                if search_term:
                    filtered_df = df_m[
                        df_m['Ad_Soyad'].str.contains(search_term, case=False) | 
                        df_m['Telefon'].str.contains(search_term, case=False)
                    ]
                    st.dataframe(filtered_df, use_container_width=True)
                else:
                    st.dataframe(df_m, use_container_width=True)
            else:
                st.warning("Müşteri listeniz boş.")

        with tab_m2:
            st.markdown("### 📝 Yeni Müşteri Kartı")
            with st.form("musteri_form", clear_on_submit=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    ad = st.text_input("Ad Soyad")
                    tel = st.text_input("Telefon")
                    talep = st.selectbox("Talep", ["Satılık Daire", "Kiralık Daire", "Arsa/Yatırım", "Satıcı"])
                with col_b:
                    butce = st.text_input("Bütçe Aralığı")
                    notlar = st.text_area("Müşteri Notları")
                
                if st.form_submit_button("Müşteriyi Sisteme İşle"):
                    tarih = datetime.now().strftime("%Y-%m-%d")
                    new_cust = [tarih, ad, tel, talep, butce, notlar]
                    _, sheet_m = get_google_sheet_data("Musteriler")
                    add_row_to_sheet(sheet_m, new_cust)
    
    # --- SAYFA: PORTFÖY YÖNETİMİ ---
    elif menu == "🏠 Portföy Yönetimi":
        st.title("Portföy Yönetimi")
        
        # Sekmeli Yapı (Tabs) - Çok daha modern
        tab1, tab2 = st.tabs(["📋 Portföy Listesi", "➕ Yeni Ekle"])
        
        with tab1:
            data_p, _ = get_google_sheet_data("Portfoy")
            if data_p:
                df = pd.DataFrame(data_p)
                
                # --- MODERN TABLO GÖRÜNÜMÜ ---
                # column_config ile tabloyu özelleştiriyoruz
                st.data_editor(
                    df,
                    column_config={
                        "Fiyat": st.column_config.NumberColumn(
                            "Fiyat (TL)",
                            help="Mülkün satış/kiralama fiyatı",
                            format="%d ₺",  # Para birimi formatı
                        ),
                        "Tip": st.column_config.SelectboxColumn(
                            "Tip",
                            options=["Daire", "Villa", "Arsa", "Ticari"],
                            required=True,
                        ),
                        "Durum": st.column_config.SelectboxColumn(
                            "Durum",
                            options=["Satılık", "Kiralık"],
                            width="small",
                            required=True,
                        ),
                        "M2": st.column_config.ProgressColumn(
                            "Büyüklük (m2)",
                            format="%f m²",
                            min_value=0,
                            max_value=500, # Bar doluluk oranı için
                        ),
                    },
                    hide_index=True,
                    use_container_width=True,
                    num_rows="dynamic" # Satır eklemeye izin ver
                )
            else:
                st.info("Henüz portföy yok.")

        with tab2:
            st.subheader("Yeni Portföy Oluştur")
            with st.form("portfoy_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    baslik = st.text_input("İlan Başlığı")
                    tip = st.selectbox("Mülk Tipi", ["Daire", "Villa", "Arsa", "Ticari"])
                    fiyat = st.number_input("Fiyat", min_value=0, step=1000)
                    konum = st.text_input("Konum")
                with c2:
                    m2 = st.number_input("M2", min_value=0)
                    oda = st.selectbox("Oda", ["1+1", "2+1", "3+1", "4+1", "Villa", "Diğer"])
                    durum = st.selectbox("Durum", ["Satılık", "Kiralık"])
                
                if st.form_submit_button("Kaydet ve Yayınla"):
                    tarih = datetime.now().strftime("%Y-%m-%d")
                    # DİKKAT: Sıralama Google Sheets sütun sırasıyla aynı olmalı
                    new_data = [tarih, baslik, tip, fiyat, konum, m2, oda, durum]
                    
                    _, sheet = get_google_sheet_data("Portfoy")
                    add_row_to_sheet(sheet, new_data)

    # --- SAYFA: MÜŞTERİ İLİŞKİLERİ ---
    elif menu == "👥 Müşteri İlişkileri":
        st.title("Müşteri Veritabanı")
        
        tab_m1, tab_m2 = st.tabs(["🔍 Müşteri Bul", "busts_in_silhouette Müşteri Ekle"])
        
        with tab_m1:
            data_m, _ = get_google_sheet_data("Musteriler")
            if data_m:
                df_m = pd.DataFrame(data_m)
                
                # Arama Kutusu
                search_term = st.text_input("🔍 İsim veya Telefon ile ara:", "")
                
                if search_term:
                    # Büyük/Küçük harf duyarsız arama
                    filtered_df = df_m[
                        df_m['Ad_Soyad'].str.contains(search_term, case=False) | 
                        df_m['Telefon'].str.contains(search_term, case=False)
                    ]
                    st.dataframe(filtered_df, use_container_width=True)
                else:
                    st.dataframe(df_m, use_container_width=True)
            else:
                st.warning("Müşteri listeniz boş.")

        with tab_m2:
            with st.container():
                st.markdown("### 📝 Yeni Müşteri Kartı")
                with st.form("musteri_form", clear_on_submit=True):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        ad = st.text_input("Ad Soyad")
                        tel = st.text_input("Telefon (5XX...)")
                        talep = st.selectbox("Talep", ["Satılık Daire", "Kiralık Daire", "Arsa/Yatırım", "Satıcı"])
                    with col_b:
                        butce = st.text_input("Bütçe Aralığı")
                        notlar = st.text_area("Müşteri Notları", height=100)
                    
                    if st.form_submit_button("Müşteriyi Sisteme İşle"):
                        tarih = datetime.now().strftime("%Y-%m-%d")
                        new_cust = [tarih, ad, tel, talep, butce, notlar]
                        _, sheet_m = get_google_sheet_data("Musteriler")
                        add_row_to_sheet(sheet_m, new_cust)

if __name__ == "__main__":
    main()
