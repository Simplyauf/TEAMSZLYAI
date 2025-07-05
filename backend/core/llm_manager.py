"""
LLM Manager using Ollama for LLaMA
Handles text generation and chat completions
"""

import httpx
import json
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
import asyncio

from .config import settings

logger = logging.getLogger(__name__)


class LLMManager:
    """Manages LLM interactions using Ollama"""

    def __init__(self):
        self.base_url = settings.ollama_url
        self.model = settings.ollama_model
        self.client = httpx.AsyncClient(timeout=60.0)

    async def initialize(self):
        """Initialize LLM and ensure model is available"""
        try:
            # Check if Ollama is running
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                raise Exception(f"Ollama not accessible: {response.status_code}")

            # Check if our model is available
            models = response.json()
            available_models = [model["name"] for model in models.get("models", [])]

            if self.model not in available_models:
                logger.info(f"Model {self.model} not found, pulling...")
                await self._pull_model()

            logger.info(f"LLM Manager initialized with model: {self.model}")

        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}")
            raise

    async def _pull_model(self):
        """Pull the model if it's not available"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model}
            )

            if response.status_code != 200:
                raise Exception(f"Failed to pull model: {response.status_code}")

            logger.info(f"Successfully pulled model: {self.model}")

        except Exception as e:
            logger.error(f"Failed to pull model: {str(e)}")
            raise

    async def generate_response(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 1000,
        temperature: float = 0.1
    ) -> str:
        """Generate a response using the LLM"""
        try:
            # Build the full prompt with context
            full_prompt = self._build_prompt(prompt, context)

            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature,
                        "top_p": 0.9,
                        "stop": ["Human:", "Assistant:"]
                    }
                }
            )

            if response.status_code != 200:
                raise Exception(f"LLM request failed: {response.status_code}")

            result = response.json()
            return result.get("response", "").strip()

        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            raise

    def _build_prompt(self, question: str, context: Optional[List[Dict[str, str]]] = None) -> str:
        """Build a prompt with context for RAG"""
        if not context:
            return f"""You are a helpful AI assistant. Answer the following question clearly and concisely.

Question: {question}

Answer:"""

        # Build context from retrieved documents
        context_text = ""
        for i, doc in enumerate(context, 1):
            source_info = f"[Source: {doc.get('source', 'unknown')}"
            if doc.get('channel'):
                source_info += f" - {doc['channel']}"
            if doc.get('author'):
                source_info += f" by {doc['author']}"
            source_info += "]"

            context_text += f"\n{i}. {source_info}\n{doc.get('content', '')}\n"

        return f"""You are a helpful AI assistant with access to a knowledge base. Use the provided context to answer the question. If the context doesn't contain enough information to answer the question, say so clearly.

Context:
{context_text}

Question: {question}

Answer based on the context above:"""

    async def health_check(self) -> bool:
        """Check if LLM is healthy"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False