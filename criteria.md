# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
<!-- Why 4 of 5 and not 5 of 5? Something about your search, probably —
     "my search is a plain keyword match and some phrasings will miss" is a
     real answer. -->

`search_listings` is a plain keyword match that drops every listing scoring
zero, and the query is parsed in code before it gets there. A phrasing whose
words are not in a listing's title, description or tags ("tee shirt" for
"graphic tee") or whose size or price the parser reads wrongly can come back
empty even though a matching listing exists. On top of that, the second and
third tools each call the model, so one failed call in two per run ends the
run. One miss in five allows for that; two would mean the search or the
parsing is actually broken.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
<!-- Why is 5 of 5 reasonable here when criterion 1 isn't? What's different
     about this path? -->

This path never reaches the model. Parsing, `search_listings` and the branch
are all plain code, so the same query gives the same result every time —
there is nothing random to excuse a miss. If it fails once it fails five
times, which makes anything below 5 of 5 a bug in the branch, not bad luck.

---

## 3. The item that was found is the item that was styled

<!-- YOU WRITE THIS ONE.

     How would you know that the item your search found is the same item the
     next tool received? Name something countable or observable.

     This is the criterion people find hardest, because state failure doesn't
     look like state failure — it looks like a tool problem. Something that
     compares session["selected_item"] against what actually reached
     suggest_outfit is the shape you're after. -->

Given a query that matches at least one listing, three listing ids are the
same: the `id` of `session["search_results"][0]`, the `id` of
`session["selected_item"]`, and the `id` of the `new_item` that
`suggest_outfit` and `create_fit_card` were actually called with, as shown in
the trace — 5 of 5 tries.

**Why this target:**

Choosing the item and handing it on is plain code with no model in it, so it
cannot be right some of the time: either the loop reads the item back out of
the session or it doesn't. 5 of 5 is the only honest target. I compare ids
instead of titles because two listings can have similar titles, and I check
the tool's real input instead of only the session because a loop can store
the right item and still pass a different one.

---

## 4. The fit card is a postable caption about this item

<!-- YOU WRITE THIS ONE.

     The fit card calls a model, so the same input can produce different words
     each time. That's not a bug — it's the nature of the tool. So what would
     make it acceptable?

     Think about what you'd actually be unhappy to see. A caption that never
     mentions the price? Two different items producing the same opening
     sentence? A card longer than a caption anyone would post? Any of those can
     be turned into a number. -->

For the same matching query run 5 times, a fit card passes when it is two to
four sentences long and contains both the selected item's price (the number,
e.g. "24") and its platform name (e.g. "depop") — at least 4 of 5 cards pass.
In addition, no two of the 5 cards have the same first sentence.

**Why this target:**

The price and the platform are the two facts a reader needs to go and find
the item, and they are the two things the model is most likely to drop when
it writes something that sounds like a post. I can check both by searching
the text, and sentence count by counting. It is 4 of 5 and not 5 of 5 because
the model writes this at temperature 0.9: it will sometimes run to a fifth
sentence or write "thrifted" without naming the platform, and the tool does
not re-check its own output. The first-sentence rule is 5 of 5 because at
that temperature a repeated opening means the cache is on or the prompt is
dictating the wording, and either is a fault I can fix.

> **Revised in unit 4:** The first part is unchanged (two to four sentences,
> with the price and the platform, in at least 4 of 5 cards). The second part
> becomes: no two of the 5 cards begin with the same first five words.
>
> **Why revised:** "the same first sentence" turned out not to measure what I
> meant. In the before run all five cards opened "Scored this … Wrangler
> denim jacket on Poshmark for $42 and …", and they still counted as five
> different sentences because an adjective changed further along. Comparing
> the first five words catches cards that open the same way, and it is still
> something I can count. This makes the target harder, not easier: the before
> run, which passed the original wording, has only 3 different openings out
> of 5 under this one.

---

## 5. Outfits use pieces the user actually owns

<!-- YOU WRITE THIS ONE TOO.

     Pick something you actually care about getting right. Speed, the empty
     wardrobe path, what happens when the model can't be reached, whether the
     search respects a price ceiling — anything, as long as it names a number
     or an observable outcome. -->

Given a matching query and the example wardrobe, the outfit suggestion
contains the `name` of at least one wardrobe item (ignoring upper and lower
case, e.g. "black combat boots") and names no piece as owned that is not in
the wardrobe — in at least 4 of 5 tries.

**Why this target:**

