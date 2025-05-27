# DSI321-Big-Data-Infrastructure

## Overview
This project is a comprehensive Big Data Infrastructure system developed for the DSI321 course. It enables the collection, processing, and analysis of Twitter/X data based on specified hashtags. The system leverages modern data engineering tools and technologies to create an end-to-end data pipeline that includes data extraction, transformation, loading, and visualization components.

## Features
- **Twitter/X Data Scraping**: Automated collection of tweets based on hashtags using Playwright
- **Data Processing**: Extract insights and FAQs from collected tweets using Google Gemini AI
- **Data Storage**: Organized storage structure for tweets and processed data
- **Data Lake Integration**: LakeFS for version-controlled data management
- **Workflow Orchestration**: Prefect for scheduling and monitoring data pipelines
- **Data Visualization**: Interactive Streamlit dashboard for exploring and visualizing insights

## System Architecture

The project follows a modern data stack architecture:
1. **Data Collection Layer**: Scripts for scraping Twitter/X data
2. **Processing Layer**: Python scripts for data transformation and AI-based analysis
3. **Orchestration Layer**: Prefect workflows for managing the data pipeline
4. **Storage Layer**: File-based storage with LakeFS integration
5. **Visualization Layer**: Streamlit frontend for data exploration

## Requirements
- Python 3.12+
- Docker and Docker Compose
- Playwright for web scraping
- Google Gemini API key for AI processing

## Project Structure
```
├── build/                 # Build artifacts
├── config/                # Configuration files
│   └── twitter_auth.json  # Twitter authentication configuration
├── data/                  # Data storage
│   ├── faq/               # Extracted FAQs
│   ├── hash/              # Hashtag information
│   └── tweets/            # Scraped tweets
├── frontend/              # Streamlit dashboard
│   └── streamlit.py       # Main dashboard file
├── lakefs/                # LakeFS data
├── make/                  # Docker configurations
├── pipeline/              # Data processing scripts
│   ├── deploy.py          # Prefect flow deployment
│   ├── extraction.py      # FAQ extraction from tweets
│   ├── x_login.py         # Twitter login functionality
│   └── x_scrap.py         # Tweet scraping functionality
├── src/                   # Source code
├── docker-compose.yml     # Docker services configuration
└── pyproject.toml         # Python project dependencies
```

## Setup and Installation

### Prerequisites
1. Docker and Docker Compose installed on your system
2. Google Gemini API key for AI processing

### Installation Steps
1. Clone the repository:
   ```
   git clone https://github.com/your-username/DSI321-big-data-infrastructure.git
   cd DSI321-big-data-infrastructure
   ```

2. Create configuration files:
   - Create `config/twitter_auth.json` with your Twitter credentials
   - Set up environment variables (create a `.env` file with your `GEMINI_API_KEY`)

3. Start the infrastructure:
   ```
   docker-compose up -d
   ```

4. Access the services:
   - Prefect Dashboard: http://localhost:4200
   - LakeFS Dashboard: http://localhost:8001 (default credentials: admin/access_key/secret_key)
   - Streamlit Dashboard: http://localhost:8501 (when started)

## Usage

### Running the Data Pipeline
1. Deploy the Prefect flows:
   ```
   python pipeline/deploy.py
   ```

2. Monitor the execution in the Prefect dashboard

### Accessing the Dashboard
1. Start the Streamlit application:
   ```
   cd frontend
   streamlit run streamlit.py
   ```

2. Open your browser and navigate to http://localhost:8501

### Customizing the Data Collection
Edit the `tags` list in `pipeline/deploy.py` to collect tweets from different hashtags:
```python
tags = [
    '#ธรรมศาสตร์ช้างเผือก',
    '#DSI321'
    # Add more hashtags here
]
```

## Contributing
Contributions to this project are welcome. Please ensure your code follows the existing structure and passes all tests before submitting a pull request.

## License
This project is licensed under the terms of the LICENSE file included in the repository.

## Acknowledgements
- This project was developed as part of the DSI321 Big Data Infrastructure course
- Thanks to all contributors and instructors for their guidance and support