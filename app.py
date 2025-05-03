from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
import os
import traceback
import geopandas as gpd
import warnings

warnings.filterwarnings("ignore")

app = Flask(__name__)

# Debug flag
DEBUG = True

def debug_print(message):
    """Helper function for debug messages"""
    if DEBUG:
        print(f"[DEBUG] {message}")

# Define pivot year constant
PIVOT_YEAR = 2022

# Load data
try:
    debug_print("Loading arima_combined_df.csv...")
    df = pd.read_csv('arima_combined_df.csv')
    debug_print(f"Data loaded successfully. Shape: {df.shape}")
except Exception as e:
    debug_print(f"Error loading data: {str(e)}")
    raise

# Load shapefile
try:
    debug_print("Loading shapefile...")
    shapefile_path = 'data/10m_cultural/10m_cultural/ne_10m_admin_0_countries.shp'
    world = gpd.read_file(shapefile_path)
    debug_print(f"Shapefile loaded successfully. Shape: {world.shape}")
except Exception as e:
    debug_print(f"Error loading shapefile: {str(e)}")
    raise

# Get unique values for dropdowns
try:
    debug_print("Getting unique values for dropdowns...")
    continents = sorted(df['Continent'].unique().tolist())
    countries = sorted(df['Country/Territory'].unique().tolist())
    debug_print(f"Found {len(continents)} continents and {len(countries)} countries")
except Exception as e:
    debug_print(f"Error getting unique values: {str(e)}")
    raise

@app.route('/')
def index():
    """Main route for the application"""
    debug_print("Rendering index page...")
    
    # Pass pivot year to template
    continents = df['Continent'].unique()
    countries = df['Country/Territory'].unique()
    return render_template("index.html", 
                          continents=continents, 
                          countries=countries,
                          pivot_year=PIVOT_YEAR)

@app.route('/get_data', methods=['POST'])
def get_data():
    """Route to get data based on user selections"""
    try:
        debug_print("Processing data request...")
        data = request.get_json()
        
        # Get selection type (World/Continent/Country)
        selection_types = data.get('selection_types', [])
        debug_print(f"Selection types: {selection_types}")
        
        # Get selected values
        continent = data.get('continent')
        country = data.get('country')
        start_year = int(data.get('start_year', 1970))
        end_year = int(data.get('end_year', 2032))
        
        debug_print(f"Selected values - Continent: {continent}, Country: {country}")
        debug_print(f"Years - Start: {start_year}, End: {end_year}, Pivot: {PIVOT_YEAR}")
        
        # Filter data based on selections
        filtered_data = {}
        
        for selection_type in selection_types:
            if selection_type == 'world':
                filtered_data['world'] = df.copy()
            elif selection_type == 'continent' and continent:
                filtered_data['continent'] = df[df['Continent'] == continent]
            elif selection_type == 'country' and country:
                filtered_data['country'] = df[df['Country/Territory'] == country]
        
        # Filter by years for each selection
        for key in filtered_data:
            filtered_data[key] = filtered_data[key][
                (filtered_data[key]['Year'] >= start_year) & 
                (filtered_data[key]['Year'] <= end_year)
            ]
            debug_print(f"Filtered {key} data shape: {filtered_data[key].shape}")
        
        # Return the filtered data
        return jsonify({
            'status': 'success',
            'data': {k: v.to_dict(orient='records') for k, v in filtered_data.items()}
        })
        
    except Exception as e:
        debug_print(f"Error in get_data: {str(e)}")
        debug_print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True) 