#!/usr/bin/env python3
"""
Example script for CNR-based legal case analysis.

This demonstrates how to use the Legal Analysis SAAS API
to search and analyze legal cases by CNR (Case Number Record) number.

Prerequisites:
1. Install dependencies: pip install -r requirements.txt
2. Set up environment variables in .env file
3. Start the FastAPI server: uvicorn src.api.main:app --reload
"""

import asyncio
import httpx
import json
import sys
from typing import Dict, Any


async def analyze_case_by_cnr(cnr_number: str, base_url: str = "http://localhost:8000"):
    """
    Analyze a legal case by CNR number using the SAAS API.

    Args:
        cnr_number: CNR number to analyze (e.g., "DLCT010001232023")
        base_url: Base URL of the running FastAPI server
    """
    print(f"\n{'='*60}")
    print(f"Analyzing case by CNR: {cnr_number}")
    print(f"{'='*60}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Option 1: Full analysis with AI
            print("\n1. Performing full analysis with AI...")
            analysis_request = {
                "cnr_number": cnr_number,
                "include_analysis": True,
                "analysis_type": "case_analysis"
            }

            response = await client.post(
                f"{base_url}/analyze/cnr",
                json=analysis_request
            )

            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Analysis completed")
                print(f"   Found: {result.get('found')}")

                if result.get('found'):
                    print(f"   Document Title: {result.get('document_title')}")
                    print(f"   Court: {result.get('court')}")
                    print(f"   Date: {result.get('date')}")
                    print(f"   Citation: {result.get('citation')}")
                    print(f"   Search Results: {result.get('search_results_count')}")

                    if result.get('analysis_result'):
                        print(f"\n   AI Analysis Summary:")
                        analysis = result['analysis_result']

                        # Print key analysis sections
                        if 'case_overview' in analysis:
                            print(f"   • Case Overview: {analysis['case_overview'][:200]}...")
                        elif 'summary' in analysis:
                            print(f"   • Summary: {analysis['summary'][:200]}...")

                        if 'risk_assessment' in analysis:
                            print(f"   • Risk Assessment: Available")

                        if 'strategic_recommendations' in analysis:
                            print(f"   • Strategic Recommendations: Available")

                        print(f"\n   Full analysis saved to: cnr_analysis_{cnr_number}.json")

                        # Save full analysis to file
                        with open(f"cnr_analysis_{cnr_number}.json", "w") as f:
                            json.dump(result, f, indent=2, default=str)
                else:
                    print(f"   ❌ No documents found for CNR: {cnr_number}")
                    print(f"   Error: {result.get('error')}")
            else:
                print(f"   ❌ API Error: {response.status_code}")
                print(f"   Response: {response.text}")

            # Option 2: Search only (without AI analysis)
            print("\n2. Performing search-only (without AI analysis)...")
            search_request = {
                "cnr_number": cnr_number,
                "include_analysis": False
            }

            response = await client.post(
                f"{base_url}/search/cnr",
                json=search_request
            )

            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Search completed")
                print(f"   Found: {result.get('found')}")
                print(f"   Results: {result.get('search_results_count')} documents")

                if result.get('document_text_preview'):
                    print(f"\n   Document Preview:")
                    print(f"   {result.get('document_text_preview')}")
            else:
                print(f"   ❌ Search Error: {response.status_code}")
                print(f"   Response: {response.text}")

        except httpx.RequestError as e:
            print(f"   ❌ Request failed: {e}")
            print(f"   Make sure the FastAPI server is running at {base_url}")
            print(f"   Start server with: uvicorn src.api.main:app --reload")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")


async def test_with_sample_cnr():
    """Test with a sample CNR number."""
    # Note: Replace with actual CNR number for real testing
    sample_cnr = "DLCT010001232023"  # Example format

    print("\n" + "="*60)
    print("TEST: CNR-Based Legal Analysis")
    print("="*60)
    print("\nThis is a demonstration of CNR analysis functionality.")
    print("To test with a real CNR number:")
    print("1. Replace the sample_cnr variable with an actual CNR")
    print("2. Ensure Indian Kanoon API key is configured in .env")
    print("3. Ensure DeepSeek API key is configured for AI analysis")
    print("4. Start the FastAPI server")
    print("\n" + "-"*60)

    await analyze_case_by_cnr(sample_cnr)


async def main():
    """Main function."""
    print("CNR-Based Legal Analysis Example")
    print("================================\n")

    # Check if a CNR number was provided as command line argument
    if len(sys.argv) > 1:
        cnr_number = sys.argv[1]
        await analyze_case_by_cnr(cnr_number)
    else:
        # Use sample CNR for demonstration
        await test_with_sample_cnr()

    print("\n" + "="*60)
    print("Analysis Complete")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())