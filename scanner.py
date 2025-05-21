import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
from datetime import datetime

def is_wordpress_site(url):
    """Check if a website is running by WordPress"""
    try:
        #Technique 1: Check for common WordPress paths
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
        
        #Technique 2: Check  WordPress meta tags in homepage
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Check for WordPress generator meta tag
        meta_generator = soup.find('meta', attrs={'name': 'generator'})
        if meta_generator and 'wordpress' in meta_generator.get('content', '').lower():
            return True
            
        #Technique 3: Check for WordPress in scripts or links
        scripts = soup.find_all('script') + soup.find_all('link')
        for tag in scripts:
            if 'wp-content' in str(tag.get('src', '')) or 'wp-content' in str(tag.get('href', '')):
                return True
                
        return False
        
    except Exception as e:
        print(f"Error checking WordPress: {e}")
        return False

def find_plugins(url):
    """Find WordPress plugins used by a website entered by the user """
    plugins = []
    
    try:
        # Technique 1: Check common plugin paths
        common_plugin_paths = [
            '/wp-content/plugins/',
            '/plugins/'
        ]
        
        for path in common_plugin_paths:
            try:
                response = requests.get(urljoin(url, path), timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Look for directory listings
                    links = soup.find_all('a')
                    for link in links:
                        href = link.get('href')
                        if href and not href.startswith(('http://', 'https://', '/')) and not href.endswith(('/')):
                            plugins.append({'slug': href.rstrip('/'), 'detected_by': 'directory listing'})
            except:
                continue
        
        # Technique 2: Check source code for plugin references
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check scripts and links for plugin references
        tags = soup.find_all(['script', 'link', 'img'])
        for tag in tags:
            src = tag.get('src', '') or tag.get('href', '')
            if '/wp-content/plugins/' in src:
                plugin_slug = src.split('/wp-content/plugins/')[1].split('/')[0]
                plugins.append({'slug': plugin_slug, 'detected_by': 'resource URL'})
        
        # Technique 3: Check for known plugin files
        known_plugin_files = {
            'hello.php': 'Hello Dolly',
            'akismet/akismet.php': 'Akismet Anti-Spam',
            'jetpack/jetpack.php': 'Jetpack',
            'yoast-seo/wp-seo.php': 'Yoast SEO'
        }
        
        for file_path, plugin_name in known_plugin_files.items():
            try:
                response = requests.get(urljoin(url, f'/wp-content/plugins/{file_path}'), timeout=5)
                if response.status_code == 200:
                    plugins.append({'slug': file_path.split('/')[0], 'name': plugin_name, 'detected_by': 'known file'})
            except:
                continue
        
        # Remove duplicates
        unique_plugins = []
        seen_slugs = set()
        for plugin in plugins:
            if plugin['slug'] not in seen_slugs:
                seen_slugs.add(plugin['slug'])
                unique_plugins.append(plugin)
        
        return unique_plugins
        
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

def display_results(plugins):
    """Display the results in a table"""
    from tabulate import tabulate # type: ignore
    
    table_data = []
    for plugin in plugins:
        details = plugin.get('details', {})
        table_data.append([
            plugin['slug'],
            details.get('name', 'N/A'),
            details.get('version', 'N/A'),
            plugin['detected_by'],
            details.get('last_updated', 'N/A'),
            details.get('active_installs', 'N/A') if isinstance(details.get('active_installs'), int) else 'N/A'
        ])
    
    headers = ["Slug", "Name", "Version", "Detection Method", "Last Updated", "Active Installs"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

if __name__ == "__main__":
    print("WordPress Plugin Checker")
    website_url = input("Enter website URL (e.g., https://example.com): ").strip()
    
    if not website_url.startswith(('http://', 'https://')):
        website_url = 'https://' + website_url
    
    print(f"\nChecking if {website_url} is a WordPress site...")
    if is_wordpress_site(website_url):
        print("WordPress detected!")
        print("\nSearching for plugins...")
        plugins = find_plugins(website_url)
        
        if plugins:
            print(f"\nFound {len(plugins)} plugins:")
            
            # Get details for each plugin
            for plugin in plugins:
                details = get_plugin_details(plugin['slug'])
                if details:
                    plugin['details'] = details
            
            display_results(plugins)
            
            # Save results to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"website_plugins_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(plugins, f, indent=2)
            print(f"\nResults saved to {filename}")
        else:
            print("No plugins detected.")
    else:
        print("This doesn't appear to be a WordPress site.")

