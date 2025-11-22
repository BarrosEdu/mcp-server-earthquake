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
    """Earthquake analysis tool using the earthquake MCP server."""

    quake_params = StdioServerParameters(
        command="python",
        args=[str(QUAKE_SCRIPT)],
        env=os.environ,
    )

    try:
        llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.3)
    except Exception as exc:
        return f"Error initializing LLM: {exc}"

    try:
        # Mantém TUDO dentro do contexto do adapter
        with MCPServerAdapter(quake_params) as quake_tools:
            quake_agent = Agent(
                role="Earthquake Data Analyst",
                goal=(
                    "Provide expert-level analysis of recent earthquakes and seismic risk. "
                    "Assume the user's question is related to earthquakes or seismic activity."
                ),
                backstory=(
                    "You are a seismology specialist. You use the provided tools to query "
                    "recent earthquakes, magnitudes and locations, and then explain the "
                    "results in clear language."
                ),
                tools=quake_tools,
                llm=llm,
                verbose=True,
            )

            quake_task = Task(
                description=(
                    f"Answer the user's question about earthquakes: '{question}'. "
                    "Use the available tools to fetch recent earthquake data if needed, "
                    "and provide a concise but informative analysis."
                ),
                expected_output=(
                    "A clear paragraph (or a short set of bullet points) summarizing:\n"
                    "- the most recent relevant earthquakes for the question\n"
                    "- magnitudes and locations\n"
                    "- any notable seismic risk or trend\n"
                    "If there is no recent activity, explicitly say that."
                ),
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

        # Parse do resultado
        if isinstance(result, dict):
            tasks_output = result.get("tasks_output", [])
            if (
                isinstance(tasks_output, list)
                and tasks_output
                and isinstance(tasks_output[0], dict)
                and "raw" in tasks_output[0]
            ):
                return tasks_output[0]["raw"]
            if "raw" in result:
                return result["raw"]

        return str(result)

    except Exception as exc:
        return f"Error running earthquake analysis: {exc}"


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
        path="/mcp",
    )
