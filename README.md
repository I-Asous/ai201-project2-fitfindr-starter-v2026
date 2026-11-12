# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr takes a plain-language request for a thrifted piece, such as "vintage graphic tee under $30" or "90s track jacket in size M", and searches 40 secondhand listings from Depop, Poshmark and thredUp for the best match. It then suggests one or two outfits that pair that item with pieces the user already owns, or gives general styling advice if they have no wardrobe saved. Last, it writes a short caption about the find — the fit card — that mentions the item, its price and the platform. If nothing matches the request, it stops after the search and tells the user what to change, such as dropping the size or raising the price ceiling.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters the 40 listings in `data/listings.json` by price and size, then ranks what is left by how many of the description's keywords appear in each listing's `title`, `description`, `category`, `style_tags`, `colors` and `brand`. Ties go to the listing with more of the keywords in its `title`. It does not call the model.
- **Inputs:** 
  - `description` (str) — keywords for what the user wants, e.g. `"vintage graphic tee"`. Matched case-insensitively as whole words, ignoring filler words ("a", "in", "under", "size") and a plural "s", so "sneaker" finds "sneakers".
  - `size` (str or None) — a size to filter by; `None` skips the size filter. A listing matches when the requested size equals one whole token of its `size` field, case-insensitively, after splitting that field on spaces, slashes and brackets. So `"M"` matches `"M"`, `"S/M"` and `"M/L"` but not `"XL"`; `"8"` matches `"US 8"` but not `"US 8.5"`; `"W30"` matches `"W30 L30"`. It is never a substring test.
  - `max_price` (float or None) — price ceiling in dollars, inclusive; `None` skips the price filter.
- **Returns:** A `list[dict]` of at most `config.SEARCH_RESULT_LIMIT` (10) listings, highest keyword score first. Each dict is a whole listing exactly as it is in the data file: `id` (str), `title` (str), `description` (str), `category` (str), `style_tags` (list of str), `size` (str), `condition` (str), `price` (float), `colors` (list of str), `brand` (str or None — None on 32 of the 40), `platform` (str). Listings with a keyword score of zero are left out.
- **When it has nothing:** Returns an empty list, `[]` — not `None`, and it does not raise. This is what the planning loop branches on.

### `suggest_outfit`

- **What it does:** Asks the model, through `generate()`, for one or two outfits built around a thrifted item, naming pieces the user already owns when they have any.
- **Inputs:**
  - `new_item` (dict) — one listing dict, in the shape `search_listings` returns. `brand` may be `None`.
  - `wardrobe` (dict) — `{"items": [...]}`, where each item has `id` (str), `name` (str), `category` (str), `colors` (list of str), `style_tags` (list of str) and `notes` (str or None). `items` may be an empty list.
- **Returns:** A non-empty `str` of plain text describing one or two outfits. With a non-empty wardrobe, each outfit names at least one wardrobe piece by its `name`.
- **When it has nothing:** If `wardrobe["items"]` is empty, it still calls the model and returns a non-empty `str` of general styling advice for the item (what kinds of pieces and colors go with it), without naming any owned pieces. It never returns `""` and never raises for an empty wardrobe.

### `create_fit_card`

- **What it does:** Asks the model, through `generate()`, for a short caption the user could post about the find, written like a real post rather than a product description.
- **Inputs:**
  - `outfit` (str) — the outfit text returned by `suggest_outfit`.
  - `new_item` (dict) — the listing dict for the item, the same one passed to `suggest_outfit`.
- **Returns:** A `str` caption of two to four sentences that mentions the item, its `price` and its `platform` once each. It varies from run to run and between items, because `config.TEMPERATURE` is 0.9.
- **When it has nothing:** If `outfit` is empty or only whitespace, it does not call the model and returns the fixed message `"No fit card: there was no outfit suggestion to write a caption from."` It does not raise.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` saying what the user could change (drop the size, raise the price ceiling, or use fewer keywords) and return the session without calling `suggest_outfit` or `create_fit_card`. Otherwise take the first result as `session["selected_item"]` and go on to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** 
With regular expressions, in `agent.py::parse_query`. No model call. It takes the price ceiling first ("under $30", "below 30", "max $30", or a bare "$30"), then the size ("size M", "in size US 8", "size medium", or a capitalised size on its own such as "XL" or "W29"), and whatever text is left becomes the description. A query with no size or no price gives `None` for that field, which turns that filter off in `search_listings`.

**What moves through the session:** 
Each time round the loop, `run_agent` looks at the session, runs the one step it is missing, and writes the result back before the next step reads it. In order:

1. `query` and `wardrobe` — set when the session is created.
2. `parsed` — `{"description", "size", "max_price"}` from `parse_query(query)`.
3. `search_results` — the list `search_listings` returned for `parsed`. If it is empty, `error` is set and the run ends here.
4. `selected_item` — `search_results[0]`.
5. `outfit_suggestion` — what `suggest_outfit(selected_item, wardrobe)` returned.
6. `fit_card` — what `create_fit_card(outfit_suggestion, selected_item)` returned.

`steps` records the name of each step as it finishes, so a finished session shows how far the run got. `error` stays `None` unless the run ended early. The loop calls `trace.check_iterations` every time round, so it cannot run past `MAX_ITERATIONS`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Graphic Tee — 2003 Tour Bootleg Style — $24.0 on depop

  Outfit:   Outfit 1: Channel a grunge streetwear vibe by pairing the Graphic Tee — 2003 Tour Bootleg Style with Baggy straight-leg jeans, dark wash. Add the Black combat boots and the Black crossbody bag to complete the look. 

Outfit 2: For an edgy layered style, wear the Graphic Tee — 2003 Tour Bootleg Style tucked into Wide-leg khaki trousers. Layer the Vintage black denim jacket on top, and finish with Chunky white sneakers.

  Fit card: Scored this sick faded graphic tee on depop for only $24 and the worn-in cotton feels amazing. It has that ultimate boxy grunge look that makes every streetwear fit effortless. Can not wait to style it with baggy denim and beat-up boots.

1 model calls this session, 1 served from cache, 294 prompt + 54 output tokens
```

And the other side of the branch, a query nothing matches:

```
$ python app.py ask 'designer ballgown size XXS under $5'

  No listings matched 'designer ballgown' in size XXS under $5. Try dropping the size (XXS), raising the $5 price ceiling, or using fewer or more general words, like 'jacket' or 'tee'.

0 model calls this session
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}, {'id': 'lst_012', 'title': 'Oversized Crewneck Sweatshirt — Vintage Navy', 'description': 'Perfectly faded navy crewneck. Genuinely vintage — not manufactured distressed. Ribbed cuffs and hem. No graphics, clean.', 'category': 'tops', 'style_tags': ['vintage', 'basics', 'oversized', 'classic'], 'size': 'XL (fits oversized)', 'condition': 'good', 'price': 20.0, 'colors': ['navy'], 'brand': None, 'platform': 'thredUp'}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Outfit one combines the Vintage Levi's 501 Jeans — Medium Wash with the White ribbed tank top, Vintage black denim jacket, and Chunky white sneakers. Add the Black crossbody bag for an easy streetwear look. 

Outfit two pairs the Vintage Levi's 501 Jeans — Medium Wash with the Oversized grey crewneck sweatshirt layered underneath the Vintage black denim jacket. Complete this cozy, classic outfit with the Black combat boots and the Brown leather belt.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Scored these vintage Levi's 501 jeans on depop for $38 and they have the ultimate relaxed streetwear vibe. The knee fading makes them look like they have real history already. I cannot wait to style them with a simple pair of fresh white sneakers.
```

**The same three with nothing to give**

