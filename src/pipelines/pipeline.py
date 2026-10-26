import uuid
import inspect
from typing import Optional, Callable, Any
from src.agents.agents import build_search_agent, build_reader_agent, writer_chain, critic_chain
from src.db.database import save_research_sync, save_research
from src.tools.tools import (
    tavily_search_structured,
    extract_sources_from_text,
    scrape_url_structured,
    canonicalize_url,
    validate_url,
)
from src.tools.citations import validate_and_normalize_citations


async def _emit_progress(cb: Optional[Callable[[str, dict], Any]], stage: str, data: dict) -> None:
    """Helper to safely invoke synchronous or asynchronous progress callbacks."""
    if cb is None:
        return
    try:
        res = cb(stage, data)
        if inspect.isawaitable(res):
            await res
    except Exception:
        pass


def _extract_sources_from_agent_result(agent_result: dict, query: str = "", topic: str = "") -> list[dict]:
    """
    Extracts all structured sources from tool messages and agent response.
    Deduplicates URLs while preserving result order.
    """
    search_q = query or topic
    sources = []
    seen = set()

    messages = agent_result.get("messages", []) if isinstance(agent_result, dict) else []
    for msg in messages:
        raw_type = getattr(msg, "type", "")
        msg_type = raw_type if isinstance(raw_type, str) else type(msg).__name__
        msg_content = str(getattr(msg, "content", ""))
        if "tool" in msg_type.lower() or "title:" in msg_content.lower() or "http" in msg_content.lower():
            extracted = extract_sources_from_text(msg_content)
            for s in extracted:
                canon = canonicalize_url(s["url"])
                if canon and canon not in seen:
                    seen.add(canon)
                    s["url"] = canon
                    sources.append(s)

    # If zero sources found from agent trajectory, call Tavily structured search directly
    if not sources and search_q:
        try:
            direct_sources = tavily_search_structured(search_q, max_results=5)
            for s in direct_sources:
                canon = canonicalize_url(s["url"])
                if canon and canon not in seen:
                    seen.add(canon)
                    s["url"] = canon
                    sources.append(s)
        except Exception:
            pass

    return sources


def _perform_scraping(candidate_sources: list[dict], reader_agent_content: str = "", max_urls: int = 3) -> tuple[str, list[dict]]:
    """
    Scrapes primary discovered URLs, preserving URLs, titles, and extracted content.
    Handles individual failures gracefully without inventing content.
    """
    scraped_entries = []

    if reader_agent_content and not reader_agent_content.lower().startswith("it looks like your search results"):
        # If reader agent provided actual scraped analysis, preserve it
        scraped_entries.append(f"READER AGENT ANALYSIS:\n{reader_agent_content}")

    if not candidate_sources:
        return "No candidate source URLs were discovered to scrape.", candidate_sources

    # Scrape up to max_urls candidate URLs
    targets = candidate_sources[:max_urls]
    for src in targets:
        url = src.get("url")
        title = src.get("title", url)
        if not url or not validate_url(url):
            continue

        try:
            scrape_res = scrape_url_structured(url, title=title)
            content_text = scrape_res.get("content") or scrape_res.get("text") or ""
            if scrape_res["status"] == "scraped" and content_text:
                src["status"] = "scraped"
                scraped_entries.append(
                    f"SOURCE: {title}\nURL: {url}\nCONTENT:\n{content_text[:2500]}"
                )
            else:
                src["status"] = "failed"
                err = scrape_res.get("error") or "Could not extract readable content."
                src["error"] = err
                scraped_entries.append(
                    f"SOURCE: {title}\nURL: {url}\nSCRAPE STATUS: Failed ({err})"
                )
        except Exception as ex:
            src["status"] = "failed"
            src["error"] = str(ex)
            scraped_entries.append(
                f"SOURCE: {title}\nURL: {url}\nSCRAPE STATUS: Failed ({str(ex)})"
            )

    combined_scraped = "\n\n" + ("=" * 40) + "\n\n" + "\n\n----\n\n".join(scraped_entries) if scraped_entries else "No readable web content could be extracted from candidate URLs."
    return combined_scraped, candidate_sources


