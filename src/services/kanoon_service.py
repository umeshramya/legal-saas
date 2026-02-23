"""
Indian Kanoon API integration service.
"""

import httpx
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import urlencode

from src.config.settings import settings

logger = logging.getLogger(__name__)


class IndianKanoonClient:
    """Client for Indian Kanoon API."""

    def __init__(self):
        self.base_url = settings.indian_kanoon_base_url
        self.api_key = settings.indian_kanoon_api_key
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Accept": "application/json",
                "Authorization": f"Token {self.api_key}" if self.api_key else ""
            }
        )
        logger.info(f"Indian Kanoon client initialized with base URL: {self.base_url}")

    async def search_documents(
        self,
        query: str,
        doctypes: Optional[List[str]] = None,
        fromdate: Optional[str] = None,
        todate: Optional[str] = None,
        title: Optional[str] = None,
        cite: Optional[str] = None,
        author: Optional[str] = None,
        bench: Optional[str] = None,
        pagenum: int = 0,
        maxpages: int = 10,
    ) -> Dict[str, Any]:
        """
        Search for legal documents.

        Args:
            query: Search query text
            doctypes: List of document types to filter
            fromdate: Start date (YYYY-MM-DD format)
            todate: End date (YYYY-MM-DD format)
            title: Title filter
            cite: Citation filter
            author: Author filter
            bench: Bench filter
            pagenum: Page number (starts at 0)
            maxpages: Maximum pages to return

        Returns:
            Dict containing search results
        """
        params = {
            "formInput": query,
            "pagenum": pagenum,
        }

        # Add optional filters
        if doctypes:
            params["doctypes"] = ",".join(doctypes)
        if fromdate:
            params["fromdate"] = fromdate
        if todate:
            params["todate"] = todate
        if title:
            params["title"] = title
        if cite:
            params["cite"] = cite
        if author:
            params["author"] = author
        if bench:
            params["bench"] = bench

        url = f"{self.base_url}/search/"
        try:
            # Indian Kanoon API requires POST for search endpoint
            response = await self.client.post(url, data=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in Kanoon search: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in Kanoon search: {e}")
            raise

    async def get_document(self, doc_id: str, maxcites: int = 10, maxcitedby: int = 10) -> Dict[str, Any]:
        """
        Get a document by ID.

        Args:
            doc_id: Document ID from Kanoon
            maxcites: Maximum citations to include
            maxcitedby: Maximum documents that cite this

        Returns:
            Dict containing document details
        """
        params = {}
        if maxcites:
            params["maxcites"] = maxcites
        if maxcitedby:
            params["maxcitedby"] = maxcitedby

        url = f"{self.base_url}/doc/{doc_id}/"
        try:
            # Indian Kanoon API requires POST for document retrieval
            response = await self.client.post(url, data=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting Kanoon document {doc_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting Kanoon document {doc_id}: {e}")
            raise

    async def get_document_metadata(self, doc_id: str) -> Dict[str, Any]:
        """
        Get document metadata.

        Args:
            doc_id: Document ID from Kanoon

        Returns:
            Dict containing document metadata
        """
        url = f"{self.base_url}/docmeta/{doc_id}/"
        try:
            # Indian Kanoon API requires POST for metadata retrieval
            response = await self.client.post(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting Kanoon metadata {doc_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting Kanoon metadata {doc_id}: {e}")
            raise

    async def get_original_document(self, doc_id: str) -> bytes:
        """
        Get original court copy (PDF).

        Args:
            doc_id: Document ID from Kanoon

        Returns:
            Bytes of the PDF document
        """
        url = f"{self.base_url}/origdoc/{doc_id}/"
        try:
            # Indian Kanoon API requires POST for original document retrieval
            response = await self.client.post(url)
            response.raise_for_status()
            return response.content
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting Kanoon original {doc_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting Kanoon original {doc_id}: {e}")
            raise

    async def search_document_fragments(self, doc_id: str, query: str) -> Dict[str, Any]:
        """
        Search within a document for fragments.

        Args:
            doc_id: Document ID from Kanoon
            query: Search query within document

        Returns:
            Dict containing document fragments
        """
        params = {"formInput": query}
        url = f"{self.base_url}/docfragment/{doc_id}/"
        try:
            # Indian Kanoon API requires POST for fragment search
            response = await self.client.post(url, data=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error searching fragments in {doc_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error searching fragments in {doc_id}: {e}")
            raise

    async def batch_search(
        self,
        queries: List[str],
        filters: Optional[Dict[str, Any]] = None,
        limit_per_query: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform batch searches.

        Args:
            queries: List of search queries
            filters: Common filters for all queries
            limit_per_query: Maximum results per query

        Returns:
            List of search results for each query
        """
        results = []
        for query in queries:
            try:
                result = await self.search_documents(query=query, maxpages=limit_per_query)
                results.append({
                    "query": query,
                    "results": result.get("results", []),
                    "total": result.get("total", 0),
                    "success": True
                })
            except Exception as e:
                results.append({
                    "query": query,
                    "error": str(e),
                    "success": False
                })
        return results

    def parse_search_result(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse search results into standardized format.

        Args:
            result: Raw search result from API

        Returns:
            List of parsed documents
        """
        parsed_docs = []
        for doc in result.get("results", []):
            parsed_doc = {
                "id": doc.get("tid"),
                "title": doc.get("title"),
                "citation": doc.get("cite"),
                "court": doc.get("court"),
                "date": doc.get("date"),
                "author": doc.get("author"),
                "bench": doc.get("bench"),
                "size": doc.get("size", 0),
                "snippet": doc.get("snippet"),
                "score": doc.get("score", 0),
                "type": doc.get("type"),
            }
            parsed_docs.append(parsed_doc)
        return parsed_docs

    def generate_citation_search_queries(self, case_number: str, parties: List[str]) -> List[str]:
        """
        Generate search queries for finding a case by citation.

        Args:
            case_number: Case number to search for
            parties: List of party names

        Returns:
            List of search queries
        """
        queries = []

        # Search by exact case number
        queries.append(f'"{case_number}"')

        # Search by parties
        for party in parties[:3]:  # Limit to first 3 parties
            if party:
                queries.append(f'"{party}" AND "{case_number[:10]}"')  # First 10 chars of case number

        # Search by citation pattern
        if "/" in case_number:
            year = case_number.split("/")[-1]
            queries.append(f'"{year}" AND "AIR"')
            queries.append(f'"{year}" AND "SCC"')
            queries.append(f'"{year}" AND "SCR"')

        return queries

    async def search_by_cnr(self, cnr_number: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Search for documents by CNR (Case Number Record) number.

        Args:
            cnr_number: CNR number to search for (e.g., "DLCT010001232023")
            max_results: Maximum number of results to return

        Returns:
            Dict containing search results with documents
        """
        # CNR numbers can appear in different formats in documents
        # Try different search patterns
        search_patterns = [
            f'"{cnr_number}"',                     # Exact CNR
            f'CNR {cnr_number}',                   # CNR with space
            f'CNR NO: {cnr_number}',              # Common format
            f'CNR NO.{cnr_number}',               # Alternative format
            f'CNR NO {cnr_number}',               # Without punctuation
            f'Case Number Record: {cnr_number}',  # Full phrase
        ]

        all_results = []
        total_found = 0

        for pattern in search_patterns:
            try:
                result = await self.search_documents(
                    query=pattern,
                    maxpages=min(max_results, 5)  # Limit pages per pattern
                )

                if result.get('results'):
                    all_results.extend(result['results'])
                    total_found = result.get('total', 0)
                    logger.info(f"Found {len(result['results'])} documents with pattern: {pattern}")

                    # If we found results, we can stop searching further patterns
                    # or continue to collect more
                    if len(all_results) >= max_results:
                        break

            except Exception as e:
                logger.warning(f"Search with pattern '{pattern}' failed: {e}")
                continue

        # Remove duplicates by document ID
        unique_docs = {}
        for doc in all_results:
            doc_id = doc.get('tid')
            if doc_id and doc_id not in unique_docs:
                unique_docs[doc_id] = doc

        # Limit to max_results
        final_results = list(unique_docs.values())[:max_results]

        return {
            'cnr_number': cnr_number,
            'total_found': total_found,
            'unique_results': len(final_results),
            'results': final_results,
            'search_patterns_used': search_patterns[:len(all_results)] if all_results else []
        }

    async def analyze_case_by_cnr(self, cnr_number: str) -> Dict[str, Any]:
        """
        Find and analyze a case by CNR number.

        Args:
            cnr_number: CNR number to search for

        Returns:
            Dict containing case analysis
        """
        # Step 1: Search for documents by CNR
        search_result = await self.search_by_cnr(cnr_number, max_results=5)

        if not search_result['results']:
            return {
                'cnr_number': cnr_number,
                'found': False,
                'message': f'No documents found for CNR: {cnr_number}',
                'analysis': None
            }

        # Step 2: Get the most relevant document
        primary_doc = search_result['results'][0]
        doc_id = primary_doc.get('tid')

        if not doc_id:
            return {
                'cnr_number': cnr_number,
                'found': True,
                'message': 'Document found but no ID available',
                'documents': search_result['results'],
                'analysis': None
            }

        # Step 3: Get full document details
        try:
            document = await self.get_document(doc_id)

            # Step 4: Extract text for analysis
            # The document response structure depends on Kanoon API
            # This is a placeholder - actual text extraction may need adjustment
            document_text = ""

            # Try to extract text from different possible fields
            if isinstance(document, dict):
                # Check for text fields
                if 'text' in document:
                    document_text = document['text']
                elif 'content' in document:
                    document_text = document['content']
                elif 'judgment' in document:
                    document_text = document['judgment']
                elif 'description' in document:
                    document_text = document['description']

            # If no text found, use snippet from search result
            if not document_text and 'snippet' in primary_doc:
                document_text = primary_doc['snippet']

            return {
                'cnr_number': cnr_number,
                'found': True,
                'document_id': doc_id,
                'document_title': primary_doc.get('title', 'Unknown'),
                'court': primary_doc.get('court', 'Unknown'),
                'date': primary_doc.get('date', 'Unknown'),
                'citation': primary_doc.get('cite', 'Unknown'),
                'document_text': document_text[:5000],  # Limit text length
                'metadata': {
                    'search_results': len(search_result['results']),
                    'total_found': search_result['total_found']
                },
                'analysis_ready': bool(document_text)
            }

        except Exception as e:
            logger.error(f"Error analyzing case by CNR {cnr_number}: {e}")
            return {
                'cnr_number': cnr_number,
                'found': True,
                'error': str(e),
                'document_id': doc_id,
                'document_title': primary_doc.get('title', 'Unknown'),
                'analysis_ready': False
            }

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Global client instance
_kanoon_client = None


async def get_kanoon_client() -> IndianKanoonClient:
    """
    Get or create Indian Kanoon client.

    Returns:
        IndianKanoonClient instance
    """
    global _kanoon_client
    if _kanoon_client is None:
        _kanoon_client = IndianKanoonClient()
    return _kanoon_client


async def close_kanoon_client():
    """Close Kanoon client."""
    global _kanoon_client
    if _kanoon_client:
        await _kanoon_client.close()
        _kanoon_client = None