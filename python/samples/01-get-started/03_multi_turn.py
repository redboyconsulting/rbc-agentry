# Copyright (c) Microsoft. All rights reserved.

import asyncio

from agent_framework import Agent
from agent_framework.ollama import OllamaChatClient

"""
Multi-Turn Conversations — Use AgentSession to maintain context

This sample shows how to keep conversation history across multiple calls
by reusing the same session object. It uses OllamaChatClient with a local
Ollama reasoning model (qwen3:14b).
"""


async def main() -> None:
    # <create_agent>
    client = OllamaChatClient(model="qwen3:14b")

    agent = Agent(
        client=client,
        name="ConversationAgent",
        instructions="You are a friendly assistant. Keep your answers brief.",
        # Let the model reason before answering; the reasoning is kept apart from the answer text.
        default_options={"think": True},
    )
    # </create_agent>

    # <multi_turn>
    # Create a session to maintain conversation history
    session = agent.create_session()

    # First turn
    result = await agent.run("My name is Alice and I love hiking.", session=session)
    print(f"Agent: {result}\n")

    # Second turn — the agent should remember the user's name and hobby
    result = await agent.run("What do you remember about me?", session=session)
    print(f"Agent: {result}")
    # </multi_turn>


if __name__ == "__main__":
    asyncio.run(main())
