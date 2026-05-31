"""Resume parsing service using LLM structured output extraction."""

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm_factory import get_llm
from app.schemas import ResumeData

SYSTEM_PROMPT = """\
You are an expert resume parser. Given the raw text of a resume, extract all \
relevant information into the requested structured format.

Rules:
- Extract ONLY information explicitly present in the text.
- If a field is not found, leave it as empty string or empty list.
- For skills, list each skill as a separate item.
- For experience, capture each role separately with company, role title, dates, and key highlights.
- Be precise with names, dates, and company names – do not infer or fabricate."""


def parse_resume(text: str) -> ResumeData:
    """Parse resume text into structured data using LLM with_structured_output."""
    llm = get_llm()

    # Use LangChain's with_structured_output for guaranteed Pydantic schema conformance
    structured_llm = llm.with_structured_output(ResumeData)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Parse the following resume:\n\n{text}"),
    ]

    result: ResumeData = structured_llm.invoke(messages)
    return result
