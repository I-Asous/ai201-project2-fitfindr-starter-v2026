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

**Real output from one try**, pasted as text, naming the file and function
that produced it:

Criterion 3, try 1. Produced by `run_eval.py::main` calling `agent.py::run_agent`; the trace lines come from the `trace.step` calls inside `run_agent`.

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

  Found Denim Jacket — Light Wash, Cropped ($42 on poshmark), but the model couldn't be reached to style it. Check GEMINI_API_KEY in your .env and try again.

1 model calls this session
```

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

This is the second after run. The first, `results/run_2026-10-04_2119_after.md`, lost 13 of its 30 tries to the model provider returning `503 UNAVAILABLE … This model is currently experiencing high demand`, so it could not measure the change. I kept the file and re-ran once the model was answering again. The second run still lost 4 tries to the same error, and those are counted above as they fell.

**Did it help, and how do I know:** Partly. It helped the thing it was aimed at, but not enough to meet the revised target, and a different criterion missed in the same run for an unrelated reason.

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