```
$ python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
[]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_empty_wardrobe()))"
Grab these classic Levi 501s for sure. For an effortless casual look, pair them with a slightly oversized graphic t-shirt tucked in, a vintage leather belt, and retro white sneakers or chunky loafers. Layer with an unbuttoned flannel or a distressed denim jacket for a cool double-denim moment. Alternatively, dress them up by styling them with a fitted black ribbed turtleneck, a tailored double-breasted blazer in houndstooth or camel, and pointed-toe leather boots. Add a structured secondhand handbag and minimal gold jewelry to elevate the vintage denim into something chic and timeless.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('   ', load_listings()[0]))"
No fit card: there was no outfit suggestion to write a caption from.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for: To clarify the task at hand and what I should do, look out for and keep in mind
- *What came back: An easy to understand approach of how to complete the project and what to consider as I work through it
- *What I changed: My approach to how I manuever through this project rather than just doing im supposed but being mindful on the lesson its planning*

**Moment 2**

- *What I asked for:* I asked Claude to build the planning loop in `agent.py::run_agent` from my branch rule and run both paths.
- *What came back:* A working loop, but in the empty-wardrobe test run the fit card for the $45 track jacket read "for forty five dollars". My criterion 4 checks for the price as a number, so that card would have failed it.
- *What I changed:* The system prompt in `tools.py::create_fit_card` now says to write the price as a dollar figure, like $24, never in words. Every completed card in the eval runs after that had the price as a figure.

**Moment 3 (unit 4)**

- *What I asked for:* I asked Claude to trigger the three failures again (empty search, empty wardrobe, a bad key) and read each message the way a user who can't see the code would.
- *What came back:* All three were handled, but it pointed out that the model-unavailable message ended "Check GEMINI_API_KEY in your .env and try again" whatever the cause. My first after run had 13 tries fail on the provider's 503 error, and every one of them told the user to check a key that was fine.
- *What I changed:* `agent.py::_model_unavailable` now passes on the reason `generate.py` already works out, so a rejected key, a dropped connection and a provider error each give a different next step.

**Moment 4 (unit 4)**

- *What I asked for:* I asked Claude to score every try in both saved run logs again, without looking at my verdicts first, and compare.
- *What came back:* No verdict changed. It did find two gaps in the write-up: the Run Log had pasted output for criterion 3 only, and my criterion 3 verdict rested on a title in the trace where the criterion asks for an id. One sentence it first drafted for the README said four of the five sneaker cards opened the same way; the run log shows three, and it corrected that before it went in.
- *What I changed:* The README now has real output for all five criteria, the second-pass tables, and a re-run of the search showing `lst_004` is the first result by id. I kept my targets as written, including criterion 5, which the same pass showed was probably set too low.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The item that was found is the item that was styled | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card is a postable caption about this item | 4 of 5, and 5 different first sentences | PASS | PASS | PASS | PASS | PASS | MET (5/5, 5 different) |
| 5. Outfits use pieces the user actually owns | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Each criterion was scored on its own scenario in `scenarios.py`:

| # | Scenario query | Wardrobe |
|---|---|---|
| 1 | `vintage graphic tee under $30` | example |
| 2 | `designer ballgown size XXS under $5` | example |
| 3 | `90s track jacket in size M` | example |
| 4 | `denim jacket under $50` | example |
| 5 | `platform sneakers size 8` | example |

The run also included one diagnostic scenario that is not one of the five (`denim jacket under $50` with the empty wardrobe). It completed 5 of 5 tries.

The whole run is in `results/run_2026-10-04_2109_before.md`: 6 scenarios, 5 tries each, caching off, temperature 0.9, 50 model calls. It was taken before `search_listings` was moved onto MCP.

**Real output from one try of each criterion**, pasted as text, naming the file and function
that produced it:

Criterion 1, try 1. Produced by `run_eval.py::main` calling `agent.py::run_agent`; the trace lines come from the `trace.step` calls inside `run_agent`.

```
### matching query completes

- Query: `vintage graphic tee under $30`
- Wardrobe: example

**Try 1**

- stopped early: no
- selected_item: Graphic Tee — 2003 Tour Bootleg Style ($24.0, depop)
- search_results: 10

Outfit suggestion:

Outfit 1:
Graphic Tee — 2003 Tour Bootleg Style
Baggy straight-leg jeans, dark wash
Vintage black denim jacket
Black combat boots
Black crossbody bag

Outfit 2:
Graphic Tee — 2003 Tour Bootleg Style
Wide-leg khaki trousers
Brown leather belt
Chunky white sneakers
Black cropped zip hoodie

Fit card:

Scored this perfectly faded 2003 tour bootleg graphic tee on depop for $24. The cotton is already super soft and has that exact broken-in grunge vibe I live for. Can not wait to style this with baggy denim and combat boots for an effortless weekend look.

Trace:

[1] parse_query
      in:  vintage graphic tee under $30
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey, Y2K Baby Tee — Butterfly Print … +7 more
      →    branch: results found, going on to select an item
[3] select_item
      in:  search_results[0] of 10
      out: lst_006 Graphic Tee — 2003 Tour Bootleg Style
[4] suggest_outfit
      in:  new_item=lst_006 Graphic Tee — 2003 Tour Bootleg Style, wardrobe=10 items
      out: Outfit 1: Graphic Tee — 2003 Tour Bootleg Style Baggy straight-leg jeans, dark wash Vintage black denim jacket…
[5] create_fit_card
      in:  new_item=lst_006 Graphic Tee — 2003 Tour Bootleg Style, outfit=288 chars
      out: Scored this perfectly faded 2003 tour bootleg graphic tee on depop for $24. The cotton is already super soft a…
```

Criterion 2, try 1. Same file and function. `fit_card` stays `None` and the trace has two steps, because `run_agent` returns at the empty-search branch.

```
### impossible query stops early

- Query: `designer ballgown size XXS under $5`
- Wardrobe: example

**Try 1**

- stopped early: yes — No listings matched 'designer ballgown' in size XXS under $5. Try dropping the size (XXS), raising the $5 price ceiling, or using fewer or more general words, like 'jacket' or 'tee'.
- selected_item: (none)
- search_results: 0

Trace:

[1] parse_query
      in:  designer ballgown size XXS under $5
      out: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit
```

Criterion 3, try 1. Same file and function.

```
### found item is the styled item

- Query: `90s track jacket in size M`
- Wardrobe: example

**Try 1**

- stopped early: no
- selected_item: 90s Track Jacket — Navy/White Stripe ($45.0, poshmark)
- search_results: 4

Outfit suggestion:

Outfit 1: Sporty Streetwear
Layer your 90s Track Jacket — Navy/White Stripe over the White ribbed tank top. Pair them with your Baggy straight-leg jeans, dark wash secured by the Brown leather belt. Finish the look with your Chunky white sneakers and Black crossbody bag for an effortless 90s athletic vibe.

Outfit 2: Casual Retro
Wear the 90s Track Jacket — Navy/White Stripe zipped up over the White ribbed tank top, paired with your Wide-leg khaki trousers. Complete this relaxed, vintage-inspired outfit using your Chunky white sneakers and Black crossbody bag.

Fit card:

Scored this vintage Champion 90s track jacket on Poshmark and it has the ultimate sporty streetwear vibe. It was a steal at $45 and is going to be my go-to for layering all season long. Can not wait to style this with baggy jeans and chunky sneakers.

Trace:

[1] parse_query
      in:  90s track jacket in size M
      out: {'description': '90s track jacket', 'size': 'M', 'max_price': None}
[2] search_listings
      in:  {'description': '90s track jacket', 'size': 'M', 'max_price': None}
      out: 4 items: 90s Track Jacket — Navy/White Stripe, 90s Leather Bomber — Black, 90s Silk Slip Dress — Floral, Midi Length … +1 more
      →    branch: results found, going on to select an item
[3] select_item
      in:  search_results[0] of 4
      out: lst_004 90s Track Jacket — Navy/White Stripe
[4] suggest_outfit
      in:  new_item=lst_004 90s Track Jacket — Navy/White Stripe, wardrobe=10 items
      out: Outfit 1: Sporty Streetwear Layer your 90s Track Jacket — Navy/White Stripe over the White ribbed tank top. Pa…
[5] create_fit_card
      in:  new_item=lst_004 90s Track Jacket — Navy/White Stripe, outfit=566 chars
      out: Scored this vintage Champion 90s track jacket on Poshmark and it has the ultimate sporty streetwear vibe. It w…
```

Criterion 4, try 1. Same file and function. The fit card text comes from `tools.py::create_fit_card`.

```
### fit card is a postable caption

- Query: `denim jacket under $50`
- Wardrobe: example

**Try 1**

- stopped early: no
- selected_item: Denim Jacket — Light Wash, Cropped ($42.0, poshmark)
- search_results: 7

Outfit suggestion:

Outfit 1:
Denim Jacket — Light Wash, Cropped
White ribbed tank top
Baggy straight-leg jeans, dark wash
Chunky white sneakers
Black crossbody bag

