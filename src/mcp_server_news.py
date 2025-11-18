from dotenv import load_dotenv
from fastmcp import FastMCP
from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
import agentops
import os


AGENTOPS_API_KEY = os.getenv("AGENTOPS_API_KEY")
agentops.init(AGENTOPS_API_KEY, default_tags=["yfinance_analyst"])

# Load env vars
load_dotenv()

# Instantiate MCP server
mcp = FastMCP("yfinance-agent-server")

@mcp.tool(name="yfinance_analyst")
async def yfinance_analyst_tool(question: str) -> str:
    """Analyze yfinance library and answer questions about out data using CrewAI-powered agent."""
    # Set up MCPServerAdapter to talk to the Supabase stock tools server

    finance_params = StdioServerParameters(
        command="uvx",
        args=["yfmcp@latest"],
    )
    airbnb_params = StdioServerParameters(
        command="npx",
        args=["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"],
        env=os.environ,
    )
    quake_params = StdioServerParameters(
        command="python",
        args=["mcp/earthquake_mcp_server.py"],
        env=os.environ,  # para passar EARTHQUAKE_API_KEY, etc, se precisar
    )
    airbnb_llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.3)
    finance_llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.3)
    quake_llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.3)


    with (
        MCPServerAdapter(finance_params) as finance_tools,
        MCPServerAdapter(airbnb_params) as airbnb_tools,
        MCPServerAdapter(quake_params) as quake_tools,

    ):
        airbnb_agent = Agent(
            role="Accommodation Finder Agent",
            goal="Identify the most suitable and top-rated accommodations that match user expectations and budget.",
            backstory="An AI agent with advanced knowledge of short-term rentals. Skilled at finding apartments, hotels, "
            "and boutique stays that align with user preferences like location, amenities, and ratings.",
            tools=airbnb_tools,
            llm=airbnb_llm,
            verbose=True,
        )
        finance_analyst = Agent(
            role="Senior Finance Analyst",
            goal=(
                "Analyze, interpret, and respond to any financial data request using expert-level knowledge "
                "of corporate finance, accounting, market data, and SQL. Provide clear insights and accurate data analysis."
            ),
            backstory=(
                "A highly experienced financial analyst with a strong background in corporate finance, market research, and data analytics. "
                "Trained to understand complex financial statements, investment metrics, and economic indicators, and to convert user requests "
                "into precise SQL queries or structured financial insights. Has deep knowledge of stock markets, financial KPIs, company performance, "
                "and can advise users on revenue, profit trends, valuation ratios, and much more. Adept at interpreting business objectives and "
                "retrieving or transforming the right data from financial databases."
            ),
            tools=finance_tools,
            verbose=True,
            llm=finance_llm,
            allow_delegation=False,
        )
        quake_agent = Agent(
            role="Earthquake Data Analyst",
            goal="Analyze recent earthquakes and seismic risk using the earthquake MCP tools.",
            backstory="A specialist agent focused on querying and interpreting earthquake data.",
            tools=quake_tools,
            llm= quake_llm,  # pode reutilizar
            verbose=True,
        )
        finance_task = Task(
            description=f"Answer this financial data request accurately: {question}",
            expected_output="A concise, accurate SQL query result or an explanation of the financial insight retrieved.",
            tools=finance_tools,
            agent=finance_analyst,
        )
        airbnb_task = Task(
            description=f"Find accommodation that matches the following criteria: {question}",
            expected_output="A list of accommodation options that match the user's preferences and budget.",
            tools=airbnb_tools,
            agent=airbnb_agent,
        )
        quake_task = Task(
            description=f"Analyze earthquake risk or recent events related to: {question}",
            expected_output="A summary of relevant earthquakes and risk insights for the area or period requested.",
            tools=quake_tools,
            agent=quake_agent,
        )


        crew = Crew(
            agents=[finance_analyst,airbnb_agent,quake_agent],
            tasks=[finance_task,airbnb_task,quake_task],
            process=Process.sequential,
            verbose=True,
        )


        result = await crew.kickoff_async()

        # Se for dict no formato CrewAI, extrai o "raw" mais útil
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

        # Se não for dict, garante que vira string
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