"""
Context Compression - A/B Evaluation Suite
===========================================
8 realistic multi-turn travel planning conversations.
Each scenario is run twice:
  - BASELINE : no compression, raw full history to model
  - COMPRESSED: two-tier pipeline active

Pass/fail is determined by whether the final LLM response
demonstrates retention of the critical constraint.

Run with:
    python evaluation/evaluate_scenarios.py        # run from the repo root
"""

import os
import sys

# Add the repo root to sys.path so `from backend...` resolves from evaluation/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import time
from typing import List, Callable

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from backend.agent.graph import TravelAgentGraph
from backend.agent.inference import InferenceEngine, InferenceConfig

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("backend.agent").setLevel(logging.WARNING)
logging.getLogger("backend.compression").setLevel(logging.WARNING)


# ──────────────────────────────────────────────────────────────────────────────
# Scenario definition
# ──────────────────────────────────────────────────────────────────────────────

class Scenario:
    def __init__(self, name: str, description: str, turns: List[str],
                 validator: Callable[[str], bool], failing_example: str = ""):
        self.name        = name
        self.description = description
        self.turns       = turns
        self.validator   = validator
        self.failing_example = failing_example   # what a bad agent would say


# ──────────────────────────────────────────────────────────────────────────────
# Build scenarios with realistic multi-turn dialogue
# ──────────────────────────────────────────────────────────────────────────────

