#!/usr/bin/env python3
"""
SnapCal+ Gemini Setup Script
Helps configure Gemini 2.0 Flash integration for food recognition
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file with Gemini configuration"""
    
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    if env_example.exists():
        # Copy from example
        with open(env_example, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ Created .env file from .env.example")
    else:
        # Create basic .env file
        env_content = """# SnapCal+ Backend Environment Variables

# Database
DATABASE_URL=sqlite:///./snapcal.db

# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
USE_GEMINI_AI=true

# Application Settings
DEBUG=true
DEFAULT_LANGUAGE=en
DEFAULT_CURRENCY=RM

# File Upload Settings
MAX_FILE_SIZE=10485760
UPLOAD_DIR=uploads
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("✅ Created basic .env file")

def check_dependencies():
    """Check if required dependencies are installed"""
    
    try:
        import google.generativeai as genai
        print("✅ google-generativeai is installed")
        return True
    except ImportError:
        print("❌ google-generativeai is not installed")
        print("   Run: pip install google-generativeai==0.8.0")
        return False

def test_gemini_connection():
    """Test Gemini API connection if API key is provided"""
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key or api_key == "your_gemini_api_key_here":
        print("⚠️  GEMINI_API_KEY not set in .env file")
        print("   Get your API key from: https://ai.google.dev/")
        print("   Then update GEMINI_API_KEY in .env file")
        return False
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Test with a simple text generation
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content("Hello, just testing the connection.")
        
        print("✅ Gemini API connection successful!")
        print(f"   Model: gemini-2.0-flash")
        print(f"   Response preview: {response.text[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Gemini API connection failed: {e}")
        print("   Check your API key and try again")
        return False

def main():
    """Main setup function"""
    
    print("🚀 SnapCal+ Gemini Setup")
    print("=" * 40)
    
    # Check if we're in the backend directory
    if not Path("app").exists() or not Path("requirements.txt").exists():
        print("❌ Please run this script from the backend directory")
        sys.exit(1)
    
    print("📂 Current directory: backend/")
    
    # Step 1: Check dependencies
    print("\n1️⃣ Checking dependencies...")
    deps_ok = check_dependencies()
    
    # Step 2: Create .env file
    print("\n2️⃣ Setting up environment file...")
    create_env_file()
    
    # Step 3: Test Gemini connection (if possible)
    print("\n3️⃣ Testing Gemini API connection...")
    if deps_ok:
        test_gemini_connection()
    else:
        print("⏭️  Skipping connection test (install dependencies first)")
    
    print("\n" + "=" * 40)
    print("🎉 Setup Complete!")
    print("\n📋 Next Steps:")
    print("1. Get your Gemini API key from: https://ai.google.dev/")
    print("2. Update GEMINI_API_KEY in .env file")
    print("3. Install dependencies: pip install -r requirements.txt")
    print("4. Run the server: uvicorn app.main:app --reload")
    print("5. Test with image upload at: http://localhost:8000/docs")
    
    print("\n🔧 Configuration:")
    print("- Gemini model: gemini-2.0-flash")
    print("- Fallback: Mock AI (when Gemini fails)")
    print("- Supported formats: JPEG, PNG, WebP")
    print("- Max file size: 10MB")

if __name__ == "__main__":
    main() 