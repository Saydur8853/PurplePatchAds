import os
import json
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure directories exist
for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

# Add custom Jinja2 test for regex matching
@app.template_test('regex_match')
def regex_match_test(value, pattern):
    """Test to match strings against regex patterns"""
    if value is None:
        return False
    return bool(re.search(pattern, str(value), re.IGNORECASE))

# PurplePatch seller IDs to check for
PURPLEPATCH_SELLERS = [
    'incrementx.com',
    'purplepatch.online',
    'adserver.purplepatch.online'
]

class AdsAnalyzer:
    def __init__(self):
        self.purplepatch_found = []
        self.competitors = []
        self.all_entries = []
        
    def parse_ads_txt(self, content):
        """Parse ads.txt content and extract information"""
        lines = content.split('\n')
        entries = []
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Remove line number prefix if present
            if '|' in line and line.split('|')[0].isdigit():
                line = '|'.join(line.split('|')[1:])
            
            parts = [part.strip() for part in line.split(',')]
            if len(parts) >= 3:
                domain = parts[0].strip()
                seller_id = parts[1].strip()
                relationship = parts[2].strip()
                cert_authority_id = parts[3].strip() if len(parts) > 3 else ''
                
                entry = {
                    'line_number': line_num,
                    'domain': domain,
                    'seller_id': seller_id,
                    'relationship': relationship,
                    'cert_authority_id': cert_authority_id,
                    'raw_line': line
                }
                entries.append(entry)
                
                # Check if this is a PurplePatch entry
                if any(pp in domain.lower() for pp in ['incrementx', 'purplepatch']):
                    self.purplepatch_found.append(entry)
                else:
                    self.competitors.append(entry)
        
        self.all_entries = entries
        return entries
    
    def analyze_competitors(self):
        """Identify and categorize competitors"""
        competitor_analysis = {}
        
        for entry in self.competitors:
            domain = entry['domain']
            if domain not in competitor_analysis:
                competitor_analysis[domain] = {
                    'domain': domain,
                    'entries': [],
                    'direct_count': 0,
                    'reseller_count': 0
                }
            
            competitor_analysis[domain]['entries'].append(entry)
            if entry['relationship'].upper() == 'DIRECT':
                competitor_analysis[domain]['direct_count'] += 1
            elif entry['relationship'].upper() == 'RESELLER':
                competitor_analysis[domain]['reseller_count'] += 1
        
        return competitor_analysis

