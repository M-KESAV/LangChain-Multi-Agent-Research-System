from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.tools.tools import web_search, scrape_url
from dotenv import load_dotenv
import os

load_dotenv()


def get_gemini_llm(temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    """Initializes and returns the ChatGoogleGenerativeAI model using backend configuration."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not configured in the environment.")
    model_name = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature
    )


class AgentWrapper:
    """Wraps agent graph to guarantee string content in the final AIMessage."""
    def __init__(self, agent):
        self.agent = agent

    def invoke(self, inputs, config=None, **kwargs):
        res = self.agent.invoke(inputs, config=config, **kwargs)
        if "messages" in res and res["messages"]:
            last = res["messages"][-1]
            if hasattr(last, "text") and isinstance(last.content, list):
                last.content = str(last.text)
        return res

    async def ainvoke(self, inputs, config=None, **kwargs):
        res = await self.agent.ainvoke(inputs, config=config, **kwargs)
        if "messages" in res and res["messages"]:
            last = res["messages"][-1]
            if hasattr(last, "text") and isinstance(last.content, list):
                last.content = str(last.text)
        return res


# 1st Agent : Search Agent
def build_search_agent():
    llm = get_gemini_llm(temperature=0.0)
    agent = create_agent(
        model=llm,
        tools=[web_search],
    )
    return AgentWrapper(agent)


# 2nd Agent : Reader Agent
def build_reader_agent():
    llm = get_gemini_llm(temperature=0.0)
    agent = create_agent(
        model=llm,
        tools=[scrape_url],
    )
    return AgentWrapper(agent)


# Writer Chain Prompt
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional."""),
])


# Critic Chain Prompt
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])


class LazyChain:
    """Lazily initializes the LCEL chain upon first invoke to prevent import crashes when keys are missing."""
    def __init__(self, prompt: ChatPromptTemplate, temperature: float = 0.0):
        self.prompt = prompt
        self.temperature = temperature
        self._chain = None

    def _get_chain(self):
        if self._chain is None:
            llm = get_gemini_llm(temperature=self.temperature)
            self._chain = self.prompt | llm | StrOutputParser()
        return self._chain

    def invoke(self, inputs, config=None, **kwargs) -> str:
        return self._get_chain().invoke(inputs, config=config, **kwargs)

    async def ainvoke(self, inputs, config=None, **kwargs) -> str:
        return await self._get_chain().ainvoke(inputs, config=config, **kwargs)


# 3rd Chain: Writer Chain
writer_chain = LazyChain(writer_prompt, temperature=0.0)

# 4th Chain: Critic Chain
critic_chain = LazyChain(critic_prompt, temperature=0.0)
