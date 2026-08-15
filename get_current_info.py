import requests
from bs4 import BeautifulSoup
import time

async def _daily_update():
    source_url = 'https://goethe-flensburg.de/wp-content/uploads/vertretung/S_Dateien/f1/subst_001.htm'
    while True:
        try:
            response = requests.get(source_url)
            if response.status_code == 200:
                break
            else:
                print(f"Received status code {response.status_code}, retrying...")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching the URL: {e}, retrying...")
        time.sleep(2)
    source_html = response.text

    # BeautifulSoup verwenden, um das HTML zu parsen
    soup = BeautifulSoup(source_html, 'html.parser')
    
    # Finde alle Tabellen auf der Seite
    tables = soup.find_all('table')
    
    # Entferne die erste Tabelle nur, wenn mehr als eine Tabelle vorhanden ist
    if len(tables) > 1:
        first_table = tables[0]
        first_table.decompose()
    
    # Das bereinigte HTML
    cleaned_html = str(soup)
    
    # BeautifulSoup verwenden, um die verbleibende HTML-Tabelle zu parsen
    soup = BeautifulSoup(cleaned_html, 'html.parser')
    table = soup.find('table')
    
    # Tabelle in ein 2D-Array konvertieren
    table_data = []
    if table:
        for row in table.find_all('tr'):
            row_data = []
            for cell in row.find_all(['td', 'th']):
                row_data.append(cell.get_text(strip=True))
            table_data.append(row_data)
    else:
        print("No table found in the HTML content.")
    
    return table_data
