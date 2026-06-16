# Import PubMed search tool
from app.tools.pubmed_tool import pubmed_search_tool

# Import clinical trials search tool
from app.tools.clinical_trials_tool import clinical_trials_search_tool

# Import NCI PDQ local search tool
from app.tools.nci_pdq_tool import nci_pdq_search_tool

# Import medical entity extraction tool
from app.tools.entity_extraction_tool import medical_entity_extraction_tool

# Import risk scoring tool
from app.tools.risk_scoring_tool import risk_scoring_tool

# Import report parser tool
from app.tools.report_parser_tool import report_parser_tool

# Import citation checker tool
from app.tools.citation_checker_tool import citation_checker_tool

# Import emergency red flag tool
from app.tools.emergency_tool import emergency_red_flag_tool

# Import vector search tool
from app.tools.vector_search_tool import vector_search_tool

# Import BM25 search tool
from app.tools.bm25_search_tool import bm25_search_tool


# Store all tools in one list
ALL_TOOLS = [
    pubmed_search_tool,
    clinical_trials_search_tool,
    nci_pdq_search_tool,
    medical_entity_extraction_tool,
    risk_scoring_tool,
    report_parser_tool,
    citation_checker_tool,
    emergency_red_flag_tool,
    vector_search_tool,
    bm25_search_tool,
]