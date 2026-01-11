# engine.py
# TakeItIz | Anti-Advisor engine v17.2
# FIX: Added 'end_date' parameter to calculate_costs function signature 
# to match the call from app.py.

from __future__ import annotations
import datetime as _dt
import math
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import requests
from urllib.parse import quote

@dataclass
class FxQuote:
    base: str
    quote: str
    rate: float
    ts: float

class TakeItIzEngine:
    def __init__(self, user_agent: str = "TakeItIz/1.0", timeout_s: int = 12):
        self.user_agent = user_agent
        self.timeout_s = timeout_s
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": self.user_agent})
        
        self._fx_cache: Dict[Tuple[str, str], FxQuote] = {}
        
        # ROTAÇÃO DE SERVIDORES
        self._overpass_endpoints = [
            "https://overpass-api.de/api/interpreter", 
            "https://overpass.kumi.systems/api/interpreter",
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
        ]

    # --- HELPERS ---
    @staticmethod
    def _ensure_date(d: Any) -> _dt.date:
        if isinstance(d, _dt.datetime): return d.date()
        if isinstance(d, _dt.date): return d
        return _dt.date.today()

    @staticmethod
    def _fmt_int_ptbr(n: float) -> str:
        return f"{n:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @classmethod
    def _fmt_money(cls, n: float, ccy: str) -> str:
        s = {"BRL": "R$", "USD": "$", "EUR": "€", "GBP": "£"}.get(ccy, ccy)
        return f"{s} {cls._fmt_int_ptbr(n)}"

    # --- CÂMBIO ---
    def _fx_from_er_api(self, base: str) -> Optional[Dict[str, float]]:
        try:
            r = self._session.get(f"https://open.er-api.com/v6/latest/{base.upper()}", timeout=5)
            return {k.upper(): float(v) for k, v in r.json().get("rates", {}).items()} if r.status_code == 200 else None
        except: return None

    def get_fx_rate(self, base: str, quote: str, max_age_s: int = 43200) -> float:
        base, quote = base.upper(), quote.upper()
        if base == quote: return 1.0
        key = (base, quote)
        if key in self._fx_cache and (time.time() - self._fx_cache[key].ts) < max_age_s:
            return self._fx_cache[key].rate
        rates = self._fx_from_er_api(base)
        if rates and quote in rates:
            self._fx_cache[key] = FxQuote(base, quote, rates[quote], time.time())
            return rates[quote]
        if base != "USD" and quote != "USD":
            r1 = self.get_fx_rate(base, "USD")
            r2 = self.get_fx_rate("USD", quote)
            return r1 * r2
        return 1.0

    # --- GEOCODING ---
    def geocode_city(self, city: str) -> Dict[str, Any]:
        try:
            headers = {"User-Agent": "TakeItIzApp/1.0"}
            r = requests.get("https://nominatim.openstreetmap.org/search", 
                                params={"q": city, "format": "json", "limit": 1, "addressdetails": 1}, 
                                headers=headers, timeout=8)
            if r.status_code != 200 or not r.json(): return {"ok": False}
            hit = r.json()[0]
            return {
                "ok": True, "lat": float(hit["lat"]), "lon": float(hit["lon"]),
                "country_code": hit.get("address", {}).get("country_code", "").upper(),
                "display_name": hit.get("display_name")
            }
        except: return {"ok": False}

    # --- MÓDULO 1: CUSTOS (CORRIGIDO) ---
    # Adicionado 'end_date' na lista de argumentos abaixo:
    def calculate_costs(self, city, country_code, start_date, end_date, travelers, include_lodging, vibe, style_norm, target_currency, lat):
        cc = country_code.upper()
        cost_idx, lodging_idx = 1.0, 1.0
        
        if cc in ["CH", "NO", "IS", "US", "SG"]: cost_idx, lodging_idx = 1.5, 1.6
        elif cc in ["GB", "FR", "DE", "IE", "JP", "AE", "AU"]: cost_idx, lodging_idx = 1.3, 1.35
        elif cc in ["BR", "AR", "MX", "ZA", "TH", "CN"]: cost_idx, lodging_idx = 0.65, 0.60
        
        city_clean = city.lower().replace("ã", "a").replace("á", "a").replace("ô", "o").replace("é", "e").replace("í", "i")
        
        if "york" in city_clean: cost_idx = 1.8; lodging_idx = 2.8 
        elif "paris" in city_clean: cost_idx = 1.5; lodging_idx = 1.9
        elif "london" in city_clean: cost_idx = 1.6; lodging_idx = 2.0
        elif "dubai" in city_clean: cost_idx = 1.5; lodging_idx = 1.8
        elif "paulo" in city_clean: cost_idx = 0.80; lodging_idx = 0.85 
        elif "rio" in city_clean: cost_idx = 0.75; lodging_idx = 0.95
        elif "varginha" in city_clean: cost_idx = 0.55; lodging_idx = 0.40

        month = start_date.month
        season_idx = 1.0
        is_north = (lat or 0) > 0
        if is_north and month in [6,7,8]: season_idx = 1.2
        if not is_north and month in [12,1,2]: season_idx = 1.25
        if "rio" in city_clean and month in [12,1,2]: season_idx = 1.6 

        base_usd = {
            "economico": {"food": 30, "transport": 5, "activities": 10, "misc": 5, "lodging": 60},
            "base":      {"food": 55, "transport": 12, "activities": 25, "misc": 15, "lodging": 110},
            "conforto":  {"food": 90, "transport": 25, "activities": 50, "misc": 25, "lodging": 200},
            "luxo":      {"food": 180, "transport": 60, "activities": 100, "misc": 60, "lodging": 450}
        }.get(style_norm.lower(), {"food": 55, "transport": 12, "activities": 25, "misc": 15, "lodging": 110})

        usd_to_target = self.get_fx_rate("USD", target_currency)
        total_usd = 0
        breakdown_usd = {}

        for k in ["food", "transport", "activities", "misc"]:
            val = base_usd[k] * travelers * cost_idx * season_idx
            if k == "activities" and "cultura" in vibe.lower(): val *= 1.3
            if k == "food" and "gastro" in vibe.lower(): val *= 1.4
            breakdown_usd[k] = val
            total_usd += val

        nightlife_usd = 0
        if "festa" in vibe.lower(): nightlife_usd = 50 * travelers * cost_idx
        breakdown_usd["nightlife"] = nightlife_usd
        total_usd += nightlife_usd

        lodging_val = 0
        if include_lodging:
            rooms = math.ceil(travelers / 2)
            lodging_val = base_usd["lodging"] * rooms * lodging_idx * season_idx
        breakdown_usd["lodging"] = lodging_val
        total_usd += lodging_val

        breakdown_final = {k: v * usd_to_target for k, v in breakdown_usd.items()}
        total_final = total_usd * usd_to_target
        
        return {
            "estimate": total_final,
            "range_low": total_final * 0.85,
            "range_high": total_final * 1.15,
            "breakdown": breakdown_final
        }

    # --- MÓDULO 2: MAPA ---
    def fetch_map_data(self, lat: float, lon: float, vibe_context: str = "mistão") -> Dict[str, Any]:
        vibe_lower = vibe_context.lower()
        limit = 35
        timeout_ql = "[timeout:12]"
        
        radius = 3500 
        big_radius = 12000 
        
        if "festa" in vibe_lower or "caos" in vibe_lower:
            query = f"""{timeout_ql}[out:json];(
                nwr["amenity"~"bar|pub|nightclub|casino"](around:{radius},{lat},{lon});
            );out center {limit};"""
            
        elif "natureza" in vibe_lower or "trilha" in vibe_lower:
            query = f"""{timeout_ql}[out:json];(
                nwr["natural"~"beach|peak|water|wood|scrub|coastline"](around:{big_radius},{lat},{lon});
                nwr["leisure"~"park|nature_reserve"](around:{big_radius},{lat},{lon});
                nwr["tourism"~"viewpoint|attraction"](around:{big_radius},{lat},{lon});
            );out center {limit};"""
            
        elif "cultura" in vibe_lower:
            query = f"""{timeout_ql}[out:json];(
                nwr["tourism"~"museum|gallery|artwork|historic"](around:{radius},{lat},{lon});
                nwr["amenity"="theatre"](around:{radius},{lat},{lon});
            );out center {limit};"""
            
        elif "gastro" in vibe_lower:
            query = f"""{timeout_ql}[out:json];(
                nwr["amenity"~"restaurant|cafe|bistro"](around:{radius},{lat},{lon});
            );out center {limit};"""
            
        else: 
            query = f"""{timeout_ql}[out:json];(
                nwr["amenity"~"restaurant|bar|cafe"](around:{radius},{lat},{lon});
                nwr["tourism"~"attraction|viewpoint"](around:{radius},{lat},{lon});
            );out center {limit};"""

        return self._exec_overpass(query)

    def _exec_overpass(self, query):
        for i, ep in enumerate(self._overpass_endpoints):
            try:
                r = self._session.post(ep, data=query, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    items = []
                    for el in data.get("elements", []):
                        tags = el.get("tags", {})
                        if "name" in tags:
                            kind = "poi"
                            if "amenity" in tags: kind = tags["amenity"]
                            elif "leisure" in tags: kind = tags["leisure"]
                            elif "tourism" in tags: kind = tags["tourism"]
                            elif "natural" in tags: kind = "nature"
                            
                            clean_name = tags["name"]
                            lat = el.get("lat") or el.get("center", {}).get("lat")
                            lon = el.get("lon") or el.get("center", {}).get("lon")
                            
                            if lat and lon:
                                gmaps_link = f"https://www.google.com/maps/search/?api=1&query={quote(clean_name)}"
                                items.append({"name": clean_name, "kind": kind, "lat": lat, "lon": lon, "maps_url": gmaps_link})
                    
                    return {"status": "ok", "items": items}
            except Exception as e:
                if i == len(self._overpass_endpoints) - 1:
                    return {"status": "timeout", "note": "Mapas indisponíveis (todos servidores ocupados)."}
                continue 
                
        return {"status": "timeout", "note": "Mapas indisponíveis."}

    # --- MÓDULO 3: FERIADOS ---
    def fetch_holidays(self, country_code, start_date, end_date):
        cc = (country_code or "").upper()
        if not cc: return []
        items = []
        try:
            year = start_date.year
            url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{cc}"
            r = self._session.get(url, timeout=5)
            if r.status_code == 200:
                for h in r.json():
                    d_str = h.get("date")
                    d = _dt.date.fromisoformat(d_str)
                    if start_date <= d <= end_date:
                        items.append({"date": d.strftime("%d/%m/%Y"), "name": h.get("localName") or h.get("name")})
        except: pass
        return items