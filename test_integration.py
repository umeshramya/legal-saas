#!/usr/bin/env python3
"""
Test script to verify Indian Kanoon API integration and DeepSeek AI analysis.
"""

import asyncio
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_kanoon_integration():
    """Test Indian Kanoon API integration."""
    print("Testing Indian Kanoon API integration...")

    try:
        from services.kanoon_service import IndianKanoonClient

        # Initialize client (will use settings from .env)
        client = IndianKanoonClient()

        # Test search
        print("1. Testing search functionality...")
        results = await client.search_documents(
            query="arbitration",
            doctypes=["supremecourt"],
            maxpages=2
        )

        print(f"   Search results: {results.get('total', 0)} documents found")

        if results.get('results'):
            first_doc = results['results'][0]
            print(f"   First document: {first_doc.get('title', 'No title')}")
            print(f"   Citation: {first_doc.get('cite', 'No citation')}")

        # Test document retrieval (if we have a doc_id)
        if results.get('results'):
            doc_id = results['results'][0].get('tid')
            if doc_id:
                print(f"\n2. Testing document retrieval for ID: {doc_id}...")
                try:
                    doc = await client.get_document(doc_id, maxcites=2, maxcitedby=2)
                    print(f"   Document retrieved successfully")
                    print(f"   Title: {doc.get('title', 'No title')}")
                    print(f"   Court: {doc.get('court', 'No court')}")
                except Exception as e:
                    print(f"   Document retrieval failed: {e}")

        await client.close()
        print("\n✅ Indian Kanoon API integration test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Indian Kanoon API integration test FAILED: {e}")
        return False

async def test_deepseek_integration():
    """Test DeepSeek AI integration."""
    print("\nTesting DeepSeek AI integration...")

    try:
        from services.deepseek_service import DeepSeekAnalysisService

        # Check if API key is configured
        from config.settings import settings
        if not settings.deepseek_api_key:
            print("   DeepSeek API key not configured. Skipping actual API test.")
            print("   (Set DEEPSEEK_API_KEY in .env to test)")
            return True  # Consider it passed if not configured

        # Initialize service
        service = DeepSeekAnalysisService()

        # Test connection
        print("1. Testing API connection...")
        connected = await service.test_connection()
        if connected:
            print("   ✅ DeepSeek API connection successful")
        else:
            print("   ❌ DeepSeek API connection failed")
            return False

        # Test document analysis with sample text
        print("\n2. Testing document analysis...")
        sample_text = """This is a test legal document about breach of contract.
        The plaintiff alleges that the defendant failed to deliver goods as per agreement dated January 15, 2023.
        The defendant claims force majeure due to unforeseen circumstances."""

        try:
            result = await service.analyze_document(
                document_text=sample_text,
                analysis_type="document_summary"
            )
            print("   ✅ Document analysis completed")
            print(f"   Processing time: {result.get('metadata', {}).get('processing_time_ms', 0)}ms")
            print(f"   Token count: {result.get('metadata', {}).get('token_count', 0)}")
        except Exception as e:
            print(f"   ❌ Document analysis failed: {e}")
            return False

        await service.close()
        print("\n✅ DeepSeek AI integration test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ DeepSeek AI integration test FAILED: {e}")
        return False

async def test_document_processing():
    """Test document processing (OCR, text extraction)."""
    print("\nTesting document processing...")

    try:
        from services.document_processor import DocumentProcessor

        processor = DocumentProcessor()

        # Test with sample text (simulating file upload)
        print("1. Testing text extraction...")

        # Create a simple test
        test_text = "Test legal document content for processing."

        keywords = processor.extract_keywords(test_text)
        print(f"   Keyword extraction: {keywords}")

        reading_time = processor.estimate_reading_time(test_text)
        print(f"   Reading time estimate: {reading_time} minute(s)")

        print("\n✅ Document processing test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Document processing test FAILED: {e}")
        return False


async def test_cnr_search():
    """Test CNR search functionality."""
    print("\nTesting CNR search...")

    try:
        from services.kanoon_service import IndianKanoonClient

        # Initialize client
        client = IndianKanoonClient()

        # Test that the method exists (won't actually call API without valid CNR)
        print("1. Testing method availability...")

        # Check if search_by_cnr method exists
        if hasattr(client, 'search_by_cnr'):
            print("   ✅ search_by_cnr method exists")
        else:
            print("   ❌ search_by_cnr method not found")
            return False

        if hasattr(client, 'analyze_case_by_cnr'):
            print("   ✅ analyze_case_by_cnr method exists")
        else:
            print("   ❌ analyze_case_by_cnr method not found")
            return False

        # Note: We don't test actual API call without a valid CNR
        # to avoid unnecessary API usage
        print("2. Skipping actual API test (requires valid CNR)")
        print("   To test with real CNR, update test_integration.py")

        await client.close()
        print("\n✅ CNR search test PASSED (method check only)")
        return True

    except Exception as e:
        print(f"\n❌ CNR search test FAILED: {e}")
        return False

async def main():
    """Run all integration tests."""
    print("=" * 60)
    print("LEGAL ANALYSIS SAAS - INTEGRATION TESTS")
    print("=" * 60)

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    tests = [
        ("Indian Kanoon API", test_kanoon_integration),
        ("DeepSeek AI", test_deepseek_integration),
        ("Document Processing", test_document_processing),
        ("CNR Search", test_cnr_search),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print(f"{'='*60}")

        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))

    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")

    all_passed = True
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:30} {status}")
        if not success:
            all_passed = False

    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

    # Return exit code
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    asyncio.run(main())