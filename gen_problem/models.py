from langchain_openai import AzureChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
load_dotenv()

def gemini_2_flash(temperature):
    return ChatGoogleGenerativeAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        model="gemini-2.0-flash",
        temperature=temperature,
        max_tokens=8190
    )

def gemini_2_5_pro(temperature):
    return ChatGoogleGenerativeAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        model="gemini-2.5-pro-preview-03-25",
        temperature=temperature,
        max_tokens=65000,
        max_retries=3,
        timeout=60
    )

def gpt_4o_mini(temperature=0.7):
    return AzureChatOpenAI(
        model="gpt-4o-mini",
        temperature=temperature,
        max_tokens=16000,
        api_version="2024-08-01-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        azure_deployment="gpt-4o-mini"
    )

def o3_mini():
    return AzureChatOpenAI(
        model="o3-mini",
        model_kwargs = {"max_completion_tokens": 100000},
        api_version="2024-12-01-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        azure_deployment="o3-mini"
    )