class AdSlotAnalyzer:
    def __init__(self):
        self.slots = []
        
    def parse_ad_slot_code(self, content):
        """Parse ad slot code and extract positioning information"""
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all PurplePatch ad slots
        slots = soup.find_all('ins', attrs={'data-purplepatch-slotid': True})
        
        slot_info = []
        for slot in slots:
            slot_data = {
                'slot_id': slot.get('data-purplepatch-slotid'),
                'publisher_name': slot.get('data-publisher-name'),
                'publisher_url': slot.get('data-publisher-url'),
                'ad_type': slot.get('data-publisher-adtype'),
                'category': slot.get('data-publisher-category'),
                'position': slot.get('data-publisher-position'),
                'width': slot.get('data-publisher-width'),
                'height': slot.get('data-publisher-height'),
                'timestamp': slot.get('data-publisher-timestamp'),
                'viewability_score': self.calculate_viewability_score(slot)
            }
            slot_info.append(slot_data)
        
        self.slots = slot_info
        return slot_info
    
    def calculate_viewability_score(self, slot):
        """Calculate a basic viewability score based on position and size"""
        try:
            width = int(slot.get('data-publisher-width', 0))
            height = int(slot.get('data-publisher-height', 0))
            position = slot.get('data-publisher-position', '').lower()
            category = slot.get('data-publisher-category', '').lower()
            
            score = 50  # Base score
            
            # Size factor (larger ads typically more viewable)
            area = width * height
            if area >= 728 * 90:  # Large banners
                score += 20
            elif area >= 300 * 250:  # Medium rectangles
                score += 15
            elif area >= 320 * 100:  # Mobile banners
                score += 10
            
            # Position factor
            if 'home' in category:
                score += 10
            if 'article' in category:
                score += 15
            if 'mobile' in category:
                score += 5
            
            # Static positions are generally more viewable
            if position == 'static':
                score += 10
            
            return min(100, max(0, score))
        except:
            return 50  # Default score if calculation fails

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'ads_txt' not in request.files and 'ad_slot' not in request.files:
        flash('No files selected')
        return redirect(url_for('index'))
    
    analysis_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    results = {'analysis_id': analysis_id}
    
    # Process ads.txt file
    if 'ads_txt' in request.files and request.files['ads_txt'].filename:
        ads_file = request.files['ads_txt']
        if ads_file.filename != '':
            filename = secure_filename(ads_file.filename)
            ads_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{analysis_id}_ads_{filename}")
            ads_file.save(ads_path)
            
            # Analyze ads.txt
            with open(ads_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analyzer = AdsAnalyzer()
            analyzer.parse_ads_txt(content)
            competitor_analysis = analyzer.analyze_competitors()
            
            results['ads_txt'] = {
                'purplepatch_found': analyzer.purplepatch_found,
                'competitors': competitor_analysis,
                'total_entries': len(analyzer.all_entries),
                'purplepatch_count': len(analyzer.purplepatch_found),
                'competitor_count': len(analyzer.competitors)
            }
    
    # Process ad slot file
    if 'ad_slot' in request.files and request.files['ad_slot'].filename:
        slot_file = request.files['ad_slot']
        if slot_file.filename != '':
            filename = secure_filename(slot_file.filename)
            slot_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{analysis_id}_slot_{filename}")
            slot_file.save(slot_path)
            
            # Analyze ad slots
            with open(slot_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            slot_analyzer = AdSlotAnalyzer()
            slot_analyzer.parse_ad_slot_code(content)
            
            results['ad_slots'] = {
                'slots': slot_analyzer.slots,
                'total_slots': len(slot_analyzer.slots),
                'avg_viewability': sum(slot['viewability_score'] for slot in slot_analyzer.slots) / len(slot_analyzer.slots) if slot_analyzer.slots else 0
            }
    
    # Generate output files directly
    generate_output_files(results, analysis_id)
    
    return render_template('results.html', results=results)

@app.route('/analyze_url', methods=['POST'])
def analyze_url():
    publisher_url = request.form.get('publisher_url')
    if not publisher_url:
        flash('Please provide a publisher URL')
        return redirect(url_for('index'))
    
    analysis_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    results = {'analysis_id': analysis_id, 'publisher_url': publisher_url}
    
    try:
        # Try to fetch ads.txt from the publisher's domain
        if not publisher_url.startswith(('http://', 'https://')):
            publisher_url = 'https://' + publisher_url
        
        ads_txt_url = publisher_url.rstrip('/') + '/ads.txt'
        response = requests.get(ads_txt_url, timeout=10)
        
        if response.status_code == 200:
            analyzer = AdsAnalyzer()
            analyzer.parse_ads_txt(response.text)
            competitor_analysis = analyzer.analyze_competitors()
            
            results['ads_txt'] = {
                'purplepatch_found': analyzer.purplepatch_found,
                'competitors': competitor_analysis,
                'total_entries': len(analyzer.all_entries),
                'purplepatch_count': len(analyzer.purplepatch_found),
                'competitor_count': len(analyzer.competitors)
            }
            
            # Also try to detect ad slots from the website
            try:
                website_response = requests.get(publisher_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
                if website_response.status_code == 200:
                    slot_analyzer = AdSlotAnalyzer()
                    detected_slots = detect_ad_slots_from_website(website_response.text, publisher_url)
                    
                    if detected_slots:
                        results['ad_slots'] = {
                            'slots': detected_slots,
                            'total_slots': len(detected_slots),
                            'avg_viewability': sum(slot['viewability_score'] for slot in detected_slots) / len(detected_slots) if detected_slots else 0
                        }
            except Exception as e:
                # If website scraping fails, continue without ad slot data
                pass
        else:
            results['ads_txt_error'] = f'Could not fetch ads.txt (Status: {response.status_code})'
    
    except Exception as e:
        results['ads_txt_error'] = f'Error fetching ads.txt: {str(e)}'
    
    # Generate output files directly
    generate_output_files(results, analysis_id)
    
    return render_template('results.html', results=results)

@app.route('/sample_analysis')
def sample_analysis():
    """Analyze sample data for demonstration"""
    analysis_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    results = {'analysis_id': analysis_id, 'is_sample': True}
    
    # Analyze sample ads.txt file
    sample_ads_path = 'Sample/Ads.Txt/Banglanews24.txt'
    if os.path.exists(sample_ads_path):
        with open(sample_ads_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        analyzer = AdsAnalyzer()
        analyzer.parse_ads_txt(content)
        competitor_analysis = analyzer.analyze_competitors()
        
        results['ads_txt'] = {
            'purplepatch_found': analyzer.purplepatch_found,
            'competitors': competitor_analysis,
            'total_entries': len(analyzer.all_entries),
            'purplepatch_count': len(analyzer.purplepatch_found),
            'competitor_count': len(analyzer.competitors),
            'sample_file': 'Banglanews24.txt'
        }
    
    # Analyze sample ad slot file
    sample_slot_path = 'Sample/Adslot code/bangla_news24_adslot_codes_purple_patch.txt'
    if os.path.exists(sample_slot_path):
        with open(sample_slot_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        slot_analyzer = AdSlotAnalyzer()
        slot_analyzer.parse_ad_slot_code(content)
        
        results['ad_slots'] = {
            'slots': slot_analyzer.slots,
            'total_slots': len(slot_analyzer.slots),
            'avg_viewability': sum(slot['viewability_score'] for slot in slot_analyzer.slots) / len(slot_analyzer.slots) if slot_analyzer.slots else 0,
            'sample_file': 'bangla_news24_adslot_codes_purple_patch.txt'
        }
    
    # Generate output files directly
    generate_output_files(results, analysis_id)
    
    return render_template('results.html', results=results)


def detect_ad_slots_from_website(html_content, website_url):
    """Detect potential ad slots from website HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    detected_slots = []
    slot_id_counter = 1
    
    # Look for existing PurplePatch ad slots
    existing_slots = soup.find_all('ins', attrs={'data-purplepatch-slotid': True})
    for slot in existing_slots:
        slot_data = {
            'slot_id': slot.get('data-purplepatch-slotid'),
            'publisher_name': slot.get('data-publisher-name', extract_domain_name(website_url)),
            'publisher_url': website_url,
            'ad_type': slot.get('data-publisher-adtype', 'Banner'),
            'category': slot.get('data-publisher-category', 'Website Content'),
            'position': slot.get('data-publisher-position', 'Static'),
            'width': slot.get('data-publisher-width', '300'),
            'height': slot.get('data-publisher-height', '250'),
            'timestamp': slot.get('data-publisher-timestamp', datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z'),
            'viewability_score': calculate_basic_viewability_score(slot.get('data-publisher-width', '300'), slot.get('data-publisher-height', '250'), slot.get('data-publisher-position', 'Static'))
        }
        detected_slots.append(slot_data)
    
    # If no existing slots found, analyze potential ad slot positions
    if not detected_slots:
        potential_positions = analyze_potential_ad_positions(soup, website_url)
        detected_slots.extend(potential_positions)
    
    return detected_slots

def extract_domain_name(url):
    """Extract clean domain name from URL"""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    return domain.replace('www.', '').replace('.com', '').replace('.', ' ').title()

def calculate_basic_viewability_score(width, height, position):
    """Calculate basic viewability score"""
    try:
        w = int(width)
        h = int(height)
        area = w * h
        
        score = 50  # Base score
        
        # Size factor
        if area >= 728 * 90:  # Large banners
            score += 20
        elif area >= 300 * 250:  # Medium rectangles
            score += 15
        elif area >= 320 * 100:  # Mobile banners
            score += 10
        
        # Position factor
        if position and position.lower() == 'static':
            score += 10
        
        return min(100, max(0, score))
    except:
        return 60  # Default good score

def analyze_potential_ad_positions(soup, website_url):
    """Analyze website structure to suggest potential ad positions"""
    potential_slots = []
    domain_name = extract_domain_name(website_url)
    
    # Look for common ad container patterns
    ad_containers = []
    
    # Common ad container selectors
    selectors = [
        'div[class*="ad"]',
        'div[id*="ad"]', 
        'div[class*="banner"]',
        'div[class*="advertisement"]',
        'div[class*="google"]',
        'iframe[src*="google"]',
        'iframe[src*="doubleclick"]',
        'div.header',  # Header position
        'div.sidebar', # Sidebar position
        'div.content', # Content area
        'div.footer'   # Footer position
    ]
    
    position_counter = 1
    
    # Analyze header area
    header = soup.find(['header', 'div'], class_=lambda x: x and ('header' in x.lower() or 'top' in x.lower()))
    if header:
        potential_slots.append(create_suggested_slot(
            slot_id=str(position_counter),
            publisher_name=domain_name,
            publisher_url=website_url,
            category="Desktop Header",
            width="728",
            height="90",
            position="Header"
        ))
        position_counter += 1
    
    # Analyze sidebar area
    sidebar = soup.find(['aside', 'div'], class_=lambda x: x and ('sidebar' in x.lower() or 'side' in x.lower()))
    if sidebar:
        potential_slots.append(create_suggested_slot(
            slot_id=str(position_counter),
            publisher_name=domain_name,
            publisher_url=website_url,
            category="Desktop Sidebar",
            width="300",
            height="250",
            position="Sidebar"
        ))
        position_counter += 1
    
    # Analyze content area
    content = soup.find(['main', 'div', 'article'], class_=lambda x: x and ('content' in x.lower() or 'main' in x.lower() or 'article' in x.lower()))
    if content:
        potential_slots.append(create_suggested_slot(
            slot_id=str(position_counter),
            publisher_name=domain_name,
            publisher_url=website_url,
            category="Desktop Article Content",
            width="300",
            height="250",
            position="Content"
        ))
        position_counter += 1
    
    # Add mobile suggestions
    potential_slots.append(create_suggested_slot(
        slot_id=str(position_counter),
        publisher_name=domain_name,
        publisher_url=website_url,
        category="Mobile Header",
        width="320",
        height="100",
        position="Mobile Header"
    ))
    position_counter += 1
    
    potential_slots.append(create_suggested_slot(
        slot_id=str(position_counter),
        publisher_name=domain_name,
        publisher_url=website_url,
        category="Mobile Content",
        width="300",
        height="250",
        position="Mobile Content"
    ))
    
    return potential_slots[:5]  # Limit to 5 suggestions

def create_suggested_slot(slot_id, publisher_name, publisher_url, category, width, height, position):
    """Create a suggested ad slot"""
    return {
        'slot_id': slot_id,
        'publisher_name': publisher_name,
        'publisher_url': publisher_url,
        'ad_type': 'Banner',
        'category': category,
        'position': position,
        'width': width,
        'height': height,
        'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z',
        'viewability_score': calculate_basic_viewability_score(width, height, position)
    }

def generate_output_files(results, analysis_id):
    """Generate output files directly in sample format"""
    # Create folder structure like Sample folder
    ads_txt_folder = os.path.join(app.config['OUTPUT_FOLDER'], 'Ads.Txt')
    adslot_folder = os.path.join(app.config['OUTPUT_FOLDER'], 'Adslot code')
    os.makedirs(ads_txt_folder, exist_ok=True)
    os.makedirs(adslot_folder, exist_ok=True)
    
    # Determine website name from URL or use analysis ID
    website_name = "Analysis"
    if results.get('publisher_url'):
        from urllib.parse import urlparse
        domain = urlparse(results['publisher_url']).netloc
        website_name = domain.replace('www.', '').replace('.', '_')
    elif results.get('is_sample'):
        website_name = "Sample"
    
    # Generate ads.txt file in sample format
    if 'ads_txt' in results:
        ads_txt_content = generate_sample_ads_txt_format(results['ads_txt'])
        ads_txt_filename = f'{website_name}_{analysis_id}.txt'
        ads_txt_path = os.path.join(ads_txt_folder, ads_txt_filename)
        
        with open(ads_txt_path, 'w', encoding='utf-8') as f:
            f.write(ads_txt_content)
    
    # Generate ad slot file in sample format
    if 'ad_slots' in results:
        ad_slot_content = generate_sample_adslot_format(results['ad_slots'], website_name)
        ad_slot_filename = f'{website_name.lower()}_adslot_codes_purple_patch_{analysis_id}.txt'
        ad_slot_path = os.path.join(adslot_folder, ad_slot_filename)
        
        with open(ad_slot_path, 'w', encoding='utf-8') as f:
            f.write(ad_slot_content)

def generate_sample_ads_txt_format(ads_txt_data):
    """Generate ads.txt file in same format as sample files"""
    lines = []
    lines.append("MANAGERDOMAIN = incrementx.com")
    lines.append("")
    lines.append("IncrementX Ads.Txt Lines:")
    lines.append("")
    
    # Add all entries from the analysis back to ads.txt format
    line_number = 5
    
    # Add PurplePatch entries first
    if ads_txt_data.get('purplepatch_found'):
        for entry in ads_txt_data['purplepatch_found']:
            line = f"{entry['domain']}, {entry['seller_id']}, {entry['relationship']}"
            if entry.get('cert_authority_id'):
                line += f", {entry['cert_authority_id']}"
            lines.append(f"{line_number}|{line}")
            line_number += 1
    
    # Add empty line
    lines.append(f"{line_number}|")
    line_number += 1
    
    # Add competitor entries
    if ads_txt_data.get('competitors'):
        for domain, competitor in ads_txt_data['competitors'].items():
            for entry in competitor.get('entries', []):
                line = f"{entry['domain']}, {entry['seller_id']}, {entry['relationship']}"
                if entry.get('cert_authority_id'):
                    line += f", {entry['cert_authority_id']}"
                lines.append(f"{line_number}|{line}")
                line_number += 1
    
    return "\r\n".join(lines)

def generate_sample_adslot_format(ad_slot_data, website_name):
    """Generate ad slot file in same format as sample files"""
    lines = []
    
    if ad_slot_data.get('slots'):
        for i, slot in enumerate(ad_slot_data['slots'], 1):
            # Add slot description
            width = slot.get('width', '300')
            height = slot.get('height', '250')
            category = slot.get('category', 'Desktop Home Page & Article Page')
            
            lines.append(f"{i}. {width}x{height} - {category}")
            lines.append("")
            
            # Add slot HTML code
            slot_id = slot.get('slot_id', '93')
            publisher_name = slot.get('publisher_name', website_name)
            publisher_url = slot.get('publisher_url', f'https://www.{website_name.lower()}.com/')
            ad_type = slot.get('ad_type', 'Banner')
            position = slot.get('position', 'Static')
            timestamp = slot.get('timestamp', datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z')
            
            lines.append(f'<ins data-purplepatch-slotid="{slot_id}"')
            lines.append('         data-purplepatch-ct0="%%CLICK_URL_UNESC%%"')
            lines.append('         data-purplepatch-id="53126d71827fcba70ff68055b9a73ca1pdt"')
            lines.append(f'         data-publisher-name="{publisher_name}"')
            lines.append(f'         data-publisher-url="{publisher_url}"')
            lines.append('         data-publisher-platform=""')
            lines.append(f'         data-publisher-adtype="{ad_type}"')
            lines.append(f'         data-publisher-category="{category}"')
            lines.append(f'         data-publisher-position="{position}"')
            lines.append('         data-publisher-slot="0"')
            lines.append(f'         data-publisher-width="{width}"')
            lines.append(f'         data-publisher-height="{height}"')
            lines.append(f'         data-publisher-timestamp="{timestamp}">')
            lines.append('</ins>')
            lines.append('<script async src="//adserver.purplepatch.online/async.js" type="text/javascript"></script>')
            lines.append("")
            lines.append("")
    
    return "\n".join(lines)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)