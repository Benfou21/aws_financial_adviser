import streamlit as st
import boto3
import os
import json
import uuid
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from io import BytesIO

from reportpdf import download_report

st.set_page_config(layout="wide")

# Récupérer la liste des tickers du S&P 500
@st.cache_data
def get_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    sp500_table = tables[0]
    tickers = sp500_table["Symbol"].tolist()
    return tickers

# def download_report(selected_ticker):
#     buffer = BytesIO()
#     create_pdf(buffer, selected_ticker)
#     buffer.seek(0)
#     return buffer

# Fonction pour récupérer les rapports 10-K et 8-K pour un ticker donné
def get_rapport(ticker_symbole):
    ticker = yf.Ticker(ticker_symbole)
    info_sec = ticker.sec_filings
    dico_10_K = {}
    dico_8_K = {}
    for i in info_sec:
        if i['type'] == '8-K':
            dico_8_K[f"8-K : {i['date']}"] = i["exhibits"]['8-K']
        elif i['type'] == '10-K':
            dico_10_K[f"10-K : {i['date']}"] = i["exhibits"]['10-K']
        else:
            continue
    return dico_10_K, dico_8_K

def market_data(Ticker, info="Close"):
    ticker=yf.Ticker(Ticker)
    sortie=ticker.history(period="2y")
    sortie=sortie[info]
    return sortie.tolist()

def esg_info(Ticker:str ):
    ticker=yf.Ticker(Ticker)
    sortie=ticker.sustainability
    sortie=sortie.to_dict()
    sortie=sortie["esgScores"]["totalEsg"]
    return sortie

def get_latest_roa(ticker: str):
    company = yf.Ticker(ticker)
    
    financials = company.financials
    balance_sheet = company.balance_sheet
    if financials is not None and balance_sheet is not None:
        latest_year = financials.columns[0]
        net_income = financials.loc['Net Income'][latest_year]
        total_assets = balance_sheet.loc['Total Assets'][latest_year]    
        roa = (net_income / total_assets) * 100
        return roa
    else:
        return 

def get_latest_pe_ratio(ticker: str):

    company = yf.Ticker(ticker)
    pe_ratio = company.info.get('trailingPE')
    return pe_ratio

def get_latest_ps_ratio(ticker: str):

    company = yf.Ticker(ticker)
    ps_ratio = company.info.get('priceToSalesTrailing12Months')
    return ps_ratio

def get_beta( Tricker : str):
    company= yf.Ticker(Tricker)
    return company.info.get('beta')

def get_roe(ticker):
    """
    Récupère le ROE (Return on Equity) d'une entreprise à partir de son symbole de ticker.

    Parameters:
        ticker (str): Le symbole du ticker de l'entreprise.

    Returns:
        float: Le ROE de l'entreprise, ou None si la valeur n'est pas disponible.
    """
    try:
        # Récupérer les données de l'entreprise
        stock = yf.Ticker(ticker)

        # Récupérer le bilan et le compte de résultat
        balance_sheet = stock.balance_sheet
        income_statement = stock.financials


        # Vérifier si les données nécessaires sont disponibles
        if 'Net Income' in income_statement.index:
            net_income = income_statement.loc['Net Income'].iloc[0]  # Bénéfice net
            
            # Essayer d'accéder à 'Total Stockholder Equity' ou à d'autres lignes potentielles
            if 'Total Stockholder Equity' in balance_sheet.index:
                total_equity = balance_sheet.loc['Total Stockholder Equity'].iloc[0]
            elif 'Ordinary Shares' in balance_sheet.index:
                total_equity = balance_sheet.loc['Ordinary Shares'].iloc[0]
            elif 'Total Assets' in balance_sheet.index:
                total_equity = balance_sheet.loc['Total Assets'].iloc[0]  # Vérification alternative
            else:
                print("Aucune ligne appropriée pour les capitaux propres trouvée.")
                return None
            
            # Calculer le ROE
            roe = net_income / total_equity
            return roe
        else:
            print("Bénéfice net non disponible pour le ticker:", ticker)
            return None
    except Exception as e:
        print("Une erreur s'est produite:", e)
        return None
    



