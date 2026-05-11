import json
from google.adk.agents import LlmAgent, SequentialAgent

# ==========================================
# 1. mock tools (the kitchen stations)
# ==========================================


def grill_beef(doneness: str) -> str:
    """simulates the Grill Chef cooking the beef patty."""
    # returns data representing cooked meat as JSON
    return json.dumps(
        {"item": "Angus Beef Patty", "status": f"Cooked {doneness}", "weight": "1/2 lb"}
    )


def prep_greens(style: str) -> str:
    """simulates the Salad Chef preparing the fresh greens and toppings."""
    # returns data representing the prepped vegetables as JSON
    return json.dumps(
        {
            "item": "Fresh Greens",
            "style": style,
            "components": ["Crisp Lettuce", "Heirloom Tomato", "Red Onion"],
        }
    )


def assemble_plate(meat_json: str, greens_json: str) -> dict:
    """Combines the grill and salad outputs into a single burger order."""
    # parses both inputs and merges them into one complete order
    meat = json.loads(meat_json)
    greens = json.loads(greens_json)
    return {
        "order": "Burger Meal 🍔",
        "grill": meat,
        "salad": greens,
        "status": "ready",
        "assembled_by": "ADK Kitchen Brigade",
    }


# ==========================================
# 2. the chefs (sub-agents)
# ==========================================

# the grill chef gets the heavy model. focused only on cooking the meat.
grill_chef = LlmAgent(
    model="gemini-2.5-flash",
    name="GrillChef",
    description="Cooks the beef patty to the requested doneness using the grill.",
    instruction="""You are the Grill Chef. Your ONLY job is to use the grill_beef tool
    to cook the meat to the requested doneness. Do not format the output. Just return the raw JSON.""",
    tools=[grill_beef],
)

# the salad chef gets a fast model. focused only on prepping the greens.
salad_chef = LlmAgent(
    model="gemini-2.5-flash",
    name="SaladChef",
    description="Preps the fresh greens and toppings in the requested style.",
    instruction="""You are the Salad Chef. Your ONLY job is to use the prep_greens
    tool to prepare the requested style of greens. Return the raw JSON from the tool.""",
    tools=[prep_greens],
)

# the plater agent gets a fast model. focused only on assembly and presentation.
plater_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="PlaterAgent",
    description="Assembles the final plate using the grill and salad outputs.",
    instruction="""You are the Plater Agent. Take the raw JSON data provided by both
    the Grill Chef and the Salad Chef, and use the assemble_plate tool to combine them.

    Once you get the result, present the order to the guest in a fun, friendly way:
    - Use emojis to make it visually appealing
    - Format it as a clean order receipt with clear sections for the burger and salad
    - Include the cooking style, greens style, and all components
    - Add a warm sign-off message
    - Do NOT show raw JSON to the guest — make it feel like a real restaurant experience""",
    tools=[assemble_plate],
)

# ==========================================
# 3. the expediter (sequential pipeline)
# ==========================================

# SequentialAgent ensures the order: cook the beef -> prep the greens -> plate the meal
kitchen_expediter = SequentialAgent(
    name="KitchenExpediter",
    description="Runs the full kitchen pipeline in order: grill -> salad -> plate.",
    sub_agents=[grill_chef, salad_chef, plater_agent],
)

# ==========================================
# 4. the host (root agent — ADK entry point)
# ==========================================

# root_agent is required by ADK as the entry point for the agent module.
# the host greets the user, collects the order details, then transfers to the kitchen pipeline.
root_agent = LlmAgent(
    model="gemini-2.5-pro",
    name="KitchenHost",
    description="Greets guests, takes their burger order, and routes it to the kitchen.",
    instruction="""You are the friendly host of the ADK Kitchen Brigade.

    When a guest arrives, greet them warmly and let them know you're here to craft their perfect burger.

    Ask them two things:
    1. How they'd like their beef cooked — options: rare, medium-rare, medium, medium-well, or well-done
    2. What style of greens they'd prefer — options: classic, caesar, or garden

    Once you have both answers, transfer the order to KitchenExpediter to prepare the meal.
    Do not cook or prep anything yourself.""",
    sub_agents=[kitchen_expediter],
)
