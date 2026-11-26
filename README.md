# BGMI / PMGC match calendar

Files
- index.html: the website (match data is in the block marked EDIT YOUR DATA HERE)
- links.json: stream links found automatically (do not edit by hand)
- fetch_links.py: finds YouTube streams and writes links.json
- .github/workflows/update-links.yml: runs the script every 2 hours

How links are chosen
1. A link typed into index.html always wins.
2. Otherwise the site looks in links.json for a stream on the same day (IST) whose title has the right words
   (for example "PMGC" and "Gauntlet"). The words are set in LINK_RULES in index.html.

One-time setup: see the chat instructions (API key, GitHub secret, Vercel import).
