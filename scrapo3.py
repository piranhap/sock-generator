#!/usr/bin/env python3
"""
scrapo3.py — Synthetic persona generator
Generates fake identities for research/testing. Supports US + South American locales.

Usage:
    python scrapo3.py -n 10 -c us -f excel -o batch1
    python scrapo3.py -n 5 -c br --photos
    python scrapo3.py --help
"""

import argparse
import hashlib
import json
import random
import string
import unicodedata
import uuid
from datetime import date
from pathlib import Path

import requests
from faker import Faker
import pandas as pd

# ── Locale map ────────────────────────────────────────────────────────────────
# es_PE and es_VE don't exist in Faker; use es_ES for name/address generation
# while still producing correct country-specific IDs.

LOCALES = {
    "us": "en_US",
    "ar": "es_AR",
    "br": "pt_BR",
    "co": "es_CO",
    "cl": "es_CL",
    "mx": "es_MX",
    "pe": "es_ES",
    "ve": "es_ES",
}

# ── Static tables ──────────────────────────────────────────────────────────────

HAIR_COLORS   = ["Black", "Brown", "Dark Brown", "Blonde", "Red", "Auburn", "Gray", "White"]
EYE_COLORS    = ["Brown", "Black", "Blue", "Green", "Hazel", "Gray", "Amber"]
BLOOD_TYPES   = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
RELIGIONS     = ["Catholic", "Christian", "Evangelical", "Muslim", "Jewish", "Hindu",
                 "Buddhist", "Atheist", "Agnostic"]
POLITICS      = ["Left", "Center-Left", "Center", "Center-Right", "Right",
                 "Libertarian", "Apolitical"]
ANIMALS       = ["Dog", "Cat", "Rabbit", "Parrot", "Hamster", "Fish", "Horse", "Turtle"]
SEASONS       = ["Spring", "Summer", "Fall", "Winter"]
CEREALS       = ["Corn Flakes", "Frosted Flakes", "Cheerios", "Lucky Charms", "Granola", "Muesli"]
ALIGNMENTS    = [
    "Lawful Good", "Neutral Good", "Chaotic Good",
    "Lawful Neutral", "True Neutral", "Chaotic Neutral",
    "Lawful Evil",  "Neutral Evil",  "Chaotic Evil",
]
COMFORT_FOODS = {
    "us": ["Pizza", "Burger", "Mac & Cheese", "Fried Chicken", "Meatloaf"],
    "ar": ["Asado", "Empanadas", "Milanesa", "Locro", "Dulce de leche"],
    "br": ["Feijoada", "Pão de queijo", "Coxinha", "Brigadeiro", "Churrasco"],
    "co": ["Bandeja Paisa", "Ajiaco", "Empanadas", "Arepa", "Sancocho"],
    "cl": ["Completo", "Empanadas", "Cazuela", "Pastel de choclo", "Curanto"],
    "mx": ["Tacos", "Tamales", "Pozole", "Enchiladas", "Chiles en nogada"],
    "pe": ["Ceviche", "Lomo saltado", "Ají de gallina", "Papa a la huancaína", "Anticuchos"],
    "ve": ["Pabellón criollo", "Arepas", "Hallacas", "Tequeños", "Cachapas"],
}
CAR_MAKES = {
    "us": ["Ford", "Chevrolet", "Dodge", "Tesla", "Jeep", "Ram", "GMC", "Buick"],
    "ar": ["Volkswagen", "Ford", "Chevrolet", "Renault", "Fiat", "Toyota", "Peugeot"],
    "br": ["Volkswagen", "Fiat", "Chevrolet", "Hyundai", "Jeep", "Renault", "Toyota"],
    "cl": ["Hyundai", "Kia", "Mazda", "Toyota", "Volkswagen", "Chevrolet", "Mitsubishi"],
    "co": ["Renault", "Chevrolet", "Mazda", "Kia", "Hyundai", "Toyota", "Nissan"],
    "mx": ["Nissan", "Volkswagen", "Chevrolet", "KIA", "Toyota", "Mazda", "Honda"],
    "pe": ["Toyota", "Hyundai", "Kia", "Volkswagen", "Nissan", "Chevrolet", "Mazda"],
    "ve": ["Toyota", "Ford", "Chevrolet", "Mitsubishi", "Hyundai", "Renault"],
}
CAR_MODELS = {
    "Ford":       ["F-150", "Mustang", "Explorer", "Escape", "Ranger"],
    "Chevrolet":  ["Silverado", "Equinox", "Malibu", "Traverse", "Colorado"],
    "Dodge":      ["Charger", "Challenger", "Durango", "Journey"],
    "Tesla":      ["Model 3", "Model Y", "Model S", "Model X"],
    "Jeep":       ["Wrangler", "Grand Cherokee", "Cherokee", "Compass"],
    "Ram":        ["1500", "2500", "ProMaster"],
    "GMC":        ["Sierra", "Terrain", "Acadia", "Canyon"],
    "Buick":      ["Encore", "Enclave", "Envision"],
    "Volkswagen": ["Golf", "Jetta", "Passat", "Tiguan", "Polo", "Gol"],
    "Renault":    ["Logan", "Sandero", "Duster", "Kwid", "Clio"],
    "Fiat":       ["Uno", "Argo", "Cronos", "Toro", "Mobi"],
    "Toyota":     ["Corolla", "Hilux", "RAV4", "Yaris", "Land Cruiser"],
    "Peugeot":    ["208", "308", "2008", "3008"],
    "Hyundai":    ["Elantra", "Tucson", "Santa Fe", "Creta", "i20"],
    "Kia":        ["Sportage", "Rio", "Seltos", "Carnival", "Sorento"],
    "Mazda":      ["CX-5", "3", "6", "CX-30"],
    "Mitsubishi": ["Outlander", "Eclipse Cross", "L200", "Montero"],
    "Nissan":     ["Sentra", "Versa", "X-Trail", "Frontier", "Kicks"],
    "Honda":      ["Civic", "CR-V", "Fit", "Accord", "HR-V"],
}

