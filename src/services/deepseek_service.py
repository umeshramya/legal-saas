"""
DeepSeek AI integration for legal document analysis.
Uses OpenAI-compatible API interface.
"""

import openai
import json
import logging
import time
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime
import asyncio

from src.config.settings import settings

logger = logging.getLogger(__name__)


class DeepSeekAnalysisService:
    """Service for DeepSeek AI analysis of legal documents."""

    def __init__(self):
        self.client = openai.AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url
        )
        self.model = "deepseek-chat"  # DeepSeek chat model
        self.max_tokens = 4000
        self.temperature = 0.1  # Low temperature for consistent legal analysis

        # Analysis templates
        self.templates = {
            "document_summary": """You are a legal expert analyzing a court document.

Document: {document_text}

Provide a comprehensive analysis including:
1. **Document Type**: What type of legal document is this?
2. **Key Parties**: Who are the parties involved?
3. **Core Issues**: What are the main legal issues?
4. **Arguments**: What arguments are presented by each party?
5. **Legal Provisions**: What laws, statutes, or precedents are cited?
6. **Outcome/Relief**: What relief is being sought or what was decided?
7. **Key Dates**: Important dates mentioned.
8. **Risk Assessment**: Potential risks for each party.
9. **Strategic Recommendations**: Legal strategies to consider.

Format the response as structured JSON with these sections.""",

            "case_analysis": """You are a senior legal advisor analyzing a complete case.

Case Context: {case_context}
Documents Summary: {documents_summary}

Provide a comprehensive case analysis including:
1. **Case Overview**: Brief summary of the case.
2. **Strengths/Weaknesses**: Analysis of each party's position.
3. **Legal Issues**: Key legal questions to be decided.
4. **Precedent Analysis**: Relevant case law and how it applies.
5. **Risk Assessment**: Probability of success for each party.
6. **Strategic Recommendations**: Recommended legal strategies.
7. **Timeline Analysis**: Critical dates and deadlines.
8. **Evidence Gaps**: Missing evidence or documentation.
9. **Settlement Potential**: Likelihood and terms of settlement.

Format the response as structured JSON.""",

            "risk_assessment": """You are a legal risk analyst.

Document/Context: {context}

Analyze the legal risks including:
1. **High Risk Factors**: Factors with significant potential negative impact.
2. **Medium Risk Factors**: Moderate risks that need monitoring.
3. **Low Risk Factors**: Minor risks with limited impact.
4. **Procedural Risks**: Risks related to court procedures and timelines.
5. **Evidence Risks**: Risks related to evidence quality and admissibility.
6. **Financial Risks**: Potential financial exposure.
7. **Reputational Risks**: Impact on reputation and public perception.
8. **Mitigation Strategies**: Recommended actions to mitigate each risk.

Format as structured JSON with risk scores (1-10) for each factor.""",

            "document_review": """You are a legal document reviewer.

Document Text: {document_text}

Review this legal document for:
1. **Clarity and Ambiguity**: Identify unclear or ambiguous language.
2. **Completeness**: Missing sections or information.
3. **Legal Compliance**: Compliance with relevant laws and regulations.
4. **Formatting Issues**: Formatting or structural problems.
5. **Citation Accuracy**: Verify citations and legal references.
6. **Consistency**: Internal consistency of terms and definitions.
7. **Recommendations**: Specific suggestions for improvement.

Format as structured JSON with detailed comments.""",
        }

        logger.info(f"DeepSeek analysis service initialized with model: {self.model}")

    async def analyze_document(
        self,
        document_text: str,
        analysis_type: str = "document_summary",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a legal document using DeepSeek.

        Args:
            document_text: Text content of the document
            analysis_type: Type of analysis (document_summary, risk_assessment, etc.)
            context: Additional context for the analysis

        Returns:
            Dict containing analysis results
        """
        if analysis_type not in self.templates:
            raise ValueError(f"Invalid analysis type: {analysis_type}")

        # Prepare prompt
        prompt_template = self.templates[analysis_type]
        prompt = prompt_template.format(
            document_text=document_text[:8000],  # Limit text length
            context=json.dumps(context) if context else "",
            case_context=context.get("case_context", "") if context else "",
            documents_summary=context.get("documents_summary", "") if context else ""
        )

        # Add system prompt
        system_prompt = """You are an expert legal analyst with deep knowledge of Indian law.
        Provide accurate, well-reasoned analysis in structured JSON format.
        Focus on practical legal advice that can be used by lawyers and clients.
        Be thorough but concise."""

        start_time = time.time()
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            processing_time = int((time.time() - start_time) * 1000)
            content = response.choices[0].message.content

            # Try to parse JSON response
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # If not JSON, wrap it
                result = {
                    "analysis": content,
                    "format_warning": "Response was not valid JSON"
                }

            # Add metadata
            result["metadata"] = {
                "model": self.model,
                "analysis_type": analysis_type,
                "processing_time_ms": processing_time,
                "token_count": response.usage.total_tokens,
                "cost_estimate": self.estimate_cost(
                    response.usage.prompt_tokens if hasattr(response.usage, 'prompt_tokens') else response.usage.total_tokens // 2,
                    response.usage.completion_tokens if hasattr(response.usage, 'completion_tokens') else response.usage.total_tokens // 2
                )
            }

            logger.info(f"Document analysis completed in {processing_time}ms")
            return result

        except Exception as e:
            logger.error(f"Error in DeepSeek analysis: {e}")
            raise

    async def batch_analyze_documents(
        self,
        documents: List[Dict[str, str]],
        analysis_type: str = "document_summary",
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple documents concurrently.

        Args:
            documents: List of dicts with 'id' and 'text' keys
            analysis_type: Type of analysis
            max_concurrent: Maximum concurrent analyses

        Returns:
            List of analysis results
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_semaphore(doc: Dict[str, str]) -> Dict[str, Any]:
            async with semaphore:
                try:
                    result = await self.analyze_document(
                        document_text=doc["text"],
                        analysis_type=analysis_type
                    )
                    return {
                        "document_id": doc["id"],
                        "success": True,
                        "result": result
                    }
                except Exception as e:
                    return {
                        "document_id": doc["id"],
                        "success": False,
                        "error": str(e)
                    }

        tasks = [analyze_with_semaphore(doc) for doc in documents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                final_results.append({
                    "success": False,
                    "error": str(result)
                })
            else:
                final_results.append(result)

        return final_results

    async def generate_legal_arguments(
        self,
        issue: str,
        facts: str,
        favorable_law: Optional[str] = None,
        opposing_law: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate legal arguments for a specific issue.

        Args:
            issue: Legal issue to address
            facts: Relevant facts
            favorable_law: Law favorable to your position
            opposing_law: Law favorable to opposing position

        Returns:
            Dict containing arguments and counterarguments
        """
        prompt = f"""Generate legal arguments for the following issue:

Legal Issue: {issue}

Facts: {facts}

{f"Favorable Law: {favorable_law}" if favorable_law else ""}
{f"Opposing Law: {opposing_law}" if opposing_law else ""}

Provide:
1. **Strong Arguments**: Best arguments for your position
2. **Weak Arguments**: Weaker but potentially useful arguments
3. **Counterarguments**: Likely arguments from opposing side
4. **Rebuttals**: How to counter opposing arguments
5. **Case Law**: Relevant precedent cases
6. **Statutory Support**: Supporting statutes and regulations
7. **Practical Considerations**: Non-legal factors to consider

Format as structured JSON."""

        system_prompt = """You are a skilled legal advocate specializing in Indian law.
        Generate persuasive, well-reasoned legal arguments supported by law and precedent.
        Be strategic and practical in your recommendations."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.3,  # Slightly higher for creative arguments
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"arguments": content}

        except Exception as e:
            logger.error(f"Error generating legal arguments: {e}")
            raise

    async def predict_case_outcome(
        self,
        case_summary: str,
        party_positions: Dict[str, str],
        similar_cases: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Predict the likely outcome of a case.

        Args:
            case_summary: Summary of the case
            party_positions: Dict with party names and their positions
            similar_cases: List of similar case summaries

        Returns:
            Dict with outcome predictions
        """
        similar_cases_text = "\n".join(similar_cases) if similar_cases else "None provided"

        prompt = f"""Predict the likely outcome of this case:

Case Summary: {case_summary}

Party Positions:
{json.dumps(party_positions, indent=2)}

Similar Cases:
{similar_cases_text}

Provide:
1. **Most Likely Outcome**: Most probable result with percentage confidence
2. **Alternative Outcomes**: Other possible outcomes with probabilities
3. **Key Factors**: Factors that will influence the outcome
4. **Critical Evidence**: Evidence that could change the outcome
5. **Timeline Prediction**: Estimated timeline for resolution
6. **Settlement Likelihood**: Probability of settlement
7. **Risk Assessment**: Risks for each party
8. **Strategic Recommendations**: Actions to improve outcome

Format as structured JSON with confidence percentages (0-100%)."""

        system_prompt = """You are an experienced legal predictor with knowledge of Indian courts.
        Be realistic and evidence-based in your predictions.
        Consider judicial trends, procedural aspects, and practical realities."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"prediction": content}

        except Exception as e:
            logger.error(f"Error predicting case outcome: {e}")
            raise

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost of API call.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in RMB (Chinese Yuan)
        """
        # DeepSeek pricing: 1 RMB per million input tokens, 2 RMB per million output tokens
        input_cost_per_million = 1.00  # 1 RMB per million input tokens
        output_cost_per_million = 2.00  # 2 RMB per million output tokens

        input_cost = (input_tokens / 1_000_000) * input_cost_per_million
        output_cost = (output_tokens / 1_000_000) * output_cost_per_million

        return round(input_cost + output_cost, 4)

    async def test_connection(self) -> bool:
        """
        Test connection to DeepSeek API.

        Returns:
            True if connection successful
        """
        try:
            await self.client.chat.completions.create(
                model=self.model,
                max_tokens=10,
                messages=[
                    {
                        "role": "user",
                        "content": "Test"
                    }
                ]
            )
            return True
        except Exception as e:
            logger.error(f"DeepSeek API connection test failed: {e}")
            return False

    async def close(self):
        """Close client."""
        await self.client.close()


# Global service instance
_deepseek_service = None


async def get_deepseek_service() -> DeepSeekAnalysisService:
    """
    Get or create DeepSeek analysis service.

    Returns:
        DeepSeekAnalysisService instance
    """
    global _deepseek_service
    if _deepseek_service is None:
        _deepseek_service = DeepSeekAnalysisService()
    return _deepseek_service


async def close_deepseek_service():
    """Close DeepSeek service."""
    global _deepseek_service
    if _deepseek_service:
        await _deepseek_service.close()
        _deepseek_service = None