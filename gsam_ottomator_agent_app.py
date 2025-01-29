"""
GSAM Ottomator Agent
"""
import os
from dotenv import load_dotenv

from fastapi import Depends, HTTPException

from gsam_ottomator_agent.gsam_supabase_agent import (
    init_fastapi_app as init_fastapi_app_supabase,
    verify_token as verify_token_supabase,
    gsam_supabase_agent,
    AgentRequest as SupaBaseAgentRequest,
    AgentResponse as SupaBaseAgentResponse
)
from gsam_ottomator_agent.gsam_postgres_agent import (
    init_fastapi_app as init_fastapi_app_postgres,
    verify_token as verify_token_postgres,
    gsam_postgres_agent,
    AgentRequest as PostgresAgentRequest,
    AgentResponse as PostgresAgentResponse
)


# Load environment variables
load_dotenv()

agent_db_type = "supabase" if os.getenv("SUPABASE_URL") else "postgres"

app = init_fastapi_app_supabase()
if agent_db_type == "postgres":
    app = init_fastapi_app_postgres()


@app.post("/api/gsam-supabase-agent", response_model=SupaBaseAgentResponse)
async def gsam_supabase_agent_endpoint(
    request: SupaBaseAgentRequest,
    authenticated: bool = Depends(verify_token_supabase)
):
    if agent_db_type != "supabase":
        raise HTTPException(
            status_code=400,
            detail="Invalid agent database type [GSAE-E010]"
        )
    result = await gsam_supabase_agent(request)
    return result


@app.post("/api/gsam-postgres-agent", response_model=PostgresAgentResponse)
async def gsam_postgres_agent_endpoint(
    request: PostgresAgentRequest,
    authenticated: bool = Depends(verify_token_postgres)
):
    if agent_db_type != "postgres":
        raise HTTPException(
            status_code=400,
            detail="Invalid agent database type [GPAE-E010]"
        )
    result = await gsam_postgres_agent(request)
    return result
