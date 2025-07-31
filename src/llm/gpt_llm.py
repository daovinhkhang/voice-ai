import asyncio
import logging
from typing import List, Dict, Optional
from openai import OpenAI
from src.utils.config import config

logger = logging.getLogger(__name__)

class GPTLLM:
    """Language Model using OpenAI GPT-3.5 Turbo for Vietnamese conversation"""
    
    def __init__(self):
        """Initialize GPT LLM client"""
        config.validate()
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.LLM_MODEL
        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt = self._get_system_prompt()
        logger.info(f"Initialized GPTLLM with model: {self.model}")
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for Vietnamese AI assistant"""
        return """Bạn là một trợ lý AI thông minh và thân thiện, có thể nói chuyện bằng tiếng Việt một cách tự nhiên. 
        
Hãy tuân thủ các nguyên tắc sau:
1. Luôn trả lời bằng tiếng Việt
2. Giữ câu trả lời ngắn gọn, súc tích (tối đa 2-3 câu)
3. Sử dụng ngôn ngữ thân thiện, gần gũi
4. Tránh sử dụng các từ khó hiểu hoặc thuật ngữ phức tạp
5. Nếu không hiểu câu hỏi, hãy lịch sự yêu cầu người dùng nói rõ hơn
6. Luôn giữ thái độ tích cực và hữu ích

Hãy trả lời một cách tự nhiên như đang nói chuyện trực tiếp với người dùng."""
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({"role": role, "content": content})
        
        # Keep only last 10 messages to avoid token limit
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    async def generate_response(self, user_input: str) -> Optional[str]:
        """
        Generate response to user input using GPT-3.5 Turbo
        
        Args:
            user_input: User's text input in Vietnamese
            
        Returns:
            AI response text or None if failed
        """
        try:
            # Add user input to history
            self.add_to_history("user", user_input)
            
            # Prepare messages for API
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self.conversation_history)
            
            # Call GPT API
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                max_tokens=150,  # Keep responses short for voice chat
                temperature=0.7,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            # Extract response text
            if response.choices and len(response.choices) > 0:
                ai_response = response.choices[0].message.content.strip()
                
                if ai_response:
                    # Add AI response to history
                    self.add_to_history("assistant", ai_response)
                    logger.info(f"Generated response: {ai_response}")
                    return ai_response
                else:
                    logger.warning("Empty response from GPT")
                    return None
            else:
                logger.warning("No choices in GPT response")
                return None
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None
    
    async def generate_response_stream(self, user_input: str):
        """
        Generate streaming response (for future real-time implementation)
        
        Args:
            user_input: User's text input in Vietnamese
            
        Yields:
            Chunks of AI response text
        """
        try:
            # Add user input to history
            self.add_to_history("user", user_input)
            
            # Prepare messages for API
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self.conversation_history)
            
            # Call GPT API with streaming
            stream = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                max_tokens=150,
                temperature=0.7,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1,
                stream=True
            )
            
            full_response = ""
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content = delta.content
                        full_response += content
                        yield content
            
            # Add complete response to history
            if full_response:
                self.add_to_history("assistant", full_response)
                logger.info(f"Generated streaming response: {full_response}")
                
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            yield None
