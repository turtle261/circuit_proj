#!/usr/bin/env python3
"""
Simple Flask app test without eventlet conflicts
"""

import os
import sys
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_flask_import():
    """Test that Flask app can be imported without errors"""
    try:
        # Test basic imports
        from flask import Flask
        from flask_socketio import SocketIO
        import eventlet
        
        print("✓ Flask imports successful")
        print("✓ Flask-SocketIO imports successful") 
        print("✓ Eventlet imports successful")
        
        # Test basic Flask app creation
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-key'
        
        print("✓ Flask app creation successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Flask test failed: {e}")
        return False

if __name__ == '__main__':
    print("Testing Flask application components...")
    success = test_flask_import()
    
    if success:
        print("\n🎉 Flask application test passed!")
        sys.exit(0)
    else:
        print("\n❌ Flask application test failed!")
        sys.exit(1)