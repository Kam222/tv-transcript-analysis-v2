#!/usr/bin/env python3
import re
import csv
import json
import logging
from typing import List, Dict, Tuple, Any, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download required NLTK resources
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')
nltk.download('wordnet')

# ------------------------------------------------------------------------------
# Constants & Regex Patterns
# ------------------------------------------------------------------------------
BASE_URL: str = "https://transcripts.foreverdreaming.org"
TV_SHOWS_URL: str = urljoin(BASE_URL, "/viewforum.php?f=1662")  
EPISODE_REGEX: re.Pattern = re.compile(r'[Ss](\d+)[Ee](\d+)')
TIMESTAMP_REGEX: re.Pattern = re.compile(r'\[?\d{1,2}:\d{2}(?::\d{2})?\]?')
NEARBY_WINDOW: int = 50

NEGATIVE_ELEMENTS: Dict[str, str] = {
    "racism": r'\bracism\b',
    "sexism": r'\bsexism\b',
    "heterosexism/homophobia": r'\b(heterosexism|homophobia)\b',
    "corruption": r'\bcorruption\b',
    "domestic violence": r'\bdomestic violence\b',
    "vice/alcoholism/infidelity": r'\b(vice|alcoholism|infidelity)\b',
    "family and friends": r'\bfamily and friends\b',
    "mistakes/failures": r'\b(mistakes|failures)\b',
    "offensive/crude language": r'\b(offensive|crude language)\b'
}

POSITIVE_ELEMENTS: Dict[str, str] = {
    "police solve case": r'\bpolice solve case\b',
    "highlight policing initiatives": r'\bhighlight policing initiatives\b',
    "direct danger to police characters": r'\bdirect danger to police characters\b',
    "service to community": r'\bservice to community\b',
    "use of technology": r'\buse of technology\b',
    "protect others from immediate danger": r'\bprotect others from immediate danger\b',
    "family and friends": r'\bfamily and friends\b',
    "integrity/commitment to principles": r'\b(integrity|commitment to principles)\b'
}

