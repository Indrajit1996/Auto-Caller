import openai
import logging
from app.core.config import config
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.OPENAI_CONVERSATION_API_KEY)
        self.model = config.OPENAI_CONVERSATION_MODEL or "gpt-3.5-turbo"
        
        if not config.OPENAI_CONVERSATION_API_KEY:
            logger.error("OPENAI_CONVERSATION_API_KEY not found in environment variables")
            raise ValueError("OPENAI_CONVERSATION_API_KEY not found in environment variables")
    
    async def generate_conversation_response(
        self, 
        conversation_history: List[Dict], 
        user_input: str,
        max_tokens: int = 150
    ) -> Optional[str]:
        """
        Generate intelligent follow-up questions based on conversation context.
        Adapted from user's existing implementation pattern.
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": """You are a caring AI friend who checks in on the user. Your role is to:
                    - Show genuine interest in how they are feeling
                    - Ask thoughtful follow-up questions about their well-being
                    - Provide emotional support and empathy
                    - Keep the conversation focused on their feelings, mood, and general well-being
                    - Do NOT offer to help with tasks, set reminders, make calls, or provide other assistance
                    - Keep responses conversational and natural, like a caring friend
                    - If they mention being stressed, sad, or having problems, show empathy and ask how you can support them emotionally
                    - If they mention being happy or doing well, celebrate with them and ask what's contributing to their positive mood
                    - Keep responses under 50 words and conversational"""
                }
            ]
            
            # Add conversation history (last 5 interactions for context)
            for interaction in conversation_history[-5:]:
                if interaction.get('transcript'):
                    messages.append({
                        "role": "user",
                        "content": interaction['transcript']
                    })
                    if interaction.get('system_response'):
                        messages.append({
                            "role": "assistant", 
                            "content": interaction['system_response']
                        })
            
            # Add current user input
            messages.append({
                "role": "user",
                "content": user_input
            })
            
            # Generate response using OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
                n=1,
                stop=None,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            assistant_message = response.choices[0].message.content if response.choices[0].message else "I didn't understand that. Could you please repeat?"
            
            # Log response for debugging
            logger.info(f"OpenAI Response Length: {len(assistant_message)}")
            logger.info(f"OpenAI Response Preview: {assistant_message[:200]}")
            
            return assistant_message.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return "That's interesting! Tell me more about that."
    
    async def generate_final_response(self, user_input: str, max_tokens: int = 100) -> Optional[str]:
        """
        Generate a final response without asking questions - just acknowledge and respond.
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": """You are a caring AI friend who is ending a conversation. Your role is to:
                    - Acknowledge what the user just said
                    - Show empathy and understanding
                    - Provide a brief, supportive response
                    - CRITICAL: DO NOT ask any questions whatsoever
                    - CRITICAL: DO NOT use question marks (?)
                    - CRITICAL: DO NOT use words like how, what, when, where, why, who, which
                    - CRITICAL: DO NOT use phrases like "do you", "are you", "can you", "would you", "could you", "will you", "have you", "did you"
                    - Keep responses under 25 words
                    - Be warm and caring but don't continue the conversation
                    - Just acknowledge and respond with statements only
                    - Use only declarative sentences, never interrogative sentences"""
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ]
            
            # Generate response using OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
                n=1,
                stop=None,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            assistant_message = response.choices[0].message.content if response.choices[0].message else "Thank you for sharing that with me."
            
            # Log response for debugging
            logger.info(f"OpenAI Final Response: {assistant_message}")
            
            return assistant_message.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error in final response: {e}")
            return "Thank you for sharing that with me."
    
    async def generate_contextual_response(
        self, 
        user_input: str, 
        context: str = "",
        max_tokens: int = 200
    ) -> Optional[str]:
        """
        Generate response with optional context (like resume context in user's example).
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"You are an intelligent phone assistant. {context}"
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI contextual response error: {e}")
            return "I'm sorry, I didn't understand that. Could you please repeat?" 