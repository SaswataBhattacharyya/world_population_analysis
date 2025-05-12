# World Population Analysis

A web application for analyzing and visualizing global population data, including historical data and forecasts up to 2032.

## Features

- Interactive visualizations of population data
- Analysis by World/Continent/Country
- Historical and forecast data visualization
- Year range selection with dual-handle slider
- Responsive design for all devices
- MongoDB integration for data storage and retrieval

## Setup Instructions

### Prerequisites

- Python 3.8+
- MongoDB Community Server
- MongoDB Shell
- MongoDB Compass
- Required Python packages (install using `pip install -r requirements.txt`)

### MongoDB Setup

1. Download MongoDB Community Server:
   - Visit [MongoDB Download Center](https://www.mongodb.com/try/download/community)
   - Download the .deb package for Ubuntu
   - Install using: `sudo dpkg -i mongodb-org-server_*.deb`

2. Download MongoDB Shell:
   - Visit [MongoDB Shell Download](https://www.mongodb.com/try/download/shell)
   - Download the .deb package
   - Install using: `sudo dpkg -i mongodb-mongosh_*.deb`

3. Download MongoDB Compass:
   - Visit [MongoDB Compass Download](https://www.mongodb.com/try/download/compass)
   - Download the .deb package
   - Install using: `sudo dpkg -i mongodb-compass_*.deb`

4. Start MongoDB Service:
   ```bash
   sudo systemctl start mongod
   sudo systemctl enable mongod
   sudo systemctl status mongod
   ```

### Installation

1. Clone the repository:
```bash
git clone https://github.com/SaswataBhattacharyya/world_population_analysis.git
cd world_population_analysis
   ```

2. Install dependencies:
```bash
   pip install -r requirements.txt
   ```

3. Generate the ARIMA combined dataset:
```bash
python feature_model_final.ipynb
```
This will create the `arima_combined_df.csv` file in your working directory.

4. Verify that the shapefile path in `app.py` is correct. It should point to:
```
data/10m_cultural/10m_cultural/ne_10m_admin_0_countries.shp
```

5. Run the application:
```bash
   python app.py
   ```

6. Open your browser and navigate to:
   ```
http://127.0.0.1:5000/
   ```

## Project Structure

```
world_population_analysis/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── static/               # Static files
│   ├── css/             # CSS stylesheets
│   │   └── visualization.css
│   └── js/              # JavaScript files
│       └── visualization.js
├── templates/            # HTML templates
│   └── visualization.html
├── data/                 # Data files
│   └── 10m_cultural/    # Geographic data
├── uploads/             # User uploaded files
├── saved_models/        # Saved ML models
└── notebooks/           # Jupyter notebooks
    ├── EDA_1.ipynb
    ├── feature_model_final.ipynb
    ├── model_analysis.ipynb
    └── model_analysis_lstm.ipynb
```

## Data Sources

- World population data from reliable international sources
- Geographic data from Natural Earth

## Technologies Used

- Flask for backend web framework
- MongoDB for database
- Plotly for interactive visualizations
- Pandas for data manipulation
- GeoPandas for geographic data processing
- noUiSlider for year range selection
- Bootstrap for responsive UI

## License

MIT License

## Author

Saswata Bhattacharyya 