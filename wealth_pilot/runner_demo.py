"""
WealthPilot — Full Runner with All Services
Demonstrates the Runner as the execution engine.
"""

import asyncio
from dotenv import load_dotenv

# load .env before anything else — adk web does this for you,
# but running directly with python -m does not
load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types

from .agent import root_agent


APP_NAME = "wealth_pilot"
USER_ID = "demo_user"


async def main():
    # ── Configure all services ───────────────────────
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()
    artifact_service = InMemoryArtifactService()

    # ── Create the Runner ────────────────────────────
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,
        artifact_service=artifact_service,
    )

    # ── Create a session ─────────────────────────────
    session = await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID,
    )

    print(f"\n🎯 WealthPilot — Full Runner Demo")
    print(f"Session ID: {session.id}")
    print(f"Services: Session ✅ Memory ✅ Artifacts ✅")
    print(f"Type 'quit' to exit\n")

    # ── Interactive loop ─────────────────────────────
    while True:
        user_input = input("You: ").strip()
        if not user_input or user_input.lower() in ("quit", "exit"):
            break

        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_input)],
        )
        print("\nWealthPilot: ", end="", flush=True)
        async for event in runner.run_async(
            user_id=USER_ID, session_id=session.id, new_message=content,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text, end="", flush=True)
        print("\n")

    # ── Session summary ──────────────────────────────
    final_session = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session.id,
    )
    print(f"\n📊 Session Summary")
    print(f"Events: {len(final_session.events)}\n")


if __name__ == "__main__":
    asyncio.run(main())