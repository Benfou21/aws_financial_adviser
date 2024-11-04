import yfinance as yf
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
import matplotlib.pyplot as plt
import tempfile
from io import BytesIO

from bedrock_agents import *




def download_report(selected_ticker):
    buffer = BytesIO()
    create_pdf(buffer, selected_ticker)
    buffer.seek(0)
    return buffer

#  données financières de l'entreprise
def get_company_financials(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    income_statement = ticker.financials  # Compte de résultat
    balance_sheet = ticker.balance_sheet  # Bilan
    cashflow_statement = ticker.cashflow  # Flux de trésorerie
    return income_statement, balance_sheet, cashflow_statement

def df_to_table(dataframe):
    table_data = [dataframe.columns.insert(0, "Date").tolist()]
    for idx, row in dataframe.iterrows():
        row_data = [idx] + [
            f"{int(value):,}" if isinstance(value, (int, float)) and not pd.isna(value) else ""
            for value in row
        ]
        table_data.append(row_data)
    return table_data



# graphique d'inflation
def create_inflation_chart():
    fig, ax = plt.subplots(figsize=(6, 4))
    data = yf.download("^IRX", period="1mo", interval="1d")
    ax.plot(data.index, data["Close"], color="blue", label="Taux à 10 ans")
    ax.set_title("Graphique de l'inflation (proxy)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Taux")
    ax.legend()
    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    fig.savefig(temp_file.name, format="png")
    plt.close(fig)
    return temp_file.name

# graphique du VIX
def create_vix_chart():
    fig, ax = plt.subplots(figsize=(6, 4))
    vix_data = yf.download("^VIX", period="1mo", interval="1d")
    ax.plot(vix_data.index, vix_data["Close"], color="red", label="VIX")
    ax.set_title("Graphique du VIX sur 1 mois")
    ax.set_xlabel("Date")
    ax.set_ylabel("Volatilité")
    ax.legend()
    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    fig.savefig(temp_file.name, format="png")
    plt.close(fig)
    return temp_file.name


# graphique des prix de l'action sur 1 mois
def create_price_chart(ticker_symbol):
    data = yf.download(ticker_symbol, period="1mo", interval="1d")
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(data.index, data["Close"], color="green", label=f"{ticker_symbol} Price")
    ax.set_title(f"Prix de l'action {ticker_symbol} sur 1 mois")
    ax.set_xlabel("Date")
    ax.set_ylabel("Prix de clôture")
    ax.legend()
    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    fig.savefig(temp_file.name, format="png")
    plt.close(fig)
    return temp_file.name

# informations de l'entreprise
def get_ticker_name(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    ticker_name = {
        "code": info.get("symbol", "N/A"),
        "ticker": ticker_symbol,
        "name": info.get("longName", ticker_symbol),
        "sector": info.get("sector", "N/A"),
        "country": info.get("country", "N/A"),
        "market_cap": f"{info.get('marketCap', 'N/A'):,} USD" if info.get("marketCap") else "N/A",
        "description": info.get("longBusinessSummary", "Description non disponible.")[:300] + "..."
    }
    return ticker_name

# en-tête et le pied de page institutionnels
def create_header(company_info):
    def header(canvas, doc):
        
        logo_path = "logo_banque.png"
        canvas.drawImage(logo_path, x=doc.leftMargin, y=A4[1] - inch, width=1*inch, height=1*inch, preserveAspectRatio=True)
        canvas.setFont("Helvetica-Bold", 16)
        company_name = company_info.get("name", "Entreprise")
        canvas.drawString(doc.leftMargin + 1.2*inch, A4[1] - 0.8*inch, f"Rapport d'Analyse de {company_name}")
        canvas.setFont("Helvetica", 10)
        canvas.drawString(doc.leftMargin + 1.2*inch, A4[1] - 1*inch, "Banque d'Investissement RMBP")
        canvas.line(doc.leftMargin, A4[1] - inch - 10, A4[0] - doc.rightMargin, A4[1] - inch - 10)
    return header

def footer(canvas, doc):
    canvas.setFont("Helvetica", 8)
    canvas.drawString(doc.leftMargin, 0.75*inch, "Banque d'Investissement RMBP - Rapport d'Analyse Institutionnel")
    canvas.drawRightString(A4[0] - doc.rightMargin, 0.75*inch, f"Page {doc.page}")

def get_company_info(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    company_info = {
        "code": info.get("symbol", "N/A"),
        "ticker": ticker_symbol,
        "name": info.get("longName", ticker_symbol),
        "sector": info.get("sector", "N/A"),
        "country": info.get("country", "N/A"),
        "market_cap": f"{info.get('marketCap', 'N/A'):,} USD" if info.get("marketCap") else "N/A",
        "description": info.get("longBusinessSummary", "Description non disponible.")[:300] + "..."
    }
    return company_info

# Créer le PDF complet
def create_pdf(filename, ticker_name):
   
    company_info = get_company_info(ticker_name)
    output_macro = get_macro_news()  # Macro news context
    sentiment_output= get_news_with_sentiment(ticker_name) #Sentiment new context
    
    macrotext = gat_analyse_macro(output_macro) #Analyse macro
    profil_rest_data = profil_resp_data(ticker_name)
    response_fin = finance_resp_data(ticker_name)
    resp_sentiment_anal = sentiment_anal(ticker_name,sentiment_output)
    resp_risk_anal = risk_anal(ticker_name,output_macro)
    resp_holders_anal = holders_anal(ticker_name)
    
    resp_tot_anal = tot_anal(ticker_name,macrotext,profil_rest_data,response_fin,resp_risk_anal,resp_holders_anal)
    
    doc = SimpleDocTemplate(filename, pagesize=A4, leftMargin=inch, rightMargin=inch, topMargin=1.5*inch, bottomMargin=inch)
    elements = []
    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle("Heading2", fontSize=12, leading=14, spaceAfter=12, textColor=colors.HexColor("#003366"), fontName="Helvetica-Bold")
    normal_style = styles["BodyText"]
    normal_style.fontName = "Helvetica"
    
    # Section d'information de l'entreprise
    company_details = f"""
    <b>Code Entreprise:</b> {company_info.get('code', 'N/A')}<br/>
    <b>Ticker:</b> {company_info.get('ticker', 'N/A')}<br/>
    <b>Secteur:</b> {company_info.get('sector', 'N/A')}<br/>
    <b>Pays:</b> {company_info.get('country', 'N/A')}<br/>
    <b>Capitalisation Boursière:</b> {company_info.get('market_cap', 'N/A')}
    """
    elements.append(Paragraph(company_details, normal_style))
    elements.append(Spacer(1, 24))
    elements.append(Paragraph(f"<b>Description de l'entreprise:</b> {company_info.get('description')}", normal_style))
    elements.append(Spacer(1, 24))

    # Section Macroéconomique 
    elements.append(Paragraph("1. Analyse Macroéconomique", heading_style))
    elements.append(Paragraph("<b>Actualités Macroéconomiques:</b>", normal_style))
    elements.append(Paragraph(macrotext, normal_style))
    elements.append(Spacer(1, 12))
    inflation_chart_path = create_inflation_chart()
    vix_chart_path = create_vix_chart()
    elements.append(Paragraph("Graphiques de l'Inflation et du VIX", heading_style))
    chart_data = [
        [Image(inflation_chart_path, width=3.5*inch, height=2.5*inch), Image(vix_chart_path, width=3.5*inch, height=2.5*inch)]
    ]
    chart_table = Table(chart_data)
    chart_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    elements.append(chart_table)
    elements.append(Spacer(1, 24))






    # Ajout de la section 2 : Analyse Sectorielle
    elements.append(Paragraph("2. Analyse Sectorielle", heading_style))

    # Exemple de texte pour l'analyse sectorielle - à personnaliser ou à alimenter avec des données dynamiques
    elements.append(Paragraph(profil_rest_data, normal_style))
    elements.append(Spacer(1, 12))  # Espacement après la section






    # États Financiers
    income_statement, balance_sheet, cashflow_statement = get_company_financials(company_info["ticker"])
    elements.append(Paragraph("3. Analyse des États Financiers", heading_style))

    elements.append(Paragraph(response_fin, normal_style))
    elements.append(Spacer(1, 12))  # Espacement après la section

    # Ajout du graphique des prix de l'action
    price_chart_path = create_price_chart(company_info["ticker"])
    elements.append(Paragraph(f"Évolution du prix de l'action {company_info['ticker']} sur 1 mois", heading_style))
    elements.append(Image(price_chart_path, width=6*inch, height=4*inch))
    elements.append(Spacer(1, 24))  # Espacement après le graphique



    # section 4 : Analyse Sectorielle
    elements.append(Paragraph("4. Analyse Gouvernance et Composition du Conseil d’Administration", heading_style))
    elements.append(Paragraph(resp_holders_anal, normal_style))
    elements.append(Spacer(1, 12))  # Espacement après la section


    # section 5 : Analyse Sectorielle
    elements.append(Paragraph("5. Actualités et Sentiment de Marché", heading_style))
    elements.append(Paragraph(resp_sentiment_anal, normal_style))
    elements.append(Spacer(1, 12))  # Espacement après la section

    # section 6 : Analyse Sectorielle
    elements.append(Paragraph("6. Risques et Opportunités", heading_style))
    elements.append(Paragraph(resp_risk_anal, normal_style))
    elements.append(Spacer(1, 12))  # Espacement après la section

    # section 7 : Analyse Sectorielle
    elements.append(Paragraph("7. Synthèse et Recommandations", heading_style))
    elements.append(Paragraph(resp_tot_anal, normal_style))
    elements.append(Spacer(1, 12))  # Espacement après la section


    # Style pour la conclusion
    conclusion_style = ParagraphStyle(
        "Conclusion",
        fontSize=12,
        leading=14,
        spaceAfter=12,
        textColor=colors.HexColor("#003366"),
        fontName="Helvetica-Bold"
    )
    normal_style = getSampleStyleSheet()["BodyText"]

    conclusion_text = f"""
    <b>Conclusion</b><br/><br/>
    En conclusion, <b>{ticker_name}</b> se positionne comme un acteur significatif dans son secteur d’activité, 
    bénéficiant d’un environnement macroéconomique actuel qui présente à la fois des opportunités de croissance et des défis. 
    L’analyse de ses performances financières montre une stabilité solide, avec des perspectives favorables en raison de sa diversification stratégique et de sa présence sur les marchés clés.<br/><br/>
    L’entreprise démontre des bases financières robustes, malgré certaines marges de progression possibles dans l’optimisation de la rentabilité. 
    L’évaluation des risques révèle également une bonne préparation de l’entreprise face aux aléas du marché, bien que des facteurs externes, 
    tels que la volatilité du secteur et les conditions économiques mondiales, puissent influencer ses résultats futurs.<br/><br/>
    Ce rapport souligne l’importance de surveiller les indicateurs financiers et macroéconomiques pertinents pour suivre l’évolution de {ticker_name} 
    et saisir les opportunités d’investissement en fonction des changements de l’environnement économique.
    """
    # conclusion
    elements.append(Spacer(1, 24))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(conclusion_text, normal_style))


    # Créer le PDF
    doc.build(elements, onFirstPage=create_header(company_info), onLaterPages=footer)




if __name__ == "__main__":
    
    ticker = "RTX"
    ticker_name = get_ticker_name(ticker)
    create_pdf("rapport_institutionnel_banque.pdf", ticker_name)
