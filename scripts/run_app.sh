#!/bin/bash
set -e
# set -o allexport ; . .env ; set +o allexport ;

create_venv() {
	if [ ! -d venv ]; then
        python3 -m venv venv
    fi
	if [ -d venv ]; then
        if ! source venv/bin/activate
        then
            if ! . venv/bin/activate
            then
                echo "Error activating virtual environment"
                exit 1
            fi
        fi
    fi
}

install() {
    create_venv
	if [ -f requirements.txt ]; then
        pip install -r requirements.txt;
    fi
	if [ ! -f requirements.txt ]; then
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
        pip freeze > requirements.txt;
    fi
}

requirements() {
    install
}

run() {
    install
	streamlit run streamlit_app.py
}

ACTION=$1

case $ACTION in
    "install")
        install
        ;;
    "requirements")
        requirements
        ;;
    "run")
        run
        ;;
    *)
        echo "Usage: run_app.sh <install|requirements|run>"
        exit 1
        ;;
esac