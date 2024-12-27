from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch
import time
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Rate limiting configuration
RATE_LIMIT_WINDOW = 60  # 1 minute in seconds
MAX_REQUESTS_PER_WINDOW = 10  # Allow 10 requests per minute
request_timestamps = []

class GenerationRequest(BaseModel):
    prompt: str
    max_length: Optional[int] = 100
    temperature: Optional[float] = 0.6
    top_p: Optional[float] = 0.8

def check_rate_limit():
    current_time = time.time()
    # Remove timestamps older than the window
    while request_timestamps and current_time - request_timestamps[0] > RATE_LIMIT_WINDOW:
        request_timestamps.pop(0)
    
    if len(request_timestamps) >= MAX_REQUESTS_PER_WINDOW:
        time_until_next = request_timestamps[0] + RATE_LIMIT_WINDOW - current_time
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Please try again in {int(time_until_next)} seconds"
        )
    
    request_timestamps.append(current_time)

def load_model():
    try:
        logger.info("Loading model and tokenizer...")
        model_path = "D:/MegaProject/Text/flan-t5-base"
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
        logger.info("Model and tokenizer loaded successfully")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise

model, tokenizer = load_model()

@app.post("/generate")
async def generate_text(request: GenerationRequest):
    try:
        # Check rate limit
        check_rate_limit()
        
        # Process the prompt to handle bullet points
        processed_prompt = request.prompt.replace('\n', ' ').replace('- ', ', ').strip()
        
        # Tokenize and generate
        inputs = tokenizer(processed_prompt, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=request.max_length,
                temperature=request.temperature,
                top_p=request.top_p,
                num_return_sequences=1,
                do_sample=True,  # Enable sampling
                no_repeat_ngram_size=3,  # Avoid repetition
                length_penalty=1.5  # Encourage longer responses
            )
        
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Post-process the generated text
        generated_text = generated_text.replace(" .", ".").replace(" ,", ",")
        generated_text = " ".join(generated_text.split())  # Clean up whitespace
        
        return {"generated_text": generated_text}
    
    except HTTPException as he:
        # Re-raise HTTP exceptions (like rate limit)
        raise
    except Exception as e:
        logger.error(f"Error during text generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Text generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8005)