from components.find_plugins import FindPlugins
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
from datetime import datetime
import time 
import re
from tabulate import tabulate
import os 

class DetectTheme :
    @staticmethod
    def detect_wordpress_themes(url):
        """Detect WordPress themes being used by the site"""
        themes = []
        
        try:
            # Technique 1: Check theme directory
            theme_path = '/wp-content/themes/'
            response = requests.get(urljoin(url, theme_path), timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.find_all('a')
                for link in links:
                    href = link.get('href')
                    if href and not href.startswith(('http://', 'https://', '/')) and not href.endswith(('/')):
                        themes.append({
                            'slug': href.rstrip('/'),
                            'detected_by': 'directory listing',
                            'type': 'theme'
                        })
            
            # Technique 2: Check source code for theme references
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check CSS and JS files for theme references
            tags = soup.find_all(['link', 'script', 'img'])
            for tag in tags:
                src = tag.get('src', '') or tag.get('href', '')
                if '/wp-content/themes/' in src:
                    theme_slug = src.split('/wp-content/themes/')[1].split('/')[0]
                    themes.append({
                        'slug': theme_slug,
                        'detected_by': 'resource URL',
                        'type': 'theme'
                    })
            
            # Technique 3: Check style.css which contains theme info
            for theme in list(set([t['slug'] for t in themes])):
                try:
                    response = requests.get(urljoin(url, f'/wp-content/themes/{theme}/style.css'), timeout=5)
                    if response.status_code == 200:
                        # Parse theme info from style.css
                        theme_data = {
                            'name': 'Unknown',
                            'version': 'Unknown',
                            'author': 'Unknown'
                        }
                        
                        # Extract theme metadata
                        theme_name = re.search(r'Theme Name:\s*(.+)\s*', response.text)
                        if theme_name:
                            theme_data['name'] = theme_name.group(1).strip()
                        
                        theme_version = re.search(r'Version:\s*(.+)\s*', response.text)
                        if theme_version:
                            theme_data['version'] = theme_version.group(1).strip()
                        
                        theme_author = re.search(r'Author:\s*(.+)\s*', response.text)
                        if theme_author:
                            theme_data['author'] = theme_author.group(1).strip()
                        
                        # Update theme entry
                        for t in themes:
                            if t['slug'] == theme:
                                t.update(theme_data)
                except:
                    continue
            
            # Remove duplicates
            unique_themes = []
            seen_slugs = set()
            for theme in themes:
                if theme['slug'] not in seen_slugs:
                    seen_slugs.add(theme['slug'])
                    unique_themes.append(theme)
            
            return unique_themes
            
        except Exception as e:
            print(f"Error detecting themes: {e}")
            return []
