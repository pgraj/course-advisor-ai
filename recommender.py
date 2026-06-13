import os
import json
import chromadb
from pathlib import Path
from typing import Dict, List


from utils import client

from explore_data import find_courses


def recommend_courses(profile: Dict) -> Dict:
    """
    Maps student profile data to educational levels, cross-references real
    courses using Phase 1 filter, and uses ChromaDB +  Azure OpenAI 
    client to build a personalized advisory explanation.
    """
    education_level = profile.get("education_level")
    interests = profile.get("interests", [])
    career_goal = profile.get("career_goal", "Not specified")
    
    # 1. Map education_level → eligible academic tracks
    eligible_levels = []
    if education_level == "school_passout":
        eligible_levels = ["diploma", "bachelors"]
    elif education_level == "undergraduate":
        eligible_levels = ["bachelors"]
    elif education_level == "graduate":
        eligible_levels = ["postgraduate"]
    else:
        eligible_levels = ["diploma", "bachelors", "postgraduate"]

    # 2. Extract courses using relative path-building architecture
    json_path = Path(__file__).parent / "data" / "courses" / "courses.json"
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            courses_data = json.load(f)
        master_courses = courses_data.get("courses", [])
    except Exception as e:
        print(f"Warning: Failed to load master course JSON index ({str(e)})")
        master_courses = []

    # 3. Match interests and calculate matching scores using Phase 1 logic
    course_scores = {}
    for lvl in eligible_levels:
        for interest in interests:
            # Invoking your true Phase 1 logic with the required master list parameter
            matched = find_courses(master_courses, level=lvl, interest=interest)
            
            for course in matched:
                code = course.get("code")
                if not code:
                    continue
                if code not in course_scores:
                    course_scores[code] = {"course": course, "score": 1}
                else:
                    course_scores[code]["score"] += 1

    # Sort and grab top 3 highest-scoring candidates
    sorted_candidates = sorted(course_scores.values(), key=lambda x: x["score"], reverse=True)
    top_3_recommendations = [item["course"] for item in sorted_candidates[:3]]

    if not top_3_recommendations:
        return {
            "recommendations": [],
            "explanation": "No courses found matching your current educational eligibility criteria and core interests."
        }

    # 4. Convert candidate list into a readable text block for the prompt
    candidates_str = "\n".join([f"- {c.get('name')} ({c.get('code')})" for c in top_3_recommendations])
    
    # 5. System prompt template mapping layout
    RECOMMENDER_PROMPT = """You are the Course Advisor for Horizon Institute of Applied Studies (HIAS).
A student has shared their education level, interests, and career goal.
Based on the candidate courses below, write a 3-4 sentence recommendation explaining
which course(s) suit them best and why. Be warm, specific, and reference their
stated interests or career goal. Do not invent courses outside the candidate list.

STUDENT PROFILE:
- Education level: {education_level}
- Interests: {interests}
- Career goal: {career_goal}

CANDIDATE COURSES:
{candidates}"""

    # Format prompt text cleanly with profile attributes
    formatted_prompt = RECOMMENDER_PROMPT.format(
        education_level=education_level,
        interests=", ".join(interests),
        career_goal=career_goal if career_goal else "Not specified",
        candidates=candidates_str
    )

    # 6. Call Azure OpenAI deployment directly using  config setup
    try:
        response = client.chat.completions.create(
            model=os.getenv("CHAT_DEPLOYMENT"), 
            messages=[
                {"role": "user", "content": formatted_prompt},
            ],
            temperature=0.3
        )
        explanation = response.choices[0].message.content.strip()
    except Exception as e:
        explanation = f"Automated counseling narrative generation unavailable. (Error: {str(e)})"

    return {
        "recommendations": top_3_recommendations,
        "explanation": explanation
    }


# --- Standalone Verification Test Suite ---
if __name__ == "__main__":
    # The three hardcoded test profiles
    test_profiles = [
        {"education_level": "school_passout", "interests": ["computers", "data"], "career_goal": None},
        {"education_level": "graduate", "interests": ["leadership", "business"], "career_goal": "become a product manager"},
        {"education_level": "school_passout", "interests": ["helping people"], "career_goal": "work in hospitals"},
    ]
    
    print("================================================================")
    print("      LAUNCHING RECOMMENDER STANDALONE VERIFICATION SUITE       ")
    print("================================================================\n")
    
    for idx, profile in enumerate(test_profiles, 1):
        print(f"--- PROFILE #{idx} ---")
        print(f"Education Level : {profile['education_level']}")
        print(f"Interests       : {profile['interests']}")
        print(f"Career Goal     : {profile['career_goal']}")
        print("-" * 40)
        
        # Execute mapping pipeline
        result = recommend_courses(profile)
        
        # Output structured course matches
        print("Recommended Courses:")
        if result["recommendations"]:
            for course in result["recommendations"]:
                print(f"  → [{course.get('code')}] {course.get('name')} ({course.get('level').upper()})")
        else:
            print("  → No explicit matches found for these interest tags.")
            
        # Output LLM advisory pitch text
        print("\nAdvisor's Personalized Recommendation:")
        print(result["explanation"])
        print("=" * 64 + "\n")