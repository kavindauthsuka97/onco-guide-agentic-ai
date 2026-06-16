# Import json to parse LLM JSON output
import json

# Import BaseModel to create structured claim verification result
from pydantic import BaseModel

# Import call_llm to use Groq through LangChain
from app.utils.llm import call_llm

# Import hybrid retrieval
from app.rag.hybrid_retriever import hybrid_retrieve

# Import hybrid formatter
from app.rag.hybrid_retriever import format_hybrid_context


# Create structured result for claim verification
class ClaimVerificationResult(BaseModel):

    # Store whether all important claims are supported
    verification_passed: bool

    # Store unsupported claims
    unsupported_claims: list[str]

    # Store confidence level
    confidence: str

    # Store verification reason
    reason: str

    # Store corrected final answer
    corrected_answer: str


# Clean LLM JSON output if it comes with markdown code fences
def clean_json_text(raw_text: str) -> str:

    # Remove leading and trailing spaces
    cleaned = raw_text.strip()

    # Remove markdown json fence if present
    cleaned = cleaned.replace("```json", "")

    # Remove markdown fence if present
    cleaned = cleaned.replace("```", "")

    # Return cleaned text
    return cleaned.strip()


# Check if answer already contains external tool citations/results
def answer_contains_external_evidence(answer: str) -> bool:

    # Convert answer to lowercase
    text = answer.lower()

    # Check PubMed or ClinicalTrials evidence patterns
    return (
        "pubmed.ncbi.nlm.nih.gov" in text
        or "clinicaltrials.gov" in text
        or "nct id:" in text
        or ("title:" in text and "journal:" in text and "url:" in text)
    )


# Run claim verification
def run_claim_verification_agent(user_message: str, answer: str, selected_agent: str) -> ClaimVerificationResult:

    # If answer already contains external evidence, do not rewrite it using local RAG
    if selected_agent in ["manual_tool_agent", "react_agent", "clinical_trial_agent"] and answer_contains_external_evidence(answer):

        # Return unchanged answer
        return ClaimVerificationResult(
            verification_passed=True,
            unsupported_claims=[],
            confidence="high",
            reason="External tool evidence detected, so local claim rewriting was skipped.",
            corrected_answer=answer,
        )

    # Retrieve evidence using hybrid search
    evidence_docs = hybrid_retrieve(
        query=f"{user_message}\n\n{answer}",
        top_k=4,
        max_results=6,
    )

    # Format retrieved evidence
    evidence_context = format_hybrid_context(evidence_docs)

    # Create system prompt
    system_prompt = """
    You are the Medical Claim Verification Agent for OncoGuide.

    Your job:
    - Check whether medical claims in the answer are supported by the provided evidence.
    - Identify unsupported or overconfident claims.
    - Correct unsafe or unsupported wording.
    - Do not add new medical claims that are not supported by evidence.

    Check for:
    1. Unsupported medical claims
    2. Overconfident statements
    3. Final diagnosis
    4. Treatment decision
    5. Medication or chemotherapy dosage
    6. Clinical trial eligibility claim
    7. Missing doctor/healthcare professional safety note

    Return ONLY valid JSON:
    {
      "verification_passed": true,
      "unsupported_claims": [],
      "confidence": "low/medium/high",
      "reason": "short reason",
      "corrected_answer": "corrected safe answer"
    }

    Rules:
    - If evidence is weak, use cautious language.
    - Never say the user has cancer.
    - Never say the user is eligible for a trial.
    - Never recommend treatment decisions.
    - Always recommend doctor or healthcare professional confirmation for personal medical advice.
    """

    # Create user prompt
    user_prompt = f"""
    Selected agent:
    {selected_agent}

    User message:
    {user_message}

    Draft answer:
    {answer}

    Retrieved trusted hybrid evidence:
    {evidence_context}

    Verify the medical claims and correct the answer if needed.
    """

    # Call LLM verifier
    raw_response = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0,
    )

    # Try JSON parsing
    try:

        # Clean response
        cleaned_response = clean_json_text(raw_response)

        # Parse JSON
        parsed = json.loads(cleaned_response)

        # Return structured result
        return ClaimVerificationResult(
            verification_passed=bool(parsed.get("verification_passed", True)),
            unsupported_claims=parsed.get("unsupported_claims", []),
            confidence=parsed.get("confidence", "medium"),
            reason=parsed.get("reason", "Claim verification completed."),
            corrected_answer=parsed.get("corrected_answer", answer),
        )

    # If parsing fails
    except Exception:

        # Return safe fallback
        return ClaimVerificationResult(
            verification_passed=False,
            unsupported_claims=["Could not fully verify claims because JSON parsing failed."],
            confidence="low",
            reason="Claim verification parsing failed. Safe fallback used.",
            corrected_answer=(
                answer
                + "\n\nVerification note: Some claims could not be fully verified automatically. "
                "Please confirm this information with a qualified healthcare professional."
            ),
        )