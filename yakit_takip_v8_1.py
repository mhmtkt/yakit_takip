import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

DOSYA = "yakit_kayitlari.csv"

# ---------- SAYFA AYARLARI ----------
st.set_page_config(page_title="Yakıt Takip Sistemi v8.1", layout="wide")
st.markdown("<h1 style='text-align:center;color:#00BFFF;'>🚗 Yakıt Takip Sistemi v8.1 – Final Edition</h1>", unsafe_allow_html=True)
st.write("")

# ---------- VERİ YÜKLEME ----------
try:
    df = pd.read_csv(DOSYA)
except FileNotFoundError:
    df = pd.DataFrame(columns=["Tarih", "Kilometre", "Alinan_Yakit(L)", "Litre_Fiyati(₺)", "Toplam_Tutar(₺)", "Dolum_Türü"])
    df.to_csv(DOSYA, index=False)

# ---------- SEKMELER ----------
tab1, tab2, tab3 = st.tabs(["🧾 Veri Girişi", "📊 Analiz", "📈 Raporlar"])

# ===========================================================
# 🧾 1️⃣ VERİ GİRİŞİ SEKME
# ===========================================================
with tab1:
    st.markdown("### 💡 Yeni Yakıt Kaydı Ekle")
    col1, col2, col3 = st.columns(3)
    with col1:
        tarih = st.date_input("Tarih", datetime.now())
        km = st.number_input("Kilometre", min_value=0.0, step=1.0)
    with col2:
        yakit = st.number_input("Alınan Yakıt (L)", min_value=0.0, step=0.1)
        fiyat = st.number_input("Litre Fiyatı (₺)", min_value=0.0, step=0.01)
    with col3:
        dolum_turu = st.selectbox("Dolum Türü", ["Full (Depo Tam Doldu)", "Kısmi (Az Dolum)"])
        ekle = st.button("✅ Kaydı Ekle", use_container_width=True)

    if ekle:
        tutar = yakit * fiyat
        yeni = pd.DataFrame([[tarih, km, yakit, fiyat, tutar, dolum_turu]], columns=df.columns)
        df = pd.concat([df, yeni], ignore_index=True)
        df.to_csv(DOSYA, index=False)
        st.success("Yeni kayıt eklendi ✅")

    st.markdown("---")
    st.markdown("### 🗑️ Kayıt Silme")
    if not df.empty:
        silinecek = st.selectbox("Silinecek Kaydı Seç (Tarih - KM)", df.apply(lambda x: f"{x['Tarih']} - {x['Kilometre']} km", axis=1))
        if st.button("Sil", type="primary"):
            index = df[df.apply(lambda x: f"{x['Tarih']} - {x['Kilometre']} km", axis=1) == silinecek].index
            df.drop(index, inplace=True)
            df.to_csv(DOSYA, index=False)
            st.warning("Kayıt silindi 🗑️")
    else:
        st.info("Henüz kayıt yok kanka.")

    st.markdown("---")
    st.markdown("### 📋 Kayıtlı Veriler")
    st.dataframe(df, use_container_width=True, height=350)

