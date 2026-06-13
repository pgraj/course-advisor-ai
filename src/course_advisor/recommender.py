import os
import json
import chromadb
from pathlib import Path
from typing import Dict, List
from .utils import client
from .explore_data import find_courses


def load_master_courses_database() -> List[dict]:
    """
    18-course institutional dataset from JSON path
    using exact relative path-building architecture.
    """
    json_path = Path(__file__).parent / "data" / "courses" / "courses.json"
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            courses_data = json.load(f)
        return courses_data.get("courses", [])
    except Exception as e:
        print(f"Warning: Failed to load master course JSON index ({str(e)})")
        return []

def get_eligible_levels(education_level: str) -> List[str]:
    """
    Maps student academic backgrounds to structural institutional tracks.
    """
    if education_level == "school_passout":
        return ["diploma", "bachelors"]
    elif education_level == "undergraduate":
        return ["bachelors"]
    elif education_level == "graduate":
        return ["postgraduate"]
    return ["diploma", "bachelors", "postgraduate"]

def score_and_rank_courses(
    master_courses: List[dict], 
    eligible_levels: List[str], 
    interests: List[str]
) -> List[dict]:
    """
    Find_courses loop engine, cross-referencing interest tags, 
    and scoring relevant programmatic results to find the top 3 options.
    """
    course_scores = {}
    
    for lvl in eligible_levels:
        for interest in interests:
            # Invoking  Phase 1 logic with the required master list parameter
            matched = find_courses(master_courses, level=lvl, interest=interest)
            
            for course in matched:
                code = course.get("code")
                if not code:
                    continue
                if code not in course_scores:
                    course_scores[code] = {"course": course, "score": 1}
                else:
                    course_scores[code]["score"] += 1

    # Order by frequency of student interest alignment hits
    sorted_candidates = sorted(course_scores.values(), key=lambda x: x["score"], reverse=True)
    return [item["course"] for item in sorted_candidates[:3]]

def generate_llm_explanation(profile: Dict, recommendations: List[dict]) -> str:
    """
    Injects matches into RECOMMENDER_PROMPT, firing it off to the
    centralized Azure OpenAI deployment configuration.
    """
    # Stringify the recommended candidate subset cleanly
    candidates_str = "\n".join([f"- {c.get('name')} ({c.get('code')})" for c in recommendations])
    
    # Your exact requested system prompt injection template
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

    formatted_prompt = RECOMMENDER_PROMPT.format(
        education_level=profile.get("education_level"),
        interests=", ".join(profile.get("interests", [])),
        career_goal=profile.get("career_goal", "Not specified"),
        candidates=candidates_str
    )

    try:
        response = client.chat.completions.create(
            model=os.getenv("CHAT_DEPLOYMENT"), 
            messages=[{"role": "user", "content": formatted_prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Automated counseling narrative generation unserviceable. (Error: {str(e)})"

def recommend_courses(profile: Dict) -> Dict:
    """
    Main pipeline orchestration controller managing system-wide structural data flow.
    """
    # 1. Fetch real master course definitions from courses.json
    master_courses = load_master_courses_database()
    
    # 2. Get eligible levels based on background
    eligible_levels = get_eligible_levels(profile.get("education_level"))
    
    # 3. Query: find_courses engine and score results
    top_3_recommendations = score_and_rank_courses(
        master_courses=master_courses,
        eligible_levels=eligible_levels,
        interests=profile.get("interests", [])
    )

    if not top_3_recommendations:
        return {
            "recommendations": [],
            "explanation": "No matching courses found matching your criteria at this time."
        }

    # 4. Generate the personalized warm counseling text
    explanation = generate_llm_explanation(profile, top_3_recommendations)

    return {
        "recommendations": top_3_recommendations,
        "explanation": explanation
    }


if __name__ == "__main__":
    # Test execution suite using real mapping criteria
    test_profiles = [
        {
            "education_level": "school_passout", 
            "interests": ["computers", "data"], 
            "career_goal": None
        },
        {
            "education_level": "graduate", 
            "interests": ["leadership", "business"], 
            "career_goal": "become a product manager"
        },
        {
            "education_level": "school_passout", 
            "interests": ["helping people"], 
            "career_goal": "work in hospitals"
        },
    ]
    
    print("================================================================")
    print("      LAUNCHING RECOMENDER STANDALONE VERIFICATION SUITE        ")
    print("================================================================\n")
    
    for idx, profile in enumerate(test_profiles, 1):
        print(f"--- PROFILE #{idx} ---")
        print(f"Education Level : {profile['education_level']}")
        print(f"Interests       : {profile['interests']}")
        print(f"Career Goal     : {profile['career_goal']}")
        print("-" * 40)
        
        # Run the profile through your real orchestration engine
        result = recommend_courses(profile)
        
        # Display the structured list of recommended courses found
        print("Recommended Courses:")
        if result["recommendations"]:
            for course in result["recommendations"]:
                print(f"  → [{course.get('code')}] {course.get('name')} ({course.get('level').upper()})")
        else:
            print("  → No explicit matches found for these interest tags.")
            
        # Display the warm, personalized explanation from the Azure OpenAI LLM
        print("\nAdvisor's Personalized Recommendation:")
        print(result["explanation"])
        print("=" * 64 + "\n")