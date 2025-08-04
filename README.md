# Real-Time Multi-Stock Monitor

A Streamlit-based dashboard for monitoring and forecasting multiple stocks in real time, with configurable technical indicators, breakout logic, Telegram notifications, and AI-powered stock forecasting.

## Project Overview

- **collector.py** collects live stock data from an API and stores it in CSV files.
- **server.py** must be started first; it manages the data collection and breakout logic.
- **Breakout logic** is applied to the CSV data, using thresholds from `config.json`.
- **Telegram notifications** are sent when a breakout is detected.
- **app.py** provides a Streamlit frontend for monitoring stocks, adding new stocks, and updating thresholds.
- **Stock adding:** You can add new stocks directly from the frontend; all stock data is tracked in `data.csv`.
- **Threshold changes** made in the frontend update `config.json`, which is used by `server.py` for real-time logic.
- **Forecasting:** The project integrates with the Groq API for AI-based stock forecasting. Forecast results are saved in the `forecast/` folder.
- **Forecasting scripts:** Use `groq_forecast.py` and related scripts in `LLM_api/` for generating and saving forecasts.

## How to Run

1. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   - Create a `.env` file with your Telegram and API keys (see `.env` example in the repo).

3. **Start the server (data collector and breakout logic):**
   ```
   python server.py
   ```

4. **Start the Streamlit dashboard in a new terminal:**
   ```
   streamlit run app.py
   ```

5. **Add or configure stocks:**
   - Use the Streamlit frontend to add new stocks (saved in `data.csv`) and update thresholds (saved in `config.json`).
   - You can also manually edit `config.json` if needed.

6. **Forecasting:**
   - Run `groq_forecast.py` or scripts in `LLM_api/` to generate AI-powered forecasts. Results are saved in the `forecast/` folder.

## Features

- Live price monitoring for multiple stocks
- Add new stocks from the frontend (saved in `data.csv`)
- Configurable support, resistance, and volume thresholds (via frontend or `config.json`)
- Technical indicators: Bollinger Bands, MACD, ADX, Moving Averages, Inside Bar, Candle patterns
- Real-time breakout and breakdown alerts
- Telegram notifications for breakouts
- AI-powered stock forecasting using Groq API, with results saved in `forecast/`

## File Structure

- `app.py` - Streamlit dashboard (frontend)
- `server.py` - Runs the collector and breakout logic
- `collector.py` - Collects data from the API and writes to CSV
- `indicator.py` - Technical indicator logic
- `telegram_alert.py` - Telegram notification logic
- `groq_forecast.py` and `LLM_api/` - AI forecasting scripts
- `config.json` - Stock configuration and thresholds
- `data.csv` - List of all added stocks
- `latest_data_*.csv` - Latest stock data files
- `forecast/` - Folder containing AI forecast results