def run_research_pipeline(topic: str) -> dict:
    """
    Executes the 4-step multi-agent research pipeline synchronously.
    Saves completed or failed runs to SQLite database and returns the result state.
    """
    if not topic or not isinstance(topic, str) or not topic.strip():
        raise ValueError("Research topic cannot be empty.")

    clean_topic = topic.strip()
    run_id = str(uuid.uuid4())
    state = {
        "id": run_id,
        "topic": clean_topic,
        "status": "running",
        "search_results": "",
        "scraped_content": "",
        "report": "",
        "feedback": "",
        "sources": [],
    }

    try:
        # Step 1 - Search agent
        print("\n" + " =" * 50)
        print("step 1 - search agent is working ...")
        print("=" * 50)

        search_agent = build_search_agent()
        search_result = search_agent.invoke({
            "messages": [("user", f"Find recent, reliable and detailed information about: {clean_topic}")]
        })
        agent_summary = search_result['messages'][-1].content
        state["search_results"] = agent_summary

        # Extract structured sources from search trajectory
        sources = _extract_sources_from_agent_result(search_result, clean_topic)
        state["sources"] = sources
        print("\n Discovered sources: ", len(sources))

        # Step 2 - Reader agent
        print("\n" + " =" * 50)
        print("step 2 - Reader agent is scraping top resources ...")
        print("=" * 50)

        reader_agent = build_reader_agent()
        candidate_summary = "\n".join([f"- [{s['title']}]({s['url']}): {s.get('snippet', '')[:150]}" for s in sources[:3]])
        reader_prompt = (
            f"Topic: {clean_topic}\n\n"
            f"Here are the verified candidate URLs discovered from search:\n{candidate_summary}\n\n"
            f"Select the most authoritative URL and scrape it for deeper content."
        ) if candidate_summary else f"Search Results:\n{state['search_results'][:800]}"

        reader_result = reader_agent.invoke({
            "messages": [("user", reader_prompt)]
        })
        reader_text = reader_result['messages'][-1].content

        scraped_text, updated_sources = _perform_scraping(sources, reader_text)
        state['scraped_content'] = scraped_text
        state['sources'] = updated_sources
        print("\nscraped content: \n", state['scraped_content'][:300])

        # Step 3 - Writer chain
        print("\n" + " =" * 50)
        print("step 3 - Writer is drafting the report ...")
        print("=" * 50)

        sources_registry_items = []
        for i, s in enumerate(state["sources"], 1):
            item_text = f"[{i}] Title: {s.get('title', 'Unknown')}\n    URL: {s.get('url', '')}\n    Status: {s.get('status', 'discovered')}"
            snippet = s.get("snippet", "").strip()
            if snippet:
                item_text += f"\n    Retrieved Evidence: {snippet}"
            sources_registry_items.append(item_text)

        sources_registry = "\n\n".join(sources_registry_items) if sources_registry_items else "No external web sources were discovered."

        research_combined = (
            f"==================================================\n"
            f"VERIFIED DISCOVERED SOURCES & URLS (CITE STRICTLY BY NUMBER [N]):\n"
            f"{sources_registry}\n"
            f"==================================================\n\n"
            f"SEARCH AGENT FINDINGS:\n{state['search_results']}\n\n"
            f"PRIMARY SOURCE SCRAPED CONTENT:\n{state['scraped_content']}"
        )

        raw_report = writer_chain.invoke({
            "topic": clean_topic,
            "research": research_combined
        })

        normalized_report, citation_meta = validate_and_normalize_citations(raw_report, state["sources"])
        state["report"] = normalized_report
        print("\n Final Report\n", state['report'][:300])

        # Step 4 - Critic chain
        print("\n" + " =" * 50)
        print("step 4 - critic is reviewing the report ")
        print("=" * 50)

        state["feedback"] = critic_chain.invoke({
            "report": state['report']
        })
        print("\n critic report \n", state['feedback'])

        state["status"] = "completed"
        state["metadata"] = {
            "sources": state["sources"],
            "sources_count": len(state["sources"]),
            "citations": citation_meta,
        }
        save_research_sync(state)
        return state

    except Exception as e:
        state["status"] = "failed"
        state["metadata"] = {"error": str(e), "sources": state.get("sources", [])}
        try:
            save_research_sync(state)
        except Exception:
            pass
        raise RuntimeError(f"Research pipeline execution failed: {str(e)}") from e


