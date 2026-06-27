import os
import json
from typing import Dict, Any, List, Optional
from google.adk.agents import LlmAgent
from tools.translation_tool import detect_language, translate_to_english
from tools.mistral_llm import MistralLlm

mistral_model = MistralLlm()


PROFILES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "farmer_profiles.json")

def get_farmer_profile(user_id: str = "default_farmer") -> Dict[str, Any]:
    """
    Retrieves the farmer's profile, including name, location, land size, and crop history.
    
    Args:
        user_id: The ID of the farmer (defaults to 'default_farmer').
        
    Returns:
        A dictionary of the farmer's profile details.
    """
    if not os.path.exists(PROFILES_FILE):
        # Create empty profile database
        os.makedirs(os.path.dirname(PROFILES_FILE), exist_ok=True)
        with open(PROFILES_FILE, "w") as f:
            json.dump({}, f)
            
    try:
        with open(PROFILES_FILE, "r") as f:
            profiles = json.load(f)
        profile = profiles.get(user_id)
        if not profile:
            # Return a blank profile schema
            return {
                "user_id": user_id,
                "name": "Unknown Farmer",
                "name_en": "Unknown Farmer",
                "location": "Not Specified",
                "location_en": "Not Specified",
                "land_size_acres": 0.0,
                "crop_history": [],
                "crop_history_en": [],
                "is_new": True
            }
        profile["is_new"] = False
        # Guarantee en fields exist
        if "name_en" not in profile:
            profile["name_en"] = profile.get("name", "Unknown Farmer")
        if "location_en" not in profile:
            profile["location_en"] = profile.get("location", "Not Specified")
        if "crop_history_en" not in profile:
            profile["crop_history_en"] = profile.get("crop_history", [])
        return profile
    except Exception as e:
        return {"error": f"Failed to read profile: {str(e)}", "user_id": user_id}

def update_farmer_profile(
    name: Optional[str] = None,
    location: Optional[str] = None,
    land_size_acres: Optional[float] = None,
    crop_history: Optional[List[str]] = None,
    user_id: str = "default_farmer"
) -> Dict[str, Any]:
    """
    Updates or creates a farmer's profile.
    
    Args:
        name: Name of the farmer (e.g., "Ramesh Kumar").
        location: City/Town and State in India (e.g., "Karnal, Haryana", "Pune, Maharashtra").
        land_size_acres: Size of farmland in acres.
        crop_history: List of crops previously grown or currently growing (e.g., ["Wheat", "Mustard"]).
        user_id: The ID of the farmer (defaults to 'default_farmer').
        
    Returns:
        A dictionary with the updated profile and status.
    """
    os.makedirs(os.path.dirname(PROFILES_FILE), exist_ok=True)
    if not os.path.exists(PROFILES_FILE):
        profiles = {}
    else:
        try:
            with open(PROFILES_FILE, "r") as f:
                profiles = json.load(f)
        except Exception:
            profiles = {}
            
    profile = profiles.get(user_id, {
        "user_id": user_id,
        "name": "Unknown Farmer",
        "name_en": "Unknown Farmer",
        "location": "Not Specified",
        "location_en": "Not Specified",
        "land_size_acres": 0.0,
        "crop_history": [],
        "crop_history_en": []
    })
    
    if name is not None:
        profile["name"] = name
        lang = detect_language(name)
        profile["name_en"] = translate_to_english(name, lang) if lang != "english" else name
        
    if location is not None:
        profile["location"] = location
        lang = detect_language(location)
        profile["location_en"] = translate_to_english(location, lang) if lang != "english" else location
        
    if land_size_acres is not None:
        try:
            profile["land_size_acres"] = float(land_size_acres)
        except ValueError:
            pass
            
    if crop_history is not None:
        # Handle cases where it is passed as a string or list
        if isinstance(crop_history, str):
            crops = [c.strip() for c in crop_history.split(",") if c.strip()]
        else:
            crops = crop_history
            
        profile["crop_history"] = crops
        # Translate crop history to English in background
        crops_en = []
        for crop in crops:
            crop_lang = detect_language(crop)
            crop_en = translate_to_english(crop, crop_lang) if crop_lang != "english" else crop
            crops_en.append(crop_en)
        profile["crop_history_en"] = crops_en
            
    profiles[user_id] = profile
    
    try:
        with open(PROFILES_FILE, "w") as f:
            json.dump(profiles, f, indent=4)
        return {"success": True, "message": "Profile updated successfully.", "profile": profile}
    except Exception as e:
        return {"success": False, "error": f"Failed to save profile: {str(e)}"}

# Define the Memory Agent
memory_agent = LlmAgent(
    name="FarmerMemoryAgent",
    model=mistral_model,
    description="Manages the farmer's profile, including location, name, land size, and crop history.",
    instruction=(
        "You are the Farmer Memory Agent for KrishiMitra. Your task is to handle profile retrieval and updates. "
        "Always use 'get_farmer_profile' to view the profile and 'update_farmer_profile' to modify details. "
        "When the farmer introduces themselves or provides their details (e.g., name, location, land size, crop history), "
        "use the 'update_farmer_profile' tool to save the information. "
        "Acknowledge the update and present a friendly, formatted summary of the profile to the farmer in markdown."
    ),
    tools=[get_farmer_profile, update_farmer_profile]
)
