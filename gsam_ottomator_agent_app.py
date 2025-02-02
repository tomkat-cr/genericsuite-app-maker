"""
GSAM Ottomator Agent
"""
import os
from dotenv import load_dotenv

from pydantic import BaseModel
from fastapi import Depends, HTTPException, Request
from fastapi.responses import FileResponse

# from lib.codegen_utilities import log_debug

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


# FastAPI headers reference:
# https://fastapi.tiangolo.com/tutorial/header-param-models/#forbid-extra-headers
# https://fastapi.tiangolo.com/tutorial/header-params/#header-parameters-with-a-pydantic-model

class CommonHeaders(BaseModel):
    host: str
    scheme: str
    # save_data: bool
    # if_modified_since: str | None = None
    # traceparent: str | None = None
    # x_tag: list[str] = []


DEBUG = False

# Load environment variables
load_dotenv()

agent_db_type = "supabase" if os.getenv("SUPABASE_URL") else "postgres"

if agent_db_type == "postgres":
    app = init_fastapi_app_postgres()
else:
    app = init_fastapi_app_supabase()


@app.post("/api/gsam-supabase-agent", response_model=SupaBaseAgentResponse)
async def gsam_supabase_agent_endpoint(
    agent_request: SupaBaseAgentRequest,
    authenticated: bool = Depends(verify_token_supabase),
    request: Request = None
):
    if agent_db_type != "supabase":
        raise HTTPException(
            status_code=400,
            detail="Invalid agent database type [GSAE-E010]"
        )
    result = await gsam_supabase_agent(agent_request, authenticated,
                                       dict(request))
    return result


@app.post("/api/gsam-postgres-agent", response_model=PostgresAgentResponse)
async def gsam_postgres_agent_endpoint(
    agent_request: PostgresAgentRequest,
    authenticated: bool = Depends(verify_token_postgres),
    request: Request = None
):
    if agent_db_type != "postgres":
        raise HTTPException(
            status_code=400,                
            detail="Invalid agent database type [GPAE-E010]"
        )
    result = await gsam_postgres_agent(agent_request, authenticated,
                                       dict(request))
    return result


@app.get("/api/image/{image_name}")
async def get_image(image_name: str):
    image_path = f"./images/{image_name}"
    if not os.path.exists(image_path):
        raise HTTPException(
            status_code=404,
            detail=f"Image {image_name} not found")
    # return FileResponse(image_path, media_type="image/jpg")
    return FileResponse(image_path)
