import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import openai
from itertools import cycle
import base64

@st.cache(show_spinner=False)
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

    prompt_text = f"Tu es un spécialiste du marketing de marque. Pour un client, tu dois trouver à partir du texte de la home page et de ta connaissance du nom de marque à quel secteur d’activité il appartient. Tu peux choisir un à deux secteurs d’activité maximum. Si tu en choisi deux, sépare les avec une barre comme celle-ci : / Si tu ne sais pas ou que tu as un doute, mets “Autres”. Tu ne dois pas ajouter de commentaire, de rédaction ou autre, uniquement le ou les secteurs d’activités que tu as choisi. Voici les secteurs d’activité que tu dois choisir : Alimentaire Animaux Art et culture Associations Automobile B2B Banque / Assurance Cosmétique Divertissement Energie Gaming High Tech Home Immobilier Luxe Prêt-à-porter Retail Restauration Sport équipement Travel. Voici le nom du site : {domain}. Voici le texte de la home page : {homepage_content}"

    messages = [{"role": "system", "content": prompt_text}]
    chat = openai.ChatCompletion.create(model="gpt-4", messages=messages)
    return chat.choices[0].message.content

def identify_client_type(homepage_content, api_key):
    if homepage_content == "site n'existe plus":
        return "site n'existe plus"
    openai.api_key = api_key

    prompt_text = f"Tu es un expert du domaine du marketing. Je vais te fournir un texte qui est le contenu d’une homepage de site. A partir de celui-ci, je souhaite que tu me choisisse l’un de ces termes : B to B (c’est à dire business to business), B to C (c’est à dire business to customers), B to B to C (c’est à dire des entreprises qui commercialisent des biens et des services auprès de sociétés tierces, qui les revendent elles-mêmes au grand public). Tu peux choisir un seul de ces 3 termes. Tu n’a pas le droit d’ajouter des commentaires, fait juste un choix entre : B to B, B to C et B to B to C. Voici le contenus de la homepage : {homepage_content}"

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

    api_keys = [api_key_1, api_key_2]
    api_key_cycle = cycle(api_keys)

    # Formulaire pour les mots clés
    st.subheader('Formulaire pour les domaines')
    with st.form(key='domain_form'):
        domain_input = st.text_input('Saisissez des domaines (séparés par des virgules)')
        submit_button = st.form_submit_button(label='Soumettre')
    domains = [d.strip() for d in domain_input.split(',')] if domain_input else []

    if all(api_keys):
        data = pd.DataFrame()
        if csv_file:
            data = pd.read_csv(csv_file)
        if domains:
            domains_data = pd.DataFrame(domains, columns=['domaine du site'])
            data = pd.concat([data, domains_data], ignore_index=True)

        data['contenu home page'] = data['domaine du site'].apply(get_homepage_content)
        data['catégorisation du site'] = data.apply(lambda row: categorize_site(row['domaine du site'], row['contenu home page'], next(api_key_cycle)), axis=1)
        data['Business target'] = data['contenu home page'].apply(lambda x: identify_client_type(x, next(api_key_cycle)))

        st.dataframe(data)
        st.markdown(get_table_download_link(data), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
