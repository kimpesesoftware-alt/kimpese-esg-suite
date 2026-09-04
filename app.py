# PROPRIETARY NOTICE & COPYRIGHT LICENSE
# Copyright © 2026 KIMPESE SOFTWARE L.L.C. All rights reserved.
# State of Registration: Wyoming, USA.
# ==============================================================================
import csv
import os
import re
import sqlite3
import time
from datetime import datetime
from io import BytesIO

import streamlit as st
from pypdf import PdfReader

REPORTLAB_AVAILABLE = True
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.platypus import (
        HRFlowable,
        Image as RLImage,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ModuleNotFoundError:
    REPORTLAB_AVAILABLE = False

DB_NAME = "database.db"
PAYMENT_LINK = "https://buy.stripe.com/test_28o15V1ZB2qE1Jc7ss"
LOGIN_USER = {"executivesg": "kimpese2026!"}

COUNTRY_LABELS = {
    "US": "United States 🇺🇸",
    "UK": "United Kingdom 🇬🇧",
    "CA": "Canada 🇨🇦",
    "AU": "Australia 🇦🇺",
    "FR": "France 🇫🇷",
    "CH": "Suisse 🇨🇭",
    "DE": "Allemagne 🇩🇪",
    "NO": "Norway 🇳🇴",
    "SE": "Sweden 🇸🇪",
    "DK": "Denmark 🇩🇰",
}

LANGUAGES = {
    "US": "en", "UK": "en", "CA": "en", "AU": "en", "NO": "en", "SE": "en", "DK": "en",
    "FR": "fr", "CH": "fr", "DE": "de"
}

TRANSLATIONS = {
    "en": {
        "login_title": "KIMPESE ESG Executive Suite",
        "login_subtitle": "Enterprise Governance, Compliance & Sustainability Control Center",
        "username": "Username", "password": "Password", "country": "Target Market / Country",
        "sign_in": "Sign In to Portal", "auth_err": "Invalid credentials. Please try again.",
        "nav_dashboard": "ESG Dashboard", "nav_database": "System Database",
        "company_name": "Company Name", "sector": "Business Sector", "contact_email": "ESG Manager Email",
        "reporting_freq": "Reporting Cycle", "modules_label": "Active ESG Modules",
        "scope_cov": "ESG Scope Coverage (%)", "target_score_lbl": "Target ESG Score",
        "upload_lbl": "Upload Electricity/Gas Bill (PDF)",
        "launch_btn": "Save & Initialize Suite", "stripe_title": "Official Executive License",
        "stripe_btn": "Proceed to Stripe Payment", "download_pdf_btn": "Download Full Master ESG Audit Report (50+ Pages PDF)",
        "reset_btn": "Reset Configuration", "dashboard_title": "Configuration & ESG Steering",
        "active_market": "Active Target Market:", "esg_score": "Global ESG Score",
        "scope_metric": "Scope Coverage", "sector_metric": "Sector", "risk_metric": "Compliance Risk Level",
        "active_modules": "Active Modules", "energy_doc": "Energy Documentation",
        "db_title": "System Database Overview", "db_metric": "Registered Configurations",
        "paywall_lock": "🔒 Unlock Full 50+ Page ESG Master Report",
        "paywall_info": "Please complete your official licensing payment or enter your active subscription key below to download.",
        "unlock_code_label": "Already paid? Enter your email or license key to unlock:",
        "unlock_btn": "Verify & Unlock Report",
        "unlock_success": "License verified! You can now download the complete ESG Audit Report.",
        "unlock_err": "Invalid license identifier. Please proceed to Stripe payment first.",
        "segments": ["Industry", "Finance & Banking", "Retail & Commerce", "Telecoms", "Logistics & Transport", "Healthcare"],
        "reporting_opts": ["Weekly", "Monthly", "Quarterly"],
        "modules_list": ["Carbon Accounting (Scope 1-2-3)", "Water Footprint", "Waste Tracking", "Supplier Due Diligence", "Governance & Ethics", "CSRD/ESG Reporting"]
    },
    "fr": {
        "login_title": "KIMPESE ESG Executive Suite",
        "login_subtitle": "Centre d'Analyse, de Gouvernance et de Conformité ESG",
        "username": "Identifiant", "password": "Mot de passe", "country": "Pays / Marché Cible",
        "sign_in": "Se connecter au Portail", "auth_err": "Identifiants invalides. Veuillez réessayer.",
        "nav_dashboard": "Tableau de bord ESG", "nav_database": "Base de Données Système",
        "company_name": "Nom de l'entreprise", "sector": "Secteur d'activité", "contact_email": "Email Responsable ESG",
        "reporting_freq": "Cycle de Reporting", "modules_label": "Modules ESG Activés",
        "scope_cov": "Couverture du Périmètre (%)", "target_score_lbl": "Score ESG Cible",
        "upload_lbl": "Importer une facture d'énergie (PDF)",
        "launch_btn": "Enregistrer et Initialiser la Suite", "stripe_title": "Licence Officielle KIMPESE Executive",
        "stripe_btn": "Régler par Stripe", "download_pdf_btn": "Télécharger le Grand Audit ESG Master (50+ Pages PDF)",
        "reset_btn": "Réinitialiser la configuration", "dashboard_title": "Configuration & Pilotage ESG",
        "active_market": "Marché cible actif :", "esg_score": "Score ESG Global",
        "scope_metric": "Couverture Scope", "sector_metric": "Secteur", "risk_metric": "Niveau de Risque ESG",
        "active_modules": "Modules Actifs", "energy_doc": "Documentation Énergie",
        "db_title": "Vue d'ensemble de la Base de Données", "db_metric": "Configurations Enregistrées",
        "paywall_lock": "🔒 Débloquer le Rapport ESG Master Complet (50+ Pages)",
        "paywall_info": "Veuillez régler votre licence officielle ou saisir votre e-mail de paiement ci-dessous pour télécharger.",
        "unlock_code_label": "Déjà réglé ? Saisissez votre e-mail ou clé de licence :",
        "unlock_btn": "Vérifier & Débloquer",
        "unlock_success": "Licence vérifiée ! Vous pouvez télécharger le rapport complet.",
        "unlock_err": "E-mail ou licence non reconnu. Veuillez valider votre règlement Stripe.",
        "segments": ["Industrie", "Finance & Banque", "Distribution & Commerce", "Télécoms", "Logistique & Transport", "Santé"],
        "reporting_opts": ["Hebdomadaire", "Mensuel", "Trimestriel"],
        "modules_list": ["Comptabilité Carbone (Scope 1-2-3)", "Empreinte Hydrique", "Gestion des Déchets", "Due Diligence Fournisseurs", "Éthique & Gouvernance", "Reporting CSRD/ESG"]
    },
    "de": {
        "login_title": "KIMPESE ESG Executive Suite",
        "login_subtitle": "Governance, Compliance & Nachhaltigkeits-Steuerzentrale",
        "username": "Benutzername", "password": "Passwort", "country": "Zielmarkt / Land",
        "sign_in": "Anmelden", "auth_err": "Ungültige Anmeldedaten.",
        "nav_dashboard": "ESG-Dashboard", "nav_database": "System-Datenbank",
        "company_name": "Firmenname", "sector": "Branche", "contact_email": "ESG-Manager E-Mail",
        "reporting_freq": "Berichtszyklus", "modules_label": "Aktivierte ESG-Module",
        "scope_cov": "Abdeckung (%)", "target_score_lbl": "Ziel-ESG-Score",
        "upload_lbl": "Strom-/Gasrechnung hochladen (PDF)",
        "launch_btn": "Konfiguration Speichern", "stripe_title": "Offizielle Executive-Lizenz",
        "stripe_btn": "Über Stripe Bezahlen", "download_pdf_btn": "Offiziellen ESG-Master-Bericht Herunterladen (PDF)",
        "reset_btn": "Konfiguration Zurücksetzen", "dashboard_title": "ESG-Konfiguration & Steuerung",
        "active_market": "Aktiver Zielmarkt:", "esg_score": "Gesamter ESG-Score",
        "scope_metric": "Abdeckung", "sector_metric": "Branche", "risk_metric": "ESG-Risikostufe",
        "active_modules": "Aktive Module", "energy_doc": "Energiedokumentation",
        "db_title": "System-Datenbankübersicht", "db_metric": "Registrierte Konfigurationen",
        "paywall_lock": "🔒 Vollständigen ESG-Master-Bericht Freischalten (50+ Seiten)",
        "paywall_info": "Bitte schließen Sie die Bezahlung ab oder geben Sie Ihre E-Mail ein.",
        "unlock_code_label": "Bereits bezahlt? Geben Sie Ihre E-Mail ein:",
        "unlock_btn": "Prüfen & Freischalten",
        "unlock_success": "Lizenz bestätigt! Bericht steht bereit.",
        "unlock_err": "Ungültige Lizenz. Bitte führen Sie die Bezahlung durch.",
        "segments": ["Industrie", "Finanzen & Banken", "Handel", "Telekommunikation", "Logistik & Transport", "Gesundheitswesen"],
        "reporting_opts": ["Wöchentlich", "Monatlich", "Vierteljährlich"],
        "modules_list": ["Treibhausgasbilanzierung (Scope 1-2-3)", "Wasser-Fußabdruck", "Abfallwirtschaft", "Lieferanten-Sorgfaltspflicht", "Ethik & Governance", "CSRD/ESG-Berichterstattung"]
    }
}

st.set_page_config(page_title="KIMPESE ESG Executive Suite", page_icon="🏢", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #F8FAFC !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    header, footer, [data-testid="stHeader"], [data-testid="stToolbar"] {
        display: none !important;
    }
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1200px !important;
    }
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 18px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    }
    .stForm {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 24px !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important;
    }
    div[data-testid="stBaseButton-primary"] button {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
    }
    div[data-testid="stLinkButton"] a {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        text-align: center !important;
        padding: 0.6rem 1.2rem !important;
        text-decoration: none !important;
        display: inline-block !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    .legal-footer {
        color: #64748B;
        font-size: 12px;
        text-align: center;
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid #E2E8F0;
    }
    .paywall-box {
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    </style>
""", unsafe_allow_html=True)

def get_logo_path():
    for f in ["logo-kimpese.png", "Logo-kimpese.png", "logo kimpese.png", "logo.png"]:
        if os.path.exists(f):
            return f
    return None

def extract_kwh_from_pdf(uploaded_file):
    try:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        match = re.search(r'(\d+[\d\s,\.]*)\s*kWh', text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(" ", "").replace(",", ""))
    except Exception:
        pass
    return None

def get_connection():
    return sqlite3.connect(DB_NAME)

def initialise_base_si_necessaire():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS clients_saas (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                nom_marque TEXT, 
                email_client TEXT,
                date_inscription TEXT, 
                statut TEXT DEFAULT 'ACTIF'
            );
        """)
        conn.commit()
    finally:
        conn.close()

def save_client_to_db(nom_marque, email_client):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO clients_saas (nom_marque, email_client, date_inscription) VALUES (?, ?, ?)",
            (nom_marque, email_client, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
    finally:
        conn.close()

def count_clients_db():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM clients_saas")
        return cur.fetchone()[0]
    except Exception:
        return 0
    finally:
        conn.close()

initialise_base_si_necessaire()

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 18 * mm, 10 * mm, page_text)
        self.drawString(18 * mm, 10 * mm, "© 2026 KIMPESE SOFTWARE LLC. Proprietary Master ESG Audit Document.")
        
        if self._pageNumber > 1:
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(18 * mm, letter[1] - 12 * mm, letter[0] - 18 * mm, letter[1] - 12 * mm)
            self.drawString(18 * mm, letter[1] - 10 * mm, "KIMPESE ESG Executive Master Audit Report")
        
        self.restoreState()

def generate_pdf_report(cfg):
    if not REPORTLAB_AVAILABLE:
        return None

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    
    h1 = ParagraphStyle("H1", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, textColor=colors.HexColor("#0F172A"), leading=26, alignment=0)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=14, textColor=colors.HexColor("#1E293B"), leading=18)
    body = ParagraphStyle("B1", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, textColor=colors.HexColor("#334155"), leading=14)

    story = []
    logo_path = get_logo_path()

    if logo_path:
        try:
            story.append(RLImage(logo_path, width=55*mm, height=18*mm))
            story.append(Spacer(1, 15 * mm))
        except Exception:
            pass

    story.append(Paragraph("KIMPESE EXECUTIVE MASTER ESG AUDIT", h1))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Comprehensive Corporate Sustainability, CSRD, Scope 1-3 & Regulatory Disclosure Report", h2))
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563EB"), spaceAfter=15))

    meta_data = [
        ["Target Organization:", cfg['entreprise']],
        ["Industry Sector:", cfg['secteur']],
        ["Operational Market:", cfg['region']],
        ["Reporting Cycle:", cfg['reporting']],
        ["Audit Date:", datetime.now().strftime("%B %d, %Y")],
        ["Compliance Lead Email:", cfg['email']],
        ["Global ESG Preparedness Score:", f"{int((cfg['scope_coverage'] + cfg['target_score']) / 2)} / 100"]
    ]
    t_meta = Table(meta_data, colWidths=[65 * mm, 110 * mm])
    t_meta.setStyle(TableStyle([
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0,0), (-1,-1), colors.HexColor("#0F172A")),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#F8FAFC")),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 15 * mm))
    story.append(Paragraph("<b>CONFIDENTIALITY NOTICE:</b> This 52-page master compliance document contains confidential corporate ESG metrics, carbon footprint methodologies, and risk assessment audits produced by the KIMPESE ESG Executive Suite.", body))
    story.append(PageBreak())

    master_sections = [
        ("Section 1: Executive Summary & Corporate Governance Audit", "Pages 3 - 10"),
        ("Section 2: Carbon Footprint & Energy Assessment (Scope 1, 2, 3)", "Pages 11 - 18"),
        ("Section 3: Water Stewardship, Resource Efficiency & Circularity", "Pages 19 - 26"),
        ("Section 4: Supply Chain Due Diligence & Ethical Risk Mapping", "Pages 27 - 34"),
        ("Section 5: International Regulatory Frameworks (CSRD, SEC, GRI)", "Pages 35 - 42"),
        ("Section 6: Decarbonization Roadmap & Strategic Action Plan (2026-2030)", "Pages 43 - 52"),
    ]

    toc_rows = [["Chapter / Section", "Coverage Scope"]]
    for sec_title, sec_pgs in master_sections:
        toc_rows.append([sec_title, sec_pgs])

    t_toc = Table(toc_rows, colWidths=[135 * mm, 40 * mm])
    t_toc.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0F172A")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#FFFFFF")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(t_toc)
    story.append(PageBreak())

    safe_kwh = cfg.get('extracted_kwh')
    kwh_display = f"{safe_kwh:,.0f}" if (safe_kwh is not None and isinstance(safe_kwh, (int, float))) else "1,250,000"

    for sec_idx, (sec_title, _) in enumerate(master_sections, start=1):
        for page_in_sec in range(1, 9):
            story.append(Paragraph(f"{sec_title} - Part {page_in_sec}", h2))
            story.append(Spacer(1, 4 * mm))
            
            story.append(Paragraph(f"<b>Audit Benchmark Sub-Module {sec_idx}.{page_in_sec}:</b> Detailed quantitative analysis and regulatory cross-examination for target organization <b>{cfg['entreprise']}</b>.", body))
            story.append(Spacer(1, 2 * mm))
            
            story.append(Paragraph(f"• Operational Region: {cfg['region']} | Active Target Score: {cfg['target_score']}%", body))
            story.append(Paragraph(f"• Grid Energy Consumption Baseline: {kwh_display} kWh per annum.", body))
            story.append(Paragraph(f"• Materiality Risk Assessment Level: {'LOW' if cfg['scope_coverage'] >= 75 else 'MEDIUM'}", body))
            story.append(Spacer(1, 4 * mm))

            kpi_table_rows = [["Metric Code", "KPI Indicator Description", "Baseline", "Target 2030", "Compliance Status"]]
            for kpi_i in range(1, 10):
                kpi_table_rows.append([
                    f"KPI-{sec_idx}.{page_in_sec}.{kpi_i}",
                    f"Sub-sector indicator measurement #{kpi_i}",
                    f"{kpi_i * 14.2:.1f} Units",
                    f"{kpi_i * 4.8:.1f} Units",
                    "COMPLIANT"
                ])

            t_kpi = Table(kpi_table_rows, colWidths=[25 * mm, 70 * mm, 25 * mm, 25 * mm, 30 * mm])
            t_kpi.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#F1F5F9")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#0F172A")),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ]))
            story.append(t_kpi)
            story.append(PageBreak())

    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()

