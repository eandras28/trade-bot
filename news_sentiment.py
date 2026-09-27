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


def parse_llm_json(raw_text: str) -> Dict[str, Any]:
    """Parse JSON from LLM output, stripping markdown code blocks if present."""
    if not raw_text:
        raise ValueError("Empty response text from LLM")
    cleaned = raw_text.strip()
    
    # Try direct parse
    try:
        return json.loads(cleaned)
    except Exception:
        pass
        
    # Extract from markdown code block ```json ... ```
    if "```" in cleaned:
        for block in cleaned.split("```"):
            block = block.strip()
            if block.startswith("json"):
                block = block[4:].strip()
            try:
                return json.loads(block)
            except Exception:
                continue
                
    # Search for first { and last }
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(cleaned[start:end+1])
        
    raise ValueError(f"Could not parse valid JSON from response: {cleaned[:150]}")


class GeminiEnergyAnalyst:
    """LLM Contextual Reasoning for Energy News using Google Gemini."""

    def __init__(self, api_key: Optional[str] = None):
        raw_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
        self.api_key = raw_key.strip("'\" \n\r\t")
        self.client = None
        self.init_error = None
        self.last_error = None

        if not self.api_key:
            self.init_error = "No API key provided."
        else:
            if GENAI_AVAILABLE:
                try:
                    self.client = genai.Client(api_key=self.api_key)
                except Exception as e:
                    self.init_error = f"SDK Client init error: {e}"
                    print(f"[!] Could not initialize Gemini Client: {e}")

    @property
    def is_active(self) -> bool:
        return bool(self.api_key)

    def get_supported_models(self) -> List[tuple]:
        """
        Dynamically query Google's ModelService.ListModels to discover exactly
        which models are provisioned and active for this specific API key.
        Returns a list of (clean_model_name, api_version) tuples.
        """
        import requests
        discovered = []
        last_list_err = None

        for api_ver in ["v1beta", "v1"]:
            try:
                url = f"https://generativelanguage.googleapis.com/{api_ver}/models?key={self.api_key}"
                resp = requests.get(url, timeout=12)
                if resp.status_code == 200:
                    data = resp.json()
                    for m in data.get("models", []):
                        methods = m.get("supportedGenerationMethods", [])
                        if "generateContent" in methods:
                            name = m.get("name", "")
                            if name.startswith("models/"):
                                name = name[7:]
                            discovered.append((name, api_ver))
                    if discovered:
                        break
                else:
                    try:
                        err_msg = resp.json().get("error", {}).get("message") or resp.text
                    except Exception:
                        err_msg = resp.text
                    last_list_err = f"{api_ver} HTTP {resp.status_code}: {err_msg}"
            except Exception as e:
                last_list_err = f"{api_ver} error: {e}"

        if not discovered and last_list_err:
            self.last_error = f"ListModels failed: {last_list_err}"

        # Sort: prioritize flash models, then pro, favoring newer releases
        def priority(item):
            name, _ = item
            score = 0
            n_lower = name.lower()
            if "flash" in n_lower:
                score += 100
            elif "pro" in n_lower:
                score += 50
            if "2.5" in name:
                score += 40
            elif "2.0" in name:
                score += 30
            elif "1.5" in name:
                score += 20
            if "latest" in n_lower:
                score += 10
            if "exp" in n_lower or "preview" in n_lower:
                score -= 15
            return -score

        discovered.sort(key=priority)
        return discovered

    def _call_rest_api(self, model_name: str, prompt: str, api_ver: str = "v1beta") -> Dict[str, Any]:
        """Direct REST fallback to Google Generative Language API."""
        import requests
        clean_name = model_name[7:] if model_name.startswith("models/") else model_name
        url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{clean_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }
        resp = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=25)
        
        # If model does not support responseMimeType (returns 400), retry without it
        if resp.status_code == 400 and "responseMimeType" in resp.text:
            payload["generationConfig"] = {"temperature": 0.1}
            resp = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=25)

        if resp.status_code != 200:
            try:
                err_data = resp.json().get("error", {})
                msg = err_data.get("message") or resp.text
                status = err_data.get("status", "")
                raise RuntimeError(f"HTTP {resp.status_code} ({status}): {msg}")
            except Exception as parse_err:
                if "HTTP " in str(parse_err):
                    raise parse_err
                raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")

        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"No candidates in Gemini response: {data}")
        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return parse_llm_json(text)

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
        # Discover actual available models for this specific API key
        available = self.get_supported_models()
        if not available:
            print(f"[!] Warning: ListModels did not return models. Error: {self.last_error}")
            available = [
                ('gemini-2.0-flash', 'v1beta'),
                ('gemini-1.5-flash', 'v1beta'),
                ('gemini-1.5-flash-latest', 'v1beta'),
                ('gemini-1.5-pro-latest', 'v1beta'),
                ('gemini-pro', 'v1')
            ]
        else:
            print(f"[✓] Discovered {len(available)} models for your key. Top choices: {[m[0] for m in available[:5]]}")

        for model_name, api_ver in available[:6]:
            clean_name = model_name[7:] if model_name.startswith("models/") else model_name

            # 1. Try google-genai SDK if available
            if self.client is not None:
                try:
                    response = self.client.models.generate_content(
                        model=clean_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.1
                        )
                    )
                    data = parse_llm_json(response.text)
                    return {
                        "score": round(float(data.get("score", 0.0)), 3),
                        "regime": data.get("regime", "NEUTRAL"),
                        "rationale": data.get("rationale", ""),
                        "model_used": clean_name
                    }
                except Exception as e:
                    self.last_error = f"SDK {clean_name} failed: {e}"

            # 2. Direct REST API fallback
            try:
                data = self._call_rest_api(clean_name, prompt, api_ver=api_ver)
                return {
                    "score": round(float(data.get("score", 0.0)), 3),
                    "regime": data.get("regime", "NEUTRAL"),
                    "rationale": data.get("rationale", ""),
                    "model_used": f"{clean_name} ({api_ver} REST)"
                }
            except Exception as e:
                self.last_error = f"REST {clean_name} ({api_ver}) failed: {e}"
                continue

        print(f"[!] Gemini analysis error across all models: {self.last_error}")
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
