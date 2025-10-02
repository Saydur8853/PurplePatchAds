# PurplePatch Ads - Architecture & Implementation Documentation

## Project Overview

PurplePatch Ads is a comprehensive web-based advertising analysis tool designed to analyze publisher ads.txt files and ad slot implementations. The system helps identify PurplePatch ad network presence, analyze competitors, and optimize ad slot positioning for better viewability scores.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [System Components](#system-components)
- [Technology Stack](#technology-stack)
- [Core Implementation](#core-implementation)
- [Data Flow Architecture](#data-flow-architecture)
- [Business Logic](#business-logic)
- [API Design](#api-design)
- [File Processing Pipeline](#file-processing-pipeline)
- [Assumptions Made](#assumptions-made)
- [Security Considerations](#security-considerations)
- [Performance Optimizations](#performance-optimizations)
- [Error Handling Strategy](#error-handling-strategy)
- [Future Enhancement Opportunities](#future-enhancement-opportunities)

## Architecture Overview

The PurplePatch Ads system follows a **Flask-based MVC (Model-View-Controller)** architecture with a focus on:

- **Separation of Concerns**: Distinct analyzers for different data types
- **Modular Design**: Each component handles specific functionality
- **RESTful API Design**: Clean HTTP endpoints for different operations
- **File Processing Pipeline**: Structured approach to handle various input formats

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
├─────────────────┬─────────────────┬─────────────────────────┤
│   HTML Templates │   CSS/JS Assets │    Flask Routes        │
│   - base.html    │   - Bootstrap   │    - index()           │
│   - index.html   │   - Font Awesome│    - upload_files()    │
│   - results.html │   - Custom CSS  │    - analyze_url()     │
└─────────────────┴─────────────────┴─────────────────────────┤
├─────────────────────────────────────────────────────────────┤
│                    Business Logic Layer                     │
├─────────────────┬───────────────────────┬─────────────────────┤
│   AdsAnalyzer   │   AdSlotAnalyzer     │   Data Processors   │
│   - parse_ads_txt│   - parse_ad_slot_   │   - File generators │
│   - analyze_comp │     code()           │   - URL fetchers    │
│   - competitor   │   - calculate_view   │   - Content parsers │
│     analysis()   │     ability_score()  │                     │
└─────────────────┴───────────────────────┴─────────────────────┤
├─────────────────────────────────────────────────────────────┤
│                    Data Access Layer                        │
├─────────────────┬───────────────────────┬─────────────────────┤
│   File System   │   HTTP Requests      │   Content Analysis  │
│   - Upload dir   │   - ads.txt fetching │   - BeautifulSoup   │
│   - Output dir   │   - Website scraping │   - Regex parsing   │
│   - Sample data  │   - URL validation   │   - Pattern matching│
└─────────────────┴───────────────────────┴─────────────────────┘
```

## System Components

### 1. Core Flask Application (`app.py`)

**Purpose**: Central application orchestrator and HTTP request handler

**Key Responsibilities**:
- Route handling and request/response management
- File upload processing and validation
- Integration between analyzers and output generators
- Error handling and user feedback

**Design Patterns Applied**:
- **Factory Pattern**: Flask app configuration and setup
- **Template Method**: Consistent request processing flow
- **Dependency Injection**: Analyzer instances created per request

### 2. AdsAnalyzer Class

**Purpose**: Specialized parser and analyzer for ads.txt files

**Core Functionality**:
```python
class AdsAnalyzer:
    - parse_ads_txt(content) -> List[Dict]     # Parse ads.txt format
    - analyze_competitors() -> Dict            # Categorize competitors
    - identify_purplepatch() -> List[Dict]     # Find PurplePatch entries
```

**Key Features**:
- **Line-by-line parsing** with error tolerance
- **Competitor categorization** (Direct vs Reseller relationships)
- **PurplePatch identification** using domain pattern matching
- **Data validation** and cleanup

### 3. AdSlotAnalyzer Class

**Purpose**: HTML content analyzer for ad slot positioning and optimization

**Core Functionality**:
```python
class AdSlotAnalyzer:
    - parse_ad_slot_code(content) -> List[Dict]    # Extract ad slots
    - calculate_viewability_score(slot) -> Int     # Score algorithm
    - analyze_potential_positions() -> List[Dict]  # Suggest positions
```

**Viewability Scoring Algorithm**:
- **Base Score**: 50 points
- **Size Factor**: +20 for large banners (728x90+), +15 for medium rectangles (300x250+)
- **Position Factor**: +10 for static positioning, +15 for article content
- **Category Factor**: +10 for homepage, +5 for mobile optimization

### 4. Web Scraping Engine

**Purpose**: Real-time website analysis and ads.txt fetching

**Implementation**:
- **URL validation** and normalization
- **ads.txt automatic discovery** (`domain.com/ads.txt`)
- **HTML content analysis** for existing ad slots
- **Error handling** for network timeouts and access restrictions

## Technology Stack

### Backend Technologies
- **Python 3.7+**: Core programming language
- **Flask 3.1.2**: Web application framework
- **Werkzeug 3.1.3**: WSGI utilities and file handling
- **Requests 2.32.5**: HTTP library for web scraping

### Data Processing Libraries
- **BeautifulSoup4 4.14.2**: HTML/XML parsing and manipulation
- **Pandas 2.3.3**: Data analysis and CSV export capabilities
- **Matplotlib 3.10.6**: Visualization and chart generation
- **Seaborn 0.13.2**: Statistical data visualization

### Frontend Technologies
- **Bootstrap 5.3.0**: Responsive UI framework
- **Font Awesome 6.0.0**: Icon library
- **Vanilla JavaScript**: Client-side validation and interactions
- **Jinja2 Templates**: Server-side template rendering

## Core Implementation

### Ads.txt Parsing Algorithm

```python
def parse_ads_txt(self, content):
    """
    Multi-step parsing process:
    1. Split content by lines
    2. Filter comments and empty lines
    3. Handle line number prefixes (format: "number|content")
    4. Parse CSV-style fields (domain, seller_id, relationship, cert_id)
    5. Categorize entries (PurplePatch vs Competitors)
    6. Validate data integrity
    """
```

**Key Implementation Details**:
- **Error Tolerance**: Continues parsing even with malformed lines
- **Flexible Format Support**: Handles both raw ads.txt and numbered formats
- **Pattern Matching**: Uses regex and string matching for PurplePatch identification
- **Data Normalization**: Cleans whitespace and standardizes field formats

### Ad Slot Detection Algorithm

```python
def parse_ad_slot_code(self, content):
    """
    HTML Analysis Process:
    1. Parse HTML using BeautifulSoup
    2. Search for PurplePatch-specific attributes (data-purplepatch-slotid)
    3. Extract positioning and sizing information
    4. Calculate viewability scores
    5. Generate optimization suggestions
    """
```

### Viewability Scoring System

The system implements a proprietary viewability scoring algorithm:

```python
def calculate_viewability_score(self, slot):
    score = 50  # Base score
    
    # Size-based scoring
    area = width * height
    if area >= 728 * 90:    score += 20  # Leaderboard
    elif area >= 300 * 250: score += 15  # Medium Rectangle
    elif area >= 320 * 100: score += 10  # Mobile Banner
    
    # Position-based scoring
    if 'home' in category:    score += 10
    if 'article' in category: score += 15
    if 'mobile' in category:  score += 5
    if position == 'static':  score += 10
    
    return min(100, max(0, score))
```

## Data Flow Architecture

### Upload Processing Flow

```
User Upload → File Validation → Content Reading → Analysis Engine → Results Generation → Display
     ↓              ↓                ↓                 ↓                  ↓              ↓
File Size Check → MIME Type → Encoding Handle → Parse & Analyze → Generate Reports → Render HTML
Security Filter    Validation    (UTF-8/ASCII)   Multiple Formats   JSON + Files     Bootstrap UI
```

### URL Analysis Flow

```
URL Input → URL Validation → ads.txt Fetch → Website Scraping → Analysis → Results
    ↓           ↓               ↓              ↓               ↓         ↓
Protocol    Domain Extract → HTTP Request → HTML Analysis → Parse Data → Generate Output
Normalize   Path Building    Timeout Handle  Slot Detection   Categorize  File Export
```

## Business Logic

### PurplePatch Detection Rules

The system identifies PurplePatch entries using multiple criteria:

1. **Domain Pattern Matching**:
   - `incrementx.com`
   - `purplepatch.online`  
   - `adserver.purplepatch.online`

2. **Keyword Detection**:
   - Case-insensitive search for "incrementx" and "purplepatch"
   - Domain substring matching

3. **Seller ID Validation**:
   - Cross-references known PurplePatch seller IDs
   - Validates relationship types (DIRECT/RESELLER)

### Competitor Analysis Logic

```python
def analyze_competitors(self):
    """
    Categorization Process:
    1. Group entries by domain
    2. Count DIRECT vs RESELLER relationships
    3. Calculate domain authority scores
    4. Identify top competitors by entry count
    5. Generate competitive intelligence reports
    """
```

## API Design

### RESTful Endpoints

| Method | Endpoint | Purpose | Response Format |
|--------|----------|---------|-----------------|
| GET | `/` | Homepage | HTML Template |
| POST | `/upload` | File Upload Analysis | HTML Results Page |
| POST | `/analyze_url` | URL-based Analysis | HTML Results Page |
| GET | `/sample_analysis` | Demo Analysis | HTML Results Page |

### Request/Response Structure

**Upload Request**:
```
Content-Type: multipart/form-data
Files: ads_txt (optional), ad_slot (optional)
Max Size: 16MB per file
```

**Analysis Response**:
```json
{
    "analysis_id": "20241002_190239",
    "ads_txt": {
        "purplepatch_found": [...],
        "competitors": {...},
        "total_entries": 150,
        "purplepatch_count": 3,
        "competitor_count": 147
    },
    "ad_slots": {
        "slots": [...],
        "total_slots": 5,
        "avg_viewability": 75.4
    }
}
```

## File Processing Pipeline

### Input Processing

1. **File Upload Handling**:
   - Secure filename generation using `werkzeug.utils.secure_filename()`
   - File size validation (16MB limit)
   - MIME type checking for security
   - Temporary file storage in `uploads/` directory

2. **Content Encoding**:
   - UTF-8 encoding with fallback to ASCII
   - BOM (Byte Order Mark) removal
   - Line ending normalization (Windows/Unix compatibility)

### Output Generation

The system generates structured output files mimicking sample data format:

```
output/
├── Ads.Txt/
│   └── {website}_{analysis_id}.txt
└── Adslot code/
    └── {website}_adslot_codes_purple_patch_{analysis_id}.txt
```

**Ads.txt Output Format**:
```
MANAGERDOMAIN = incrementx.com

IncrementX Ads.Txt Lines:

5|domain.com, seller_id, DIRECT, cert_authority
6|google.com, pub-123456, RESELLER, f08c47fec0942fa0
```

**Ad Slot Output Format**:
```html
1. 728x90 - Desktop Header Banner

<ins data-purplepatch-slotid="93"
     data-purplepatch-ct0="%%CLICK_URL_UNESC%%"
     data-purplepatch-id="53126d71827fcba70ff68055b9a73ca1pdt"
     data-publisher-name="Publisher Name"
     data-publisher-url="https://www.publisher.com/"
     data-publisher-adtype="Banner"
     data-publisher-category="Desktop Header"
     data-publisher-position="Static"
     data-publisher-width="728"
     data-publisher-height="90"
     data-publisher-timestamp="2024-10-02T19:02:39.123Z">
</ins>
<script async src="//adserver.purplepatch.online/async.js" type="text/javascript"></script>
```

## Assumptions Made

### Technical Assumptions

1. **File Format Standards**:
   - Ads.txt files follow IAB standard format: `domain, seller_id, relationship, cert_authority_id`
   - HTML content is valid and parseable by BeautifulSoup
   - Files are encoded in UTF-8 or ASCII

2. **Network Accessibility**:
   - Target websites have publicly accessible ads.txt files
   - No aggressive rate limiting on ads.txt endpoints
   - Standard HTTP/HTTPS protocols are used

3. **Browser Compatibility**:
   - Modern browsers with JavaScript enabled
   - Bootstrap 5 CSS framework support
   - HTML5 file upload API availability

### Business Assumptions

1. **PurplePatch Network Identification**:
   - PurplePatch domains remain consistent (`incrementx.com`, `purplepatch.online`)
   - Domain matching is sufficient for network identification
   - Case-insensitive matching is appropriate

2. **Viewability Scoring**:
   - Larger ad sizes generally have better viewability
   - Static positioning is preferred over dynamic positioning
   - Article pages provide better viewability than homepage

3. **Competitive Analysis**:
   - DIRECT relationships indicate primary partnerships
   - RESELLER relationships indicate secondary partnerships
   - Entry count correlates with competitive presence

### Data Assumptions

1. **Sample Data Compatibility**:
   - Existing sample files represent expected format standards
   - Line numbering format (`number|content`) is consistent
   - Output structure should match sample organization

2. **User Behavior**:
   - Users understand ads.txt format and purpose
   - File uploads are legitimate business files
   - Analysis results are used for competitive intelligence

## Security Considerations

### File Upload Security

1. **File Validation**:
   - Filename sanitization using `secure_filename()`
   - File size limits (16MB maximum)
   - Extension whitelisting for expected file types

2. **Content Security**:
   - No executable file processing
   - HTML content parsed safely using BeautifulSoup
   - No eval() or exec() of user content

3. **Network Security**:
   - Request timeouts to prevent DoS
   - User-Agent headers for legitimate scraping
   - No authentication data transmission

### Data Privacy

1. **Temporary File Management**:
   - Files stored temporarily in isolated directories
   - No persistent storage of sensitive data
   - Analysis results include timestamp-based IDs

2. **Error Handling**:
   - No sensitive information in error messages
   - Generic error responses for security issues
   - Logging excludes user data

## Performance Optimizations

### Processing Optimizations

1. **Memory Management**:
   - Streaming file processing for large ads.txt files
   - Generator functions for memory-efficient parsing
   - Limited result set sizes to prevent memory exhaustion

2. **Network Optimizations**:
   - Connection timeouts (10 seconds)
   - Efficient HTTP header usage
   - Parallel processing potential for multiple URLs

3. **Caching Strategy**:
   - Static asset caching (CSS, JS, images)
   - Template caching for frequently accessed pages
   - Potential for ads.txt result caching

### Scalability Considerations

1. **Horizontal Scaling**:
   - Stateless request processing
   - File-based session management
   - Load balancer compatibility

2. **Vertical Scaling**:
   - Efficient data structures (lists, dictionaries)
   - Minimal memory footprint per request
   - CPU-optimized parsing algorithms

## Error Handling Strategy

### Input Validation Errors

```python
# File upload errors
if 'ads_txt' not in request.files:
    flash('No files selected')
    return redirect(url_for('index'))

# File size validation
if file.size > app.config['MAX_CONTENT_LENGTH']:
    return "File too large", 413
```

### Network Error Handling

```python
# URL accessibility errors
try:
    response = requests.get(ads_txt_url, timeout=10)
    if response.status_code == 200:
        # Process content
    else:
        results['ads_txt_error'] = f'Could not fetch ads.txt (Status: {response.status_code})'
except Exception as e:
    results['ads_txt_error'] = f'Error fetching ads.txt: {str(e)}'
```

### Parsing Error Recovery

```python
# Graceful parsing with error tolerance
for line_num, line in enumerate(lines, 1):
    try:
        # Parse line
        parts = [part.strip() for part in line.split(',')]
        if len(parts) >= 3:
            # Process valid entry
    except Exception:
        # Continue processing remaining lines
        continue
```

## Future Enhancement Opportunities

### Feature Enhancements

1. **Advanced Analytics**:
   - Historical trend analysis
   - Competitive benchmarking reports
   - Revenue opportunity calculations
   - Market share analysis

2. **Integration Capabilities**:
   - Google Ad Manager API integration
   - Real-time bidding data analysis
   - Automated report generation
   - Email notification system

3. **Machine Learning**:
   - Predictive viewability modeling
   - Automated ad placement optimization
   - Anomaly detection in ads.txt files
   - Competitive intelligence automation

### Technical Improvements

1. **Database Integration**:
   - PostgreSQL or MongoDB for persistent storage
   - Historical analysis data retention
   - User account management
   - Analysis result archiving

2. **API Development**:
   - RESTful API for programmatic access
   - Webhook support for real-time updates
   - GraphQL endpoint for flexible queries
   - Rate limiting and authentication

3. **Performance Enhancements**:
   - Redis caching layer
   - Asynchronous processing with Celery
   - CDN integration for static assets
   - Database query optimization

### User Experience

1. **Dashboard Development**:
   - Interactive charts and visualizations
   - Customizable reporting templates
   - Drag-and-drop file interface
   - Real-time progress indicators

2. **Mobile Optimization**:
   - Progressive Web App (PWA) functionality
   - Mobile-responsive design improvements
   - Touch-optimized interactions
   - Offline capability support

---

## Conclusion

The PurplePatch Ads system represents a comprehensive solution for advertising network analysis and optimization. Its modular architecture, robust error handling, and flexible processing pipeline provide a solid foundation for current requirements while maintaining extensibility for future enhancements.

The system successfully balances functionality, performance, and maintainability through careful architectural decisions and implementation best practices. The documented assumptions and design rationale provide clear guidance for future development and maintenance efforts.

---

*This documentation serves as a comprehensive guide for understanding, maintaining, and extending the PurplePatch Ads analysis system.*