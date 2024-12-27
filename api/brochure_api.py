from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import logging
from pathlib import Path
import time
from typing import Optional
import json

# Add the parent directory to sys.path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from models.generate_single_page_brochure import SinglePageBrochureGenerator
from api.models import BrochureRequest, BrochureResponse, ErrorResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Brochure Generation API",
    description="API for generating hotel brochures using AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store background tasks status
tasks_status = {}

def generate_brochure_task(task_id: str, request: BrochureRequest):
    try:
        logger.info(f"Starting brochure generation task {task_id} for {request.hotel_name}")
        tasks_status[task_id] = {"status": "processing", "message": "Generating brochure..."}
        
        # Initialize the brochure generator
        generator = SinglePageBrochureGenerator(
            hotel_name=request.hotel_name,
            location=request.location,
            layout=request.layout
        )
        
        # Generate the brochure
        generator.generate_brochure()
        
        # Update task status
        brochure_filename = f"{request.hotel_name}_full_bleed_brochure.png"
        brochure_path = os.path.join("generated_brochures", brochure_filename)
        
        if os.path.exists(brochure_path):
            tasks_status[task_id] = {
                "status": "completed",
                "message": "Brochure generated successfully",
                "file_path": brochure_path
            }
        else:
            tasks_status[task_id] = {
                "status": "failed",
                "message": "Failed to generate brochure"
            }
            
    except Exception as e:
        logger.error(f"Error in task {task_id}: {str(e)}")
        tasks_status[task_id] = {
            "status": "failed",
            "message": str(e)
        }

@app.post("/generate-brochure")
async def generate_brochure(request: BrochureRequest, background_tasks: BackgroundTasks):
    try:
        # Generate unique task ID
        task_id = f"task_{int(time.time())}"
        
        # Add task to background tasks
        background_tasks.add_task(generate_brochure_task, task_id, request)
        
        return JSONResponse({
            "status": "processing",
            "message": f"Brochure generation started. Check status at /task-status/{task_id}",
            "task_id": task_id
        })
        
    except Exception as e:
        logger.error(f"Error in generate_brochure: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in tasks_status:
        raise HTTPException(status_code=404, detail="Task not found")
    return JSONResponse(tasks_status[task_id])

@app.get("/download-brochure/{file_path:path}")
async def download_brochure(file_path: str):
    try:
        # Ensure the file path is within the generated_brochures directory
        full_path = os.path.join(parent_dir, file_path)
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="Brochure not found")
            
        return FileResponse(
            full_path,
            media_type="application/octet-stream",
            filename=os.path.basename(file_path)
        )
    except Exception as e:
        logger.error(f"Error in download_brochure: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8006)
