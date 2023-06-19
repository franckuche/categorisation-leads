import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import openai
from itertools import cycle
import base64

def get_homepage_content(url):
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'http://' + url
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.text[:5000]

def categorize_site(domain, content, api_key):
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

    api_keys = [api_key_1, api_key_2, api_key_3]
    api_key_cycle = cycle(api_keys)

    if csv_file and all(api_keys):
        data = pd.read_csv(csv_file)
        data['contenu home page'] = data['domaine du site'].apply(get_homepage_content)
        data['catégorisation du site'] = data.apply(lambda row: categorize_site(row['domaine du site'], row['contenu home page'], next(api_key_cycle)), axis=1)

        st.dataframe(data)
        st.markdown(get_table_download_link(data), unsafe_allow_html=True)

if __name__ == "__main__":
    main()

