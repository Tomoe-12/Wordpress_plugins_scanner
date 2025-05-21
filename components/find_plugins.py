# find_plugins.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import os 
import json 
from datetime import datetime,timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from config_loader import ConfigLoader

config = ConfigLoader()


class FindPlugins :
    cache_file = 'wpscan_plugins_cache.json'
    cache_duration_hours = 24

    COMMON_WP_PATHS = [
                '/wp-admin/',
                '/wp-content/',
                '/wp-includes/',
                '/readme.html',
                '/wp-login.php'
    ]

    KNOWN_FALSE_POSITIVES = {
            'themes', 'uploads', 'upgrade', 'languages', 'cache',
            'images', 'assets', 'js', 'css', 'fonts'
    }

    PLUGIN_PATHS = [
        '/wp-content/plugins/', '/plugins/'
    ]

    PLUGIN_SIGNATURE_FILES = [
                ('akismet/akismet.php', 'Akismet Anti-Spam'),
                ('jetpack/jetpack.php', 'Jetpack'),
                ('yoast-seo/wp-seo.php', 'Yoast SEO'),
                ('wordpress-seo/wp-seo.php', 'Yoast SEO'),  # Add alternative path
                ('yoast-seo/js/dist/yoast-seo-', 'Yoast SEO'),  # Check for minified assets
    ]
    
    # Get request limit from config dynamically
    request_limit = config.get_int('wpscan_api_request_limit', 30)
    
    @staticmethod
    def get_known_plugins_from_wporg(limit=100):
        """Fetch known plugin slugs from WordPress.org API with JSON caching"""
        try:
            # Check for existing cache
            if os.path.exists(FindPlugins.cache_file):
                with open(FindPlugins.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    cached_time = datetime.strptime(cache_data['fetched_at'], '%Y-%m-%d %H:%M:%S')
                    if datetime.now() - cached_time < timedelta(hours=FindPlugins.cache_duration_hours):
                        print("[*] Using cached plugin slugs from WordPress.org API")
                        return cache_data['plugin_slugs'][:limit]

            print("[*] Fetching fresh plugin slugs from WordPress.org API")

       
            # return plugin_slugs[:limit]
            # Fetch more plugins in one request
            per_page = max(limit, 250)
            response = requests.get(
                f"https://api.wordpress.org/plugins/info/1.2/?action=query_plugins&request[page]=1&request[per_page]={per_page}",
                timeout=15
            )
            if response.status_code != 200:
                print(f"[!] Failed to fetch from WordPress.org API: {response.status_code}")
                return []

            data = response.json()
            if 'plugins' not in data or not data['plugins']:
                return []

            plugin_slugs = [plugin['slug'] for plugin in data['plugins']][:limit]

            with open(FindPlugins.cache_file, 'w') as f:
                json.dump({
                    'fetched_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'plugin_slugs': plugin_slugs
                }, f, indent=2)

            return plugin_slugs

        except Exception as e:
            print(f"[!] Error fetching WordPress.org plugins: {e}")
            return []
   
    @staticmethod
    def standard_wordpress_checks(url):
        """Check if a website is running by WordPress"""
        try:
            # Technique 1: Check for common WordPress paths
            for path in FindPlugins.COMMON_WP_PATHS:
                try:
                    res = requests.get(urljoin(url, path), timeout=10)
                    res.raise_for_status()
                    if res.status_code == 200:
                        return True
                except:
                    continue
            
            # Technique 2: Check WordPress meta tags in homepage
            res = requests.get(url, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Check for WordPress generator meta tag
            if(meta := soup.find('meta',attrs={'name':'generator'})):
                if 'wordpress' in meta.get('content','').lower():
                    return True
                
            # Technique 3: Check for WordPress in scripts or links
            for tag in soup.find_all(['script','link']):
                if 'wp-content' in str(tag.get('src', '')) or 'wp-content' in str(tag.get('href', '')):
                    return True
                    
            return False
            
        except Exception as e:
            print(f"Error checking WordPress: {e}")
            return False
        
    @staticmethod
    def find_plugins(url):
        """Detect installed plugins on a WordPress site"""
        plugins = []
       
        try:
            soup = BeautifulSoup(requests.get(url, timeout=10).text, 'html.parser')

            # Technique 1: Detect via resource URLs
            for tag in soup.find_all(['script', 'link', 'img', 'iframe']):
                src = tag.get('src') or tag.get('href')
                if src and '/wp-content/plugins/' in src:
                    slug = src.split('/wp-content/plugins/')[1].split('/')[0]
                    if slug.lower() not in FindPlugins.KNOWN_FALSE_POSITIVES:
                        plugins.append({'slug': slug, 'detected_by': 'resource URL', 'type': 'plugin'})
                  
            # Technique 2: Check known plugin files
            for path, name in FindPlugins.PLUGIN_SIGNATURE_FILES:
                try:
                    res = requests.head(urljoin(url, f'/wp-content/plugins/{path}'), timeout=5)
                    if res.status_code == 200:
                        plugins.append({
                            'slug': path.split('/')[0],
                            'name': name,
                            'detected_by': 'known file',
                            'type': 'plugin'
                        })
                except:
                    continue
        
            # Technique 3: Check for plugin-specific files
            for plugin in set(p['slug'] for p in plugins):
                try:
                    res = requests.get(urljoin(url, f'/wp-content/plugins/{plugin}/readme.txt'), timeout=5)
                    if res.status_code == 200 and '=== Plugin Name ===' in res.text:
                        version_match = re.search(r'^Version:\s*([\d\.]+)', res.text, re.MULTILINE | re.IGNORECASE)
                        version = version_match.group(1) if version_match else 'unknown'
                        for p in plugins:
                            if p['slug'] == plugin:
                                p['version'] = version
                                p['verified_by'] = 'readme.txt'
                except:
                    continue
        
             # Technique 4: Enumeration via known slugs
            for slug in FindPlugins.get_known_plugins_from_wporg():
                try:
                    res = requests.head(urljoin(url, f'/wp-content/plugins/{slug}/'), timeout=5)
                    if res.status_code == 200:
                        plugins.append({'slug': slug, 'detected_by': 'API enumeration', 'type': 'plugin'})
                except:
                    continue
             # Technique 5: Directory listings
            for path in FindPlugins.PLUGIN_PATHS:
                try:
                    res = requests.get(urljoin(url, path), timeout=10)
                    if res.status_code == 200:
                        soup_dir = BeautifulSoup(res.text, 'html.parser')
                        for link in soup_dir.find_all('a'):
                            href = link.get('href')
                            if href:
                                slug = href.strip('/').split('/')[0]
                                if slug.lower() not in FindPlugins.KNOWN_FALSE_POSITIVES:
                                    plugins.append({'slug': slug, 'detected_by': 'directory listing', 'type': 'plugin'})
                except:
                    continue
            
            # Remove duplicates and common false positives
            final_plugins, seen = [], set()
            for plugin in plugins:
                slug = plugin['slug'].lower()
                if slug in FindPlugins.KNOWN_FALSE_POSITIVES or slug in seen:
                    continue
                if re.match(r'^\d+\.\d+(\.\d+)?$', slug):  # skip version numbers
                    continue
                seen.add(slug)
                final_plugins.append(plugin)

            return final_plugins

        except Exception as e:
            print(f"[!] Error detecting plugins: {e}")
            return []
        

