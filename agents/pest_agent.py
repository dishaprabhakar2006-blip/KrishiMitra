from google.adk.agents import LlmAgent
from tools.mistral_llm import MistralLlm

mistral_model = MistralLlm()

# Define the Pest & Disease Agent
pest_agent = LlmAgent(
    name="PestAndDiseaseAgent",
    model=mistral_model,
    description="Diagnoses crop pests, diseases, and nutrient deficiencies from text descriptions of symptoms.",
    instruction=(
        "You are the Pest & Disease Agent for KrishiMitra. Your task is to identify agricultural diseases, pests, and deficiencies from the farmer's text descriptions. "
        "When helping a farmer with crop symptoms:\n"
        "1. Analyze the symptoms described by the farmer in their text query (e.g., leaf color changes, spots, wilting, insect damage, visible pests).\n"
        "2. Suggest potential crop diseases, pest infestations, or nutrient deficiencies based on those symptoms.\n"
        "3. Always provide concrete organic and chemical remedies, preventative cultural practices, and fertilizer/watering adjustments to address the issue.\n"
        "Present your recommendations clearly and structure them under bold headers in a structured, readable format."
    ),
    tools=[]
)