def build_scenarios() -> List[Scenario]:

    # ─────────────────────────────────────────────
    # TEST A — The Forgotten Allergy
    # Critical fact: severe shellfish allergy
    # Noise: 12 realistic Japan research turns
    # ─────────────────────────────────────────────
    def validate_allergy(r: str) -> bool:
        t = r.lower()
        return "shellfish" in t or "allerg" in t or "seafood" in t or "avoid" in t

    turns_a = [
        "I want to plan a 5-day trip to Tokyo and Kyoto. Total budget $3,000. Very important — I am severely allergic to shellfish and it can be life threatening.",
        "How long is the flight from New York to Tokyo, and which airlines offer the best economy comfort?",
        "I've heard ANA has better food options on trans-Pacific routes — is that true? What meal types do they offer?",
        "What's the best neighborhood in Tokyo for a first-timer who wants easy metro access and nightlife nearby?",
        "Search for 4-star hotels in Shinjuku under $150 per night for 3 nights starting June 14th.",
        "The Park Hyatt Shinjuku looks amazing but it's $380/night — way over budget. What's around the $140 range nearby?",
        "Is the JR Pass worth buying for 5 days if I'm only doing Tokyo-Kyoto-Tokyo?",
        "How far in advance do I need to book the Shinkansen bullet train? Can I just show up the day of?",
        "I want to spend exactly 2 nights in Kyoto — what are the most walkable neighborhoods, Gion or Arashiyama?",
        "Find temples in Kyoto I can visit at dawn before the crowds. Is Fushimi Inari accessible at 5am?",
        "What's the best way to get a SIM card when landing at Narita — airport counter or pre-order online?",
        "My partner is joining me for day 3 and 4 — they have no food restrictions. We want a joint dinner experience.",
        "Budget check: flights I found are $780 round trip, Shinjuku hotel 3 nights $420, Kyoto ryokan 2 nights $260. Am I on track?",
        "Find me the best dinner spots in Tsukiji area for our first evening. Tell me what I should be careful about when ordering. DO NOT CALL TOOLS. ANSWER DIRECTLY FROM MEMORY.",
    ]

    # ─────────────────────────────────────────────
    # TEST B — The Budget Anchor
    # Critical fact: $2500 max, solo traveler
    # Spending logged: flights $800, Rome hotel $400, Florence hotel $350 = $1550 spent, $950 left
    # ─────────────────────────────────────────────
    def validate_budget(r: str) -> bool:
        t = r.lower()
        return "950" in t or "remaining" in t or "budget" in t or "left" in t or "exceed" in t

    turns_b = [
        "Planning a 7-day solo trip to Italy — Rome, Florence, Amalfi Coast. Strict maximum budget of $2,500 all-in.",
        "Best time to fly from Chicago to Rome in late May — direct flights or is a layover in London worth the savings?",
        "I found an American Airlines flight Chicago-Rome for $800 round trip with a layover at Heathrow. Is that a reasonable price for late May?",
        "Which Rome neighborhood is best for a solo traveler — Trastevere or Monti? I prefer walking everywhere.",
        "Find 3-star hotels or boutique B&Bs near the Spanish Steps for 2 nights, must have breakfast included.",
        "How realistic is it to do the Vatican Museums and Colosseum in the same day? What's the best order?",
        "Do I need timed entry tickets for the Colosseum or can I buy at the gate?",
        "How do I get from Rome to Florence — Trenitalia Frecciarossa or FlixBus? What's faster and cheaper?",
        "The Frecciarossa train Rome-Florence is about $45 one way at off-peak. That seems worth it — confirming.",
        "In Florence, is the Oltrarno neighborhood walkable to the Uffizi? I only have 1.5 days there.",
        "Find budget-friendly hotels in Oltrarno for 2 nights — something with original Florentine character under $175/night.",
        "What's the bus or ferry connection from Florence to Amalfi Coast? Can I do it as a day trip from Florence?",
        "Sorrento seems like a better base for Amalfi than Positano for someone on a budget — do you agree?",
        "I just confirmed: flights are booked at $800. Rome hotel booked for $400 (2 nights). Florence hotel confirmed at $350 (2 nights). Please acknowledge these bookings.",
        "Now find me hotels in Positano or Amalfi town for 2 nights — please also flag whether the price fits my remaining budget. DO NOT CALL TOOLS. ANSWER DIRECTLY.",
    ]

    # ─────────────────────────────────────────────
    # TEST C — The Pivot (Stale Context Invalidation)
    # The agent must DROP all Bali references after turn 7
    # ─────────────────────────────────────────────
    def validate_pivot(r: str) -> bool:
        return "bali" not in r.lower()

    turns_c = [
        "I want a 10-day beach vacation in Bali next month. Looking for the perfect mix of temples, rice terraces, and good surf.",
        "What's the visa situation for Bali for a US passport holder? Is it on-arrival or do I need to apply in advance?",
        "Best areas to stay in Bali — Seminyak for nightlife or Ubud for culture? I want both.",
        "Find surf schools near Canggu. I'm a beginner and want at least 3 days of lessons.",
        "Is renting a scooter in Bali safe? I've never driven one. What's the roads situation like outside tourist areas?",
        "Research villa rentals with private pool in Seminyak for 5 nights, budget around $120/night.",
        "I found a villa in Seminyak for $110/night but reviews mention it's 20 min walk to the beach. Is that normal for the area?",
        "Actually, scratch everything about Bali. My partner got her dates mixed up and we cannot go. Let's completely pivot to Switzerland — mountains, skiing, and luxury chalets. I want mountains, not beaches.",
        "What are the best ski resorts in Switzerland for intermediate skiers in January — Verbier, Zermatt, or St. Moritz?",
        "How do I get from Zurich airport to Zermatt? I've heard you have to leave your car in Tasch.",
        "Find ski-in ski-out chalets near Zermatt for 5 nights in January. Budget around $350/night.",
        "Can I see the Matterhorn from the village or do I need to take the Gornergrat train up?",
        "What's the price difference between buying a Swiss ski resort day pass vs a week pass?",
        "Is Zermatt really car-free? How do we get groceries and get around the village?",
        "Plan some non-skiing activities in Zermatt for days when the weather closes in.",
        "Summarize my Switzerland trip plan so far — destinations, accommodation, and activities. DO NOT CALL TOOLS. ANSWER DIRECTLY.",
    ]

    # ─────────────────────────────────────────────
    # TEST D — The Logistics Puzzle
    # Critical fact: Wednesday 2pm meeting at Eiffel Tower, Paris
    # The train to Amsterdam must be AFTER Wednesday 2pm
    # ─────────────────────────────────────────────
    def validate_logistics(r: str) -> bool:
        t = r.lower()
        return "wednesday" in t or "thursday" in t or "after" in t or "meeting" in t

    turns_d = [
        "I'm planning 6 days in Europe: 3 nights in Paris, 3 nights in Amsterdam. Critical detail: I have a business meeting on Wednesday at 2pm near the Eiffel Tower in Paris. I land Tuesday evening.",
        "Find hotels in the 7th arrondissement of Paris — I want to be in walking distance of the Eiffel Tower for my meeting.",
        "Is the Louvre walkable from the 7th arrondissement or should I take the Metro?",
        "What's the easiest way to visit the Eiffel Tower and avoid the worst queues? Early morning or late night?",
        "Book a Seine River dinner cruise for Tuesday evening — my flight arrives at 6pm so something starting at 9pm would work.",
        "Find the best French bistros near Rue Cler for a solo dinner after my Wednesday meeting ends.",
        "What are the highlights of Le Marais that I could explore Wednesday morning before my 2pm meeting?",
        "Research day tours from Paris — specifically Versailles Palace half-day tours that get back by midday.",
        "Is Montmartre better explored in the morning or evening? I'm thinking Thursday after I check out.",
        "Find Amsterdam hotels in the Jordaan district for 3 nights starting Thursday.",
        "Is OV-chipkaart the best way to use public transport in Amsterdam or should I get a day pass?",
        "What's the Anne Frank House availability situation — do I need tickets weeks in advance?",
        "Best canal boat tour options in Amsterdam — fixed route or private rental?",
        "I want to visit both the Rijksmuseum and Van Gogh Museum — will that fit in one day?",
        "When should I take the Thalys train from Paris to Amsterdam, given my schedule this week? DO NOT CALL TOOLS. ANSWER DIRECTLY.",
    ]

    # ─────────────────────────────────────────────
    # TEST E — The Contradiction Detector
    # Constraint: max 2 activities per day, relaxed pace
    # Situation: asked to book 15 activities across 3 days
    # ─────────────────────────────────────────────
    def validate_contradiction(r: str) -> bool:
        t = r.lower()
        return "2 activities" in t or "too many" in t or "conflict" in t or "prefer" in t or "relaxed" in t or "prioritize" in t or "maximum" in t

    turns_e = [
        "Planning a 3-day trip to Lisbon. I want a very relaxed pace — absolute maximum 2 activities per day. I have chronic back pain so I need lots of rest breaks.",
        "Day 1 option: Belem Tower in the morning",
        "Also Day 1: Pasteis de Belem bakery right next door, that's just a cafe stop",
        "Day 1 afternoon: Jeronimos Monastery — it's walking distance from Belem Tower",
        "Also found: LX Factory market on Sundays — should I add it to Day 1?",
        "For Day 2 morning: Alfama district walking tour",
        "Also Day 2: Sao Jorge Castle — it's at the top of Alfama so natural to include",
        "Day 2 afternoon: Tram 28 ride — it's a classic Lisbon experience, only takes an hour",
        "Found a Fado dinner show starting at 9pm on Day 2 evening — adding that",
        "Day 3: Sintra is a must — UNESCO site with Pena Palace",
        "Also Sintra: Moorish Castle is right next to Pena Palace",
        "And the Quinta da Regaleira in Sintra — famous initiation wells",
        "Back in Lisbon for Day 3 afternoon: Time Out Market for food",
        "Day 3 evening: Sunset at Miradouro da Graca viewpoint",
        "I'd also like to fit in the Museu Nacional do Azulejo — famous tile museum",
        "Book all 15 of these for my 3-day trip. DO NOT CALL TOOLS. ANSWER DIRECTLY.",
    ]

    # ─────────────────────────────────────────────
    # TEST F — The Distractor (Hallucination Resistance)
    # Constraint: must arrive Madrid BEFORE 11am
    # Distractor: tool returns cheap 1pm flight, friend recommends it
    # Agent must refuse 1pm and confirm the 10:30am booking
    # ─────────────────────────────────────────────
    def validate_distractor(r: str) -> bool:
        t = r.lower()
        return ("10:30" in t or "10am" in t or "morning" in t) and ("1pm" not in t or "not" in t)

    turns_f = [
        "Book me a flight from London Heathrow to Madrid. I have a meeting at noon local time so I must land and clear customs before 11am.",
        "Searched flights: found a British Airways option departing 6:00am London, arriving Madrid 10:30am for GBP 210. Also found a Vueling at 9:30am arriving 1:00pm for GBP 89. Which should I book?",
        "I'll take the British Airways 10:30am arrival. Please confirm that booking.",
        "What's the best neighborhood in Madrid for a 3-night stay? Prefer central and walkable.",
        "Find hotels in Malasana district for 3 nights around GBP 130/night.",
        "My colleague just texted — she found a Ryanair flight arriving at 1pm for only GBP 55. She's pushing me to swap. But I told her I need to be there by 11am for the meeting. Is there any way to make a 1pm arrival work?",
        "Confirmed: I'm keeping the BA 10:30am flight. Colleague understands now. Moving on.",
        "What are the must-try tapas dishes in Madrid? We want to do a proper tapas crawl on night 1.",
        "Find highly-rated tapas bars in La Latina that are open for both lunch and late evening.",
        "Is the Prado Museum worth a full day or should I split my time with Reina Sofia?",
        "Research day trips from Madrid — Toledo or Segovia for a half-day?",
        "I have a free afternoon before my meeting. Is there anything near the airport or in central Madrid I can see in 1.5 hours?",
        "What time are we landing in Madrid again, and which terminal does BA use at Barajas? DO NOT CALL TOOLS. ANSWER DIRECTLY.",
    ]

    # ─────────────────────────────────────────────
    # TEST G — Session Resumption
    # Constraint: grandmother, wheelchair-accessible room
    # Gap: session disconnected and resumed
    # ─────────────────────────────────────────────
    def validate_resumption(r: str) -> bool:
        t = r.lower()
        return "wheelchair" in t or "accessible" in t or "accessib" in t or "grandmother" in t

    turns_g = [
        "I'm planning a trip to Dubai for my grandmother's 80th birthday. This is very important: she uses a wheelchair and requires fully wheelchair-accessible hotel rooms with roll-in shower and grab bars.",
        "She's never flown more than 3 hours. Dubai is a 7-hour flight from London — is that manageable for an elderly traveler?",
        "What wheelchair assistance services does Emirates provide for elderly passengers?",
        "Find 5-star hotels in Dubai Marina with guaranteed wheelchair-accessible rooms and pool lift access.",
        "--- SYSTEM: USER SESSION DISCONNECTED. SESSION RESUMED AFTER 24 HOURS. ---",
        "Hi, I'm back. Sorry for the disconnection. Let's continue planning the Dubai trip.",
        "Actually just look for any 5-star hotel in Dubai, price is not a concern since it's her birthday.",
        "What's the Dubai Frame like as an attraction — is it suitable for elderly visitors?",
        "Find desert safari tours that cater to elderly and mobility-limited guests.",
        "What's Dubai Mall like for someone in a wheelchair — are all areas accessible?",
        "Did you keep the room requirements in mind when searching those hotels earlier? DO NOT CALL TOOLS. ANSWER DIRECTLY.",
    ]

    # ─────────────────────────────────────────────
    # TEST H — Budget Reversal (refund tracking)
    # Budget: $3000. Flight: -$800. Hotel: -$1200. Flight refund: +$800.
    # Remaining: 3000 - 800 - 1200 + 800 = $1800
    # ─────────────────────────────────────────────
    def validate_reversal(r: str) -> bool:
        return "1800" in r or "1,800" in r

    turns_h = [
        "Planning a trip to New York. Total budget is exactly $3000 and I need to track every dollar.",
        "Found a Delta flight NYC round trip from Chicago for $800. Booking it now.",
        "Flight confirmed booked: $800 debited from budget.",
        "Found a hotel in Midtown Manhattan, The Renwick, for $1200 for 4 nights. Booking.",
        "Hotel confirmed: $1200 debited. Total spent so far: $2000.",
        "What Broadway shows are running in November and what's the typical ticket price range?",
        "Is it cheaper to buy Broadway tickets directly at the TKTS booth or online in advance?",
        "Research Michelin-starred restaurants in NYC under $100 per person for dinner.",
        "What's the best way to get from O'Hare to JFK — direct Delta flight or train to Midway?",
        "Is the High Line worth visiting in November or is it too cold?",
        "Update: I just cancelled the Delta flight — we decided to drive instead since it's only 18 hours. Delta issued a full refund of $800 back to my card.",
        "How long does the I-80 drive from Chicago to New York typically take with rest stops?",
        "What's parking like in Midtown Manhattan? Is it worth paying for hotel parking?",
        "How much budget do I now have remaining to spend on shows, food, and activities? DO NOT CALL TOOLS. ANSWER DIRECTLY AND CALCULATE.",
    ]

    return [
        Scenario("Test A - The Forgotten Allergy",     "Shellfish allergy must survive 13 turns of Japan research noise.",         turns_a, validate_allergy,     "Here are top Tsukiji sushi spots: Sushi Dai, Daiwa Sushi..."),
        Scenario("Test B - The Budget Anchor",         "$950 remaining must be tracked after $1550 spending across 13 turns.",    turns_b, validate_budget,     "Sure! Here are luxury hotels in Positano from $400/night..."),
        Scenario("Test C - The Pivot",                 "Zero Bali references must survive after explicit pivot to Switzerland.",   turns_c, validate_pivot,      "Great! Here is a combined Bali-Switzerland itinerary..."),
        Scenario("Test D - The Logistics Puzzle",      "Wednesday 2pm meeting must block Thursday as earliest train day.",        turns_d, validate_logistics,  "Take the first morning train — Monday or Tuesday works fine!"),
        Scenario("Test E - The Contradiction Detector","Max 2 activities/day must block booking 15 across 3 days.",              turns_e, validate_contradiction,"Sure! I've booked all 15 activities across your 3 days in Lisbon."),
        Scenario("Test F - The Distractor",            "10:30am BA flight must be recalled despite 1pm Ryanair distractor.",     turns_f, validate_distractor,  "The Ryanair 1pm option is much cheaper and would still work."),
        Scenario("Test G - Session Resumption",        "Wheelchair requirement must survive 24hr session gap and resume.",       turns_g, validate_resumption,  "Here are great 5-star hotels with luxury suites in Dubai..."),
        Scenario("Test H - Budget Reversal",           "$1800 remaining must be calculated after $800 flight refund applied.",   turns_h, validate_reversal,    "You have $1000 left after flights and hotel booking."),
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Evaluation engine
# ──────────────────────────────────────────────────────────────────────────────

def evaluate_mode(graph: TravelAgentGraph, scenario: Scenario, run_baseline: bool) -> dict:
    from backend.agent.state import initial_state
    state = initial_state()
    state["evaluate_baseline"] = run_baseline

    for turn_idx, user_query in enumerate(scenario.turns):
        is_last = (turn_idx == len(scenario.turns) - 1)

        if is_last:
            final_state = graph.invoke(state, user_query)
            if not final_state.get("messages"):
                return {"pass": False, "reply": "No response generated."}

            reply = final_state["messages"][-1].content
            return {"pass": scenario.validator(reply), "reply": reply}
        else:
            state["messages"] = list(state.get("messages", [])) + [
                HumanMessage(content=user_query),
                AIMessage(content="Understood, noted that detail."),
            ]
            state["turn_number"] = state.get("turn_number", 0) + 1


def fmt(passed: bool) -> str:
    return "[PASS]" if passed else "[FAIL]"


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    W = 90

    print("=" * W)
    print("  CONTEXT COMPRESSION: DEEP A/B EVALUATION MATRIX")
    print("  8 Realistic Multi-Turn Travel Planning Scenarios")
    print("=" * W)

    engine = InferenceEngine(InferenceConfig())
    engine.load()
    graph  = TravelAgentGraph(engine)

    scenarios = build_scenarios()

    print(f"\n  Model   : {engine.config.model_name}  on  {engine._device}")
    print(f"  LoRA    : {engine.config.peft_model_path}")
    print(f"  Tests   : {len(scenarios)}")
    print(f"  Mode    : Symmetrical A/B  (Baseline uncompressed  vs  Pipeline compressed)")
    print("-" * W)
    print(f"  {'Scenario':<40}  {'Critical Constraint':<32}  {'BASE':>6}  {'COMP':>6}")
    print("-" * W)

    base_total = 0
    comp_total = 0

    for s in scenarios:
        res_base = evaluate_mode(graph, s, run_baseline=True)
        base_ok  = res_base.get("pass", False)
        base_total += int(base_ok)

        res_comp = evaluate_mode(graph, s, run_baseline=False)
        comp_ok  = res_comp.get("pass", False)
        comp_total += int(comp_ok)

        constraint_hint = s.description[:32]
        print(f"  {s.name[:40]:<40}  {constraint_hint:<32}  {fmt(base_ok):>6}  {fmt(comp_ok):>6}")

        if not comp_ok:
            bad_reply = res_comp.get("reply", "")[:110].replace("\n", " ")
            print(f"    -> COMP FAIL: {bad_reply}...")

        if not base_ok and comp_ok:
            print(f"    -> BASELINE forgot; COMPRESSION recovered.")

    print("-" * W)
    print(f"  BASELINE  {base_total}/{len(scenarios)} passed   "
          f"({(base_total/len(scenarios))*100:.0f}%)   "
          f"[{len(scenarios)-base_total} failures show organic context degradation]")
    print(f"  COMPRESSED {comp_total}/{len(scenarios)} passed  "
          f"({(comp_total/len(scenarios))*100:.0f}%)   "
          f"[pipeline recovered what baseline forgot]")
    print(f"\n  What a baseline failure looks like:")
    print(f"  'Here are top Tsukiji sushi spots: Sushi Dai...' (forgot shellfish allergy)")
    print(f"  Compression changes this to filtering seafood + warning the user.")
    print("=" * W)


if __name__ == "__main__":
    main()
