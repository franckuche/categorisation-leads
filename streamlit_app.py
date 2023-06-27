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
    url = 'http://' + url if 'http://' not in url and 'https://' not in url else url
    try:
        response = requests.get(url)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text(strip=True)[:5000]
    except requests.exceptions.RequestException as e:
        st.error(f"Error retrieving website content: {e}")
        return "site does not exist"
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return "site does not exist"

def categorize_site(domain, home_page_content, api_key):
    try:
        openai.api_key = api_key
        response = openai.Classification.create(
            search_model="davinci",
            documents=["E-commerce", "Portfolio", "Educational", "News or Magazine", "Community Forum", "Nonprofit", "Entertainment", "Technology", "Personal Blog", "Web Portal", "Wiki or Knowledge", "Social Media", "Business Brochure"],
            query=home_page_content,
        )
        return response['choices'][0]['label']
    except Exception as e:
        st.error(f"Error categorizing site: {e}")
        return "error in categorizing"

def identify_client_type(home_page_content, api_key):
    try:
        openai.api_key = api_key
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": home_page_content},
        ]
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"Error identifying client type: {e}")
        return "error in identifying client type"

def get_marketing_words(home_page_content, api_key):
    try:
        openai.api_key = api_key
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": home_page_content},
        ]
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"Error getting marketing words: {e}")
        return "error in getting marketing words"

def get_table_download_link(df):
    try:
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}">Download csv file</a>'
        return href
    except Exception as e:
        st.error(f"Error preparing download link: {e}")
        return ""

def process_in_batches(df, func, api_key_cycle, batch_size, pause):
    results = []
    for i in range(0, len(df), batch_size):
        batch = df[i:i+batch_size]
        try:
            batch_results = func(batch, api_key_cycle)
            results.extend(batch_results)
            time.sleep(pause)
        except Exception as e:
            st.error(f"Error processing in batches: {e}")
            results.extend(["error in processing"]*len(batch))
    return results

def categorize_batch(batch, api_key_cycle):
    return batch.apply(lambda row: categorize_site(row['domaine du site'], row['contenu home page'], next(api_key_cycle)), axis=1)

def identify_client_type_batch(batch, api_key_cycle):
    return batch['contenu home page'].apply(lambda x: identify_client_type(x, next(api_key_cycle)))

def get_marketing_words_batch(batch, api_key_cycle):
    return batch['contenu home page'].apply(lambda x: get_marketing_words(x, next(api_key_cycle)))

def main():
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

    if all(api_keys):
        data = pd.DataFrame()
        if csv_file:
            data = pd.read_csv(csv_file)
        elif domains:
            data = pd.DataFrame(domains, columns=['domaine du site'])

        rate_limit = 18  
        batch_size = rate_limit
        pause_time = 60  

        data['contenu home page'] = data['domaine du site'].apply(get_homepage_content)
        data['catégorisation du site'] = process_in_batches(data, categorize_batch, api_key_cycle, batch_size, pause_time)
        data['Business target'] = process_in_batches(data, identify_client_type_batch, api_key_cycle, batch_size, pause_time)
        data['Marketing words'] = process_in_batches(data, get_marketing_words_batch, api_key_cycle, batch_size, pause_time)

        st.dataframe(data)
        st.markdown(get_table_download_link(data), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
