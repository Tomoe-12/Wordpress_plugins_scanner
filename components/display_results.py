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

class DisplayResult :
    @staticmethod
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
