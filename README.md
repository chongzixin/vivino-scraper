# Vivino Bulk Wine Scraper

This project provides a Python 2.7 script to extract and process wine data from the Vivino "Bulk Explore" API via Apify, or from local JSON files that have the same format as the Apify actor's output.

- The script downloads wine images, prepares a mapped CSV file with key wine attributes, and handles Unicode and data cleaning.
- Using local JSON allows you to bypass scraping by letting Apify handle it for you, focusing just on CSV preparation and image downloads.

---

## Features

- Scrape wines using the Vivino-Bulk Apify actor (API mode).
- Or process local JSON files exported from Apify actor runs (same data structure).
- Download wine and bottle images to `/images`.
- Save processed wine data to CSV files under `/csv`.
- Automatically create `/images` and `/csv` folders if they do not exist.
- Supports command-line argument input for specifying local JSON files.
- API token securely managed via `.env` file.

---

## Folder Structure

```
/images # Downloaded wine images (auto-created)
/csv # CSV files are saved here (auto-created)
/json # Place local JSON files here for testing (optional)
vivino_scraper.py # Main Python script
.env # Contains API_TOKEN=your_apify_token (ignored by git)
README.md # This documentation file
```


---

## Setup Instructions

### 1. Python Environment

- Requires **Python 2.7**.
- No external packages needed (uses standard library).

### 2. API Token Setup

1. Create a `.env` file in your project root (same folder as `vivino_scraper.py`):
`API_TOKEN=your_actual_apify_api_token_here`

2. Add `.env` to your `.gitignore` to keep your token private.
3. The script loads this token at runtime from the `.env` file.

---

## Usage

### Running the Full Scrape via Apify API

Simply run:
`python vivino_scraper.py`

- The script starts an Apify actor run, waits for it to complete, fetches the scraped wine data, downloads images, and saves everything into:

  - `csv/wines_data.csv`
  - `images/` folder (all downloaded images)

### Running the Script with a Local JSON file

You can provide a local JSON file (such as one downloaded from a previous Apify actor run) as an argument:

`python vivino_scraper.py json/sample-response.json`

- This reprocesses the JSON file **with the exact same expected data format** as Apify's actor produces.
- Saves the CSV as `csv/sample-response.csv`.
- Downloads images referenced in the JSON to `/images`.
- Perfect for development, testing, or avoiding repeated scraping.

---

## CSV Output Format

The CSV file contains these columns with mapped data:

| Column            | Source Field in JSON                                               | Description                             |
|-------------------|-------------------------------------------------------------------|---------------------------------------|
| `name`            | `summary.name`                                                    | Wine name                             |
| `country`         | `summary.country`                                                 | Country of origin                     |
| `price`           | `summary.price`                                                   | Price reported                       |
| `rating`          | `summary.rating`                                                  | Vivino rating                        |
| `image_url`       | Local path to downloaded summary image                           | Local path (e.g., `images/xxx.jpg`) |
| `bottle_image_url`| Local path to downloaded bottle image                            | Local path (e.g., `images/xxx.jpg`) |
| `region`          | `vintage.wine.region.name`                                       | Wine region                         |
| `winery`          | `vintage.wine.winery.name`                                       | Winery name                        |
| `flavor`          | Comma-separated `vintage.wine.taste.flavor[].group` (symbols removed; underscores replaced with spaces) | Flavor groups                       |
| `food_pairing`    | Comma-separated `vintage.wine.style.food[].name`                 | Food pairing suggestions            |
| `grapes`          | Comma-separated `vintage.wine.style.grapes[].name`               | Grape varietals                     |

---

## Notes on Local JSON File Format

- The local JSON file **must have the same structure and fields as produced by the Apify Vivino-Bulk actor's dataset output**.
- This design allows you to run the heavy scraping only once or on Apify's platform, and subsequently work offline on processing, image downloading, or analytics.
- Simply download or export the JSON dataset from Apify and pass it as an argument to the script.

---

## Additional Details

- The script fixes image URLs missing colons (`https//` → `https://`) before downloading.
- Image filenames are sanitized and saved to `/images`.
- CSV filenames mirror the local JSON filename (with `.csv` extension) and are saved under `/csv`.
- Unicode and special characters are handled properly in CSV output for Python 2.
- The script automatically creates needed folders if missing.
- If no local JSON is specified, a full scrape is triggered via Apify actor, according to filters set inside `start_actor_run()`.

---

## Example Command-Line Workflow

1. Run full scrape (API):
`python vivino_scraper.py`

2. Process a local JSON file:
`python vivino_scraper.py json/my_apify_dataset.json`


3. Check CSV output in `/csv` and images in `/images`.

---

## Troubleshooting & Tips

- **Memory errors on Apify?** Try narrower filters or increase actor memory as per Apify dashboard.
- **Pip command not found?** This script uses only standard Python 2 libs.
- Make sure your Python defaults to Python 2 when running the script (`python --version`).
- The script contains comprehensive error handling and progress logs to track scraping and processing.

---

## License & Usage

- Use this script responsibly, respecting Vivino's and Apify's Terms of Service.
- The data and images are obtained via scraping and should be used for educational/non-commercial purposes unless permissions are obtained.

---

**Happy Wine Data Scraping and Analysis!**

---

If you have questions or want to contribute, feel free to open an issue or pull request.