#!/usr/bin/env python3
"""Test Supabase configuration validation.

This script tests that the system properly validates Supabase configuration
when FILE_STORAGE_PROVIDER=supabase.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_supabase_validation():
    """Test Supabase configuration validation."""
    print("🔧 Testing Supabase Configuration Validation")
    print("=" * 60)
    
    # Save original environment
    original_env = {}
    env_vars = [
        'FILE_STORAGE_PROVIDER',
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY',
        'FILE_STORAGE_SUPABASE_BUCKET'
    ]
    
    for var in env_vars:
        original_env[var] = os.environ.get(var)
    
    try:
        # Test 1: Missing SUPABASE_URL
        print("\n📋 Test 1: Missing SUPABASE_URL")
        os.environ['FILE_STORAGE_PROVIDER'] = 'supabase'
        os.environ.pop('SUPABASE_URL', None)
        os.environ.pop('SUPABASE_SERVICE_ROLE_KEY', None)
        os.environ['FILE_STORAGE_SUPABASE_BUCKET'] = 'test-bucket'
        
        try:
            # Clear settings cache
            from app.core.config import get_settings
            get_settings.cache_clear()
            
            settings = get_settings()
            print("❌ Should have failed but didn't")
        except ValueError as e:
            if "SUPABASE_URL is required" in str(e):
                print("✅ Correctly caught missing SUPABASE_URL")
            else:
                print(f"❌ Wrong error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        # Test 2: Missing SUPABASE_SERVICE_ROLE_KEY
        print("\n📋 Test 2: Missing SUPABASE_SERVICE_ROLE_KEY")
        os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
        os.environ.pop('SUPABASE_SERVICE_ROLE_KEY', None)
        
        try:
            get_settings.cache_clear()
            settings = get_settings()
            print("❌ Should have failed but didn't")
        except ValueError as e:
            if "SUPABASE_SERVICE_ROLE_KEY is required" in str(e):
                print("✅ Correctly caught missing SUPABASE_SERVICE_ROLE_KEY")
            else:
                print(f"❌ Wrong error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        # Test 3: Missing bucket name (should warn but not fail)
        print("\n📋 Test 3: Missing bucket name (should warn but not fail)")
        os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test-key'
        os.environ.pop('FILE_STORAGE_SUPABASE_BUCKET', None)
        
        try:
            get_settings.cache_clear()
            settings = get_settings()
            print("✅ Uses default bucket with warning (expected behavior)")
            print(f"  Default bucket: {settings.file_storage.supabase_bucket}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        # Test 4: Valid configuration
        print("\n📋 Test 4: Valid Supabase configuration")
        os.environ['FILE_STORAGE_SUPABASE_BUCKET'] = 'windx-uploads'
        
        try:
            get_settings.cache_clear()
            settings = get_settings()
            print("✅ Valid configuration accepted")
            print(f"  Provider: {settings.file_storage.provider}")
            print(f"  Supabase URL: {settings.supabase_url}")
            print(f"  Bucket: {settings.file_storage.supabase_bucket}")
        except Exception as e:
            print(f"❌ Unexpected error with valid config: {e}")
        
        # Test 5: Local provider (should not validate Supabase)
        print("\n📋 Test 5: Local provider (no Supabase validation)")
        os.environ['FILE_STORAGE_PROVIDER'] = 'local'
        os.environ.pop('SUPABASE_URL', None)
        os.environ.pop('SUPABASE_SERVICE_ROLE_KEY', None)
        
        try:
            get_settings.cache_clear()
            settings = get_settings()
            print("✅ Local provider works without Supabase config")
            print(f"  Provider: {settings.file_storage.provider}")
        except Exception as e:
            print(f"❌ Unexpected error with local provider: {e}")
        
    finally:
        # Restore original environment
        for var, value in original_env.items():
            if value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = value
        
        # Clear cache one more time
        try:
            get_settings.cache_clear()
        except:
            pass
    
    print("\n🎉 Supabase Validation Tests Complete!")


if __name__ == "__main__":
    test_supabase_validation()