# World Population Analysis

A web application for analyzing and visualizing global population data, including historical data and forecasts up to 2032.

## Features

- Interactive visualizations of population data
- Analysis by World/Continent/Country
- Historical and forecast data visualization
- Year range selection with dual-handle slider
- Responsive design for all devices

## Setup Instructions

### Prerequisites

- Python 3.8+
- Required Python packages (install using `pip install -r requirements.txt`)

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

## Data Sources

- World population data from reliable international sources
- Geographic data from Natural Earth

## Technologies Used

- Flask for backend web framework
- Plotly for interactive visualizations
- Pandas for data manipulation
- GeoPandas for geographic data processing
- noUiSlider for year range selection
- Bootstrap for responsive UI

## Project Structure

- `app.py`: Main application file with Flask routes and data processing
- `templates/`: HTML templates
- `static/css/`: CSS stylesheets
- `data/`: Geographic data for map visualization
- `uploads/`: Directory for user-uploaded files
- `saved_models/`: Directory for saved ARIMA models

## License

MIT License

## Author

Saswata Bhattacharyya 