# ── Zodiac ─────────────────────────────────────────────────────────────────────

def zodiac_sign(dob: date) -> str:
    m, d = dob.month, dob.day
    if (m == 3 and d >= 21) or (m == 4 and d <= 19):  return "Aries"
    if (m == 4 and d >= 20) or (m == 5 and d <= 20):  return "Taurus"
    if (m == 5 and d >= 21) or (m == 6 and d <= 20):  return "Gemini"
    if (m == 6 and d >= 21) or (m == 7 and d <= 22):  return "Cancer"
    if (m == 7 and d >= 23) or (m == 8 and d <= 22):  return "Leo"
    if (m == 8 and d >= 23) or (m == 9 and d <= 22):  return "Virgo"
    if (m == 9 and d >= 23) or (m == 10 and d <= 22): return "Libra"
    if (m == 10 and d >= 23) or (m == 11 and d <= 21): return "Scorpio"
    if (m == 11 and d >= 22) or (m == 12 and d <= 21): return "Sagittarius"
    if (m == 12 and d >= 22) or (m == 1 and d <= 19):  return "Capricorn"
    if (m == 1 and d >= 20) or (m == 2 and d <= 18):   return "Aquarius"
    return "Pisces"

# ── Helpers ────────────────────────────────────────────────────────────────────

