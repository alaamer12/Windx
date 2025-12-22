#!/usr/bin/env python3
"""Test script for the enhanced file storage system.

This script tests the file storage system with various scenarios including:
- Supabase configuration validation
- Image processing capabilities
- File size and dimension validation
- Provider switching
"""

import asyncio
import io
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import get_settings
from app.services.storage import get_storage_service


def create_test_image(width: int, height: int, format: str = "JPEG") -> bytes:
    """Create a test image with specified dimensions.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        format: Image format (JPEG, PNG, etc.)
        
    Returns:
        bytes: Image data
    """
    try:
        from PIL import Image
        
        # Create a simple test image
        img = Image.new('RGB', (width, height), color='red')
        
        # Add some content to make it more realistic (only if image is large enough)
        if width > 20 and height > 20:
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.rectangle([2, 2, width-2, height-2], outline='blue', width=1)
            
            # Only add text if image is large enough
            if width > 50 and height > 30:
                draw.text((5, 5), f"{width}x{height}", fill='white')
        
        # Save to bytes
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        return buffer.getvalue()
        
    except ImportError:
        print("PIL/Pillow not available - creating dummy image data")
        # Create dummy image data (not a real image)
        return b"dummy_image_data_" + f"{width}x{height}_{format}".encode()


async def test_configuration_validation():
    """Test configuration validation."""
    print("🔧 Testing Configuration Validation")
    print("=" * 50)
    
    settings = get_settings()
    
    print(f"File Storage Provider: {settings.file_storage.provider}")
    print(f"Max File Size: {settings.file_storage.max_size_mb:.1f}MB")
    print(f"Min File Size: {settings.file_storage.min_size_kb:.1f}KB")
    print(f"Max Dimensions: {settings.file_storage.max_width}x{settings.file_storage.max_height}")
    print(f"Min Dimensions: {settings.file_storage.min_width}x{settings.file_storage.min_height}")
    print(f"Compression Enabled: {settings.file_storage.enable_compression}")
    print(f"Auto Resize: {settings.file_storage.auto_resize}")
    print(f"Compression Quality: {settings.file_storage.compression_quality}")
    
    # Test Supabase validation
    if settings.file_storage.provider == "supabase":
        print(f"\nSupabase Configuration:")
        print(f"  URL: {settings.supabase_url or 'NOT SET'}")
        print(f"  Service Key: {'SET' if settings.supabase_service_role_key else 'NOT SET'}")
        print(f"  Bucket: {settings.file_storage.supabase_bucket}")
        
        if not settings.supabase_url or not settings.supabase_service_role_key:
            print("⚠️  WARNING: Supabase configuration incomplete!")
            return False
    
    print("✅ Configuration validation passed")
    return True


async def test_storage_service():
    """Test storage service initialization."""
    print("\n🚀 Testing Storage Service")
    print("=" * 50)
    
    try:
        storage_service = get_storage_service()
        provider_info = storage_service.get_provider_info()
        
        print("Provider Information:")
        for key, value in provider_info.items():
            print(f"  {key}: {value}")
        
        print("✅ Storage service initialized successfully")
        return storage_service
        
    except Exception as e:
        print(f"❌ Storage service initialization failed: {e}")
        return None


async def test_file_validation():
    """Test file validation."""
    print("\n📋 Testing File Validation")
    print("=" * 50)
    
    storage_service = get_storage_service()
    
    # Test cases
    test_cases = [
        {
            "name": "Valid small image",
            "data": create_test_image(100, 100),
            "filename": "test_small.jpg",
            "should_pass": True,
        },
        {
            "name": "Valid large image",
            "data": create_test_image(2000, 2000),
            "filename": "test_large.jpg",
            "should_pass": True,
        },
        {
            "name": "Too small image",
            "data": create_test_image(10, 10),
            "filename": "test_tiny.jpg",
            "should_pass": False,
        },
        {
            "name": "Empty file",
            "data": b"",
            "filename": "empty.jpg",
            "should_pass": False,
        },
        {
            "name": "Invalid extension",
            "data": b"some data",
            "filename": "test.txt",
            "should_pass": False,
        },
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        
        # Test validation through upload (without actually uploading)
        result = storage_service._validate_file(test_case['data'], test_case['filename'])
        
        if test_case['should_pass']:
            if result.success:
                print(f"  ✅ Passed as expected")
            else:
                print(f"  ❌ Failed unexpectedly: {result.error}")
        else:
            if not result.success:
                print(f"  ✅ Failed as expected: {result.error}")
            else:
                print(f"  ❌ Passed unexpectedly")


async def test_image_processing():
    """Test image processing capabilities."""
    print("\n🖼️  Testing Image Processing")
    print("=" * 50)
    
    storage_service = get_storage_service()
    
    if not storage_service.image_processor:
        print("⚠️  Image processing not available (PIL/Pillow not installed)")
        return
    
    # Test image validation
    test_image = create_test_image(1000, 800)
    validation_result = storage_service.image_processor.validate_image(test_image)
    
    if validation_result.success:
        print("✅ Image validation passed")
        if validation_result.original_info:
            info = validation_result.original_info
            print(f"  Original: {info.width}x{info.height}, {info.format}, {info.size_bytes} bytes")
    else:
        print(f"❌ Image validation failed: {validation_result.error}")
        return
    
    # Test image processing
    processing_result = storage_service.image_processor.process_image(test_image, "test.jpg")
    
    if processing_result.success:
        print("✅ Image processing passed")
        if processing_result.original_info and processing_result.processed_info:
            orig = processing_result.original_info
            proc = processing_result.processed_info
            print(f"  Original: {orig.width}x{orig.height}, {orig.size_bytes} bytes")
            print(f"  Processed: {proc.width}x{proc.height}, {proc.size_bytes} bytes")
            
            size_reduction = ((orig.size_bytes - proc.size_bytes) / orig.size_bytes) * 100
            print(f"  Size reduction: {size_reduction:.1f}%")
    else:
        print(f"❌ Image processing failed: {processing_result.error}")


async def test_upload_simulation():
    """Test upload simulation (without actually uploading)."""
    print("\n📤 Testing Upload Simulation")
    print("=" * 50)
    
    storage_service = get_storage_service()
    
    # Create test image
    test_image = create_test_image(500, 400)
    
    print(f"Test image size: {len(test_image)} bytes")
    print("Simulating upload process...")
    
    # This would normally upload, but we'll just test the validation and processing
    validation_result = storage_service._validate_file(test_image, "test_upload.jpg")
    
    if validation_result.success:
        print("✅ File validation passed")
        
        if storage_service.image_processor:
            processing_result = storage_service.image_processor.process_image(test_image, "test_upload.jpg")
            if processing_result.success:
                print("✅ Image processing passed")
                print("📋 Upload would proceed with processed image")
            else:
                print(f"❌ Image processing failed: {processing_result.error}")
        else:
            print("📋 Upload would proceed with original file (no image processing)")
    else:
        print(f"❌ File validation failed: {validation_result.error}")


async def main():
    """Main test function."""
    print("🧪 File Storage System Test Suite")
    print("=" * 60)
    
    # Test configuration
    config_ok = await test_configuration_validation()
    if not config_ok:
        print("\n❌ Configuration validation failed - stopping tests")
        return
    
    # Test service initialization
    storage_service = await test_storage_service()
    if not storage_service:
        print("\n❌ Storage service initialization failed - stopping tests")
        return
    
    # Run tests
    await test_file_validation()
    await test_image_processing()
    await test_upload_simulation()
    
    print("\n🎉 Test Suite Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())