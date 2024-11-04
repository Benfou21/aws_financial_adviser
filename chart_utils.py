import streamlit as st
import yfinance as yf



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