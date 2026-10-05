"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import suggest_outfit, create_fit_card
from generate import ModelUnavailable
from mcp_client import MCPError, call_tool


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "steps": [],                 # the steps that have run, in order
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── query parsing ─────────────────────────────────────────────────────────────

# "under $30", "below 30", "max $30", "up to 30", "less than $30", "$30 or less"
_PRICE_WORDED = re.compile(
    r"\b(?:under|below|less\s+than|max(?:imum)?|up\s+to|at\s+most|no\s+more\s+than)"
    r"\s*\$?\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_PRICE_BARE = re.compile(r"\$\s*(\d+(?:\.\d+)?)(?:\s+or\s+(?:less|under))?", re.IGNORECASE)

# "size M", "in size US 8", "size 8.5", "size medium"
_SIZE_WORDED = re.compile(
    r"\b(?:in\s+)?(?:a\s+)?size\s+(?:us\s+)?([a-z0-9]+(?:\.\d+)?)", re.IGNORECASE
)
# A size on its own, with no "size" in front: "XL", "W30". Capitals only, so
# the "s" and "m" inside ordinary words are never read as sizes.
_SIZE_BARE = re.compile(r"\b(XXS|XS|S|M|L|XL|XXL|W\d{2})\b")

_SIZE_WORDS = {
    "small": "S", "medium": "M", "large": "L",
    "xsmall": "XS", "xlarge": "XL",
}


def parse_query(query: str) -> dict:
    """
    Pull a description, a size and a price ceiling out of a plain-language
    query, with regular expressions. No model call.

    "vintage graphic tee under $30, size M"
        → {"description": "vintage graphic tee", "size": "M", "max_price": 30.0}

    `size` and `max_price` are None when the query doesn't give one.
    """
    rest = query
    max_price = None
    size = None

    match = _PRICE_WORDED.search(rest) or _PRICE_BARE.search(rest)
    if match:
        max_price = float(match.group(1))
        rest = rest[: match.start()] + " " + rest[match.end():]

    match = _SIZE_WORDED.search(rest) or _SIZE_BARE.search(rest)
    if match:
        size = _SIZE_WORDS.get(match.group(1).lower(), match.group(1).upper())
        rest = rest[: match.start()] + " " + rest[match.end():]

    description = re.sub(r"[,;.!?]+", " ", rest)
    description = re.sub(r"\s+", " ", description).strip()

    return {"description": description, "size": size, "max_price": max_price}


def _nothing_found_message(parsed: dict) -> str:
    """What to tell the user when the search came back empty: what to change."""
    looked_for = f"'{parsed['description']}'" if parsed["description"] else "that"
    if parsed["size"]:
        looked_for += f" in size {parsed['size']}"
    if parsed["max_price"] is not None:
        looked_for += f" under ${parsed['max_price']:g}"

    changes = []
    if parsed["size"]:
        changes.append(f"dropping the size ({parsed['size']})")
    if parsed["max_price"] is not None:
        changes.append(f"raising the ${parsed['max_price']:g} price ceiling")
    changes.append("using fewer or more general words, like 'jacket' or 'tee'")

    if len(changes) > 1:
        changes[-1] = "or " + changes[-1]
    joiner = ", " if len(changes) > 2 else " "
    return f"No listings matched {looked_for}. Try {joiner.join(changes)}."


def _item_label(item: dict) -> str:
    """A listing as the trace shows it: the id first, so two runs can be compared."""
    return f"{item['id']} {item['title']}"


def _model_unavailable(session: dict, step_name: str, exc: Exception) -> dict:
    """End the run with a message, not a stack trace, when the model can't be reached."""
    item = session["selected_item"]
    trace.step(step_name, inputs=f"new_item={_item_label(item)}",
               note=f"model unavailable, stopping: {str(exc).splitlines()[0]}")
    session["error"] = (
        f"Found {item['title']} (${item['price']:g} on {item['platform']}), but "
        f"the model couldn't be reached to style it. Check GEMINI_API_KEY in "
        f"your .env and try again."
    )
    return session


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    Built to the branch rule in the README's Planning Loop section. The steps:

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)
    count = 0

    # Each time round, look at what the session holds and run the one step it
    # is missing. Every result goes into the session before the next step
    # reads it back out.
    while True:
        count += 1
        trace.check_iterations(count)
        done = session["steps"]

        if "parse_query" not in done:
            session["parsed"] = parse_query(query)
            done.append("parse_query")
            trace.step("parse_query", inputs=query, returned=str(session["parsed"]))

        elif "search_listings" not in done:
            parsed = session["parsed"]
            # search_listings lives behind the MCP server now. Same inputs,
            # same list of listing dicts back.
            try:
                session["search_results"] = call_tool("search_listings", {
                    "description": parsed["description"],
                    "size": parsed["size"],
                    "max_price": parsed["max_price"],
                })
            except MCPError as exc:
                trace.step("search_listings (via MCP)", inputs=str(parsed),
                           note=f"MCP call failed, stopping: {exc}")
                session["error"] = (
                    "The listing search couldn't be reached, so nothing was "
                    "searched. Check that `python mcp_server.py` starts on its "
                    "own, then try again."
                )
                return session
            done.append("search_listings")

            # THE BRANCH. Nothing came back, so there is nothing to style:
            # say what to change and stop before suggest_outfit.
            empty = not session["search_results"]
            trace.step(
                "search_listings (via MCP)",
                inputs=str(parsed),
                returned=session["search_results"],
                note="branch: empty, stopping before suggest_outfit" if empty
                else "branch: results found, going on to select an item",
            )
            if empty:
                session["error"] = _nothing_found_message(parsed)
                return session

        elif session["selected_item"] is None:
            session["selected_item"] = session["search_results"][0]
            done.append("select_item")
            trace.step(
                "select_item",
                inputs=f"search_results[0] of {len(session['search_results'])}",
                returned=_item_label(session["selected_item"]),
            )

        elif session["outfit_suggestion"] is None:
            try:
                session["outfit_suggestion"] = suggest_outfit(
                    session["selected_item"], session["wardrobe"]
                )
            except ModelUnavailable as exc:
                return _model_unavailable(session, "suggest_outfit", exc)
            done.append("suggest_outfit")
            trace.step(
                "suggest_outfit",
                inputs=f"new_item={_item_label(session['selected_item'])}, "
                       f"wardrobe={len(session['wardrobe'].get('items') or [])} items",
                returned=session["outfit_suggestion"],
            )

        elif session["fit_card"] is None:
            try:
                session["fit_card"] = create_fit_card(
                    session["outfit_suggestion"], session["selected_item"]
                )
            except ModelUnavailable as exc:
                return _model_unavailable(session, "create_fit_card", exc)
            done.append("create_fit_card")
            trace.step(
                "create_fit_card",
                inputs=f"new_item={_item_label(session['selected_item'])}, "
                       f"outfit={len(session['outfit_suggestion'])} chars",
                returned=session["fit_card"],
            )

        else:
            return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
