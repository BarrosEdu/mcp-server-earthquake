import os
from pathlib import Path

import agentops
from crewai import Agent, Task, Crew, Process
from crewai_tools import MCPServerAdapter
from dotenv import load_dotenv
from fastmcp import FastMCP
from langchain_openai import ChatOpenAI
from mcp import StdioServerParameters

# Load env vars first
load_dotenv()

AGENTOPS_API_KEY = os.getenv("AGENTOPS_API_KEY")
if AGENTOPS_API_KEY:
    agentops.init(AGENTOPS_API_KEY, default_tags=["earthquake_analyst"])

# Instantiate MCP server
mcp = FastMCP("earthquake-agent-server")

BASE_DIR = Path(__file__).resolve().parent.parent
QUAKE_SCRIPT = BASE_DIR / "mcp" / "earthquake_mcp_server.py"


@mcp.tool(name="earthquake_analyst")
async def earthquake_analyst_tool(question: str) -> str:
    """Earthquake analysis tool using MCP server."""

    quake_params = StdioServerParameters(
        command="python",
        args=[str(QUAKE_SCRIPT)],
        env=os.environ,
    )

    try:
        llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.3)
    except Exception as e:
        return f"Error initializing LLM: {str(e)}"

    try:
        with MCPServerAdapter(quake_params) as quake_tools:
            quake_agent = Agent(
                role="Earthquake Data Analyst",
                goal="Provide expert-level earthquake and seismic risk analysis for earthquake-related questions.",
                backstory="You are a domain-restricted seismology analyst. You are STRICTLY forbidden from answering other topics.",
                tools=quake_tools,
                llm=llm,
                verbose=True,
            )

        quake_task = Task(
            description=f"Answer the earthquake-related question: '{question}'. Use available tools to get recent earthquake data and provide a comprehensive analysis.",
            expected_output="A comprehensive earthquake analysis including recent seismic events, magnitudes, risk assessment, and geographic interpretation.",
            tools=quake_tools,
            agent=quake_agent,
        )
        crew = Crew(
            agents=[quake_agent],
            tasks=[quake_task],
            process=Process.sequential,
            verbose=True,
            tracing=True,
        )

        result = await crew.kickoff_async()

        if isinstance(result, dict):
            tasks_output = result.get("tasks_output", [])
            if (
                isinstance(tasks_output, list)
                and tasks_output
                and isinstance(tasks_output[0], dict)
                and "raw" in tasks_output[0]
            ):
                return tasks_output[0]["raw"]
            elif "raw" in result:
                return result["raw"]

        return str(result)
    except Exception as e:
        return f"Error running earthquake analysis: {str(e)}"


if __name__ == "__main__":

    port = int(os.getenv("PORT", "8000"))
    mcp.run(
        transport="http",   # recomendado para deploy web :contentReference[oaicite:1]{index=1}
        host="0.0.0.0",     # obrigatório no Render :contentReference[oaicite:2]{index=2}
        port=port,
        path="/mcp"         # endpoint MCP → ex: https://...onrender.com/mcp
    )