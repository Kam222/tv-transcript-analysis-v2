# TV Transcript Scraper (Phase 1)
<<<<<<< HEAD

## Overview
Scrapes TV show transcripts from ForeverDreaming, cleans them up, and tries to make sense of what’s actually being said. Built because finding structured TV dialogue data is surprisingly annoying. This is the **Phase 1** prototype – it works, but it’s far from perfect.

## How It Works
- **Step 1:** Enter a TV show name, scraper finds transcripts.
- **Step 2:** Cleans the mess (removes HTML, timestamps, junk text).
- **Step 3:** Tries to categorize content using dumb-but-useful keyword matching.
- **Step 4:** Runs a basic sentiment analysis (because why not).
- **Step 5:** Dumps everything into a CSV.

## Install & Run
```bash
git clone https://github.com/yourusername/tv-transcript-analysis.git
cd tv-transcript-analysis
pip install -r requirements.txt
python tv_transcript.py
```

## What’s Inside?
- `tv_transcript.py` – The main script.
- `data/` – Where scraped transcripts live.
- `reports/` – Processed CSV outputs.

## Issues & Future Work
🚨 **Known Bugs:**
- Regex for extracting season/episode metadata is broken.
- Picks up random forum posts as episodes (oops).
- Keyword matching is way too naive.
- Sentiment analysis lacks depth (detects “sorry” but not sarcasm).

🔜 **Next Steps (Phase 2):**
- Scale up the scraper (handle full seasons, retry logic, proxy rotation).
- Store data in a structured format (probably PostgreSQL or MongoDB).
- Smarter annotations (expand keywords, explore weak supervision).
- Start experimenting with ML models (BERT for classification?).

## License
MIT – use, break, improve, share.

🚀 Built in July 2023 as part of a research project at MIT/gov lab.

=======
>>>>>>> 804f7b4 (Initial commit)
