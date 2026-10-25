import uuid
from src.agents.agents import build_search_agent, build_reader_agent, writer_chain, critic_chain
from src.db.database import save_research_sync, save_research


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
        state["search_results"] = search_result['messages'][-1].content
        print("\n search result ", state['search_results'])

        # Step 2 - Reader agent
        print("\n" + " =" * 50)
        print("step 2 - Reader agent is scraping top resources ...")
        print("=" * 50)

        reader_agent = build_reader_agent()
        reader_result = reader_agent.invoke({
            "messages": [("user",
                f"Based on the following search results about '{clean_topic}', "
                f"pick the most relevant URL and scrape it for deeper content.\n\n"
                f"Search Results:\n{state['search_results'][:800]}"
            )]
        })
        state['scraped_content'] = reader_result['messages'][-1].content
        print("\nscraped content: \n", state['scraped_content'])

        # Step 3 - Writer chain
        print("\n" + " =" * 50)
        print("step 3 - Writer is drafting the report ...")
        print("=" * 50)

        research_combined = (
            f"SEARCH RESULTS : \n {state['search_results']} \n\n"
            f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
        )

        state["report"] = writer_chain.invoke({
            "topic": clean_topic,
            "research": research_combined
        })
        print("\n Final Report\n", state['report'])

        # Step 4 - Critic chain
        print("\n" + " =" * 50)
        print("step 4 - critic is reviewing the report ")
        print("=" * 50)

        state["feedback"] = critic_chain.invoke({
            "report": state['report']
        })
        print("\n critic report \n", state['feedback'])

        state["status"] = "completed"
        save_research_sync(state)
        return state

    except Exception as e:
        state["status"] = "failed"
        state["metadata"] = {"error": str(e)}
        try:
            save_research_sync(state)
        except Exception:
            pass
        raise RuntimeError(f"Research pipeline execution failed: {str(e)}") from e


async def run_research_pipeline_async(topic: str) -> dict:
    """
    Executes the 4-step multi-agent research pipeline asynchronously.
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
    }

    try:
        search_agent = build_search_agent()
        search_result = await search_agent.ainvoke({
            "messages": [("user", f"Find recent, reliable and detailed information about: {clean_topic}")]
        })
        state["search_results"] = search_result['messages'][-1].content

        reader_agent = build_reader_agent()
        reader_result = await reader_agent.ainvoke({
            "messages": [("user",
                f"Based on the following search results about '{clean_topic}', "
                f"pick the most relevant URL and scrape it for deeper content.\n\n"
                f"Search Results:\n{state['search_results'][:800]}"
            )]
        })
        state['scraped_content'] = reader_result['messages'][-1].content

        research_combined = (
            f"SEARCH RESULTS : \n {state['search_results']} \n\n"
            f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
        )

        state["report"] = await writer_chain.ainvoke({
            "topic": clean_topic,
            "research": research_combined
        })

        state["feedback"] = await critic_chain.ainvoke({
            "report": state['report']
        })

        state["status"] = "completed"
        await save_research(state)
        return state

    except Exception as e:
        state["status"] = "failed"
        state["metadata"] = {"error": str(e)}
        try:
            await save_research(state)
        except Exception:
            pass
        raise RuntimeError(f"Research pipeline execution failed: {str(e)}") from e
