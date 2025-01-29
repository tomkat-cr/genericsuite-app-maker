#!/bin/bash
# run_schema_generator.sh
# 2024-10-27 | CR
#
set -o allexport ; . .env ; set +o allexport ;
REPO_BASEDIR="`pwd`"
cd "`dirname "$0"`"
SCRIPTS_DIR="`pwd`"
#
if [ ! -d "venv" ]; then
    python -m venv venv
fi
source venv/bin/activate
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    pip install requests ollama openai groq
    pip freeze > requirements.txt
fi

if [ "${CODEGEN_AI_PROVIDER}" = "" ]; then
    CODEGEN_AI_PROVIDER="${LANGCHAIN_DEFAULT_MODEL}"
fi
if [ "${CODEGEN_AI_PROVIDER}" = "" ]; then
    echo "ERROR: CODEGEN_AI_PROVIDER not set"
    exit 1
fi

if [ "${USER_INPUT}" = "" ]; then
    USER_INPUT="./user_input_example.md"
fi

PARAMETERS=""

# Ollama specific parameters
if [ "${OLLAMA_BASE_URL}" != "" ]; then
    PARAMETERS="${PARAMETERS} --ollama_base_url ${OLLAMA_BASE_URL}"
fi
if [ "${OLLAMA_TEMPERATURE}" != "" ]; then
    PARAMETERS="${PARAMETERS} --temperature ${OLLAMA_TEMPERATURE}"
fi
if [ "${OLLAMA_STREAM}" != "" ]; then
    PARAMETERS="${PARAMETERS} --stream ${OLLAMA_STREAM}"
fi

# Model specific parameters

if [ "${CODEGEN_AI_MODEL}" != "" ]; then
    PARAMETERS="${PARAMETERS} --model ${CODEGEN_AI_MODEL}"
else
    if [ "${CODEGEN_AI_PROVIDER}" = "ollama" ]; then
        if [ "${OLLAMA_MODEL}" != "" ]; then
            PARAMETERS="${PARAMETERS} --model ${OLLAMA_MODEL}"
        fi
    fi
    if [ "${CODEGEN_AI_PROVIDER}" = "nvidia" ]; then
        if [ "${NVIDIA_MODEL}" != "" ]; then
            PARAMETERS="${PARAMETERS} --model ${NVIDIA_MODEL}"
        fi
    fi
    if [ "${CODEGEN_AI_PROVIDER}" = "chat_openai" ]; then
        if [ "${OPENAI_MODEL}" != "" ]; then
            PARAMETERS="${PARAMETERS} --model ${OPENAI_MODEL}"
        fi
    fi
    if [ "${CODEGEN_AI_PROVIDER}" = "openai" ]; then
        if [ "${OPENAI_MODEL}" != "" ]; then
            PARAMETERS="${PARAMETERS} --model ${OPENAI_MODEL}"
        fi
    fi
    if [ "${CODEGEN_AI_PROVIDER}" = "groq" ]; then
        if [ "${GROQ_MODEL}" != "" ]; then
            PARAMETERS="${PARAMETERS} --model ${GROQ_MODEL}"
        fi
    fi
    if [ "${CODEGEN_AI_PROVIDER}" = "aria" ]; then
        if [ "${RHYMES_ARIA_MODEL}" != "" ]; then
            PARAMETERS="${PARAMETERS} --model ${RHYMES_ARIA_MODEL}"
        fi
    fi
fi

# Other parameters
if [ "${AGENTS_COUNT}" != "" ]; then
    PARAMETERS="${PARAMETERS} --agents_count ${AGENTS_COUNT}"
fi

echo ""
echo "Executing: python schema_generator.py --user_input \"${USER_INPUT}\" --provider ${CODEGEN_AI_PROVIDER} ${PARAMETERS}"
pwd
echo ""
python lib/codegen_schema_generator.py --user_input "${USER_INPUT}" --provider ${CODEGEN_AI_PROVIDER} ${PARAMETERS}

deactivate
if [ "${CODEGEN_KEEP_VENV}" != "1" ]; then
    rm -rf venv
fi
