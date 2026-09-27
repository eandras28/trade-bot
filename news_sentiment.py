"""News Scraper and Hybrid Sentiment Engine (Gemini LLM Contextual Reasoning + Energy Lexicon Fallback)."""
import os
import json
from typing import Dict, List, Any, Optional
import feedparser
import yfinance as yf
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Try importing google.genai
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


# Specialized domain dictionary for oil & commodities fallback
ENERGY_LEXICON = {
    "production cut": 2.5,
    "output cut": 2.5,
    "quota cut": 2.0,
    "inventory draw": 2.2,
    "stockpile draw": 2.0,
    "drawdown": 1.5,
    "supply disruption": 2.4,
    "pipeline outage": 2.0,
    "refinery outage": 1.8,
    "drone strike": 2.2,
    "tanker seized": 2.0,
    "sanctions": 1.8,
    "embargo": 2.0,
    "tight supply": 2.0,
    "backwardation": 1.5,
    "spr refill": 1.5,
    "record demand": 2.0,
    "strong demand": 1.8,
    "upgrade": 1.5,
    "dividend hike": 1.5,
    "buyback": 1.5,
    "inventory build": -2.2,
    "stockpile build": -2.2,
    "production increase": -2.2,
    "output hike": -2.2,
    "supply glut": -2.8,
    "oil glut": -2.8,
    "oversupply": -2.5,
    "surplus": -2.0,
    "quota breach": -2.0,
    "cheating on quotas": -2.2,
    "ceasefire": -2.0,
    "peace talks": -1.8,
    "de-escalation": -1.8,
    "demand destruction": -2.5,
    "demand slump": -2.2,
    "recession": -2.2,
    "economic slowdown": -2.0,
    "downgrade": -1.8,
    "contango": -1.5,
    "windfall tax": -1.8
}


class GeminiEnergyAnalyst:
    """LLM Contextual Reasoning for Energy News using Google Gemini."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.client = None
        if GENAI_AVAILABLE and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[!] Could not initialize Gemini Client: {e}")

    @property
    def is_active(self) -> bool:
        return self.client is not None

    def analyze_news_batch(self, target_name: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a batch of headlines using Gemini with deep commodity context reasoning.
        """
        if not self.is_active or not articles:
            return {}

        headlines_text = "\n".join([
            f"- [{a.get('publisher', 'News')}]: {a.get('title', '')}. {a.get('summary', '')}"
            for a in articles[:6]
        ])

        prompt = f"""You are a Senior Quantitative Commodity Analyst at an energy hedge fund.
Analyze these breaking headlines for {target_name} and determine the fundamental price impact over the next 1-5 trading days.

Headlines:
{headlines_text}

Consider:
- Physical supply/demand shifts and OPEC+ quota discipline.
- EIA inventory surprises (unexpected builds vs draws).
- Geopolitical risk premiums (Middle East, sanctions, chokepoint transit).
- Forward guidance vs corporate PR spin.

Respond strictly with a JSON object in this format:
{{
  "score": <float between -1.0 (extreme bearish) and 1.0 (extreme bullish)>,
  "regime": "<STRONG BULLISH | MILD BULLISH | NEUTRAL | MILD BEARISH | STRONG BEARISH>",
  "rationale": "<A sharp 1-2 sentence executive explanation of the fundamental reason>"
}}
"""
        # Try available Google AI Studio models in order of stability
        candidate_models = ['gemini-1.5-flash', 'gemini-2.0-flash', 'gemini-1.5-pro']
        last_error = None

        for model_name in candidate_models:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )
                data = json.loads(response.text)
                return {
                    "score": round(float(data.get("score", 0.0)), 3),
                    "regime": data.get("regime", "NEUTRAL"),
                    "rationale": data.get("rationale", ""),
                    "model_used": model_name
                }
            except Exception as e:
                last_error = e
                continue

        print(f"[!] Gemini analysis error across all models: {last_error}")
        return {}