Outfit 2:
Denim Jacket — Light Wash, Cropped
Oversized grey crewneck sweatshirt
Wide-leg khaki trousers
Chunky white sneakers

Fit card:

Scored this vintage Wrangler denim jacket on Poshmark for $42 and the structured shoulders give it the ultimate effortless streetwear vibe. I am obsessed with the light wash and can already tell it is going to be my go-to outerwear piece for throwing over oversized crewnecks all fall.

Trace:

[1] parse_query
      in:  denim jacket under $50
      out: {'description': 'denim jacket', 'size': None, 'max_price': 50.0}
[2] search_listings
      in:  {'description': 'denim jacket', 'size': None, 'max_price': 50.0}
      out: 7 items: Denim Jacket — Light Wash, Cropped, 90s Track Jacket — Navy/White Stripe, High-Waisted Denim Shorts — Cutoff … +4 more
      →    branch: results found, going on to select an item
[3] select_item
      in:  search_results[0] of 7
      out: lst_007 Denim Jacket — Light Wash, Cropped
[4] suggest_outfit
      in:  new_item=lst_007 Denim Jacket — Light Wash, Cropped, wardrobe=10 items
      out: Outfit 1: Denim Jacket — Light Wash, Cropped White ribbed tank top Baggy straight-leg jeans, dark wash Chunky …
[5] create_fit_card
      in:  new_item=lst_007 Denim Jacket — Light Wash, Cropped, outfit=271 chars
      out: Scored this vintage Wrangler denim jacket on Poshmark for $42 and the structured shoulders give it the ultimat…
```

Criterion 5, try 1. Same file and function. The outfit text comes from `tools.py::suggest_outfit`.

```
### outfit uses owned pieces

- Query: `platform sneakers size 8`
- Wardrobe: example

**Try 1**

- stopped early: no
- selected_item: Platform Sneakers — White Chunky Sole ($48.0, poshmark)
- search_results: 1

Outfit suggestion:

Outfit one: Pair your Platform Sneakers — White Chunky Sole with the Baggy straight-leg jeans, dark wash and the White ribbed tank top. Layer the Oversized grey crewneck sweatshirt on top and finish with the Black crossbody bag for an effortless streetwear look.

Outfit two: Style the Platform Sneakers — White Chunky Sole with the Wide-leg khaki trousers and the White ribbed tank top. Throw on the Vintage black denim jacket and accessorize with the Brown leather belt for a cool Y2K-inspired casual outfit.

Fit card:

Found these chunky white platform sneakers on Poshmark for $48 and they have the ultimate late 90s streetwear vibe. The little bit of sole yellowing just makes them look authentically vintage instead of brand new. Can not wait to style these with some baggy dark wash denim and a basic white tank.

Trace:

[1] parse_query
      in:  platform sneakers size 8
      out: {'description': 'platform sneakers', 'size': '8', 'max_price': None}
[2] search_listings
      in:  {'description': 'platform sneakers', 'size': '8', 'max_price': None}
      out: 1 items: Platform Sneakers — White Chunky Sole
      →    branch: results found, going on to select an item
[3] select_item
      in:  search_results[0] of 1
      out: lst_019 Platform Sneakers — White Chunky Sole
[4] suggest_outfit
      in:  new_item=lst_019 Platform Sneakers — White Chunky Sole, wardrobe=10 items
      out: Outfit one: Pair your Platform Sneakers — White Chunky Sole with the Baggy straight-leg jeans, dark wash and t…
[5] create_fit_card
      in:  new_item=lst_019 Platform Sneakers — White Chunky Sole, outfit=510 chars
      out: Found these chunky white platform sneakers on Poshmark for $48 and they have the ultimate late 90s streetwear …
```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
| - | --------- | ------ | ------- | ------------- |
| 1 | A matching query completes all three tools | 4 of 5 | MET (5/5) | A try passes when `session["error"]` is `None`, the trace shows `search_listings`, `suggest_outfit` and `create_fit_card` in that order, and `fit_card` is a non-empty string. All five did; the cards were 234 to 326 characters. |
| 2 | An impossible query stops before the second tool | 5 of 5 | MET (5/5) | A try passes when the trace ends at `search_listings` with `[] (empty)`, there is no `suggest_outfit` step, `fit_card` is `None`, and the message names something to change. All five traces have two steps, and the message says to drop the size (XXS), raise the $5 ceiling, or use more general words. |
| 3 | The item that was found is the item that was styled | 5 of 5 | MET (5/5) | A try passes when the same listing id appears as the `select_item` output and as the `new_item` input of both `suggest_outfit` and `create_fit_card` in the trace, and it is the first search result. All five show `lst_004` in all three places, and "90s Track Jacket — Navy/White Stripe" is the first title in the `search_listings` output. |
| 4 | The fit card is a postable caption about this item | 4 of 5, and 5 different first sentences | MET (5/5, 5 different) | A card passes when it has two to four sentences and contains "42" and "poshmark" (ignoring case). I counted sentences by splitting on ". ", "! " and "? ". The five cards had 2, 2, 3, 3 and 3 sentences, and every one had both facts. No two first sentences were word-for-word the same. |
| 5 | Outfits use pieces the user actually owns | 4 of 5 | MET (5/5) | A try passes when the outfit text contains at least one wardrobe item's `name` exactly (ignoring case) and no piece outside the wardrobe is presented as owned. I searched each outfit for the ten names, then read each one for invented pieces. Each try named six or seven wardrobe pieces exactly, and the only other item mentioned was the sneakers being bought. |

**Diagnoses**

No criterion was missed, so there is no miss to place in a tool, the branch, the session or the model's output. Three things in the output are worth recording anyway, because each one is a way these verdicts could be weaker than they look.

1. **Criterion 4's first-sentence rule passed without showing much variety (model output).** The five first sentences differ, but all five open "Scored this … Wrangler denim jacket on Poshmark for $42 and …". The rule only fails on a word-for-word repeat, so cards that differ by two adjectives count as different. The mechanism is in `tools.py::create_fit_card`: the system prompt asks for the item, price and platform once each, and the model satisfies all three in the opening clause every time, which leaves only the adjectives free to change.

2. **A repeated first sentence did turn up, in a different scenario (model output).** In the criterion 5 scenario, tries 2 and 3 both opened with "Scored these chunky white platform sneakers with major late 90s energy on Poshmark for $48." Criterion 4 was not scored on that scenario, so the verdict stands, but the same rule applied there would have found only 4 different first sentences out of 5. Caching was off, so these were two real answers.

3. **Criterion 3's check on the first search result uses the title, not the id (the trace).** The trace prints search results as titles, so for `search_results[0]` I matched the title, while the other two places show the id. `search_listings` has no model in it and returns the same list every time, so I am confident in the verdict, but it is weaker evidence than the criterion asks for.

Each criterion was run on one query taken from the starter's example list, so 5 of 5 everywhere says these five queries work, not that every phrasing does. Criterion 1's reason predicted misses from phrasings the keyword search can't match, and none of these queries tested that.

**The pattern**

Diagnoses 1 and 2 are one problem, not two. Both are fit cards opening the same way, both come from the same prompt in `tools.py::create_fit_card`, and the same thing shows in every scenario that reached a fit card: the track jacket cards all began "Scored this vintage Champion" or "Just scored this vintage Champion", and three of the five sneaker cards began "Scored these chunky white platform sneakers", with a fourth one letter off ("Score these chunky white platform sneakers"). It is the model's output, caused by the prompt, and it is the only pattern in the run. Nothing went wrong in a tool, the branch or the session on any of the 25 tries.

**Were the targets low?**

Nothing was missed, so this needs a plain answer for each one.

- **Criteria 2 and 3** are at 5 of 5 already and came in at 5 of 5. They cannot be set higher.
- **Criterion 1** is at 4 of 5 and came in at 5 of 5, but I do not think it was low. The allowance was for a model call failing, and that is exactly what happened in the after run, where it scored 2 of 5.
- **Criterion 4** was too easy, and not because of its number. Its second rule ("no two cards have the same first sentence") passed five cards that all opened the same way. That is a criterion measuring the wrong thing, so I revised it in `criteria.md`, with the original left in place above the revision: no two of the 5 cards may begin with the same first five words. The new rule is harder, and the before run misses it with 3 different openings out of 5.
- **Criterion 5** is the one I would tighten next. I set 4 of 5 because I expected the model to paraphrase wardrobe names ("your combat boots") and it never did: every outfit in both runs, 10 of 10, named six or seven pieces exactly and invented none. On this evidence the target should be 5 of 5. I have not changed it, because raising a target after seeing the results is still fitting the target to the results.

**Closing the gap in diagnosis 3**

Criterion 3 asks for the id of `search_results[0]`, and the trace only shows its title. To check that the title is enough, I ran the same search again, both directly and through MCP: `search_listings('90s track jacket', 'M', None)` returns ids `lst_004`, `lst_022`, `lst_013`, `lst_032` in that order, and the four titles are all different. So the first title in the trace can only be `lst_004`, which is the id the other two places show. The verdict stays MET. The trace should still print the id, and that is listed under What's Still Broken.

**Second pass over the scoring**

After the table was filled in, every try in both saved run logs was scored a second time from the output in `results/`, with a short script for the parts that can be counted (trace steps, listing ids, sentence count, price and platform in the card, exact wardrobe names, first five words) and by reading the outfits for the part that can't (a piece presented as owned that is not in the wardrobe). No verdict changed.

Before run, `results/run_2026-10-04_2109_before.md`:

| Criterion | Target | Second pass | What was checked on each try |
| --------- | ------ | ----------- | ---------------------------- |
| 1. A matching query completes all three tools | 4 of 5 | 5/5 | `stopped early: no`, five trace steps in order, a fit card of 234 to 326 characters |
| 2. An impossible query stops before the second tool | 5 of 5 | 5/5 | The trace ends at `search_listings` with `[] (empty)`, there is no `suggest_outfit` step, and the message names the size, the price ceiling and the wording as things to change |
| 3. The item that was found is the item that was styled | 5 of 5 | 5/5 | `lst_004` is the `select_item` output and the `new_item` of both `suggest_outfit` and `create_fit_card`; the first search result's title matches it |
| 4. The fit card is a postable caption about this item | 4 of 5, and 5 different first sentences | 5/5, 5 different | 2, 2, 3, 3 and 3 sentences; every card contains "42" and "Poshmark"; under the revised rule, 3 different five-word openings |
| 5. Outfits use pieces the user actually owns | 4 of 5 | 5/5 | 6 or 7 exact wardrobe names per outfit, and no piece outside the wardrobe presented as owned |

After run, `results/run_2026-10-04_2125_after.md`:

| Criterion | Target | Second pass | What was checked on each try |
| --------- | ------ | ----------- | ---------------------------- |
| 1. A matching query completes all three tools | 4 of 5 | 2/5 (FAIL, FAIL, PASS, FAIL, PASS) | Tries 1 and 2 stopped at `suggest_outfit` and try 4 at `create_fit_card`; tries 3 and 5 have five steps and a fit card |
| 2. An impossible query stops before the second tool | 5 of 5 | 5/5 | Same two-step trace and message as before |
| 3. The item that was found is the item that was styled | 5 of 5 | 5/5 | `lst_004` in all three places on every try |
| 4. The fit card is a postable caption about this item | 4 of 5, and (revised) 5 different first-five-word openings | 5/5 cards, 4 different openings | Three sentences, "42" and "Poshmark" in every card; tries 3 and 4 both begin "I had been hunting for" |
| 5. Outfits use pieces the user actually owns | 4 of 5 | 5/5 | 6 or 7 exact wardrobe names per outfit, and no piece outside the wardrobe presented as owned |

The same pass confirmed the opening counts quoted under The Improvement: the track jacket scenario went from 2 different five-word openings to 5, and the platform sneakers from 3 to 5. It did not close the gap in diagnosis 3: the first search result is still matched by title, because the trace does not print its id.

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```
$ python app.py ask 'vintage graphic tee under $30' --trace
[1] parse_query
      in:  vintage graphic tee under $30
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey, Y2K Baby Tee — Butterfly Print … +7 more
      →    branch: results found, going on to select an item
