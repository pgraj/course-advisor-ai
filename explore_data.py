from pathlib import Path
from collections import Counter

import json

# Define the path to the JSON file relative to this script
json_path = Path(__file__).parent / "data" / "courses" / "courses.json"

# Open and load the JSON file
with open(json_path, "r", encoding="utf-8") as f:
    courses_data = json.load(f)

courses_data["institute"]   # dict with the institute info
courses_data["courses"]  

# the list of 18 course dicts ← what you want
courses = courses_data["courses"]
levels = {}
stream = {}
postgraduate = {}



def find_courses(courses, level=None, stream=None, interest=None):
    filtered_list = []
    
    for c in courses:
        if level is not None and c.get("level")!= level:
            continue
        if stream is not None and c.get("stream") != stream:
            continue
        
        
        if interest is not None:
            interest_lower = interest.lower()
            if not any(interest_lower in i.lower() for i in c.get("interests", [])):
                continue
        
        filtered_list.append(c)
    
    return (filtered_list)

if __name__ == "__main__":
    # These calculations and prints will ONLY run when executing this file directly.
    # They are completely skipped when recommender.py imports find_courses!
    
    print("Total courses:", len(courses))

    levels = {}
    for c in courses:
        levels[c["level"]] = levels.get(c["level"], 0) + 1

    stream = Counter(c["stream"] for c in courses)
    print("By level:", levels)
    print("By stream:", stream)

    print("\n--- Running find_courses Verification Tests ---")

    print([c["name"] for c in find_courses(courses, level="diploma")])
    print([c["name"] for c in find_courses(courses, stream="Health")])
    print([c["name"] for c in find_courses(courses, level="postgraduate", interest="leadership")])