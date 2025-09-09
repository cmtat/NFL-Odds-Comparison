# NFL-Odds-Comparison

This repository contains a small command line tool for comparing your sportsbook's
odds with the market consensus from sharp bookmakers.

The script uses [The Odds API](https://the-odds-api.com) to retrieve current
lines from sharp books such as Pinnacle, Bookmaker and Circa Sports. It then
removes the vig to estimate the true probabilities and calculates the expected
value (EV) of the odds from your book.

## Installation

```bash
pip install -r requirements.txt
```

## Example

An example JSON file is provided in `examples/book_example.json`.

Run the tool with:

```bash
python odds_ev_tool.py examples/book_example.json --event EVENT_ID --api-key YOUR_KEY
```

`EVENT_ID` should correspond to the event from The Odds API and `YOUR_KEY` is
your API key. The key may also be supplied via the `THE_ODDS_API_KEY`
environment variable.

The output lists the expected value for each line in the file based on the
consensus market probability.
