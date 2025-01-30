#!/bin/bash
# run_agent.sh
# 2025-01-28 | CR
#
set -e

REPO_BASEDIR="`pwd`"
cd "`dirname "$0"`"
SCRIPTS_DIR="`pwd`"
cd "${REPO_BASEDIR}"

set -o allexport
if [ ! -f .env ]
then
    echo "ERROR: .env file not found"
    exit 1
fi
if ! source .env
then
    if ! . .env
    then
        echo "ERROR: .env file could not be sourced"
        exit 1
    fi
fi
set +o allexport ;

start_venv() {
    if [ ! -d venv ]; then
        if ! python -m venv venv
        then
            echo "Error creating virtual environment"
            exit 1
        fi
    fi
    if ! source venv/bin/activate
    then
        if ! . venv/bin/activate
        then
            echo "Error activating virtual environment"
            exit 1
        fi
    fi
}

install_requirements() {
    start_venv
    if [ -f requirements.txt ]; then
        pip install -r requirements.txt
    else
        pip install --upgrade pip;
        # Dependencies needed for the Agent:
        # fastapi, uvicorn, pydantic, pydantic, pydantic, supabase, asyncpg, nest_asyncio, python-dotenv, llama-index
        # Dependencies needed for the UI:
        # streamlit, requests, python-dotenv, pymongo, python-pptx, openai, ollama, groq, together, llama-index
        if ! pip install \
            fastapi \
            uvicorn \
            pydantic \
            pydantic-ai \
            pydantic-ai[logfire] \
            supabase \
            asyncpg \
            nest_asyncio \
            streamlit \
            requests \
            python-dotenv \
            pymongo \
            python-pptx \
            openai \
            ollama \
            groq \
            together \
            llama-index;
        then
            echo "Error installing requirements"
            exit 1
        fi
        REQUIREMENTS_DIR="."
        if [ ! -f "gsam_ottomator_agent_app.py" ]; then
            REQUIREMENTS_DIR=".."
        fi
        if ! pip freeze > "${REQUIREMENTS_DIR}/requirements.txt"
        then
            echo "Error saving requirements"
            exit 1
        fi
    fi
}

check_docker() {
    if ! command -v docker &> /dev/null
    then
        echo "ERROR: Docker is not installed"
        exit 1
    fi
    if ! docker ps &> /dev/null
    then
        echo "ERROR: Docker is not running"
        exit 1
    fi
}

if [ "$ACTION" = "" ]; then
    ACTION="$1"
fi
if [ "$ACTION" = "" ]; then
    echo "Usage: run_agent.sh <install|run|stop|requirements|uvicorn_server|logs>"
    exit 1
fi

if [ "$ACTION" = "requirements" ]; then
    echo ""
    echo "Install requirements"
    echo ""
    install_requirements
    deactivate
fi

if [ "$ACTION" = "run_uvicorn_server" ]; then
    echo ""
    echo "Run the uvicorn server"
    echo ""
    install_requirements
    if [ "${PORT}" = "" ];then
        PORT="8001"
    fi
    pwd
    ls -la
    uvicorn gsam_ottomator_agent_app:app --host 0.0.0.0 --port ${PORT} --reload
    deactivate
fi

if [ "$ACTION" = "install" ]; then
    check_docker
    echo ""
    echo "Build the base image first (make sure Docker is running on your machine)"
    echo ""
    cd ./base_python_docker
    docker build -t ottomator/base-python:latest .
    cd ..

    echo ""
    echo "2. Build the agent image (you can swap between Supabase and PostgreSQL versions in the Dockerfile):"
    echo ""
    docker build -t gsam-python-agent .
fi

if [ "$ACTION" = "run" ]; then
    check_docker
    echo ""
    echo "Run the container"
    echo ""
    docker run -v "$(pwd)/..":/app -d --name gsam-python-agent -p 8001:8001 --env-file .env gsam-python-agent
    docker ps
    docker logs -f gsam-python-agent
fi

if [ "$ACTION" = "stop" ]; then
    check_docker
    echo ""
    echo "Stop and remove the container"
    echo ""
    if ! docker stop gsam-python-agent
    then
        echo "Container not running"
    fi
    if ! docker rm gsam-python-agent
    then
        echo "Container already removed"
    fi
    docker ps
fi

if [ "$ACTION" = "logs" ]; then
    check_docker
    docker logs -f gsam-python-agent
fi

echo ""
echo "Done!"
