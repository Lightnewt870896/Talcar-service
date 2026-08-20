import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
import json
import glob
import subprocess
import platform

try:
    import fitz  # PyMuPDF
    from PIL import Image, ImageTk
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

CONFIG_FILE = "config.json"

def load_config():
    default_dir = os.path.join(os.path.expanduser("~"), "Documents", "Orcamentos_Talcar")
    if not os.path.exists(default_dir):
        try:
            os.makedirs(default_dir)
        except Exception:
            default_dir = os.getcwd()

    config = {"pdf_folder": default_dir}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if "pdf_folder" in saved and os.path.exists(saved["pdf_folder"]):
                    config["pdf_folder"] = saved["pdf_folder"]
        except Exception:
            pass
    return config

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível salvar as configurações: {e}")

class BudgetApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TALCAR GARAGE - Gestor de Orçamentos")
        self.geometry("950x780")
        self.configure(bg="#121212")

        self.config_data = load_config()

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background="#121212", foreground="#ffffff", fieldbackground="#1e1e1e")
        style.configure("TLabel", background="#121212", foreground="#ffffff", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), background="#7b2cbf", foreground="#ffffff", borderwidth=0)
        style.map("TButton", background=[("active", "#9d4edd")])
        style.configure("TLabelframe", background="#121212", foreground="#9d4edd")
        style.configure("TLabelframe.Label", background="#121212", foreground="#9d4edd", font=("Segoe UI", 11, "bold"))
        
        style.configure("TNotebook", background="#121212", borderwidth=0)
        style.configure("TNotebook.Tab", background="#1e1e1e", foreground="#aaaaaa", padding=[15, 8], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#7b2cbf")], foreground=[("selected", "#ffffff")])

        # Estilização explícita da Treeview para correção de contraste/fundo branco
        style.configure("Treeview", 
                        background="#1e1e1e", 
                        foreground="#ffffff", 
                        fieldbackground="#1e1e1e", 
                        rowheight=25, 
                        borderwidth=0)
        style.configure("Treeview.Heading", 
                        background="#2a2a3a", 
                        foreground="#9d4edd", 
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview", 
                  background=[("selected", "#7b2cbf")], 
                  foreground=[("selected", "#ffffff")])

        self.create_header()
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_create = ttk.Frame(self.notebook, padding=10)
        self.tab_history = ttk.Frame(self.notebook, padding=10)
        self.tab_config = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_create, text=" 📝 Novo / Editar Orçamento ")
        self.notebook.add(self.tab_history, text=" 📂 Histórico de Orçamentos ")
        self.notebook.add(self.tab_config, text=" ⚙️ Configurações ")

        self.setup_tab_create()
        self.setup_tab_history()
        self.setup_tab_config()

    def create_header(self):
        header_frame = tk.Frame(self, bg="#000000", height=50)
        header_frame.pack(fill="x", side="top")
        header_label = tk.Label(header_frame, text="TALCAR GARAGE / AUTO SERVICE", font=("Segoe UI", 16, "bold"), bg="#000000", fg="#9d4edd")
        header_label.pack(pady=8)

    # ==================== ABA 1: GERAR / EDITAR ORÇAMENTO ====================
    def setup_tab_create(self):
        main_frame = ttk.Frame(self.tab_create)
        main_frame.pack(fill="both", expand=True)

        info_frame = ttk.LabelFrame(main_frame, text=" Dados do Cliente e Veículo ", padding=10)
        info_frame.pack(fill="x", pady=5)

        labels = [
            ("Nº Orçamento:", 0, 0), ("Data Entrada:", 0, 2),
            ("Nome Cliente:", 1, 0), ("Telefone:", 1, 2),
            ("Marca:", 2, 0), ("Veículo:", 2, 2),
            ("Placa:", 3, 0), ("Quilometragem:", 3, 2)
        ]

        self.entries = {}
        for label_text, row, col in labels:
            lbl = ttk.Label(info_frame, text=label_text)
            lbl.grid(row=row, column=col, sticky="e", padx=5, pady=4)
            ent = ttk.Entry(info_frame)
            ent.grid(row=row, column=col+1, sticky="ew", padx=5, pady=4)
            key = label_text.replace(":", "").strip()
            self.entries[key] = ent

        self.entries["Nº Orçamento"].insert(0, "001")
        self.entries["Data Entrada"].insert(0, datetime.now().strftime("%d/%m/%Y"))

        info_frame.columnconfigure(1, weight=1)
        info_frame.columnconfigure(3, weight=1)

        items_frame = ttk.LabelFrame(main_frame, text=" Peças a Substituir ", padding=10)
        items_frame.pack(fill="both", expand=True, pady=10)

        columns = ("desc", "qtd", "valor")
        self.tree = ttk.Treeview(items_frame, columns=columns, show="headings", height=5)
        self.tree.heading("desc", text="Descrição do Item / Peça")
        self.tree.heading("qtd", text="Qtd")
        self.tree.heading("valor", text="Valor Total (R$)")

        self.tree.column("desc", width=400)
        self.tree.column("qtd", width=80, anchor="center")
        self.tree.column("valor", width=120, anchor="e")
        self.tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(items_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        add_frame = ttk.Frame(main_frame)
        add_frame.pack(fill="x", pady=5)

        ttk.Label(add_frame, text="Item:").pack(side="left", padx=2)
        self.item_desc = ttk.Entry(add_frame, width=30)
        self.item_desc.pack(side="left", padx=5)

        ttk.Label(add_frame, text="Qtd:").pack(side="left", padx=2)
        self.item_qtd = ttk.Entry(add_frame, width=5)
        self.item_qtd.pack(side="left", padx=5)
        self.item_qtd.insert(0, "1")

        ttk.Label(add_frame, text="Total Peça (R$):").pack(side="left", padx=2)
        self.item_val = ttk.Entry(add_frame, width=10)
        self.item_val.pack(side="left", padx=5)

        ttk.Button(add_frame, text="+ Adicionar", command=self.add_item).pack(side="left", padx=5)
        ttk.Button(add_frame, text="- Remover", command=self.remove_item).pack(side="left", padx=5)

        totals_frame = ttk.LabelFrame(main_frame, text=" Serviço / Mão de Obra ", padding=10)
        totals_frame.pack(fill="x", pady=5)

        ttk.Label(totals_frame, text="Valor da Mão de Obra (R$):").grid(row=0, column=0, sticky="e", padx=5)
        self.mo_entry = ttk.Entry(totals_frame, width=15)
        self.mo_entry.grid(row=0, column=1, sticky="w", padx=5)
        self.mo_entry.insert(0, "0.00")

        btn_generate = ttk.Button(main_frame, text="📄 GERAR E VISUALIZAR ORÇAMENTO EM PDF", command=self.generate_pdf)
        btn_generate.pack(fill="x", pady=10, ipady=8)

    def add_item(self):
        desc = self.item_desc.get().strip()
        qtd = self.item_qtd.get().strip()
        val = self.item_val.get().strip()

        if not desc or not qtd or not val:
            messagebox.showwarning("Atenção", "Preencha a descrição, quantidade e valor do item!")
            return

        try:
            val_float = float(val.replace(",", "."))
            self.tree.insert("", "end", values=(desc, qtd, f"R$ {val_float:.2f}"))
            self.item_desc.delete(0, tk.END)
            self.item_qtd.delete(0, tk.END)
            self.item_qtd.insert(0, "1")
            self.item_val.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Erro", "Valor de peça inválido!")

    def remove_item(self):
        selected = self.tree.selection()
        for s in selected:
            self.tree.delete(s)

    def generate_pdf(self):
        num_orc = self.entries["Nº Orçamento"].get().strip()
        data_ent = self.entries["Data Entrada"].get().strip()
        cliente = self.entries["Nome Cliente"].get().strip()
        telefone = self.entries["Telefone"].get().strip()
        marca = self.entries["Marca"].get().strip()
        veiculo = self.entries["Veículo"].get().strip()
        placa = self.entries["Placa"].get().strip()
        km = self.entries["Quilometragem"].get().strip()

        try:
            mao_obra = float(self.mo_entry.get().replace(",", "."))
        except ValueError:
            mao_obra = 0.00

        target_dir = self.config_data["pdf_folder"]
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        base_name = f"Orcamento_{num_orc if num_orc else '001'}_{cliente.replace(' ', '_') if cliente else 'Cliente'}"
        filepath = os.path.join(target_dir, f"{base_name}.pdf")
        json_path = os.path.join(target_dir, f"{base_name}.json")

        # Salvar dados para permitir edição futura
        items_data_save = []
        for item in self.tree.get_children():
            vals = self.tree.item(item)["values"]
            items_data_save.append({"desc": vals[0], "qtd": vals[1], "valor": vals[2]})

        save_payload = {
            "num_orc": num_orc,
            "data_ent": data_ent,
            "cliente": cliente,
            "telefone": telefone,
            "marca": marca,
            "veiculo": veiculo,
            "placa": placa,
            "km": km,
            "mao_obra": self.mo_entry.get().strip(),
            "items": items_data_save
        }

        try:
            with open(json_path, "w", encoding="utf-8") as jf:
                json.dump(save_payload, jf, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Erro ao salvar backup JSON: {e}")

        # Gerar PDF
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('TitleStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=22, textColor=colors.HexColor('#ffffff'), alignment=1, leading=24)
        sub_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#9d4edd'), alignment=1, leading=14)
        contact_style = ParagraphStyle('ContactStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#aaaaaa'), alignment=1, leading=12)
        sec_header = ParagraphStyle('SecHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor('#9d4edd'))
        cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#ffffff'))
        cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#9d4edd'))

        logo_path = None
        for ext in ['logo.png', 'logo.jpg', 'logo.jpeg', 'logo.PNG', 'logo.JPG']:
            if os.path.exists(ext):
                logo_path = ext
                break

        if logo_path:
            img = RLImage(logo_path, width=130, height=85)
            img.hAlign = 'CENTER'
            elements.append(img)
            elements.append(Spacer(1, 8))
        else:
            # Correção de sobreposição do texto ajustando Spacer e Styles
            elements.append(Paragraph("TALCAR GARAGE", title_style))
            elements.append(Spacer(1, 4))
            elements.append(Paragraph("AUTO SERVICE", sub_style))
            elements.append(Spacer(1, 8))

        elements.append(Paragraph("Rua Natal n°37 Diadema-SP<br/>WhatsApp: (11) 93278-7113 | Instagram: @TALCAR.AUTOSERVICE", contact_style))
        elements.append(Spacer(1, 15))

        doc_info = [[
            Paragraph("<b>ORÇAMENTO / ORDEM DE SERVIÇO</b>", cell_style),
            Paragraph(f"<b>Nº: {num_orc}</b>", cell_bold)
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
            [Paragraph("Cliente:", cell_bold), Paragraph(cliente, cell_style), Paragraph("Telefone:", cell_bold), Paragraph(telefone, cell_style)],
            [Paragraph("Veículo:", cell_bold), Paragraph(veiculo, cell_style), Paragraph("Marca:", cell_bold), Paragraph(marca, cell_style)],
            [Paragraph("Placa:", cell_bold), Paragraph(placa, cell_style), Paragraph("Quilometragem:", cell_bold), Paragraph(km, cell_style)],
            [Paragraph("Entrada:", cell_bold), Paragraph(data_ent, cell_style), Paragraph("", cell_style), Paragraph("", cell_style)]
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

        items_data = [[
            Paragraph("Descrição da Peça / Serviço", cell_bold),
            Paragraph("Qtd", cell_bold),
            Paragraph("Total Peça", cell_bold)
        ]]

        total_pecas = 0.0
        for item in self.tree.get_children():
            vals = self.tree.item(item)["values"]
            desc_val, qtd_val, val_str = vals[0], vals[1], vals[2]
            val_num = float(str(val_str).replace("R$", "").strip().replace(",", "."))
            total_pecas += val_num
            items_data.append([
                Paragraph(str(desc_val), cell_style),
                Paragraph(str(qtd_val), cell_style),
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

        try:
            doc.build(elements, onFirstPage=make_background)
            self.refresh_history()
            self.open_pdf_viewer(filepath)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar PDF: {str(e)}")

    # ==================== ABA 2: HISTÓRICO DE ORÇAMENTOS ====================
    def setup_tab_history(self):
        main_frame = ttk.Frame(self.tab_history)
        main_frame.pack(fill="both", expand=True)

        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill="x", pady=5)

        ttk.Label(filter_frame, text="🔍 Pesquisar Orçamento:").pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_history())
        
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=35)
        search_entry.pack(side="left", padx=5)

        ttk.Button(filter_frame, text="🔄 Atualizar Lista", command=self.refresh_history).pack(side="right", padx=5)

        hist_columns = ("filename", "date", "size")
        self.history_tree = ttk.Treeview(main_frame, columns=hist_columns, show="headings", height=15)
        self.history_tree.heading("filename", text="Nome do Arquivo PDF")
        self.history_tree.heading("date", text="Data de Modificação")
        self.history_tree.heading("size", text="Tamanho (KB)")

        self.history_tree.column("filename", width=450)
        self.history_tree.column("date", width=180, anchor="center")
        self.history_tree.column("size", width=100, anchor="e")
        self.history_tree.pack(fill="both", expand=True, side="left", pady=5)

        hist_scroll = ttk.Scrollbar(main_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=hist_scroll.set)
        hist_scroll.pack(side="right", fill="y", pady=5)

        actions_frame = ttk.Frame(self.tab_history)
        actions_frame.pack(fill="x", pady=10)

        ttk.Button(actions_frame, text="✏️ Editar Orçamento", command=self.edit_selected_budget).pack(side="left", padx=5)
        ttk.Button(actions_frame, text="👁️ Abrir PDF", command=self.view_selected_pdf).pack(side="left", padx=5)
        ttk.Button(actions_frame, text="↗️ Abrir no Sistema", command=self.open_selected_system).pack(side="left", padx=5)
        ttk.Button(actions_frame, text="🗑️ Excluir", command=self.delete_selected_pdf).pack(side="right", padx=5)

        self.refresh_history()

    def edit_selected_budget(self):
        pdf_path = self.get_selected_pdf_path()
        if not pdf_path:
            return

        json_path = pdf_path.rsplit(".", 1)[0] + ".json"
        if not os.path.exists(json_path):
            messagebox.showwarning("Aviso", "Não foram encontrados os dados editáveis deste orçamento (arquivo JSON não existe).")
            return

        try:
            with open(json_path, "r", encoding="utf-8") as jf:
                data = json.load(jf)

            # Limpar formulário atual
            for key, entry in self.entries.items():
                entry.delete(0, tk.END)

            self.tree.delete(*self.tree.get_children())
            self.mo_entry.delete(0, tk.END)

            # Preencher formulário com dados salvos
            self.entries["Nº Orçamento"].insert(0, data.get("num_orc", ""))
            self.entries["Data Entrada"].insert(0, data.get("data_ent", ""))
            self.entries["Nome Cliente"].insert(0, data.get("cliente", ""))
            self.entries["Telefone"].insert(0, data.get("telefone", ""))
            self.entries["Marca"].insert(0, data.get("marca", ""))
            self.entries["Veículo"].insert(0, data.get("veiculo", ""))
            self.entries["Placa"].insert(0, data.get("placa", ""))
            self.entries["Quilometragem"].insert(0, data.get("km", ""))
            self.mo_entry.insert(0, data.get("mao_obra", "0.00"))

            for item in data.get("items", []):
                self.tree.insert("", "end", values=(item["desc"], item["qtd"], item["valor"]))

            # Alternar para a aba de criação
            self.notebook.select(self.tab_create)
            messagebox.showinfo("Sucesso", "Orçamento carregado com sucesso para edição!")

        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar os dados para edição: {e}")

    def refresh_history(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        folder = self.config_data["pdf_folder"]
        if not os.path.exists(folder):
            return

        pdf_files = glob.glob(os.path.join(folder, "*.pdf"))
        pdf_files.sort(key=os.path.getmtime, reverse=True)

        for fpath in pdf_files:
            fname = os.path.basename(fpath)
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%d/%m/%Y %H:%M:%S")
            fsize = f"{os.path.getsize(fpath) / 1024:.1f} KB"
            self.history_tree.insert("", "end", values=(fname, mtime, fsize), tags=(fpath,))

    def filter_history(self):
        query = self.search_var.get().lower().strip()
        for item in self.history_tree.get_children():
            vals = self.history_tree.item(item)["values"]
            fname = str(vals[0]).lower()
            if query in fname:
                self.history_tree.reattach(item, "", "end")
            else:
                self.history_tree.detach(item)

    def get_selected_pdf_path(self):
        selected = self.history_tree.selection()
        if not selected:
            messagebox.showwarning("Atenção", "Selecione um orçamento na lista!")
            return None
        item = selected[0]
        fname = self.history_tree.item(item)["values"][0]
        return os.path.join(self.config_data["pdf_folder"], fname)

    def view_selected_pdf(self):
        path = self.get_selected_pdf_path()
        if path and os.path.exists(path):
            self.open_pdf_viewer(path)

    def open_selected_system(self):
        path = self.get_selected_pdf_path()
        if path and os.path.exists(path):
            self.open_file_in_system(path)

    def delete_selected_pdf(self):
        path = self.get_selected_pdf_path()
        if path and os.path.exists(path):
            if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir permanentemente o arquivo:\n{os.path.basename(path)}?"):
                try:
                    os.remove(path)
                    json_path = path.rsplit(".", 1)[0] + ".json"
                    if os.path.exists(json_path):
                        os.remove(json_path)
                    self.refresh_history()
                    messagebox.showinfo("Sucesso", "Arquivo e dados excluídos com sucesso!")
                except Exception as e:
                    messagebox.showerror("Erro", f"Não foi possível excluir o arquivo: {e}")

    # ==================== ABA 3: CONFIGURAÇÕES ====================
    def setup_tab_config(self):
        main_frame = ttk.LabelFrame(self.tab_config, text=" Diretório de Destino dos Orçamentos ", padding=15)
        main_frame.pack(fill="x", pady=10)

        ttk.Label(main_frame, text="Pasta onde todos os PDFs gerados serão salvos:").pack(anchor="w", pady=5)

        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill="x", pady=5)

        self.path_entry = ttk.Entry(path_frame)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.path_entry.insert(0, self.config_data["pdf_folder"])

        ttk.Button(path_frame, text="📁 Selecionar Pasta", command=self.browse_folder).pack(side="right")

        ttk.Button(main_frame, text="💾 Salvar Configurações", command=self.save_folder_config).pack(anchor="e", pady=15)

    def browse_folder(self):
        chosen = filedialog.askdirectory(initialdir=self.config_data["pdf_folder"])
        if chosen:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, chosen)

    def save_folder_config(self):
        new_path = self.path_entry.get().strip()
        if not os.path.exists(new_path):
            try:
                os.makedirs(new_path, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Erro", f"Caminho inválido ou sem permissão: {e}")
                return

        self.config_data["pdf_folder"] = new_path
        save_config(self.config_data)
        self.refresh_history()
        messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")

    # ==================== VISUALIZADOR DE PDF ====================
    def open_pdf_viewer(self, pdf_path):
        viewer_win = tk.Toplevel(self)
        viewer_win.title(f"Visualizador de PDF - {os.path.basename(pdf_path)}")
        viewer_win.geometry("800x900")
        viewer_win.configure(bg="#1a1a1a")

        top_bar = tk.Frame(viewer_win, bg="#000000", height=40)
        top_bar.pack(fill="x", side="top")

        btn_sys = ttk.Button(top_bar, text="↗️ Abrir no Leitor do Sistema", command=lambda: self.open_file_in_system(pdf_path))
        btn_sys.pack(side="right", padx=10, pady=5)

        if not HAS_FITZ:
            msg_frame = tk.Frame(viewer_win, bg="#1a1a1a")
            msg_frame.pack(expand=True)
            tk.Label(msg_frame, text="📄 Orçamento gerado com sucesso!", font=("Segoe UI", 14, "bold"), bg="#1a1a1a", fg="#ffffff").pack(pady=10)
            tk.Label(msg_frame, text=f"Arquivo salvo em:\n{pdf_path}", font=("Segoe UI", 10), bg="#1a1a1a", fg="#aaaaaa").pack(pady=5)
            tk.Label(msg_frame, text="Para visualizar a prévia do PDF diretamente nesta janela,\ninstale o PyMuPDF e Pillow executando no terminal:\n\npip install PyMuPDF Pillow", font=("Segoe UI", 10, "italic"), bg="#1a1a1a", fg="#9d4edd").pack(pady=15)
            ttk.Button(msg_frame, text="Abrir PDF Agora", command=lambda: self.open_file_in_system(pdf_path)).pack(pady=10)
            return

        try:
            doc = fitz.open(pdf_path)
            canvas_frame = tk.Frame(viewer_win, bg="#1a1a1a")
            canvas_frame.pack(fill="both", expand=True)

            canvas = tk.Canvas(canvas_frame, bg="#1a1a1a", highlightthickness=0)
            scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="#1a1a1a")

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            images_list = []
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=130)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                photo = ImageTk.PhotoImage(img)
                images_list.append(photo)

                lbl = tk.Label(scrollable_frame, image=photo, bg="#1a1a1a", bd=2, relief="solid")
                lbl.pack(pady=15, padx=20)

            viewer_win.images_list = images_list

        except Exception as e:
            messagebox.showerror("Erro de Leitura", f"Não foi possível renderizar a prévia do PDF: {e}")

    def open_file_in_system(self, filepath):
        try:
            if platform.system() == 'Darwin':
                subprocess.call(('open', filepath))
            elif platform.system() == 'Windows':
                os.startfile(filepath)
            else:
                subprocess.call(('xdg-open', filepath))
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir o arquivo no sistema: {e}")

if __name__ == "__main__":
    app = BudgetApp()
    app.mainloop()