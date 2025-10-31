import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import re
import io
from datetime import datetime

# === OCR CONFIG ===
OCR_API_KEY = "K84058354088957"  # 👈 BURAYA KENDİ KEY'İNİ YAZ (https://ocr.space/ocrapi)

# === PAGE CONFIG ===
st.set_page_config(page_title="Yakıt Takip v9 - Cloud OCR", page_icon="⛽", layout="wide")

st.title("⛽ Yakıt Takip Sistemi v9 - Cloud OCR Edition")
st.markdown("Fişten otomatik okuma ve manuel giriş sistemi")

DATA_FILE = "yakit_kayitlari.csv"

# === LOAD OR CREATE DATA ===
try:
    df = pd.read_csv(DATA_FILE)
except FileNotFoundError:
    df = pd.DataFrame(columns=["Tarih", "Alınan Litre", "Toplam_Tutar(₺)", "Litre_Fiyatı(₺)", "Km_Sayacı"])

# === SEKMELER ===
tab1, tab2, tab3 = st.tabs(["🧾 Kayıt Ekle", "📷 Fişten Oku (OCR)", "📊 Analiz"])

# ------------------------------------------------------------------------
# 🧾 1️⃣ MANUEL KAYIT EKLEME
with tab1:
    st.subheader("Yeni Yakıt Kaydı Ekle")

    tarih = st.date_input("Tarih", datetime.today())
    litre = st.number_input("Alınan Litre", min_value=0.0, step=0.01)
    tutar = st.number_input("Toplam Tutar (₺)", min_value=0.0, step=0.01)
    fiyat = st.number_input("Litre Fiyatı (₺)", min_value=0.0, step=0.01)
    km = st.number_input("Km Sayacı", min_value=0, step=1)

    if st.button("💾 Kaydı Ekle"):
        yeni = pd.DataFrame(
            [[tarih, litre, tutar, fiyat, km]],
            columns=df.columns
        )
        df = pd.concat([df, yeni], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success("✅ Yakıt kaydı eklendi!")

# ------------------------------------------------------------------------
# 📷 2️⃣ OCR İLE FİŞTEN OKUMA
with tab2:
    st.subheader("📷 Yakıt Fişinden Bilgi Oku")

    uploaded_file = st.file_uploader("Yakıt fişini yükle (.jpg, .png)", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        st.info("⏳ Fiş işleniyor, lütfen bekleyin...")

        response = requests.post(
            "https://api.ocr.space/parse/image",
            files={"filename": uploaded_file.getvalue()},
            data={"apikey": OCR_API_KEY, "language": "tur"}
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("ParsedResults"):
                text = data["ParsedResults"][0]["ParsedText"]
                st.text_area("🧾 Okunan Fiş Metni", text, height=200)

                tarih = re.search(r"\d{2}[./-]\d{2}[./-]\d{4}", text)
                tutar = re.search(r"(\d+[.,]\d+)\s*TL", text)
                litre = re.search(r"(\d+[.,]\d+)\s*(L|Lt|Litre)", text)
                fiyat = re.search(r"(\d+[.,]\d+)\s*(TL\/L|TL\/Lt|TL/Litre)", text)

                tarih_val = tarih.group(0) if tarih else "-"
                litre_val = litre.group(1).replace(",", ".") if litre else "-"
                tutar_val = tutar.group(1).replace(",", ".") if tutar else "-"
                fiyat_val = fiyat.group(1).replace(",", ".") if fiyat else "-"

                st.write("📅 Tarih:", tarih_val)
                st.write("⛽ Litre:", litre_val)
                st.write("💸 Tutar:", tutar_val)
                st.write("💰 Litre Fiyatı:", fiyat_val)

                if st.button("💾 Bu Verileri Kaydet"):
                    if tarih_val != "-" and tutar_val != "-" and litre_val != "-":
                        yeni = pd.DataFrame(
                            [[tarih_val, float(litre_val), float(tutar_val), float(fiyat_val) if fiyat_val != "-" else 0, 0]],
                            columns=df.columns
                        )
                        df = pd.concat([df, yeni], ignore_index=True)
                        df.to_csv(DATA_FILE, index=False)
                        st.success("✅ OCR'dan alınan fiş kaydedildi!")
                    else:
                        st.warning("Eksik veri tespit edildi, lütfen kontrol et.")
            else:
                st.error("Fiş okunamadı. Görsel net değilse tekrar deneyebilirsin.")
        else:
            st.error("OCR servisine bağlanılamadı. API Key geçerli mi kontrol et!")

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# 📊 3️⃣ ANALİZ
with tab3:
    st.subheader("📊 Yakıt Analizi")

    if df.empty:
        st.info("Henüz veri yok.")
    else:
        st.dataframe(df)

        df["Tarih"] = pd.to_datetime(df["Tarih"], errors="coerce")
        df = df.sort_values("Tarih")

        # 100 km'de tüketim ve km başına maliyet hesaplama
        df["Tuketim_L_100km"] = (
            df["Alınan Litre"] / (df["Km_Sayacı"].diff().fillna(0) / 100)
        ).replace([float("inf"), -float("inf")], 0)

        df["Km_Basi_Maliyet_TL_km"] = (
            df["Toplam_Tutar(₺)"] / df["Km_Sayacı"].diff().fillna(1)
        ).replace([float("inf"), -float("inf")], 0)

        col1, col2 = st.columns(2)
        col1.metric("💧 Ortalama Tüketim (L/100km)", f"{df['Tuketim_L_100km'].mean():.2f}")
        col2.metric("💸 Ortalama Maliyet (₺/km)", f"{df['Km_Basi_Maliyet_TL_km'].mean():.2f}")

        st.line_chart(
            df.set_index("Tarih")[["Tuketim_L_100km", "Km_Basi_Maliyet_TL_km"]]
        )
