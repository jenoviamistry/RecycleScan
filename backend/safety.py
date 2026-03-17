import os # lets us read the env vars injected at runtime
import json
import google.generativeai as genai # google python library for Gemini API (nicknamed genai)
from dataclasses import dataclass 
from dotenv import load_dotenv # opens env and loads API keys into memory 

load_dotenv() # loads env file into env memory 
genai.configure(api_key=os.getenv("GEMINI_API_KEY")) # read the API key and use for each request

# Constants
CONFIDENCE_THRESH = 0.5 # if huggingface returns conf. score < 0.5, ask for clarification

# From San Mateo County Household Hazardous Waste Earth911 guidelines
HAZARDOUS_KEYS = {
    #fuels
    "gasoline", "kerosene", "motor oil", "brake fluid",
    "transmission fluid", "hydraulic fluid", "power steering fluid",
    "antifreeze", "lighter fluid",
    #paints
    "latex paint", "oil paint", "paint stripper", "paint thinner",
    "varnish", "lacquer", "wood stain", "sealer",
    #batteries
    "battery", "lithium", "lithium-ion", "nickel-cadmium",
    #chemicals
    "acid", "solvent", "degreaser", "pool chemical",
    "photographic chemical", "fertilizer", "fungicide",
    "herbicide", "insecticide", "pesticide", "adhesive",
    #aerosol
    "aerosol", "propane", "compressed gas",
    #alcohol based
    "hair dye", "nail polish", "nail polish remover", "lice shampoo",
    #mercury
    "mercury", "fluorescent", "cfl",
    #extra
    "chemistry set", "oil filter", "bleach"
}

#Dataclass
@dataclass # generate all the init code for data-holding class
class SafetyResult: # data type returned after every safety check
    is_safe: bool # did all pass? false = needs attention
    requires_special_handling: bool # hazardous item, needs a facility
    clarification_needed: bool # image was unclear or confidence low
    clarification_prompt: str | None # ask user for clarification if needed, can be a string or empty
    override_reason: str | None #if the safety layer overrode, why?
    item_name: str | None # what did Gemini identify the item as
    disposal_method: str | None # trash, recycle, compost, special case
    explanation: str | None # Gemini's explanation language for user

#Gemini safety prompt, giving a template response
GEMINI_PROMPT = """
You are a waste disposal assistant. Analyze this image carefully.
Respond only in valid JSON with this exact structure please:
{
    "item_name": "name of the item",
    "material": "primary material (plastic, metal, glass, paper, cardboard, or other)",
    "is_hazardous": true or false,
    "hazard_reason": "why is it hazardous, or null if it is not hazardous",
    "disposal_method": "trash, recycle, compost, or special",
    "explanation": "plain and simple language explanation of why it should be disposed this way please",
    "confidence": "high, medium, or low"
}

Rules: If the item contains or appears to be a hazardous material set is_hazardous to true. 
Look carefully at labels, shape, and context clues. If you cannot clearly identify the item, set confidence to low.
disposal_method must be exactly one of: trash, recycle, compost, or special.
Never invent disposal facilities or addresses.
"""

#Safety Functions
def check_confidence(huggingface_confidence: float) -> SafetyResult | None: # pass a float (the huggingface confidence), return SafetyResult object or None(nothing wrong keep going)
    if huggingface_confidence < CONFIDENCE_THRESH: # less the 0.5 confidence returned
        return SafetyResult(
            is_safe = False,
            requires_special_handling = False,
            clarification_needed = True,
            clarification_prompt = ("I could not clearly identify this item. "
                                    "Could you please retake the photo with better lighting, "
                                    "or check if there is a recycling symbol on it. Thanks!"
            ),
            override_reason = None,
            item_name = None,
            disposal_method = None,
            explanation = None
        )
    return None

async def analyze_with_gemini(image_bytes: bytes) -> SafetyResult: # async so doesn't freeze other requests, always return SafetyResult
    model = genai.GenerativeModel("gemini-1.5-flash")
    try:
        response = model.generate_content([ # send request to gemini
            {"mime_type": "image/jpeg", "data": image_bytes}, # tell Gemini image format and give raw image data
            GEMINI_PROMPT # structured instructions I created
        ])

        raw = response.text.strip() # raw Gemini response as a JSON string, remove lead/trail whitespace or newlines
        if raw.startswith("```"): # remove if present
            raw = raw.split("```")[1] 
            if raw.startswith("json"): # remove if present
                raw = raw[4:]
        
        gemini_data = json.loads(raw) # convert JSON string into python dict gemini_date["item_name"]
    
    except Exception as e: # if anything went wrong, catch here log as e
        return SafetyResult(
            is_safe = False,
            requires_special_handling = False,
            clarification_needed = True,
            clarification_prompt = f"Gemini error: {str(e)}",
            override_reason = None,
            item_name = None,
            disposal_method = None,
            explanation = None
        )
    
    # if low confidence ask user for clarification
    if gemini_data.get("confidence") == "low": # used .get incase no key exists instead of crashing
        return SafetyResult(
            is_safe = False,
            requires_special_handling = False,
            clarification_needed = True,
            clarification_prompt = (
                "I'm not confident about this item.."
                "Can you please retake the photo or describe what it is? Thanks!"
            ),
            override_reason = None,
            item_name = gemini_data.get("item_name"),
            disposal_method = None,
            explanation = None
        )

    # if hazardous override everything, "special" hardcoded for now
    if gemini_data.get("is_hazardous"):
        return SafetyResult(
            is_safe = False,
            requires_special_handling = True,
            clarification_needed = False,
            clarification_prompt = None,
            override_reason = (
                f"Hazardous item detected: {gemini_data.get('item_name')}."
                f"{gemini_data.get('hazard_reason')}"
                f"Please use a certified disposal facility."
            ),
            item_name = gemini_data.get("item_name"),
            disposal_method = "special",
            explanation = gemini_data.get("explanation")
        )
    
    return SafetyResult( # safety checks passed for confidence and hazardous
        is_safe = True,
        requires_special_handling = False,
        clarification_needed = False,
        clarification_prompt = None,
        override_reason = None,
        item_name = gemini_data.get("item_name"),
        disposal_method = gemini_data.get("disposal_method"),
        explanation = gemini_data.get("explanation")
    )

async def run_safety_checks(huggingface_confidence: float, image_bytes: bytes) -> SafetyResult:
    confidence_result = check_confidence(huggingface_confidence) 
    if confidence_result: # if not none (confidence was not fine), something is wrong, enter if =
        return confidence_result # stop here, send SafetyResult back to main.py
    #else keep going
    return await analyze_with_gemini(image_bytes) # confidence was fine, now ask Gemini
