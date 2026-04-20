import os
import re
import logging
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from services.neo4j_service import neo4j_service

logger = logging.getLogger(__name__)

SCHEMA_CONTEXT = """
Graph Schema — Sanchaalan Saathi Knowledge Graph:

Node Labels and Properties:
- Location: {id, name, ward, lat, lng, point}
- Need: {id, type, sub_type, description, urgency_score, population_affected, status, reported_at}
  type values: infrastructure | water_sanitation | medical | food | shelter | safety
  status values: PENDING | CLAIMED | VERIFIED
- Skill: {name, category}
  category values: medical | technical | logistics | education | construction
- Volunteer: {id, name, phone, reputationScore, availabilityStatus, totalXP, totalTasksCompleted}
  availabilityStatus values: ACTIVE | BUSY | OFFLINE
- Task: {id, title, status}

Relationship Types:
- (Need)-[:LOCATED_IN]->(Location)
- (Need)-[:REQUIRES_SKILL]->(Skill)
- (Need)-[:CAUSED_BY]->(Need)         ← causal chain edges
- (Need)-[:SPAWNED_TASK]->(Task)
- (Volunteer)-[:LOCATED_IN]->(Location)
- (Volunteer)-[:HAS_SKILL]->(Skill)
- (Volunteer)-[:ASSIGNED_TO]->(Need)

Rules for generating Cypher:
1. Output ONLY a raw Cypher query string — no markdown, no explanation, no ```cypher blocks.
2. ALWAYS LIMIT results to 20 unless the user asks for more.
3. Use OPTIONAL MATCH for relationships that might not exist.
4. Never use WRITE operations (CREATE, MERGE, SET, DELETE) — read-only queries only.
5. Property names are case-sensitive: use `availabilityStatus` (camelCase) not `availability_status`.
"""

prompt = PromptTemplate(
    input_variables=["question", "schema"],
    template="""You are a Cypher query generator for a Neo4j graph database.

Schema:
{schema}

User Question: {question}

Generate a Cypher query that answers the question. Return ONLY the raw Cypher query string, nothing else."""
)

# Dangerous keywords that must never appear in generated Cypher
WRITE_KEYWORDS = re.compile(
    r"\b(CREATE|MERGE|SET|DELETE|REMOVE|DROP|DETACH|CALL\s+apoc\.periodic|LOAD\s+CSV)\b",
    re.IGNORECASE
)


async def text_to_cypher(question: str) -> dict:
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            google_api_key=os.environ.get("GEMINI_API_KEY", "")
        )
        formatted_prompt = prompt.format(schema=SCHEMA_CONTEXT, question=question)

        # Run sync LangChain call in thread pool to not block the event loop
        response = await asyncio.get_event_loop().run_in_executor(
            None, llm.invoke, formatted_prompt
        )
        cypher = response.content.strip()

        # Strip any markdown code fences
        for prefix in ("```cypher", "```"):
            if cypher.startswith(prefix):
                cypher = cypher[len(prefix):]
        if cypher.endswith("```"):
            cypher = cypher[:-3]
        cypher = cypher.strip()

        # Safety: reject write operations
        if WRITE_KEYWORDS.search(cypher):
            return {"error": "Query contains write operations — not permitted.", "cypher": cypher, "results": []}

        # Execute cypher
        results = await neo4j_service.run_query(cypher)
        return {"cypher": cypher, "results": results}

    except Exception as e:
        logger.error(f"Text to cypher failed: {e}")
        return {"error": str(e), "cypher": None, "results": []}
