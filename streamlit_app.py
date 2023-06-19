import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import openai
from itertools import cycle
import base64
import concurrent.futures

@st.cache
def get_homepage_content(url):
    url = 'http://' + url if 'http://' not in url else url

    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text(strip=True)[:5000]  # on limite à 5000 caractères
    except:
        return "site n'existe plus"

def categorize_site(domain, homepage_content, api_key):
    if homepage_content == "site n'existe plus":
        return "site n'existe plus"   
    openai.api_key = api_key

    prompt_text = f"Tu es un spécialiste du marketing de marque. Pour un client, tu dois trouver à partir du texte de la home page et de ta connaissance du nom de marque à quel secteur d’activité il appartient. Tu peux choisir un à deux secteurs d’activité maximum. Si tu en choisi deux, sépare les avec une barre comme celle-ci : / Si tu ne sais pas ou que tu as un doute, mets “Autres”. Tu ne dois pas ajouter de commentaire, de rédaction ou autre, uniquement le ou les secteurs d’activités que tu as choisi. Voici les secteurs d’activité que tu dois choisir : Alimentaire Animaux Art et culture Associations Automobile B2B Banque / Assurance Cosmétique Divertissement Energie Gaming High Tech Home Immobilier Luxe Prêt-à-porter Retail Restauration Sport équipement Travel. Voici le nom du site : {domain}. Voici le texte de la home page : {content}"

    messages = [{"role": "system", "content": prompt_text}]
    chat = openai.ChatCompletion.create(model="gpt-4", messages=messages)
    return chat.choices[0].message.content

def get_table_download_link(df):
    csv = df.to_csv(index=False, encoding='utf-8-sig')  # Explicitly encode to UTF-8
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="output.csv">Télécharger le CSV</a>'
    return href

def main():
    st.title('Scraping et catégorisation des sites web')

    csv_file = st.file_uploader('Importez votre CSV', type=['csv'])
    
    st.subheader('OpenAI API Keys')
    api_key_1 = st.text_input('Insérer la première clé API OpenAI', type='password')
    api_key_2 = st.text_input('Insérer la deuxième clé API OpenAI', type='password')
    api_key_3 = st.text_input('Insérer la troisième clé API OpenAI', type='password')
    api_key_4 = st.text_input('Insérer la quatrième clé API OpenAI', type='password')
    api_key_5 = st.text_input('Insérer la cinquième clé API OpenAI', type='password')
    api_key_6 = st.text_input('Insérer la sixième clé API OpenAI', type='password')
    api_key_7 = st.text_input('Insérer la septième clé API OpenAI', type='password')
    api_key_8 = st.text_input('Insérer la huitième clé API OpenAI', type='password')
    api_key_9 = st.text_input('Insérer la neuvième clé API OpenAI', type='password')
    api_key_10 = st.text_input('Insérer la dixième clé API OpenAI', type='password')

    api_keys = [api_key_1, api_key_2, api_key_3, api_key_4, api_key_5, api_key_6, api_key_7, api_key_8, api_key_9, api_key_10]
    api_key_cycle = cycle(api_keys)

    if csv_file and all(api_keys):
        data = pd.read_csv(csv_file)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            data['contenu home page'] = list(executor.map(get_homepage_content, data['domaine du site']))
            data['catégorisation du site'] = list(executor.map(categorize_site, data['domaine du site'], data['contenu home page'], api_key_cycle))

        st.dataframe(data)
        st.markdown(get_table_download_link(data), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
