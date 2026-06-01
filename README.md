# persona-gen

A command-line tool that generates realistic synthetic identities for research, testing, and data population. Supports the United States and seven South American countries, producing locale-accurate names, government IDs, contact details, vehicles, and more — exported to CSV, Excel, or JSON.

---

## Features

- **8 country locales** — US, Argentina, Brazil, Chile, Colombia, Mexico, Peru, Venezuela
- **Country-specific government IDs** — SSN, DNI, CPF, RUT, Cédula, CURP, RUC, RIF, and matching tax IDs
- **Locale-accurate names, addresses, and phone numbers** via the Faker library
- **50+ fields per persona** — identity, credentials, physical traits, financials, preferences, D&D stats
- **AI-generated photos** (optional) — downloads from [thispersondoesnotexist.com](https://thispersondoesnotexist.com)
- **Flexible output** — CSV, Excel (`.xlsx`), or JSON

---

## Requirements

- Python 3.10+
- See `requirements.txt`

```bash
pip install -r requirements.txt
```

---

## Usage

```bash
# 1 US persona → personas.csv
python scrapo3.py

# 50 Brazilian personas → output.xlsx
python scrapo3.py -n 50 -c br -f excel -o output

# 10 Mexican personas with AI photos → saved to ./out/
python scrapo3.py -n 10 -c mx --photos --output-dir out

# Full help
python scrapo3.py --help
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `-n`, `--count` | `1` | Number of personas to generate |
| `-c`, `--country` | `us` | Country code (see table below) |
| `-f`, `--format` | `csv` | Output format: `csv`, `excel`, `json` |
| `-o`, `--output` | `personas` | Output filename without extension |
| `--output-dir` | `.` | Directory for output files |
| `--photos` | off | Download an AI-generated face per persona |

### Country codes

| Code | Country | National ID | Tax ID |
|------|---------|-------------|--------|
| `us` | United States | SSN | EIN |
| `ar` | Argentina | DNI | CUIT |
| `br` | Brazil | CPF | CNPJ |
| `cl` | Chile | RUT | RUT |
| `co` | Colombia | Cédula | NIT |
| `mx` | Mexico | CURP | RFC |
| `pe` | Peru | DNI | RUC |
| `ve` | Venezuela | Cédula | RIF |

---

## Output fields

| Field | Description |
|-------|-------------|
| `country`, `gender` | Country code and gender |
| `first_name`, `middle_name`, `last_name`, `initials`, `maiden_name` | Full name details |
| `birthday`, `birthplace`, `zodiac_sign` | Birth information |
| `username`, `password`, `password_hash_md5`, `password_hash_sha1` | Login credentials |
| `email`, `phone`, `address` | Contact information |
| `national_id_label`, `national_id` | Primary government ID |
| `tax_id_label`, `tax_id` | Tax identification number |
| `drivers_license_*` | License number, state, issued/expiry dates *(US only)* |
| `car`, `car_plate` | Vehicle and license plate |
| `hair_color`, `eyes_color`, `height`, `weight`, `shoe_size`, `blood_type` | Physical traits |
| `guid`, `uniqid` | Unique identifiers |
| `wu_mtcn`, `mg_mtcn` | Western Union / MoneyGram transfer numbers |
| `credit_score_*` | FICO, Experian, Equifax, Vantage, NextGen, SBSS *(US only)* |
| `ptin`, `itin`, `atin` | Preparer/Individual/Adoption tax IDs *(US only)* |
| `religion`, `political_side` | Beliefs and affiliations |
| `favorite_color`, `favorite_food`, `favorite_cereal`, `favorite_season`, `favorite_animal` | Personal preferences |
| `lucky_number` | Lucky number |
| `alignment`, `charisma`, `constitution`, `dexterity`, `intelligence`, `strength`, `wisdom` | D&D character stats |
| `bio` | Auto-generated one-line biography |
| `photo` | Filename of downloaded AI photo (if `--photos` used) |

---

## License

MIT — see [LICENSE](LICENSE).
