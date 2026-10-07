import httpx

from app.tools.wiki_tools import WikiTools


def make_tools(handler):
    calls = []

    def recording(request: httpx.Request):
        calls.append(request)
        return handler(request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(recording), headers={"User-Agent": "FanDesk-Test/1.0"})
    return WikiTools("FanDesk-Test/1.0", client=client), calls


async def test_search_returns_titles_and_strips_markup():
    def handler(request):
        assert request.url.params["srsearch"] == "Vikram 2022 film"
        return httpx.Response(200, json={"query": {"search": [
            {"title": "Vikram (2022 film)", "snippet": '<span class="searchmatch">Vikram</span> is a 2022 film'},
            {"title": "Vikram (actor)", "snippet": "Indian actor"},
        ]}})

    tools, calls = make_tools(handler)
    out = await tools.search_wikipedia({"query": "Vikram 2022 film"})
    assert out.ok and out.summary == "2 results"
    assert "Vikram (2022 film): Vikram is a 2022 film" in out.text
    assert calls[0].headers["User-Agent"] == "FanDesk-Test/1.0"


async def test_summary_wraps_page_text_as_data_and_caches():
    def handler(request):
        assert request.url.path.endswith("/Vikram_(2022_film)")
        return httpx.Response(200, json={"title": "Vikram (2022 film)", "extract": "Directed by Lokesh Kanagaraj."})

    tools, calls = make_tools(handler)
    first = await tools.get_page_summary({"title": "Vikram (2022 film)"})
    second = await tools.get_page_summary({"title": "Vikram (2022 film)"})
    assert first.text.startswith('<page title="Vikram (2022 film)">')
    assert first.extra == {"title": "Vikram (2022 film)"}
    assert second.text == first.text
    assert len(calls) == 1  # second lookup came from the 24-hour cache


async def test_missing_page_is_a_clean_tool_error():
    tools, _ = make_tools(lambda request: httpx.Response(404, json={}))
    out = await tools.get_page_summary({"title": "No Such Film"})
    assert not out.ok
    assert out.summary == "Page not found"


async def test_network_failure_does_not_raise():
    def handler(request):
        raise httpx.ConnectError("offline")

    tools, _ = make_tools(handler)
    out = await tools.search_wikipedia({"query": "anything"})
    assert not out.ok
    assert out.text.startswith("ERROR")
