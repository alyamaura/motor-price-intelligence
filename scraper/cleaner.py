import re

BRAND_MAP = {
    'honda': 'honda', 'yamaha': 'yamaha',
    'suzuki': 'suzuki', 'kawasaki': 'kawasaki',
}

MODEL_MAP = {
    'beat': 'beat',
    'vario 110': 'vario_110', 'vario110': 'vario_110',
    'vario 125': 'vario_125', 'vario125': 'vario_125',
    'vario 160': 'vario_160', 'vario160': 'vario_160',
    'scoopy': 'scoopy',
    'pcx 150': 'pcx_150', 'pcx150': 'pcx_150',
    'pcx 160': 'pcx_160', 'pcx160': 'pcx_160',
    'adv 150': 'adv_150', 'adv 160': 'adv_160', 'adv160': 'adv_160',
    'genio': 'genio',
    'cbr 150': 'cbr_150r', 'cbr150': 'cbr_150r',
    'cbr 250': 'cbr_250rr', 'cbr250': 'cbr_250rr',
    'cb150r': 'cb150r', 'sonic': 'sonic_150r',
    'revo': 'revo', 'supra x': 'supra_x_125',
    'mio m3': 'mio_m3', 'mio s': 'mio_s', 'mio z': 'mio_z',
    'freego': 'freego', 'aerox': 'aerox_155',
    'nmax': 'nmax_155', 'xmax': 'xmax_250', 'lexi': 'lexi',
    'r15': 'r15', 'r25': 'r25',
    'mt15': 'mt15', 'mt-15': 'mt15', 'mt25': 'mt25',
    'address': 'address', 'nex': 'nex_ii',
    'burgman': 'burgman_street',
    'gsx-r': 'gsx_r150', 'gsx-s': 'gsx_s150',
    'ninja 250': 'ninja_250', 'ninja250': 'ninja_250',
    'zx25r': 'ninja_zx25r', 'z250': 'z250',
    'klx': 'klx_150', 'w175': 'w175',
}


def normalize_brand(text):
    if not text:
        return None
    t = text.lower().strip()
    for k, v in BRAND_MAP.items():
        if k in t:
            return v
    return None


def normalize_model(text):
    if not text:
        return None
    t = text.lower().strip()
    for k, v in MODEL_MAP.items():
        if k in t:
            return v
    return None


def parse_price(text):
    if not text:
        return None
    digits = re.sub(r'[^\d]', '', text)
    if not digits:
        return None
    price = int(digits)
    if price < 1_000_000 or price > 500_000_000:
        return None
    return price


def parse_year(text):
    if not text:
        return None
    years = re.findall(r'\b(19[89]\d|20[012]\d)\b', text)
    return int(years[0]) if years else None


def parse_mileage(text):
    if not text:
        return None
    t = text.lower()
    for pattern in [r'(\d+[\.,]?\d*)\s*(?:ribu\s*)?km',
                    r'(\d+[\.,]?\d*)\s*kilometer']:
        m = re.search(pattern, t)
        if m:
            raw = m.group(1).replace(',', '').replace('.', '')
            km = int(raw)
            if 'ribu' in t[max(0, m.start()-5):m.end()+5]:
                km *= 1000
            if km < 500:
                km *= 1000
            if 0 <= km <= 500_000:
                return km
    return None


def is_valid_listing(brand, model, year, price):
    if not brand or not model:
        return False
    if not year or year < 1990 or year > 2026:
        return False
    if not price or price < 1_000_000:
        return False
    return True