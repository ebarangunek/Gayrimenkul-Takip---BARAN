import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# --- 1. SAYFA AYARLARI ---
st.set_page_config(
    page_title="BARAN Gayrimenkul Takip - Pro OS",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. VERİTABANI BAĞLANTISI ---
def get_google_sheet_data(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
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
        st.toast("✅ Kayıt Başarıyla Eklendi!", icon="🎉")
        time.sleep(1)
    except Exception as e:
        st.error(f"Ekleme Hatası: {e}")

# --- İLAN SİLME FONKSİYONU (YENİ) ---
def delete_row_from_sheet(sheet_object, title_to_delete):
    try:
        # Başlık sütununu (2. sütun) al
        titles = sheet_object.col_values(2) 
        # Aranan başlığın satır numarasını bul (Listeler 0'dan başlar ama Sheets 1'den, o yüzden +1)
        if title_to_delete in titles:
            row_index = titles.index(title_to_delete) + 1
            sheet_object.delete_rows(row_index)
            st.toast(f"🗑️ '{title_to_delete}' başarıyla silindi!", icon="✅")
            time.sleep(1)
            st.rerun()
        else:
            st.warning("Silinecek kayıt bulunamadı.")
    except Exception as e:
        st.error(f"Silme Hatası: {e}")

# --- 3. ANA ARAYÜZ ---
def main():
    if 'secili_menü' not in st.session_state:
        st.session_state.secili_menü = "📊 Dashboard"

    def sayfa_degistir(hedef_sayfa):
        st.session_state.secili_menü = hedef_sayfa

    # --- YAN MENÜ ---
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Remax_logo.svg/2560px-Remax_logo.svg.png", width=180)
        st.title("REMAX OS v2.0")
        
        menu = st.radio(
            "Menü",
            ["📊 Dashboard", "🏠 Portföy Yönetimi", "🗺️ Harita & Analiz", "🤖 Akıllı Eşleşme", "👥 Müşteriler"],
            key="secili_menü"
        )
        
        st.write("---")
        
        # --- HEDEF TAKİPÇİSİ (GAMIFICATION) ---
        st.subheader("🎯 Aylık Hedef")
        hedef_ciro = 10000000 # 10 Milyon TL Portföy Hedefi
        
        # Anlık veriyi çekip hesaplayalım
        data_p, _ = get_google_sheet_data("Portfoy")
        mevcut_ciro = 0
        if data_p:
            df_temp = pd.DataFrame(data_p)
            if 'Fiyat' in df_temp.columns:
                 # Fiyat temizliği
                 mevcut_ciro = pd.to_numeric(df_temp['Fiyat'].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce').sum()
        
        progress = min(mevcut_ciro / hedef_ciro, 1.0)
        st.progress(progress)
        st.caption(f"Hedef: {(mevcut_ciro/1000000):.1f}M / {(hedef_ciro/1000000):.1f}M TL")
        if progress >= 1.0:
            st.balloons()

    # --- SAYFA 1: DASHBOARD ---
    if menu == "📊 Dashboard":
        st.title("Yönetim Paneli")
        
        data_p, _ = get_google_sheet_data("Portfoy")
        data_m, _ = get_google_sheet_data("Musteriler")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📦 Aktif İlan", len(data_p))
        with col2:
            st.metric("👥 Müşteri", len(data_m))
        with col3:
            # Tahmini Komisyon (%2 + KDV varsayımı)
            komisyon = mevcut_ciro * 0.02
            st.metric("💰 Beklenen Hizmet Bedeli", f"{komisyon/1000:,.0f}k ₺")
        with col4:
            st.metric("📅 Hatırlatmalar", "3 Adet", delta="Bugün")

        # --- AKILLI HATIRLATICI (Smart Reminders) ---
        st.subheader("🔔 Yaklaşan Görevler")
        # Basit bir hatırlatıcı demosu
        with st.expander("Hatırlatıcıları Göster", expanded=True):
            st.info("📞 Ahmet Bey (Yatırımcı) aranacak - Bugün 14:00")
            st.warning("🔑 Atakum 3+1 Daire anahtarı teslim alınacak - Yarın")

        # Hızlı Butonlar
        c1, c2 = st.columns(2)
        with c1:
            st.button("➕ Hızlı İlan Ekle", on_click=sayfa_degistir, args=("🏠 Portföy Yönetimi",), use_container_width=True)
        with c2:
            st.button("🔍 Eşleşme Bul", on_click=sayfa_degistir, args=("🤖 Akıllı Eşleşme",), use_container_width=True)

    # --- SAYFA 2: PORTFÖY YÖNETİMİ (SİLME ÖZELLİKLİ) ---
    elif menu == "🏠 Portföy Yönetimi":
        st.title("Portföy İşlemleri")
        
        tab1, tab2, tab3 = st.tabs(["📋 Liste & Galeri", "➕ Yeni Ekle", "🗑️ İlan Sil"])
        
        with tab1:
            data_p, _ = get_google_sheet_data("Portfoy")
            if data_p:
                df = pd.DataFrame(data_p)
                
                # Fotoğraf Galerisi Modu
                galeri_modu = st.toggle("Galeri Görünümü Aç 🖼️")
                
                if galeri_modu:
                    cols = st.columns(3)
                    for index, row in df.iterrows():
                        with cols[index % 3]:
                            # Eğer görsel linki yoksa placeholder koy
                            img_link = row['Gorsel'] if str(row['Gorsel']).startswith('http') else "https://via.placeholder.com/300x200?text=Gorsel+Yok"
                            st.image(img_link, use_container_width=True)
                            st.subheader(f"{row['Fiyat']:,} ₺")
                            st.caption(f"{row['Baslik']} - {row['Konum']}")
                else:
                    # Klasik Liste
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("Portföy boş.")

        with tab2:
            with st.form("yeni_ilan"):
                c1, c2 = st.columns(2)
                with c1:
                    baslik = st.text_input("Başlık")
                    tip = st.selectbox("Tip", ["Daire", "Villa", "Arsa", "Ticari"])
                    fiyat = st.number_input("Fiyat", min_value=0)
                    konum = st.text_input("Konum (Mahalle)")
                    gorsel = st.text_input("Görsel Linki (URL)")
                with c2:
                    m2 = st.number_input("M2", min_value=0)
                    oda = st.selectbox("Oda", ["1+1", "2+1", "3+1", "4+1", "Diğer"])
                    durum = st.selectbox("Durum", ["Satılık", "Kiralık"])
                    col_lat, col_lon = st.columns(2)
                    enlem = col_lat.number_input("Enlem (Lat)", format="%.6f", value=41.28667)
                    boylam = col_lon.number_input("Boylam (Lon)", format="%.6f", value=36.33)

                if st.form_submit_button("Kaydet"):
                    tarih = datetime.now().strftime("%Y-%m-%d")
                    # DİKKAT: Sheets sırasıyla aynı olmalı
                    new_data = [tarih, baslik, tip, fiyat, konum, m2, oda, durum, gorsel, enlem, boylam]
                    _, sheet = get_google_sheet_data("Portfoy")
                    add_row_to_sheet(sheet, new_data)

        with tab3:
            st.error("DİKKAT: Bu işlem geri alınamaz!")
            data_p, sheet_p = get_google_sheet_data("Portfoy")
            if data_p:
                df_del = pd.DataFrame(data_p)
                # Selectbox ile silinecek ilanı seçtiriyoruz
                silinecek_baslik = st.selectbox("Silinecek İlanı Seçin:", df_del['Baslik'].tolist())
                
                if st.button("Seçili İlanı Veritabanından Sil 🗑️"):
                    delete_row_from_sheet(sheet_p, silinecek_baslik)

    # --- SAYFA 3: HARİTA & ANALİZ ---
    elif menu == "🗺️ Harita & Analiz":
        st.title("Lokasyon ve Piyasa Analizi")
        
        col_map, col_analiz = st.columns([2, 1])
        
        with col_map:
            st.subheader("📍 Portföy Haritası")
            data_p, _ = get_google_sheet_data("Portfoy")
            if data_p:
                df_map = pd.DataFrame(data_p)
                # Enlem ve Boylam sütunlarını sayıya çevirmeyi dene
                try:
                    df_map['lat'] = pd.to_numeric(df_map['Enlem'])
                    df_map['lon'] = pd.to_numeric(df_map['Boylam'])
                    st.map(df_map, zoom=12)
                except:
                    st.warning("Harita verisi için Enlem/Boylam sütunlarını kontrol edin.")
            else:
                st.write("Veri yok.")

        with col_analiz:
            st.subheader("📉 Rakip Analizi (Manuel)")
            st.info("Sahibinden.com verilerini otomatik çekmek yasal kısıtlamalara tabidir. Burayı kendi pazar notlarınız için kullanabilirsiniz.")
            
            bolge = st.selectbox("Bölge Seç", ["Atakum", "İlkadım", "Canik"])
            ort_fiyat = st.number_input("Piyasa Ort. Fiyat (m2)", value=25000)
            benim_fiyat = st.number_input("Benim Ort. Fiyatım", value=23000)
            
            fark = ((benim_fiyat - ort_fiyat) / ort_fiyat) * 100
            
            if fark < 0:
                st.success(f"Piyasadan %{abs(fark):.1f} daha UCUZSUNUZ! 🔥")
            else:
                st.error(f"Piyasadan %{fark:.1f} daha PAHALISINIZ!")

    # --- SAYFA 4: AKILLI EŞLEŞME (MATCHMAKER) ---
    elif menu == "🤖 Akıllı Eşleşme":
        st.title("Smart Matchmaker ⚡")
        st.markdown("Hangi müşterinize hangi ev uygun?")
        
        data_p, _ = get_google_sheet_data("Portfoy")
        data_m, _ = get_google_sheet_data("Musteriler")
        
        if data_p and data_m:
            df_p = pd.DataFrame(data_p)
            df_m = pd.DataFrame(data_m)
            
            # Eşleştirme Algoritması
            musteri_sec = st.selectbox("Müşteri Seçin:", df_m['Ad_Soyad'])
            
            # Seçilen müşterinin bilgilerini bul
            secilen_m = df_m[df_m['Ad_Soyad'] == musteri_sec].iloc[0]
            talep = secilen_m['Talep'] # Örn: "Satılık Daire"
            
            st.write(f"**{musteri_sec}** için aranan kriter: `{talep}`")
            st.divider()
            
            # Basit bir filtreleme (Talep tipine göre portföyde ara)
            # Not: Daha zeki olması için müşteri bütçesi ile ilan fiyatını kıyaslayabiliriz.
            
            uygun_ilanlar = pd.DataFrame()
            
            if "Satılık" in talep:
                uygun_ilanlar = df_p[df_p['Durum'] == 'Satılık']
            elif "Kiralık" in talep:
                uygun_ilanlar = df_p[df_p['Durum'] == 'Kiralık']
            
            if not uygun_ilanlar.empty:
                st.success(f"🎉 {len(uygun_ilanlar)} Adet Uygun İlan Bulundu!")
                st.dataframe(uygun_ilanlar[['Baslik', 'Fiyat', 'Konum', 'Oda']], use_container_width=True)
            else:
                st.warning("Şu an uygun ilan yok.")
        else:
            st.error("Yeterli veri yok.")

    # --- SAYFA 5: MÜŞTERİLER ---
    elif menu == "👥 Müşteriler":
        st.title("Müşteri Veritabanı")
        # Eski müşteri kodu buraya aynen gelebilir veya geliştirilebilir
        data_m, _ = get_google_sheet_data("Musteriler")
        if data_m:
            st.dataframe(pd.DataFrame(data_m), use_container_width=True)

if __name__ == "__main__":
    main()
