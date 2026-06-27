import os
import json
import logging
import httpx
from typing import AsyncGenerator, Optional, List, Dict, Any
from google.genai import types
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from pydantic import Field

logger = logging.getLogger("krishnamitra.mistral_llm")

def _clean_schema(d: Any) -> Any:
    """Recursively clean schema dict to remove None values and serialize Enums/Pydantic types."""
    if hasattr(d, "model_dump"):
        d = d.model_dump()
    if isinstance(d, dict):
        cleaned = {}
        for k, v in d.items():
            if v is not None:
                cleaned[k] = _clean_schema(v)
        # Mistral/OpenAI parameters must define type="object" if properties are present
        if "properties" in cleaned and "type" not in cleaned:
            cleaned["type"] = "object"
        return cleaned
    elif isinstance(d, list):
        return [_clean_schema(x) for x in d]
    elif hasattr(d, "value"): # Handle Enum
        return d.value
    return d

class MistralLlm(BaseLlm):
    model: str = "mistral-large-latest"

    @classmethod
    def supported_models(cls) -> list[str]:
        return ["mistral-large-latest"]

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        # 1. Get API Key
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            yield LlmResponse(
                error_code="MISSING_API_KEY",
                error_message="MISTRAL_API_KEY is not set in the environment or .env file."
            )
            return

        # 2. Extract System Instruction
        messages = []
        sys_inst = llm_request.config.system_instruction
        if sys_inst:
            sys_text = ""
            if isinstance(sys_inst, str):
                sys_text = sys_inst
            elif getattr(sys_inst, "parts", None):
                sys_text = "\n".join([p.text for p in sys_inst.parts if getattr(p, "text", None)])
            elif isinstance(sys_inst, list):
                sys_text = "\n".join([p.text for p in sys_inst if getattr(p, "text", None)])
            
            # Check if this is the Crop Advisory Agent or Scheme Finder Agent
            is_crop_agent = "Crop Advisory Agent" in sys_text
            is_scheme_agent = "Scheme Finder Agent" in sys_text
            
            if (is_crop_agent or is_scheme_agent) and sys_text:
                # Find the user's latest query text (skipping synthetic ADK tool-context messages)
                user_query = ""
                for content in reversed(llm_request.contents):
                    if content.role == "user":
                        text_content = "".join([p.text for p in content.parts if getattr(p, "text", None)])
                        if text_content and not text_content.startswith("For context:"):
                            user_query = text_content
                            break
                
                if user_query:
                    import re
                    # Clean out category labels like "[Weather and Irrigation Category]"
                    clean_query = re.sub(r'^\[.*?\]\s*', '', user_query)
                    
                    try:
                        from tools.ragretriever import retrieve_relevant_chunks
                        with open("mistral_debug.log", "a", encoding="utf-8") as f_debug:
                            f_debug.write(f"RAG query execution: clean_query='{clean_query}', original='{user_query}'\n")
                        chunks = retrieve_relevant_chunks(clean_query, top_k=3)
                        if chunks:
                            context_str = "\n\n=== RETRIEVED AGRICULTURAL KNOWLEDGE CONTEXT ===\n" + "\n\n".join(chunks) + "\n================================================\n"
                            sys_text += context_str
                    except Exception as e:
                        # Fail silently in production, log for debug
                        with open("mistral_debug.log", "a", encoding="utf-8") as f_debug:
                            f_debug.write(f"RAG retrieval error: {str(e)}\n")
            
            if sys_text:
                messages.append({"role": "system", "content": sys_text})

        # 3. Translate Gemini contents to Mistral messages
        for content in llm_request.contents:
            role = "user" if content.role == "user" else "assistant"
            
            # Check for tool responses (function response parts)
            has_tool_response = False
            for part in content.parts:
                if part.function_response:
                    has_tool_response = True
                    tool_call_id = part.function_response.id or f"call_{part.function_response.name}"
                    tool_name = part.function_response.name
                    
                    resp_val = part.function_response.response
                    if isinstance(resp_val, dict):
                        resp_content = json.dumps(resp_val)
                    else:
                        resp_content = str(resp_val)
                        
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "name": tool_name,
                        "content": resp_content
                    })
            
            if has_tool_response:
                continue

            # Standard user/assistant message parts
            content_text = ""
            tool_calls = []
            for part in content.parts:
                if part.text:
                    content_text += part.text
                elif part.function_call:
                    tool_calls.append({
                        "id": part.function_call.id or f"call_{part.function_call.name}",
                        "type": "function",
                        "function": {
                            "name": part.function_call.name,
                            "arguments": json.dumps(part.function_call.args) if isinstance(part.function_call.args, dict) else part.function_call.args
                        }
                    })
            
            msg = {"role": role}
            if content_text:
                msg["content"] = content_text
            else:
                msg["content"] = ""
                
            if tool_calls:
                msg["tool_calls"] = tool_calls
                
            messages.append(msg)

        # 4. Extract tools
        tools = []
        if llm_request.config.tools:
            for tool in llm_request.config.tools:
                if isinstance(tool, types.Tool) and tool.function_declarations:
                    for fd in tool.function_declarations:
                        params = _clean_schema(fd.parameters) if fd.parameters else {"type": "object", "properties": {}}
                        tools.append({
                            "type": "function",
                            "function": {
                                "name": fd.name,
                                "description": fd.description or "",
                                "parameters": params
                            }
                        })

        # 5. Build payload
        payload = {
            "model": self.model,
            "messages": messages
        }
        if tools:
            payload["tools"] = tools
            
        # Handle structured outputs / response schema
        if llm_request.config.response_schema:
            payload["response_format"] = {"type": "json_object"}

        # 6. Call Mistral API via httpx
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # DEBUG LOG PAYLOAD
        with open("mistral_debug.log", "a", encoding="utf-8") as f_debug:
            f_debug.write(f"=== MISTRAL REQUEST PAYLOAD ===\n{json.dumps(payload, indent=2)}\n\n")
            
        import asyncio
        max_retries = 5
        backoff_delay = 3.0
        response = None
        
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        "https://api.mistral.ai/v1/chat/completions",
                        json=payload,
                        headers=headers
                    )
                
                # Check for rate limits (429)
                if response.status_code == 429 and attempt < max_retries:
                    with open("mistral_debug.log", "a", encoding="utf-8") as f_debug:
                        f_debug.write(f"Rate limited (429). Retrying in {backoff_delay}s... (Attempt {attempt+1}/{max_retries})\n\n")
                    await asyncio.sleep(backoff_delay)
                    backoff_delay *= 2
                    continue
                    
                break
            except Exception as e:
                if attempt < max_retries:
                    await asyncio.sleep(backoff_delay)
                    backoff_delay *= 2
                    continue
                yield LlmResponse(
                    error_code="CONNECTION_ERROR",
                    error_message=f"Failed to connect to Mistral AI: {str(e)}"
                )
                return
        try:
            # DEBUG LOG RESPONSE
            if response is not None:
                with open("mistral_debug.log", "a", encoding="utf-8") as f_debug:
                    f_debug.write(f"=== MISTRAL RESPONSE (Status: {response.status_code}) ===\n{response.text}\n\n")
                    
                if response.status_code != 200:
                    yield LlmResponse(
                        error_code=str(response.status_code),
                        error_message=f"Mistral API returned error code {response.status_code}: {response.text}"
                    )
                    return
            else:
                yield LlmResponse(
                    error_code="NO_RESPONSE",
                    error_message="Mistral API returned no response."
                )
                return
                
            data = response.json()
            choice = data["choices"][0]
            message = choice["message"]
            
            finish_reason = types.FinishReason.STOP
            choice_finish = choice.get("finish_reason")
            if choice_finish == "length":
                finish_reason = types.FinishReason.MAX_TOKENS
            elif choice_finish == "tool_calls":
                finish_reason = types.FinishReason.STOP
            
            # 7. Convert Mistral response back to LlmResponse
            parts = []
            if message.get("content"):
                parts.append(types.Part(text=message["content"]))
                
            if message.get("tool_calls"):
                for tc in message["tool_calls"]:
                    tc_id = tc.get("id")
                    tc_func = tc.get("function", {})
                    tc_name = tc_func.get("name")
                    tc_args_str = tc_func.get("arguments", "{}")
                    
                    try:
                        tc_args = json.loads(tc_args_str)
                    except Exception:
                        tc_args = tc_args_str
                        
                    parts.append(types.Part(
                        function_call=types.FunctionCall(
                            name=tc_name,
                            args=tc_args,
                            id=tc_id
                        )
                    ))
                    
            content = types.Content(role="model", parts=parts)
            
            usage_data = data.get("usage", {})
            usage = types.GenerateContentResponseUsageMetadata(
                prompt_token_count=usage_data.get("prompt_tokens", 0),
                candidates_token_count=usage_data.get("completion_tokens", 0),
                total_token_count=usage_data.get("total_tokens", 0)
            )
            
            yield LlmResponse(
                content=content,
                finish_reason=finish_reason,
                usage_metadata=usage,
                partial=False,
                turn_complete=True
            )
            
        except Exception as e:
            yield LlmResponse(
                error_code="CONNECTION_ERROR",
                error_message=f"Failed to communicate with Mistral: {str(e)}"
            )
