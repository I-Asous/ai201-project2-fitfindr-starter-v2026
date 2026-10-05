"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────

# Words that say nothing about the item. Left in, "a" and "in" would score
# against half the descriptions in the data.
_STOPWORDS = {
    "a", "an", "and", "the", "for", "in", "on", "of", "with", "to", "or",
    "under", "over", "below", "size", "sized", "looking", "want", "need",
    "some", "any", "me", "my", "i", "im", "find", "something",
}


def _words(text: str) -> list[str]:
    """Lowercase words and numbers. "8.5" stays one token; "S/M" becomes two."""
    return re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text.lower())


def _size_matches(wanted: str, listing_size: str) -> bool:
    """
    True when every token of the size asked for is a whole token of the
    listing's size. "M" matches "S/M" and not "XL"; "8" matches "US 8" and
    not "US 8.5". Never a substring test.
    """
    wanted_tokens = _words(wanted)
    return bool(wanted_tokens) and set(wanted_tokens) <= set(_words(listing_size))


def _keywords(text: str) -> set[str]:
    """
    Words to score on, with a plural "s" dropped so "sneaker" finds "sneakers"
    and "top" finds the "tops" category. Short tokens like "90s" are left alone.
    """
    return {
        w[:-1] if len(w) > 3 and w.endswith("s") else w
        for w in _words(text)
        if w not in _STOPWORDS
    }


def _searchable_words(listing: dict) -> set[str]:
    parts = [
        listing["title"],
        listing["description"],
        listing["category"],
        " ".join(listing["style_tags"]),
        " ".join(listing["colors"]),
        listing["brand"] or "",  # None for most listings
    ]
    return _keywords(" ".join(parts))


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    keywords = _keywords(description)

    scored = []
    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None and not _size_matches(size, listing["size"]):
            continue

        score = len(keywords & _searchable_words(listing))
        if score > 0:
            # Keywords in the title break ties: the loop takes the first
            # result, so "Graphic Tee" should beat a listing merely tagged it.
            in_title = len(keywords & _keywords(listing["title"]))
            scored.append((score, in_title, listing))

    # sort() is stable, so anything still tied stays in data-file order.
    scored.sort(key=lambda entry: entry[:2], reverse=True)
    return [listing for *_, listing in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def _describe_item(item: dict) -> str:
    """One listing as prompt text. Brand is left out when there isn't one."""
    lines = [
        f"Title: {item['title']}",
        f"Category: {item['category']}",
        f"Colors: {', '.join(item['colors'])}",
        f"Style: {', '.join(item['style_tags'])}",
        f"Size: {item['size']}",
        f"Condition: {item['condition']}",
        f"Price: ${item['price']:g}",
        f"Platform: {item['platform']}",
        f"Description: {item['description']}",
    ]
    if item.get("brand"):
        lines.insert(1, f"Brand: {item['brand']}")
    return "\n".join(lines)


def _describe_wardrobe(items: list[dict]) -> str:
    lines = []
    for piece in items:
        line = (
            f"- {piece['name']} ({piece['category']}; "
            f"{', '.join(piece['colors'])}; {', '.join(piece['style_tags'])})"
        )
        if piece.get("notes"):
            line += f" — {piece['notes']}"
        lines.append(line)
    return "\n".join(lines)


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    items = wardrobe.get("items") or []

    if not items:
        system = (
            "You are a thrift stylist. The user has not saved any wardrobe, so "
            "you do not know what they own. Give general styling advice only: "
            "the kinds of pieces and colors that go with the item. Never say or "
            "imply that the user owns a particular piece. Plain text, no "
            "markdown, under 120 words."
        )
        prompt = (
            "I'm thinking of buying this thrifted item:\n\n"
            f"{_describe_item(new_item)}\n\n"
            "Suggest one or two ways to style it."
        )
    else:
        system = (
            "You are a thrift stylist. Build outfits from the new item plus "
            "pieces the user already owns. Use only pieces from the wardrobe "
            "list, and write each piece's name exactly as it appears in the "
            "list. Do not invent pieces the user does not own. Plain text, no "
            "markdown, under 120 words."
        )
        prompt = (
            "I'm thinking of buying this thrifted item:\n\n"
            f"{_describe_item(new_item)}\n\n"
            "Here is what I already own:\n\n"
            f"{_describe_wardrobe(items)}\n\n"
            "Suggest one or two outfits that combine the new item with pieces "
            "from my wardrobe."
        )

    return generate(prompt, system=system).strip()


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

NO_OUTFIT_MESSAGE = "No fit card: there was no outfit suggestion to write a caption from."


def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit or not outfit.strip():
        return NO_OUTFIT_MESSAGE

    system = (
        "You write short social media captions about thrift finds. Sound like "
        "a real person posting, not a product description. Write two to four "
        "sentences. Mention the item, its price and the platform it came from "
        "exactly once each, and be specific about the vibe. Write the price "
        "as a dollar figure, like $24, never in words. Plain text only: "
        "no hashtags, no markdown, no quotation marks around the caption."
    )
    prompt = (
        "The find:\n\n"
        f"{_describe_item(new_item)}\n\n"
        "How I'm going to wear it:\n\n"
        f"{outfit.strip()}\n\n"
        "Write the caption."
    )

    return generate(prompt, system=system).strip()
