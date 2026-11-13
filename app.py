import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ================= KONFIGURASI HALAMAN =================
st.set_page_config(
    page_title="UTS Visualisasi Data - E-Commerce",
    page_icon="🛒",
    layout="wide"
)

# ================= FUNGSI BANTU =================
def format_rupiah_singkat(n):
    if n >= 1_000_000_000:
        return f"Rp {n/1_000_000_000:.2f} M"
    elif n >= 1_000_000:
        return f"Rp {n/1_000_000:.2f} Jt"
    elif n >= 1_000:
        return f"Rp {n/1_000:.2f} Rb"
    else:
        return f"Rp {n:,.0f}"

# ================= LOAD DATA =================
@st.cache_data
def load_data():
    # Path disesuaikan dengan nama file Kaggle di dalam folder dataset
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "dataset", "ecommerce_sales_1000_records.csv")
    
    df = pd.read_csv(file_path, parse_dates=["Date"])
    # Hitung Total Sales (Quantity * Price)
    df["Total_Sales"] = df["Quantity"] * df["Price"]
    return df

df = load_data()

# ================= SIDEBAR FILTER =================
st.sidebar.header("🎛️ Filter Dashboard")

# Filter 1: Rentang Tanggal
min_date = df["Date"].min().date()
max_date = df["Date"].max().date()
date_range = st.sidebar.date_input(
    "📅 Rentang Tanggal",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Filter 2: Kategori Produk
kategori = st.sidebar.multiselect(
    "📦 Pilih Kategori",
    options=sorted(df["Category"].unique()),
    default=sorted(df["Category"].unique())
)

# Filter 3: Kota
kota = st.sidebar.multiselect(
    "📍 Pilih Kota",
    options=sorted(df["City"].unique()),
    default=sorted(df["City"].unique())
)

# Terapkan filter
if len(date_range) == 2:
    start_date, end_date = date_range
    mask = (df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)
    df_filtered = df[mask & df["Category"].isin(kategori) & df["City"].isin(kota)]
else:
    df_filtered = df[df["Category"].isin(kategori) & df["City"].isin(kota)]

# ================= HEADER =================
st.title("🛒 Dashboard Penjualan E-Commerce")
st.markdown("**UTS Visualisasi Data** — Analisis Performa Penjualan Kaggle Dataset")

# ================= KPI CARDS (Minimal 3) =================
st.subheader("📌 Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

total_revenue = df_filtered["Total_Sales"].sum()
total_orders = len(df_filtered)
avg_order_value = df_filtered["Total_Sales"].mean() if total_orders > 0 else 0
total_units = df_filtered["Quantity"].sum()

col1.metric("💰 Total Pendapatan", format_rupiah_singkat(total_revenue))
col2.metric("🧾 Total Pesanan", f"{total_orders:,}")
col3.metric("📈 Rata-rata Pesanan", format_rupiah_singkat(avg_order_value))
col4.metric("📦 Total Unit Terjual", f"{total_units:,}")

st.divider()

# ================= CHART 1 & 2: Bar & Pie =================
col1, col2 = st.columns(2)

with col1:
    # Top 10 Produk berdasarkan Pendapatan
    rev_prod = df_filtered.groupby("Product")["Total_Sales"].sum().reset_index().sort_values("Total_Sales", ascending=False).head(10)
    fig_bar = px.bar(
        rev_prod, x="Total_Sales", y="Product", 
        orientation="h",
        title="Top 10 Produk berdasarkan Pendapatan", 
        text="Total_Sales",
        color="Total_Sales", color_continuous_scale="Blues"
    )
    fig_bar.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    fig_bar.update_layout(yaxis=dict(categoryorder="total ascending"))
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    # Proporsi Pendapatan per Kategori
    rev_cat = df_filtered.groupby("Category")["Total_Sales"].sum().reset_index()
    fig_pie = px.pie(
        rev_cat, names="Category", values="Total_Sales", 
        title="Proporsi Pendapatan per Kategori",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_pie.update_traces(textinfo="percent+label")
    st.plotly_chart(fig_pie, use_container_width=True)

# ================= CHART 3: Line Chart (Tren Waktu) =================
st.subheader("📈 Tren Penjualan Bulanan")
df_filtered["Bulan"] = df_filtered["Date"].dt.to_period("M").astype(str)
monthly = df_filtered.groupby("Bulan")["Total_Sales"].sum().reset_index()

fig_line = px.line(
    monthly, x="Bulan", y="Total_Sales", 
    title="Total Pendapatan Bulanan", 
    markers=True
)
fig_line.update_traces(line_color='#636EFA', line_width=3)
fig_line.update_layout(hovermode="x unified")
st.plotly_chart(fig_line, use_container_width=True)

# ================= CHART 4: Scatter Plot (Korelasi) =================
st.subheader("🔍 Hubungan Kuantitas dan Harga")
fig_scatter = px.scatter(
    df_filtered, x="Quantity", y="Price", 
    color="Category", size="Total_Sales",
    title="Sebaran Quantity vs Price (Ukuran = Total Sales)",
    hover_data=["Product", "City"],
    opacity=0.7
)
st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# ================= STORYTELLING / INSIGHT UTAMA =================
st.subheader("💡 Insight Utama (Storytelling)")

if total_revenue > 0:
    top_prod = rev_prod.iloc[0]["Product"] if not rev_prod.empty else "-"
    top_cat = rev_cat.sort_values("Total_Sales", ascending=False).iloc[0]["Category"] if not rev_cat.empty else "-"
    top_city = df_filtered.groupby("City")["Total_Sales"].sum().sort_values(ascending=False).head(1)
    city_name = top_city.index[0] if not top_city.empty else "-"
    
    st.markdown(f"""
    Berdasarkan data e-commerce yang difilter, berikut adalah temuan utamanya:
    
    1. **Kategori Paling Cuan:** Kategori **{top_cat}** menjadi penyumbang pendapatan terbesar pada periode ini.
    2. **Produk Terlaris:** **{top_prod}** adalah produk dengan pendapatan tertinggi.
    3. **Pasar Utama:** Kota **{city_name}** menjadi penyumbang pendapatan terbesar secara keseluruhan.
    4. **Perilaku Pembeli:** Terlihat dari Scatter Plot bahwa produk dengan harga tinggi (seperti Laptop) cenderung dibeli dalam kuantitas yang sedikit, sedangkan produk murah (seperti Buku) sering dibeli dalam jumlah banyak.
    """)
else:
    st.warning("Tidak ada data yang sesuai dengan filter yang dipilih.")

# ================= DATA TABLE =================
with st.expander("📋 Lihat Tabel Data Transaksi (Filtered)"):
    st.dataframe(df_filtered.sort_values("Date", ascending=False), use_container_width=True)
    
    # Download button
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download Data (CSV)", csv, "ecommerce_filtered.csv", "text/csv")
