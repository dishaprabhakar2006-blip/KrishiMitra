import os
from typing import Tuple
from google import genai
from google.adk.agents import LlmAgent

# Import sub-agents
from agents.memory_agent import memory_agent
from agents.weather_agent import weather_agent
from agents.crop_agent import crop_agent
from agents.pest_agent import pest_agent
from agents.market_agent import market_agent
from agents.scheme_agent import scheme_agent
from agents.profit_agent import profit_agent

from tools.translation_tool import detect_language, translate_to_english, translate_from_english
from tools.mistral_llm import MistralLlm

mistral_model = MistralLlm()

# Define the Orchestrator Agent
orchestrator_agent = LlmAgent(
    name="OrchestratorAgent",
    model=mistral_model,

    description="Main router agent for KrishiMitra. Understands query intent and delegates to specialized sub-agents.",
    instruction=(
        "You are KrishiMitra's Orchestrator Agent. Your role is to serve as the lead coordinator. "
        "Your primary job is to understand what the farmer needs and call the correct specialized sub-agent by using their corresponding tool/function:\n"
        "- If the query contains the keywords 'mandi', 'price', 'rate', 'market', or 'sell' (or asks about crop prices, market rates, commodity prices, or crop selling advice): you MUST immediately call MarketPriceAgent.\n"
        "- If they ask about crop health, crop diseases, plant pathology, leaf damage, insects, pests, or crop symptoms (like yellow leaves, spots, wilting): call PestAndDiseaseAgent.\n"
        "- If they ask about weather forecasts, rainfall, climate conditions, temperature, or weather-based irrigation planning: call WeatherAgent.\n"
        "- If they ask about government schemes, subsidies, PM-KISAN, PMFBY, crop insurance, or financial aid: call SchemeFinderAgent.\n"
        "- If they ask about cultivation cost, expected yield, profit calculation, or expected margins: call ProfitCalculatorAgent.\n"
        "- If they want to select what crops to sow, soil suitability, seed varieties, or general crop recommendations: call CropAdvisoryAgent.\n"
        "- If they want to view, update, register, or change profile details: call FarmerMemoryAgent.\n\n"
        "Crucial Routing & Conversational Rules:\n"
        "1. If the query contains any of the words 'mandi', 'price', 'rate', 'market', or 'sell', you MUST delegate to MarketPriceAgent. Do not answer these directly in the Orchestrator.\n"
        "2. When routing, transfer control and state context completely to the sub-agent.\n"
        "3. If the query does not match any specialized sub-agent (e.g. general greetings, conversational questions, general farming advice, or mixed questions), DO NOT delegate. Instead, respond directly using your own knowledge as a helpful, warm, expert agricultural assistant. Answer the farmer's question directly, clearly, and concisely in a friendly tone using Mistral AI. Never say 'I could not formulate a response' under any circumstances."
    ),
    sub_agents=[
        memory_agent,
        weather_agent,
        crop_agent,
        pest_agent,
        market_agent,
        scheme_agent,
        profit_agent
    ]
)