# Fonction pour obtenir les 8 derniers dividendes d'une entreprise
def get_last_dividends(ticker_symbol, num_dividends=8):
    ticker = yf.Ticker(ticker_symbol)
    dividends = ticker.dividends  # Récupérer les dividendes historiques
    
    # Vérifier s'il y a des données disponibles
    if dividends.empty:
        st.write("Aucun dividende historique trouvé pour ce ticker.")
        return None
    
    # Obtenir les derniers dividendes
    last_dividends = dividends.tail(num_dividends).reset_index()
    last_dividends["Date"] = last_dividends["Date"].dt.strftime('%Y-%m-%d')
    last_dividends.columns = ["Date", "Dividende par Action"]  # Renommer les colonnes pour plus de clarté
    return last_dividends
# Fonction pour obtenir les principaux détenteurs de l'entreprise
def get_top_holders(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    top_holders = ticker.institutional_holders  # Récupérer les top holders
    
    # Vérifier s'il y a des données disponibles
    if top_holders is None or top_holders.empty:
        st.write("Aucun détenteur institutionnel trouvé pour ce ticker.")
        return None
    
    # Supprimer la colonne de dates si elle existe
    if "Date Reported" in top_holders.columns:
        top_holders = top_holders.drop(columns=["Date Reported"])
    
    return top_holders



# Interface utilisateur Streamlit
st.title("Rapports SEC pour les entreprises du S&P 500")



# Sélection du ticker dans la barre latérale
with st.sidebar:
    st.header("Sélection du Ticker")
    sp500_tickers = get_sp500_tickers()
    selected_ticker = st.selectbox("Sélectionnez un ticker du S&P 500 :", sp500_tickers)

    # Obtenir et afficher les rapports pour le ticker sélectionné
    if selected_ticker:
        dico_10K, dico_8K = get_rapport(selected_ticker)

        st.subheader(f"Rapports pour {selected_ticker}")

        with st.expander("Rapport 10-K"):
            if dico_10K:
                for label, url in dico_10K.items():
                    st.markdown(f"[{label}]({url})", unsafe_allow_html=True)
            else:
                st.write("Aucun rapport 10-K trouvé.")

        with st.expander("Rapport 8-K"):
            if dico_8K:
                for label, url in dico_8K.items():
                    st.markdown(f"[{label}]({url})", unsafe_allow_html=True)
            else:
                st.write("Aucun rapport 8-K trouvé.")

        if st.button("Get report"):
            pdf_buffer = download_report(selected_ticker)
            st.download_button(
                label="Télécharger le rapport PDF",
                data=pdf_buffer,
                file_name=f"rapport_{selected_ticker}.pdf",
                mime="application/pdf"
            )


# Configuration des variables d'environnement et des clients AWS
agent_id = os.getenv("AGENT_ID")
agent_alias = os.getenv("AGENT_CHAT_ALIAS")
access_key = os.getenv("AWS_ACCESS_KEY_ID")
secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
session_token = os.getenv("AWS_SESSION_TOKEN")
region_name = 'us-west-2'

# Initialiser le client Bedrock
# bedrock_client = boto3.client(
#     'bedrock-runtime', 
#     region_name=region_name,
#     aws_access_key_id=access_key,
#     aws_secret_access_key=secret_key,
#     aws_session_token=session_token
# )

# Initialiser le runtime client pour l'agent Bedrock
runtime_client = boto3.client(
    service_name="bedrock-agent-runtime",
    region_name=region_name,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    aws_session_token=session_token
)

# Génération d'un identifiant de session unique
session_id = str(uuid.uuid4())

# Fonction pour appeler l'agent avec une requête utilisateur
def call_agent_with_prompt(user_prompt):
    try:
        
        response = runtime_client.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias,
            sessionId=session_id,
            inputText=user_prompt
        )
       
        event_stream = response.get('completion')
        
        response_text = ''

        # Parcourir l'EventStream pour obtenir la réponse
        for event in event_stream:
            if 'chunk' in event:
                chunk = event['chunk']
                content = chunk.get('bytes', b'').decode('utf-8')
                response_text += content
            else:
                print("Événement non traité :", event)

        return response_text

    except Exception as e:
        print("Erreur lors de l'appel à l'agent :", e)
        return None

