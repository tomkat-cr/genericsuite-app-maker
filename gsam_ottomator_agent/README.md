# GSAM Python FastAPI Agent

Author: [Carlos J. Ramirez](https://www.carlosjramirez.com)

Based on the [oTtomator Python agent](https://github.com/coleam00/ottomator-agents/tree/main/~sample-python-agent~) code from: [Cole Medin](https://www.youtube.com/@ColeMedin)

The [GSAM](../README.md) Python FastAPI agent, is a tool to help on the software development process for any Application. It allows to generate application ideas, app description, database estructures, and presentation content from a text prompt, and kick start code to be used with the [GenericSuite](https://genericsuite.carlosjramirez.com) library. It's compatible with the [OTTomator](https://ottomator.ai) [Live Agent Studio](https://studio.ottomator.ai).

## Overview

This AI-powered agent provides:

- **Innovative App Ideas Generation**: Craft mind-blowing web/mobile app concepts emphasizing unique features, target audiences, and potential uses.
- **Names Generation**: Propose catchy, creative names for software applications.
- **PowerPoint Content Creation**: Draft content for presentation slides and suggest prompts for generating presentation images.
- **App Description and Table Definitions**: Develop comprehensive application descriptions and detailed table definitions.
- **CRUD JSON and Python Code Generation**: Produce generic CRUD editor configuration JSON and corresponding Python code using Langchain Tools for specified operations.

It also:

- Process natural language queries
- Maintain conversation history
- Integrate with external AI models
- Store and retrieve conversation data
- Handle authentication and security

The agent comes in two variants:
1. **Supabase Version** (`gsam_supabase_agent.py`): Uses Supabase client for database operations
2. **Postgres Version** (`gsam_postgres_agent.py`): Uses direct PostgreSQL connection via asyncpg

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- PostgreSQL database or Supabase account
- Basic understanding of:
  - FastAPI and async Python
  - RESTful APIs
  - Pydantic models
  - Environment variables
  - PostgreSQL (for Postgres version)

## Core Components

### 1. FastAPI Application (`gsam_ottomator_agent_app.py`)

The main application is built using FastAPI, providing:

- **Authentication**
  - Bearer token validation via environment variables
  - Secure endpoint protection
  - Customizable security middleware

- **Request Handling**
  - Async endpoint processing
  - Structured request validation
  - Error handling and HTTP status codes

- **Database Integration**
  - Supabase connection management
  - Message storage and retrieval
  - Session-based conversation tracking

### 2. Data Models

#### Request Model
```python
class AgentRequest(BaseModel):
    query: str        # The user's input text
    user_id: str      # Unique identifier for the user
    request_id: str   # Unique identifier for this request
    session_id: str   # Current conversation session ID
```

#### Response Model
```python
class AgentResponse(BaseModel):
    success: bool     # Indicates if the request was processed successfully
```

### 3. Database Schema

The agent uses Supabase tables with the following structure:

#### Messages Table
```sql
messages (
    id: uuid primary key
    created_at: timestamp with time zone
    session_id: text
    message: jsonb {
        type: string       # 'human' or 'assistant'
        content: string    # The message content
        data: jsonb       # Optional additional data
    }
)
```

## Setup

1. **Clone Repository**
   ```bash
   # Clone the repository
   git clone git clone https://github.com/tomkat-cr/genericsuite-app-maker.git
   cd genericsuite-app-maker

   # Copy example environment file
   cp .env.example .env

   # Edit .env with your credentials
   nano .env  # or use your preferred editor
   ```

2. **Configure Environment Variables**

   > ⚠️ **Important**: For Docker, do not wrap environment variable values in quotes, even if they contain special characters. Docker will handle the values correctly without quotes.

   #### Supabase Configuration
   Required environment variables in `.env` file (do not use quotes around values):
   ```env
   SUPABASE_URL=your-project-url
   SUPABASE_SERVICE_KEY=your-service-key
   API_BEARER_TOKEN=your-token-here
   ```

   #### PostgreSQL Configuration
   Required environment variables:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/dbname
   API_BEARER_TOKEN=your-chosen-token
   ```

   The DATABASE_URL format is:
   ```plaintext
   postgresql://[user]:[password]@[host]:[port]/[database_name]
   ```

   #### LLM configurations
   ```env
   OPENROUTER_API_KEY=your-api-key-here
   OPENROUTER_MODEL_NAME=your-model-name-here
   ```

   #### Image generation configurations
   ```env
   # to use HuggingFace and Flux
   HUGGINGFACE_API_KEY=your-api-key-here
   ```

   #### Video generation configurations
   ```env
   # to use Rhymes Allegro
   RHYMES_ALLEGRO_API_KEY=your-api-key-here
   ```

3. **Create Database Tables**
   For both Supabase and PostgreSQL, you'll need to create the following tables:

```sql
-- Enable the pgcrypto extension for UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE messages (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT NOT NULL,
    message JSONB NOT NULL
);

CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

ALTER publication supabase_realtime ADD TABLE messages;
```

   > Note: If you're using Supabase, the `pgcrypto` extension is already enabled by default.

## Installation Methods

### Docker Installation (Recommended)

1. Build the base images
```bash
cd genericsuite-app-maker/gsam_ottomator_agent
make install
```

2. Run the container:
```bash
cd genericsuite-app-maker/gsam_ottomator_agent
make run
```

The agent will be available at `http://localhost:8001`.

To restart the container:
```bash
cd genericsuite-app-maker/gsam_ottomator_agent
make restart
```

To Stop and destroy the container:
```bash
cd genericsuite-app-maker/gsam_ottomator_agent
make stop
```

### Local Installation (Docker Alternative)

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. Run the agent:

For Supabase version:

Set the `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` environment variables in your `.env` file, then run:
 
```bash
uvicorn gsam_ottomator_agent_app:app --host 0.0.0.0 --port 8001
```

For PostgreSQL version:

Set the `DATABASE_URL` environment variable and leave `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` empty in your `.env` file, then run:
 
```bash
uvicorn gsam_ottomator_agent_app:app --host 0.0.0.0 --port 8001
```

## Configuration

The agent uses environment variables for configuration. You can set these variables in a `.env` file or using your operating system's environment variable settings.

## Making Your First Request

Test your agent using curl or any HTTP client:

### Supabase Version
```bash
curl -X POST http://localhost:8001/api/gsam-supabase-agent \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Hello, agent!",
    "user_id": "test-user",
    "request_id": "test-request-1",
    "session_id": "test-session-1"
  }'
```

### Postgres Version
```bash
curl -X POST http://localhost:8001/api/gsam-postgres-agent \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Hello, agent!",
    "user_id": "test-user",
    "request_id": "test-request-1",
    "session_id": "test-session-1"
  }'
```

## Troubleshooting

Common issues and solutions:

1. **Authentication Errors**
   - Verify bearer token in environment
   - Check Authorization header format
   - Ensure token matches exactly

2. **Database Connection Issues**
   - For Supabase:
     - Verify Supabase credentials
     - Validate table permissions
   - For PostgreSQL:
     - Check DATABASE_URL format
     - Verify database user permissions
     - Ensure database is running and accessible
     - Check if tables are created correctly

3. **Performance Problems**
   - Check database query performance
   - Consider caching frequently accessed data
   - For PostgreSQL:
     - Monitor connection pool usage
     - Adjust pool size if needed (default is reasonable for most cases)


## Credits

This project is developed and maintained by [Carlos J. Ramirez](https://www.linkedin.com/in/carlosjramirez/). For more information or to contribute to the project, visit [GenericSuite App Maker on GitHub](https://github.com/tomkat-cr/genericsuite-app-maker).

Happy Coding!