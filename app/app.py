import streamlit as st
import asyncio
from fastmcp import Client
import json
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Risk Analyst Chat", page_icon="📊", layout="wide")
st.title("Earthquake Risk Analyst – AI Chat Interface")

st.markdown("""""")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Helper: Call the MCP agent server via SSE
async def call_agent(question: str):
    client = Client("https://mcp-server-earthquake.onrender.com/mcp")  # ajuste se mudar a porta/URL
    async with client:
        result = await client.call_tool(
            "yfinance_analyst",
            {"question": question},
        )

        # Se a tool retornou erro
        if getattr(result, "is_error", False):
            # tenta usar data como mensagem de erro
            return f"Tool error: {getattr(result, 'data', result)}"

        # 1) Preferir structured_content["result"], se existir
        sc = getattr(result, "structured_content", None)
        if isinstance(sc, dict) and "result" in sc:
            return sc["result"]

        # 2) Se tiver .data como string, usar isso
        data = getattr(result, "data", None)
        if isinstance(data, str) and data.strip():
            return data

        # 3) Se tiver lista de content com .text, juntar tudo
        content_list = getattr(result, "content", None)
        if isinstance(content_list, list) and content_list:
            texts = [
                getattr(c, "text", "")
                for c in content_list
                if hasattr(c, "text") and getattr(c, "text")
            ]
            if texts:
                return "\n\n".join(texts)

        # 4) Fallback: repr do objeto (último caso)
        return str(result)



# Accept user input
if prompt := st.chat_input("Ask me anything ..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("The agent is thinking..."):
            try:
                response = asyncio.run(call_agent(prompt))

                # Tentar interpretar resposta como JSON estruturado
                try:
                    resp_json = json.loads(response)
                    if isinstance(resp_json, dict):
                        # Se vier no formato CrewAI (raw + tasks_output)
                        if (
                            "tasks_output" in resp_json
                            and isinstance(resp_json["tasks_output"], list)
                            and len(resp_json["tasks_output"]) > 0
                            and "raw" in resp_json["tasks_output"][0]
                        ):
                            display_data = resp_json["tasks_output"][0]["raw"]
                        elif "raw" in resp_json:
                            display_data = resp_json["raw"]
                        else:
                            display_data = response
                    else:
                        display_data = response
                except Exception:
                    display_data = response

                # Agora tentar exibir display_data como DataFrame ou JSON bonitinho
                try:
                    data = json.loads(display_data)
                    if isinstance(data, list) and all(
                        isinstance(row, dict) for row in data
                    ):
                        df = pd.DataFrame(data)
                        st.dataframe(df)
                        response = None
                    else:
                        st.json(data)
                        response = None
                except Exception:
                    # Não era JSON → mostra como texto normal
                    response = display_data

            except Exception as e:
                import traceback

                tb = traceback.format_exc()
                response = f"Error: {e}\n\nTraceback:\n{tb}"

            if response:
                st.markdown(response)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response if response else "[Structured output above]",
        }
    )