TONE_KEYWORDS: Dict[str, List[str]] = {
    "empathetic": ["sorry", "apologize", "compassion", "empathy", "understand"],
    "resolute": ["determined", "resolve", "fight", "stand", "strong"],
    "critical": ["criticize", "blame", "fault", "accuse"],
    "optimistic": ["hope", "optimistic", "bright", "positive"]
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger: logging.Logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------------------------
def fetch_page(url: str) -> str:
    """Retrieve the HTML content of a given URL."""
    logger.info(f"Fetching URL: {url}")
    response = requests.get(url)
    response.raise_for_status()
    logger.debug(f"Fetched {len(response.text)} characters from {url}")
    return response.text


def extract_season_episode(title: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract 'SxxExx' pattern from the episode title (if present)."""
    match = EPISODE_REGEX.search(title)
    if match:
        season, episode = match.groups()
        logger.debug(f"Extracted season: {season}, episode: {episode} from title: {title}")
        return season, episode
    logger.debug(f"No season/episode info found in title: {title}")
    return None, None


def clean_transcript(raw_text: str) -> str:
    """Convert text to lowercase, remove HTML tags, timestamps, and extra whitespace."""
    logger.info("Cleaning transcript text")
    text: str = raw_text.lower()
    text = re.sub(r'<[^>]+>', '', text)         # remove HTML tags
    text = re.sub(TIMESTAMP_REGEX, '', text)    # remove timestamps like [00:01:23]
    text = re.sub(r'\s+', ' ', text).strip()    # remove extra whitespace
    logger.debug(f"Cleaned transcript (first 100 chars): {text[:100]}...")
    return text


def tokenize_and_lemmatize(text: str) -> str:
    """Tokenize, remove stopwords/punctuation, and lemmatize the transcript."""
    logger.info("Tokenizing and lemmatizing transcript")
    tokens: List[str] = word_tokenize(text)
    stop_words: set = set(stopwords.words('english'))
    lemmatizer: WordNetLemmatizer = WordNetLemmatizer()
    processed_tokens: List[str] = [
        lemmatizer.lemmatize(token) for token in tokens if token.isalnum() and token not in stop_words
    ]
    final_text: str = ' '.join(processed_tokens)
    logger.debug(f"Processed tokens (first 20): {processed_tokens[:20]}")
    return final_text


def annotate_story_elements(transcript: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Find occurrences of negative and positive story elements in the transcript text.
    For negative elements, store counts + timestamps.
    For positive elements, store counts + up to 3 'checks' with local context.
    """
    logger.info("Annotating story elements")
    negative_annotations: Dict[str, Any] = {}
    positive_annotations: Dict[str, Any] = {}

    # Negative elements
    for element, pattern in NEGATIVE_ELEMENTS.items():
        regex = re.compile(pattern, re.IGNORECASE)
        matches = list(regex.finditer(transcript))
        count: int = len(matches)
        timestamps: List[str] = []
        for match in matches:
            start = max(0, match.start() - NEARBY_WINDOW)
            end = match.end() + NEARBY_WINDOW
            nearby_text = transcript[start:end]
            ts_matches = TIMESTAMP_REGEX.findall(nearby_text)
            timestamps.extend(ts_matches)
            logger.debug(f"Negative element '{element}' found at position {match.start()} with timestamps: {ts_matches}")
        negative_annotations[element] = {"count": count, "timestamps": timestamps}

    # Positive elements
    for element, pattern in POSITIVE_ELEMENTS.items():
        regex = re.compile(pattern, re.IGNORECASE)
        matches = list(regex.finditer(transcript))
        count: int = len(matches)
        checks: List[Dict[str, Any]] = []
        # Only store up to 3 checks
        for i, match in enumerate(matches):
            if i >= 3:
                break
            start = max(0, match.start() - NEARBY_WINDOW)
            end = match.end() + NEARBY_WINDOW
            nearby_text = transcript[start:end]
            ts_matches = TIMESTAMP_REGEX.findall(nearby_text)
            checks.append({"check": f"Check {i+1}", "timestamps": ts_matches})
            logger.debug(f"Positive element '{element}' found at position {match.start()} with timestamps: {ts_matches}")
        positive_annotations[element] = {"count": count, "checks": checks}

    return negative_annotations, positive_annotations


def analyze_narrative_tone(transcript: str) -> Dict[str, Any]:
    """
    Count occurrences of tone keywords in the transcript
    (e.g., empathetic, resolute, critical, optimistic).
    """
    logger.info("Performing narrative tone analysis")
    tone_counts: Dict[str, int] = {tone: 0 for tone in TONE_KEYWORDS}
    tokens: List[str] = word_tokenize(transcript.lower())

    for token in tokens:
        for tone, keywords in TONE_KEYWORDS.items():
            if token in keywords:
                tone_counts[tone] += 1
                logger.debug(f"Token '{token}' contributes to tone '{tone}'")

    return tone_counts

# ------------------------------------------------------------------------------
# Scraping Functions
# ------------------------------------------------------------------------------
def scrape_all_tv_show_forums() -> List[Dict[str, str]]:
    """
    Start from the 'TV Shows' forum (f=1662) and gather links to specific TV shows.
    This function handles pagination by following the 'Next' link, if present.
    Returns a list of dicts: {title, url}.
    """
    logger.info("Scraping from the 'TV Shows' forum (f=1662).")
    all_shows: List[Dict[str, str]] = []
    next_page_url: str = TV_SHOWS_URL

    while True:
        html = fetch_page(next_page_url)
        soup = BeautifulSoup(html, "html.parser")

        # Each subforum for a show is typically a link with class 'forumtitle'
        # or 'forumtitle notranslate'. We'll check both.
        forum_links = soup.find_all('a', class_=lambda c: c and 'forumtitle' in c.split())
        for fl in forum_links:
            title = fl.get_text(strip=True)
            href = fl.get('href', '')
            full_url = urljoin(BASE_URL, href)
            all_shows.append({"title": title, "url": full_url})
            logger.debug(f"TV show found: {title} -> {full_url}")

        # Next page for "TV Shows" forum
        next_link = soup.find('a', string='Next')
        if next_link and next_link.get('href'):
            next_page_url = urljoin(BASE_URL, next_link['href'])
            logger.info(f"Found next page under 'TV Shows': {next_page_url}")
        else:
            logger.info("No more pages under 'TV Shows'.")
            break

    logger.info(f"Total sub-forums (TV shows) found: {len(all_shows)}")
    return all_shows


def scrape_episode_links(show_url: str) -> List[Dict[str, Any]]:
    """
    Given the forum URL for a specific show, scrape all episode links,
    handling multi-page 'Next' pagination in that show forum.
    """
    logger.info(f"Scraping episode links from: {show_url}")
    episodes: List[Dict[str, Any]] = []
    next_page_url: Optional[str] = show_url

    while next_page_url:
        page_html: str = fetch_page(next_page_url)
        soup: BeautifulSoup = BeautifulSoup(page_html, 'html.parser')

        # Each episode is identified by <a class="topictitle">
        for a_tag in soup.find_all('a', class_='topictitle'):
            title: str = a_tag.get_text(strip=True)
            href: str = a_tag.get('href', '')
            episode_url: str = urljoin(BASE_URL, href)
            season, episode = extract_season_episode(title)
            episodes.append({
                "title": title,
                "season": season if season else "",
                "episode": episode if episode else "",
                "url": episode_url
            })
            logger.debug(f"Found episode: {title} (Season: {season}, Episode: {episode}) at {episode_url}")

        # Check for "Next" pagination link
        next_link = soup.find('a', string='Next')
        if next_link and next_link.get('href'):
            next_page_url = urljoin(BASE_URL, next_link['href'])
            logger.info(f"Found next page of episodes: {next_page_url}")
        else:
            next_page_url = None

    return episodes


def process_episode(episode: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch and process the text of a single episode.
    Returns dict containing cleaned transcript, story elements, tone, etc.
    """
    logger.info(f"Processing episode: {episode['title']}")
    episode_html: str = fetch_page(episode["url"])
    soup: BeautifulSoup = BeautifulSoup(episode_html, 'html.parser')

    # Usually transcripts are in 'div.postbody'
    post_body = soup.find('div', class_='postbody')
    if not post_body:
        logger.error(f"Transcript not found for episode: {episode['title']}")
        transcript_raw: str = ""
    else:
        transcript_raw = post_body.get_text(separator=" ", strip=True)

    # Keep the original text (lowercased) for annotation (timestamps, etc.)
    transcript_for_annotation: str = transcript_raw.lower()

    # Clean transcript for final analysis
    transcript_clean: str = clean_transcript(transcript_raw)
    transcript_processed: str = tokenize_and_lemmatize(transcript_clean)

    # Annotate story elements and tone
    negative_annotations, positive_annotations = annotate_story_elements(transcript_for_annotation)
    narrative_tone: Dict[str, Any] = analyze_narrative_tone(transcript_clean)

    return {
        "season": episode["season"],
        "episode": episode["episode"],
        "title": episode["title"],
        "cleaned_transcript": transcript_processed,
        "negative_story_elements": negative_annotations,
        "positive_story_elements": positive_annotations,
        "narrative_tone": narrative_tone
    }

# ------------------------------------------------------------------------------
# Main Entry Point
# ------------------------------------------------------------------------------
def main() -> None:
    """Main script function: gather TV show from user, find it, scrape episodes, annotate, save CSV."""
    tv_show: str = input("Enter TV show name: ").strip().lower()

    # 1. Gather all shows under 'TV Shows' forum (f=1662)
    all_shows = scrape_all_tv_show_forums()

    # 2. Match user input
    matched_forum = None
    for forum_data in all_shows:
        if forum_data["title"].lower() == tv_show:
            matched_forum = forum_data
            break

    # 3. Error if not found
    if not matched_forum:
        logger.error(f"TV show '{tv_show}' not found under 'TV Shows' (f=1662).")
        return

    # 4. Scrape episodes for that matched show
    show_url = matched_forum["url"]
    logger.info(f"Found TV show '{matched_forum['title']}' at URL: {show_url}")
    episodes: List[Dict[str, Any]] = scrape_episode_links(show_url)
    logger.info(f"Total episodes found for '{matched_forum['title']}': {len(episodes)}")

    # 5. Process each episode
    processed_episodes: List[Dict[str, Any]] = []
    for ep in episodes:
        processed_episodes.append(process_episode(ep))

    # 6. Write data to CSV
    csv_columns: List[str] = [
        "Season", "Episode", "Title", "Cleaned Transcript",
        "Negative Story Elements", "Positive Story Elements", "Narrative Tone Annotations"
    ]
    csv_file: str = "transcript_analysis.csv"

    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=csv_columns)
        writer.writeheader()
        for ep_data in processed_episodes:
            writer.writerow({
                "Season": ep_data["season"],
                "Episode": ep_data["episode"],
                "Title": ep_data["title"],
                "Cleaned Transcript": ep_data["cleaned_transcript"],
                "Negative Story Elements": json.dumps(ep_data["negative_story_elements"]),
                "Positive Story Elements": json.dumps(ep_data["positive_story_elements"]),
                "Narrative Tone Annotations": json.dumps(ep_data["narrative_tone"])
            })

    logger.info(f"CSV report generated: {csv_file}")

if __name__ == '__main__':
    main()
