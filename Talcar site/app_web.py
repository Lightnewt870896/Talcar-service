import streamlit as st
import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

st.set_page_config(page_title="TALCAR GARAGE - Gestor de Orçamentos", page_icon="🚗", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #121212;
        color: #ffffff;
    }
    input, textarea, select {
        color: #ffffff !important;
        background-color: #1e1e1e !important;
    }
    div[data-testid="stTable"] {
        background-color: #1e1e1e;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

DB_FILE = "orcamentos_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

def generate_pdf_bytes(data):
    pdf_filename = "temp_orcamento.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=22, textColor=colors.HexColor('#ffffff'), alignment=1, leading=24)
    sub_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#9d4edd'), alignment=1, leading=14)
    contact_style = ParagraphStyle('ContactStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#aaaaaa'), alignment=1, leading=12)
    sec_header = ParagraphStyle('SecHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor('#9d4edd'))
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#ffffff'))
    cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#9d4edd'))

    logo_path = None
    for ext in ['logo.png', 'logo.jpg', 'logo.jpeg']:
        if os.path.exists(ext):
            logo_path = ext
            break

    if logo_path:
        img = RLImage(logo_path, width=130, height=85)
        img.hAlign = 'CENTER'
        elements.append(img)
        elements.append(Spacer(1, 8))
    else:
        elements.append(Paragraph("TALCAR GARAGE", title_style))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph("AUTO SERVICE", sub_style))
        elements.append(Spacer(1, 8))

    elements.append(Paragraph("Rua Natal n°37 Diadema-SP<br/>WhatsApp: (11) 93278-7113 | Instagram: @TALCAR.AUTOSERVICE", contact_style))
    elements.append(Spacer(1, 15))

    doc_info = [[
        Paragraph("<b>ORÇAMENTO / ORDEM DE SERVIÇO</b>", cell_style),
        Paragraph(f"<b>Nº: {data['num_orc']}</b>", cell_bold)
    ]]
    t_doc = Table(doc_info, colWidths=[380, 150])
    t_doc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#161622')),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t_doc)
    elements.append(Spacer(1, 15))

    info_data = [
        [Paragraph("Cliente:", cell_bold), Paragraph(data['cliente'], cell_style), Paragraph("Telefone:", cell_bold), Paragraph(data['telefone'], cell_style)],
        [Paragraph("Veículo:", cell_bold), Paragraph(data['veiculo'], cell_style), Paragraph("Marca:", cell_bold), Paragraph(data['marca'], cell_style)],
        [Paragraph("Placa:", cell_bold), Paragraph(data['placa'], cell_style), Paragraph("Quilometragem:", cell_bold), Paragraph(data['km'], cell_style)],
        [Paragraph("Entrada:", cell_bold), Paragraph(data['data_ent'], cell_style), Paragraph("", cell_style), Paragraph("", cell_style)]
    ]
    t_info = Table(info_data, colWidths=[70, 195, 85, 180])
    t_info.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#222230')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("PEÇAS A SUBSTITUIR / SERVIÇOS", sec_header))
    elements.append(Spacer(1, 5))

    items_data = [[Paragraph("Descrição da Peça / Serviço", cell_bold), Paragraph("Qtd", cell_bold), Paragraph("Total Peça", cell_bold)]]
    total_pecas = 0.0

    for item in data['lista_items']:
        val_num = float(item['val'])
        total_pecas += val_num
        items_data.append([
            Paragraph(item['desc'], cell_style),
            Paragraph(str(item['qtd']), cell_style),
            Paragraph(f"R$ {val_num:.2f}", cell_style)
        ])

    t_items = Table(items_data, colWidths=[350, 60, 120])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a1a26')),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#1f1f2e')),
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
        ('ALIGN', (2,0), (2,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_items)
    elements.append(Spacer(1, 15))

    mao_obra = float(data.get('mao_obra', 0.0))
    total_geral = total_pecas + mao_obra
    totals_data = [
        [Paragraph("Peças:", cell_style), Paragraph(f"R$ {total_pecas:.2f}", cell_style)],
        [Paragraph("Mão de Obra:", cell_style), Paragraph(f"R$ {mao_obra:.2f}", cell_style)],
        [Paragraph("<b>TOTAL:</b>", cell_bold), Paragraph(f"<b>R$ {total_geral:.2f}</b>", cell_bold)]
    ]
    t_totals = Table(totals_data, colWidths=[100, 100])
    t_totals.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('BACKGROUND', (0,2), (1,2), colors.HexColor('#241434')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    
    wrapper_table = Table([[Paragraph("", cell_style), t_totals]], colWidths=[330, 200])
    elements.append(wrapper_table)

    def make_background(canvas, doc_obj):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor('#0b0b0e'))
        canvas.rect(0, 0, A4[0], A4[1], fill=1)
        canvas.restoreState()

    doc.build(elements, onFirstPage=make_background)

    with open(pdf_filename, "rb") as f:
        pdf_bytes = f.read()
    if os.path.exists(pdf_filename):
        os.remove(pdf_filename)
    return pdf_bytes

# --- INTERFACE WEB ---
st.title("🚗 TALCAR GARAGE - Web App")

db = load_db()

if "lista_items" not in st.session_state:
    st.session_state.lista_items = []

tab1, tab2 = st.tabs(["📝 Criar / Editar Orçamento", "📂 Histórico de Orçamentos"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        num_orc = st.text_input("Nº Orçamento", value="001")
        cliente = st.text_input("Nome Cliente")
        marca = st.text_input("Marca")
        placa = st.text_input("Placa")
    with col2:
        data_ent = st.text_input("Data Entrada", value=datetime.now().strftime("%d/%m/%Y"))
        telefone = st.text_input("Telefone")
        veiculo = st.text_input("Veículo")
        km = st.text_input("Quilometragem")

    st.subheader("Peças a Substituir")
    c_desc, c_qtd, c_val, c_btn = st.columns([3, 1, 1, 1])
    i_desc = c_desc.text_input("Descrição da Peça", key="i_desc")
    i_qtd = c_qtd.text_input("Qtd", value="1", key="i_qtd")
    i_val = c_val.number_input("Valor Total (R$)", min_value=0.0, step=10.0, key="i_val")
    
    if c_btn.button("➕ Adicionar", use_container_width=True):
        if i_desc:
            st.session_state.lista_items.append({"Descrição": i_desc, "Qtd": i_qtd, "Valor Total (R$)": f"R$ {i_val:.2f}", "desc": i_desc, "qtd": i_qtd, "val": i_val})
            st.rerun()

    if st.session_state.lista_items:
        # Exibe apenas as colunas amigáveis na tabela
        tabela_visual = [{"Descrição": item["desc"], "Qtd": item["qtd"], "Valor Total (R$)": f"R$ {float(item['val']):.2f}"} for item in st.session_state.lista_items]
        st.table(tabela_visual)
        if st.button("🗑️ Limpar Itens"):
            st.session_state.lista_items = []
            st.rerun()

    mao_obra = st.number_input("Mão de Obra (R$)", min_value=0.0, step=50.0)

    if st.button("💾 Salvar e Gerar PDF", type="primary", use_container_width=True):
        payload = {
            "num_orc": num_orc, "data_ent": data_ent, "cliente": cliente,
            "telefone": telefone, "marca": marca, "veiculo": veiculo,
            "placa": placa, "km": km, "mao_obra": mao_obra,
            "lista_items": st.session_state.lista_items
        }
        db[num_orc] = payload
        save_db(db)
        
        pdf_data = generate_pdf_bytes(payload)
        st.success(f"Orçamento Nº {num_orc} salvo com sucesso!")
        st.download_button(
            label="📄 Baixar PDF do Orçamento",
            data=pdf_data,
            file_name=f"Orcamento_{num_orc}_{cliente}.pdf",
            mime="application/pdf"
        )

with tab2:
    st.subheader("Orçamentos Salvos")
    search = st.text_input("🔍 Pesquisar por Cliente ou Nº")
    
    for key, data in list(db.items()):
        if search.lower() in data['cliente'].lower() or search in data['num_orc']:
            with st.expander(f"Orçamento Nº {data['num_orc']} - {data['cliente']} ({data['data_ent']})"):
                st.write(f"**Veículo:** {data['marca']} {data['veiculo']} | **Placa:** {data['placa']}")
                st.write(f"**Telefone:** {data['telefone']}")
                
                tabela_visual_hist = [{"Descrição": item["desc"], "Qtd": item["qtd"], "Valor Total (R$)": f"R$ {float(item['val']):.2f}"} for item in data.get('lista_items', [])]
                st.table(tabela_visual_hist)
                
                col_e1, col_e2 = st.columns(2)
                if col_e1.button("✏️ Carregar para Editar", key=f"edit_{key}"):
                    st.session_state.lista_items = data.get('lista_items', [])
                    st.info("Itens recarregados! Vá para a aba 'Criar / Editar Orçamento' para finalizar.")
                
                pdf_hist = generate_pdf_bytes(data)
                col_e2.download_button("📄 Baixar PDF", pdf_hist, file_name=f"Orcamento_{data['num_orc']}.pdf", mime="application/pdf", key=f"pdf_{key}")