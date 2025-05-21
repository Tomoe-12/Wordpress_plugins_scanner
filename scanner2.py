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

def standard_wordpress_checks(url):
    """Check if a website is running by WordPress"""
    try:
        # Technique 1: Check for common WordPress paths
        paths_to_check = [
            '/wp-admin/',
            '/wp-content/',
            '/wp-includes/',
            '/readme.html',
            '/wp-login.php'
        ]
        
        for path in paths_to_check:
            try:
                response = requests.get(urljoin(url, path), timeout=10)
                if response.status_code == 200:
                    return True
            except:
                continue
        
        # Technique 2: Check WordPress meta tags in homepage
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Check for WordPress generator meta tag
        meta_generator = soup.find('meta', attrs={'name': 'generator'})
        if meta_generator and 'wordpress' in meta_generator.get('content', '').lower():
            return True
            
        # Technique 3: Check for WordPress in scripts or links
        scripts = soup.find_all('script') + soup.find_all('link')
        for tag in scripts:
            if 'wp-content' in str(tag.get('src', '')) or 'wp-content' in str(tag.get('href', '')):
                return True
                
        return False
        
    except Exception as e:
        print(f"Error checking WordPress: {e}")
        return False

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

def find_plugins2(url):
    """More accurate WordPress plugin detection that excludes themes and other false positives"""
    plugins = []
    KNOWN_FALSE_POSITIVES = {
        'themes', 'uploads', 'upgrade', 'languages', 'cache',
        'images', 'assets', 'js', 'css', 'fonts'
    }
   
    try:
        # Technique 1: Check plugin directories more carefully
        plugin_paths = [
            '/wp-content/plugins/',
            '/plugins/'
        ]
        
        for path in plugin_paths:
            try:
                response = requests.get(urljoin(url, path), timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    links = soup.find_all('a')
                    for link in links:
                        href = link.get('href')
                        if href and not href.startswith(('http://', 'https://', '/')) and not href.endswith(('/')):
                            # Skip common non-plugin directories
                            if href.lower() in KNOWN_FALSE_POSITIVES:
                                continue
                            plugins.append({
                                'slug': href.rstrip('/'), 
                                'detected_by': 'directory listing',
                                'type': 'plugin'
                            })
            except:
                continue
        
        # Technique 2: More precise source code analysis
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check scripts, links, and iframes more carefully
        tags = soup.find_all(['script', 'link', 'img', 'iframe'])
        for tag in tags:
            src = tag.get('src', '') or tag.get('href', '')
            
            # Only consider URLs containing the plugin path
            if '/wp-content/plugins/' in src:
                parts = src.split('/wp-content/plugins/')[1].split('/')
                if len(parts) > 0:
                    plugin_slug = parts[0]
                    # Skip if this is actually a theme reference
                    if plugin_slug.lower() != 'themes' and not src.lower().startswith('/wp-content/themes/'):
                        plugins.append({
                            'slug': plugin_slug, 
                            'detected_by': 'resource URL',
                            'type': 'plugin'
                        })
        
        # Technique 3: Check for plugin-specific files
        plugin_files = [
            ('akismet/akismet.php', 'Akismet Anti-Spam'),
            ('jetpack/jetpack.php', 'Jetpack'),
            ('yoast-seo/wp-seo.php', 'Yoast SEO'),
            # Add more plugin files here
        ]
        
        for file_path, plugin_name in plugin_files:
            try:
                response = requests.head(urljoin(url, f'/wp-content/plugins/{file_path}'), timeout=5)
                if response.status_code == 200:
                    plugins.append({
                        'slug': file_path.split('/')[0], 
                        'name': plugin_name, 
                        'detected_by': 'known file',
                        'type': 'plugin'
                    })
            except:
                continue
        
        # Technique 4: Check for readme.txt files in plugin directories
        unique_slugs = {p['slug'] for p in plugins}
        for slug in list(unique_slugs):
            try:
                response = requests.get(urljoin(url, f'/wp-content/plugins/{slug}/readme.txt'), timeout=5)
                if response.status_code == 200:
                    # Parse readme.txt to confirm it's a plugin
                    if '=== Plugin Name ===' in response.text:
                        # Extract version if available
                        version = 'unknown'
                        version_match = re.search(r'===.*?===.*?Version:\s*([\d.]+)', response.text, re.DOTALL)
                        if version_match:
                            version = version_match.group(1)
                        
                        # Update existing entries
                        for p in plugins:
                            if p['slug'] == slug:
                                p['version'] = version
                                p['verified_by'] = 'readme.txt'
            except:
                continue
        
        # Remove duplicates and false positives
        final_plugins = []
        seen_slugs = set()
        
        for plugin in plugins:
            slug = plugin['slug'].lower()
            
            # Skip common false positives
            if slug in KNOWN_FALSE_POSITIVES:
                continue
                
            # Skip version numbers in paths
            if re.match(r'^\d+\.\d+(\.\d+)?$', slug):
                continue
                
            if slug not in seen_slugs:
                seen_slugs.add(slug)
                final_plugins.append(plugin)
        
        return final_plugins
        
    except Exception as e:
        print(f"Error finding plugins: {e}")
        return []

def get_plugin_details(slug):
    """Get plugin details from WordPress API"""
    api_url = f"https://api.wordpress.org/plugins/info/1.2/?action=plugin_information&request[slug]={slug}"
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def display_results(items):
    """Display the results in a table"""
    table_data = []
    for item in items:
        if item['type'] == 'plugin':
            details = item.get('details', {})
            table_data.append([
                item['slug'],
                details.get('name', 'N/A'),
                details.get('version', 'N/A'),
                'Plugin',
                item['detected_by'],
                details.get('last_updated', 'N/A'),
                details.get('active_installs', 'N/A') if isinstance(details.get('active_installs'), int) else 'N/A'
            ])
        else:  # Theme
            table_data.append([
                item['slug'],
                item.get('name', 'N/A'),
                item.get('version', 'N/A'),
                'Theme',
                item['detected_by'],
                'N/A',
                'N/A'
            ])
    
    headers = ["Slug", "Name", "Version", "Type", "Detection Method", "Last Updated", "Active Installs"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def is_wordpress_site(url):
    """Enhanced WordPress detection that accounts for VIP sites"""
    try:
        # Standard checks first
        if standard_wordpress_checks(url):
            return True
            
        # Additional checks for VIP sites
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for VIP-specific headers
        if 'x-hosting-provider' in response.headers:
            if 'wordpress' in response.headers['x-hosting-provider'].lower():
                return True
                
        # Check for VIP-specific classes in HTML
        vip_classes = ['wpcom', 'vip', 'wordpress-vip']
        for cls in vip_classes:
            if soup.find(class_=cls):
                return True
                
        # Check for VIP-specific comments
        if 'wpvip' in response.text.lower():
            return True
            
        return False
        
    except Exception as e:
        print(f"Error checking WordPress: {e}")
        return False

def check_cloudflare_protected(url):
    """Check if site is protected by Cloudflare"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 403 and 'cloudflare' in response.text.lower():
            return True
        if 'server' in response.headers and 'cloudflare' in response.headers['server'].lower():
            return True
        return False
    except:
        return False

if __name__ == "__main__":
    print("WordPress Plugin & Theme Checker (VIP Edition)")
    website_url = input("Enter website URL: ").strip()
    
    if not website_url.startswith(('http://', 'https://')):
        website_url = 'https://' + website_url
    
    print(f"\nChecking {website_url}...")
    time.sleep(1)
    
    if check_cloudflare_protected(website_url):
        print("Note: Site appears to be behind Cloudflare - some detection may be limited")
    
    if is_wordpress_site(website_url):
        print("WordPress detected (possibly VIP hosted)!")
        print("\nSearching for plugins and themes (this may take longer for VIP sites)...")
        
        try:
            # Find both plugins and themes
            # plugins = find_plugins(website_url)
            plugins= FindPlugins.find_plugins(website_url)
            themes = detect_wordpress_themes(website_url)
            print(f"\nFound {len(plugins)+len(themes)} plugins or features:")
            
            all_items = plugins + themes
            
            # Get plugin details from WordPress API
            for item in all_items:
                if item['type'] == 'plugin':
                    details = get_plugin_details(item['slug'])
                    if details:
                        item['details'] = details

            
            # Define the Results directory (absolute path)
            script_dir = os.path.dirname(os.path.abspath(__file__))  # Gets the folder where the script is
            results_dir = os.path.join(script_dir, 'Results')
            # Create Results directory if it doesn't exist
            os.makedirs(results_dir, exist_ok=True)
            
            if all_items:
                print(f"\nFound {len(all_items)} items ({len(plugins)} plugins, {len(themes)} themes):")
                display_results(all_items)

                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # filename = f"wordpress_scan_{timestamp}.json"
                sanitized_url=website_url.replace('https://', '').replace('http://', '').replace('/', '_').replace('.', '-')
                filename = f"wordpress_scan_{sanitized_url}_{timestamp}.json"
                filePath = os.path.join(results_dir,filename)

                with open(filePath, 'w') as f:
                    json.dump(all_items, f, indent=2)
                print(f"\nResults saved to {filePath}")
            else:
                print("No plugins or themes detected. This may be a highly customized VIP site.")
        except Exception as e:
            print(f"Scanning interrupted. VIP sites often have stricter protections: {e}")
    else:
        print("This doesn't appear to be a WordPress site.")