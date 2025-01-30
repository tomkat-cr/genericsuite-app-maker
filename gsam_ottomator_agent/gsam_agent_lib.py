"""
GSAM Agent library
"""
from __future__ import annotations as _annotations


from typing import List, Any
import os
from dataclasses import dataclass
from dotenv import load_dotenv

from pydantic_ai import (
    Agent,
    RunContext
)
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    TextPart
)
import logfire
from fastapi import HTTPException
from supabase import Client
from openai import AsyncOpenAI

from lib.codegen_utilities import log_debug
from lib.codegen_general_lib import GeneralLib
from lib.codegen_utilities import get_app_config
from lib.codegen_generation_lib import CodeGenLib
from lib.codegen_ideation_lib import IdeationLib
from lib.codegen_app_ideation_lib import (
    get_ideation_from_prompt_config,
    get_buttons_config_for_prompt,
)

# !pip install nest_asyncio
import nest_asyncio


DEBUG = False
MOCK_IMAGES = False
MOCK_VIDEOS = True

nest_asyncio.apply()


@dataclass
class PydanticAIDeps:
    supabase: Client
    openai_client: AsyncOpenAI


class AppContext:
    def __init__(self, params: dict = None):
        self.params = params or {}

    def set_param(self, param_name: str, param_value: Any):
        self.params[param_name] = param_value

    def get_param(self, param_name: str) -> Any:
        return self.params.get(param_name)

    def set_params(self, params: dict):
        self.params = params

    def get_params(self) -> dict:
        return self.params


load_dotenv()

app_config = get_app_config()
cgsl = GeneralLib(app_config)

app_context = AppContext({})

model_params = {}
default_llm_provider = cgsl.get_par_value("DEFAULT_LLM_PROVIDER", "openai")
if default_llm_provider == "openrouter":
    model_name = cgsl.get_par_value("OPENROUTER_MODEL_NAME")
    model_params["api_key"] = cgsl.get_par_value("OPENROUTER_API_KEY")
    model_params["base_url"] = "https://openrouter.ai/api/v1"
else:
    model_name = cgsl.get_par_value("OPENAI_MODEL_NAME", "gpt-4o-mini")
    model_params["api_key"] = cgsl.get_par_value("OPENAI_API_KEY")

model = OpenAIModel(model_name, **model_params)

# openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
openai_client = AsyncOpenAI(**model_params)

supabase: Client = Client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

logfire.configure(send_to_logfire="if-token-present")

system_prompt = cgsl.get_par_value("AGENT_SYSTEM_PROMPT")

# https://ai.pydantic.dev/api/agent/
pydantic_ai_agent = Agent(
    model, system_prompt=system_prompt, deps_type=PydanticAIDeps, retries=2
)


# Agent utilities


def headers_to_dict(headers: list[tuple(bytes, bytes)]
                    ) -> dict:
    """
    Convert a FastAPI headers object to a dictionary.
    """
    return {k.decode("latin-1"): v.decode("latin-1") for k, v in headers}


def convert_messages(conversation_history: list) -> list:
    """
    Convert a list of messages to a list of dictionaries.
    """
    # Convert conversation history to format expected by agent
    log_debug(f">>> conversation_history:\n{conversation_history}", DEBUG)
    messages = []
    for msg in conversation_history:
        msg_type = msg["role"]
        msg_content = msg["content"]
        result = ModelRequest(parts=[UserPromptPart(content=msg_content)]) \
            if msg_type == "human" else \
            ModelResponse(parts=[TextPart(content=msg_content)])
        messages.append(result)
    return messages


# Agent entry point


def run_agent(user_input: str, messages: list, http_request: dict):
    """
    Run the agent with streaming text for the user_input prompt,
    while maintaining the entire conversation in `st.session_state.messages`.
    """
    # Set app context
    app_context.set_params({
        "http_request": http_request
    })

    # Prepare dependencies
    deps = PydanticAIDeps(
        supabase=supabase,
        openai_client=openai_client
    )

    # Prepare messages
    messages = convert_messages(messages)

    # Run the agent in a stream
    result = pydantic_ai_agent.run_sync(
        user_input,
        deps=deps,
        message_history=messages,
    )
    log_debug(f">>> run_agent: {result.data}")
    return result.data


# GenericSuite tools


