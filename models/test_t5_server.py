import requests
import json
import time
from collections import deque

# Rate limiting setup
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds
MAX_REQUESTS_PER_WINDOW = 100
request_timestamps = deque()

def check_rate_limit():
    current_time = time.time()
    # Remove timestamps older than the window
    while request_timestamps and current_time - request_timestamps[0] > RATE_LIMIT_WINDOW:
        request_timestamps.popleft()
    
    if len(request_timestamps) >= MAX_REQUESTS_PER_WINDOW:
        time_until_next = request_timestamps[0] + RATE_LIMIT_WINDOW - current_time
        raise Exception(f"Rate limit exceeded. Please try again in {int(time_until_next)} seconds")
    
    request_timestamps.append(current_time)

def test_hotel_description(hotel_name="Sunset Bay Resort", restaurant_name="The Ocean Grill"):
    url = "http://localhost:8003/generate"  # Updated port to 8003
    
    prompts = [
        {
            "section": "Hotel Overview",
            "prompt": f"Generate a detailed luxury hotel description highlighting elegance and service: {hotel_name} is an exquisite"
        },
        {
            "section": "Restaurant",
            "prompt": f"Generate a fine dining restaurant description with cuisine style and atmosphere: {restaurant_name} at {hotel_name} enchants guests with"
        },
        {
            "section": "Amenities",
            "prompt": f"List premium hotel amenities and facilities with elegant descriptions: {hotel_name} pampers guests with"
        },
        {
            "section": "Location",
            "prompt": f"Describe the prime location and surroundings of this luxury hotel: {hotel_name} is perfectly positioned"
        }
    ]
    
    for section in prompts:
        print(f"\n=== Generating {section['section']} ===")
        try:
            # Check rate limit before making request
            check_rate_limit()
            
            data = {
                "prompt": section['prompt'],
                "max_length": 150,  # Increased length for more detailed descriptions
                "temperature": 0.8,  # Slightly higher temperature for more creative output
                "top_p": 0.95
            }
            
            response = requests.post(url, json=data)
            if response.status_code == 429:  # Rate limit error
                error_data = response.json()
                print(f"Rate limit error: {error_data.get('detail', 'Too many requests')}")
                # Wait for a bit before retrying
                time.sleep(5)
                continue
                
            if response.status_code == 200:
                result = response.json()
                print("\nGenerated Text:")
                print(result["generated_text"])
                print("\n" + "="*50)
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"Error: {str(e)}")
            # If it's a rate limit error, wait before continuing
            if "Rate limit exceeded" in str(e):
                print("Waiting before next request...")
                time.sleep(5)

def test_amenities_generation():
    # Test hotel details
    hotel_name = "Desert Rose Palace"
    location = "Dubai"
    
    # Create the amenities prompt
    prompt = f"Generate 6 ultra-luxury amenities for {hotel_name} in {location}. Focus on unique, exclusive features that match the desert location and modern luxury experience. Each amenity should be extraordinary and specific to a luxury desert resort. Format: 1. [amenity]. 2. [amenity]. etc."
    
    # Sample amenities for testing
    generated_text = """1. Private Desert Safari with Luxury 4x4 Fleet
2. Rooftop Infinity Pool with Dubai Skyline Views
3. Royal Desert Spa with Gold-Infused Treatments
4. Personal Butler and Luxury Shopping Concierge
5. Private Helipad with City Tour Service
6. Michelin-Star Arabic Fusion Restaurant"""
    
    print("\nGenerated Amenities for Desert Rose Palace, Dubai:")
    print("-" * 50)
    
    # Process the amenities
    amenities = []
    for amenity in generated_text.split("\n"):
        # Clean up the amenity text
        clean_amenity = amenity.strip()
        # Remove leading numbers and dots
        clean_amenity = ' '.join(clean_amenity.split()[1:]) if clean_amenity and clean_amenity[0].isdigit() else clean_amenity
        if clean_amenity:
            amenities.append(clean_amenity)
            print(f"* {clean_amenity}")
    
    return amenities

if __name__ == "__main__":
    test_amenities_generation()
