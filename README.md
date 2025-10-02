# PurplePatch Ads

## How to Run the Project

Follow these simple steps to get the project up and running:

### Prerequisites
- Git installed on your system
- Python 3.7+ installed

## Running on Windows

### Step-by-Step Instructions (Windows)

#### Step 1: Clone the Project
```bash
git clone [repository-url]
cd PurplePatchAds
```

#### Step 2: Run the Launcher
Double-click on `purplepatch_launcher.bat` or run it from the command line:
```cmd
purplepatch_launcher.bat
```

#### Step 3: Follow the Launcher Prompts
The launcher will guide you through the remaining setup process. Simply follow the on-screen instructions.

## Running on Linux/macOS

### Step-by-Step Instructions (Linux/macOS)

#### Step 1: Clone the Project
```bash
git clone [repository-url]
cd PurplePatchAds
```

#### Step 2: Set Up Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install required packages
pip install flask pandas matplotlib seaborn beautifulsoup4 requests werkzeug
```

#### Step 4: Create Required Directories
```bash
mkdir -p uploads output static templates
```

#### Step 5: Run the Application
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Start the Flask application
python app.py
```

#### Step 6: Access the Application
Open your web browser and navigate to:
- Local: `http://127.0.0.1:5000`
- Network: `http://[your-ip]:5000` (if network accessible)

### Quick Start Script for Linux/macOS
For convenience, you can create a bash script equivalent to the Windows launcher:

```bash
#!/bin/bash
echo "Starting PurplePatch Ads Analyzer..."
echo "Activating virtual environment..."
source venv/bin/activate
echo "Starting application..."
python app.py
```

Save this as `purplepatch_launcher.sh`, make it executable with `chmod +x purplepatch_launcher.sh`, and run with `./purplepatch_launcher.sh`

---

**Note**: Make sure you have all necessary dependencies installed before running the launcher. The launcher script will handle the project initialization and startup process automatically.
