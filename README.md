# Bill Summary Generator

A Streamlit web application that generates concise summaries and talking points for legislative bills using Anthropic's Claude API.

## Features

- Multiple input methods:
  - Direct text input
  - PDF upload (single or batch)
  - NCGA bill number lookup
- Comprehensive analysis:
  - Bill summary
  - Key points
  - Platform-specific talking points
  - One-sentence key takeaway
- Security:
  - Password protection
  - Secure API key handling
- Batch processing support
- Clean, responsive interface

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `example.env` to `.env` and configure:
   ```bash
   cp example.env .env
   ```
4. Edit `.env` and add:
   - `ANTHROPIC_API_KEY`: Your Anthropic API key
   - `APP_PASSWORD`: Your desired app password (default: demo123)

## Local Development

Run the Streamlit app locally:
```bash
streamlit run streamlit_app.py
```

## Deployment Options

### 1. Streamlit Cloud (Recommended)
1. Push your code to GitHub
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Add secrets in Streamlit Cloud:
   - `ANTHROPIC_API_KEY`
   - `APP_PASSWORD`
5. Deploy

### 2. Heroku
1. Install Heroku CLI
2. Create a `Procfile`:
   ```
   web: streamlit run streamlit_app.py
   ```
3. Initialize git and push to Heroku:
   ```bash
   git init
   heroku create your-app-name
   heroku config:set ANTHROPIC_API_KEY=your-key
   heroku config:set APP_PASSWORD=your-password
   git push heroku main
   ```

### 3. Digital Ocean App Platform
1. Push code to GitHub
2. Connect Digital Ocean to GitHub
3. Create new App
4. Set environment variables:
   - `ANTHROPIC_API_KEY`
   - `APP_PASSWORD`
5. Deploy

## Security Notes

- Never commit `.env` file
- Use environment variables for secrets
- Change default password
- Keep API key secure
- Consider IP whitelisting if needed
