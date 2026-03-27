import streamlit as st
import io
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="PRmarcenaria Tech", layout="wide")

# --- LAYOUT INDUSTRIAL LIGHT (CSS PREMIUM) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    
    .stApp {
        background-color: #f8f9fa;
        color: #1a1c1e;
        font-family: 'Inter', sans-serif;
    }
    
    .main-title {
        background-color: #ffffff;
        color: #003366;
        padding: 25px;
        border-bottom: 5px solid #ff6600;
        border-radius: 10px;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }

    .card-metric {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border-top: 5px solid #003366;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }

    /* Inputs Limpos */
    .stNumberInput input, .stTextInput input, .stSelectbox div {
        background-color: #ffffff !important;
        border: 1px solid #ced4da !important;
        border-radius: 8px !important;
    }
    
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #e9ecef;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='main-title'><h1>📐 PRmarcenaria | Engenharia Pro</h1><p>Sistema de Cálculo e Ordem de Produção Técnica</p></div>", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("📋 Parâmetros de Mercado")
    preco_mdf = st.number_input("Preço da Chapa (R$)", value=285.0)
    preco_fita = st.number_input("Preço Metro Fita (R$)", value=6.0)
    st.divider()
    st.info("Valores usados para compor o custo estimado no PDF.")

# --- ENTRADA DE DADOS ---
tab1, tab2 = st.tabs(["🏗️ Configuração", "📊 Resultados & PDF"])

with tab1:
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.subheader("📍 Projeto")
        nome_proj = st.text_input("Cliente / Obra", "Projeto Exemplo")
        esp = st.selectbox("Espessura MDF (mm)", [6, 15, 18, 25], index=1)
    
    with c2:
        st.subheader("📏 Dimensões (mm)")
        comp = st.number_input("Comprimento Total", value=1200.0)
        larg = st.number_input("Largura Peça", value=600.0)
        alt = st.number_input("Altura Total", value=2100.0)
        prof = st.number_input("Profundidade", value=550.0)

# Lógica de Materiais
def processar_calculos(c, l, a, e, p):
    area_bruta = ((a * p * 2) + (c * p * 2) + (c * a)) / 1_000_000
    chapas = max(1, int(area_bruta / 5.06) + 1)
    fita = ((c + a + p) * 5) / 1000
    p_g = int(area_bruta * 15)
    dob = 4 if a > 1600 else 2
    return {"area": area_bruta, "chapas": chapas, "fita": fita, "p_g": p_g, "dob": dob}

res = processar_calculos(comp, larg, alt, esp, prof)

with tab2:
    # Visualização 3D Técnica
    st.subheader("📦 Perspectiva de Volume")
    ratio_w, ratio_h, ratio_d = comp/2500*300, alt/2500*300, prof/2500*150
    
    box_3d = f"""
    <div style="height: 350px; display: flex; justify-content: center; align-items: center; perspective: 1000px; background: white; border-radius: 15px; border: 1px solid #eee;">
        <div style="width: {ratio_w}px; height: {ratio_h}px; position: relative; transform-style: preserve-3d; transform: rotateX(-15deg) rotateY(25deg);">
            <div style="position: absolute; width: 100%; height: 100%; background: #003366; border: 1px solid #fff; opacity: 0.85; transform: translateZ({ratio_d/2}px);"></div>
            <div style="position: absolute; width: {ratio_d}px; height: 100%; background: #002244; border: 1px solid #fff; transform: rotateY(90deg) translateZ({ratio_w - ratio_d/2}px);"></div>
            <div style="position: absolute; width: 100%; height: {ratio_d}px; background: #ff6600; border: 1px solid #fff; transform: rotateX(90deg) translateZ({ratio_d/2}px);"></div>
        </div>
    </div>
    """
    components.html(box_3d, height=360)

    st.divider()
    
    # Grid de Resultados
    st.subheader("📋 Resumo de Materiais")
    r1, r2, r3, r4 = st.columns(4)
    r1.markdown(f"<div class='card-metric'><b>MDF {esp}mm</b><br><h2>{res['chapas']} UN</h2></div>", unsafe_allow_html=True)
    r2.markdown(f"<div class='card-metric'><b>Fita PVC</b><br><h2>{res['fita']:.1f} M</h2></div>", unsafe_allow_html=True)
    r3.markdown(f"<div class='card-metric'><b>Parafusos 4x40</b><br><h2>{res['p_g']} UN</h2></div>", unsafe_allow_html=True)
    r4.markdown(f"<div class='card-metric'><b>Dobradiças</b><br><h2>{res['dob']} UN</h2></div>", unsafe_allow_html=True)

    # --- GERADOR DE PDF PROFISSIONAL (CORRIGIDO) ---
    def exportar_pdf_profissional(dados, p_mdf, p_fita, nome):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Correção do HexColor (H e C Maiúsculos)
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor("#003366"), spaceAfter=20)
        elements.append(Paragraph(f"ORDEM DE MATERIAL: {nome}", title_style))
        elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 25))

        # Tabela de Custos
        data_financeiro = [
            ['ITEM', 'ESPECIFICAÇÃO', 'QTD', 'UNITÁRIO', 'TOTAL'],
            ['MDF', f'{dados["esp"]}mm', f'{dados["chapas"]} UN', f'R$ {p_mdf:.2f}', f'R$ {dados["chapas"]*p_mdf:.2f}'],
            ['Fita Borda', 'Padrão PVC', f'{dados["fita"]:.1f} M', f'R$ {p_fita:.2f}', f'R$ {dados["fita"]*p_fita:.2f}'],
            ['Dobradiças', 'C35 Amort.', f'{dados["dob"]} UN', '-', '-'],
            ['Parafusos', '4.0 x 40', f'{dados["p_g"]} UN', '-', '-']
        ]
        
        t1 = Table(data_financeiro, colWidths=[150, 110, 80, 90, 90])
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ]))
        elements.append(t1)
        elements.append(Spacer(1, 40))

        # Tabela de Corte Técnica
        elements.append(Paragraph("LISTA DE CORTE (REFERÊNCIA)", styles['Heading2']))
        corte_data = [
            ['PEÇA', 'QTD', 'COMP (mm)', 'LARG (mm)', 'OBS'],
            ['Laterais', '2', str(int(alt)), str(int(prof)), 'Sentido Veio'],
            ['Base/Teto', '2', str(int(comp)), str(int(prof)), 'Interno'],
            ['Prateleira', '1', str(int(comp-30)), str(int(prof-10)), 'Ajustável'],
            ['Fundo', '1', str(int(alt-10)), str(int(comp-10)), 'MDF 6mm']
        ]
        
        t2 = Table(corte_data, colWidths=[140, 60, 110, 110, 100])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#ff6600")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ]))
        elements.append(t2)

        doc.build(elements)
        buffer.seek(0)
        return buffer

    # Exportação
    st.divider()
    pdf_out = exportar_pdf_profissional({**res, 'esp': esp}, preco_mdf, preco_fita, nome_proj)
    st.download_button(
        label="🚀 GERAR ORDEM DE PRODUÇÃO (PDF PROFISSIONAL)",
        data=pdf_out,
        file_name=f"ORDEM_{nome_proj}.pdf",
        mime="application/pdf",
        use_container_width=True
    )