class OilSentimentAnalyzer:
    def __init__(self):
        # 1. Lexicon engine
        self.vader = SentimentIntensityAnalyzer()
        self.vader.lexicon.update(ENERGY_LEXICON)

        # 2. LLM engine
        self.llm_analyst = GeminiEnergyAnalyst()
        if self.llm_analyst.is_active:
            print("[✓] AI Context Engine: Google Gemini LLM Active (Deep Context Reasoning)")
        else:
            print("[i] AI Context Engine: Energy-Domain NLP Lexicon Active (Set GEMINI_API_KEY for LLM reasoning)")

    def analyze_text(self, text: str) -> float:
        if not text:
            return 0.0
        scores = self.vader.polarity_scores(text)
        return scores['compound']

    def fetch_ticker_news(self, symbol: str, limit: int = 8) -> List[Dict[str, Any]]:
        articles = []
        try:
            ticker = yf.Ticker(symbol)
            items = ticker.news or []
            for item in items[:limit]:
                content = item.get("content", {})
                title = content.get("title") or item.get("title") or ""
                summary = content.get("summary") or item.get("summary") or ""
                pub_date = content.get("pubDate") or item.get("pubDate") or ""
                provider = content.get("provider", {}).get("displayName") or item.get("publisher") or "Yahoo Finance"
                link = content.get("canonicalUrl", {}).get("url") or item.get("link") or ""

                if not title:
                    continue

                full_text = f"{title}. {summary}"
                score = self.analyze_text(full_text)

                articles.append({
                    "title": title,
                    "summary": summary,
                    "score": round(score, 3),
                    "publisher": provider,
                    "pubDate": pub_date,
                    "url": link,
                    "type": f"{symbol} News"
                })
        except Exception as e:
            print(f"Error fetching ticker news for {symbol}: {e}")

        return articles

    def fetch_macro_crude_news(self, limit: int = 12) -> List[Dict[str, Any]]:
        articles = []
        try:
            query = "crude+oil+OR+OPEC+OR+petroleum+inventory"
            url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(url)

            for entry in feed.entries[:limit]:
                title = entry.get("title", "")
                published = entry.get("published", "")
                link = entry.get("link", "")
                source = entry.get("source", {}).get("title", "Google News")

                score = self.analyze_text(title)
                articles.append({
                    "title": title,
                    "summary": "",
                    "score": round(score, 3),
                    "publisher": source,
                    "pubDate": published,
                    "url": link,
                    "type": "Macro Crude / OPEC"
                })
        except Exception as e:
            print(f"Error fetching macro news: {e}")

        return articles

    def get_market_sentiment_report(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Aggregate sentiment for macro crude plus each symbol using Gemini LLM if available,
        falling back seamlessly to the domain lexicon.
        """
        macro_news = self.fetch_macro_crude_news(limit=10)

        # 1. Macro Analysis
        macro_rationale = ""
        if self.llm_analyst.is_active and macro_news:
            llm_macro = self.llm_analyst.analyze_news_batch("WTI Crude Oil & OPEC", macro_news)
            if llm_macro:
                avg_macro_score = llm_macro["score"]
                macro_rationale = llm_macro.get("rationale", "")
            else:
                macro_scores = [a["score"] for a in macro_news if a["score"] != 0]
                avg_macro_score = sum(macro_scores) / len(macro_scores) if macro_scores else 0.0
        else:
            macro_scores = [a["score"] for a in macro_news if a["score"] != 0]
            avg_macro_score = sum(macro_scores) / len(macro_scores) if macro_scores else 0.0
            if avg_macro_score > 0.1:
                macro_rationale = "Physical supply tightening or geopolitical risk premiums dominating."
            elif avg_macro_score < -0.1:
                macro_rationale = "Unexpected inventory builds or diplomatic de-escalation dampening crude prices."
            else:
                macro_rationale = "Macro crude fundamentals balanced with no strong directional catalyst."

        # 2. Per-symbol Analysis
        symbol_reports = {}
        for sym in symbols:
            sym_news = self.fetch_ticker_news(sym, limit=6)
            sym_rationale = ""

            if self.llm_analyst.is_active and sym_news:
                llm_sym = self.llm_analyst.analyze_news_batch(sym, sym_news)
                if llm_sym:
                    avg_sym_score = llm_sym["score"]
                    sym_rationale = llm_sym.get("rationale", "")
                else:
                    scores = [a["score"] for a in sym_news if a["score"] != 0]
                    avg_sym_score = sum(scores) / len(scores) if scores else 0.0
            else:
                scores = [a["score"] for a in sym_news if a["score"] != 0]
                avg_sym_score = sum(scores) / len(scores) if scores else 0.0

            # Composite: 50% ticker, 50% macro
            composite = 0.5 * avg_sym_score + 0.5 * avg_macro_score

            if composite >= 0.25:
                regime = "🟢 STRONG BULLISH CATALYST"
            elif composite >= 0.08:
                regime = "🌱 MILD BULLISH"
            elif composite <= -0.25:
                regime = "🛑 STRONG BEARISH / SHORT"
            elif composite <= -0.08:
                regime = "🔻 MILD BEARISH"
            else:
                regime = "⚪ NEUTRAL"

            symbol_reports[sym] = {
                "composite_score": round(composite, 3),
                "ticker_score": round(avg_sym_score, 3),
                "macro_score": round(avg_macro_score, 3),
                "sentiment_regime": regime,
                "news_count": len(sym_news),
                "rationale": sym_rationale or macro_rationale,
                "top_articles": sorted(sym_news, key=lambda x: abs(x["score"]), reverse=True)[:3]
            }

        return {
            "macro_score": round(avg_macro_score, 3),
            "macro_rationale": macro_rationale,
            "engine_mode": "Gemini LLM Contextual" if self.llm_analyst.is_active else "Energy Domain Lexicon",
            "macro_news_count": len(macro_news),
            "top_macro_news": sorted(macro_news, key=lambda x: abs(x["score"]), reverse=True)[:5],
            "symbols": symbol_reports
        }