@pydantic_ai_agent.tool
async def generate_json_and_code(
    ctx: RunContext[PydanticAIDeps], user_query: str
) -> str:
    """
    Generate a JSON (compatible with GenericSuite) and AI Tools code
    (compatible with LangChain) based on the provided text.

    Args:
        ctx: The context including the Supabase client and OpenAI client
        user_query: The text to base the JSON and code on

    Returns:
        A JSON and code result
    """
    codegen_lib = CodeGenLib(app_config)
    result = codegen_lib.process_json_and_code_generation(user_query)
    return result


def get_ideation_result(user_query: str, button_index: int):
    """
    Get the result of an ideation request based on the provided
    text and button index.

    Args:
        user_query: The text to base the ideation request on
        button_index: The index of the button to base the ideation request on

    Returns:
        The result of the ideation request
    """
    form_config = get_ideation_from_prompt_config()
    buttons_config = get_buttons_config_for_prompt()
    buttons_submitted = [buttons_config[button_index]['key']]
    buttons_submitted_data = cgsl.get_buttons_submitted_data(
        buttons_submitted, [buttons_config[button_index]], False)
    fields_values = {
        "question": user_query,
        "buttons_submitted_data": buttons_submitted_data
    }
    ideation_lib = IdeationLib(app_config)
    result = ideation_lib.process_ideation_form(fields_values,
                                                form_config)
    return result


@pydantic_ai_agent.tool
async def generate_app_ideas(
    ctx: RunContext[PydanticAIDeps], user_query: str
) -> str:
    """
    Generate an app ideas based on the provided text.

    Args:
        ctx: The context including the Supabase client and OpenAI client
        user_query: The text to base the app ideas on

    Returns:
        The app ideas
    """
    return get_ideation_result(user_query, 0)


@pydantic_ai_agent.tool
async def generate_app_name(
    ctx: RunContext[PydanticAIDeps], user_query: str
) -> str:
    """
    Generate an app name suggestions based on the provided text.

    Args:
        ctx: The context including the Supabase client and OpenAI client
        user_query: The text to base the app name on

    Returns:
        The name suggestions for the app
    """
    return get_ideation_result(user_query, 1)


@pydantic_ai_agent.tool
async def generate_app_description(
    ctx: RunContext[PydanticAIDeps], user_query: str
) -> str:
    """
    Generate an app description and database schema based on the
    provided text.

    Args:
        ctx: The context including the Supabase client and OpenAI client
        user_query: The text to base the app description on

    Returns:
        A description and database schema of the app
    """
    return get_ideation_result(user_query, 2)


@pydantic_ai_agent.tool
async def generate_ppt_slides(
    ctx: RunContext[PydanticAIDeps], user_query: str
) -> str:
    """
    Generate PowerPoint slides based on the provided text.

    Args:
        ctx: The context including the Supabase client and OpenAI client
        user_query: The text to base the slides on

    Returns:
        A URL to the generated PowerPoint presentation
    """
    return get_ideation_result(user_query, 3)


@pydantic_ai_agent.tool
async def generate_images(
    ctx: RunContext[PydanticAIDeps],
    user_query: str
) -> str:
    """
    Generate images based on the provided text.

    Args:
        ctx: The context including the Supabase client and OpenAI client
        user_query: The text to base the images on

    Returns:
        A URL to the generated images
    """
    # Get the scheme (http/https) and host name from the request
    request = app_context.get_param("http_request")
    headers = headers_to_dict(request.get("headers"))
    log_debug(f"generate_images | request: {request}", debug=DEBUG)
    # host_name = f'{request.get("server")[0]}:{request.get("server")[1]}'
    host_name = headers.get("host")
    log_debug(f"generate_images | host_name: {host_name}", debug=DEBUG)
    # Get the http/https from the request
    scheme = request.get("scheme")
    log_debug(f"generate_images | scheme: {scheme}", debug=DEBUG)
    # Generate the image from the user input
    if MOCK_IMAGES:
        img_gen_result = {
            "error": False,
            "answer": "./images/" +
                      "hf_img_74d9a262-93cf-47c2-b745-9cd22faa4e29.jpg",
        }
    else:
        img_gen_result = cgsl.image_generation(user_query)
    if img_gen_result.get("error"):
        raise HTTPException(
            status_code=400,
            detail=f"{img_gen_result.get('error_message')} [GSAL-GI-E010]"
        )
    # Return the image URL
    image_name = img_gen_result.get("answer")
    if image_name.startswith("./images/"):
        image_name = image_name.replace(
            "./images/",
            f"{scheme}://{host_name}/api/image/")
    log_debug(f"generate_images | Image name: {image_name}", debug=DEBUG)
    return image_name


