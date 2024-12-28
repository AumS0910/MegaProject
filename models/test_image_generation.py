import requests
import base64
import io
from PIL import Image
import os
import json

def test_image_generation(hotel_name="Sunset Bay Resort", location="Maldives", custom_prompts=None):
    """Generate images using Stable Diffusion API"""
    print("\n=== test_image_generation ===")
    print(f"Hotel name: {hotel_name}")
    print(f"Location: {location}")
    
    try:
        # Create output directory if it doesn't exist
        output_dir = "generated_images"
        os.makedirs(output_dir, exist_ok=True)
        print(f"Created/verified output directory: {output_dir}")
        print(f"Directory contents before generation:")
        for f in os.listdir(output_dir):
            if hotel_name.replace(' ', '_') in f:
                print(f"  {f}")

        # Define prompts
        prompts = [
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
        print(f"Using prompts: {json.dumps(prompts, indent=2)}")

        # Track generated images
        generated_images = []
        failed_images = []

        # Generate each image
        for prompt_data in prompts:
            try:
                print(f"\nGenerating {prompt_data['name']} image...")
                
                # Prepare the request
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

                # Make the API request
                response = requests.post(
                    url="http://127.0.0.1:7860/sdapi/v1/txt2img",
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                )

                # Check if request was successful
                if response.status_code != 200:
                    print(f"Error: Received status code {response.status_code}")
                    failed_images.append(prompt_data['name'])
                    continue

                # Get the image data
                response_data = response.json()
                if 'images' not in response_data or not response_data['images']:
                    print("No images in response")
                    failed_images.append(prompt_data['name'])
                    continue

                # Process the first image
                image_data = response_data['images'][0]
                if ',' in image_data:  # Remove data URL prefix if present
                    image_data = image_data.split(',', 1)[1]

                # Convert base64 to image
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))

                # Save the image with consistent path separator and name
                safe_hotel_name = hotel_name.replace(' ', '_')
                filename = os.path.join(output_dir, f"{safe_hotel_name}_{prompt_data['name']}.png").replace('\\', '/')
                print(f"Saving image to: {filename}")
                image.save(filename)
                print(f"Successfully saved {prompt_data['name']} image to {filename}")
                print(f"File exists after save: {os.path.exists(filename)}")
                print(f"File size: {os.path.getsize(filename)} bytes")
                generated_images.append(filename)

            except Exception as e:
                print(f"Error generating {prompt_data['name']}: {str(e)}")
                failed_images.append(prompt_data['name'])

        # Check directory contents after generation
        print(f"\nDirectory contents after generation:")
        for f in os.listdir(output_dir):
            if hotel_name.replace(' ', '_') in f:
                print(f"  {f}")

        # Check if all images were generated
        if failed_images:
            error_msg = f"Failed to generate images: {', '.join(failed_images)}"
            print(error_msg)
            return False
        
        print(f"Successfully generated all images: {', '.join(generated_images)}")
        return True

    except Exception as e:
        print(f"Error in image generation: {str(e)}")
        return False

if __name__ == "__main__":
    # Test the function
    test_image_generation("Test Hotel", "Test Location")
