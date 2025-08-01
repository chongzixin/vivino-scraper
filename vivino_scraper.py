# TODO: fix Error processing wine 71: 'ascii' codec can't encode character u'\xe2' in position 2: ordinal not in range(128)
# TODO: fix pagination so that we can scrape more wines

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import csv
import os
import urllib2
import time
import re
import os
from urlparse import urlparse

# Load environment variables from .env file
def load_dotenv(dotenv_path='.env'):
    if os.path.exists(dotenv_path):
        with open(dotenv_path) as f:
            for line in f:
                if line.strip() == '' or line.strip().startswith('#'):
                    continue
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
load_dotenv()

# Apify API Configuration
API_TOKEN = os.environ.get('API_TOKEN')
ACTOR_ID = 'canadesk~vivino-bulk'
API_BASE_URL = 'https://api.apify.com/v2'

class VivinoWineScraper:
    def __init__(self, api_token):
        self.api_token = api_token
        self.images_folder = 'images'
        self.csv_filename = 'wines_data.csv'
        
        # Create images directory if it doesn't exist
        if not os.path.exists(self.images_folder):
            os.makedirs(self.images_folder)
    
    def load_dataset_items_from_file(self, filepath):
        """Load all items from a local JSON file instead of an API call"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                # data is expected to be a list
                print("Loaded {} items from {}".format(len(data), filepath))
                return data
        except Exception as e:
            print("Error loading dataset items from file: {}".format(str(e)))
            return []

    def start_actor_run(self):
        """Start the Vivino-Bulk actor run for wine exploration"""
        input_data = {
            "process": "ge",
            "market": "SG",
            "winetypes": ["Red", "White", "Rose", "Sparkling", "Dessert", "Fortified"],
            "grapetypes": [],
            "foodtypes": [],
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
            },
            "sortby": "ratings_count",
            "maximum": 10000,
            "delay": 2,
            "ratingmin": "3.2",
            "retries": 3,
            "pricemax": 70,
            "pricemin": 10,
            "allreviews": False,
        }
        
        url = "{}/acts/{}/runs?token={}".format(API_BASE_URL, ACTOR_ID, self.api_token)
        
        req = urllib2.Request(url)
        req.add_header('Content-Type', 'application/json')
        req.get_method = lambda: 'POST'
        
        try:
            response = urllib2.urlopen(req, json.dumps(input_data))
            run_data = json.loads(response.read())
            return run_data['data']['id']
        except Exception as e:
            print("Error starting actor run: {}".format(str(e)))
            return None
    
    def wait_for_completion(self, run_id):
        """Wait for the actor run to complete"""
        url = "{}/actor-runs/{}?token={}".format(API_BASE_URL, run_id, self.api_token)
        
        print("Waiting for scraping to complete...")
        while True:
            try:
                response = urllib2.urlopen(url)
                run_info = json.loads(response.read())
                status = run_info['data']['status']
                
                if status == 'SUCCEEDED':
                    print("Scraping completed successfully!")
                    return run_info['data']['defaultDatasetId']
                elif status == 'FAILED':
                    print("Scraping failed!")
                    return None
                elif status in ['RUNNING', 'READY']:
                    print("Still running... waiting 30 seconds")
                    time.sleep(30)
                else:
                    print("Unknown status: {}".format(status))
                    time.sleep(30)
            except Exception as e:
                print("Error checking run status: {}".format(str(e)))
                time.sleep(30)
    
    def fetch_dataset_items(self, dataset_id):
        """Fetch all items from the dataset"""
        items = []
        offset = 0
        limit = 1000
        
        while True:
            url = "{}/datasets/{}/items?token={}&offset={}&limit={}".format(
                API_BASE_URL, dataset_id, self.api_token, offset, limit
            )
            
            try:
                response = urllib2.urlopen(url)
                data = json.loads(response.read())
                print(data)
                
                if not data:
                    break
                
                items.extend(data)
                offset += limit
                print("Fetched {} items so far...".format(len(items)))
                
            except Exception as e:
                print("Error fetching dataset items: {}".format(str(e)))
                break
        
        return items
    
    def download_image(self, image_url, wine_name):
        """Download wine image and return local path"""
        if not image_url:
            return ''
        
        if image_url.startswith('https//') and not image_url.startswith('https://'):
            image_url = image_url.replace('https//', 'https://', 1)
        
        try:
            # Clean wine name for filename
            clean_name = re.sub(r'[^\w\s-]', '', wine_name)
            clean_name = re.sub(r'[-\s]+', '_', clean_name)
            
            # Get file extension from URL
            parsed_url = urlparse(image_url)
            ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
            
            filename = "{}{}".format(clean_name[:50], ext)  # Limit filename length
            filepath = os.path.join(self.images_folder, filename)
            
            # Download image
            response = urllib2.urlopen(image_url)
            with open(filepath, 'wb') as f:
                f.write(response.read())
            
            return filepath
            
        except Exception as e:
            print("Error downloading image for {}: {}".format(wine_name, str(e)))
            return ''
    
    def clean_array_to_string(self, array_data, key_path):
        """Convert array of objects to comma-separated string"""
        if not array_data:
            return ''
        
        try:
            values = []
            for item in array_data:
                # Navigate nested keys (e.g., 'name' or 'group')
                current = item
                for key in key_path.split('.'):
                    current = current.get(key, {})

                if isinstance(current, basestring):
                    # Remove symbols and clean text
                    clean_value = re.sub(r'_', ' ', current)  # Replace underscores with spaces
                    
                    if clean_value:
                        values.append(clean_value)
            
            return ', '.join(values)
        except Exception as e:
            print("Error processing array data: {}".format(str(e)))
            return ''
    
    def process_wine_data(self, raw_items):
        """Process raw wine data according to the specified mapping"""
        processed_wines = []
        
        for idx, item in enumerate(raw_items):
            try:
                summary = item.get('summary', {})
                vintage = item.get('vintage', {})
                wine = vintage.get('wine', {}) if vintage else {}
                
                # Download images
                wine_name = summary.get('name', 'wine_{}'.format(idx))
                image_url = summary.get('image', '')
                local_image_path = self.download_image(image_url, wine_name)
                btl_image_url = wine.get('image', {}).get('variations', {}).get('bottle_medium', '')
                local_btl_image_path = self.download_image(btl_image_url, 'bottle_' + wine_name)
                # local_image_path = ''  # For testing, we won't download images
                
                # Extract and map data according to specifications
                wine_data = {
                    'name': summary.get('name', ''),
                    'country': summary.get('country', ''),
                    'price': summary.get('price', ''),
                    'rating': summary.get('rating', ''),
                    'image_url': local_image_path if local_image_path else '',
                    'bottle_image_url': local_btl_image_path if local_btl_image_path else '',
                    'region': wine.get('region', {}).get('name', '') if wine.get('region') else '',
                    'winery': wine.get('winery', {}).get('name', '') if wine.get('winery') else '',
                    'flavor': self.clean_array_to_string(
                        wine.get('taste', {}).get('flavor', []) if wine.get('taste') else [],
                        'group'
                    ),
                    'food_pairing': self.clean_array_to_string(
                        wine.get('style', {}).get('food', []) if wine.get('style') else [],
                        'name'
                    ),
                    'grapes': self.clean_array_to_string(
                        wine.get('style', {}).get('grapes', []) if wine.get('style') else [],
                        'name'
                    )
                }
                
                processed_wines.append(wine_data)
                
                if (idx + 1) % 100 == 0:
                    print("Processed {} wines...".format(idx + 1))
                    
            except Exception as e:
                print("Error processing wine {}: {}".format(idx, str(e)))
                continue
        
        return processed_wines
    
    def save_to_csv(self, wine_data):
        """Save processed wine data to CSV"""
        if not wine_data:
            print("No wine data to save!")
            return
        
        fieldnames = ['name', 'country', 'price', 'rating', 'image', 'region', 'winery', 'flavor', 'food_pairing', 'grapes']
        
        with open(self.csv_filename, 'wb') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for wine in wine_data:
                # Encode strings to UTF-8 for Python 2 compatibility
                encoded_wine = {}
                for key, value in wine.items():
                    if isinstance(value, unicode):
                        encoded_wine[key] = value.encode('utf-8')
                    elif isinstance(value, str):
                        # Try decoding to unicode and then encode as utf-8
                        try:
                            encoded_wine[key] = value.decode('utf-8').encode('utf-8')
                        except:
                            encoded_wine[key] = value  # fallback
                    else:
                        encoded_wine[key] = str(value)

                writer.writerow(encoded_wine)
        
        print("Saved {} wines to {}".format(len(wine_data), self.csv_filename))
    
    def run_complete_scrape(self, local_json_path=None):
        """Execute the complete wine scraping workflow"""
        print("Starting Vivino wine scraping...")
        
        if local_json_path:
            # For testing: read from local file
            raw_wine_data = self.load_dataset_items_from_file(local_json_path)
        else:
            # Production: use API as before

            # Step 1: Start the actor run
            run_id = self.start_actor_run()
            if not run_id:
                print("Failed to start scraping!")
                return
            
            # Step 2: Wait for the run to complete
            print("Started scraping with run ID: {}".format(run_id))
            dataset_id = self.wait_for_completion(run_id)
            if not dataset_id:
                print("Scraping did not complete successfully!")
                return
            
            # Step 3: Fetch all wine data
            print("Fetching wine data from dataset...")
            raw_wine_data = self.fetch_dataset_items(dataset_id)
            print("Retrieved {} wine records".format(len(raw_wine_data)))
        
        # Step 4: Process, download image and write CSV
        print("Processing wine data and downloading images...")
        processed_wines = self.process_wine_data(raw_wine_data)
        
        # Step 5: Save to CSV
        print("Saving data to CSV...")
        self.save_to_csv(processed_wines)
        
        print("Wine scraping completed successfully!")
        print("Total wines processed: {}".format(len(processed_wines)))
        print("Images saved to: ./{}".format(self.images_folder))
        print("CSV file saved as: {}".format(self.csv_filename))

# Main execution
if __name__ == "__main__":
    # Initialize scraper with your API token
    scraper = VivinoWineScraper(API_TOKEN)
    
    # Run the complete scraping process
    scraper.run_complete_scrape(local_json_path='sample-response.json') # provide a file name to process it
    # scraper.run_complete_scrape() # or leave empty to run the full scrape via API