@pydantic_ai_agent.tool
async def generate_video(
    ctx: RunContext[PydanticAIDeps], user_query: str
) -> str:
    """
    Generate a video based on the provided text.

    Args:
        ctx: The context including the Supabase client and OpenAI client
        user_query: The text to base the video on

    Returns:
        A URL to the generated video
    """
    if MOCK_VIDEOS:
        video_gen_result = {
            "error": False,
            "answer": "https://apiplatform-rhymes-prod-va.s3.amazonaws.com/" +
                      "20241103031651.mp4",
        }
    else:
        video_gen_result = cgsl.video_generation(user_query)
    if video_gen_result.get("error"):
        raise HTTPException(
            status_code=400,
            detail=f"{video_gen_result.get('error_message')} [GSAL-GV-E010]"
        )
    return video_gen_result.get("answer")


# Documentation and embedding tools


async def get_embedding(text: str, openai_client: AsyncOpenAI) -> List[float]:
    """Get embedding vector from OpenAI."""
    try:
        response = await openai_client.embeddings.create(
            model="text-embedding-3-small", input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return [0] * 1536  # Return zero vector on error


@pydantic_ai_agent.tool
async def retrieve_relevant_documentation(
    ctx: RunContext[PydanticAIDeps], user_query: str
) -> str:
    """
    Retrieve relevant documentation chunks based on the query with RAG.

    Args:
        ctx: The context including the Supabase client and OpenAI client
        user_query: The user's question or query

    Returns:
        A formatted string containing the top 5 most relevant documentation
        chunks
    """
    try:
        # Get the embedding for the query
        query_embedding = await get_embedding(
            user_query,
            ctx.deps.openai_client)

        # Query Supabase for relevant documents
        result = ctx.deps.supabase.rpc(
            "match_site_pages",
            {
                "query_embedding": query_embedding,
                "match_count": 5,
                "filter": {"source": "pydantic_ai_docs"},
            },
        ).execute()

        if not result.data:
            return "No relevant documentation found."

        # Format the results
        formatted_chunks = []
        for doc in result.data:
            chunk_text = f"""
# {doc['title']}

{doc['content']}
"""
            formatted_chunks.append(chunk_text)

        # Join all chunks with a separator
        return "\n\n---\n\n".join(formatted_chunks)

    except Exception as e:
        print(f"Error retrieving documentation: {e}")
        return f"Error retrieving documentation: {str(e)}"


@pydantic_ai_agent.tool
async def list_documentation_pages(ctx: RunContext[PydanticAIDeps]
                                   ) -> List[str]:
    """
    Retrieve a list of all available GenericSuite documentation pages.

    Returns:
        List[str]: List of unique URLs for all documentation pages
    """
    try:
        # Query Supabase for unique URLs where source is pydantic_ai_docs
        result = (
            ctx.deps.supabase.from_("site_pages")
            .select("url")
            .eq("metadata->>source", "pydantic_ai_docs")
            .execute()
        )

        if not result.data:
            return []

        # Extract unique URLs
        urls = sorted(set(doc["url"] for doc in result.data))
        return urls

    except Exception as e:
        print(f"Error retrieving documentation pages: {e}")
        return []


@pydantic_ai_agent.tool
async def get_page_content(ctx: RunContext[PydanticAIDeps], url: str) -> str:
    """
    Retrieve the full content of a specific documentation page by combining
    all its chunks.

    Args:
        ctx: The context including the Supabase client
        url: The URL of the page to retrieve

    Returns:
        str: The complete page content with all chunks combined in order
    """
    try:
        # Query Supabase for all chunks of this URL, ordered by chunk_number
        result = (
            ctx.deps.supabase.from_("site_pages")
            .select("title, content, chunk_number")
            .eq("url", url)
            .eq("metadata->>source", "pydantic_ai_docs")
            .order("chunk_number")
            .execute()
        )

        if not result.data:
            return f"No content found for URL: {url}"

        # Format the page with its title and all chunks

        # Get the main title
        page_title = result.data[0]["title"].split(" - ")[0]
        formatted_content = [f"# {page_title}\n"]

        # Add each chunk's content
        for chunk in result.data:
            formatted_content.append(chunk["content"])

        # Join everything together
        return "\n\n".join(formatted_content)

    except Exception as e:
        print(f"Error retrieving page content: {e}")
        return f"Error retrieving page content: {str(e)}"
