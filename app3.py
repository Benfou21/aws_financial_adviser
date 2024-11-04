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
from chart_utils import *
from bedrock_agents import call_agent_with_prompt


# var d'environnement et des clients AWS
agent_id = os.getenv("AGENT_ID")
agent_alias = os.getenv("AGENT_CHAT_ALIAS")
access_key = os.getenv("AWS_ACCESS_KEY_ID")
secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
session_token = os.getenv("AWS_SESSION_TOKEN")
region_name = os.getenv("AWS_DEFAULT_REGION") 



session_id = str(uuid.uuid4())



st.set_page_config(layout="wide")

# Récupérer la liste des tickers du S&P 500
@st.cache_data
def get_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    sp500_table = tables[0]
    tickers = sp500_table["Symbol"].tolist()
    return tickers





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
        
        if st.button("Générer rapport d'analyse"):
            pdf_buffer = download_report(selected_ticker)
            st.download_button(
                label="Télécharger le rapport PDF",
                data=pdf_buffer,
                file_name=f"rapport_{selected_ticker}.pdf",
                mime="application/pdf"
            )






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
        response = call_agent_with_prompt(user_prompt,agent_alias)
        
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



