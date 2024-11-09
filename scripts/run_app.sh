#!/bin/bash
set -e
# set -o allexport ; . .env ; set +o allexport ;

create_venv() {
	if [ ! -d venv ]; then python3 -m venv venv; fi
	if [ -d venv ]; then source venv/bin/activate; fi
}

install() {
    create_venv
	if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
	if [ ! -f requirements.txt ]; then pip install --upgrade pip; pip install streamlit requests python-dotenv pymongo openai ollama groq together ; pip freeze > requirements.txt; fi
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