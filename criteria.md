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
