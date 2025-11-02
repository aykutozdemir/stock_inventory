"""
Web scraping service for component datasheet retrieval
"""
import logging
import requests
import re
import urllib.parse
from typing import Optional, Dict, Any, List
from backend.services.datasheet_service import DatasheetService
from PyPDF2 import PdfReader
import io

logger = logging.getLogger(__name__)

class WebScrapingService:
    """Service for web scraping component datasheets"""

    def __init__(self):
        self.datasheet_service = DatasheetService()

    def search_component_specs(self, query: str) -> str:
        """Search for component specifications online"""
        try:
            logger.info(f"Searching for component specs: {query}")

            # Clean and prepare the search query
            search_query = self._prepare_search_query(query)

            # Try multiple sources
            results = []

            # Search Digi-Key
            digikey_result = self._search_digikey(search_query)
            if digikey_result:
                results.append(f"**Digi-Key**: {digikey_result}")

            # Search Mouser
            mouser_result = self._search_mouser(search_query)
            if mouser_result:
                results.append(f"**Mouser**: {mouser_result}")

            # Search Newark/Farnell
            newark_result = self._search_newark(search_query)
            if newark_result:
                results.append(f"**Newark/Farnell**: {newark_result}")

            # Search RS Components
            rs_result = self._search_rscomponents(search_query)
            if rs_result:
                results.append(f"**RS Components**: {rs_result}")

            if results:
                response = f"📄 **Datasheet Search Results for '{query}'**:\n\n" + "\n\n".join(results)

                # Check for common component specs
                common_specs = self.get_common_component_specs(search_query)
                if common_specs:
                    response += f"\n\n{common_specs}"

                response += f"\n\n💡 **Tip**: For detailed specifications, try searching with the exact part number (e.g., 'LM358N' instead of 'LM358 op amp')."

                # Also check if we have this in our local database
                local_info = self._check_local_datasheets(search_query)
                if local_info:
                    response += f"\n\n📚 **Local Database**: {local_info}"

                return response
            else:
                return f"🔍 No datasheet results found for '{query}'. Try:\n• Using exact part numbers (e.g., 'BC547' instead of 'transistor')\n• Checking manufacturer names (e.g., 'Texas Instruments LM358')\n• Searching for specific specifications"

        except Exception as e:
            logger.error(f"Error searching component specs: {e}")
            return f"❌ Search temporarily unavailable. Error: {str(e)}"

    def generate_datasheet_summary(self, pdf_data: bytes, component_name: str = "") -> Optional[str]:
        """Generate a comprehensive summary from PDF datasheet data"""
        try:
            # Extract text from PDF
            text = self._extract_text_from_pdf(pdf_data)
            if not text:
                return None

            # Generate comprehensive summary
            summary = self._create_comprehensive_summary(text, component_name)
            return summary

        except Exception as e:
            logger.error(f"Error generating datasheet summary: {e}")
            return None

    def _extract_text_from_pdf(self, pdf_data: bytes) -> Optional[str]:
        """Extract text content from PDF data"""
        try:
            pdf_file = io.BytesIO(pdf_data)
            pdf_reader = PdfReader(pdf_file)

            text_content = []
            # Extract text from first few pages (typically contain key specs)
            max_pages = min(10, len(pdf_reader.pages))  # Limit to first 10 pages

            for page_num in range(max_pages):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append(page_text)
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {e}")
                    continue

            full_text = '\n'.join(text_content)
            return full_text if full_text.strip() else None

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return None

    def _prepare_search_query(self, query: str) -> str:
        """Clean and optimize search query for component databases"""
        # Remove common words and clean up
        query = query.lower().strip()

        # Remove question words and common phrases
        remove_words = ['what', 'is', 'the', 'a', 'an', 'for', 'find', 'search', 'show', 'me', 'datasheet', 'spec', 'specification', 'özellik']
        words = query.split()
        filtered_words = [word for word in words if word not in remove_words and len(word) > 1]

        # Join back and clean
        search_query = ' '.join(filtered_words)

        # Handle common component abbreviations
        replacements = {
            'op amp': 'op-amp',
            'opamp': 'op-amp',
            'operational amplifier': 'op-amp',
            'led': 'LED',
            'mosfet': 'MOSFET',
            'transistor': 'transistor',
            'resistor': 'resistor',
            'capacitor': 'capacitor',
            'inductor': 'inductor',
            'diode': 'diode',
            'microcontroller': 'MCU microcontroller',
            'ic': 'IC',
            'chip': 'IC'
        }

        for old, new in replacements.items():
            search_query = search_query.replace(old, new)

        return search_query.strip()

    def _search_digikey(self, query: str) -> Optional[str]:
        """Search Digi-Key for component information"""
        try:
            # Digi-Key search URL
            search_url = f"https://www.digikey.com/en/products/result?keywords={query.replace(' ', '+')}"

            # For now, return a simulated result (in production, would use requests/beautifulsoup)
            # This is a placeholder that would be replaced with actual scraping
            return f"Component found: {query}. Visit: {search_url} for detailed specifications and datasheets."

        except Exception as e:
            logger.warning(f"Digi-Key search failed: {e}")
            return None

    def _search_mouser(self, query: str) -> Optional[str]:
        """Search Mouser Electronics for component information"""
        try:
            # Mouser search URL
            search_url = f"https://www.mouser.com/c/?q={query.replace(' ', '+')}"

            # Placeholder for actual implementation
            return f"Component found: {query}. Visit: {search_url} for detailed specifications and datasheets."

        except Exception as e:
            logger.warning(f"Mouser search failed: {e}")
            return None

    def _search_newark(self, query: str) -> Optional[str]:
        """Search Newark/Farnell for component information"""
        try:
            # Newark search URL
            search_url = f"https://www.newark.com/search?st={query.replace(' ', '+')}"

            # Placeholder for actual implementation
            return f"Component found: {query}. Visit: {search_url} for detailed specifications and datasheets."

        except Exception as e:
            logger.warning(f"Newark search failed: {e}")
            return None

    def _search_rscomponents(self, query: str) -> Optional[str]:
        """Search RS Components for component information"""
        try:
            # RS Components search URL
            search_url = f"https://uk.rs-online.com/web/c/?sra=oss&r=t&searchTerm={query.replace(' ', '+')}"

            # Placeholder for actual implementation
            return f"Component found: {query}. Visit: {search_url} for detailed specifications and datasheets."

        except Exception as e:
            logger.warning(f"RS Components search failed: {e}")
            return None

    def _check_local_datasheets(self, query: str) -> Optional[str]:
        """Check if we have this component in our local datasheet database"""
        try:
            # Search our local datasheet database
            results = self.datasheet_service.find_by_component(query)

            if results:
                datasheet = results[0]  # Get the first/most recent one
                return f"Available in local database: {datasheet['component_name']} (File: {datasheet['original_filename']}, Size: {datasheet['file_size']} bytes)"
            else:
                return None

        except Exception as e:
            logger.error(f"Error checking local datasheets: {e}")
            return None

    def get_common_component_specs(self, component_name: str) -> Optional[str]:
        """Get specifications by scraping from distributor websites"""
        try:
            # Try to get specs from Digi-Key first
            specs = self._scrape_component_specs_digikey(component_name)
            if specs:
                return specs

            # Fallback to Mouser
            specs = self._scrape_component_specs_mouser(component_name)
            if specs:
                return specs

            return None
        except Exception as e:
            logger.error(f"Error getting component specs: {e}")
            return None

    def _scrape_component_specs_digikey(self, component_name: str) -> Optional[str]:
        """Scrape basic specifications from Digi-Key product pages"""
        try:
            import requests
            from bs4 import BeautifulSoup

            # Search for the component
            search_url = f"https://www.digikey.com/en/products/result?keywords={component_name.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            response = requests.get(search_url, headers=headers, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'lxml')

                # Look for the first product link and try to get specs from the product page
                product_link = soup.find('a', href=re.compile(r'/products/detail'))
                if product_link:
                    product_url = f"https://www.digikey.com{product_link['href']}"
                    logger.info(f"Found Digi-Key product page: {product_url}")

                    # Try to get specs from the product page
                    product_response = requests.get(product_url, headers=headers, timeout=15)
                    if product_response.status_code == 200:
                        product_soup = BeautifulSoup(product_response.content, 'lxml')

                        specs = []

                        # Look for specification table
                        spec_table = product_soup.find('table', class_=re.compile(r'spec'))
                        if spec_table:
                            rows = spec_table.find_all('tr')
                            for row in rows[:12]:  # Limit rows
                                cols = row.find_all(['td', 'th'])
                                if len(cols) >= 2:
                                    param = cols[0].get_text(strip=True)
                                    value = cols[1].get_text(strip=True)
                                    if param and value and len(param) < 30 and len(value) < 30:
                                        # Clean and format
                                        param = re.sub(r'[^\w\s]', '', param).strip()
                                        value = re.sub(r'[^\w\s\.\-\(\)µΩmMkKVVAWHz°C°F%]', '', value).strip()
                                        if param and value and re.search(r'\d', value):
                                            specs.append(f"• {param}: {value}")

                        # If no table found, try alternative methods
                        if not specs:
                            # Look for spec elements with common patterns
                            spec_elements = product_soup.find_all(['span', 'div'], class_=re.compile(r'(value|spec|param)'))
                            for element in spec_elements[:15]:
                                text = element.get_text(strip=True)
                                if text and 3 < len(text) < 40 and re.search(r'\d', text):
                                    text = re.sub(r'[^\w\s\.\-\(\)µΩmMkKVVAWHz°C°F%]', '', text).strip()
                                    if text and any(unit in text for unit in ['V', 'A', 'W', 'Hz', '°C', 'µ', 'm', 'k', 'M', 'pF', 'nF', 'µF']):
                                        specs.append(f"• {text}")

                        if specs:
                            unique_specs = list(dict.fromkeys(specs))[:10]
                            return f"📋 **{component_name.upper()} - Key Specifications from Digi-Key:**\n\n" + "\n".join(unique_specs)

            # Fallback: provide general information
            return f"📄 **{component_name.upper()} - Digi-Key Search Results:**\n\nComponent found on Digi-Key. Visit the search results page to see detailed specifications from various manufacturers: {search_url}"

        except Exception as e:
            logger.warning(f"Failed to scrape Digi-Key for {component_name}: {e}")
            return f"📄 **{component_name.upper()} - Digi-Key:** Component search available at: {search_url}"

    def _scrape_component_specs_mouser(self, component_name: str) -> Optional[str]:
        """Scrape basic specifications from Mouser product pages"""
        try:
            import requests
            from bs4 import BeautifulSoup

            # Search for the component
            search_url = f"https://www.mouser.com/c/?q={component_name.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            response = requests.get(search_url, headers=headers, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'lxml')

                # Look for the first product link
                product_link = soup.find('a', href=re.compile(r'/products/'))
                if product_link and 'href' in product_link.attrs:
                    product_url = f"https://www.mouser.com{product_link['href']}"
                    logger.info(f"Found Mouser product page: {product_url}")

                    # Try to get specs from the product page
                    product_response = requests.get(product_url, headers=headers, timeout=15)
                    if product_response.status_code == 200:
                        product_soup = BeautifulSoup(product_response.content, 'lxml')

                        specs = []

                        # Look for specification tables on Mouser
                        spec_containers = product_soup.find_all(['div', 'table'], class_=re.compile(r'(specs|spec|characteristic)'))

                        for container in spec_containers[:3]:  # Limit containers
                            # Look for key-value pairs in the container
                            rows = container.find_all(['tr', 'div'])
                            for row in rows[:15]:  # Limit rows per container
                                # Try to find parameter and value
                                labels = row.find_all(['th', 'td', 'span', 'div'], class_=re.compile(r'(label|param|key)'))
                                values = row.find_all(['td', 'span', 'div'], class_=re.compile(r'(value|spec)'))

                                if labels and values:
                                    param = labels[0].get_text(strip=True)
                                    value = values[0].get_text(strip=True) if len(values) > 0 else ""

                                    if param and value and len(param) < 30 and len(value) < 30:
                                        param = re.sub(r'[^\w\s]', '', param).strip()
                                        value = re.sub(r'[^\w\s\.\-\(\)µΩmMkKVVAWHz°C°F%]', '', value).strip()
                                        if param and value and re.search(r'\d', value):
                                            specs.append(f"• {param}: {value}")

                        # If no structured specs found, try general pattern matching
                        if not specs:
                            page_text = product_soup.get_text()
                            spec_patterns = [
                                r'(?i)(voltage|current|resistance|capacitance|power|frequency)[:\-\s]*([^\s,]{1,20})',
                                r'(?i)(vcc|supply|input|output)[:\-\s]*([^\s,]{1,20})',
                                r'(?i)(gain|hfe|beta)[:\-\s]*([^\s,]{1,20})'
                            ]

                            for pattern in spec_patterns:
                                matches = re.findall(pattern, page_text)
                                for match in matches[:8]:
                                    param, value = match
                                    if value and re.search(r'\d', value):
                                        specs.append(f"• {param.title()}: {value}")

                        if specs:
                            unique_specs = list(dict.fromkeys(specs))[:8]
                            return f"📋 **{component_name.upper()} - Key Specifications from Mouser:**\n\n" + "\n".join(unique_specs)

            # Fallback: provide general information
            return f"📄 **{component_name.upper()} - Mouser Search Results:**\n\nComponent found on Mouser. Visit the search results page to see detailed specifications from various manufacturers: {search_url}"

        except Exception as e:
            logger.warning(f"Failed to scrape Mouser for {component_name}: {e}")
            return f"📄 **{component_name.upper()} - Mouser:** Component search available at: {search_url}"

    def download_datasheet_pdf(self, component_name: str) -> Optional[Dict[str, Any]]:
        """Download PDF datasheet and extract specifications"""
        try:
            logger.info(f"Attempting to download PDF datasheet for: {component_name}")

            # 1) Try DuckDuckGo PDF search first (more generic and robust)
            result = self._download_from_duckduckgo(component_name)
            if result:
                return result

            # 2) Try Digi-Key
            result = self._download_from_digikey(component_name)
            if result:
                return result

            # 3) Try Mouser
            result = self._download_from_mouser(component_name)
            if result:
                return result

            return None

        except Exception as e:
            logger.error(f"Error downloading datasheet PDF: {e}")
            return None

    def _download_from_duckduckgo(self, component_name: str) -> Optional[Dict[str, Any]]:
        """Search DuckDuckGo for '<component> datasheet pdf' and download the first PDF."""
        try:
            import requests
            from bs4 import BeautifulSoup

            query = f"{component_name} datasheet pdf"
            q = urllib.parse.quote_plus(query)
            search_url = f"https://duckduckgo.com/html/?q={q}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36'
            }

            resp = requests.get(search_url, headers=headers, timeout=15)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, 'lxml')
            links: List[str] = []
            for a in soup.find_all('a', href=True, class_=re.compile(r'result__a|result__url')):
                href = a['href']
                # DuckDuckGo may wrap links like /l/?kh=-1&uddg=<encoded>
                if href.startswith('/l/?') and 'uddg=' in href:
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    if 'uddg' in parsed:
                        href = urllib.parse.unquote(parsed['uddg'][0])
                links.append(href)

            # Prefer direct PDF links; else try visiting and checking for PDF content-type
            pdf_candidates = [u for u in links if '.pdf' in u.lower()]
            candidates = pdf_candidates[:3] or links[:5]

            for url in candidates:
                try:
                    r = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
                    content_type = r.headers.get('content-type', '').lower()
                    if r.status_code == 200 and ('application/pdf' in content_type or url.lower().endswith('.pdf')):
                        logger.info(f"Successfully downloaded PDF via DuckDuckGo: {url}")

                        specs = self._extract_specs_from_pdf(r.content, component_name)
                        filename = f"{component_name.replace(' ', '_')}_duckduckgo.pdf"

                        return {
                            'pdf_data': r.content,
                            'filename': filename,
                            'source_url': url,
                            'manufacturer': specs.get('manufacturer'),
                            'package_type': specs.get('package_type'),
                            'voltage_rating': specs.get('voltage_rating'),
                            'current_rating': specs.get('current_rating'),
                            'power_rating': specs.get('power_rating'),
                            'temperature_range': specs.get('temperature_range'),
                            'tolerance': specs.get('tolerance'),
                            'key_specifications': specs.get('key_specifications'),
                            'extracted_specs': specs.get('extracted_specs')
                        }
                except Exception as e:
                    logger.debug(f"DuckDuckGo candidate failed {url}: {e}")
                    continue

            return None
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
            return None

    def _download_from_digikey(self, component_name: str) -> Optional[Dict[str, Any]]:
        """Download PDF from Digi-Key"""
        try:
            import requests
            from bs4 import BeautifulSoup

            search_url = f"https://www.digikey.com/en/products/result?keywords={component_name.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            response = requests.get(search_url, headers=headers, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'lxml')

                # Look for datasheet download links
                datasheet_links = soup.find_all('a', href=re.compile(r'\.pdf'))

                for link in datasheet_links[:3]:  # Check first few PDF links
                    pdf_url = link['href']
                    if not pdf_url.startswith('http'):
                        pdf_url = f"https://www.digikey.com{pdf_url}"

                    # Try to download the PDF
                    try:
                        pdf_response = requests.get(pdf_url, headers=headers, timeout=15)

                        if pdf_response.status_code == 200 and 'application/pdf' in pdf_response.headers.get('content-type', ''):
                            logger.info(f"Successfully downloaded PDF from Digi-Key: {pdf_url}")

                            # Extract specifications from PDF
                            specs = self._extract_specs_from_pdf(pdf_response.content, component_name)

                            return {
                                'pdf_data': pdf_response.content,
                                'filename': f"{component_name.replace(' ', '_')}_digikey.pdf",
                                'source_url': pdf_url,
                                'manufacturer': specs.get('manufacturer'),
                                'package_type': specs.get('package_type'),
                                'voltage_rating': specs.get('voltage_rating'),
                                'current_rating': specs.get('current_rating'),
                                'power_rating': specs.get('power_rating'),
                                'temperature_range': specs.get('temperature_range'),
                                'tolerance': specs.get('tolerance'),
                                'key_specifications': specs.get('key_specifications'),
                                'extracted_specs': specs.get('extracted_specs')
                            }

                    except Exception as e:
                        logger.warning(f"Failed to download PDF from {pdf_url}: {e}")
                        continue

            return None

        except Exception as e:
            logger.warning(f"Error downloading from Digi-Key: {e}")
            return None

    def _download_from_mouser(self, component_name: str) -> Optional[Dict[str, Any]]:
        """Download PDF from Mouser"""
        try:
            import requests
            from bs4 import BeautifulSoup

            search_url = f"https://www.mouser.com/c/?q={component_name.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            response = requests.get(search_url, headers=headers, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'lxml')

                # Look for datasheet download links
                datasheet_links = soup.find_all('a', href=re.compile(r'\.pdf'))

                for link in datasheet_links[:3]:  # Check first few PDF links
                    pdf_url = link['href']
                    if not pdf_url.startswith('http'):
                        pdf_url = f"https://www.mouser.com{pdf_url}"

                    # Try to download the PDF
                    try:
                        pdf_response = requests.get(pdf_url, headers=headers, timeout=15)

                        if pdf_response.status_code == 200 and 'application/pdf' in pdf_response.headers.get('content-type', ''):
                            logger.info(f"Successfully downloaded PDF from Mouser: {pdf_url}")

                            # Extract specifications from PDF
                            specs = self._extract_specs_from_pdf(pdf_response.content, component_name)

                            return {
                                'pdf_data': pdf_response.content,
                                'filename': f"{component_name.replace(' ', '_')}_mouser.pdf",
                                'source_url': pdf_url,
                                'manufacturer': specs.get('manufacturer'),
                                'package_type': specs.get('package_type'),
                                'voltage_rating': specs.get('voltage_rating'),
                                'current_rating': specs.get('current_rating'),
                                'power_rating': specs.get('power_rating'),
                                'temperature_range': specs.get('temperature_range'),
                                'tolerance': specs.get('tolerance'),
                                'key_specifications': specs.get('key_specifications'),
                                'extracted_specs': specs.get('extracted_specs')
                            }

                    except Exception as e:
                        logger.warning(f"Failed to download PDF from {pdf_url}: {e}")
                        continue

            return None

        except Exception as e:
            logger.warning(f"Error downloading from Mouser: {e}")
            return None

    def _extract_specs_from_pdf(self, pdf_data: bytes, component_name: str) -> Dict[str, str]:
        """Extract specifications from PDF data"""
        try:
            # Extract text from PDF
            text = self._extract_text_from_pdf(pdf_data)
            if not text:
                return {}

            # Detect component type
            component_type = self._detect_component_type(text, component_name)

            # Extract component-type-specific specifications
            specs = self._extract_component_specifications(text, component_type)

            # Extract additional metadata
            metadata = self._extract_metadata(text, component_type)

            # Combine specifications
            extracted_specs = []
            if specs:
                extracted_specs.append(f"Specifications: {specs}")
            if metadata:
                extracted_specs.append(f"Additional: {metadata}")

            # Extract key individual specs for database fields
            key_specs = self._extract_key_specs(text, component_type)

            return {
                'extracted_specs': '\n'.join(extracted_specs) if extracted_specs else None,
                'key_specifications': specs,
                'manufacturer': key_specs.get('manufacturer'),
                'package_type': key_specs.get('package_type'),
                'voltage_rating': key_specs.get('voltage_rating'),
                'current_rating': key_specs.get('current_rating'),
                'power_rating': key_specs.get('power_rating'),
                'temperature_range': key_specs.get('temperature_range'),
                'tolerance': key_specs.get('tolerance')
            }

        except Exception as e:
            logger.error(f"Error extracting specs from PDF: {e}")
            return {}

    def _extract_key_specs(self, text: str, component_type: str) -> Dict[str, str]:
        """Extract individual key specifications for database fields"""
        specs = {}

        # Extract voltage rating
        voltage_patterns = [
            r'(?i)(?:peak\s+)?(?:inverse\s+)?voltage[:\-\s]*([0-9]+(?:\.[0-9]+)?)\s*V',
            r'(?i)voltage\s*rating[:\-\s]*([0-9]+(?:\.[0-9]+)?)\s*V',
            r'(?i)V[Rr]\s*=?\s*([0-9]+(?:\.[0-9]+)?)\s*V'
        ]
        for pattern in voltage_patterns:
            match = re.search(pattern, text)
            if match:
                specs['voltage_rating'] = match.group(1)
                break

        # Extract current rating
        current_patterns = [
            r'(?i)(?:average\s+)?(?:forward\s+)?current[:\-\s]*([0-9]+(?:\.[0-9]+)?)\s*(mA|A)',
            r'(?i)current\s*rating[:\-\s]*([0-9]+(?:\.[0-9]+)?)\s*(mA|A)',
            r'(?i)I[Ff]\s*=?\s*([0-9]+(?:\.[0-9]+)?)\s*(mA|A)'
        ]
        for pattern in current_patterns:
            match = re.search(pattern, text)
            if match:
                value = match.group(1)
                unit = match.group(2).lower() if len(match.groups()) > 1 else 'A'
                specs['current_rating'] = f"{value}{unit}"
                break

        # Extract power rating
        power_patterns = [
            r'(?i)(?:power\s+)?dissipation[:\-\s]*([0-9]+(?:\.[0-9]+)?)\s*(mW|W)',
            r'(?i)power\s*rating[:\-\s]*([0-9]+(?:\.[0-9]+)?)\s*(mW|W)',
            r'(?i)P[tT]\s*=?\s*([0-9]+(?:\.[0-9]+)?)\s*(mW|W)'
        ]
        for pattern in power_patterns:
            match = re.search(pattern, text)
            if match:
                value = match.group(1)
                unit = match.group(2).lower() if len(match.groups()) > 1 else 'W'
                specs['power_rating'] = f"{value}{unit}"
                break

        # Extract temperature range
        temp_patterns = [
            r'(?i)temperature[:\-\s]*([\-0-9]+(?:\.[0-9]+)?)[°\s]*[CF]\s*(?:to\s*[+-]?[0-9]+(?:\.[0-9]+)?)[°\s]*[CF]',
            r'(?i)operating\s+temperature[:\-\s]*([\-0-9]+)[°\s]*[CF]\s*(?:to\s*[+-]?[0-9]+)[°\s]*[CF]',
            r'(?i)T[jJ]\s*=?\s*([\-0-9]+)[°\s]*[CF]\s*(?:to\s*[+-]?[0-9]+)[°\s]*[CF]'
        ]
        for pattern in temp_patterns:
            match = re.search(pattern, text)
            if match:
                specs['temperature_range'] = match.group(0).strip()
                break

        # Extract tolerance
        tolerance_patterns = [
            r'(?i)tolerance[:\-\s]*[±]?([0-9]+(?:\.[0-9]+)?)\s*%',
            r'(?i)accuracy[:\-\s]*[±]?([0-9]+(?:\.[0-9]+)?)\s*%'
        ]
        for pattern in tolerance_patterns:
            match = re.search(pattern, text)
            if match:
                specs['tolerance'] = f"±{match.group(1)}%"
                break

        # Extract package type
        package_patterns = [
            r'(?i)package[:\-\s]*([A-Z0-9\-]+)',
            r'(?i)case[:\-\s]*([A-Z0-9\-]+)',
            r'(?i)TO-(\d+)',
            r'(?i)DO-(\d+)',
            r'(?i)SOIC-(\d+)',
            r'(?i)DIP-(\d+)'
        ]
        for pattern in package_patterns:
            match = re.search(pattern, text)
            if match:
                specs['package_type'] = match.group(1) if len(match.groups()) == 1 else match.group(0)
                break

        # Extract manufacturer
        mfg_patterns = [
            r'(?i)(?:by|from)\s+([A-Z][A-Za-z\s&]+?)(?:\s+(?:Inc|Corp|Ltd|GmbH|Co\.?|Technologies?|Semiconductor|Ltd\.?))?(?:\s|$)'
        ]
        for pattern in mfg_patterns:
            match = re.search(pattern, text)
            if match and len(match.group(1).strip()) > 3:
                manufacturer = match.group(1).strip()
                if manufacturer.lower() not in ['the', 'and', 'for', 'with', 'this', 'that']:
                    specs['manufacturer'] = manufacturer
                    break

        return specs

    def _create_comprehensive_summary(self, text: str, component_name: str = "") -> str:
        """Create a comprehensive summary from extracted text"""
        try:
            # Clean and normalize text
            text = self._clean_text(text)

            # Detect component type
            component_type = self._detect_component_type(text, component_name)

            # Extract key information sections
            summary_parts = []

            # Component identification with type
            if component_name:
                type_info = f" ({component_type})" if component_type else ""
                summary_parts.append(f"Component: {component_name}{type_info}")

            # Extract component-type-specific specifications
            specs = self._extract_component_specifications(text, component_type)
            if specs:
                summary_parts.append(f"Specifications: {specs}")

            # Extract features
            features = self._extract_features(text)
            if features:
                summary_parts.append(f"Key Features: {features}")

            # Extract electrical characteristics
            electrical = self._extract_electrical_characteristics(text)
            if electrical:
                summary_parts.append(f"Electrical Characteristics: {electrical}")

            # Extract additional metadata
            metadata = self._extract_metadata(text, component_type)
            if metadata:
                summary_parts.append(f"Additional: {metadata}")

            # Extract package information
            package = self._extract_package_info(text)
            if package:
                summary_parts.append(f"Package: {package}")

            # Extract applications
            applications = self._extract_applications(text)
            if applications:
                summary_parts.append(f"Applications: {applications}")

            # Combine all parts into comprehensive summary
            if summary_parts:
                return ' | '.join(summary_parts)
            else:
                # Fallback: create basic summary from first meaningful sentences
                sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20][:3]
                return '. '.join(sentences) + '.' if sentences else "Datasheet summary not available"

        except Exception as e:
            logger.error(f"Error creating comprehensive summary: {e}")
            return "Error generating summary"

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove extra whitespace and line breaks
        text = re.sub(r'\s+', ' ', text)
        # Remove page headers/footers (common patterns)
        text = re.sub(r'Page \d+.*?(?=\w)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\d{1,2}/\d{1,2}', '', text)  # Remove dates
        return text.strip()

    def _extract_specifications(self, text: str) -> Optional[str]:
        """Extract key specifications"""
        specs = []

        # Common specification patterns
        patterns = [
            r'(?i)voltage.*?[:=]\s*([^\s,;]+)',
            r'(?i)current.*?[:=]\s*([^\s,;]+)',
            r'(?i)power.*?[:=]\s*([^\s,;]+)',
            r'(?i)frequency.*?[:=]\s*([^\s,;]+)',
            r'(?i)temperature.*?[:=]\s*([^\s,;]+)',
            r'(?i)resistance.*?[:=]\s*([^\s,;]+)',
            r'(?i)capacitance.*?[:=]\s*([^\s,;]+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            specs.extend(matches[:2])  # Limit to 2 matches per type

        return ', '.join(specs[:5]) if specs else None  # Limit total specs

    def _extract_features(self, text: str) -> Optional[str]:
        """Extract key features"""
        features = []

        # Look for feature lists or bullet points
        feature_patterns = [
            r'(?i)(?:features?|advantages?)[:\-]*\s*(.*?)(?=\w{3,}[\s\.:]|$)',
            r'(?i)(?:•|\*|\-)\s*([^\•\*\-\n]+)',
        ]

        for pattern in feature_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match.strip()) > 10:  # Meaningful length
                    features.append(match.strip()[:50])  # Truncate long features

        return '; '.join(features[:3]) if features else None

    def _extract_electrical_characteristics(self, text: str) -> Optional[str]:
        """Extract electrical characteristics"""
        chars = []

        # Electrical parameter patterns
        electrical_patterns = [
            r'(?i)Vcc.*?[:=]\s*([^\s,;]+)',
            r'(?i)Vdd.*?[:=]\s*([^\s,;]+)',
            r'(?i)Icc.*?[:=]\s*([^\s,;]+)',
            r'(?i)Imax.*?[:=]\s*([^\s,;]+)',
        ]

        for pattern in electrical_patterns:
            matches = re.findall(pattern, text)
            chars.extend(matches[:1])  # One match per type

        return ', '.join(chars) if chars else None

    def _extract_package_info(self, text: str) -> Optional[str]:
        """Extract package information"""
        package_patterns = [
            r'(?i)package.*?[:\-]\s*([^\s,;]+)',
            r'(?i)(SOT|SOIC|DIP|QFN|QFP|BGA)\-?\d*',
            r'(?i)(TO|DO)\-?\d+',
        ]

        for pattern in package_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]

        return None

    def _extract_applications(self, text: str) -> Optional[str]:
        """Extract application information"""
        app_patterns = [
            r'(?i)applications?[:\-]*\s*(.*?)(?=\w{3,}[\s\.:]|$)',
        ]

        for pattern in app_patterns:
            matches = re.findall(pattern, text)
            if matches:
                app_text = matches[0][:100]  # Limit length
                return app_text.replace('\n', ' ').strip()

        return None

    def _detect_component_type(self, text: str, component_name: str = "") -> Optional[str]:
        """Detect component type from text and component name"""
        try:
            # Combine text and component name for better detection
            search_text = (component_name + " " + text).lower()

            # Component type detection patterns
            type_patterns = {
                'Resistor': [
                    r'\b(resistor|resistance|r\d{1,4})\b',
                    r'\b(ohm|Ω|kΩ|mΩ)\b',
                    r'\btolerance\s*[±]?\d+%',
                    r'\bpower\s*rating\b'
                ],
                'Capacitor': [
                    r'\b(capacitor|capacitance|c\d{1,4})\b',
                    r'\b(μf|nf|pf|farad)\b',
                    r'\belectrolytic|ceramic|tantalum\b',
                    r'\besr|equivalent\s*series\s*resistance\b'
                ],
                'Inductor': [
                    r'\b(inductor|coil|choke|l\d{1,4})\b',
                    r'\b(μh|nh|mh|henry)\b',
                    r'\bsaturation\s*current\b',
                    r'\bdc\s*resistance|dcr\b'
                ],
                'Diode': [
                    r'\b(diode|rectifier)\b',
                    r'\b(vf|forward\s*voltage)\b',
                    r'\b(vr|reverse\s*voltage)\b',
                    r'\b(1n\d{4}|1smd|schottky|zener)\b'
                ],
                'LED': [
                    r'\b(led|light\s*emitting\s*diode)\b',
                    r'\b(luminous|brightness)\b',
                    r'\b(wavelength|nm)\b',
                    r'\b(viewing\s*angle)\b'
                ],
                'Transistor': [
                    r'\b(transistor|BJT)\b',
                    r'\b(npn|pnp)\b',
                    r'\b(hfe|beta|gain)\b',
                    r'\b(collector|emitter|base)\b'
                ],
                'MOSFET': [
                    r'\b(mosfet|fet)\b',
                    r'\b(n-channel|p-channel)\b',
                    r'\b(vgs|gate\s*threshold)\b',
                    r'\b(rds|drain\s*source)\b'
                ],
                'Voltage Regulator': [
                    r'\b(regulator|ldo)\b',
                    r'\b(78\d+|lm\d+|mc\d+)\b',
                    r'\b(dropout\s*voltage)\b',
                    r'\b(output\s*voltage|vout)\b'
                ],
                'Op-Amp': [
                    r'\b(op.?amp|operational\s*amplifier|comparator)\b',
                    r'\b(lm\d+|tl\d+|ad\d+)\b',
                    r'\b(slew\s*rate|offset\s*voltage)\b',
                    r'\b(gain\s*bandwidth)\b'
                ],
                'Microcontroller': [
                    r'\b(microcontroller|microprocessor|ic|chip)\b',
                    r'\b(atmega|pic|stm32|esp32|arduino)\b',
                    r'\b(flash|ram|eeprom)\b',
                    r'\b(mhz|clock)\b'
                ],
                'Crystal': [
                    r'\b(crystal|oscillator|xtal)\b',
                    r'\b(hz|mhz)\b',
                    r'\b(load\s*capacitance)\b',
                    r'\b(frequency\s*tolerance)\b'
                ],
                'Relay': [
                    r'\b(relay|switch)\b',
                    r'\b(spdt|dpdt|spst)\b',
                    r'\b(coil\s*voltage)\b',
                    r'\b(contact\s*rating)\b'
                ],
                'Transformer': [
                    r'\b(transformer)\b',
                    r'\b(primary|secondary)\b',
                    r'\b(turns\s*ratio)\b',
                    r'\b(va|watts?)\b'
                ],
                'Sensor': [
                    r'\b(sensor|detector)\b',
                    r'\b(temperature|pressure|motion|light)\b',
                    r'\b(analog|digital|i2c|spi)\b',
                    r'\b(measurement\s*range)\b'
                ]
            }

            # Check for matches and score each type
            type_scores = {}
            for component_type, patterns in type_patterns.items():
                score = 0
                for pattern in patterns:
                    if re.search(pattern, search_text):
                        score += 1
                if score > 0:
                    type_scores[component_type] = score

            # Return the type with highest score if any found
            if type_scores:
                return max(type_scores, key=type_scores.get)

            return None

        except Exception as e:
            logger.error(f"Error detecting component type: {e}")
            return None

    def _extract_component_specifications(self, text: str, component_type: Optional[str]) -> Optional[str]:
        """Extract specifications based on component type"""
        try:
            specs = []

            if component_type == 'Resistor':
                specs.extend(self._extract_resistor_specs(text))
            elif component_type == 'Capacitor':
                specs.extend(self._extract_capacitor_specs(text))
            elif component_type == 'Inductor':
                specs.extend(self._extract_inductor_specs(text))
            elif component_type == 'Diode':
                specs.extend(self._extract_diode_specs(text))
            elif component_type == 'LED':
                specs.extend(self._extract_led_specs(text))
            elif component_type == 'Transistor':
                specs.extend(self._extract_transistor_specs(text))
            elif component_type == 'MOSFET':
                specs.extend(self._extract_mosfet_specs(text))
            elif component_type == 'Voltage Regulator':
                specs.extend(self._extract_regulator_specs(text))
            elif component_type == 'Op-Amp':
                specs.extend(self._extract_opamp_specs(text))
            elif component_type == 'Microcontroller':
                specs.extend(self._extract_microcontroller_specs(text))
            elif component_type == 'Crystal':
                specs.extend(self._extract_crystal_specs(text))
            elif component_type == 'Relay':
                specs.extend(self._extract_relay_specs(text))
            elif component_type == 'Transformer':
                specs.extend(self._extract_transformer_specs(text))
            elif component_type == 'Sensor':
                specs.extend(self._extract_sensor_specs(text))
            else:
                # Generic extraction for unknown types
                specs.extend(self._extract_generic_specs(text))

            return ', '.join(specs) if specs else None

        except Exception as e:
            logger.error(f"Error extracting component specifications: {e}")
            return None

    def _extract_resistor_specs(self, text: str) -> List[str]:
        """Extract resistor-specific specifications"""
        specs = []

        # Resistance value
        resistance_matches = re.findall(r'(?i)(resistance|value)[:=]\s*([^\s,;]+)', text)
        for match in resistance_matches[:2]:
            specs.append(f"Resistance: {match[1]}")

        # Power rating
        power_matches = re.findall(r'(?i)(power|wattage)[:=]\s*([^\s,;]+)', text)
        for match in power_matches[:1]:
            specs.append(f"Power: {match[1]}")

        # Tolerance
        tolerance_matches = re.findall(r'(?i)tolerance[:=]\s*[±]?([^\s,;]+)', text)
        for match in tolerance_matches[:1]:
            specs.append(f"Tolerance: {match}")

        # Temperature coefficient
        temp_coeff_matches = re.findall(r'(?i)(temp|temperature).*coefficient[:=]\s*([^\s,;]+)', text)
        for match in temp_coeff_matches[:1]:
            specs.append(f"Temp Coeff: {match[1]}")

        # Max working voltage
        voltage_matches = re.findall(r'(?i)(max|working|rated).*voltage[:=]\s*([^\s,;]+)', text)
        for match in voltage_matches[:1]:
            specs.append(f"Max Voltage: {match[1]}")

        return specs

    def _extract_capacitor_specs(self, text: str) -> List[str]:
        """Extract capacitor-specific specifications"""
        specs = []

        # Capacitance value
        cap_matches = re.findall(r'(?i)(capacitance|value)[:=]\s*([^\s,;]+)', text)
        for match in cap_matches[:2]:
            specs.append(f"Capacitance: {match[1]}")

        # Rated voltage
        voltage_matches = re.findall(r'(?i)(rated|working).*voltage[:=]\s*([^\s,;]+)', text)
        for match in voltage_matches[:1]:
            specs.append(f"Voltage: {match[1]}")

        # Tolerance
        tolerance_matches = re.findall(r'(?i)tolerance[:=]\s*[±]?([^\s,;]+)', text)
        for match in tolerance_matches[:1]:
            specs.append(f"Tolerance: {match}")

        # ESR
        esr_matches = re.findall(r'(?i)esr[:=]\s*([^\s,;]+)', text)
        for match in esr_matches[:1]:
            specs.append(f"ESR: {match}")

        # Leakage current
        leakage_matches = re.findall(r'(?i)leakage.*current[:=]\s*([^\s,;]+)', text)
        for match in leakage_matches[:1]:
            specs.append(f"Leakage: {match}")

        return specs

    def _extract_inductor_specs(self, text: str) -> List[str]:
        """Extract inductor-specific specifications"""
        specs = []

        # Inductance value
        ind_matches = re.findall(r'(?i)(inductance|value)[:=]\s*([^\s,;]+)', text)
        for match in ind_matches[:2]:
            specs.append(f"Inductance: {match[1]}")

        # Saturation current
        sat_matches = re.findall(r'(?i)saturation.*current[:=]\s*([^\s,;]+)', text)
        for match in sat_matches[:1]:
            specs.append(f"Sat Current: {match}")

        # DC resistance
        dcr_matches = re.findall(r'(?i)(dcr|dc.*resistance)[:=]\s*([^\s,;]+)', text)
        for match in dcr_matches[:1]:
            specs.append(f"DCR: {match[1]}")

        # Q factor
        q_matches = re.findall(r'(?i)(q|quality).*factor[:=]\s*([^\s,;]+)', text)
        for match in q_matches[:1]:
            specs.append(f"Q Factor: {match[1]}")

        # Self-resonant frequency
        srf_matches = re.findall(r'(?i)(srf|self.?resonant).*frequency[:=]\s*([^\s,;]+)', text)
        for match in srf_matches[:1]:
            specs.append(f"SRF: {match[1]}")

        return specs

    def _extract_diode_specs(self, text: str) -> List[str]:
        """Extract diode-specific specifications"""
        specs = []

        # Forward voltage
        vf_matches = re.findall(r'(?i)(vf|forward.*voltage)[:=]\s*([^\s,;]+)', text)
        for match in vf_matches[:1]:
            specs.append(f"Vf: {match[1]}")

        # Reverse voltage
        vr_matches = re.findall(r'(?i)(vr|reverse.*voltage|max.*reverse)[:=]\s*([^\s,;]+)', text)
        for match in vr_matches[:1]:
            specs.append(f"Vr: {match[1]}")

        # Reverse leakage current
        leakage_matches = re.findall(r'(?i)(reverse.*leakage|ir)[:=]\s*([^\s,;]+)', text)
        for match in leakage_matches[:1]:
            specs.append(f"Ir: {match[1]}")

        # Forward current
        if_matches = re.findall(r'(?i)(if|forward.*current)[:=]\s*([^\s,;]+)', text)
        for match in if_matches[:1]:
            specs.append(f"If: {match[1]}")

        # Reverse recovery time
        trr_matches = re.findall(r'(?i)(trr|reverse.*recovery.*time)[:=]\s*([^\s,;]+)', text)
        for match in trr_matches[:1]:
            specs.append(f"Trr: {match[1]}")

        return specs

    def _extract_led_specs(self, text: str) -> List[str]:
        """Extract LED-specific specifications"""
        specs = []

        # Forward voltage
        vf_matches = re.findall(r'(?i)(vf|forward.*voltage)[:=]\s*([^\s,;]+)', text)
        for match in vf_matches[:1]:
            specs.append(f"Vf: {match[1]}")

        # Forward current
        if_matches = re.findall(r'(?i)(if|forward.*current)[:=]\s*([^\s,;]+)', text)
        for match in if_matches[:1]:
            specs.append(f"If: {match[1]}")

        # Luminous intensity
        intensity_matches = re.findall(r'(?i)(luminous.*intensity|brightness)[:=]\s*([^\s,;]+)', text)
        for match in intensity_matches[:1]:
            specs.append(f"Intensity: {match[1]}")

        # Viewing angle
        angle_matches = re.findall(r'(?i)(viewing.*angle)[:=]\s*([^\s,;]+)', text)
        for match in angle_matches[:1]:
            specs.append(f"Angle: {match[1]}")

        # Wavelength
        wave_matches = re.findall(r'(?i)(wavelength|λ)[:=]\s*([^\s,;]+)', text)
        for match in wave_matches[:1]:
            specs.append(f"Wavelength: {match[1]}")

        return specs

    def _extract_transistor_specs(self, text: str) -> List[str]:
        """Extract transistor-specific specifications"""
        specs = []

        # Type (NPN/PNP)
        type_matches = re.findall(r'(?i)\b(npn|pnp)\b', text)
        if type_matches:
            specs.append(f"Type: {type_matches[0].upper()}")

        # Collector current
        ic_matches = re.findall(r'(?i)(ic|collector.*current)[:=]\s*([^\s,;]+)', text)
        for match in ic_matches[:1]:
            specs.append(f"Ic: {match[1]}")

        # Collector-emitter voltage
        vce_matches = re.findall(r'(?i)(vce|collector.*emitter.*voltage)[:=]\s*([^\s,;]+)', text)
        for match in vce_matches[:1]:
            specs.append(f"Vce: {match[1]}")

        # Gain
        gain_matches = re.findall(r'(?i)(hfe|beta|gain)[:=]\s*([^\s,;]+)', text)
        for match in gain_matches[:1]:
            specs.append(f"Gain: {match[1]}")

        # Transition frequency
        ft_matches = re.findall(r'(?i)(ft|transition.*frequency)[:=]\s*([^\s,;]+)', text)
        for match in ft_matches[:1]:
            specs.append(f"fT: {match[1]}")

        # Power dissipation
        power_matches = re.findall(r'(?i)(power.*dissipation|ptot)[:=]\s*([^\s,;]+)', text)
        for match in power_matches[:1]:
            specs.append(f"Ptot: {match[1]}")

        return specs

    def _extract_mosfet_specs(self, text: str) -> List[str]:
        """Extract MOSFET-specific specifications"""
        specs = []

        # Type (N/P Channel)
        type_matches = re.findall(r'(?i)\b(n-channel|p-channel)\b', text)
        if type_matches:
            specs.append(f"Type: {type_matches[0].title()}")

        # Drain-source voltage
        vds_matches = re.findall(r'(?i)(vds|drain.*source.*voltage)[:=]\s*([^\s,;]+)', text)
        for match in vds_matches[:1]:
            specs.append(f"Vds: {match[1]}")

        # Gate threshold voltage
        vgs_matches = re.findall(r'(?i)(vgs|gate.*threshold.*voltage)[:=]\s*([^\s,;]+)', text)
        for match in vgs_matches[:1]:
            specs.append(f"Vgs(th): {match[1]}")

        # Drain current
        id_matches = re.findall(r'(?i)(id|drain.*current)[:=]\s*([^\s,;]+)', text)
        for match in id_matches[:1]:
            specs.append(f"Id: {match[1]}")

        # Rds(on)
        rds_matches = re.findall(r'(?i)(rds|rds\(on\))[:=]\s*([^\s,;]+)', text)
        for match in rds_matches[:1]:
            specs.append(f"Rds(on): {match[1]}")

        # Gate charge
        qg_matches = re.findall(r'(?i)(qg|gate.*charge)[:=]\s*([^\s,;]+)', text)
        for match in qg_matches[:1]:
            specs.append(f"Qg: {match[1]}")

        return specs

    def _extract_regulator_specs(self, text: str) -> List[str]:
        """Extract voltage regulator-specific specifications"""
        specs = []

        # Input voltage range
        vin_matches = re.findall(r'(?i)(input.*voltage|vin)[:=]\s*([^\s,;]+)', text)
        for match in vin_matches[:1]:
            specs.append(f"Vin: {match[1]}")

        # Output voltage
        vout_matches = re.findall(r'(?i)(output.*voltage|vout)[:=]\s*([^\s,;]+)', text)
        for match in vout_matches[:1]:
            specs.append(f"Vout: {match[1]}")

        # Output current
        iout_matches = re.findall(r'(?i)(output.*current|iout)[:=]\s*([^\s,;]+)', text)
        for match in iout_matches[:1]:
            specs.append(f"Iout: {match[1]}")

        # Dropout voltage
        dropout_matches = re.findall(r'(?i)(dropout.*voltage)[:=]\s*([^\s,;]+)', text)
        for match in dropout_matches[:1]:
            specs.append(f"Dropout: {match[1]}")

        # Efficiency
        eff_matches = re.findall(r'(?i)efficiency[:=]\s*([^\s,;]+)', text)
        for match in eff_matches[:1]:
            specs.append(f"Efficiency: {match[1]}")

        # Quiescent current
        iq_matches = re.findall(r'(?i)(iq|quiescent.*current)[:=]\s*([^\s,;]+)', text)
        for match in iq_matches[:1]:
            specs.append(f"Iq: {match[1]}")

        return specs

    def _extract_opamp_specs(self, text: str) -> List[str]:
        """Extract op-amp-specific specifications"""
        specs = []

        # Input offset voltage
        vos_matches = re.findall(r'(?i)(vos|offset.*voltage)[:=]\s*([^\s,;]+)', text)
        for match in vos_matches[:1]:
            specs.append(f"Vos: {match[1]}")

        # Input bias current
        ib_matches = re.findall(r'(?i)(ib|bias.*current)[:=]\s*([^\s,;]+)', text)
        for match in ib_matches[:1]:
            specs.append(f"Ib: {match[1]}")

        # Slew rate
        slew_matches = re.findall(r'(?i)(slew.*rate)[:=]\s*([^\s,;]+)', text)
        for match in slew_matches[:1]:
            specs.append(f"Slew Rate: {match[1]}")

        # Gain bandwidth product
        gbp_matches = re.findall(r'(?i)(gain.*bandwidth|gbp)[:=]\s*([^\s,;]+)', text)
        for match in gbp_matches[:1]:
            specs.append(f"GBP: {match[1]}")

        # Supply voltage range
        vcc_matches = re.findall(r'(?i)(supply.*voltage|vcc)[:=]\s*([^\s,;]+)', text)
        for match in vcc_matches[:1]:
            specs.append(f"Vcc: {match[1]}")

        return specs

    def _extract_microcontroller_specs(self, text: str) -> List[str]:
        """Extract microcontroller-specific specifications"""
        specs = []

        # Supply voltage
        vcc_matches = re.findall(r'(?i)(supply.*voltage|vcc|operating.*voltage)[:=]\s*([^\s,;]+)', text)
        for match in vcc_matches[:1]:
            specs.append(f"Vcc: {match[1]}")

        # Operating frequency
        freq_matches = re.findall(r'(?i)(operating.*frequency|clock.*speed)[:=]\s*([^\s,;]+)', text)
        for match in freq_matches[:1]:
            specs.append(f"Frequency: {match[1]}")

        # Memory specs
        flash_matches = re.findall(r'(?i)flash[:=]\s*([^\s,;]+)', text)
        for match in flash_matches[:1]:
            specs.append(f"Flash: {match[1]}")

        ram_matches = re.findall(r'(?i)ram[:=]\s*([^\s,;]+)', text)
        for match in ram_matches[:1]:
            specs.append(f"RAM: {match[1]}")

        eeprom_matches = re.findall(r'(?i)eeprom[:=]\s*([^\s,;]+)', text)
        for match in eeprom_matches[:1]:
            specs.append(f"EEPROM: {match[1]}")

        # Temperature range
        temp_matches = re.findall(r'(?i)(temperature.*range|operating.*temp)[:=]\s*([^\s,;]+)', text)
        for match in temp_matches[:1]:
            specs.append(f"Temp Range: {match[1]}")

        return specs

    def _extract_crystal_specs(self, text: str) -> List[str]:
        """Extract crystal/oscillator-specific specifications"""
        specs = []

        # Frequency
        freq_matches = re.findall(r'(?i)(frequency|freq)[:=]\s*([^\s,;]+)', text)
        for match in freq_matches[:1]:
            specs.append(f"Frequency: {match[1]}")

        # Load capacitance
        load_matches = re.findall(r'(?i)(load.*capacitance|cl)[:=]\s*([^\s,;]+)', text)
        for match in load_matches[:1]:
            specs.append(f"Load Cap: {match[1]}")

        # Frequency tolerance
        tol_matches = re.findall(r'(?i)(frequency.*tolerance|tolerance)[:=]\s*([^\s,;]+)', text)
        for match in tol_matches[:1]:
            specs.append(f"Tolerance: {match[1]}")

        # Drive level
        drive_matches = re.findall(r'(?i)(drive.*level)[:=]\s*([^\s,;]+)', text)
        for match in drive_matches[:1]:
            specs.append(f"Drive Level: {match[1]}")

        return specs

    def _extract_relay_specs(self, text: str) -> List[str]:
        """Extract relay-specific specifications"""
        specs = []

        # Coil voltage
        coil_matches = re.findall(r'(?i)(coil.*voltage)[:=]\s*([^\s,;]+)', text)
        for match in coil_matches[:1]:
            specs.append(f"Coil Voltage: {match[1]}")

        # Coil resistance
        res_matches = re.findall(r'(?i)(coil.*resistance)[:=]\s*([^\s,;]+)', text)
        for match in res_matches[:1]:
            specs.append(f"Coil Resistance: {match[1]}")

        # Contact rating
        contact_matches = re.findall(r'(?i)(contact.*rating)[:=]\s*([^\s,;]+)', text)
        for match in contact_matches[:1]:
            specs.append(f"Contact Rating: {match[1]}")

        # Contact form
        form_matches = re.findall(r'(?i)(contact.*form|configuration)[:=]\s*([^\s,;]+)', text)
        for match in form_matches[:1]:
            specs.append(f"Contact Form: {match[1]}")

        return specs

    def _extract_transformer_specs(self, text: str) -> List[str]:
        """Extract transformer-specific specifications"""
        specs = []

        # Primary/Secondary voltage
        prim_matches = re.findall(r'(?i)(primary.*voltage)[:=]\s*([^\s,;]+)', text)
        for match in prim_matches[:1]:
            specs.append(f"Primary V: {match[1]}")

        sec_matches = re.findall(r'(?i)(secondary.*voltage)[:=]\s*([^\s,;]+)', text)
        for match in sec_matches[:1]:
            specs.append(f"Secondary V: {match[1]}")

        # Power rating
        power_matches = re.findall(r'(?i)(power.*rating|va|watts?)[:=]\s*([^\s,;]+)', text)
        for match in power_matches[:1]:
            specs.append(f"Power: {match[1]}")

        # Turns ratio
        ratio_matches = re.findall(r'(?i)(turns.*ratio)[:=]\s*([^\s,;]+)', text)
        for match in ratio_matches[:1]:
            specs.append(f"Turns Ratio: {match[1]}")

        return specs

    def _extract_sensor_specs(self, text: str) -> List[str]:
        """Extract sensor-specific specifications"""
        specs = []

        # Supply voltage
        vcc_matches = re.findall(r'(?i)(supply.*voltage|vcc)[:=]\s*([^\s,;]+)', text)
        for match in vcc_matches[:1]:
            specs.append(f"Vcc: {match[1]}")

        # Output type
        output_matches = re.findall(r'(?i)(output.*type)[:=]\s*([^\s,;]+)', text)
        for match in output_matches[:1]:
            specs.append(f"Output: {match[1]}")

        # Measurement range
        range_matches = re.findall(r'(?i)(measurement.*range|range)[:=]\s*([^\s,;]+)', text)
        for match in range_matches[:1]:
            specs.append(f"Range: {match[1]}")

        # Sensitivity
        sens_matches = re.findall(r'(?i)sensitivity[:=]\s*([^\s,;]+)', text)
        for match in sens_matches[:1]:
            specs.append(f"Sensitivity: {match[1]}")

        # Accuracy
        acc_matches = re.findall(r'(?i)accuracy[:=]\s*([^\s,;]+)', text)
        for match in acc_matches[:1]:
            specs.append(f"Accuracy: {match[1]}")

        return specs

    def _extract_metadata(self, text: str, component_type: Optional[str]) -> Optional[str]:
        """Extract additional metadata applicable to most components"""
        metadata = []

        # Operating temperature range for non-microcontroller components
        if component_type not in ['Microcontroller']:
            temp_patterns = [
                r'(?i)operating\s+temperature[:\-]\s*([\-+]?\d+°?[CF]\s*(?:to\s*[+-]?\d+°?[CF]|[+-]?\d+°?[CF]))',
                r'(?i)junction\s+temp[:\-]\s*([\-+]?\d+°?[CF]\s*(?:to\s*[+-]?\d+°?[CF]|[+-]?\d+°?[CF]))'
            ]
            for pattern in temp_patterns:
                temp_match = re.search(pattern, text)
                if temp_match:
                    metadata.append(f"Op Temp: {temp_match.group(1).strip()}")
                    break

        # Mounting type detection
        if re.search(r'(?i)through.hole|tht|axial|radial', text):
            metadata.append("Mounting: Through Hole")
        elif re.search(r'(?i)surface.mount|smt| gull.wing|j.leaded', text):
            metadata.append("Mounting: Surface Mount")

        # Manufacturer extraction from common formats
        mfg_patterns = [
            r'(?i)by\s+([A-Z][A-Za-z\s&]+?)(?:\s+(?:Inc|Corp|Ltd|GmbH|Co\.?|Technologies?|Semiconductor|Ltd\.?))?(?:\s|$)',
            r'(?i)from\s+([A-Z][A-Za-z\s&]+?)(?:\s+(?:Inc|Corp|Ltd|GmbH|Co\.?|Technologies?|Semiconductor|Ltd\.?))?(?:\s|$)'
        ]
        for pattern in mfg_patterns:
            mfg_match = re.search(pattern, text)
            if mfg_match and len(mfg_match.group(1).strip()) > 3:
                manufacturer = mfg_match.group(1).strip()
                if manufacturer.lower() not in ['the', 'and', 'for', 'with', 'this', 'that']:
                    metadata.append(f"Mfg: {manufacturer}")
                    break

        # Standards and compliance (only add if not already mentioned in features)
        standards = []
        if re.search(r'(?i)rohs\s*(?:compliant|conform|certified)', text):
            standards.append("RoHS")
        if re.search(r'(?i)aec.?q\d+|automotive\s+(?:qualified|grade)', text):
            standards.append("Automotive")
        if re.search(r'(?i)military|mil.?std|space\s+(?:qualified|grade)', text):
            standards.append("Military")

        if standards:
            metadata.append(f"Standards: {', '.join(standards)}")

        return ', '.join(metadata) if metadata else None

    def _extract_generic_specs(self, text: str) -> List[str]:
        """Extract generic specifications for unknown component types"""
        specs = []

        # Generic voltage specs
        voltage_matches = re.findall(r'(?i)voltage[:=]\s*([^\s,;]+)', text)
        for match in voltage_matches[:2]:
            specs.append(f"Voltage: {match}")

        # Generic current specs
        current_matches = re.findall(r'(?i)current[:=]\s*([^\s,;]+)', text)
        for match in current_matches[:2]:
            specs.append(f"Current: {match}")

        # Generic power specs
        power_matches = re.findall(r'(?i)power[:=]\s*([^\s,;]+)', text)
        for match in power_matches[:1]:
            specs.append(f"Power: {match}")

        # Generic frequency specs
        freq_matches = re.findall(r'(?i)frequency[:=]\s*([^\s,;]+)', text)
        for match in freq_matches[:1]:
            specs.append(f"Frequency: {match}")

        return specs
