from components.find_plugins import FindPlugins
import requests
from bs4 import BeautifulSoup

class IsWP :
    @staticmethod
    def is_wordpress_site(url):
       
        try:
            # Standard checks first
            if FindPlugins.standard_wordpress_checks(url):
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
