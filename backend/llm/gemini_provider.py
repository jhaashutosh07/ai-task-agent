from typing import AsyncGenerator
import json
import google.generativeai as genai
from .base import BaseLLM, Message, ToolDefinition


class GeminiProvider(BaseLLM):
    """Google Gemini LLM provider"""

    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model)

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        stream: bool = False
    ) -> Message | AsyncGenerator[str, None]:
        # Convert messages to Gemini format
        gemini_messages = []
        system_instruction = None

        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            elif msg.role == "user":
                gemini_messages.append({"role": "user", "parts": [msg.content]})
            elif msg.role == "assistant":
                gemini_messages.append({"role": "model", "parts": [msg.content]})
            elif msg.role == "tool":
                # Tool results
                gemini_messages.append({
                    "role": "user",
                    "parts": [{"function_response": {
                        "name": msg.tool_call_id,
                        "response": {"result": msg.content}
                    }}]
                })

        # Create model with system instruction if provided
        if system_instruction:
            model = genai.GenerativeModel(
                self.model_name,
                system_instruction=system_instruction
            )
        else:
            model = self.model

        # Convert tools to Gemini format
        gemini_tools = None
        if tools:
            function_declarations = []
            for tool in tools:
                func_decl = {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": self._convert_parameters(tool.parameters)
                }
                function_declarations.append(func_decl)
            gemini_tools = [genai.protos.Tool(function_declarations=function_declarations)]

        if stream:
            return self._stream_response(model, gemini_messages, gemini_tools)
        else:
            return await self._get_response(model, gemini_messages, gemini_tools)

    def _convert_parameters(self, params: dict) -> dict:
        """Convert JSON Schema to Gemini parameter format"""
        # Gemini uses a similar but slightly different format
        converted = {
            "type": "OBJECT",
            "properties": {},
            "required": params.get("required", [])
        }

        for prop_name, prop_def in params.get("properties", {}).items():
            prop_type = prop_def.get("type", "string").upper()
            if prop_type == "INTEGER":
                prop_type = "NUMBER"
            converted["properties"][prop_name] = {
                "type": prop_type,
                "description": prop_def.get("description", "")
            }

        return converted

    async def _get_response(
        self,
        model: genai.GenerativeModel,
        messages: list[dict],
        tools: list | None
    ) -> Message:
        # Start chat
        chat = model.start_chat(history=messages[:-1] if len(messages) > 1 else [])

        # Get last message
        last_message = messages[-1]["parts"][0] if messages else ""

        # Generate response
        kwargs = {}
        if tools:
            kwargs["tools"] = tools

        response = await chat.send_message_async(last_message, **kwargs)

        # Extract content and function calls
        content = ""
        tool_calls = []

        for part in response.parts:
            if hasattr(part, "text"):
                content = part.text
            elif hasattr(part, "function_call"):
                fc = part.function_call
                tool_calls.append({
                    "id": fc.name,  # Gemini doesn't have separate IDs
                    "type": "function",
                    "function": {
                        "name": fc.name,
                        "arguments": json.dumps(dict(fc.args))
                    }
                })

        return Message(
            role="assistant",
            content=content,
            tool_calls=tool_calls if tool_calls else None
        )

    async def _stream_response(
        self,
        model: genai.GenerativeModel,
        messages: list[dict],
        tools: list | None
    ) -> AsyncGenerator[str, None]:
        chat = model.start_chat(history=messages[:-1] if len(messages) > 1 else [])
        last_message = messages[-1]["parts"][0] if messages else ""

        kwargs = {"stream": True}
        if tools:
            kwargs["tools"] = tools

        response = await chat.send_message_async(last_message, **kwargs)

        async for chunk in response:
            if chunk.text:
                yield chunk.text

    async def chat_with_vision(
        self,
        messages: list[Message],
        images: list[bytes],
        tools: list[ToolDefinition] | None = None
    ) -> Message:
        """Chat with image understanding"""
        import PIL.Image
        import io

        # Build conversation with images
        gemini_messages = []
        system_instruction = None

        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            elif msg.role == "user":
                parts = []
                # Add images
                for img_data in images:
                    img = PIL.Image.open(io.BytesIO(img_data))
                    parts.append(img)
                parts.append(msg.content)
                gemini_messages.append({"role": "user", "parts": parts})
            else:
                gemini_messages.append({"role": "model", "parts": [msg.content]})

        # Use vision model
        vision_model = genai.GenerativeModel(
            "gemini-1.5-pro-vision" if "vision" not in self.model_name else self.model_name,
            system_instruction=system_instruction
        )

        return await self._get_response(vision_model, gemini_messages, None)

    async def health_check(self) -> bool:
        try:
            response = await self.model.generate_content_async("hi")
            return True
        except Exception:
            return False

    @property
    def supports_vision(self) -> bool:
        return True

    @property
    def cost_per_1k_tokens(self) -> tuple[float, float]:
        """Return (input_cost, output_cost) per 1K tokens"""
        costs = {
            "gemini-1.5-pro": (0.00125, 0.005),
            "gemini-1.5-flash": (0.000075, 0.0003),
            "gemini-1.0-pro": (0.0005, 0.0015),
        }
        return costs.get(self.model_name, (0.00125, 0.005))