[3] select_item
      in:  search_results[0] of 10
      out: lst_006 Graphic Tee — 2003 Tour Bootleg Style
[4] suggest_outfit
      in:  new_item=lst_006 Graphic Tee — 2003 Tour Bootleg Style, wardrobe=10 items
      out: Outfit 1: Channel a grunge streetwear vibe by pairing the Graphic Tee — 2003 Tour Bootleg Style with Baggy str…
[5] create_fit_card
      in:  new_item=lst_006 Graphic Tee — 2003 Tour Bootleg Style, outfit=421 chars
      out: I am so excited to wear this vintage style graphic tee tucked into wide leg khaki trousers with a black denim …

  Found:    Graphic Tee — 2003 Tour Bootleg Style — $24.0 on depop

  Outfit:   Outfit 1: Channel a grunge streetwear vibe by pairing the Graphic Tee — 2003 Tour Bootleg Style with Baggy straight-leg jeans, dark wash. Add the Black combat boots and the Black crossbody bag to complete the look. 

Outfit 2: For an edgy layered style, wear the Graphic Tee — 2003 Tour Bootleg Style tucked into Wide-leg khaki trousers. Layer the Vintage black denim jacket on top, and finish with Chunky white sneakers.

  Fit card: I am so excited to wear this vintage style graphic tee tucked into wide leg khaki trousers with a black denim jacket thrown over top. The boxy fit gives it the ultimate grunge streetwear vibe that is so hard to track down. I found it on depop and still cannot believe it only cost $24.

1 model calls this session, 1 served from cache, 332 prompt + 62 output tokens
```

**Empty search**

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit

  No listings matched 'designer ballgown' in size XXS under $5. Try dropping the size (XXS), raising the $5 price ceiling, or using fewer or more general words, like 'jacket' or 'tee'.

0 model calls this session
```

The happy path has five steps and the empty search has two: it ends at `search_listings (via MCP)` with `[] (empty)`, and `suggest_outfit` and `create_fit_card` never run.

**The other two failure modes**

Empty wardrobe. The run completes; `suggest_outfit` receives `wardrobe=0 items` and returns general advice that names no owned pieces:

```
$ python app.py ask 'denim jacket under $50' --empty-wardrobe --trace
(running with an empty wardrobe)
[1] parse_query
      in:  denim jacket under $50
      out: {'description': 'denim jacket', 'size': None, 'max_price': 50.0}
[2] search_listings (via MCP)
      in:  {'description': 'denim jacket', 'size': None, 'max_price': 50.0}
      out: 7 items: Denim Jacket — Light Wash, Cropped, 90s Track Jacket — Navy/White Stripe, High-Waisted Denim Shorts — Cutoff … +4 more
      →    branch: results found, going on to select an item
[3] select_item
      in:  search_results[0] of 7
      out: lst_007 Denim Jacket — Light Wash, Cropped
[4] suggest_outfit
      in:  new_item=lst_007 Denim Jacket — Light Wash, Cropped, wardrobe=0 items
      out: That vintage Wrangler jacket is a fantastic find for any wardrobe. For a classic casual look, layer it over a …
[5] create_fit_card
      in:  new_item=lst_007 Denim Jacket — Light Wash, Cropped, outfit=625 chars
      out: My old cropped denim jacket finally bit the dust, so I had been on the hunt for a boxy replacement with some a…

  Found:    Denim Jacket — Light Wash, Cropped — $42.0 on poshmark

  Outfit:   That vintage Wrangler jacket is a fantastic find for any wardrobe. For a classic casual look, layer it over a fitted black ribbed turtleneck and pair it with high-waisted wide-leg black trousers and chunky white sneakers. The structured shoulders will balance the relaxed pants, and the light blue denim pops beautifully against black. For an effortless streetwear vibe, throw it on over a vintage graphic tee and an olive green slip skirt, finished off with well-worn canvas sneakers. Since the wash is so versatile, you can also easily pair it with floral midi dresses or monochrome sweatsuits for an instant style upgrade.

  Fit card: My old cropped denim jacket finally bit the dust, so I had been on the hunt for a boxy replacement with some actual structure. This Wrangler piece delivers on the shoulders and has that perfect effortless streetwear vibe. I picked it up on Poshmark for $42 and honestly cannot wait to wear it with everything.

2 model calls this session, 520 prompt + 184 output tokens
```

Model unreachable, triggered on purpose with a bad key. `agent.py::run_agent` catches `ModelUnavailable`, keeps the item the search found, and ends with a message in `session["error"]` instead of a stack trace:

