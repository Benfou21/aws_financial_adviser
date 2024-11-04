
import logging
import boto3
from botocore.exceptions import ClientError
import json
import os
from dotenv import load_dotenv


import yfinance as yf
import pandas as pd

import requests
from bs4 import BeautifulSoup



load_dotenv()
import uuid
session_id = str(uuid.uuid4())

ticker_name = "RTX" # mettre la variable choisi dans la liste

access_key = os.getenv("AWS_ACCESS_KEY_ID")
secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
session_token = os.getenv("AWS_SESSION_TOKEN")
region_name = os.getenv("AWS_DEFAULT_REGION")

bedrock_client = boto3.client('bedrock-runtime', region_name=region_name,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    aws_session_token=session_token  )

agent_id = os.getenv("AGENT_ID")
agent_alias = os.getenv("AGENT_ALIAS")






# Fonction pour l'analyse de sentiment en utilisant l'API Messages de Claude 3
def analyze_sentiment(text):
    try:
        # Préparation de la requête pour l'API Messages
        response = bedrock_client.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 50,
                "temperature": 0.5,
                "messages": [
                    {"role": "user", "content": f"Analyse le sentiment de ce texte : \"{text}\""}
                ]
            })
        )

        # Affichage de la réponse brute pour diagnostic
        response_body = json.loads(response['body'].read().decode('utf-8'))
        
        # Vérification de la structure de la réponse et extraction du texte
        content = response_body.get("content")
        if isinstance(content, list):
            sentiment_analysis = " ".join([part["text"] for part in content if "text" in part])
        else:
            sentiment_analysis = content  # Directement utiliser le contenu si c'est une chaîne
        
        return sentiment_analysis or "Pas de résultat détecté"
    except Exception as e:
        print("Erreur :", e)
        return None




def call_agent_with_prompt(user_prompt,agent_alias):
    runtime_client=boto3.client(
        service_name="bedrock-agent-runtime",
        region_name=region_name,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token  # Facultatif
    ),
    try:
        
        response = runtime_client[0].invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias,  #agent alias
            sessionId=session_id,
            inputText=user_prompt,
            #enableTrace=True
        )
        event_stream = response.get('completion')
        response_text = ''

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
    

# Fonction pour extraire le texte principal de l'article
def extract_article_text(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extraction des paragraphes de l'article
    paragraphs = soup.find_all('p')
    article_text = ' '.join([para.get_text() for para in paragraphs])
    return article_text


def analyze_subject_sentiment(text):
    try:
        response = bedrock_client.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "temperature": 0.5,
                "messages": [
                    {"role": "user", "content": f"Donne uniquement sujet principal de cet article ainsi que le sentiment du text associé sans explicatioN: \"{text}\""}
                ]
            })
        )
        
        response_body = json.loads(response['body'].read().decode('utf-8'))
        content = response_body.get("content")
        
        subject_analysis = content[0]["text"] if content else "Pas de sujet détecté"
        return subject_analysis
    
    except Exception as e:
        print("Erreur d'analyse du sujet :", e)
        return None
    


# Fonction principale pour obtenir les informations d'actualité avec sujet et sentiment
def get_news_with_sentiment(ticker_name):
    
    ticker = yf.Ticker(ticker_name)
    news = ticker.news
    sentiment_output = ''
    
    for item in news:
        title = item.get('title')
        link = item.get('link')
        source = item.get('publisher')
        
        # Extraire le texte de l'article
        article_text = extract_article_text(link)
        
        # Analyser le sujet et le sentiment
        subject_sentiment = analyze_subject_sentiment(article_text)
        
        sentiment_output += title + subject_sentiment
        

    return sentiment_output







def caption_summary(text,max_token):
    try:
        response = bedrock_client.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_token,
                "temperature": 0.5,
                "messages": [
                    {"role": "user", "content": f"Tu es un macro économiste, rédige un résumé des points clés  macro économique des différents sujets, avec détails (ex chiffres) : Insère `<br/>` pour un retour à la ligne simple et utilise plusieurs `<br/><br/>` pour des sauts de ligne plus importants.\"{text}\""}
                ]
            })
        )

        response_body = json.loads(response['body'].read().decode('utf-8'))
        content = response_body.get("content")
        
        sentiment_analysis = content[0]["text"] if content else "Pas de sentiment détecté"
        return sentiment_analysis
    
    except Exception as e:
        print("Erreur d'analyse de sentiment :", e)





def get_macro_news() :
    tickers = {
        "^GSPC": "S&P 500 - Indice Boursier",
        "DX-Y.NYB": "Indice du Dollar Américain",
        "^TNX": "Taux des Obligations à 10 ans",
        "GC=F": "Prix de l'Or",
        "CL=F": "Prix du Pétrole (WTI)",
        "^VIX": "VIX - Volatilité des Marchés"
    }
    
    output_text = ""
    for ticker_symbol, description in tickers.items():
        ticker = yf.Ticker(ticker_symbol)
        news_items = ticker.news
        
        for item in news_items[:2]:
            
            text_article = extract_article_text(item["link"])
            if text_article != "Thank you for your patience. Our engineers are working quickly to resolve the issue." :
                
                text = caption_summary(text_article,150)
                
                output_text += text
    caption_macro = caption_summary(output_text,max_token=300)
    return caption_macro







