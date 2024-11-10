# CHANGELOG

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/) and [Keep a Changelog](http://keepachangelog.com/).



## Unreleased
---

### New

### Changes

### Fixes

### Breaks


## Unreleased
## 0.1.0 (2024-11-09)
---

### New
Add tabs to organize the multiple app and code generation options [GS-55].
Add use response as prompt feature [GS-55].
Add llamaindex embeddings index query on code generator.
Add get_unified_flag() to configure providers and models that only accepts user messages,  not system prompt, like o1-preview.
Add prepare_model_params() to normalize the client and model parameters preparartion.
Add LlamaIndexCustomLLM to abstract the llamaindex models with codegen LlmProvider.
Add show_conversation_debug() to give the usert with detailled model responses.

### Changes
Main streamlit UI layout elements separated in different functions [GS-55].
All model type (text, video, image) uses the model configuration UI selection [GS-55].
"Invalid LLM/ImageGen/TextToVideo provider" detailed error.
read_file() allows to save the read files in a local directory to allow llamaindex embeddings to read it.

### Fixes
Fix the way enhance prompt feature works, because it was not working properly with the absense of prompt text model [GS-55].


## 0.0.1 (2024-11-08)
---

### New
Project started for the [Llama Impact Hackathon](https://lablab.ai/event/llama-impact-hackathon) [GS-55].
Add frontend UI in stramlit.io [GS-152].
Add code generation backend to create the Genericsuite JSON files and Tools Python code [GS-149].
Add video generation and follow-up data in the conversation database [GS-153].
Add image generation [GS-152].
Add the video gallery page [GS-153].
Add the image gallery page [GS-55].
Add MongoDB support [GS-152].
Add prompt enhancement support [GS-152].
Add data management pull down section in the side bar [GS-152].
Add import and export database items to JSON files [GS-152].
Add DatabaseAbstract class to normalize the database classes structure [GS-152].
Add initial version of the GS mini-library, chat feature, image generation [GS-149].
Add Streamlit UI library to normalize all Streamlit specific methods and include it in the codegen library [GS-55].
Add get_new_item_id() to normalize the new "id" creation [GS-152].
Add code generation results processing and save in conversations [SS-149].
Add configuration in JSON files [GS-55].
Add parameters values that can be read from a file path, e.g. "[refine_video_prompt.txt]" [GS-55].
Add suggestions user customizable prompt [SS-149].
Add conversations buffer to speed up the separated questions and content display [SS-149].
Add models selection [GS-55].
Add buttons to generate project ideas, names, presentation and video script [GS-55].