# Initialiser l'historique de la conversation dans la session
if "conversation" not in st.session_state:
    st.session_state.conversation = []

with st.container():
    # Interface utilisateur Streamlit
    st.title("Chat with AI Agent")

    # Champ de saisie pour le message utilisateur
    user_prompt = st.chat_input("Say something")

    # Vérifier si un message a été entré
    if user_prompt:
        # Ajouter le message utilisateur à la conversation
        st.session_state.conversation.append(("user", user_prompt))
        
        # Appeler l'agent avec le prompt utilisateur
        with st.chat_message("assistant"):
            st.write("Processing your request...")
            
        user_prompt += f"Ticker entreprise : {selected_ticker}"
        response = call_agent_with_prompt(user_prompt)
        
        # Ajouter la réponse de l'agent à la conversation
        if response:
            st.session_state.conversation.append(("assistant", response))
        else:
            st.session_state.conversation.append(("assistant", "No response received from the agent."))

    # Afficher l'historique de la conversation
    for role, message in st.session_state.conversation:
        with st.chat_message(role):
            st.write(message)







st.markdown(
    """
    <style>
    .spacer {
        height: 600px; /* Ajustez la hauteur selon votre besoin */
    }
    </style>
    <div class="spacer"></div>
    """,
    unsafe_allow_html=True,
)


