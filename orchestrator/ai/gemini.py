"""Gemini AI integration."""

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from orchestrator.config import get_settings
from orchestrator.utils.logging import logger
import asyncio
from typing import List, Dict, Any, Optional
import json

class GeminiClient:
    """Wrapper for Google Gemini models."""
    
    def __init__(self):
        self.settings = get_settings()
        self._configured = False
        self._model = None
        self._flash_model = None
        
    def configure(self):
        """Configure the Gemini API."""
        if self._configured:
            return
            
        if not self.settings.google_api_key or self.settings.google_api_key == "dummy_key_replace_me":
            logger.warning("Google API Key not set. AI features will fail.")
            return

        genai.configure(api_key=self.settings.google_api_key)
        
        # Configure safety settings (block only high probability)
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }
        
        # Initialize models
        self._model = genai.GenerativeModel(self.settings.orchestrator_model)  # Pro model for synthesis
        self._flash_model = genai.GenerativeModel(self.settings.gemini_model)  # Flash model for agents
        
        self._configured = True
        logger.info(f"Gemini initialized. Pro: {self.settings.orchestrator_model}, Flash: {self.settings.gemini_model}")

    async def generate_response(
        self, 
        prompt: str, 
        system_instruction: str = None,
        use_flash: bool = False,
        json_mode: bool = False
    ) -> str:
        """Generate a response from Gemini."""
        if not self._configured:
            self.configure()
            
        model = self._flash_model if use_flash else self._model
        
        # Add system instruction to prompt if provided (Gemini Python SDK handles system prompts differently based on version,
        # but prepending is a safe fallback)
        full_prompt = prompt
        if system_instruction:
            # For models that support system_instruction arg, we'd use it in init. 
            # Here we prepend for compatibility.
            full_prompt = f"System Instruction: {system_instruction}\n\nUser Request: {prompt}"
            
        generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            candidate_count=1,
            response_mime_type="application/json" if json_mode else "text/plain"
        )

        try:
            # Async generation
            response = await model.generate_content_async(
                full_prompt, 
                generation_config=generation_config,
                safety_settings=self.safety_settings
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise

    async def plan_mission(self, query: str, available_agents: List[Dict]) -> List[str]:
        """
        Decide which agents to recruit for a task.
        Returns a list of agent IDs.
        """
        agents_desc = "\n".join([f"- {a['id']}: {a['role']} (Tools: {a['tools']})" for a in available_agents])
        
        prompt = f"""
        You are the Hive Mind Orchestrator. Your goal is to select the best agents to answer a user query.
        
        User Query: "{query}"
        
        Available Agents:
        {agents_desc}
        
        Select 1-5 agents that are strictly necessary. 
        Return ONLY a JSON array of agent IDs. Example: ["res_01_web", "res_02_code"]
        """
        
        try:
            response_text = await self.generate_response(prompt, use_flash=True, json_mode=True)
            agent_ids = json.loads(response_text)
            
            # Validate IDs
            valid_ids = {a['id'] for a in available_agents}
            selected = [aid for aid in agent_ids if aid in valid_ids]
            
            # Fallback if empty or invalid
            if not selected:
                logger.warning("Gemini returned no valid agents, defaulting to Web Scout")
                return ["res_01_web"]
                
            return selected
        except Exception as e:
            logger.error(f"Mission planning failed: {e}")
            # Fallback
            return ["res_01_web"]

    async def synthesize_results(self, query: str, agent_results: List[Dict]) -> str:
        """Synthesize multiple agent outputs into a cohesive answer."""
        
        results_text = ""
        for res in agent_results:
            agent_name = res.get('agent', 'Unknown Agent')
            summary = res.get('summary', 'No summary')
            # Extract detailed result if available, otherwise use summary
            details = str(res.get('result', ''))[:500]  # Truncate for context window
            
            results_text += f"\n--- Report from {agent_name} ---\n{summary}\nDetails: {details}\n"
            
        prompt = f"""
        You are the Hive Mind. A user asked a question, and your specialized agents have gathered information.
        Synthesize their reports into a single, comprehensive, high-quality answer.
        
        User Query: "{query}"
        
        Agent Reports:
        {results_text}
        
        Instructions:
        1. Answer the user's question directly.
        2. Resolve conflicting information if any.
        3. Cite the specific agent (e.g., "According to Code Hunter...") when referencing specific data.
        4. Be professional and concise.
        """
        
        return await self.generate_response(prompt, use_flash=False)

# Global instance
gemini_client = GeminiClient()