Using the wardrobe is the whole point of `suggest_outfit`; without it the
user gets advice any search engine could give. The wardrobe goes into the
prompt, so the model should use it, but it tends to paraphrase ("your combat
boots" for "Black combat boots") or add a piece the user doesn't have. An
exact-name check will count a paraphrase as a miss, so I allow one in five.
I am not loosening it to "mentions something similar" because I couldn't
score that the same way twice.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->

---

<!-- ═══════════════════ UNIT 9 — DEPLOY AND INSTRUMENT ═══════════════════ -->

# Deployment criteria — unit 9 (shape A, hosted on Render)

Written **before** the first hosted measurement. Each one is scored from the
committed run records in `results/deploy_hosted_*.md`, which `measure.py`
writes. The sessions are defined up front, so the denominators can't drift:

- **3 sessions**, each started after at least 15 minutes with no traffic, so
  each one begins with Render waking a sleeping instance.
- Each session is `python measure.py --url <service> --rounds 3`: one
  `GET /health`, then 5 requests × 3 rounds = **15 `/ask` requests**. Of
  those, 9 are full runs (two matching queries and one with an empty
  wardrobe), 3 have no match and 3 are bad requests.
- Across all 3 sessions: 3 cold starts, **45 `/ask` requests**, 27 full runs.

"Warm" means any `/ask` whose log line has `nth_since_boot` > 1, so it is not
the first request the process served. "Cold confirmed" means the session's
first `/ask` has `nth_since_boot` = 1, which proves the instance really
restarted. `/health` isn't logged, so it doesn't count toward
`nth_since_boot`.

---

## D1. A cold start answers within a minute

In each session, the first `GET /health` returns 200 within **60 s** measured
from the client, and that session's first `/ask` has `nth_since_boot` = 1 —
**3 of 3 sessions**.

**Why this target:**

The client measures this because the server can't. While Render is waking
the instance, my process doesn't exist yet, so `request_log.py` has nothing
to time. Render describes the free-tier spin-up as about a minute. On top of
that, my boot only imports Flask, `google-genai` and my own modules, and
`data/listings.json` holds just 40 listings. Nothing loads a model and nothing
reads a large file. So anything over 60 s would come from my import path, not
from the platform, and that's worth knowing. It's 3 of 3, not 2 of 3,
because there are only three cold starts to look at. If one of them is over
a minute, a user hits that wait one time in three. The `nth_since_boot` check
is there so a session where the instance never actually slept can't pass as
a fast cold start.

> **Revised in unit 9, before any hosted result:** a session counts as cold
> when the server's `uptime_s` at the first `/ask` is **no greater than the
> seconds elapsed since the session started** (measured by `measure.py`),
> instead of when `nth_since_boot` = 1. A session that isn't cold doesn't
> count toward the 3 and has to be re-run after 15 idle minutes. The 60 s
> target and the 3 of 3 are unchanged.
>
> **Why revised:** `nth_since_boot` = 1 couldn't tell a woken instance from
> one that was already awake and just hadn't served an `/ask` yet, because
> `/health` isn't logged. Right after a deploy, an awake instance would have
> passed as a 0.2 s "cold start". Comparing uptime against session time
> proves the process didn't exist when the session began. This makes D1
> harder to pass, not easier.

---

## D2. Warm full runs are fast at the median and bounded at the tail

Across the 27 full runs (outcome `complete`), counting only warm ones, the
client-side round trip has **p50 ≤ 8 s** and **p95 ≤ 75 s**, and none
returns 5xx.

**Why this target:**

On my laptop a full run took about 2.2 s: one MCP subprocess spawn for
`search_listings` plus two model calls. The model calls wait on the network,
so Render shouldn't change them much. Spawning the MCP subprocess starts a
whole new Python interpreter that imports `mcp`, and that work is CPU-bound.
The free tier's 0.1 CPU could make it close to ten times slower than on my
laptop. 8 s covers that and still fails if something else is slow.

The tail target is set by `generate.py`, not by the hosting. A session sends
18 model calls in roughly a minute, and `generate.py` paces at 15 a minute,
so I expect about one run per session to wait out the rest of the minute
(up to ~60 s). With 27 runs, p95 is the 26th slowest, so the 3 expected
pacing waits are inside it. 75 s allows exactly one pacing wait per run.
A run that waited twice, or one that got a 429 the pacing should have
prevented, would go past it. The no-5xx part checks that `--timeout 300` does
its job: gunicorn's default 30 s would have killed exactly the runs that
were waiting.

---

## D3. Every request leaves exactly one log line, and the line tells the truth

Each of the 45 `/ask` requests has **exactly one** line in `/logs` with the
same `request_id` as its `X-Request-Id` header. That line's `outcome` agrees
with what the client got back (`complete`, `no_match`, `bad_request`, ...) —
**45 of 45**.

**Why this target:**

The log line is written by code on the response path. No model is involved
and nothing in it is random, so it can't be right only some of the time.
Anything short of 45 of 45 is a bug. A run that crashed might log the wrong
outcome, or none, which is exactly when I'd need the log. The one realistic
way to lose a line is outside my code: if gunicorn kills a worker or Render
restarts the instance mid-session, the request gets no response and
`/logs` loses its memory. I'm counting that as a miss on purpose, because a
log that disappears when the instance restarts is the failure this criterion
is meant to catch. The agreement check is there because one line per request
is easy to get. A line with `outcome: complete` on a request that actually
failed is worse than no line at all.

---

## D4. Peak memory stays under half the plan

In every session, the highest `peak_rss_mb + children_peak_rss_mb` among
that session's log lines is **≤ 256 MB** — **3 of 3 sessions**.

**Why this target:**

The free plan has 512 MB. Locally, the server peaked at about 101 MB and the
MCP subprocess at about 58 MB, 159 MB in total. Python on Linux can come out
somewhat higher. 256 MB is half the plan, and I chose half for a reason:
`serve.py`'s lock is the only thing that stops two agent runs, and two MCP
subprocesses, from running at once. If the lock ever failed, a second copy
of the work would still fit under 512 MB rather than getting the instance
OOM-killed. The children figure is the largest single MCP subprocess, not a
sum. That's correct here because the lock means only one runs at a time.