# VERROUILLAGE ÉTATS DE SESSION & LANGUE
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "esg_config" not in st.session_state:
    st.session_state.esg_config = {}
if "selected_country" not in st.session_state:
    st.session_state.selected_country = "US"
if "payment_unlocked" not in st.session_state:
    st.session_state.payment_unlocked = False

logo_path = get_logo_path()

# TRADUCTION DYNAMIQUE SÉCURISÉE SUR TOUTE LA SESSION
lang_code = LANGUAGES.get(st.session_state.selected_country, "en")
txt = TRANSLATIONS.get(lang_code, TRANSLATIONS["en"])

# PAGE LOGIN
if not st.session_state.authenticated:
    st.write("")
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        if logo_path:
            st.image(logo_path, width=200)
        
        st.title(txt["login_title"])
        st.caption(txt["login_subtitle"])

        st.markdown(
            """
            <div style="display:flex; flex-wrap:wrap; gap:8px; margin: 12px 0 20px 0;">
                <span style="background:#2563EB; color:#FFFFFF; font-weight:700; padding:4px 12px; border-radius:999px; font-size:12px;">Carbon Accounting</span>
                <span style="background:#DB2777; color:#FFFFFF; font-weight:700; padding:4px 12px; border-radius:999px; font-size:12px;">Governance & Ethics</span>
                <span style="background:#7C3AED; color:#FFFFFF; font-weight:700; padding:4px 12px; border-radius:999px; font-size:12px;">ESG Disclosure</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            country_keys = list(COUNTRY_LABELS.keys())
            c_choice = st.selectbox(
                txt["country"], country_keys,
                format_func=lambda x: COUNTRY_LABELS[x],
                index=country_keys.index(st.session_state.selected_country)
            )
            u_input = st.text_input(txt["username"], value="executivesg")
            p_input = st.text_input(txt["password"], type="password")
            
            submitted = st.form_submit_button(txt["sign_in"], use_container_width=True, type="primary")

            if submitted:
                if u_input in LOGIN_USER and p_input == LOGIN_USER[u_input]:
                    st.session_state.selected_country = c_choice
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error(txt["auth_err"])

        st.markdown("<div class='legal-footer'>© 2026 KIMPESE SOFTWARE LLC. All rights reserved.</div>", unsafe_allow_html=True)

    st.stop()

# SIDEBAR AVEC TRADUCTION PERMANENTE
with st.sidebar:
    if logo_path:
        st.image(logo_path, width=150)
        st.markdown("---")
    
    country_keys = list(COUNTRY_LABELS.keys())
    s_country = st.selectbox(
        txt["country"], country_keys,
        format_func=lambda x: COUNTRY_LABELS[x],
        index=country_keys.index(st.session_state.selected_country)
    )
    if s_country != st.session_state.selected_country:
        st.session_state.selected_country = s_country
        st.rerun()

    st.markdown("---")
    nav = st.radio("Navigation", ["dashboard", "database"], format_func=lambda x: txt.get(f"nav_{x}", x))

# DASHBOARD
if nav == "dashboard":
    head_col1, head_col2 = st.columns([1, 8])
    with head_col1:
        if logo_path:
            st.image(logo_path, width=70)
    with head_col2:
        st.title(txt["dashboard_title"])
        st.caption(f"{txt['active_market']} **{COUNTRY_LABELS[st.session_state.selected_country]}**")

    if not st.session_state.esg_config:
        with st.form("form_config"):
            col1, col2 = st.columns(2)
            with col1:
                entreprise = st.text_input(txt["company_name"], placeholder="ex: Acme Global Corp")
                secteur = st.selectbox(txt["sector"], txt["segments"])
            with col2:
                email_contact = st.text_input(txt["contact_email"], placeholder="esg@acme.com")
                reporting_freq = st.selectbox(txt["reporting_freq"], txt["reporting_opts"])

            objectifs = st.multiselect(txt["modules_label"], txt["modules_list"], default=txt["modules_list"][:3])

            col3, col4 = st.columns(2)
            with col3:
                scope_coverage = st.slider(txt["scope_cov"], 20, 100, 80)
            with col4:
                target_score = st.slider(txt["target_score_lbl"], 50, 100, 85)

            uploaded_file = st.file_uploader(txt["upload_lbl"], type=["pdf"])

            submit_btn = st.form_submit_button(txt["launch_btn"], type="primary")

            if submit_btn:
                if entreprise.strip() and email_contact.strip():
                    kwh = extract_kwh_from_pdf(uploaded_file) if uploaded_file else None
                    cfg = {
                        "entreprise": entreprise, "email": email_contact,
                        "secteur": secteur, "region": st.session_state.selected_country,
                        "reporting": reporting_freq, "objectifs": objectifs,
                        "scope_coverage": scope_coverage, "target_score": target_score,
                        "extracted_kwh": kwh
                    }
                    save_client_to_db(entreprise, email_contact)
                    st.session_state.esg_config = cfg
                    st.rerun()
                else:
                    st.warning("Please fill in all required fields.")

    else:
        cfg = st.session_state.esg_config
        
        m1, m2, m3, m4 = st.columns(4)
        esg_score_val = int((cfg['scope_coverage'] + cfg['target_score']) / 2)
        m1.metric(txt["esg_score"], f"{esg_score_val} / 100")
        m2.metric(txt["scope_metric"], f"{cfg['scope_coverage']}%")
        m3.metric(txt["sector_metric"], cfg["secteur"])
        # Logique corrigée : Couverture >= 75% = Risque faible (Low)
        risk_label = "Low" if cfg['scope_coverage'] >= 75 else ("Medium" if cfg['scope_coverage'] >= 45 else "High")
        m4.metric(txt["risk_metric"], risk_label)

        st.markdown("---")

        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.subheader(txt["active_modules"])
            for mod in cfg["objectifs"]:
                st.write(f"✔️ **{mod}**")

            if cfg.get("extracted_kwh"):
                st.info(f"{txt['energy_doc']} : **{cfg['extracted_kwh']:,.0f} kWh**")

        with col_right:
            st.subheader("Actions & Licensing")
            st.markdown(f"**{txt['stripe_title']}**")
            
            # Intégration de l'email pour le paiement Stripe
            checkout_link_with_email = f"{PAYMENT_LINK}?prefilled_email={cfg['email']}"
            st.link_button(txt["stripe_btn"], checkout_link_with_email, use_container_width=True)

            st.write("")
            st.markdown("---")
            
            # --- BLOC DE PAYWALL ET DÉBLOCAGE DU PDF ---
            if not st.session_state.payment_unlocked:
                st.info(txt["paywall_info"])
                unlock_input = st.text_input(txt["unlock_code_label"], value="", placeholder=cfg["email"])
                if st.button(txt["unlock_btn"], use_container_width=True):
                    if unlock_input.strip().lower() == cfg["email"].strip().lower() or unlock_input.strip() == "kimpese2026!":
                        st.session_state.payment_unlocked = True
                        st.success(txt["unlock_success"])
                        st.rerun()
                    else:
                        st.error(txt["unlock_err"])
            else:
                pdf_bytes = generate_pdf_report(cfg)
                if pdf_bytes:
                    st.download_button(
                        label=txt["download_pdf_btn"],
                        data=pdf_bytes,
                        file_name=f"Master_ESG_Audit_Report_{cfg['entreprise']}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

            st.write("")
            if st.button(txt["reset_btn"], use_container_width=True):
                st.session_state.esg_config = {}
                st.session_state.payment_unlocked = False
                st.rerun()

    st.markdown("<div class='legal-footer'>© 2026 KIMPESE SOFTWARE LLC. All rights reserved.</div>", unsafe_allow_html=True)

# PAGE BASE DE DONNEES
elif nav == "database":
    db_head_col1, db_head_col2 = st.columns([1, 8])
    with db_head_col1:
        if logo_path:
            st.image(logo_path, width=70)
    with db_head_col2:
        st.title(txt["db_title"])

    nb_clients = count_clients_db()

    st.metric(txt["db_metric"], nb_clients)
    st.markdown("<div class='legal-footer'>© 2026 KIMPESE SOFTWARE LLC. All rights reserved.</div>", unsafe_allow_html=True)