with st.container():

    # Générer des données pour le portefeuille
    
    market_dt = market_data(selected_ticker)
    closing_value=np.array(market_dt)
    x= np.linspace(0, 20, len(market_dt))

    volume_value=np.array(market_data(selected_ticker, info="Volume"))
    
    col11, col21 = st.columns(2)

    with col11:

        fig1 = go.Figure()

        # Courbe pour la valeur du portefeuille
        fig1.add_trace(go.Scatter(x=x, y=closing_value, mode='lines', name=f'Valeur de {selected_ticker}', 
                                line=dict(shape='spline', smoothing=0.5, color='#A8DADC', width=4)))  # Couleur douce et ligne plus épaisse
        fig1.update_layout(title=f"Valeur de l'actif {selected_ticker}", yaxis=dict(title='Prix'),)
        


        #                 xaxis=dict(
        # # Courbe pour la valeur du S&P 500
        # fig1.add_trace(go.Scatter(x=x, y=volume_value, mode='lines', name='S&P 500', 
        #                         line=dict(shape='spline', smoothing=0.5, color='#FF7F50', width=4)))  # Couleur orangée pour l'indice

        # # Mise à jour du layout pour correspondre au thème sombre et personnalisation
        # fig1.update_layout(title='Valeur du portefeuille vs S&P 500',
        #                 xaxis=dict(
        #         title=None,  # Aucune chaîne vide
        #         showgrid=False,
        #         tickfont=dict(color='#f3faf1'),  # Couleur des ticks et labels de l'axe des X
        #         showline=False,  # Désactiver la ligne de l'axe des X
        #         zeroline=False,  # Désactiver la ligne de base à zéro de l'axe des X
        #         automargin=False  # Ne pas allouer d'espace pour un titre
        #     ),
        #     yaxis=dict(
        #         title='',
        #         showgrid=False,  # Retirer la grille si nécessaire
        #         tickfont=dict(color='#459ad6', size=14),
        #         showline=False,  # Désactiver la ligne de l'axe des Y
        #         zeroline=False  # Désactiver la ligne de base à zéro de l'axe des Y
        #     ),
        #     margin=dict(l=0, r=10, t=50, b=40),
        #                 plot_bgcolor='rgba(0, 0, 0, 0)',
        #                 paper_bgcolor='#121212',
        #                 font=dict(color='#FFFFFF'),
        #                 showlegend=True,
        #                 legend=dict(
        #         orientation="h",  # Légende horizontale
        #         x=0.5,  # Centre horizontalement
        #         xanchor="center",  # Ancrer au centre horizontalement
        #         y=-0.2,  # Placer sous le graphique
        #         yanchor="bottom"  # Ancrer en bas
        #     ))  # Afficher la légende pour différencier les courbes

        # Afficher le graphique
        st.plotly_chart(fig1, use_container_width=True)

        # Ajouter une légende pour les résultats simulés
        st.markdown("<p style='font-size: 18px; margin-top: 20px; font-weight: bold; margin-bottom: -20px;'>RÉSULTATS : DONNÉES SIMULÉES</p>", unsafe_allow_html=True)




        # Couleurs pour les titres et les valeurs
        title_color = "#0D47A1"  # Très foncé pour les titres
        data_color = "#1976D2"   # Plus clair pour les données
        separator_color = "#E0E0E0"  # Couleur de la ligne séparatrice

        # Créer trois colonnes
        col1, col2, col3 = st.columns(3)

        # Première colonne (ESG)
        with col1:
            st.markdown(f"<h3 style='color: {title_color}; margin-bottom: -10px;'>ESG</h3>", unsafe_allow_html=True)  # Réduire l'écart entre le titre et la barre
            st.markdown(f"<hr style='border:1px solid {separator_color}; margin-top: -5px; margin-bottom: 5px;'/>", unsafe_allow_html=True)  # Ligne séparatrice avec marges ajustées
            st.markdown(f"<p style='color: {data_color}; font-size: 48px; margin-top: -25px; font-weight: bold;'>{esg_info(selected_ticker)}</p>", unsafe_allow_html=True)

        # Deuxième colonne (Beta)
        with col2:
            st.markdown(f"<h3 style='color: {'#76496b'}; margin-bottom: -10px;'>BETA</h3>", unsafe_allow_html=True)
            st.markdown(f"<hr style='border:1px solid {separator_color}; margin-top: -5px; margin-bottom: 5px;'/>", unsafe_allow_html=True)  # Ligne séparatrice avec marges ajustées
            st.markdown(f"<p style='color: {'#a74c9e'}; font-size: 48px; margin-top: -25px; font-weight: bold;'>{get_beta(selected_ticker)}</p>", unsafe_allow_html=True)

        # Troisième colonne (PS)
        with col3:
            st.markdown(f"<h3 style='color: {'#ebbbc5'}; margin-bottom: -10px;'>PS</h3>", unsafe_allow_html=True)  # Réduire l'écart entre le titre et la barre
            st.markdown(f"<hr style='border:1px solid {separator_color}; margin-top: -5px; margin-bottom: 5px;'/>", unsafe_allow_html=True)  # Ligne séparatrice avec marges ajustées
            st.markdown(f"<p style='color: {'#f6c2cf'}; font-size: 48px; margin-top: -25px; font-weight: bold;'>{round(get_latest_ps_ratio(selected_ticker),1)}</p>", unsafe_allow_html=True)

        last_dividends_df = get_last_dividends(selected_ticker)
        if last_dividends_df is not None:
            st.write(f"Les 8 derniers dividendes de {selected_ticker.upper()}:")
            st.table(last_dividends_df)







    #autre graphique 

    with col21:



        fig2 = go.Figure()


        # Courbe pour la valeur du S&P 500
        fig2.add_trace(go.Scatter(x=x, y=volume_value, mode='lines', name='S&P 500', 
                                line=dict(shape='spline', smoothing=0.5, color='#FF7F50', width=4)))  # Couleur orangée pour l'indice
        

        fig2.update_layout(title='Volume échanger',
                        yaxis=dict(title='Volume'),)

        # Afficher le second graphique
        st.plotly_chart(fig2, use_container_width=True)


        # Simuler des données pour Return, R-Squared et CAGR
        return_value = round(np.random.uniform(5, 15), 2)
        r_squared_value = round(np.random.uniform(0.7, 0.99), 2)
        cagr_value = round(np.random.uniform(5, 10), 2)

        st.markdown("<p style='font-size: 18px; margin-top: 20px; font-weight: bold; margin-bottom: -20px;'>RÉSULTATS : DONNÉES SIMULÉES</p>", unsafe_allow_html=True)


        # Créer trois colonnes supplémentaires pour Return, R-Squared, et CAGR
        col4, col5, col6 = st.columns(3)

        # Quatrième colonne (PE)
        with col4:
            st.markdown(f"<h3 style='color: #a7f6e0; margin-bottom: -10px;'>PE</h3>", unsafe_allow_html=True)  # Réduire l'écart entre le titre et la barre
            st.markdown(f"<hr style='border:1px solid {separator_color}; margin-top: -5px; margin-bottom: 5px;'/>", unsafe_allow_html=True)  # Ligne séparatrice avec marges ajustées
            st.markdown(f"<p style='color: #bcede7; font-size: 48px; margin-top: -25px; font-weight: bold;'>{round(get_latest_pe_ratio(selected_ticker),2)}</p>", unsafe_allow_html=True)

        # Cinquième colonne (ROA)
        with col5:
            st.markdown(f"<h3 style='color: #d5f2b6; margin-bottom: -10px;'>ROA</h3>", unsafe_allow_html=True)
            st.markdown(f"<hr style='border:1px solid {separator_color}; margin-top: -5px; margin-bottom: 5px;'/>", unsafe_allow_html=True)  # Ligne séparatrice avec marges ajustées
            st.markdown(f"<p style='color: #e0ecbc; font-size: 48px; margin-top: -25px; font-weight: bold;'>{round(get_latest_roa(selected_ticker),1)}</p>", unsafe_allow_html=True)

        # Sixième colonne (ROE)
        with col6:
            st.markdown(f"<h3 style='color: #8ef5c8; margin-bottom: -10px;'>ROE</h3>", unsafe_allow_html=True)  # Réduire l'écart entre le titre et la barre
            st.markdown(f"<hr style='border:1px solid {separator_color}; margin-top: -5px; margin-bottom: 5px;'/>", unsafe_allow_html=True)  # Ligne séparatrice avec marges ajustées
            st.markdown(f"<p style='color: #9ce4c6; font-size: 48px; margin-top: -25px; font-weight: bold;'>{round(get_roe(selected_ticker),2)}</p>", unsafe_allow_html=True)


        top_holders_df = get_top_holders(selected_ticker)
        if top_holders_df is not None:
            st.write(f"Principaux détenteurs institutionnels de {selected_ticker.upper()}:")
            st.table(top_holders_df)




###############################################################################################
# # Titre de l'application
# st.title("Affichage des Dividendes et Principaux Détenteurs d'une Entreprise")

# # Entrée utilisateur pour le ticker
# ticker_symbol = st.text_input("Entrez le ticker de l'entreprise", "MSFT")

# # Affichage des données en deux colonnes
# if ticker_symbol:
#     # Créer deux colonnes pour l'affichage
#     col1, col2 = st.columns(2)
    
#     # Afficher les 8 derniers dividendes dans la première colonne
#     with col1:
        
    
#     # Afficher les principaux détenteurs dans la deuxième colonne
#     with col2:
#         

################################################################################################