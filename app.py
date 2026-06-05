# ============================================================================
# PROYEK SERTIFIKASI DATA ANALYST BNSP - MODUL 6: DASHBOARD BI INTERAKTIF
# LENGKAP & UTUH (SUDAH FIXED IMPORT SCIPY T-TEST)
# ============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from scipy.stats import ttest_ind # impor fungsi uji t-test biar gak nameerror

# 1. atur konfigurasi dasar halaman web dashboard bawaan streamlit
st.set_page_config(
    page_title="Dashboard Analisis Perilaku Belajar & Kesejahteraan Mahasiswa",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. seting palet warna charts standar yang kontras, bersih, dan profesional
CHART_PALETTE = ['#2563EB', '#7C3AED', '#06B6D4', '#16A34A', '#EA580C', '#DC2626']
BURNOUT_COLORS = {'Low': '#22C55E', 'Medium': '#EAB308', 'High': '#EF4444'}
POLICY_COLORS = {'Actively_Encouraged': '#10B981', 'Allowed_With_Citation': '#3B82F6', 'Strict_Ban': '#EF4444'}
SEGMENT_COLORS = {'Light User (0-5j)': '#22C55E', 'Moderate User (5-15j)': '#EAB308', 'Heavy User (>15j)': '#EF4444'}

# 3. fungsi pembuat layout plotly yang konsisten dan rapi di seluruh tab
def get_plotly_layout(title_text="", height_px=450, show_legend=True):
    """mengembalikan konfigurasi layout plotly yang bersih tanpa background bising"""
    return dict(
        title=dict(text=title_text, font=dict(size=16, color='#1E293B', family='sans-serif')),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='sans-serif', color='#334155', size=12),
        height=height_px,
        margin=dict(l=50, r=30, t=60, b=50),
        showlegend=show_legend,
        legend=dict(bgcolor='rgba(255,255,255,0.8)', font=dict(size=11)),
        xaxis=dict(gridcolor='rgba(226, 232, 240, 0.6)', zerolinecolor='rgba(226, 232, 240, 0.6)'),
        yaxis=dict(gridcolor='rgba(226, 232, 240, 0.6)', zerolinecolor='rgba(226, 232, 240, 0.6)'),
    )