# ===========================================================
# 📊 2️⃣ ANALİZ SEKME
# ===========================================================
with tab2:
    st.markdown("### 📊 Yakıt Tüketim Analizi")
    if len(df[df["Dolum_Türü"].str.contains("Full")]) >= 2:
        df = df.sort_values("Kilometre").reset_index(drop=True)
        donemler = []
        last_full_index = None

        for i in range(len(df)):
            if "Full" in df.loc[i, "Dolum_Türü"]:
                if last_full_index is not None:
                    onceki = df.loc[last_full_index]
                    simdiki = df.loc[i]
                    ara_kayitlar = df.loc[last_full_index + 1:i - 1]
                    ekstra_yakit = ara_kayitlar["Alinan_Yakit(L)"].sum() if not ara_kayitlar.empty else 0

                    yol = simdiki["Kilometre"] - onceki["Kilometre"]
                    harcanan_yakit = simdiki["Alinan_Yakit(L)"] + ekstra_yakit
                    maliyet = harcanan_yakit * onceki["Litre_Fiyati(₺)"]

                    if yol > 0:
                        l100 = (harcanan_yakit / yol) * 100
                        tl_km = maliyet / yol
                        donemler.append({
                            "Dönem": f"{onceki['Tarih']} ➜ {simdiki['Tarih']}",
                            "Yol (km)": yol,
                            "Harcanan Yakıt (L)": round(harcanan_yakit, 2),
                            "100 km'de Tüketim (L)": round(l100, 2),
                            "Km Başına Maliyet (₺)": round(tl_km, 2)
                        })
                last_full_index = i

        sonuc_df = pd.DataFrame(donemler)

        col1, col2 = st.columns(2)
        col1.metric("💧 Ortalama Tüketim (L/100km)", "{:.2f}".format(sonuc_df["100 km'de Tüketim (L)"].mean()))
        col2.metric("💸 Ortalama Maliyet (₺/km)", "{:.2f}".format(sonuc_df["Km Başına Maliyet (₺)"].mean()))

        st.markdown("---")
        col3, col4 = st.columns(2)

        with col3:
            fig_tuketim = px.area(
                sonuc_df, x="Dönem", y="100 km'de Tüketim (L)",
                title="💧 100 km Başına Yakıt Tüketimi", color_discrete_sequence=["#00BFFF"])
            st.plotly_chart(fig_tuketim, use_container_width=True)

        with col4:
            fig_maliyet = px.area(
                sonuc_df, x="Dönem", y="Km Başına Maliyet (₺)",
                title="💸 Km Başına Maliyet", color_discrete_sequence=["#FF8C00"])
            st.plotly_chart(fig_maliyet, use_container_width=True)

        st.markdown("### 📋 Dönemsel Veriler")
        st.dataframe(sonuc_df, use_container_width=True)

    else:
        st.info("Analiz için en az iki 'Full' dolum gerekli kanka.")

# ===========================================================
# 📈 3️⃣ RAPORLAR SEKME
# ===========================================================
with tab3:
    st.markdown("### 🗓️ Aylık Yakıt Raporu")
    if not df.empty:
        df["Tarih"] = pd.to_datetime(df["Tarih"])
        df["Ay"] = df["Tarih"].dt.strftime("%Y-%m")
        df["Gidilen_Km"] = df["Kilometre"].diff().fillna(0)

        aylik = df.groupby("Ay").agg({
            "Alinan_Yakit(L)": "sum",
            "Toplam_Tutar(₺)": "sum",
            "Gidilen_Km": "sum"
        }).rename(columns={
            "Alinan_Yakit(L)": "Toplam Yakıt (L)",
            "Toplam_Tutar(₺)": "Toplam Tutar (₺)",
            "Gidilen_Km": "Toplam KM"
        })

        aylik["Ort. Tüketim (L/100km)"] = (aylik["Toplam Yakıt (L)"] / aylik["Toplam KM"]) * 100
        aylik["Ort. Maliyet (₺/km)"] = aylik["Toplam Tutar (₺)"] / aylik["Toplam KM"]

        st.dataframe(aylik.style.format({
            "Toplam Yakıt (L)": "{:.2f}",
            "Toplam Tutar (₺)": "{:.2f}",
            "Toplam KM": "{:.0f}",
            "Ort. Tüketim (L/100km)": "{:.2f}",
            "Ort. Maliyet (₺/km)": "{:.2f}"
        }), use_container_width=True)

        st.markdown("---")
        st.markdown("### ♾️ Ömür Boyu Toplam Veriler (İlk Dolum Hariç)")
        if len(df) > 1:
            df_calc = df.iloc[1:].copy()
            toplam_km = df["Kilometre"].max() - df["Kilometre"].iloc[0]
            toplam_yakit = df_calc["Alinan_Yakit(L)"].sum()
            toplam_tutar = df_calc["Toplam_Tutar(₺)"].sum()
            ort_tuketim = (toplam_yakit / toplam_km) * 100 if toplam_km > 0 else 0
            ort_maliyet = toplam_tutar / toplam_km if toplam_km > 0 else 0

            toplam_df = pd.DataFrame({
                "Toplam KM": [round(toplam_km, 0)],
                "Toplam Yakıt (L)": [round(toplam_yakit, 2)],
                "Toplam Tutar (₺)": [round(toplam_tutar, 2)],
                "Ort. Tüketim (L/100km)": [round(ort_tuketim, 2)],
                "Ort. Maliyet (₺/km)": [round(ort_maliyet, 2)]
            })
            st.dataframe(toplam_df, use_container_width=True)
        else:
            st.info("Toplam veriler için yeterli kayıt yok.")
    else:
        st.info("Henüz veri bulunmuyor.")
