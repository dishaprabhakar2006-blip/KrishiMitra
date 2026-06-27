import os
import sys
import asyncio
from dotenv import load_dotenv

# Ensure the current directory is in the path
sys.path.append(os.path.dirname(__file__))

def check_imports():
    print("1. Testing agent and tool imports...")
    try:
        from tools.weather_tool import get_weather_forecast
        from tools.market_tool import get_mandi_prices
        print("   [OK] Tools imported successfully.")
    except Exception as e:
        print(f"   [ERROR] Failed to import tools: {str(e)}")
        return False

    try:
        from agents.memory_agent import memory_agent
        from agents.weather_agent import weather_agent
        from agents.crop_agent import crop_agent
        from agents.pest_agent import pest_agent
        from agents.market_agent import market_agent
        from agents.scheme_agent import scheme_agent
        from agents.profit_agent import profit_agent
        from agents.orchestrator_agent import orchestrator_agent
        print("   [OK] Agents imported and instantiated successfully.")
    except Exception as e:
        print(f"   [ERROR] Failed to import agents: {str(e)}")
        return False
        
    try:
        import main
        print("   [OK] main.py imported successfully.")
    except Exception as e:
        print(f"   [ERROR] Failed to import main.py: {str(e)}")
        return False
        
    return True

async def test_orchestrator():
    print("\n2. Testing Orchestrator agent execution...")
    load_dotenv()
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("   [WARN] MISTRAL_API_KEY is not set in .env. Skipping execution test.")
        return True
        
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai.types import Content, Part
    from agents.orchestrator_agent import orchestrator_agent
    
    try:
        session_service = InMemorySessionService()
        runner = Runner(
            agent=orchestrator_agent,
            session_service=session_service,
            app_name="krishnamitra_verify",
            auto_create_session=True
        )
        
        # Test query
        test_query = "What crops should I sow in monsoon in Maharashtra? My name is Ramesh."
        msg = Content(role="user", parts=[Part(text=test_query)])
        
        print(f"   Sending query: '{test_query}'")
        
        response_text = ""
        responding_agent = ""
        
        import uuid
        session_id = f"verify_session_{uuid.uuid4()}"
        async for event in runner.run_async(user_id="default_farmer", session_id=session_id, new_message=msg):
            if event.node_name:
                responding_agent = event.node_name
            if event.message and event.message.parts:
                text_part = "".join([p.text for p in event.message.parts if getattr(p, "text", None)])
                if text_part:
                    response_text = text_part
                    
        print(f"   [OK] Response received from agent '{responding_agent}':")
        print("-" * 50)
        import sys
        safe_text = response_text.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8')
        print(safe_text[:300] + "..." if len(safe_text) > 300 else safe_text)
        print("-" * 50)
        return True
    except Exception as e:
        print(f"   [ERROR] Execution failed: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("KrishiMitra Verification Script")
    print("=" * 60)
    
    if not check_imports():
        print("\n[ERROR] Verification FAILED during imports.")
        sys.exit(1)
        
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(test_orchestrator())
    
    if success:
        print("\n[SUCCESS] Verification SUCCESSFUL! All checks passed.")
    else:
        print("\n[ERROR] Verification FAILED during agent execution.")
        sys.exit(1)

if __name__ == "__main__":
    main()
