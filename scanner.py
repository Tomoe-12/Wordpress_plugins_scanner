from components.find_plugins import FindPlugins
from components.get_plugin_details import PluginDetails
from components.theme import DetectTheme
from components.display_results import DisplayResult
from components.Is_wp import IsWP
from urllib.parse import urljoin
import json
from datetime import datetime
import time 
import os 

if __name__ == "__main__":
    print("WordPress Plugin & Theme Checker")
    website_url = input("Enter website URL (eg:https://example.com): ").strip()
   
    if not website_url.startswith(('http://', 'https://')):
        website_url = 'https://' + website_url
    
    print(f"\nChecking {website_url}...")
    time.sleep(1)

    if IsWP.is_wordpress_site(website_url):
        print("WordPress detected!")
        print("\nSearching for plugins and themes ...")
        
        try:
            # Find both plugins and themes
            plugins= FindPlugins.find_plugins(website_url)
            themes = DetectTheme.detect_wordpress_themes(website_url)
            print(f"\nFound {len(plugins)+len(themes)} plugins or features:")
            
            all_items = plugins + themes
            
            # Get plugin details from WordPress API
            for item in all_items:
                if item['type'] == 'plugin':
                    details = PluginDetails.get_plugin_details(item['slug'])
                    if details:
                        item['details'] = details

            
            # Define the Results directory (absolute path)
            script_dir = os.path.dirname(os.path.abspath(__file__))  # Gets the folder where the script is
            results_dir = os.path.join(script_dir, 'Results')
            # Create Results directory if it doesn't exist
            os.makedirs(results_dir, exist_ok=True)
            
            if all_items:
                print(f"\nFound {len(all_items)} items ({len(plugins)} plugins, {len(themes)} themes):")
                DisplayResult.display_results(all_items)

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
        