async def run_research_pipeline_async(
    topic: str,
    on_progress: Optional[Callable[[str, dict], Any]] = None,
    run_id: Optional[str] = None
) -> dict:
    """
    Executes the 4-step multi-agent research pipeline asynchronously.
    Emits granular progress events for streaming interfaces.
    Saves running, completed, or failed runs to SQLite database and returns the result state.
    """
    if not topic or not isinstance(topic, str) or not topic.strip():
        raise ValueError("Research topic cannot be empty.")

    clean_topic = topic.strip()
    run_id = run_id or str(uuid.uuid4())
    state = {
        "id": run_id,
        "topic": clean_topic,
        "status": "running",
        "search_results": "",
        "scraped_content": "",
        "report": "",
        "feedback": "",
        "sources": [],
    }

    try:
        # Persist initial running state
        await save_research(state)
        await _emit_progress(on_progress, "started", {
            "stage": "started",
            "id": run_id,
            "topic": clean_topic,
            "message": "Research pipeline initialized."
        })

        # Step 1 - Search agent
        await _emit_progress(on_progress, "searching", {
            "stage": "searching",
            "id": run_id,
            "message": "Search agent is searching the web for relevant sources..."
        })
        search_agent = build_search_agent()
        search_result = await search_agent.ainvoke({
            "messages": [("user", f"Find recent, reliable and detailed information about: {clean_topic}")]
        })
        agent_summary = search_result['messages'][-1].content
        state["search_results"] = agent_summary

        # Extract structured sources from search trajectory
        sources = _extract_sources_from_agent_result(search_result, clean_topic)
        state["sources"] = sources

        # Step 2 - Reader agent
        await _emit_progress(on_progress, "reading", {
            "stage": "reading",
            "id": run_id,
            "message": f"Reader agent is scraping and analyzing key resources ({len(sources)} sources discovered)..."
        })
        reader_agent = build_reader_agent()
        candidate_summary = "\n".join([f"- [{s['title']}]({s['url']}): {s.get('snippet', '')[:150]}" for s in sources[:3]])
        reader_prompt = (
            f"Topic: {clean_topic}\n\n"
            f"Here are the verified candidate URLs discovered from search:\n{candidate_summary}\n\n"
            f"Select the most authoritative URL and scrape it for deeper content."
        ) if candidate_summary else f"Search Results:\n{state['search_results'][:800]}"

        reader_result = await reader_agent.ainvoke({
            "messages": [("user", reader_prompt)]
        })
        reader_text = reader_result['messages'][-1].content

        scraped_text, updated_sources = _perform_scraping(sources, reader_text)
        state['scraped_content'] = scraped_text
        state['sources'] = updated_sources

        # Step 3 - Writer chain
        await _emit_progress(on_progress, "writing", {
            "stage": "writing",
            "id": run_id,
            "message": "Writer agent is synthesizing information and drafting the report with citations..."
        })

        sources_registry_items = []
        for i, s in enumerate(state["sources"], 1):
            item_text = f"[{i}] Title: {s.get('title', 'Unknown')}\n    URL: {s.get('url', '')}\n    Status: {s.get('status', 'discovered')}"
            snippet = s.get("snippet", "").strip()
            if snippet:
                item_text += f"\n    Retrieved Evidence: {snippet}"
            sources_registry_items.append(item_text)

        sources_registry = "\n\n".join(sources_registry_items) if sources_registry_items else "No external web sources were discovered."

        research_combined = (
            f"==================================================\n"
            f"VERIFIED DISCOVERED SOURCES & URLS (CITE STRICTLY BY NUMBER [N]):\n"
            f"{sources_registry}\n"
            f"==================================================\n\n"
            f"SEARCH AGENT FINDINGS:\n{state['search_results']}\n\n"
            f"PRIMARY SOURCE SCRAPED CONTENT:\n{state['scraped_content']}"
        )

        raw_report = await writer_chain.ainvoke({
            "topic": clean_topic,
            "research": research_combined
        })

        normalized_report, citation_meta = validate_and_normalize_citations(raw_report, state["sources"])
        state["report"] = normalized_report

        # Step 4 - Critic chain
        await _emit_progress(on_progress, "reviewing", {
            "stage": "reviewing",
            "id": run_id,
            "message": "Critic agent is evaluating report quality, citations, and evidence..."
        })
        state["feedback"] = await critic_chain.ainvoke({
            "report": state['report']
        })

        state["status"] = "completed"
        state["metadata"] = {
            "sources": state["sources"],
            "sources_count": len(state["sources"]),
            "citations": citation_meta,
        }
        await save_research(state)
        await _emit_progress(on_progress, "completed", {
            "stage": "completed",
            "id": run_id,
            "topic": clean_topic,
            "report": state["report"],
            "feedback": state["feedback"],
            "sources": state["sources"],
        })
        return state

    except Exception as e:
        state["status"] = "failed"
        state["metadata"] = {"error": str(e), "sources": state.get("sources", [])}
        try:
            await save_research(state)
        except Exception:
            pass
        await _emit_progress(on_progress, "failed", {
            "stage": "failed",
            "id": run_id,
            "error": str(e)
        })
        raise RuntimeError(f"Research pipeline execution failed: {str(e)}") from e
