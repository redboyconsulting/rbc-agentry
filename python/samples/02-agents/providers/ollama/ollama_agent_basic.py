# Copyright (c) Microsoft. All rights reserved.

import asyncio
import itertools
import os
import shutil
from datetime import datetime

from agent_framework import Agent, MCPStdioTool, tool
from agent_framework.ollama import OllamaChatClient, OllamaChatOptions
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

"""
Ollama Agent Basic Example

This sample demonstrates implementing an Ollama agent with basic tool usage,
running interactively: it keeps asking the console for a question and lets
you talk to the agent about anything, instead of a fixed canned query.

Ensure to install Ollama and have a model running locally before running the sample
Not all Models support function calling, to test function calling try llama3.2 or qwen3:4b
Set the model to use via the OLLAMA_MODEL environment variable or modify the code below.
https://ollama.com/

Reasoning (thinking):
If the model supports reasoning (e.g. qwen3:14b, qwen3:8b), it is enabled
automatically so the model thinks before answering, which gives better
answers for complex questions. Models without reasoning (e.g. llama3.2) keep
working, just without it.
- OLLAMA_THINK=0 disables reasoning even if the model supports it.
- OLLAMA_SHOW_REASONING=0 hides the reasoning text and only shows the answer.

Optional Playwright browser automation (MCP):
Set ENABLE_PLAYWRIGHT_MCP=1 and have Node.js/npx installed to give the agent
browser automation tools (navigate, click, screenshot, etc.) served by the
official @playwright/mcp server (started automatically as a child process,
no separate setup required beyond Node.js). https://github.com/microsoft/playwright-mcp
If online startup times out, first run `npx -y @playwright/mcp@latest --help`
and then set PLAYWRIGHT_MCP_OFFLINE=1 to use npm's cache without registry requests.
Set PLAYWRIGHT_BROWSER=msedge to control Microsoft Edge instead of the default browser.

"""


# NOTE: approval_mode="never_require" is for sample brevity. Use "always_require" in production;
# see samples/02-agents/tools/function_tool_with_approval.py
# and samples/02-agents/tools/function_tool_with_approval_and_sessions.py.
# This function is exposed to the model as a "tool" it can call by name
# (the model decides when to invoke it based on the user's query).
@tool(approval_mode="never_require")
def get_time(location: str) -> str:
    """Get the current time."""
    return f"The current time in {location} is {datetime.now().strftime('%I:%M %p')}."


async def _spinner(stop_event: asyncio.Event) -> None:
    """Print a rotating "thinking" indicator until stop_event is set.

    Local models can take a few seconds before the first streamed token
    arrives; this gives the user visible feedback that the agent is
    working instead of an apparently frozen terminal.
    """
    frames = itertools.cycle("|/-\\")
    while not stop_event.is_set():
        print(f"\rAgent: {next(frames)} pensando...", end="", flush=True)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=0.15)
        except asyncio.TimeoutError:
            pass
    # Clear the spinner line before the caller prints the real answer.
    print("\r" + " " * 40, end="", flush=True)


async def _model_supports_thinking(client: OllamaChatClient) -> bool:
    """Ask the Ollama server whether the configured model supports reasoning.

    Sending think=True to a model without that capability makes Ollama reject
    the request, so reasoning is only enabled when the model reports it.
    """
    try:
        info = await client.client.show(client.model)
    except Exception as exc:  # noqa: BLE001 - any failure just means "don't enable thinking"
        print(f"No se pudieron consultar las capacidades de '{client.model}' ({exc}); se omite el razonamiento.")
        return False
    return "thinking" in (info.capabilities or [])


