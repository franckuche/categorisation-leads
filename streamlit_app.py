import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import openai
from itertools import cycle
import base64
import time

@st.cache(show_spinner=False)
def get_homepage_content(url):
    try:
        if not isinstance(url, str) or url == "":
            return "L'URL n'est pas valide"
        url = 'http://' + url if 'http://' not in url and 'https://' not in url else url

        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text(strip=True)[:5000]
    except Exception as e:
        return f"Erreur lors de la récupération du contenu de la page d'accueil : {str(e)}"

def categorize_site(domain, homepage_content, api_key):
    try:
        if homepage_content == "site n'existe plus":
            return "site n'existe plus"    
        openai.api_key = api_key
        prompt_text = f"Tu es un spécialiste du marketing de marque. Pour un client, tu dois trouver à partir du texte de la home page et de ta connaissance du nom de marque à quel secteur d’activité il appartient. Tu peux choisir un à deux secteurs d’activité maximum. Si tu en choisi deux, sépare les avec une barre comme celle-ci : / Si tu ne sais pas ou que tu as un doute, mets “Autres”. Tu ne dois pas ajouter de commentaire, de rédaction ou autre, uniquement le ou les secteurs d’activités que tu as choisi. Voici les secteurs d’activité que tu dois choisir : Alimentaire Animaux Art et culture Associations Automobile B2B Banque / Assurance Cosmétique Divertissement Energie Gaming High Tech Home Immobilier Luxe Prêt-à-porter Retail Restauration Sport équipement Travel. Voici le nom du site : {domain}. Voici le texte de la home page : {homepage_content}"
        messages = [{"role": "system", "content": prompt_text}]
        chat = openai.ChatCompletion.create(model="gpt-4", messages=messages)
        return chat.choices[0].message.content
    except Exception as e:
        return f"Erreur lors de la catégorisation du site : {str(e)}"

def identify_client_type(homepage_content, api_key):
    try:
        if homepage_content == "site n'existe plus":
            return "site n'existe plus"
        openai.api_key = api_key

        prompt_text = f"Tu es un expert du domaine du marketing. Je vais te fournir un texte qui est le contenu d’une homepage de site. A partir de celui-ci, je souhaite que tu me choisisse l’un de ces termes : B to B (c’est à dire business to business), B to C (c’est à dire business to customers), B to B to C (c’est à dire des entreprises qui commercialisent des biens et des services auprès de sociétés tierces, qui les revendent elles-mêmes au grand public). Tu peux choisir un seul de ces 3 termes. Tu n’a pas le droit d’ajouter des commentaires, fait juste un choix entre : B to B, B to C et B to B to C. Voici le contenus de la homepage : {homepage_content}"
        messages = [{"role": "system", "content": prompt_text}]
        chat = openai.ChatCompletion.create(model="gpt-4", messages=messages)
        return chat.choices[0].message.content
    except Exception as e:
        return f"Erreur lors de l'identification du type de client : {str(e)}"

def get_table_download_link(df):
    try:
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="output.csv">Télécharger le CSV</a>'
        return href
    except Exception as e:
        return f"Erreur lors de la création du lien de téléchargement : {str(e)}"

def get_marketing_words(homepage_content, api_key):
    try:
        if homepage_content == "site n'existe plus":
            return "site n'existe plus"
        openai.api_key = api_key

        prompt_text = f"Tu es un expert en secteur d'activités d'entreprise. Je vais te fournir un texte qui est le contenu d’une homepage de site. A partir de celle-ci, j’ai besoin que tu me catégories la home page en fonction du métier qui est le plus proche du contenu. Tu devras toujours donné ta réponse au masculin. Par exemple, si tu as un contenu lié au métier de professeur, tu dois dire professeur et non professeure tu m'expliques avec une phrase de 3 ou 4 mots maximum l'activité de l'entreprise. Voici le contenus de la homepage : {homepage_content}. Quel est le type de métier relier à cette page ? Donne moi ta réponse en 2-3 mots maximum. Ne met jamais de ponctuation"
    
        messages = [{"role": "system", "content": prompt_text}]
        chat = openai.ChatCompletion.create(model="gpt-4", messages=messages)
        return chat.choices[0].message.content
    except Exception as e:
        return f"Erreur lors de la récupération des mots marketing : {str(e)}"

def main():
    try:
        st.title('Scraping et catégorisation des sites web')

        csv_file = st.file_uploader('Importez votre CSV', type=['csv'])

        st.subheader('OpenAI API Keys')
        api_key_1 = st.text_input('Insérer la première clé API OpenAI', type='password')
        api_key_2 = st.text_input('Insérer la deuxième clé API OpenAI', type='password')

        api_keys = [api_key_1, api_key_2]
        api_key_cycle = cycle(api_keys)

        st.subheader('Formulaire pour les domaines')
        with st.form(key='domain_form'):
            domain_input = st.text_input('Saisissez des domaines (séparés par des virgules)')
            submit_button = st.form_submit_button(label='Soumettre')
        domains = [d.strip() for d in domain_input.split(',')] if domain_input else []

        if all(api_keys) and (csv_file or domains):
            data = pd.DataFrame()
            if csv_file:
                try:
                    data = pd.read_csv(csv_file, encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        data = pd.read_csv(csv_file, encoding='latin-1')
                        data.to_csv(csv_file, encoding='utf-8', index=False)
                        data = pd.read_csv(csv_file, encoding='utf-8')
                    except Exception as e:
                        st.error(f"Une erreur s'est produite lors de la lecture du fichier CSV : {str(e)}")
                        return
            if domains:
                if 'Domain' not in data.columns:
                    data['Domain'] = domains
                else:
                    data['Domain'] = data['Domain'].append(pd.Series(domains), ignore_index=True)

            data['Homepage Content'] = data['Domain'].apply(get_homepage_content)
            time.sleep(1)

            for column, function in zip(['Sector', 'Client Type', 'Marketing Words'], [categorize_site, identify_client_type, get_marketing_words]):
                data[column] = data.apply(lambda row: function(row['Domain'], row['Homepage Content'], next(api_key_cycle)), axis=1)
                time.sleep(1)

            st.write(data)
            st.markdown(get_table_download_link(data), unsafe_allow_html=True)
        elif not all(api_keys):
            st.error('Veuillez insérer les clés API OpenAI')
    except Exception as e:
        st.error(f"Une erreur s'est produite : {str(e)}")

if __name__ == "__main__":
    main()
