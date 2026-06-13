import os
import json
from typing import Dict, Tuple

# Core runtime bindings from your engineering framework
from .chat_engine import ask
from .recommender import recommend_courses

def handle_message(message: str, state: Dict) -> Tuple[str, Dict]:
    """
    Main dialogue router. Processes profile attributes first to maintain consistent state
    tracking across hybrid intent turns, checks for conversational questions to prevent 
    intent confusion, routes policy queries, and manages course recommendations.
    
    Returns:
        Tuple[str, Dict]: A tuple containing (response_text, updated_state)
    """
    msg_lower = message.lower().strip()
    
    # -------------------------------------------------------------------------
    # STATE INITIALIZATION
    # -------------------------------------------------------------------------
    if "education_level" not in state:
        state["education_level"] = None
    if "interests" not in state:
        state["interests"] = []
    if "career_goal" not in state:
        state["career_goal"] = None
    if "recommended" not in state:
        state["recommended"] = False

    # -------------------------------------------------------------------------
    # STEP 1: Process Profiling Signals First (With Option A Question Guard)
    # -------------------------------------------------------------------------
    # Detect Education Levels
    if any(word in msg_lower for word in ["school passout", "school leaver", "finished school", "high school"]):
        state["education_level"] = "school_passout"
    elif any(word in msg_lower for word in ["undergraduate", "bachelors", "doing my degree", "uni student"]):
        state["education_level"] = "undergraduate"
    elif any(word in msg_lower for word in ["graduate", "finished my degree", "postgrad", "completed bachelors"]):
        state["graduate_level"] = "graduate"

    # Option A: Detect if the message is a question or an inquiry turn
    QUESTION_STARTERS = ("does", "do", "what", "what's", "how", "is", "can", "could", "which", "tell me")
    is_question = "?" in msg_lower or msg_lower.startswith(QUESTION_STARTERS)

    # ONLY parse or mutate interests if the turn is an explicit statement/profile signal
    if not is_question:
        clean_msg = msg_lower.replace(",", " ").replace(".", " ").replace("!", " ").replace("?", " ")
        words = set(clean_msg.split())
        
        interest_keywords = [
            "data", "tech", "technology", "computer", "computers", 
            "business", "leadership", "health", "hospital", "science", "ai"
        ]
        
        # Broadened negation dictionary layout to capture conversational rejections
        NEGATIONS = [
            "not interested", "no i am not", "no i'm not", "no, i'm not", "no, i am not",
            "don't like", "do not like", "don't want", "do not want", "dont want", "no want",
            "remove", "not into", "drop", "exclude", "no "
        ]
        is_negation = any(neg in msg_lower for neg in NEGATIONS) or msg_lower.startswith("no ")
        
        for keyword in interest_keywords:
            if keyword in words:
                if is_negation:
                    if keyword in state["interests"]:
                        state["interests"].remove(keyword)
                        state["recommended"] = False  # Reset flag to allow recalculation
                else:
                    if keyword not in state["interests"]:
                        state["interests"].append(keyword)
                        state["recommended"] = False  # Reset flag to trigger fresh recommendation

    # Detect Career Goals
    if "become a" in msg_lower:
        state["career_goal"] = msg_lower.split("become a")[-1].strip().strip("!.,? ")
    elif "work in" in msg_lower:
        state["career_goal"] = msg_lower.split("work in")[-1].strip().strip("!.,? ")
    elif "career goal is" in msg_lower:
        state["career_goal"] = msg_lower.split("career goal is")[-1].strip().strip("!.,? ")

    # -------------------------------------------------------------------------
    # STEP 2: Institutional Policy Rule-Based Intent Check
    # -------------------------------------------------------------------------
    policy_keywords = ["fee", "refund", "cancel", "enrol", "exam", "extension", "census", "withdraw"]
    if any(keyword in msg_lower for keyword in policy_keywords):
        qa_result = ask(message)
        sources_str = f"\n\n[Sources: {', '.join(qa_result['sources'])}]" if qa_result["sources"] else ""
        return f"{qa_result['answer']}{sources_str}", state

    # -------------------------------------------------------------------------
    # STEP 3: Dialogue Orchestration & Dynamic Recommendation Phase
    # -------------------------------------------------------------------------
    if state["education_level"] and state["interests"]:
        if not state["recommended"]:
            state["recommended"] = True
            rec_result = recommend_courses(state)
            
            course_list = [f"- {c.get('name')} ({c.get('code')})" for c in rec_result["recommendations"]]
            courses_str = "\n".join(course_list) if course_list else "- No structural program matches found."
            
            response_output = (
                f"Thank you for sharing your details! Based on your profile, I have compiled your "
                f"academic options:\n\n{courses_str}\n\n{rec_result['explanation']}"
            )
            return response_output, state
        else:
            # Fallback when profile is already complete and no adjustments were requested
            return "I see your profile is set up! Let me know if you have specific questions about these courses or our academic policies.", state

    # Dynamic Slot-Filling Engine Questions
    if not state["education_level"]:
        return (
            "Welcome to HIAS! To help me guide your academic journey, what is your current "
            "highest level of completed education? (e.g., high school passout, undergraduate student, or graduate?)", 
            state
        )
        
    if not state["interests"]:
        return (
            "Got it. What areas or subjects are you passionate about? (e.g., computers, data, leadership, health?)", 
            state
        )

    return "Tell me a bit more about your background, fields of interest, or what career goals you are aiming for!", state


# --- Comprehensive Multi-Turn Test Suite Runner ---
if __name__ == "__main__":
    print("================================================================")
    print("             LAUNCHING CONVERSATIONAL ADVISOR ROUTER            ")
    print("================================================================\n")

    chat_state = {"education_level": None, "interests": [], "career_goal": None}
    
    # Execution script covering standard input, changes, negations, and question traps
    turns = [
        "Hi, I just finished school. What happens if I withdraw after census?",
        "Oh, okay. Well, I am really interested in computers and data.",
        "does computers also have data?",
        "No want computers.",
        "I'm interested in leadership."
    ]
    
    for i, user_message in enumerate(turns, 1):
        print(f"Turn {i} | Student: '{user_message}'")
        ai_response, chat_state = handle_message(user_message, chat_state)
        print(f"Turn {i} | Advisor :\n{ai_response}")
        print(f"Current System State: {chat_state}")
        print("-" * 80 + "\n")