# 4. fungsi load data dengan cache memori agar aplikasi cepat saat filter diubah
@st.cache_data
def load_processed_student_data():
    """memuat file csv hasil cleaning dan melakukan sinkronisasi variabel turunan bisnis"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_target = 'ai_student_impact_dataset_final.csv'
    path_lengkap = os.path.join(script_dir, file_target)
    
    # jika file final rekayasa fitur belum ada, fallback ke file hasil cleaning biasa
    if not os.path.exists(path_lengkap):
        file_target = 'ai_student_clean.csv'
        path_lengkap = os.path.join(script_dir, file_target)
        
    df = pd.read_csv(path_lengkap)

    # validasi rentang nilai logis untuk memastikan konsistensi data (modul 4)
    kategori_tahun_valid = ['Freshman', 'Sophomore', 'Junior', 'Senior', 'Graduate']
    df = df[df['Year_of_Study'].isin(kategori_tahun_valid)]
    df['Pre_Semester_GPA'] = df['Pre_Semester_GPA'].clip(0.0, 4.00)
    df['Post_Semester_GPA'] = df['Post_Semester_GPA'].clip(0.0, 4.00)
    df['Tool_Diversity'] = df['Tool_Diversity'].clip(1, 5)
    df['Skill_Retention_Score'] = df['Skill_Retention_Score'].clip(0.0, 100.0)

    # sinkronisasi ulang tipe data paid subscription
    if df['Paid_Subscription'].dtype == 'object':
        df['Paid_Subscription'] = df['Paid_Subscription'].map({'True': True, 'False': False, True: True, False: False})

    # pembuatan variabel kategori durasi penggunaan ai (modul 5d)
    df['AI_Usage_Segment'] = pd.cut(
        df['Weekly_GenAI_Hours'],
        bins=[-0.01, 5, 15, df['Weekly_GenAI_Hours'].max() + 1],
        labels=['Light User (0-5j)', 'Moderate User (5-15j)', 'Heavy User (>15j)']
    )
    
    # pembuatan variabel segmen dependensi psikologis untuk analisis risiko
    df['AI_Dependency_Segment'] = pd.cut(
        df['Perceived_AI_Dependency'],
        bins=[-0.01, 3, 6, 10.01],
        labels=['Ketergantungan Rendah (1-3)', 'Ketergantungan Sedang (4-6)', 'Ketergantungan Tinggi (7-10)']
    )
    
    # rekayasa fitur pertumbuhan gpa mahasiswa (modul 5a)
    df['GPA_Change'] = df['Post_Semester_GPA'] - df['Pre_Semester_GPA']

    return df

# memuat dataset awal secara global
df_global = load_processed_student_data()

# ============================================================================
# PANEL SIDEBAR KONTROL & MESIN PENAPIS DATA (FILTER ENGINE)
# ============================================================================

# mengekstrak daftar unik dari dataset global untuk parameter penapis
opsi_jurusan = sorted(df_global['Major_Category'].dropna().unique().tolist())
urutan_studi = ['Freshman', 'Sophomore', 'Junior', 'Senior', 'Graduate']
opsi_jenjang = [y for y in urutan_studi if y in df_global['Year_of_Study'].unique()]
opsi_kebijakan = sorted(df_global['Institutional_Policy'].dropna().unique().tolist())

# fungsi callback buat reset filter (solusi anti error session state)
def eksekusi_reset_filter():
    st.session_state.sidebar_jurusan = opsi_jurusan
    st.session_state.sidebar_jenjang = opsi_jenjang
    st.session_state.sidebar_kebijakan = opsi_kebijakan

# inisialisasi awal session state sebelum widget multiselect dimuat
if 'sidebar_jurusan' not in st.session_state:
    st.session_state.sidebar_jurusan = opsi_jurusan
if 'sidebar_jenjang' not in st.session_state:
    st.session_state.sidebar_jenjang = opsi_jenjang
if 'sidebar_kebijakan' not in st.session_state:
    st.session_state.sidebar_kebijakan = opsi_kebijakan

# menyusun komponen penapis data interaktif di area sidebar
with st.sidebar:
    st.header("🎛️ Panel Filter Analisis")
    st.write("Sesuaikan kriteria di bawah ini untuk menyaring ringkasan data:")
    st.markdown("---")
    
    pilihan_jurusan = st.multiselect(
        "1. Pilih Bidang Studi (Major):",
        options=opsi_jurusan,
        key='sidebar_jurusan'
    )
    
    st.markdown("")
    
    pilihan_jenjang = st.multiselect(
        "2. Pilih Jenjang Studi (Year of Study):",
        options=opsi_jenjang,
        key='sidebar_jenjang'
    )
    
    st.markdown("")
    
    pilihan_kebijakan = st.multiselect(
        "3. Pilih Kebijakan Kampus:",
        options=opsi_kebijakan,
        key='sidebar_kebijakan'
    )
    
    st.markdown("")
    
    st.button(
        "🔄 Reset Semua Filter", 
        on_click=eksekusi_reset_filter, 
        use_container_width=True
    )
        
    st.markdown("---")
    
    final_jurusan = pilihan_jurusan if pilihan_jurusan else opsi_jurusan
    final_jenjang = pilihan_jenjang if pilihan_jenjang else opsi_jenjang
    final_kebijakan = pilihan_kebijakan if pilihan_kebijakan else opsi_kebijakan

    df = df_global[
        (df_global['Major_Category'].isin(final_jurusan)) &
        (df_global['Year_of_Study'].isin(final_jenjang)) &
        (df_global['Institutional_Policy'].isin(final_kebijakan))
    ].copy()

    st.info(f"📊 **Data Terfilter:**\n\n**{len(df):,}** dari **{len(df_global):,}** records mahasiswa berhasil disaring.")

if len(df) == 0:
    st.warning("⚠️ Tidak ada data murni yang sesuai dengan kombinasi filter Anda. Harap pilih kembali kriteria pada panel kontrol sidebar.")
    st.stop()
    
# ============================================================================
# KEY PERFORMANCE INDICATORS (KPI) GENERATOR
# ============================================================================

st.subheader("📌 Indikator Kinerja Utama (Key Performance Indicators)")
st.markdown("Berikut adalah ringkasan metrik performa dan kesejahteraan mahasiswa berdasarkan parameter filter aktif:")

total_mhs_filter = len(df)
avg_post_gpa_filter = df['Post_Semester_GPA'].mean()
avg_retention_filter = df['Skill_Retention_Score'].mean()

mhs_high_burnout = len(df[df['Burnout_Risk_Level'] == 'High'])
pct_high_burnout_filter = (mhs_high_burnout / total_mhs_filter) * 100 if total_mhs_filter > 0 else 0.0
avg_ai_hours_filter = df['Weekly_GenAI_Hours'].mean()

avg_pre_gpa_filter = df['Pre_Semester_GPA'].mean()
delta_gpa = avg_post_gpa_filter - avg_pre_gpa_filter

avg_retention_global = df_global['Skill_Retention_Score'].mean()
delta_retention = avg_retention_filter - avg_retention_global

pct_burnout_global = (len(df_global[df_global['Burnout_Risk_Level'] == 'High']) / len(df_global)) * 100
delta_burnout = pct_high_burnout_filter - pct_burnout_global

avg_ai_hours_global = df_global['Weekly_GenAI_Hours'].mean()
delta_ai_hours = avg_ai_hours_filter - avg_ai_hours_global

kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

with kpi_col1:
    st.metric(
        label="👥 Total Mahasiswa",
        value=f"{total_mhs_filter:,} Mhs",
        delta=f"{total_mhs_filter - len(df_global):,} mhs",
        delta_color="off"
    )

with kpi_col2:
    st.metric(
        label="📈 Rata-rata IPK Akhir",
        value=f"{avg_post_gpa_filter:.2f} / 4.00",
        delta=f"{delta_gpa:+.3f} vs IPK Awal",
        delta_color="normal"
    )

with kpi_col3:
    st.metric(
        label="🧠 Retensi Pengetahuan",
        value=f"{avg_retention_filter:.1f}%",
        delta=f"{delta_retention:+.2f}% vs Global",
        delta_color="normal"
    )

with kpi_col4:
    st.metric(
        label="⚠️ High Burnout Risk",
        value=f"{pct_high_burnout_filter:.1f}%",
        delta=f"{delta_burnout:+.2f}% vs Global",
        delta_color="inverse"
    )

with kpi_col5:
    st.metric(
        label="🤖 Rata-rata Jam AI",
        value=f"{avg_ai_hours_filter:.1f} jam/mgg",
        delta=f"{delta_ai_hours:+.2f} jam vs Global",
        delta_color="off"
    )

st.markdown("---")

# ============================================================================
# NAVIGATION TABS & GRAPH GENERATOR (TAB 1 - TAB 6)
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Overview Demografi",
    "🤖 Dampak Performa AI",
    "🧠 Analisis Kesehatan Mental",
    "📖 Eksplorasi Retensi Ilmu",
    "⚠️ Pemetaan Matriks Risiko",
    "⚖️ Inferensi Statistik & Faktor Dominan"
])

# --- TAB 1: OVERVIEW DEMOGRAFI ---
with tab1:
    st.markdown("### 📋 Gambaran Umum Distribusi Sampel Mahasiswa")
    st.write("Analisis makroskopis mengenai sebaran mahasiswa aktif berdasarkan rumpun keilmuan, jenjang tingkat angkatan, serta jenis regulasi penggunaan teknologi digital.")
    
    ov_col1, ov_col2 = st.columns(2)
    
    with ov_col1:
        df_major_counts = df['Major_Category'].value_counts().reset_index()
        df_major_counts.columns = ['Bidang Studi', 'Jumlah Responden']
        
        fig_major = px.bar(
            df_major_counts, x='Bidang Studi', y='Jumlah Responden',
            text='Jumlah Responden', color='Bidang Studi', color_discrete_sequence=CHART_PALETTE
        )
        fig_major.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_major.update_layout(get_plotly_layout("Distribusi Sampel Berdasarkan Rumpun Bidang Studi", height_px=400, show_legend=False))
        st.plotly_chart(fig_major, use_container_width=True)
        
    with ov_col2:
        df_year_counts = df['Year_of_Study'].value_counts().reindex(
            [y for y in urutan_studi if y in df['Year_of_Study'].unique()]
        ).reset_index()
        df_year_counts.columns = ['Jenjang Studi', 'Jumlah']
        
        fig_year = px.bar(
            df_year_counts, x='Jenjang Studi', y='Jumlah',
            text='Jumlah', color='Jenjang Studi', color_discrete_sequence=CHART_PALETTE[2:]
        )
        fig_year.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_year.update_layout(get_plotly_layout("Distribusi Sampel Berdasarkan Jenjang Tingkat Studi", height_px=400, show_legend=False))
        st.plotly_chart(fig_year, use_container_width=True)

    st.markdown("---")
    ov_col3, ov_col4 = st.columns(2)
    
    with ov_col3:
        df_policy_counts = df['Institutional_Policy'].value_counts().reset_index()
        df_policy_counts.columns = ['Kebijakan Kampus', 'Jumlah']
        
        fig_policy = px.pie(
            df_policy_counts, values='Jumlah', names='Kebijakan Kampus',
            color='Kebijakan Kampus', color_discrete_map=POLICY_COLORS, hole=0.45
        )
        fig_policy.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#FFFFFF', width=2)))
        fig_policy.update_layout(get_plotly_layout("Proporsi Struktur Kebijakan Aturan Perguruan Tinggi", height_px=400, show_legend=True))
        st.plotly_chart(fig_policy, use_container_width=True)
        
    with ov_col4:
        df_gpa_major = df.groupby('Major_Category')[['Pre_Semester_GPA', 'Post_Semester_GPA']].mean().reset_index()
        
        fig_gpa_major = go.Figure()
        fig_gpa_major.add_trace(go.Bar(
            name='IPK Awal (Pre)', x=df_gpa_major['Major_Category'], y=df_gpa_major['Pre_Semester_GPA'],
            marker_color='#94A3B8', text=df_gpa_major['Pre_Semester_GPA'].round(2), textposition='outside'
        ))
        fig_gpa_major.add_trace(go.Bar(
            name='IPK Akhir (Post)', x=df_gpa_major['Major_Category'], y=df_gpa_major['Post_Semester_GPA'],
            marker_color='#2563EB', text=df_gpa_major['Post_Semester_GPA'].round(2), textposition='outside'
        ))
        fig_gpa_major.update_layout(get_plotly_layout("Perbandingan Capaian IPK Awal vs IPK Akhir Lintas Bidang Studi", height_px=400), barmode='group')
        fig_gpa_major.update_yaxes(range=[0, 4.5])
        st.plotly_chart(fig_gpa_major, use_container_width=True)

# --- TAB 2: DAMPAK PERFORMA AI ---
with tab2:
    st.markdown("### 🤖 Korelasi Intensitas Waktu Pemanfaatan AI vs Performa Nilai")
    st.write("Eksplorasi mendalam mengenai korelasi durasi penggunaan asisten pintar terhadap prestasi akademik.")
    
    acad_col1, acad_col2 = st.columns(2)
    
    with acad_col1:
        df_seg_stats = df.groupby('AI_Usage_Segment', observed=True).agg(
            Avg_Pre=('Pre_Semester_GPA', 'mean'), Avg_Post=('Post_Semester_GPA', 'mean')
        ).reset_index()
        
        fig_gpa_seg = go.Figure()
        fig_gpa_seg.add_trace(go.Bar(
            name='IPK Awal', x=df_seg_stats['AI_Usage_Segment'].astype(str), y=df_seg_stats['Avg_Pre'],
            marker_color='#94A3B8', text=df_seg_stats['Avg_Pre'].round(2), textposition='outside'
        ))
        fig_gpa_seg.add_trace(go.Bar(
            name='IPK Akhir', x=df_seg_stats['AI_Usage_Segment'].astype(str), y=df_seg_stats['Avg_Post'],
            marker_color='#7C3AED', text=df_seg_stats['Avg_Post'].round(2), textposition='outside'
        ))
        fig_gpa_seg.update_layout(get_plotly_layout("Perubahan Skor IPK Berdasarkan Klaster Durasi Penggunaan AI", height_px=400), barmode='group')
        fig_gpa_seg.update_yaxes(range=[0, 4.5])
        st.plotly_chart(fig_gpa_seg, use_container_width=True)
        
    with acad_col2:
        df_delta_stats = df.groupby('AI_Usage_Segment', observed=True)['GPA_Change'].mean().reset_index()
        
        fig_delta = px.bar(
            df_delta_stats, x='AI_Usage_Segment', y='GPA_Change',
            text=df_delta_stats['GPA_Change'].round(3), color='AI_Usage_Segment',
            color_discrete_sequence=['#22C55E', '#EAB308', '#EF4444']
        )
        fig_delta.update_traces(texttemplate='%{text:+}', textposition='outside')
        fig_delta.update_layout(get_plotly_layout("Rata-rata Pertumbuhan Akselerasi Nilai (Delta IPK) per Segmen AI", height_px=400, show_legend=False))
        st.plotly_chart(fig_delta, use_container_width=True)

    st.markdown("---")
    st.markdown("##### 📈 Sebaran Distribusi Kontinu Durasi Jam AI vs Capaian IPK Akhir")
    
    df_sample_scatter = df.sample(min(5000, len(df)), random_state=42)
    fig_scatter_gpa = px.scatter(
        df_sample_scatter, x='Weekly_GenAI_Hours', y='Post_Semester_GPA',
        color='AI_Usage_Segment', color_discrete_map=SEGMENT_COLORS, opacity=0.4,
        labels={'Weekly_GenAI_Hours': 'Jam AI / Minggu', 'Post_Semester_GPA': 'Post GPA'}
    )
    
    for kst, warna_garis in SEGMENT_COLORS.items():
        sub_data_klaster = df[df['AI_Usage_Segment'] == kst]
        if len(sub_data_klaster) > 10:
            koef_polinomial = np.polyfit(sub_data_klaster['Weekly_GenAI_Hours'], sub_data_klaster['Post_Semester_GPA'], 1)
            fungsi_linear = np.poly1d(koef_polinomial)
            sumbu_x_garis = np.linspace(sub_data_klaster['Weekly_GenAI_Hours'].min(), sub_data_klaster['Weekly_GenAI_Hours'].max(), 50)
            
            fig_scatter_gpa.add_trace(go.Scatter(
                x=sumbu_x_garis, y=fungsi_linear(sumbu_x_garis), mode='lines',
                line=dict(color=warna_garis, width=2, dash='dash'), name=f"Tren Linier {kst}"
            ))
            
    fig_scatter_gpa.update_layout(get_plotly_layout("", height_px=480, show_legend=True))
    st.plotly_chart(fig_scatter_gpa, use_container_width=True)

# --- TAB 3: ANALISIS KESEHATAN MENTAL ---
with tab3:
    st.markdown("### 🧠 Dampak Regulasi Kampus Terhadap Kesehatan Mental Responden")
    st.write("Analisis proporsi tingkat stres kejenuhan (*burnout*) serta tingkat kecemasan ujian berdasarkan variasi kebijakan kampus.")
    
    men_col1, men_col2 = st.columns(2)
    
    with men_col1:
        df_burn_cross = pd.crosstab(df['Institutional_Policy'], df['Burnout_Risk_Level'], normalize='index').reset_index()
        kolom_burn_order = [k for k in ['Low', 'Medium', 'High'] if k in df_burn_cross.columns]
        df_burn_melted = df_burn_cross.melt(id_vars=['Institutional_Policy'], value_vars=kolom_burn_order, var_name='Risiko Burnout', value_name='Proporsi')
        df_burn_melted['Persentase (%)'] = df_burn_melted['Proporsi'] * 100
        
        fig_burn_policy = px.bar(
            df_burn_melted, x='Institutional_Policy', y='Persentase (%)', color='Risiko Burnout',
            color_discrete_map=BURNOUT_COLORS, category_orders={'Risiko Burnout': ['Low', 'Medium', 'High']}
        )
        fig_burn_policy.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
        fig_burn_policy.update_layout(get_plotly_layout("Proporsi Tingkat Risiko Burnout Berdasarkan Kebijakan Kampus", height_px=420), barmode='stack')
        st.plotly_chart(fig_burn_policy, use_container_width=True)
        
    with men_col2:
        fig_anx_box = px.box(
            df, x='Institutional_Policy', y='Anxiety_Level_During_Exams',
            color='Institutional_Policy', color_discrete_map=POLICY_COLORS,
            labels={'Anxiety_Level_During_Exams': 'Skor Kecemasan Ujian (1-10)'}
        )
        fig_anx_box.update_layout(get_plotly_layout("Sebaran Distribusi Skor Kecemasan Ujian Berdasarkan Kebijakan Kampus", height_px=420, show_legend=False))
        st.plotly_chart(fig_anx_box, use_container_width=True)

# --- TAB 4: EKSPLORASI RETENSI ILMU ---
with tab4:
    st.markdown("### 📖 Evaluasi Kualitas Belajar: Penurunan Daya Retensi Ilmu")
    st.write("Menguji risiko degradasi retensi pemahaman materi kuliah akibat tingkat ketergantungan ai.")
    
    ret_col1, ret_col2 = st.columns(2)
    
    with ret_col1:
        df_sample_ret = df.sample(min(3000, len(df)), random_state=42)
        fig_scatter_ret = px.scatter(
            df_sample_ret, x='Perceived_AI_Dependency', y='Skill_Retention_Score',
            color='AI_Usage_Segment', color_discrete_map=SEGMENT_COLORS, opacity=0.35,
            labels={'Perceived_AI_Dependency': 'Skor Dependensi AI', 'Skill_Retention_Score': 'Skor Retensi (%)'}
        )
        koef_ret = np.polyfit(df['Perceived_AI_Dependency'], df['Skill_Retention_Score'], 1)
        fungsi_ret = np.poly1d(koef_ret)
        r_value_ret = df['Perceived_AI_Dependency'].corr(df['Skill_Retention_Score'])
        sumbu_x_ret = np.linspace(df['Perceived_AI_Dependency'].min(), df['Perceived_AI_Dependency'].max(), 50)
        
        fig_scatter_ret.add_trace(go.Scatter(
            x=sumbu_x_ret, y=fungsi_ret(sumbu_x_ret), mode='lines',
            line=dict(color='#DC2626', width=3, dash='dash'), name=f"Tren Linear (r = {r_value_ret:.3f})"
        ))
        fig_scatter_ret.update_layout(get_plotly_layout("Tren Hubungan Skor Ketergantungan AI vs Skor Retensi Ilmu (Sampel 3.000)", height_px=420))
        st.plotly_chart(fig_scatter_ret, use_container_width=True)
        
    with ret_col2:
        df_ret_grouped = df.groupby('Perceived_AI_Dependency')['Skill_Retention_Score'].mean().reset_index()
        
        fig_ret_bar = px.bar(
            df_ret_grouped, x='Perceived_AI_Dependency', y='Skill_Retention_Score',
            color='Skill_Retention_Score', color_continuous_scale='YlOrRd_r', text='Skill_Retention_Score'
        )
        fig_ret_bar.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_ret_bar.update_layout(get_plotly_layout("Rata-rata Skor Retensi Pengetahuan Mahasiswa per Level Dependensi AI", height_px=420, show_legend=False))
        fig_ret_bar.update_coloraxes(showscale=False)
        fig_ret_bar.update_yaxes(range=[0, 105])
        st.plotly_chart(fig_ret_bar, use_container_width=True)

# --- TAB 5: PEMETAAN MATRIKS RISIKO ---
with tab5:
    st.markdown("### ⚠️ Pemetaan Matriks Risiko Kerentanan Mahasiswa")
    st.write("Identifikasi dini kelompok responden yang berada dalam zona bahaya akademik akibat kombinasi dependensi ekstrem dan burnout tinggi.")
    
    df_matrix = pd.crosstab(df['AI_Dependency_Segment'], df['Burnout_Risk_Level'])
    order_dep = ['Ketergantungan Rendah (1-3)', 'Ketergantungan Sedang (4-6)', 'Ketergantungan Tinggi (7-10)']
    order_burn = ['Low', 'Medium', 'High']
    df_matrix = df_matrix.reindex(index=order_dep, columns=order_burn).fillna(0).astype(int)
    
    risk_col1, risk_col2 = st.columns([3, 2])
    
    with risk_col1:
        fig_heatmap_risk = px.imshow(
            df_matrix, text_auto=True, color_continuous_scale=['#16A34A', '#CA8A04', '#DC2626'],
            labels=dict(x="Tingkat Risiko Burnout", y="Segmen Ketergantungan AI", color="Jumlah Responden")
        )
        fig_heatmap_risk.update_layout(get_plotly_layout("Matriks Silang Volume Jiwa Responden: Dependensi AI × Burnout Risk", height_px=400, show_legend=False))
        st.plotly_chart(fig_heatmap_risk, use_container_width=True)
        
    with risk_col2:
        df_high_danger = df[(df['Perceived_AI_Dependency'] >= 7) & (df['Burnout_Risk_Level'] == 'High')]
        total_danger_jiwa = len(df_high_danger)
        persen_danger_total = (total_danger_jiwa / len(df)) * 100 if len(df) > 0 else 0.0
        
        st.markdown("##### 🔴 Profil Mahasiswa Kelompok Rentan (Zona Bahaya)")
        st.markdown(f"Terdapat sebanyak **{total_danger_jiwa:,} jiwa** ({persen_danger_total:.1f}% dari data filter) mahasiswa yang tergolong dalam kondisi kritis.")
        
        if total_danger_jiwa > 0:
            st.metric(label="Rata-rata Skor Kecemasan Ujian Kelompok Kritis", value=f"{df_high_danger['Anxiety_Level_During_Exams'].mean():.1f} / 10")
            st.metric(label="Rata-rata Skor Retensi Pengetahuan Kelompok Kritis", value=f"{df_high_danger['Skill_Retention_Score'].mean():.1f}%")
            st.metric(label="Capaian Rata-rata IPK Akhir Kelompok Kritis", value=f"{df_high_danger['Post_Semester_GPA'].mean():.2f}")
        else:
            st.info("Tidak ditemukan catatan mahasiswa dalam zona kritis untuk filter aktif saat ini.")

# --- TAB 6: INFERENSI STATISTIK & FAKTOR DOMINAN ---
with tab6:
    st.markdown("### ⚖️ Analisis Inferensi Pengujian Hipotesis & Faktor Dominan")
    st.write("Bagian ini menyajikan pembuktian ilmiah untuk menguji isu kesetaraan akses digital (akun premium vs gratis) serta memetakan faktor perilaku belajar yang paling memengaruhi keberhasilan studi.")
    
    df_paid = df[df['Paid_Subscription'] == True]
    df_free = df[df['Paid_Subscription'] == False]
    
    st.markdown("##### 1. Hasil Pengujian Hipotesis Komparatif Digital Divide (Independent Two-Sample T-Test)")
    
    if len(df_paid) > 1 and len(df_free) > 1:
        t_stat_gpa, p_val_gpa = ttest_ind(df_paid['Post_Semester_GPA'].dropna(), df_free['Post_Semester_GPA'].dropna())
        t_stat_ret, p_val_ret = ttest_ind(df_paid['Skill_Retention_Score'].dropna(), df_free['Skill_Retention_Score'].dropna())
        
        col_ttest1, col_ttest2 = st.columns(2)
        
        with col_ttest1:
            st.markdown("**Parameter Evaluasi: Indeks Prestasi Kumulatif Akhir (Post-GPA)**")
            st.write(f"* Nilai T-Statistic : `{t_stat_gpa:.4f}`")
            st.write(f"* Nilai P-Value : `{p_val_gpa:.4f}`")
            
            if p_val_gpa < 0.05:
                st.error("🔬 **Kesimpulan:** Signifikan (p < 0.05). Akses finansial platform premium memberikan perbedaan performa akademik yang nyata.")
            else:
                st.info("🔬 **Kesimpulan:** Tidak Signifikan (p >= 0.05). Kesenjangan finansial tidak menciptakan perbedaan performa akademik yang nyata.")
                
        with col_ttest2:
            st.markdown("**Parameter Evaluasi: Skor Retensi Pengetahuan (Skill Retention)**")
            st.write(f"* Nilai T-Statistic : `{t_stat_ret:.4f}`")
            st.write(f"* Nilai P-Value : `{p_val_ret:.4f}`")
            
            if p_val_ret < 0.05:
                st.error("🔬 **Kesimpulan:** Signifikan (p < 0.05). Akses finansial platform premium memberikan perbedaan daya retensi pengetahuan yang nyata.")
            else:
                st.info("🔬 **Kesimpulan:** Tidak Signifikan (p >= 0.05). Kesenjangan finansial tidak menciptakan perbedaan daya retensi pengetahuan yang nyata.")
    else:
        st.warning("Jumlah sampel data terfilter tidak mencukupi untuk melakukan uji t-test.")
        
    st.markdown("---")
    
    st.markdown("##### 2. Peringkat Faktor Dominan Penentu Keberhasilan Akademik Mahasiswa (PB-07)")
    st.write("Grafik di bawah mengurutkan nilai koefisien korelasi Pearson (r) seluruh peubah perilaku belajar terhadap variabel target utama (IPK Akhir Semester):")
    
    kolom_analisis_dominan = [
        'Pre_Semester_GPA', 'Weekly_GenAI_Hours', 'Traditional_Study_Hours', 
        'Tool_Diversity', 'Perceived_AI_Dependency', 'Anxiety_Level_During_Exams', 
        'Skill_Retention_Score'
    ]
    
    matriks_target_corr = df[kolom_analisis_dominan].corrwith(df['Post_Semester_GPA']).sort_values()
    
    df_corr_ranking = pd.DataFrame({
        'Indikator Perilaku': matriks_target_corr.index,
        'Koefisien Korelasi Pearson (r)': matriks_target_corr.values
    })
    
    kamus_label_indo = {
        'Pre_Semester_GPA': 'IPK Awal Semester (Pre-GPA)',
        'Weekly_GenAI_Hours': 'Durasi Jam Penggunaan AI Mingguan',
        'Traditional_Study_Hours': 'Alokasi Jam Belajar Tradisional',
        'Tool_Diversity': 'Ragam Keberagaman Perangkat AI',
        'Perceived_AI_Dependency': 'Tingkat Ketergantungan Psikologis AI',
        'Anxiety_Level_During_Exams': 'Tingkat Kecemasan Menghadapi Ujian',
        'Skill_Retention_Score': 'Skor Daya Retensi Pengetahuan'
    }
    df_corr_ranking['Indikator Perilaku'] = df_corr_ranking['Indikator Perilaku'].map(kamus_label_indo)
    
    fig_dominan_bar = px.bar(
        df_corr_ranking, x='Koefisien Korelasi Pearson (r)', y='Indikator Perilaku',
        orientation='h', text='Koefisien Korelasi Pearson (r)', color='Koefisien Korelasi Pearson (r)',
        color_continuous_scale='RdBu', range_color=[-1, 1]
    )
    fig_dominan_bar.update_traces(texttemplate='%{text:.3f}', textposition='outside')
    fig_dominan_bar.update_layout(get_plotly_layout("", height_px=400, show_legend=False))
    fig_dominan_bar.update_coloraxes(showscale=False)
    st.plotly_chart(fig_dominan_bar, use_container_width=True)
    
    fitur_paling_positif = matriks_target_corr.idxmax()
    st.success(f"💡 **Insight Konklusi Kebijakan:** Indikator tunggal yang bertindak sebagai faktor prediktor paling dominan memengaruhi keberhasilan nilai akademik mahasiswa secara positif adalah **{kamus_label_indo[fitur_paling_positif]}** dengan nilai koefisien korelasi mencapai **r = {matriks_target_corr[fitur_paling_positif]:+.3f}**.")

# ============================================================================
# BAGIAN BAWAH DASHBOARD: CONTAINER EKSPLORASI DATA MENTAH BERSIH & FITUR UNDUH
# ============================================================================
st.markdown("---")
st.subheader("📋 Pencarian & Eksplorasi Data Mentah Bersih")
st.write("Gunakan tabel di bawah ini untuk melihat rekaman data individual secara mendetail atau mengekstrak hasil saringan filter:")

st.dataframe(df, use_container_width=True)

csv_buffer = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Unduh Data Terfilter (.CSV)",
    data=csv_buffer,
    file_name="data_mahasiswa_terfilter_clean.csv",
    mime="text/csv",
    use_container_width=False
)

st.markdown("<br><div style='text-align: center; color: gray; font-size: 0.8rem;'>Dashboard Sertifikasi BNSP Data Analyst — 2026</div>", unsafe_allow_html=True)