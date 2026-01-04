import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- AYARLAR ---
# Sayfa yapısı ve başlığı
st.set_page_config(page_title="REMAX/Park Portföy - BARAN", page_icon="🏠", layout="wide")

# --- GÜNCELLENMİŞ GOOGLE SHEETS BAĞLANTISI ---
def get_google_sheet_data(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        # 1. Yöntem: Streamlit Cloud Secrets (Sunucu)
        if "gcp_service_account" in st.secrets:
            creds_dict = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        # 2. Yöntem: Yerel Dosya (Bilgisayarın)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
            
        client = gspread.authorize(creds)
        sheet = client.open("baran_gayrimenkul_veritabani").worksheet(sheet_name)
        data = sheet.get_all_records()
        return data, sheet
    except Exception as e:
        st.error(f"Veritabanı bağlantı hatası: {e}")
        return [], None

# --- YENİ KAYIT EKLEME FONKSİYONU ---
def add_row_to_sheet(sheet_object, row_data):
    try:
        sheet_object.append_row(row_data)
        st.success("✅ Kayıt başarıyla eklendi!")
        # Veri eklendikten sonra sayfayı yenilemek için önbelleği temizleyebiliriz (opsiyonel)
    except Exception as e:
        st.error(f"Kayıt eklenirken hata oluştu: {e}")

# --- ARAYÜZ (FRONTEND) ---
def main():
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Remax_logo.svg/2560px-Remax_logo.svg.png", width=150)
    st.sidebar.title("Danışman Paneli")
    secim = st.sidebar.radio("Menü:", ["🏠 Özet & Durum", "➕ Portföy Ekle", "📋 Portföy Listesi", "busts_in_silhouette Müşteri Ekle", "search Müşteri Listesi"])

    # --- 1. ÖZET EKRANI ---
    if secim == "🏠 Özet & Durum":
        st.title("REMAX/Park - Dijital Asistan")
        st.write(f"Bugün: {datetime.now().strftime('%d.%m.%Y')}")
        
        # Verileri Çek
        data_p, _ = get_google_sheet_data("portfoy")
        data_m, _ = get_google_sheet_data("musteriler")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Toplam Portföy", len(data_p))
        with col2:
            st.metric("Kayıtlı Müşteri", len(data_m))
        with col3:
             st.info("Veritabanı: Google Sheets 🟢")

    # --- 2. PORTFÖY EKLEME ---
    elif secim == "➕ Portföy Ekle":
        st.header("Yeni Mülk Girişi")
        
        # Form Alanları
        with st.form("portfoy_form"):
            col1, col2 = st.columns(2)
            with col1:
                baslik = st.text_input("İlan Başlığı")
                tip = st.selectbox("Tipi", ["Daire", "Villa", "Arsa", "Dükkan", "Ofis"])
                fiyat = st.number_input("Fiyat", min_value=0)
                konum = st.text_input("Konum / Mahalle")
            with col2:
                m2 = st.number_input("Metrekare (m2)", min_value=0)
                oda = st.selectbox("Oda Sayısı", ["1+1", "2+1", "3+1", "4+1", "Villa", "Yok"])
                durum = st.selectbox("Durum", ["Satılık", "Kiralık"])
            
            submit = st.form_submit_button("Portföyü Kaydet")
            
            if submit:
                tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
                # Veriyi Hazırla
                yeni_veri = [tarih, baslik, tip, fiyat, konum, m2, oda, durum]
                # Veriyi Gönder
                _, sheet_obj = get_google_sheet_data("portfoy")
                if sheet_obj:
                    add_row_to_sheet(sheet_obj, yeni_veri)

    # --- 3. PORTFÖY LİSTELEME ---
    elif secim == "📋 Portföy Listesi":
        st.header("Güncel Portföy Listesi")
        data_p, _ = get_google_sheet_data("portfoy")
        
        if data_p:
            df = pd.DataFrame(data_p)
            st.dataframe(df, use_container_width=True)
            
            # Filtreleme Özelliği
            st.subheader("Hızlı Arama")
            arama = st.text_input("Başlık veya Konum içinde ara:")
            if arama:
                filtreli = df[df['Baslik'].str.contains(arama, case=False) | df['Konum'].str.contains(arama, case=False)]
                st.write("Arama Sonuçları:")
                st.dataframe(filtreli)
        else:
            st.warning("Henüz hiç portföy eklenmemiş.")

    # --- 4. MÜŞTERİ EKLEME ---
    elif secim == "busts_in_silhouette Müşteri Ekle":
        st.header("Yeni Müşteri Kaydı")
        
        with st.form("musteri_form"):
            ad = st.text_input("Ad Soyad")
            tel = st.text_input("Telefon")
            talep = st.selectbox("Talep", ["Satılık Daire Arıyor", "Kiralık Daire Arıyor", "Yatırımcı", "Mülk Sahibi"])
            butce = st.text_input("Bütçe Aralığı")
            notlar = st.text_area("Özel Notlar")
            
            submit_m = st.form_submit_button("Müşteriyi Kaydet")
            
            if submit_m:
                tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
                yeni_musteri = [tarih, ad, tel, talep, butce, notlar]
                _, sheet_obj_m = get_google_sheet_data("musteriler")
                if sheet_obj_m:
                    add_row_to_sheet(sheet_obj_m, yeni_musteri)

    # --- 5. MÜŞTERİ LİSTESİ ---
    elif secim == "search Müşteri Listesi":
        st.header("Müşteri Veritabanı")
        data_m, _ = get_google_sheet_data("Musteriler")
        
        if data_m:
            df_m = pd.DataFrame(data_m)
            st.dataframe(df_m, use_container_width=True)
        else:
            st.warning("Henüz müşteri kaydı yok.")

if __name__ == "__main__":
    main()