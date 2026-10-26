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
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
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
    ("system", """You are an expert technical research analyst and writer.
You write authoritative, objective, deeply informative, and rigorously cited research reports based strictly on verified research intelligence.

CORE CITATION & GROUNDING RULES:
1. Ground every claim and finding in the provided Research Gathered data.
2. In-text citations are MANDATORY: cite your sources directly in the text using strictly numbered brackets: [1], [2], [3], etc. NEVER use author or shorthand names in brackets (e.g. do NOT write [IDTechEx] or [Nature]); use strictly the corresponding numerical index [N].
3. Every in-text citation [N] MUST map 1-to-1 consistently to the exact numbered entry [N] in the '## Sources & References' section at the end of the report.
4. Every citation and URL in your report MUST strictly match a source provided in the VERIFIED DISCOVERED SOURCES list. Each cited URL and source MUST belong to an actual source returned in that list. NEVER invent, fabricate, or guess URLs, domain names, citations, publication dates, or statistics.
5. Evidence requirement: NEVER claim that a source supports a statement unless the retrieved snippet or scraped content actually provides evidence for that statement. If information is uncertain or incomplete, state that limitation clearly.
6. If no usable external sources or URLs were discovered, explicitly report that the topic lacks verified citations and do not use numerical citations.
7. End the report with a dedicated '## Sources & References' section listing each cited numbered entry [N] with its verified Title and canonical URL."""),
    ("human", """Write a comprehensive, professional research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report with clear markdown formatting:
# [Topic Title]
## Introduction & Executive Summary
## Key Findings (minimum 3 well-grounded, detailed sections with in-text numerical citations [N])
## In-Depth Analysis & Practical Implications
## Conclusion & Strategic Outlook
## Sources & References (strictly numbered [1], [2] matching the in-text citations and verified sources)

Be detailed, factual, and maintain strict academic/industry rigor."""),
])


# Critic Chain Prompt
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a rigorous and constructive research critic. Be honest, objective, and specific.
Evaluate the report for structural quality, empirical depth, factual grounding, and especially source citation coverage and citation-to-source consistency.
Verify that every in-text citation [N] corresponds consistently to a numbered entry in Sources & References, that no fabricated references are cited, and that claims are supported by the cited sources."""),
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

Citation & Source Quality:
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
