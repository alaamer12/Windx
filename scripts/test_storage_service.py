#!/usr/bin/env python3
"""Test script for the file storage service.

This script tests the file storage service configuration and basic operations
to ensure the strategy pattern is working correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import get_settings
from app.services.storage import get_storage_service


async def test_storage_service():
    """Test the file storage service configuration."""
    print("🧪 Testing File Storage Service")
    print("=" * 50)
    
    try:
        # Get settings and storage service
        settings = get_settings()
        storage_service = get_storage_service()
        
        print(f"📊 Configuration:")
        print(f"   Provider: {settings.file_storage.provider}")
        print(f"   Max Size: {settings.file_storage.max_size_mb:.1f}MB")
        print(f"   Allowed Extensions: {', '.join(settings.file_storage.allowed_extensions)}")
        
        if settings.file_storage.provider == "supabase":
            print(f"   Supabase Bucket: {settings.file_storage.supabase_bucket}")
            print(f"   Supabase URL: {settings.supabase_url or 'Not configured'}")
            print(f"   Service Role Key: {'✅ Configured' if settings.supabase_service_role_key else '❌ Missing'}")
        elif settings.file_storage.provider == "local":
            print(f"   Local Directory: {settings.file_storage.local_dir}")
            print(f"   Base URL: {settings.file_storage.base_url}")
        
        print(f"\n🔧 Storage Service Info:")
        provider_info = storage_service.get_provider_info()
        for key, value in provider_info.items():
            print(f"   {key.title()}: {value}")
        
        # Test with a small dummy file
        print(f"\n🧪 Testing file operations...")
        
        # Create a small test image (1x1 pixel PNG)
        test_image_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,  # bit depth, color type, etc.
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0x00, 0x00, 0x00,  # image data
            0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00,  # 
            0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42,  # IEND chunk
            0x60, 0x82
        ])
        
        # Test upload
        print("   📤 Testing upload...")
        upload_result = await storage_service.upload_file(
            file=test_image_data,
            filename="test_image.png"
        )
        
        if upload_result.success:
            print(f"   ✅ Upload successful!")
            print(f"      Filename: {upload_result.filename}")
            print(f"      URL: {upload_result.url}")
            print(f"      Size: {upload_result.size} bytes")
            
            # Test file exists
            print("   🔍 Testing file exists...")
            exists = await storage_service.file_exists(upload_result.filename)
            print(f"   {'✅' if exists else '❌'} File exists: {exists}")
            
            # Test get URL
            print("   🔗 Testing get URL...")
            url = await storage_service.get_file_url(upload_result.filename)
            print(f"   {'✅' if url else '❌'} Get URL: {url}")
            
            # Test delete
            print("   🗑️ Testing delete...")
            deleted = await storage_service.delete_file(upload_result.filename)
            print(f"   {'✅' if deleted else '❌'} Delete successful: {deleted}")
            
        else:
            print(f"   ❌ Upload failed: {upload_result.error}")
        
        print(f"\n🎉 Storage service test completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    print("🚀 File Storage Service Test")
    print("=" * 50)
    
    try:
        success = asyncio.run(test_storage_service())
        if success:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        sys.exit(1)