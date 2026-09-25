from langchain_core.tools import tool
from langchain.agents import create_agent
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from warnings import filterwarnings
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import Runnable
import time

filterwarnings('ignore')
import urllib3
import os
from bs4 import BeautifulSoup
from ddgs import DDGS

@tool
def get_info_from_query(query):
    """Gets the text from the query. Can be used for searching the internet
        Just pass the query and function will search on the internet and give the text
    """
    search_result_urls = []
    num = 2
    with DDGS() as ddgs:
        raw_response = ddgs.text(query, max_results=num)

        for res in raw_response:
            search_result_urls.append(res.get("href"))


    http = urllib3.PoolManager()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    final_text=""
    for url in search_result_urls:
        try:
            response = http.request('GET', url, headers=headers, timeout=10.0)

            if response.status != 200:
                return "fetch failed with status " + str(response.status)
            html_text = response.data.decode('utf-8', errors='replace')

        except urllib3.exceptions.HTTPError as e:
            print('Fetch failed due to ' + str(e))
            return "fetch failed due to " + str(e)

        soup = BeautifulSoup(html_text, 'html.parser')
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        raw_text = soup.get_text()
        lines = (line.strip() for line in raw_text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        final_text += clean_text[:3000]


    return final_text


def stream_ans(agent:Runnable, prompt, config):
    for step in agent.stream({"messages" : [("user", prompt)]}, config=config, stream_mode='updates'):
        for node_name, state_data in step.items():
            last_msg = state_data["messages"][-1]
            if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                tool_name = last_msg.tool_calls[0]['name']
                print("The agent has used the tool " + tool_name)

            elif node_name == 'tools':
                print(f"✅ [Tool Execution] -> Scraped {len(last_msg.content)} characters of text.")

            elif last_msg.content:
                print(last_msg.content[0]["text"])



if __name__ == "__main__":
    load_dotenv()

    llm = ChatGoogleGenerativeAI(
        model='gemini-3.5-flash-lite',
        temperature=0,
    )

    tools = [get_info_from_query]

    checkpointer = InMemorySaver()

    agent = create_agent(
        model=llm,
        system_prompt="You are a research agent that gives short and concise answers to questions",
        tools=tools,
        checkpointer=checkpointer
    )

    print("Agent created. Invoking the agent... ")
    while True:
        print("Enter your prompt : ")
        inp = input()
        print("Processing ur request")
        ti = time.time()
        # response = agent.invoke({"messages" : [("user", inp)]}, config={'configurable' : {"thread_id" : "research_thread1"}})
        # for msg in response["messages"]:
        #     if hasattr(msg, 'tool_calls') and msg.tool_calls:
        #         print("Tool has been called")

        stream_ans(agent, inp, {'configurable' : {'thread_id' : 'research_thread1'}})

        print("Response generated in " + str(time.time() - ti) + " time")



    print("Exiting....")

