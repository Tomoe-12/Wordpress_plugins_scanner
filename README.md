# Wordpress Plugins Scanner

A Python tool to scan WordPress websites for installed plugins using the WPScan API. This helps security researchers and developers identify plugins and their versions for security assessment purposes.

---

## Features

- Integrates with WPScan API for plugin detection  
- Supports custom plugin lists for scanning  
- Loads configuration dynamically  
- Implements caching for improved performance  

---

## Requirements

- Python 3.6+  
- `requests` library  
- (Optional) WPScan API key for enhanced scanning  

---

## Installation

```bash
git clone https://github.com/Tomoe-12/Wordpress_plugins_scanner.git
cd Wordpress_plugins_scanner
pip install -r requirements.txt
```

---

## Usage

To scan a WordPress site for installed plugins, run the scanner with the following command:

```bash
python scanner.py --url <target_url>
```

Replace `<target_url>` with the URL of the WordPress site you want to scan.

### Additional Options

You can view all available command-line options by running:

```bash
python scanner.py --help
```

This will display options such as specifying output directories, using custom plugin lists, or enabling verbose logging (if supported).

---

## Project Structure

- `scanner.py` — Main scanning script  
- `config_loader.py` — Loads configuration settings  
- `plugins.txt` — List of plugins to scan for  
- `wpscan_plugins_cache.json` — Cache for WPScan plugin data  
- `Results/` — Directory where scan results are saved  

---

## Contributing

Contributions are welcome! Please fork the repo, create a branch, and submit a pull request.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Disclaimer

This tool is for educational and security research purposes only. Always obtain proper authorization before scanning any website. Unauthorized scanning may violate laws or terms of service.
