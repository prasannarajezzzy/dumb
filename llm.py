from loguru import logger
from ollama import chat

# Simple in-memory cache
cache = {}

async def get_llm_response(prompt: str) -> str:
    try:
        # Check cache first
        if prompt in cache:
            logger.info(f"Cache hit for prompt: {prompt}")
            return cache[prompt]

        logger.info(f"Generating LLM response for prompt: {prompt}")
        
        # Direct asynchronous LLM call (if supported by `chat`)
        response = chat(model='llama3.2', messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ])
        generated_text = response['message']['content']
        
        # Cache the response
        cache[prompt] = generated_text

        logger.info(f"LLM response: {generated_text}")
        return generated_text
    except Exception as e:
        logger.error(f"LLM API Error: {e}")
        raise Exception("Failed to get response from LLM.")
