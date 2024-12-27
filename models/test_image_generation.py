import requests
import json
import base64
from PIL import Image
import io
import os

def test_image_generation(hotel_name="Sunset Bay Resort", location="Maldives", custom_prompts=None):
    # The correct endpoint for Stable Diffusion WebUI API
    url = "http://127.0.0.1:7860/sdapi/v1/txt2img"
    
    # Create output directory if it doesn't exist
    output_dir = "generated_images"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Default prompts
    default_prompts = [
        {
            "name": "exterior",
            "prompt": f"Professional architectural photography of {hotel_name} in {location}, luxury resort exterior, beachfront, palm trees, sunset, high-end hotel photography, 4k, detailed, professional lighting"
        },
        {
            "name": "room",
            "prompt": f"Interior photography of a luxury suite at {hotel_name}, elegant hotel room, ocean view, king size bed, modern furniture, ambient lighting, professional hotel photography, 4k, detailed"
        },
        {
            "name": "restaurant",
            "prompt": f"Elegant restaurant interior at {hotel_name}, luxury dining area, ocean view, fine dining setup, warm lighting, professional restaurant photography, 4k, detailed"
        }
    ]
    
    # Use custom prompts if provided
    if custom_prompts:
        prompts = [
            {"name": "exterior", "prompt": custom_prompts.get("exterior", default_prompts[0]["prompt"])},
            {"name": "room", "prompt": custom_prompts.get("room", default_prompts[1]["prompt"])},
            {"name": "restaurant", "prompt": custom_prompts.get("restaurant", default_prompts[2]["prompt"])}
        ]
    else:
        prompts = default_prompts
    
    for prompt_data in prompts:
        print(f"\n=== Generating {prompt_data['name']} image ===")
        print(f"Prompt: {prompt_data['prompt']}")
        
        payload = {
            "prompt": prompt_data["prompt"],
            "negative_prompt": "low quality, blurry, distorted, ugly, bad anatomy, bad proportions, deformed",
            "steps": 20,
            "width": 768,
            "height": 512,
            "cfg_scale": 7.0,
            "sampler_name": "Euler a",
            "batch_size": 1
        }
        
        try:
            print("Sending request to Stable Diffusion...")
            response = requests.post(url=url, json=payload)
            print(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                r = response.json()
                print("Successfully received response")
                
                # Save each generated image
                for i, image_b64 in enumerate(r['images']):
                    image = Image.open(io.BytesIO(base64.b64decode(image_b64.split(",", 1)[0] if "," in image_b64 else image_b64)))
                    
                    # Save the image
                    filename = f"{output_dir}/{hotel_name}_{prompt_data['name']}.png"
                    image.save(filename)
                    print(f"Generated {prompt_data['name']} image saved as: {filename}")
            else:
                print(f"Error: Received status code {response.status_code}")
                print("Response content:", response.text)
                
        except Exception as e:
            print(f"Error generating {prompt_data['name']} image: {str(e)}")
            print("Full error details:", str(e))

if __name__ == "__main__":
    print("Starting image generation test...")
    print("Checking if Stable Diffusion API is accessible...")
    try:
        response = requests.get("http://127.0.0.1:7860/sdapi/v1/sd-models")
        if response.status_code == 200:
            print("Successfully connected to Stable Diffusion API")
        else:
            print(f"Warning: Could not get models list. Status code: {response.status_code}")
    except Exception as e:
        print(f"Warning: Could not connect to Stable Diffusion API: {str(e)}")
    
    # Test with a specific hotel
    test_image_generation(
        hotel_name="Ocean Paradise Resort",
        location="Maldives"
    )