```
$ GEMINI_API_KEY=not-a-real-key AI201_CACHE=0 python app.py ask 'denim jacket under $50' --trace
[1] parse_query
      in:  denim jacket under $50
      out: {'description': 'denim jacket', 'size': None, 'max_price': 50.0}
[2] search_listings (via MCP)
      in:  {'description': 'denim jacket', 'size': None, 'max_price': 50.0}
      out: 7 items: Denim Jacket — Light Wash, Cropped, 90s Track Jacket — Navy/White Stripe, High-Waisted Denim Shorts — Cutoff … +4 more
      →    branch: results found, going on to select an item
[3] select_item
      in:  search_results[0] of 7
      out: lst_007 Denim Jacket — Light Wash, Cropped
[4] suggest_outfit
      in:  new_item=lst_007 Denim Jacket — Light Wash, Cropped
      →    model unavailable, stopping: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.

  Found Denim Jacket — Light Wash, Cropped ($42 on poshmark), but it couldn't be styled. The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.

1 model calls this session
```

**What the agent said, each time**

| Failure | How I triggered it | What the agent said |
|---|---|---|
| Empty search | `'designer ballgown size XXS under $5'` | "No listings matched 'designer ballgown' in size XXS under $5. Try dropping the size (XXS), raising the $5 price ceiling, or using fewer or more general words, like 'jacket' or 'tee'." |
| Empty wardrobe | `'denim jacket under $50' --empty-wardrobe` | No error. It found the denim jacket and gave general advice that names no owned pieces, starting "That vintage Wrangler jacket is a fantastic find for any wardrobe. For a classic casual look, layer it over a fitted black ribbed turtleneck…", then wrote the fit card. |
| Model unavailable | `GEMINI_API_KEY=not-a-real-key AI201_CACHE=0`, a query that finds listings | "Found Denim Jacket — Light Wash, Cropped ($42 on poshmark), but it couldn't be styled. The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com." |

