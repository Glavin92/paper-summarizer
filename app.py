import os
from flask import Flask, render_template, request, redirect, url_for
import bibtexparser
import requests
from bs4 import BeautifulSoup
import time
import json

app = Flask(__name__)

def fetch_author_url(name):
    # Replace spaces with '+' for URL encoding
    url = f'https://dblp.org/search/author/api?q={name.replace(" ", "+")}&format=json'
    response = requests.get(url)
    print(response)
    
    if response.status_code != 200:
        return None  # Handle API failure
    try:
        data = response.json()
        # Check if there are hits
        if data['result']['hits']['hit']:
            # Return the URL of the first author found
            return data['result']['hits']['hit'][0]['info']['url']
    except (KeyError, IndexError):
        return None  # Handle cases where the expected data structure doesn't exist
    return None

def fetch_papers(author_url):
    response = requests.get(author_url)
    if response.status_code != 200:
        return []  # If the request fails, return an empty list
    
    soup = BeautifulSoup(response.text, 'html.parser')
    papers = []
    seen = set()  # Set to track unique papers by title or other criteria

    results = soup.find_all('li', class_='entry')

    for result in results:
        title_tag = result.find('span', class_='title')
        title = title_tag.text.strip() if title_tag else "No Title"
        
        # Check if the title is already seen
        if title in seen:
            continue  # Skip duplicate entries
        seen.add(title)

        author_tags = result.find_all('span', itemprop='author')
        authors = [author.text.strip() for author in author_tags]
        formatted_authors = ', '.join(authors) if authors else "No Author Info"
        
        snippet_tag = result.find('span', class_='abstract')
        snippet = snippet_tag.text.strip() if snippet_tag else "No Abstract"
        snippet = snippet.replace("△ Less", "").strip()
        
        year_tag = result.find('span', itemprop='datePublished')
        year = year_tag.text.strip() if year_tag else "No Year"
        
        link_tag = result.find('div', class_='head').find('a')
        link = link_tag['href'] if link_tag else "No Link"
        
        type_ = result.find('img').get('title', 'No Type')

        papers.append({
            "Title": title,
            "Authors": formatted_authors,
            "Year": year,
            "Link": link,
            "Type": type_,
            "Description": snippet,
        })
    
    # Save papers to text.json
    with open('text.json', 'w', encoding='utf-8') as w:
        json.dump(papers, w, ensure_ascii=False, indent=4)
    
    return papers



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '':
        return redirect(url_for('index'))

    faculty_publications = {}
    authors_set = set()  # Use a set to ensure uniqueness of authors

    if file and file.filename.endswith('.bib'):
        bib_data = file.read().decode('utf-8')
        bib_database = bibtexparser.loads(bib_data)
        entries = bib_database.entries
        print(entries)

        # Extract authors from BibTeX entries and store them in authors_set
        for entry in entries:
            faculty_name = entry.get('author')
            if faculty_name:
                # Split authors if multiple authors are present
                author_list = faculty_name.split(' and ')
                for author in author_list:
                    # Clean up and add to set
                    cleaned_author = author.strip()
                    if cleaned_author:
                        authors_set.add(cleaned_author)

        # Convert set to a list to pass to the template
        authors_list = list(authors_set)

        return render_template('index.html', entries=entries, faculty_publications=faculty_publications, authors=authors_list)

    return redirect(url_for('index'))


@app.route('/search', methods=['POST'])
def search():
    author_name = request.form.get('author')
    if not author_name:
        return redirect(url_for('index'))
    
    start = time.time()
    
    # Fetch author URL and papers based on the author name
    author_url = fetch_author_url(author_name)
    
    if author_url:
        publications = fetch_papers(author_url)
    else:
        publications = []  # If no author URL is found, return an empty list

    end = time.time()
    print(f'Time taken: {end - start} seconds')
    
    return render_template('index.html', faculty_publications={author_name: publications})
