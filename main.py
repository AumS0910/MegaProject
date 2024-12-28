from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from models.generate_single_page_brochure import SinglePageBrochureGenerator

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the generated_images directory
app.mount("/images", StaticFiles(directory="generated_images"), name="images")

class BrochureRequest(BaseModel):
    prompt: str

@app.post("/generate-brochure-from-prompt")
async def generate_brochure(request: BrochureRequest):
    try:
        # Extract hotel name and location from prompt
        prompt_parts = request.prompt.split(",", 1)
        if len(prompt_parts) < 2:
            raise HTTPException(status_code=400, detail="Prompt must include hotel name and location separated by comma")
        
        hotel_name = prompt_parts[0].strip()
        location = prompt_parts[1].split(",")[0].strip()
        
        # Generate brochure
        generator = SinglePageBrochureGenerator(hotel_name, location)
        
        # Generate images first
        generator.generate_images()
        
        # Generate the brochure
        brochure_path = generator.generate_brochure()
        
        # Get image paths
        image_paths = {
            "exterior": f"/images/{hotel_name.replace(' ', '_')}_exterior.png",
            "room": f"/images/{hotel_name.replace(' ', '_')}_room.png",
            "restaurant": f"/images/{hotel_name.replace(' ', '_')}_restaurant.png"
        }
        
        return {
            "status": "completed",
            "brochure_path": brochure_path,
            "images": image_paths
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