None of the three crashed or went silent. I changed one message after reading them as a user would. The model-unavailable message used to end "Check GEMINI_API_KEY in your .env and try again" whatever the cause, so a dropped connection or a wrong model name also told the user to check a key that was fine. `agent.py::_model_unavailable` now passes on the reason `generate.py` already works out, so the three causes it tells apart (rejected key, model name that doesn't resolve, no connection) each give a different next step. The files in `results/` were written before this change and still show the old wording.

**On the MCP move:** `search_listings` is the tool I moved. In `mcp_server.py` I registered it with `@mcp.tool()`, with the same three typed inputs as the Tool Inventory (`description: str`, `size: str | None`, `max_price: float | None`) and a description that states the size rule, the units of the price, the fields in each listing and the empty case. In `agent.py::run_agent` the direct call `search_listings(...)` became `call_tool("search_listings", {...})` from `mcp_client.py`, and the trace step is now named `search_listings (via MCP)`.

Nothing changed in what comes back. I compared the two for the same inputs and they were equal: `search_listings('graphic tee', None, 30) == call_tool('search_listings', {...})` printed `True`, both a `list` of 7 listing dicts, and the impossible query came back as `[]` through MCP as well, so the branch needed no change. The one thing I added is a handler for `MCPError`: if the server can't be started, the run ends with a message in `session["error"]` saying the search couldn't be reached. Each search now starts the server, asks, and stops it, so a run is slower by about a second.

The run in **Run Log — Before** was taken with the direct call, before this move. The after run below went through MCP.

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** One thing, in `tools.py::create_fit_card`. The prompt now tells the model what to open the caption with, picked at random from six openings in `_OPENINGS` (how you'll wear it, the detail that made you buy it, how long you'd been hunting, the mood it puts you in, a question to followers, what it replaces in your closet). It also says not to start with "Scored" or "Just scored", and that the price and platform can come later in the caption.

**Which failure it was meant to fix:** Diagnosis 1 above: every fit card for one item opened the same way. No criterion was missed in the before run, but criterion 4 passed only because its second rule could not see the problem, so I revised that rule in `criteria.md` (the original is still there, with the revision under it): no two of the 5 cards may begin with the same first five words. Scored that way, the before run misses: its five cards began "Scored this vintage Wrangler denim" (tries 1 and 5), "Scored this cropped Wrangler denim" (tries 2 and 3) and "Scored this Wrangler denim jacket" (try 4), which is 3 different openings out of 5. The diagnosis placed the cause in the prompt, which asked for item, price and platform and left the model to put all three in the first clause, so the prompt is what I changed.

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1. A matching query completes all three tools | 4 of 5 | FAIL | FAIL | PASS | FAIL | PASS | MISSED (2/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The item that was found is the item that was styled | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card is a postable caption about this item | 4 of 5, and (revised) 5 different first-five-word openings | PASS | PASS | PASS | PASS | PASS | MISSED as revised (5/5 cards pass, but 4 different openings of 5); MET as first written |
| 5. Outfits use pieces the user actually owns | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Same six scenarios as the before run, 5 tries each, caching off, in `results/run_2026-10-04_2125_after.md` (48 model calls).

**Before and after, side by side**

| Criterion | Target | Before | After | Change |
| --------- | ------ | ------ | ----- | ------ |
| 1. A matching query completes all three tools | 4 of 5 | MET (5/5) | MISSED (2/5) | Worse, from the provider's 503 errors and not from the change |
| 2. An impossible query stops before the second tool | 5 of 5 | MET (5/5) | MET (5/5) | Same |
| 3. The item that was found is the item that was styled | 5 of 5 | MET (5/5) | MET (5/5) | Same |
| 4. Cards with two to four sentences, the price and the platform | 4 of 5 | 5/5 | 5/5 | Same |
| 4. Different first-five-word openings (revised rule) | 5 of 5 | 3 of 5 | 4 of 5 | Better, still MISSED |
| 5. Outfits use pieces the user actually owns | 4 of 5 | MET (5/5) | MET (5/5) | Same |

This is the second after run. The first, `results/run_2026-10-04_2119_after.md`, lost 13 of its 30 tries to the model provider returning `503 UNAVAILABLE … This model is currently experiencing high demand`, so it could not measure the change. I kept the file and re-ran once the model was answering again. The second run still lost 4 tries to the same error, and those are counted above as they fell.

**Did it help, and how do I know:** Partly. The change helped the openings it was aimed at, from 3 different out of 5 to 4, but not enough to meet the revised target. A different criterion also missed in the same run, for an unrelated reason.

- **Criterion 4, the openings:** up from 3 different openings out of 5 to 4 out of 5 on the criterion 4 scenario. The five cards began "Who needs a boring basic", "Those structured shoulders immediately sold", "I had been hunting for", "I had been hunting for" and "Those structured shoulders are everything". None begins with "Scored", where all five did before. It still misses, because tries 3 and 4 share their first five words. The cause is in the change itself: `random.choice` picks one of six openings independently for each card, so five cards will usually repeat at least one, and two cards given "how long you had been hunting" both began "I had been hunting for".
- **Criterion 4, the rest:** unchanged. All five cards still have three sentences, "$42" and "Poshmark", so moving the price later in the caption did not make the model drop it.
- **Other scenarios, same check:** the track jacket went from 2 different openings out of 5 to 5 out of 5, and the platform sneakers from 3 to 5.
- **Criterion 1 got worse, from 5/5 to 2/5, and the change did not cause it.** Tries 1 and 2 stopped at `suggest_outfit` and try 4 at `create_fit_card`, each with the provider's 503 "high demand" error in the trace. The place is the loop and the adapter, not the model's output: `generate.py::generate` retries only rate-limit errors, so a 503 raises `ModelUnavailable` at once, and `run_agent` ends the run on the first one. The handler did its job — each try ended with a message naming the item that was found, not a stack trace — but a run that stops is still not a fit card, so those tries fail.

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->

---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

**Criterion 1 — a matching query completes all three tools (MISSED 2/5 in the after run).** A temporary 503 from the model provider ends the run, because nothing retries it. I would retry a failed model step once or twice in `run_agent`, with a short wait, before giving up with the current message. I stopped because the miss showed up in the after run, after my one improvement was already made and measured, and adding a second change would have meant I could no longer say which change moved which number.

**Criterion 4 — the fit card, as revised (MISSED, 4 different openings of 5).** Picking the opening at random lets two cards draw the same one. I would stop picking independently: either rotate through the openings so five cards in a row cannot repeat, or drop the fixed list and have the prompt name a different detail of the listing each time. Rotation needs the tool to remember what it used last, and `create_fit_card` keeps nothing between calls today, which is why I did not do it here.

**Things that pass but that I do not fully trust:**

- **Criterion 3's evidence.** The trace prints search results as titles, so the check that `search_results[0]` is the selected item compares a title while the other two places compare the id. Printing the first result's id in the `search_listings (via MCP)` step would close that.
- **One query per criterion.** Every criterion was scored on a single query from the starter's example list. Criterion 1's reason said the keyword search would miss some phrasings ("tee shirt" for "graphic tee"), and no scenario tried one, so the misses I did get came from somewhere I had not predicted.
- **The search has no notion of meaning.** "denim jacket under $50" returns seven listings including denim shorts and a track jacket, because each shares one word. The first result has been right in every run, and only the first is used, but nothing guarantees that.
- **The Sample Run section is from before the improvement.** Its fit cards were produced by the earlier prompt, so re-running those commands now gives captions that open differently.

<!-- ═══════════════════ UNIT 9 — DEPLOY AND INSTRUMENT ═══════════════════ -->

## Unit 9 — The Extension

**System extended:** FitFindr, the thrift-search agent from units 3 and 4.
The agent itself is unchanged. `run_agent()`, the three tools, the MCP server
and the prompts are exactly what unit 4 left.

**Shape: A — deploy and instrument. Path A, hosted on Render:
https://fitfindr-ha9z.onrender.com**

**What's new:**

- **A hosted run path.** [`render.yaml`](render.yaml) builds the service and
  starts it with `gunicorn serve:app --workers 1 --timeout 300`. `serve.py`'s
  `POST /ask` and `GET /health` are live on Render's free tier. Details and
  the environment are in [RUNNING.md](RUNNING.md).
- **A structured request log.** [`request_log.py`](request_log.py) writes one
  JSON line per `/ask` with named fields. That covers when it happened, what
  came in (`query`, `parsed`), what went out (`outcome`, `item_id`, `steps`,
  `error`), and how long it took (`queue_ms`, `agent_ms`, `total_ms`). It also
  records what it cost (`model_calls`, `prompt_tokens`, `output_tokens`) and
  what it held (`peak_rss_mb`, `children_peak_rss_mb`). Each line carries a
  `boot_id`, `nth_since_boot` and `uptime_s`, so a cold start shows up in the
  data.
- **Two routes that read the log back:** `GET /stats` (p50/p95, outcomes,
  tokens, memory since boot) and `GET /logs` (the last 200 lines). On a free
  host the log dies when the instance sleeps, so these routes are how it gets
  out.
- **A measurement client.** [`measure.py`](measure.py) times the cold start
  from outside, which the server can't do. It runs a fixed set of queries
  covering every exit from the loop and matches each response to its log line
  by `X-Request-Id`. It scores the session against D1–D5 in
  [criteria.md](criteria.md) and writes a committed record to `results/`.

**Out of scope, decided up front:**

- **No change to what the agent does.** No new tool, prompt, or parsing rule.
  If a criterion misses because the agent is slow or wrong, the fix has to be
  in how it's run, not in what it does.
- **No failure hardening beyond what unit 4 built (that's shape B).** No new
  retries, fallbacks or timeouts inside the agent.
- **No persistent log storage.** The instance's disk is wiped on sleep. The
  committed `results/deploy_*` files are the durable copy, by design, not a
  database or log service.
- **No concurrency.** One agent run at a time, as `serve.py` was built. A
  second request waits its turn.
- **No auth on `/stats` and `/logs`.** They expose queries and timings, never
  wardrobe contents. Fine for a class demo, not for real users.

## Unit 9 — Run Log, Before

Three sessions against https://fitfindr-ha9z.onrender.com, each started
after at least 20 idle minutes, each `python measure.py --url ... --rounds 3
--label before` (1 `/health` + 15 `/ask`). Deployed commit: `abbab8a`, start
command `gunicorn serve:app --workers 1 --timeout 300`. Full records:
`results/deploy_before_*.md`. Scored with `python measure.py --score
results/deploy_before_*.json`, saved as `results/score_before.txt`.

| Session (UTC) | `/health` (wake) | What happened to the 15 `/ask` requests |
|---|---|---|
| 15:29:49 | 200 in 42.8 s | #1 `complete` in 22.0 s. #2 hung 66.8 s → **502**. #3–#15 all **502** in < 1 s (including `bad_request`, which never reaches the agent) |
| 15:55:00 | 200 in 32.5 s | #1 `complete` in 41.6 s. #2 → **502** after 27.5 s. #3–#15 all **502** |
| 16:20:00 | 200 in 22.3 s | #1, #2 `model_unavailable` (17.2 s, 5.0 s). #3 `no_match` (4.5 s). #4 → **502** after 22.4 s. #5–#15 all **502** |

Each time the 502s began, Render answered with `x-render-routing: no-deploy`,
meaning no instance was running at all. A minute later the service came back
on its own with a new `boot_id` and an empty `/stats`. That pattern is the
instance being killed and restarted, not the app returning errors.

| Criterion | Target | Measured (3 sessions) | Verdict |
|---|---|---|---|
| D1 cold start | `/health` ≤ 60 s, proven cold, 3 of 3 | 42.8 / 32.5 / 22.3 s, but **cold proof lost** (no log lines survived) | **Missed: unprovable** |
| D2 warm latency | p50 ≤ 8 s, p95 ≤ 75 s, 0 × 5xx | **0 warm full runs**, **40 of 45** requests 5xx | **Missed** |
| D3 one truthful log line | 45 of 45 | **0 of 45** | **Missed** |
| D4 memory | ≤ 256 MB, 3 of 3 | nothing to read: logs and `/stats` died with the instance | **Missed: unmeasurable** |
| D5 cost | mean ≤ 1,000 tokens; calls 45 of 45 | 0 full runs logged; **0 of 45** | **Missed** |

**Structured log extract.** The before set has none to show: every line died
with its instance. These 12 lines are from trial session
`deploy_hosted_2026-11-12_033045`. That session was proven cold (uptime 21.6 s
at the first `/ask`, 40.3 s into the session), survived all 15 requests, and
isn't scored. It shows exactly what each scored session should have
returned:

```jsonl
{"ts": "2026-11-12T03:31:25.497+00:00", "request_id": "34bf3e9b12a1", "boot_id": "9c9f46cc", "nth_since_boot": 1, "uptime_s": 21.6, "route": "/ask", "status": 200, "outcome": "complete", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "item_id": "lst_006", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 17259.2, "total_ms": 17260.6, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 721, "output_tokens": 141, "model_calls_since_boot": 2, "error": null, "peak_rss_mb": 95.9, "children_peak_rss_mb": 58.4}
{"ts": "2026-11-12T03:31:31.989+00:00", "request_id": "736406e3e581", "boot_id": "9c9f46cc", "nth_since_boot": 2, "uptime_s": 28.1, "route": "/ask", "status": 200, "outcome": "complete", "query": "90s track jacket in size M", "parsed": {"description": "90s track jacket", "size": "M", "max_price": null}, "item_id": "lst_004", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 6313.9, "total_ms": 6314.2, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 779, "output_tokens": 199, "model_calls_since_boot": 4, "error": null, "peak_rss_mb": 96.1, "children_peak_rss_mb": 95.9}
{"ts": "2026-11-12T03:31:36.586+00:00", "request_id": "74e3f0ab7082", "boot_id": "9c9f46cc", "nth_since_boot": 3, "uptime_s": 32.7, "route": "/ask", "status": 200, "outcome": "no_match", "query": "designer ballgown size XXS under $5", "parsed": {"description": "designer ballgown", "size": "XXS", "max_price": 5.0}, "item_id": null, "steps": ["parse_query", "search_listings"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 4434.4, "total_ms": 4434.6, "model_calls": 0, "cache_hits": 0, "prompt_tokens": 0, "output_tokens": 0, "model_calls_since_boot": 4, "error": "No listings matched 'designer ballgown' in size XXS under $5. Try dropping the size (XXS), raising the $5 price ceiling, or using fewer or more general words, like 'jacket' or 'tee'.", "peak_rss_mb": 96.1, "children_peak_rss_mb": 96.1}
{"ts": "2026-11-12T03:31:43.922+00:00", "request_id": "c956740fe3c3", "boot_id": "9c9f46cc", "nth_since_boot": 4, "uptime_s": 40.0, "route": "/ask", "status": 200, "outcome": "complete", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "item_id": "lst_006", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 0, "queue_ms": 0.0, "agent_ms": 7004.7, "total_ms": 7004.8, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 503, "output_tokens": 155, "model_calls_since_boot": 6, "error": null, "peak_rss_mb": 96.1, "children_peak_rss_mb": 96.1}
{"ts": "2026-11-12T03:31:44.088+00:00", "request_id": "159e4b137a33", "boot_id": "9c9f46cc", "nth_since_boot": 5, "uptime_s": 40.2, "route": "/ask", "status": 400, "outcome": "bad_request", "total_ms": 0.1, "peak_rss_mb": 96.1, "children_peak_rss_mb": 96.1}
{"ts": "2026-11-12T03:31:49.987+00:00", "request_id": "50a0acbe7363", "boot_id": "9c9f46cc", "nth_since_boot": 6, "uptime_s": 46.1, "route": "/ask", "status": 200, "outcome": "complete", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "item_id": "lst_006", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 5740.9, "total_ms": 5741.1, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 757, "output_tokens": 179, "model_calls_since_boot": 8, "error": null, "peak_rss_mb": 96.2, "children_peak_rss_mb": 96.1}
{"ts": "2026-11-12T03:31:56.351+00:00", "request_id": "303d9204d179", "boot_id": "9c9f46cc", "nth_since_boot": 7, "uptime_s": 52.5, "route": "/ask", "status": 200, "outcome": "complete", "query": "90s track jacket in size M", "parsed": {"description": "90s track jacket", "size": "M", "max_price": null}, "item_id": "lst_004", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 6028.6, "total_ms": 6028.9, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 743, "output_tokens": 157, "model_calls_since_boot": 10, "error": null, "peak_rss_mb": 96.2, "children_peak_rss_mb": 96.2}
{"ts": "2026-11-12T03:32:00.699+00:00", "request_id": "459c1edd70ed", "boot_id": "9c9f46cc", "nth_since_boot": 8, "uptime_s": 56.8, "route": "/ask", "status": 200, "outcome": "no_match", "query": "designer ballgown size XXS under $5", "parsed": {"description": "designer ballgown", "size": "XXS", "max_price": 5.0}, "item_id": null, "steps": ["parse_query", "search_listings"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 4015.1, "total_ms": 4015.5, "model_calls": 0, "cache_hits": 0, "prompt_tokens": 0, "output_tokens": 0, "model_calls_since_boot": 10, "error": "No listings matched 'designer ballgown' in size XXS under $5. Try dropping the size (XXS), raising the $5 price ceiling, or using fewer or more general words, like 'jacket' or 'tee'.", "peak_rss_mb": 96.2, "children_peak_rss_mb": 96.2}
{"ts": "2026-11-12T03:32:07.566+00:00", "request_id": "027af7dcde2c", "boot_id": "9c9f46cc", "nth_since_boot": 9, "uptime_s": 63.7, "route": "/ask", "status": 200, "outcome": "complete", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "item_id": "lst_006", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 0, "queue_ms": 0.0, "agent_ms": 6707.1, "total_ms": 6707.2, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 523, "output_tokens": 181, "model_calls_since_boot": 12, "error": null, "peak_rss_mb": 96.3, "children_peak_rss_mb": 96.2}
{"ts": "2026-11-12T03:32:07.747+00:00", "request_id": "d5d24f31f828", "boot_id": "9c9f46cc", "nth_since_boot": 10, "uptime_s": 63.9, "route": "/ask", "status": 400, "outcome": "bad_request", "total_ms": 0.1, "peak_rss_mb": 96.3, "children_peak_rss_mb": 96.2}
{"ts": "2026-11-12T03:32:13.076+00:00", "request_id": "8dbde5710951", "boot_id": "9c9f46cc", "nth_since_boot": 11, "uptime_s": 69.2, "route": "/ask", "status": 200, "outcome": "complete", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "item_id": "lst_006", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 5078.6, "total_ms": 5078.9, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 723, "output_tokens": 138, "model_calls_since_boot": 14, "error": null, "peak_rss_mb": 96.4, "children_peak_rss_mb": 96.3}
{"ts": "2026-11-12T03:32:24.581+00:00", "request_id": "264058759873", "boot_id": "9c9f46cc", "nth_since_boot": 12, "uptime_s": 80.7, "route": "/ask", "status": 200, "outcome": "complete", "query": "90s track jacket in size M", "parsed": {"description": "90s track jacket", "size": "M", "max_price": null}, "item_id": "lst_004", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 11221.4, "total_ms": 11221.8, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 754, "output_tokens": 168, "model_calls_since_boot": 16, "error": null, "peak_rss_mb": 96.4, "children_peak_rss_mb": 96.4}
```

## Unit 9 — Verdicts and Diagnoses

All five missed, and **one cause sits under all five**: the instance was
killed mid-session every time, taking its in-memory log with it.

**The mechanism: `/health` can't answer while an `/ask` runs.** The place is
the start command in `render.yaml`, `gunicorn serve:app --workers 1`, which
gives one **sync** worker. A sync worker handles exactly one HTTP request at
a time, `/health` included. Render's health check (`healthCheckPath:
/health`) joins the same line as `measure.py`'s requests. While an `/ask`
runs, the check waits behind it. `measure.py` sends the next `/ask` as soon
as the last one returns, so the worker is almost never free. When enough
checks time out in a row, Render decides the instance is dead and replaces
it.

Evidence:

- **Measured locally with the same start command:** `/health` took **0.004 s**
  when idle and **2.94 s** when sent during an `/ask`. It returned only once
  the run finished.
- **The failure scales with run length.** Today's runs were slow (17–42 s
  each) and the instance died after only 1–3 of them. Last night's trial
  sessions had 5–7 s runs. One survived all 15 requests, and two died later
  in the session (4 and 1 × 5xx). Longer runs mean longer stretches with
  every health check stuck in line.
- **Memory doesn't fit.** In every session where logs survived, peak memory
  was a flat ~96 MB server + ~96 MB MCP child. That's ~192 MB even counted
  twice, under 40% of 512 MB, and not growing request to request.
- **Not yet confirmed from Render's side.** Render's Events page should say
  whether each restart was a failed health check or an out-of-memory kill.

Per criterion:

- **D1 (missed, unprovable).** All three wake-ups were under 60 s
  (22–43 s), so the target itself was probably met. But the proof that the
  instance woke from sleep lives in the log, and the log died. A cold start I
  can't prove isn't a pass.
- **D2 (missed).** 40 of 45 requests got 502 from Render's proxy, because the
  instance behind it was gone. No run survived long enough to be "warm".
- **D3 (missed, 0 of 45).** The log is in-process memory plus a file on the
  instance's disk. Both go when Render replaces the instance, so a crash
  erases the record of the crash. This is the exact failure D3 was written
  to catch. The few lines written before each crash existed briefly, but
  `/logs` is only read at the end of a session, by which point they were
  gone.
- **D4 (missed, unmeasurable).** The memory numbers come from the same log
  and `/stats`, so they died too. The trial sessions suggest ~192 MB, which
  would pass, but that isn't this result set.
- **D5 (missed, 0 of 45).** Same cause: no log line, no token count. The two
  `model_unavailable` runs in session 3 are a second, separate problem. The
  model call failed, and `measure.py` cut the error at 70 characters, so the
  reason is lost (now fixed to keep 400). The trial logs above put a full run
  at 658–978 tokens, but those aren't scored.

## Unit 9 — Cost of One Run

**One full run (two model calls) = 830 tokens ≈ $0.0006, and 23.3 s of
wall-clock time on the instance.**

How it was measured: each `/ask` log line carries `prompt_tokens` and
`output_tokens`. Those are the service's own counts from
`response.usage_metadata`, summed per request by `generate.py` and
differenced per request by `serve.py`. Over the **15 full runs** in the after
set (cache off, so every call was real):

| | Mean per full run |
|---|---|
| Prompt tokens | 658.4 |
| Output tokens | 171.6 |
| Total | **830.0** (range 662–969) |
| Model calls | **2** (every one of the 15) |
| Time in `run_agent()` | **23.3 s** mean, 17.8 s median |
| Of which: MCP spawn + search (from the 9 `no_match` runs, which make no model call) | ~4.4 s |

In money, at gemini-3.5-flash-lite's listed rate of $0.30 per 1M input
tokens and $2.50 per 1M output tokens: 658.4 × $0.30/1M + 171.6 ×
$2.50/1M = $0.00020 + $0.00043 = **$0.00063 per full run**, about 1,600 runs
per dollar. Output is 21% of the tokens but 68% of the cost. What I actually
paid was **$0**, because this runs on the free tier. Its real limit is 15
requests a minute, about 7 full runs a minute.

Failed runs cost too: the 12 `model_unavailable` runs spent 1,659 tokens
(≈ $0.0005 together) and produced no fit card.

Two caveats on the number. (1) `generate.py` counts `candidates_token_count`
but not thinking tokens (`thoughts_token_count`). If the model "thinks", those
are billed as output and missing here, so this is a floor. (2) The rate comes
from third-party listings that agree with each other. I couldn't open
Google's own pricing page.

## Unit 9 — The Improvement

**One change, one line:** the start command in `render.yaml` goes from

    gunicorn serve:app --workers 1 --timeout 300 --bind 0.0.0.0:$PORT

to

    gunicorn serve:app --workers 1 --threads 4 --timeout 300 --bind 0.0.0.0:$PORT

That's still one process, so `serve.py`'s lock still allows one agent run at
a time, and memory and the model pacing are unchanged. Four threads means a
`/health` check no longer waits behind a running `/ask`. These are threads,
not an async worker, so `mcp_client`'s `asyncio.run()` still works.

**Tested locally before deploying**, same start command: `/health` took
**0.0015 s while two `/ask` requests were in flight** (2.94 s before the
change), and the second `/ask` still logged
`[serve] another request is still running`, so the lock held.

**Something else the local test turned up, which this change does NOT fix:**
`gemini-3.5-flash-lite` was answering with `503 UNAVAILABLE: This model is
currently experiencing high demand`, after one call had already waited 47 s.
That is outside this system. It most likely explains today's 17–42 s runs
and session 3's `model_unavailable`, and it will affect the after sessions
too.

**Deployed and checked:** at 16:36 UTC, `/stats` showed commit `7a1412f`
live, and a `/health` sent during an `/ask` came back in **0.59 s**. That
`/ask` ran 91 s, and the instance survived it.

### Run Log — After

Three sessions, same command with `--label after`, same rules. Records:
`results/deploy_after_*.md`. Score: `results/score_after.txt`. One attempt at
17:54 never left my laptop: the Mac had slept, DNS failed, and all 16 calls
failed in 1 ms without reaching Render. Per the session rule it's kept as
`results/deploy_after-clientoffline_*` and was replaced by a re-run at
17:56.

| Session (UTC) | `/health` (wake) | 15 `/ask` requests |
|---|---|---|
| 17:00:00 | 200 in 22.3 s | **0 × 5xx.** 2 `complete`, 6 `model_unavailable` (Gemini 503), 3 `no_match`, 3 `bad_request` (400) |
| 17:25:00 | 200 in 22.3 s | **0 × 5xx.** 6 `complete`, 3 `model_unavailable`, 3 `no_match`, 3 `bad_request` |
| 17:56:26 | 200 in 21.4 s | **0 × 5xx.** 7 `complete`, 2 `model_unavailable`, 3 `no_match`, 3 `bad_request` |

### Before and after, side by side

| Criterion | Target | Before (sync worker) | After (`--threads 4`) |
|---|---|---|---|
| D1 cold start | ≤ 60 s, proven cold, 3 of 3 | 22–43 s, **unprovable** (logs lost) | **MET**: 3 of 3 proven cold, 21.4–22.3 s |
| D2 warm latency | p50 ≤ 8 s, p95 ≤ 75 s, 0 × 5xx | **MISSED**: 0 runs, 40 × 5xx | **MISSED**: p50 **17.2 s**, p95 33.5 s ✓, 0 × 5xx ✓ (n = 14) |
| D3 one truthful log line | 45 of 45 | **MISSED**: 0 of 45 | **MET**: 45 of 45 |
| D4 memory | ≤ 256 MB, 3 of 3 | **MISSED**: unmeasurable | **MET**: 233.4 / 234.4 / 234.4 MB |
| D5 cost | mean ≤ 1,000 tokens; calls 45 of 45 | **MISSED**: 0 of 45 | **MISSED**: mean **830** tokens ✓, calls **33 of 45** ✗ |

**What the change fixed:** every miss in the before set had one cause, the
instance being killed, and that cause is gone. Zero 5xx in 45 requests, with
runs up to 70 s, and every request left its log line. D1, D3 and D4 went from
unmeasurable to met.

**What it didn't fix, and why (the two remaining misses):**

- **D2, p50 17.2 s against 8 s.** The place is the model calls, not the
  deployment. A `no_match` run does everything except call the model (parse,
  MCP subprocess spawn, search), and it averaged **4.4 s** on Render. So the
  MCP spawn on 0.1 CPU costs about 4 s, about what D2's reasoning predicted
  (10× the laptop's 0.3 s). That leaves 8 s for two model calls if the
  target is to hold, and today they took a median ~13 s. Gemini was under
  load all afternoon (next bullet). The 70 s run used exactly 2 calls, so it
  wasn't the pacing retrying: one call was simply that slow. Last night's
  trial sessions, with Gemini healthy, ran full runs in 5.3–7 s on the same
  deployment, which would have met 8 s. I'm not counting that, since it
  isn't this result set.
- **D5, calls 33 of 45.** All 12 misses are `model_unavailable`: Gemini
  answered `503 UNAVAILABLE: This model is currently experiencing high
  demand`. That's 12 of 27 model-path runs, 44%. A run that dies at
  `suggest_outfit` logs 1 call, and one that dies at `create_fit_card` logs
  2 calls but no fit card. **All 15 full runs used exactly 2 calls**, so the
  pacing never caused a retry, which was the specific failure D5's call
  count was there to catch. The token half met: 830 against 1,000.

## Unit 9 — What's Left

**D2 and D5 are still missed, and both come from the model provider, not
the deployment.** What I'd do, in order:

1. **Retry a 503 once, after a short wait, in `generate.py`.** Today it
   treats a 503 like a bad key and gives up. That would have rescued some of
   the 12 runs. I didn't do it because it's an agent change (shape B), and
   this unit's scope rule was no change to what the agent does. It would also
   have been a second change in the same after set.
2. **Spawn the MCP server once, not once per search.** That's about 4 s of
   every run on Render's 0.1 CPU, half of D2's 8 s budget, spent starting a
   Python interpreter. One long-lived MCP session per worker would remove it.
   I stopped here because it changes `mcp_client.py` and the process model,
   and measuring it properly needs Gemini healthy, which it wasn't today.
3. **Re-run the after set on a normal day.** D2's miss is measured, and it
   stays a miss. But one afternoon of Gemini under load can't separate "8 s
   was too tight" from "the provider was slow".

**Things that pass but that I don't fully trust:**

- **The log still lives on the instance.** D3 passes because the instance no
  longer dies, not because the log could survive it if it did. A crash would
  still erase its own record. Sending each line somewhere off the box would
  fix that.
- **D4 passes with 22 MB to spare, and it rose.** It was ~192 MB with the
  sync worker and is 234 MB with threads. Whether the children figure counts
  the forked parent's memory twice is unverified. If it does, the real peak
  is lower. If it doesn't, there's less headroom than "half the plan"
  suggests.
- **`generate.py`'s 300-call budget never resets** on a server that stays up.
  After ~150 full runs in one instance's life, every request would fail.
  `/stats` shows `session_budget.used`, but nothing acts on it.
- **`/stats` and `/logs` have no auth.** Queries and timings are public to
  anyone with the URL. No wardrobe contents are logged, but it isn't
  something to leave on for real users.
- **The before-set diagnosis is inference.** The local measurement (0.004 s
  vs 2.94 s), the timing pattern and the fix's result all point to failed
  health checks. Render's event log for 15:31, 15:56 and 16:21 UTC would
  confirm it directly, and I haven't quoted it here.

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
