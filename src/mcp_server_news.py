from dotenv import load_dotenv
from fastmcp import FastMCP
from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
import agentops
import os


AGENTOPS_API_KEY = os.getenv("AGENTOPS_API_KEY")
agentops.init(AGENTOPS_API_KEY, default_tags=["earthquake_analyst"])

# Load env vars
load_dotenv()

# Instantiate MCP server
mcp = FastMCP("earthquake-agent-server")

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # sobe de src/ para raiz
QUAKE_SCRIPT = BASE_DIR / "mcp" / "earthquake_mcp_server.py"

@mcp.tool(name="earthquake_analyst")
async def earthquake_analyst_tool(question: str) -> str:
    """(Versão de teste) Usa apenas o MCP de earthquake para validar o Render."""

    quake_params = StdioServerParameters(
        command="python",
        args=[str(QUAKE_SCRIPT)],
        env=os.environ,
    )

    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.3)

    with MCPServerAdapter(quake_params) as quake_tools:
        quake_agent = Agent(
            role="Earthquake Data Analyst",
            goal=(
                "Provide expert-level earthquake and seismic risk analysis ONLY for questions "
                "explicitly related to seismic activity. For any unrelated topic, decline politely "
                "using the exact sentence: 'I am only configured to answer questions about earthquakes and seismic risk.'"
            ),
            backstory="You are a domain-restricted seismology analyst. You are STRICTLY forbidden from answering other topics.",
            tools=quake_tools,
            llm=llm,
            verbose=True,
        )

        quake_task = Task(
            description=(
                f"Analyze seismic activity strictly related to the question: '{question}'. "
                "If the question is NOT related to earthquakes, magnitudes, seismic risk, "
                "geological hazards, USGS data, or epicenter analysis, you MUST respond: "
                "'I am only configured to answer questions about earthquakes and seismic risk.'"
            ),
            expected_output=(
                "One of the following:\n"
                "1) If the question IS about earthquakes:\n"
                "   - A structured analysis including:\n"
                "     - recent seismic events\n"
                "     - magnitudes\n"
                "     - risk score\n"
                "     - geographic interpretation\n"
                "     - clear executive-level summary\n"
                "\n"
                "2) If the question IS NOT about earthquakes:\n"
                "   - The exact sentence: 'I am only configured to answer questions about earthquakes and seismic risk.'"
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

        if isinstance(result, dict):
            if (
                "tasks_output" in result
                and isinstance(result["tasks_output"], list)
                and len(result["tasks_output"]) > 0
                and "raw" in result["tasks_output"][0]
            ):
                return result["tasks_output"][0]["raw"]
            elif "raw" in result:
                return result["raw"]

        return str(result)



if __name__ == "__main__":
    # mcp.run(transport="sse", host="127.0.0.1", port=8000)
    # mcp.run()
    # Render define PORT (padrão 10000) :contentReference[oaicite:0]{index=0}
    port = int(os.getenv("PORT", "8000"))
    mcp.run(
        transport="http",   # recomendado para deploy web :contentReference[oaicite:1]{index=1}
        host="0.0.0.0",     # obrigatório no Render :contentReference[oaicite:2]{index=2}
        port=port,
        path="/mcp"         # endpoint MCP → ex: https://...onrender.com/mcp
    )