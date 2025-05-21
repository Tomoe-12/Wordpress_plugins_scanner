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

class PluginDetails :
    @staticmethod
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