def gat_analyse_macro(output_macro):

    agent_alias = os.getenv("AGENT_MACRO_ALIAS")

    # Exemple d'appel avec un *prompt* utilisateur
    user_prompt = "Réalise l'analyse macroéconimque en détail ? Insère `<br/>` pour un retour à la ligne simple et utilise plusieurs `<br/><br/>` pour des sauts de ligne plus importants."
    promt = user_prompt + "Context macro suppélementaire :" + output_macro 
    response_macro = call_agent_with_prompt(promt,agent_alias)
    
    return output_macro + response_macro



def profil_resp_data(ticker_name):
    
    agent_alias = os.getenv("AGENT_PROFIL_ALIAS")

    user_prompt = f"Présente l'entreprise {ticker_name} ? Fais le en Français. Fais une partie aussi sur l'analyse de la concurrence. Insère `<br/>` pour un retour à la ligne simple et utilise plusieurs `<br/><br/>` pour des sauts de ligne plus importants."
    
    response_profil = call_agent_with_prompt(user_prompt,agent_alias)

    return response_profil






def finance_resp_data(ticker_name):
    agent_alias = os.getenv("AGENT_FINANCE_ALIAS")


    user_prompt = f"Réalise l'analyse de l'état financère de l'entreprise {ticker_name} ? Insère `<br/>` pour un retour à la ligne simple et utilise plusieurs `<br/><br/>` pour des sauts de ligne plus importants."
    
    response_fin = call_agent_with_prompt(user_prompt,agent_alias)

    return response_fin







def sentiment_anal(ticker_name, sentiment_output):
    
    agent_alias = os.getenv("AGENT_SENTIMENT_ALIAS")
    user_prompt = f"Réalise l'analyse du sentiment de marché de l'entreprise {ticker_name} avec comme context les dernières actualité et leurs sentiments? Donne aussi quelques données pour affirmer tes propos. Insère `<br/>` pour un retour à la ligne simple et utilise plusieurs `<br/><br/>` pour des sauts de ligne plus importants."
    promt = user_prompt + "Context actualité et sentiments : " + sentiment_output
    response_sent = call_agent_with_prompt(promt,agent_alias)

    return response_sent



def get_officiel(ticker_symbol):
    ticker=yf.Ticker(ticker_symbol)
    dico_officiers=ticker.info['companyOfficers']
    df=pd.DataFrame(dico_officiers)
    for i in ["maxAge","yearBorn","fiscalYear","exercisedValue","unexercisedValue"]:
        df=df.drop(i,axis=1)
    return df

def get_holders(ticker_symbol):
    ticker=yf.Ticker(ticker_symbol)
    return pd.DataFrame(ticker.institutional_holders)


def holders_anal(ticker_name):
    
    board_output = get_holders(ticker_name).to_string() + get_officiel(ticker_name).to_string() 
    agent_alias = os.getenv("AGENT_BOARD_ALIAS")
    user_prompt = "Réalise une analyse du conseil de l'entreprise en français, sa mixité, ses niveaux de salaire ainsi qu'une rapide analyse des holders. Insère `<br/>` pour un retour à la ligne simple et utilise plusieurs `<br/><br/>` pour des sauts de ligne plus importants." 
    promt = user_prompt + "Information sur le conseil et holders :" + board_output 
    response2 = call_agent_with_prompt(promt,agent_alias)

    return response2





def risk_anal(ticker_name,output_macro):
    
    agent_alias = os.getenv("AGENT_RISK_ALIAS")


    user_prompt = f"Réalise l'analyse des risques et opportunité de l'entreprise {ticker_name} selon le context macroéconomic et la valeur beta kpi. Insère `<br/>` pour un retour à la ligne simple et utilise plusieurs `<br/><br/>` pour des sauts de ligne plus importants."
    promt = user_prompt + "Context macroeconomic : " + output_macro
    response_risk = call_agent_with_prompt(promt,agent_alias)

    return response_risk




def tot_anal(ticker_name,response_risk,response_profil,response_macro,response_fin,response_sent):
    
    tot_reponse = response_risk + response_profil + response_macro + response_fin + response_sent

    agent_alias = os.getenv("AGENT_RESUME_ALIAS")
    user_prompt = f"Réalise un récapitulatif et un conseil de stratégie vis à vis de l'entreprise {ticker_name}. Donne un avis de BUY, SELL ou HOLD avec tes informations d'un point de vue d'un analyste financier. Insère `<br/>` pour un retour à la ligne simple et utilise plusieurs `<br/><br/>` pour des sauts de ligne plus importants."
    promt = user_prompt + "Context :" + tot_reponse
    response = call_agent_with_prompt(promt,agent_alias)

    return response