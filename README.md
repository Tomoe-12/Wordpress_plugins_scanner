Wordpress Plugins Scanner
This repository contains a Python-based tool designed to scan WordPress websites for installed plugins. It utilizes the WPScan API to identify plugins and their versions, helping security professionals and developers assess the security posture of WordPress sites.

Features
WPScan Integration: Leverages the WPScan API to detect plugins and their versions.

Plugin List Management: Supports custom plugin lists for targeted scanning.

Configuration Loader: Allows dynamic loading of configuration settings.

Caching Support: Utilizes caching to improve scan performance.

Requirements
Python 3.6 or higher

requests library

WPScan API key (optional, for enhanced scanning capabilities)

Installation
Clone the repository:

bash
Copy
Edit
git clone https://github.com/Tomoe-12/Wordpress_plugins_scanner.git
Navigate to the project directory:

bash
Copy
Edit
cd Wordpress_plugins_scanner
Install required dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Usage
Run the scanner with the following command:

bash
Copy
Edit
python scanner.py --url <target_url>
Replace <target_url> with the URL of the WordPress site you wish to scan.

For a list of available options, use:

bash
Copy
Edit
python scanner.py --help
Files Overview
scanner.py: Main script to initiate the plugin scanning process.

config_loader.py: Handles loading of configuration settings.

plugins.txt: Contains a list of plugins to check for.

wpscan_plugins_cache.json: Caches WPScan plugin data for performance optimization.

Results/: Directory where scan results are saved.

Contributing
Contributions are welcome! Please fork the repository, create a new branch, and submit a pull request with your proposed changes.

License
This project is licensed under the MIT License. See the LICENSE file for more details.

Disclaimer
This tool is intended for educational and security research purposes only. Ensure you have proper authorization before scanning any website. Unauthorized scanning may violate terms of service or local laws.