def ascii_name(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()

def random_password(length: int = 12) -> str:
    chars = string.ascii_letters + string.digits + "!@#$%&*"
    return "".join(random.choices(chars, k=length))

def hash_password(pw: str) -> tuple:
    return (
        hashlib.md5(pw.encode()).hexdigest(),
        hashlib.sha1(pw.encode()).hexdigest(),
    )

def rand_email(first: str, last: str) -> str:
    domains = ["gmail.com", "outlook.com", "yahoo.com", "protonmail.com", "hotmail.com"]
    f = ascii_name(first).lower()
    l = ascii_name(last).lower()
    num = random.randint(10, 99)
    sep = random.choice([".", "_", ""])
    patterns = [
        f"{f}{sep}{l}",
        f"{f[0]}{l}",
        f"{f}{num}",
        f"{f}{sep}{l}{num}",
    ]
    return f"{random.choice(patterns)}@{random.choice(domains)}"

def dnd_stat() -> int:
    return sum(sorted([random.randint(1, 6) for _ in range(4)])[1:])

def rand_car(country: str) -> str:
    make  = random.choice(CAR_MAKES.get(country, CAR_MAKES["us"]))
    model = random.choice(CAR_MODELS.get(make, ["Sedan"]))
    year  = random.randint(2010, 2024)
    return f"{year} {make} {model}"

def rand_plate(country: str) -> str:
    up = string.ascii_uppercase
    if country == "br":
        return f"{''.join(random.choices(up,k=3))}-{random.randint(1000,9999)}"
    if country == "ar":
        return f"{''.join(random.choices(up,k=2))} {random.randint(100,999)} {''.join(random.choices(up,k=2))}"
    if country == "cl":
        return f"{''.join(random.choices(up,k=4))}-{random.randint(10,99)}"
    if country == "mx":
        return f"{''.join(random.choices(up,k=3))}-{random.randint(10,99)}-{random.randint(10,99)}"
    return f"{''.join(random.choices(up,k=3))}-{random.randint(1000,9999)}"

def fetch_photo(save_to: Path) -> bool:
    try:
        resp = requests.get("https://thispersondoesnotexist.com/", timeout=15)
        resp.raise_for_status()
        save_to.write_bytes(resp.content)
        return True
    except Exception:
        return False

# ── Government ID generators ───────────────────────────────────────────────────

def _gen_ssn() -> str:
    return f"{random.randint(100,899):03d}-{random.randint(10,99):02d}-{random.randint(1000,9999):04d}"

def _gen_dl_us(fake: Faker) -> dict:
    state  = fake.state_abbr()
    fmts   = [
        lambda: f"{random.choice(string.ascii_uppercase)}{random.randint(1000000,9999999)}",
        lambda: str(random.randint(100000000, 999999999)),
        lambda: f"{''.join(random.choices(string.ascii_uppercase,k=2))}{random.randint(100000,999999)}",
    ]
    issued = fake.date_between(start_date="-10y", end_date="-1y")
    exp    = date(issued.year + random.randint(4, 8), issued.month, issued.day)
    return {
        "drivers_license_number":  random.choice(fmts)(),
        "drivers_license_state":   state,
        "drivers_license_issued":  issued.strftime("%m/%d/%Y"),
        "drivers_license_expires": exp.strftime("%m/%d/%Y"),
    }

def _gen_cpf() -> str:
    n  = [random.randint(0, 9) for _ in range(9)]
    d1 = (sum((10 - i) * n[i] for i in range(9)) * 10) % 11
    n.append(0 if d1 >= 10 else d1)
    d2 = (sum((11 - i) * n[i] for i in range(10)) * 10) % 11
    n.append(0 if d2 >= 10 else d2)
    s  = "".join(map(str, n))
    return f"{s[:3]}.{s[3:6]}.{s[6:9]}-{s[9:]}"

def _gen_rut_cl() -> str:
    n     = random.randint(5_000_000, 25_000_000)
    total = sum(int(d) * [2,3,4,5,6,7][i % 6] for i, d in enumerate(reversed(str(n))))
    r     = 11 - (total % 11)
    check = "0" if r == 11 else "K" if r == 10 else str(r)
    return f"{n:,}".replace(",", ".") + f"-{check}"

def _gen_curp(first: str, last: str, dob: date, gender: str) -> str:
    state_codes = [
        "AG","BC","BS","CM","CS","CH","DF","DG","GT","GR",
        "HG","JC","MC","MN","MS","NT","NL","OC","PL","QT",
        "QR","SP","SL","SR","TC","TS","TL","VZ","YN","ZS",
    ]
    g         = "H" if gender == "male" else "M"
    la        = ascii_name(last).upper()
    fa        = ascii_name(first).upper()
    vowels    = "AEIOU"
    consonants = "BCDFGHJKLMNPQRSTVWXYZ"
    l1 = la[0]
    l2 = next((c for c in la[1:] if c in vowels), "X")
    f1 = fa[0]
    f2 = next((c for c in fa[1:] if c in vowels), "X")
    lc = next((c for c in la[1:] if c in consonants), "X")
    fc = next((c for c in fa[1:] if c in consonants), "X")
    return (
        f"{l1}{l2}{f1}{f2}{dob.strftime('%y%m%d')}"
        f"{g}{random.choice(state_codes)}{lc}{fc}{random.randint(10,99):02d}"
    )

def build_gov_ids(country: str, fake: Faker, first: str, last: str, dob: date, gender: str) -> dict:
    if country == "us":
        return {
            "national_id_label": "SSN",
            "national_id":       _gen_ssn(),
            "tax_id_label":      "EIN",
            "tax_id":            f"{random.randint(10,99)}-{random.randint(1000000,9999999)}",
            **_gen_dl_us(fake),
        }
    if country == "ar":
        dni    = f"{random.randint(10_000_000,99_999_999)}"
        prefix = "20" if gender == "male" else "27"
        return {
            "national_id_label": "DNI",
            "national_id":       dni,
            "tax_id_label":      "CUIT",
            "tax_id":            f"{prefix}-{dni}-{random.randint(0,9)}",
        }
    if country == "br":
        return {
            "national_id_label": "CPF",
            "national_id":       _gen_cpf(),
            "tax_id_label":      "CNPJ",
            "tax_id": (
                f"{random.randint(10,99)}.{random.randint(100,999)}."
                f"{random.randint(100,999)}/{random.randint(1000,9999):04d}-{random.randint(10,99):02d}"
            ),
        }
    if country == "cl":
        rut = _gen_rut_cl()
        return {"national_id_label": "RUT", "national_id": rut, "tax_id_label": "RUT", "tax_id": rut}
    if country == "co":
        return {
            "national_id_label": "Cédula",
            "national_id":       f"{random.randint(1_000_000,1_299_999_999)}",
            "tax_id_label":      "NIT",
            "tax_id":            f"{random.randint(800_000_000,999_999_999)}-{random.randint(0,9)}",
        }
    if country == "mx":
        return {
            "national_id_label": "CURP",
            "national_id":       _gen_curp(first, last, dob, gender),
            "tax_id_label":      "RFC",
            "tax_id": (
                f"{''.join(random.choices(string.ascii_uppercase,k=4))}"
                f"{dob.strftime('%y%m%d')}"
                f"{''.join(random.choices(string.ascii_uppercase+string.digits,k=3))}"
            ),
        }
    if country == "pe":
        dni = f"{random.randint(10_000_000,49_999_999)}"
        return {
            "national_id_label": "DNI",
            "national_id":       dni,
            "tax_id_label":      "RUC",
            "tax_id":            f"10{dni}{random.randint(0,9)}",
        }
    if country == "ve":
        prefix = random.choice(["V", "E"])
        return {
            "national_id_label": "Cédula",
            "national_id":       f"{prefix}-{random.randint(1_000_000,30_000_000)}",
            "tax_id_label":      "RIF",
            "tax_id":            f"J-{random.randint(10_000_000,99_999_999)}-{random.randint(0,9)}",
        }
    return {}

# ── Persona builder ────────────────────────────────────────────────────────────

def generate_persona(country: str, output_dir: Path, download_photo: bool) -> dict:
    fake   = Faker(LOCALES[country])
    gender = random.choice(["male", "female"])

    first  = fake.first_name_male() if gender == "male" else fake.first_name_female()
    last   = fake.last_name()
    middle = fake.first_name_male() if gender == "male" else fake.first_name_female()

    dob       = fake.date_of_birth(minimum_age=18, maximum_age=70)
    pw        = random_password()
    md5, sha1 = hash_password(pw)

    height_cm    = random.randint(155, 195)
    total_inches = height_cm / 2.54
    feet         = int(total_inches // 12)
    inches       = round(total_inches % 12)
    weight_kg    = random.randint(50, 110)

    age     = (date.today() - dob).days // 365
    job     = fake.job()
    company = fake.company()
    pron    = "He" if gender == "male" else "She"

    persona = {
        "country":            country.upper(),
        "gender":             gender,
        "first_name":         first,
        "middle_name":        middle,
        "last_name":          last,
        "initials":           f"{ascii_name(first[0]).upper()}.{ascii_name(middle[0]).upper()}.{ascii_name(last[0]).upper()}.",
        "maiden_name":        fake.last_name() if gender == "female" else "",
        "birthday":           dob.strftime("%B %d, %Y"),
        "birthplace":         fake.city(),
        "zodiac_sign":        zodiac_sign(dob),
        "username":           f"{ascii_name(first).lower()}{ascii_name(last).lower()}{random.randint(10,99)}",
        "password":           pw,
        "password_hash_md5":  md5,
        "password_hash_sha1": sha1,
        "email":              rand_email(first, last),
        "phone":              fake.phone_number(),
        "address":            fake.address().replace("\n", ", "),
        **build_gov_ids(country, fake, first, last, dob, gender),
        "car":                rand_car(country),
        "car_plate":          rand_plate(country),
        "hair_color":         random.choice(HAIR_COLORS),
        "eyes_color":         random.choice(EYE_COLORS),
        "height":             f"{height_cm} cm / {feet}'{inches}\"",
        "weight":             f"{weight_kg} kg / {round(weight_kg * 2.205)} lbs",
        "shoe_size":          str(random.randint(5, 13)),
        "blood_type":         random.choice(BLOOD_TYPES),
        "guid":               str(uuid.uuid4()),
        "uniqid":             uuid.uuid4().hex[:13],
        "wu_mtcn":            f"{random.randint(1_000_000_000,9_999_999_999)}",
        "mg_mtcn":            f"{random.randint(100_000_000,999_999_999)}",
        "religion":           random.choice(RELIGIONS),
        "political_side":     random.choice(POLITICS),
        "favorite_color":     fake.color_name(),
        "favorite_food":      random.choice(COMFORT_FOODS.get(country, COMFORT_FOODS["us"])),
        "favorite_cereal":    random.choice(CEREALS),
        "favorite_season":    random.choice(SEASONS),
        "favorite_animal":    random.choice(ANIMALS),
        "lucky_number":       random.randint(1, 99),
        "alignment":          random.choice(ALIGNMENTS),
        "charisma":           dnd_stat(),
        "constitution":       dnd_stat(),
        "dexterity":          dnd_stat(),
        "intelligence":       dnd_stat(),
        "strength":           dnd_stat(),
        "wisdom":             dnd_stat(),
        "bio":                f"{first} {last} is a {age}-year-old {job} at {company}. {pron} was born in {fake.city()}.",
        "photo":              "",
    }

    if country == "us":
        persona.update({
            "credit_score_fico":     random.randint(300, 850),
            "credit_score_experian": random.randint(300, 850),
            "credit_score_equifax":  random.randint(300, 850),
            "credit_score_vantage":  random.randint(300, 850),
            "credit_score_nextgen":  random.randint(150, 950),
            "credit_score_sbss":     random.randint(0, 300),
            "ptin":                  f"P{random.randint(10_000_000,99_999_999):08d}",
            "itin":                  f"9{random.randint(10,99):02d}-{random.randint(50,65):02d}-{random.randint(1000,9999):04d}",
            "atin":                  f"9{random.randint(10,99):02d}-{random.randint(10,99):02d}-{random.randint(1000,9999):04d}",
        })

    if download_photo:
        slug       = f"{ascii_name(first).lower()}_{ascii_name(last).lower()}_{uuid.uuid4().hex[:6]}"
        photo_path = output_dir / f"{slug}.jpg"
        if fetch_photo(photo_path):
            persona["photo"] = photo_path.name
        else:
            print(f"  Warning: could not download photo for {first} {last}")

    return persona

# ── Export ─────────────────────────────────────────────────────────────────────

def export(personas: list, path: Path, fmt: str):
    df = pd.DataFrame(personas)
    if fmt == "excel":
        out = path.with_suffix(".xlsx")
        df.to_excel(out, index=False)
    elif fmt == "json":
        out = path.with_suffix(".json")
        out.write_text(json.dumps(personas, indent=2, default=str), encoding="utf-8")
    else:
        out = path.with_suffix(".csv")
        df.to_csv(out, index=False, encoding="utf-8")
    print(f"Saved → {out}")

# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    country_help = ", ".join(sorted(LOCALES))
    parser = argparse.ArgumentParser(
        description="Generate synthetic personas for research/testing",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-n", "--count",    type=int, default=1,                       metavar="N", help="Number of personas")
    parser.add_argument("-c", "--country",  choices=sorted(LOCALES), default="us",                  help=f"Country ({country_help})")
    parser.add_argument("-f", "--format",   choices=["csv","excel","json"], default="csv",           help="Output format")
    parser.add_argument("-o", "--output",   default="personas",                                      help="Output filename (no extension)")
    parser.add_argument("--output-dir",     default=".",                                             help="Directory for output files")
    parser.add_argument("--photos",         action="store_true",                                     help="Download AI-generated photos")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    personas = []
    for i in range(args.count):
        print(f"  [{i+1}/{args.count}] Generating...", end="\r", flush=True)
        personas.append(generate_persona(args.country, output_dir, args.photos))

    print(f"  Generated {len(personas)} persona(s).          ")
    export(personas, output_dir / args.output, args.format)


if __name__ == "__main__":
    main()