async def interactive_chat() -> None:
    """Keep asking the console for questions until the user exits.

    Type a question and press Enter to get a streamed answer. Type
    "exit", "quit", "salir", "fin" or "adios" (or press Ctrl+C) to stop.
    """
    no_browser_instructions = (
        "You are a general-purpose helpful assistant that can discuss any topic. "
        "You have access to a get_time tool that returns the current time for a "
        "specific city. Only call that tool when the user explicitly asks what time "
        "it is somewhere AND names a city. For greetings, general knowledge, how-to "
        "questions, or anything else, just answer directly in plain text — never ask "
        "the user for their location and never mention the get_time tool unless it "
        "was actually used. You do NOT have web browser automation tools (e.g. "
        "Playwright) in this session. If asked whether you can browse the web, "
        "click, navigate, or take screenshots, say honestly that you don't have "
        "that capability right now — never claim you can do it when you can't."
    )
    with_browser_instructions = no_browser_instructions.replace(
        "You do NOT have web browser automation tools (e.g. "
        "Playwright) in this session. If asked whether you can browse the web, "
        "click, navigate, or take screenshots, say honestly that you don't have "
        "that capability right now — never claim you can do it when you can't.",
        "You also have browser automation tools (Playwright: navigate, click, "
        "screenshot, etc.) available — use them whenever the user asks you to "
        "browse or check a website.",
    )
    # base_instructions is what gets used if Playwright fails to connect and we
    # fall back below; it must truthfully say the browser tools are NOT available.
    base_instructions = no_browser_instructions
    tools: list[object] = [get_time]
    instructions = no_browser_instructions

    # Playwright MCP gives the agent browser automation tools (navigate, click,
    # screenshot, etc.). It's optional because it requires Node.js/npx AND
    # internet access (npx downloads the package on first use); only enable
    # it if explicitly requested via ENABLE_PLAYWRIGHT_MCP=1.
    playwright_enabled = os.environ.get("ENABLE_PLAYWRIGHT_MCP") == "1"
    if playwright_enabled and shutil.which("npx") is None:
        print("ENABLE_PLAYWRIGHT_MCP=1 pero no se encontró 'npx' en el PATH; se omite Playwright MCP.")
        playwright_enabled = False

    if playwright_enabled:
        playwright_args = ["-y", "@playwright/mcp@latest"]
        if os.environ.get("PLAYWRIGHT_MCP_OFFLINE") == "1":
            playwright_args = ["--offline", "-y", "@playwright/mcp"]
        if browser := os.environ.get("PLAYWRIGHT_BROWSER"):
            playwright_args.extend(["--browser", browser])
        # MCPStdioTool launches the MCP server as a child process and talks to
        # it over stdin/stdout, exposing its tools to the agent automatically.
        tools.append(
            MCPStdioTool(
                name="playwright",
                description="Browser automation tools (navigate, click, screenshot, etc.).",
                command="npx",
                args=playwright_args,
            )
        )
        instructions = with_browser_instructions

    # OllamaChatClient() with no arguments reads OLLAMA_MODEL (which model to
    # use, e.g. "qwen3:14b") and OLLAMA_HOST (defaults to
    # http://localhost:11434) from environment variables.
    client = OllamaChatClient()

    think_enabled = False
    if os.environ.get("OLLAMA_THINK", "1") != "0":
        think_enabled = await _model_supports_thinking(client)
    show_reasoning = think_enabled and os.environ.get("OLLAMA_SHOW_REASONING", "1") != "0"
    default_options: OllamaChatOptions = {"think": True} if think_enabled else {}
    print(f"Modelo: {client.model} | Razonamiento: {'activado' if think_enabled else 'desactivado'}")

    agent = Agent(
        client=client,
        name="Assistant",
        instructions=instructions,
        tools=tools,
        default_options=default_options,
    )

    # Entering the agent's context starts any MCP child process (e.g.
    # Playwright) and connects to it. If that connection hangs (e.g. no
    # internet to download the Playwright MCP package) or fails, give up
    # after PLAYWRIGHT_MCP_TIMEOUT_SECONDS and fall back to running without
    # it instead of leaving the user stuck on the "pensando..." spinner.
    # 60s because the *first* run of `npx @playwright/mcp@latest` has to
    # download the npm package (and npx itself resolving it) which can take
    # well over 15s even with a working internet connection; subsequent runs
    # are cached by npx and connect almost instantly.
    PLAYWRIGHT_MCP_TIMEOUT_SECONDS = 60
    if playwright_enabled:
        print("Conectando Playwright MCP (puede tardar ~1 min la primera vez mientras se descarga)...")
    try:
        if playwright_enabled:
            await asyncio.wait_for(agent.__aenter__(), timeout=PLAYWRIGHT_MCP_TIMEOUT_SECONDS)
            print("Playwright MCP conectado: herramientas de navegador disponibles.")
        else:
            await agent.__aenter__()
    except Exception as exc:  # noqa: BLE001 - deliberately broad: any MCP/network failure falls back
        if not playwright_enabled:
            raise
        print(
            f"No se pudo conectar Playwright MCP ({exc.__class__.__name__}); "
            "continuando sin esa herramienta. "
            "Prueba 'npx -y @playwright/mcp@latest --help' y luego PLAYWRIGHT_MCP_OFFLINE=1; "
            "ese modo requiere el paquete en la cache de npm."
        )
        tools = [get_time]
        agent = Agent(
            client=client,
            name="Assistant",
            instructions=base_instructions,
            tools=tools,
            default_options=default_options,
        )
        await agent.__aenter__()

    try:
        # create_session() keeps conversation history across turns, so the
        # agent remembers earlier questions/answers within the same run.
        session = agent.create_session()

        print("Escribe tu pregunta (o 'exit'/'quit'/'salir'/'fin' para salir):")
        while True:
            try:
                query = input("\nUser: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not query:
                continue
            if query.lower() in {"exit", "quit", "salir", "fin", "adios", "adiós"}:
                break

            # Show an animated "thinking" spinner while we wait for the model's
            # first token (local models can take a few seconds before they
            # start streaming output).
            stop_spinner = asyncio.Event()
            spinner_task = asyncio.create_task(_spinner(stop_spinner))

            # Which section is currently being printed: None (nothing yet),
            # "reasoning" or "answer". A model may alternate between them
            # (e.g. reason, call a tool, reason again, then answer).
            section: str | None = None

            async def switch_section(new_section: str, label: str) -> None:
                nonlocal section
                if section == new_section:
                    return
                if section is None:
                    # First real token arrived: stop the spinner first.
                    stop_spinner.set()
                    await spinner_task
                    print(f"\r{label}: ", end="", flush=True)
                else:
                    print(f"\n\n{label}: ", end="", flush=True)
                section = new_section

            # stream=True yields the response incrementally as chunks, useful
            # for showing output to a user as it's generated instead of waiting
            # for the full response. Reasoning arrives as "text_reasoning"
            # contents, which chunk.text does not include.
            async for chunk in agent.run(query, session=session, stream=True):
                if show_reasoning:
                    reasoning = "".join(c.text or "" for c in chunk.contents if c.type == "text_reasoning")
                    if reasoning:
                        await switch_section("reasoning", "Razonamiento")
                        print(reasoning, end="", flush=True)
                if chunk.text:
                    await switch_section("answer", "Agent")
                    print(chunk.text, end="", flush=True)

            if section is None:
                # The model never produced any text; still clear the spinner.
                stop_spinner.set()
                await spinner_task
            print()
    finally:
        # Always shut down the agent/MCP child process cleanly, even if the
        # loop above exited via break, Ctrl+C, or an unexpected error.
        await agent.__aexit__(None, None, None)


async def main() -> None:
    print("=== Basic Ollama Chat Client Agent Example (interactive) ===")
    await interactive_chat()


if __name__ == "__main__":
    asyncio.run(main())
