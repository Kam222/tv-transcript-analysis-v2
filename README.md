# TV Transcript Scraper – Phase 1 🚀

## Overview
This is **Phase 1** of a TV transcript scraper designed to pull, clean, and structure dialogue from ForeverDreaming. Because, let’s be honest, finding structured TV dialogue data is so much harder than it should be.

It’s a working prototype—**far from perfect**, but it gets the job done. Right now, it scrapes, cleans, and does some basic analysis. Future iterations will hopefully be **smarter, faster, and more robust**.

---

## How It Works 🔍
1. **Find transcripts** – Enter a TV show name, and the scraper locates available transcripts.  
2. **Clean up the mess** – Removes HTML, timestamps, and other junk.  
3. **Tag & categorize** – Uses simple keyword matching to categorize content.  
4. **Sentiment analysis (lightweight)** – Because why not?  
5. **Output to CSV** – Structured data, ready for analysis.  

---

## Installation & Running
```bash
git clone https://github.com/yourusername/tv-transcript-analysis.git
cd tv-transcript-analysis
pip install -r requirements.txt
python tv_transcript.py
```

---

## Project Structure 🗂️
- **`tv_transcript.py`** – The main script that runs everything.  
- **`data/`** – Where raw transcripts live.  
- **`reports/`** – Processed CSV outputs.  

---

## Issues & Future Work
### 🚨 Known Bugs
- **Regex extraction is messy** – Season/episode metadata parsing is unreliable.  
- **Noise from forums** – Sometimes picks up random forum posts as "episodes."  
- **Keyword matching is dumb** – Too many false positives, needs better heuristics.  
- **Sentiment analysis is shallow** – Detects words like “sorry” but fails on sarcasm.  

### 🔜 What’s Next? (Phase 2)
- **Scale up** – Full season handling, retry logic, proxy rotation.  
- **Database support** – PostgreSQL or MongoDB for structured storage.  
- **Smarter annotations** – Expand keyword matching, explore weak supervision.  
- **Machine learning** – Maybe throw BERT at it for classification?  

---

## License 📜
**MIT** – Use it, break it, improve it, share it.

🚀 Built in **July 2023** as part of a research project at MIT GOV/Lab.
