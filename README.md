# NFL Odds Comparison

This project helps you compare odds from your sportsbook with sharp-bookmaker consensus lines pulled from [The Odds API](https://the-odds-api.com). It now includes both an interactive web application and an updated command line interface.

## Features

- ✅ Pulls real-time odds for a selected event and market from multiple sportsbooks via The Odds API.
- ✅ Computes vig-free probabilities from sharp books (Pinnacle, Bookmaker, Circa) and estimates expected value (EV) for your lines.
- ✅ Calculates Kelly staking recommendations based on your bankroll and fractional Kelly preference.
- ✅ Accepts sportsbook data as JSON, HTML exports, or screenshots (OCR powered by Tesseract, optional).
- ✅ Presents a responsive web UI to upload/adjust your lines, review EV results, and compare against every available sportsbook.

## Installation

```bash
pip install -r requirements.txt
```

> **Note:** Screenshot parsing requires the [Tesseract OCR](https://tesseract-ocr.github.io/) binary in addition to the Python packages listed above. Install it via your system package manager (e.g. `apt-get install tesseract-ocr` on Debian/Ubuntu or `brew install tesseract` on macOS).

## Running the web app

1. Export your The Odds API key (or provide it in the UI each session):

   ```bash
   export THE_ODDS_API_KEY=your_api_key_here
   ```

2. Launch the Flask development server:

   ```bash
   flask --app app run
   # or
   python app.py
   ```

3. Open <http://127.0.0.1:5000/> and follow the prompts:
   - Enter/confirm your API key.
   - Select a sport, then load the desired event.
   - Upload odds from your sportsbook (HTML/JSON or screenshot) or enter them manually.
   - Review EV results, recommended stakes, and all bookmaker lines.

The interface lets you tweak parsed lines and rerun analysis without re-uploading the file. Positive EV rows are highlighted in green.

## Command line usage

Example input files live in `examples/`. The HTML sample demonstrates the `data-team` + `data-odds` attributes that make parsing straightforward.

```bash
python odds_ev_tool.py examples/book_example.json --event EVENT_ID --api-key YOUR_KEY
# or
python odds_ev_tool.py examples/book_example.html --event EVENT_ID --api-key YOUR_KEY
```

Arguments:

- `--sport` (default `americanfootball_nfl`): sport key from The Odds API.
- `--market` (`h2h`, `spreads`, `totals`): betting market to evaluate.
- `--stake`: stake amount used when reporting EV.
- `--event`: required The Odds API event identifier.
- `--api-key`: your API key (falls back to `THE_ODDS_API_KEY`).

The CLI prints the EV, vig-free probability, and fair odds for each uploaded line based on sharp-bookmaker consensus.

## Tips for preparing uploads

- **HTML/JSON:** Save the bet slip or odds page as “Webpage, HTML Only” or export as JSON with `team`/`label`, `odds`, and optional `point` values.
- **Screenshots:** Crop to the relevant market, keep odds text sharp, and ensure Tesseract OCR is available on the host running the app.
- **Manual entry:** Use the editable rows beneath the upload field to adjust or enter lines from scratch.

Enjoy finding positive EV opportunities responsibly!
