# pylint: disable=missing-module-docstring
import os
import re
import requests
from bs4 import BeautifulSoup
from pdfdocument.document import PDFDocument

# Create output folder
os.makedirs("output_pdfs", exist_ok=True)

# Function to sanitize and transform museum name to PDF filename
def transform_to_pdf_filenames(museum_name):
    safe_name = re.sub(r'[\\/*?:"<>|]', "_", museum_name)
    return os.path.join("output_pdfs", safe_name + '.pdf')

# Function to process tags and apply PDF formatting
def process_tag(tag):
    tag_name = tag.name
    if tag_name == 'h1':
        pdf.h1(tag.text.strip())
    elif tag_name == 'h2':
        pdf.h2(tag.text.strip())
    elif tag_name == 'p':
        pdf.p(tag.text.strip())
    elif tag_name == 'dt':
        pdf.h3(tag.text.strip())
    elif tag_name == 'dd':
        pdf.p(tag.text.strip())
    elif tag_name == 'th':
        pdf.h3(tag.text.strip())
    elif tag_name == 'td':
        pdf.p(tag.text.strip())

# Base URL setup
BASE_URL = 'https://www.si.edu'
MUSEUMS_LIST_URL = f'{BASE_URL}/museums'
MUSEUM_URLS = []

# Step 1: Get all museum URLs
r = requests.get(MUSEUMS_LIST_URL)
soup = BeautifulSoup(r.content, 'lxml')

links_scraped = soup.find_all('li', class_='col edan-search-result in-unit has-media has-media location')
for link_element in links_scraped:
    link = link_element.find('a', href=True)
    if link:
        MUSEUM_URLS.append(BASE_URL + link['href'])
MUSEUM_URLS = list(set(MUSEUM_URLS))  # Remove duplicates

# Step 2: Visit each museum page
for MUSEUM_URL in MUSEUM_URLS:
    r = requests.get(MUSEUM_URL)
    soup = BeautifulSoup(r.content, 'lxml')

    museum_description = []

    # Museum name
    museum_name = soup.find('h1').text.strip()
    pdf_path = transform_to_pdf_filenames(museum_name)

    # Start writing PDF
    with open(pdf_path, 'wb') as f:
        pdf = PDFDocument(f)
        pdf.init_report()

        # Description sections
        museum_description_scrap = soup.find_all('div', class_=[
            'layout l-container location-details',
            'l-region--hero pane-page-header'
        ])
        for item in museum_description_scrap:
            for tag in item.find_all(['p', 'h1', 'h2']):
                process_tag(tag)

        # Address
        address_block = soup.select_one(".location-address")
        if address_block:
            address = address_block.get_text().strip()
            pdf.h2('Address of the museum:')
            pdf.p(address)

        # Get items (exhibitions and collections)
        items = soup.find_all('li', class_='edan-search-result')
        items_links = []
        for item in items:
            for link in item.find_all('a', href=True):
                items_links.append(BASE_URL + link['href'])
        items_links = list(set(items_links))

        # Exhibitions
        pdf.h1(f'- {museum_name} Exhibitions:')
        for test_link in items_links:
            if 'exhibitions' in test_link:
                try:
                    r = requests.get(test_link)
                    soup = BeautifulSoup(r.content, 'lxml')
                    title = soup.find('h1', class_='field').text.strip()
                    pdf.h2(title)

                    date = soup.find('div', class_='field field--name-field-tagline field--type-text field--label-hidden')
                    if date:
                        pdf.h3('Date of the exhibition:')
                        pdf.p(date.text.strip())

                    location_wrapper = soup.find('div', class_='location-wrapper')
                    if location_wrapper:
                        location_text = ' '.join([str(e) for e in location_wrapper.children if e.name != 'p']).strip()
                        pdf.h3('Location:')
                        pdf.p(location_text)

                    description_block = soup.find('div', class_='edan-content')
                    if description_block:
                        pdf.h3('Informations - Description:')
                        for tag in description_block.find_all('p'):
                            process_tag(tag)
                except Exception:
                    continue  # skip on error

        # Collections
        pdf.h1(f'- {museum_name} Collections Sampler:')
        for test_link in items_links:
            if 'object' in test_link:
                try:
                    r = requests.get(test_link)
                    soup = BeautifulSoup(r.content, 'lxml')

                    title = soup.find('h1').text.strip()
                    pdf.h2(title)

                    full_details = soup.find_all('div', class_='recordDetails', id='edanWrapper')
                    for item in full_details:
                        if item.find('div', class_='tabHeading'):
                            for sub_item in item.find_all('div', class_='tab-pane', id='edanDetails'):
                                for tag in sub_item.find_all(['dd', 'dt', 'h2']):
                                    process_tag(tag)
                        else:
                            for tag in item.find_all(['dd', 'dt', 'h2']):
                                process_tag(tag)
                except Exception:
                    continue  # skip on error

        pdf.generate()
        print(f"✅ PDF created for: {museum_name}")
