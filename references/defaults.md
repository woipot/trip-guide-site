# Default brief

These defaults fill the gaps when the traveller doesn't specify something. They come from real use of this skill and produced sites people liked. The traveller's own words always win. Fork the repo and edit this file to make the skill yours.

**Language and money**
- Write the site in the traveller's language (the bundled UI strings are Russian; translate them in `scripts/build_site.py` and `assets/*.js` if you need another language).
- Show prices in local currency with a conversion to the traveller's home currency, and state the rate used.
- Price everything for the whole party, and say so on the page.

**Look and feel**
- A plain table-style report feels "technical". Use a big hero photo, real photos for days, dishes and guide chapters, a route map for every day, editorial typography and interactivity.
- Use three pages: plan, pocket guide, phrasebook. The guide and the phrasebook do not belong inside the plan.
- Leave optional "add to the trip" blocks off the page. Offer extras in the chat instead.

**Program**
- "A week or a bit more" usually means about 10–11 days. When the program grows past what was asked, cut the weaker days instead of extending the trip.
- Fix the program as a table in chat before any heavy rebuild.
- Show the distance between stops and the walking total for every day.
- Markets, tastings and other hands-on local experiences tend to be the most remembered parts. Keep one or two.

**Food**
- Everyday meals: local cafés and street food, with a per-meal cap per person. Use a moderate local cap when none is given.
- Fine dining: at most one place for the whole trip, chosen where the route already passes, not necessarily on the last day.

**Hotels**
- A comfortable 4★ chain hotel next to a metro hub, not luxury. Show 5★ hotels as optional upgrades in the picker.
- Stay one night in another city only when it saves real door-to-door transit time. Otherwise plan day trips.
- If the traveller flies with carry-on only and plans to shop, cover the baggage allowance on the return flight and where to buy a suitcase.

**Options**
- When an upgrade is cheap compared with what it adds (boat deck, observation level, massage tier, train class, taxi instead of metro), show it as a choice. Add a one-line "what you get" and the price difference in home currency. Mark the one you recommend.

**Shopping and souvenirs**
- Ask what kind of shopping matters, if any, before planning shopping days.
- Add a short list of cheap souvenirs, each with its price, where it is on the route and a tip.

**Guide**
- Write detailed, fact-dense, illustrated chapters with read-aloud and step-by-step modes. Generate them with parallel guide-writer agents (`references/guide-agents.md`).
