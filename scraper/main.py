import requests
from bs4 import BeautifulSoup
import re
import json
import os
import time
from pymongo import MongoClient


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "ubisoft_db"
COLLECTION_NAME = "games"
URL = "https://store.ubisoft.com/fr/games"


def get_db_collection():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    return db[COLLECTION_NAME]

def normalize_genre(genre):
    # FR to EN and standardize
    translation_map = {
        'aventure': 'adventure',
        'aventure-action en monde ouvert': 'open world', 
        'monde ouvert': 'open world',
        'jeu de tir': 'shooter',
        'multijoueur': 'multiplayer',
        'simulation': 'simulator',
        'stratégie': 'strategy',
        'course': 'racing',
        'simulaton de gestion urbaine': 'simulator',  
        'coop': 'co-op',
        'fps': 'shooter',  
        'open world action adventure': 'open world',  
        'city building simulator': 'simulator',  
    }
    
    genre_lower = genre.strip().lower()
    if genre_lower in translation_map:
        genre_lower = translation_map[genre_lower]
    normalized = genre_lower.title()
    special_cases = {
        'Co-op': 'Co-Op',
        'Dlc': 'DLC',
    }
    
    if normalized in special_cases:
        normalized = special_cases[normalized]
    
    return normalized

def scrape_games():
    print(f"Fetching data from {URL}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(URL, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    games = []
    product_tiles = soup.find_all('div', class_='product-tile')
    
    print(f"Found {len(product_tiles)} product tiles.")

    for tile in product_tiles:
        game_data = {}
        
        script = tile.find_next('script')
        if script and script.string:
            matches = re.search(r'var product = ({.*?});', script.string, re.DOTALL)
            if matches:
                try:
                    game_data = json.loads(matches.group(1))
                except json.JSONDecodeError:
                    print("Error parsing JSON")
                    continue
        
        if not game_data:
            tile_text = tile.get_text(strip=True)[:100]  
            print(f"No metadata found for tile: {tile_text}...")
            continue

        # Check for DLC status via data-tc100 attributes
        is_dlc = False
        tc100_elements = tile.find_all(attrs={"data-tc100": True})
        for elem in tc100_elements:
            try:
                tc100_val = elem['data-tc100']
                if tc100_val and tc100_val.strip().startswith('{'):
                    tc100_data = json.loads(tc100_val)
                    p_type = tc100_data.get('productType', '').lower()
                    if p_type == 'dlc':
                        is_dlc = True
                        break
            except (json.JSONDecodeError, TypeError, AttributeError):
                continue
        
        if is_dlc:
            current_genre = game_data.get('genre', '')
            if current_genre:
                game_data['genre'] = current_genre + ", DLC"
            else:
                game_data['genre'] = "DLC"

        price_sales = tile.find('span', class_='price-sales')
        price_standard = tile.find('span', class_='price-standard')
        
        current_price_str = None
        original_price_str = None
        is_on_sale = False
        
        if price_sales and price_standard:
            current_price_str = price_sales.get_text(strip=True)
            original_price_str = price_standard.get_text(strip=True)
            is_on_sale = True
        elif price_sales:
            current_price_str = price_sales.get_text(strip=True)
        elif price_standard:
            current_price_str = price_standard.get_text(strip=True)
        
        def parse_price(price_str):
            if not price_str:
                return None
            if "gratuit" in price_str.lower() or "free" in price_str.lower():
                return 0.0
            price_match = re.search(r'(\d+([.,]\d+)?)', price_str)
            if price_match:
                price_val = price_match.group(1).replace(',', '.')
                try:
                    return float(price_val)
                except ValueError:
                    return None
            return None
        
        if current_price_str:
            current_price = parse_price(current_price_str)
            if current_price is not None:
                game_data['unit_price'] = current_price
                if not is_on_sale:
                    game_data['original_price'] = current_price
        
        if is_on_sale and original_price_str:
            original_price = parse_price(original_price_str)
            if original_price is not None and original_price > 0:
                game_data['original_price'] = original_price
                game_data['is_on_sale'] = True
                
                current = game_data.get('unit_price', 0)
                if current < original_price:
                    discount_pct = ((original_price - current) / original_price) * 100
                    game_data['discount_percentage'] = round(discount_pct, 2)
        else:
            game_data['is_on_sale'] = False

        # Extract Image
        # There are some bugs right now.
        # The image cannot be displayed correctly. Maybe due to lazy loading or incorrect src attributes.
        img_tag = tile.find('img', class_='primary-image')
        if not img_tag:
            img_tag = tile.find('img', class_='product_image')
        if not img_tag:
            img_tag = tile.find('img')
            
        if img_tag:
            img_url = img_tag.get('data-src') or img_tag.get('src')
             
            if img_url:
                if img_url.startswith('/'):
                    img_url = "https://store.ubisoft.com" + img_url
                elif not img_url.startswith('http'):
                    pass
                game_data['image_url'] = img_url


        if 'genre' in game_data and game_data['genre']:
            genre_str = game_data['genre']
            genres = re.split(r'[/,]', genre_str)
            genres = [normalize_genre(g) for g in genres if g.strip()]
            game_data['genres'] = genres
            
        game_name = game_data.get('name', 'Unknown')
        game_id = game_data.get('id', 'No ID')
        print(f"Adding game: {game_name[:50]} (ID: {game_id})")
        
        games.append(game_data)

    print(f"Scraped {len(games)} valid games.")
    return games

def filter_on_sale_games(games):

    on_sale_games = [game for game in games if game.get('is_on_sale', False)]
    on_sale_games.sort(key=lambda x: x.get('discount_percentage', 0), reverse=True)
    
    return on_sale_games

def save_to_mongo(games):
    if not games:
        print("No games to save.")
        return

    collection = get_db_collection()
    
    # Use update_one with upsert=True to avoid duplicates based on 'id'
    count = 0
    for game in games:
        if 'id' in game:
            collection.update_one(
                {'id': game['id']},
                {'$set': game},
                upsert=True
            )
            count += 1
    
    print(f"Upserted {count} games into MongoDB.")

if __name__ == "__main__":
    print("Waiting for MongoDB to start...")
    time.sleep(5) 
    
    games_data = scrape_games()
    on_sale_games = filter_on_sale_games(games_data)
    
    save_to_mongo(games_data)
    print("Scraping completed.")
    print(f"Total games: {len(games_data)}")
