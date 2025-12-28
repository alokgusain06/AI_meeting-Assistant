"""LLM-powered reasoning engine for meeting insights using Google Gemini."""
import asyncio
from typing import AsyncGenerator, Optional
import google.generativeai as genai
from config.settings import settings


class MeetingReasoner:
    """Uses Gemini to generate meeting insights, summaries, and answer questions."""
    
    SYSTEM_PROMPT = """You are an AI meeting assistant. Your role is to:
1. Provide clear, concise summaries of meeting discussions
2. Identify key decisions, action items, and important points
3. Answer questions about what has been discussed
4. Track topics and themes being discussed

When summarizing, be concise but comprehensive. Use bullet points for clarity.
When answering questions, base your response ONLY on the provided conversation context.
If you don't have enough context to answer, say so clearly.

Format action items as: "- [ ] Action: [description] (Owner: [name if mentioned])"
Format decisions as: "- Decision: [what was decided]"
"""

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=self.SYSTEM_PROMPT
        )
        self._last_summary: str = ""
        self._summary_lock = asyncio.Lock()
    
    async def generate_summary(self, conversation_context: str) -> str:
        """Generate a summary of the current conversation."""
        if not conversation_context.strip():
            return "No conversation yet."
        
        prompt = f"""Based on the following meeting conversation, provide a concise summary.
Include:
- Main topics discussed
- Key decisions made (if any)
- Action items identified (if any)
- Current discussion focus

Conversation:
{conversation_context}

Summary:"""

        try:
            # Run synchronous Gemini call in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            summary = response.text or "Unable to generate summary."
            
            async with self._summary_lock:
                self._last_summary = summary
            
            return summary
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    async def answer_question(self, question: str, conversation_context: str) -> str:
        """Answer a question about the meeting conversation."""
        if not conversation_context.strip():
            return "There's no conversation context yet. Please wait for some discussion to happen."
        
        prompt = f"""Based on the following meeting conversation, answer this question:
Question: {question}

Conversation:
{conversation_context}

Provide a clear, direct answer based only on the conversation above. If the answer isn't in the conversation, say so."""

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            return response.text or "Unable to answer."
        except Exception as e:
            return f"Error answering question: {str(e)}"
    
    async def stream_answer(self, question: str, conversation_context: str) -> AsyncGenerator[str, None]:
        """Stream an answer for lower perceived latency."""
        if not conversation_context.strip():
            yield "There's no conversation context yet."
            return
        
        prompt = f"""Based on the following meeting conversation, answer this question:
Question: {question}

Conversation:
{conversation_context}

Answer:"""

        try:
            # Gemini streaming
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt, stream=True)
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"Error: {str(e)}"
    
    async def identify_current_topic(self, conversation_context: str) -> str:
        """Identify what topic is currently being discussed."""
        if not conversation_context.strip():
            return "No active discussion."
        
        # Use last ~1000 chars for current topic detection
        recent_context = conversation_context[-1000:] if len(conversation_context) > 1000 else conversation_context
        
        prompt = f"""What topic is currently being discussed in this conversation? 
Be brief - respond with just the topic in 1-2 sentences.

Recent conversation:
{recent_context}

Current topic:"""

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            return response.text or "Unable to identify topic."
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def get_last_summary(self) -> str:
        """Get the most recently generated summary."""
        async with self._summary_lock:
            return self._last_summary if self._last_summary else "No summary generated yet."
