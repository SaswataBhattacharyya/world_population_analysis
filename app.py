from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
import os
import traceback
import geopandas as gpd
import warnings
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.colors import ListedColormap
from sklearn.preprocessing import MinMaxScaler
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

warnings.filterwarnings("ignore")

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['world_population']
plots_collection = db['plots']

def save_plot_to_mongodb(plot_data, plot_type, metadata):
    """Save plot to MongoDB and return its ID"""
    try:
        # Convert base64 to binary
        image_data = base64.b64decode(plot_data)
        
        # Create document
        plot_doc = {
            'plot_type': plot_type,
            'metadata': metadata,
            'image_data': image_data,
            'created_at': datetime.utcnow()
        }
        
        # Insert and return ID
        result = plots_collection.insert_one(plot_doc)
        return str(result.inserted_id)
    except Exception as e:
        print(f"Error saving plot to MongoDB: {str(e)}")
        return None

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
    """Route to get data based on user selections and generate plots"""
    try:
        debug_print("app.py: Received POST to /get_data")
        data = request.get_json()
        debug_print(f"app.py: Data received: {data}")
        
        # Get selection type (World/Continent/Country)
        selection_types = data.get('selection_types', [])
        debug_print(f"Selection types: {selection_types}")
        
        # Get selected values
        continent = data.get('continent')
        country = data.get('country')
        start_year = int(data.get('start_year', 1970))
        end_year = int(data.get('end_year', 2032))
        
        debug_print(f"Selected values - Continent: {continent}, Country: {country}")
        debug_print(f"Years - Start: {start_year}, End: {end_year}")
        
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
        
        # Generate plots and store in MongoDB
        plot_ids = {}
        
        # For world level
        if 'world' in selection_types:
            plot_ids['world'] = {}
            world_plots = {
                'population_graph': fig_to_base64(create_population_graph(filtered_data['world'], 'World Population', 'world')),
                'population_maps': fig_to_base64(create_population_maps(filtered_data['world'], start_year, end_year, 'world')),
                'density_graph': fig_to_base64(create_density_graph(filtered_data['world'], 'World Population Density', 'world')),
                'density_maps': fig_to_base64(create_density_maps(filtered_data['world'], start_year, end_year, 'world')),
                'growth_graph': fig_to_base64(create_growth_graph(filtered_data['world'], 'World Population Growth', 'world')),
                'growth_maps': fig_to_base64(create_growth_maps(filtered_data['world'], start_year, end_year, 'world')),
                'population_maps_continent_wise': fig_to_base64(create_population_maps(filtered_data['world'], start_year, end_year, 'world-continent-wise')),
                'population_maps_country_wise': fig_to_base64(create_population_maps(filtered_data['world'], start_year, end_year, 'world-country-wise')),
                'density_maps_continent_wise': fig_to_base64(create_density_maps(filtered_data['world'], start_year, end_year, 'world-continent-wise')),
                'density_maps_country_wise': fig_to_base64(create_density_maps(filtered_data['world'], start_year, end_year, 'world-country-wise')),
                'growth_maps_continent_wise': fig_to_base64(create_growth_maps(filtered_data['world'], start_year, end_year, 'world-continent-wise')),
                'growth_maps_country_wise': fig_to_base64(create_growth_maps(filtered_data['world'], start_year, end_year, 'world-country-wise'))
            }
            
            for plot_type, plot_data in world_plots.items():
                if plot_data:
                    metadata = {
                        'section': 'world',
                        'plot_type': plot_type,
                        'selection': data
                    }
                    plot_id = save_plot_to_mongodb(plot_data, plot_type, metadata)
                    if plot_id:
                        plot_ids['world'][plot_type] = plot_id
        
        # For continent level
        if 'continent' in selection_types and continent:
            plot_ids['continent'] = {}
            continent_plots = {
                'location_map': fig_to_base64(create_continent_location_map(continent)),
                'population_graph': fig_to_base64(create_population_graph(filtered_data['continent'], f'{continent} Population', 'continent')),
                'population_maps': fig_to_base64(create_population_maps(filtered_data['continent'], start_year, end_year, 'continent')),
                'density_graph': fig_to_base64(create_density_graph(filtered_data['continent'], f'{continent} Population Density', 'continent')),
                'density_maps': fig_to_base64(create_density_maps(filtered_data['continent'], start_year, end_year, 'continent')),
                'growth_graph': fig_to_base64(create_growth_graph(filtered_data['continent'], f'{continent} Population Growth', 'continent')),
                'growth_maps': fig_to_base64(create_growth_maps(filtered_data['continent'], start_year, end_year, 'continent')),
                'population_pie_charts': fig_to_base64(create_population_pie_charts(filtered_data['continent'], start_year, end_year, 'continent', continent)),
                'population_maps_country_wise': fig_to_base64(create_population_maps(filtered_data['continent'], start_year, end_year, 'continent-country-wise')),
                'density_maps_country_wise': fig_to_base64(create_density_maps(filtered_data['continent'], start_year, end_year, 'continent-country-wise')),
                'growth_maps_country_wise': fig_to_base64(create_growth_maps(filtered_data['continent'], start_year, end_year, 'continent-country-wise'))
            }
            
            for plot_type, plot_data in continent_plots.items():
                if plot_data:
                    metadata = {
                        'section': 'continent',
                        'plot_type': plot_type,
                        'selection': data
                    }
                    plot_id = save_plot_to_mongodb(plot_data, plot_type, metadata)
                    if plot_id:
                        plot_ids['continent'][plot_type] = plot_id
        
        # For country level
        if 'country' in selection_types and country:
            plot_ids['country'] = {}
            country_plots = {
                'location_map': fig_to_base64(create_country_location_map(country)),
                'population_graph': fig_to_base64(create_population_graph(filtered_data['country'], f'{country} Population', 'country')),
                'population_maps': fig_to_base64(create_population_maps(filtered_data['country'], start_year, end_year, 'country')),
                'density_graph': fig_to_base64(create_density_graph(filtered_data['country'], f'{country} Population Density', 'country')),
                'density_maps': fig_to_base64(create_density_maps(filtered_data['country'], start_year, end_year, 'country')),
                'growth_graph': fig_to_base64(create_growth_graph(filtered_data['country'], f'{country} Population Growth', 'country')),
                'growth_maps': fig_to_base64(create_growth_maps(filtered_data['country'], start_year, end_year, 'country')),
                'population_pie_charts': fig_to_base64(create_population_pie_charts(filtered_data['country'], start_year, end_year, 'country', country))
            }
            
            for plot_type, plot_data in country_plots.items():
                if plot_data:
                    metadata = {
                        'section': 'country',
                        'plot_type': plot_type,
                        'selection': data
                    }
                    plot_id = save_plot_to_mongodb(plot_data, plot_type, metadata)
                    if plot_id:
                        plot_ids['country'][plot_type] = plot_id
        
        debug_print("app.py: Finished generating plots, returning to visualization.js")
        return jsonify({
            'status': 'success',
            'data': data,
            'plot_ids': plot_ids
        })
        
    except Exception as e:
        debug_print(f"Error in get_data: {str(e)}")
        debug_print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Visualization Functions
def create_country_location_map(country_name):
    """Create a map showing the selected country's location"""
    country_shape = world[world['NAME'] == country_name]
    other_countries = world[world['NAME'] != country_name]
    
    fig, ax = plt.subplots(figsize=(15, 10))
    
    # Plot other countries in blue
    other_countries.plot(
        ax=ax,
        color='blue',
        alpha=0.5,
        edgecolor='black',
        linewidth=0.5
    )
    
    # Plot selected country in green
    country_shape.plot(
        ax=ax,
        color='green',
        alpha=0.8,
        edgecolor='black',
        linewidth=0.5
    )
    
    ax.set_title(f"Location of {country_name}")
    ax.axis('off')
    
    return fig

def create_continent_location_map(continent_name):
    """Create a map showing the selected continent's location"""
    continent_shape = world[world['CONTINENT'] == continent_name]
    other_continents = world[world['CONTINENT'] != continent_name]

    fig, ax = plt.subplots(figsize=(15, 10))
    other_continents.plot(ax=ax, color='lightgrey', edgecolor='black', linewidth=0.5)
    continent_shape.plot(ax=ax, color='orange', edgecolor='black', linewidth=0.5)
    ax.set_title(f"Location of {continent_name}")
    ax.axis('off')
    return fig

def create_population_graph(data, title, level='country'):
    """Create population line graph for country, continent, or world"""
    fig, ax = plt.subplots(figsize=(12, 6))
    if level == 'country':
        # Country: plot directly
        hist_data = data[data['Year'] <= PIVOT_YEAR]
        ax.plot(hist_data['Year'], hist_data['Population'], label='Historical')
        forecast_data = data[data['Year'] > PIVOT_YEAR]
        ax.plot(forecast_data['Year'], forecast_data['Population'], '--', label='Forecast')
    elif level == 'continent':
        # Continent: sum population for all countries in the continent
        grouped = data.groupby('Year', as_index=False)['Population'].sum().sort_values('Year')
        hist_data = grouped[grouped['Year'] <= PIVOT_YEAR]
        ax.plot(hist_data['Year'], hist_data['Population'], label='Historical')
        forecast_data = grouped[grouped['Year'] > PIVOT_YEAR]
        ax.plot(forecast_data['Year'], forecast_data['Population'], '--', label='Forecast')
    elif level == 'world':
        # World: sum population for all countries
        grouped = data.groupby('Year', as_index=False)['Population'].sum().sort_values('Year')
        hist_data = grouped[grouped['Year'] <= PIVOT_YEAR]
        ax.plot(hist_data['Year'], hist_data['Population'], label='Historical')
        forecast_data = grouped[grouped['Year'] > PIVOT_YEAR]
        ax.plot(forecast_data['Year'], forecast_data['Population'], '--', label='Forecast')
    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel("Population")
    ax.legend()
    ax.grid(True)
    return fig

def create_population_maps(data, start_year, end_year, level='country'):
    start_data = data[data['Year'] == start_year]
    end_data = data[data['Year'] == end_year]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    pop_bins = [450, 1_000, 10_000, 100_000, 1_000_000, 10_000_000, 50_000_000,
                100_000_000, 500_000_000, 1_000_000_000, 2_000_000_000,
                4_000_000_000, 8_000_000_000]
    pop_labels = [
        '<1K', '1K–10K', '10K–100K', '100K–1M', '1M–10M', '10M–50M',
        '50M–100M', '100M–500M', '500M–1B', '1B–2B', '2B–4B', '4B–8B'
    ]
    if level == 'continent-country-wise':
        continent_name = start_data['Continent'].iloc[0]
        for ax, year_data, year in zip([ax1, ax2], [start_data, end_data], [start_year, end_year]):
            countries = world[world['CONTINENT'] == continent_name]
            merged = countries.merge(year_data[['Country/Territory', 'Population']],
                                    left_on='NAME', right_on='Country/Territory', how='left')
            merged['PopBin'] = pd.cut(merged['Population'], bins=pop_bins, labels=pop_labels, include_lowest=True)
            merged.plot(column='PopBin', ax=ax, cmap='YlOrRd', legend=True)
            ax.set_title(f"{continent_name} Country-wise Population in {year}")
            ax.axis('off')
    elif level == 'world-continent-wise':
        for ax, year_data, year in zip([ax1, ax2], [start_data, end_data], [start_year, end_year]):
            cont_pop = year_data.groupby('Continent')['Population'].sum().reset_index()
            continents = world.dissolve(by='CONTINENT', as_index=False)
            merged = continents.merge(cont_pop, left_on='CONTINENT', right_on='Continent', how='left')
            merged['PopBin'] = pd.cut(merged['Population'], bins=pop_bins, labels=pop_labels, include_lowest=True)
            merged.plot(column='PopBin', ax=ax, cmap='YlOrRd', legend=True)
            ax.set_title(f"World Continent-wise Population in {year}")
            ax.axis('off')
    elif level == 'world-country-wise':
        for ax, year_data, year in zip([ax1, ax2], [start_data, end_data], [start_year, end_year]):
            merged = world.merge(year_data[['Country/Territory', 'Population']],
                                left_on='NAME', right_on='Country/Territory', how='left')
            merged['PopBin'] = pd.cut(merged['Population'], bins=pop_bins, labels=pop_labels, include_lowest=True)
            merged.plot(column='PopBin', ax=ax, cmap='YlOrRd', legend=True)
            ax.set_title(f"World Country-wise Population in {year}")
            ax.axis('off')
    elif level == 'country':
        # Country: plot directly
        country_name = start_data['Country/Territory'].iloc[0]
        country_shape = world[world['NAME'] == country_name]
        
        # Calculate shared color scale
        vmin = min(start_data['Population'].iloc[0], end_data['Population'].iloc[0])
        vmax = max(start_data['Population'].iloc[0], end_data['Population'].iloc[0])
        
        # Plot start year
        pop = start_data['Population'].iloc[0]
        country_shape['Population'] = pop
        country_shape.plot(column='Population', ax=ax1, cmap='YlOrRd', 
                          legend=True, vmin=vmin, vmax=vmax)
        ax1.set_title(f"{country_name} Population in {start_year}")
        ax1.axis('off')
        
        # Plot end year
        pop = end_data['Population'].iloc[0]
        country_shape['Population'] = pop
        country_shape.plot(column='Population', ax=ax2, cmap='YlOrRd', 
                          legend=True, vmin=vmin, vmax=vmax)
        ax2.set_title(f"{country_name} Population in {end_year}")
        ax2.axis('off')
    elif level == 'continent':
        # Population maps
        continent_name = start_data['Continent'].iloc[0]
        continent_shape = world[world['CONTINENT'] == continent_name].dissolve(by='CONTINENT', as_index=False)
        # Calculate total population for start and end years
        pop_start = start_data['Population'].sum()
        pop_end = end_data['Population'].sum()
        vmin = min(pop_start, pop_end)
        vmax = max(pop_start, pop_end)
        # Plot start year
        continent_shape['Population'] = pop_start
        continent_shape.plot(column='Population', ax=ax1, cmap='YlOrRd', legend=True, vmin=vmin, vmax=vmax)
        ax1.set_title(f"{continent_name} Population in {start_year}")
        ax1.axis('off')
        # Plot end year
        continent_shape['Population'] = pop_end
        continent_shape.plot(column='Population', ax=ax2, cmap='YlOrRd', legend=True, vmin=vmin, vmax=vmax)
        ax2.set_title(f"{continent_name} Population in {end_year}")
        ax2.axis('off')
    elif level == 'world':
        # Population maps
        world_shape = world.dissolve().reset_index(drop=True)
        pop_start = start_data['Population'].sum()
        pop_end = end_data['Population'].sum()
        vmin = min(pop_start, pop_end)
        vmax = max(pop_start, pop_end)
        # Plot start year
        world_shape['Population'] = pop_start
        world_shape.plot(column='Population', ax=ax1, cmap='YlOrRd', legend=True, vmin=vmin, vmax=vmax)
        ax1.set_title(f"World Population in {start_year}")
        ax1.axis('off')
        # Plot end year
        world_shape['Population'] = pop_end
        world_shape.plot(column='Population', ax=ax2, cmap='YlOrRd', legend=True, vmin=vmin, vmax=vmax)
        ax2.set_title(f"World Population in {end_year}")
        ax2.axis('off')
    
    plt.tight_layout()
    return fig

def create_density_graph(data, title, level='country'):
    """Create density line graph for country, continent, or world"""
    fig, ax = plt.subplots(figsize=(12, 6))
    if level == 'country':
        hist_data = data[data['Year'] <= PIVOT_YEAR]
        ax.plot(hist_data['Year'], hist_data['Density'], label='Historical')
        forecast_data = data[data['Year'] > PIVOT_YEAR]
        ax.plot(forecast_data['Year'], forecast_data['Density'], '--', label='Forecast')
    elif level == 'continent':
        # For each year, sum population and area, then compute density
        grouped = data.groupby('Year').agg({'Population': 'sum', 'Area (km²)': 'sum'}).reset_index()
        grouped['Density'] = grouped['Population'] / grouped['Area (km²)']
        hist_data = grouped[grouped['Year'] <= PIVOT_YEAR]
        ax.plot(hist_data['Year'], hist_data['Density'], label='Historical')
        forecast_data = grouped[grouped['Year'] > PIVOT_YEAR]
        ax.plot(forecast_data['Year'], forecast_data['Density'], '--', label='Forecast')
    elif level == 'world':
        grouped = data.groupby('Year').agg({'Population': 'sum', 'Area (km²)': 'sum'}).reset_index()
        grouped['Density'] = grouped['Population'] / grouped['Area (km²)']
        hist_data = grouped[grouped['Year'] <= PIVOT_YEAR]
        ax.plot(hist_data['Year'], hist_data['Density'], label='Historical')
        forecast_data = grouped[grouped['Year'] > PIVOT_YEAR]
        ax.plot(forecast_data['Year'], forecast_data['Density'], '--', label='Forecast')
    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel("Density")
    ax.legend()
    ax.grid(True)
    return fig

def create_density_maps(data, start_year, end_year, level='country'):
    # Recalculate density to ensure consistency
    data['Density'] = data['Population'] / data['Area (km²)']  
    # Global MinMax scaling for all years combined
    global_scaler = MinMaxScaler()
    data['Density_scaled'] = global_scaler.fit_transform(data[['Density']].fillna(0))    
    start_data = data[data['Year'] == start_year]
    end_data = data[data['Year'] == end_year]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    density_bins = [0, 0.000025, 0.00005, 0.000075, 0.0001, 0.0005, 0.001, 0.005,
                    0.01, 0.05, 0.1, 0.2, 0.5, 0.75, 1]
    density_labels = [
        '<2.5e-5', '2.5e-5–5e-5', '5e-5–7.5e-5', '7.5e-5–1e-4', '1e-4–5e-4', '5e-4–1e-3',
        '1e-3–5e-3', '5e-3–1e-2', '1e-2–0.05', '0.05–0.1', '0.1–0.2', '0.2–0.5', '0.5–0.75', '0.75–1'
    ]

    if level == 'continent-country-wise':
        continent_name = start_data['Continent'].iloc[0]
        for ax, year_data, year in zip([ax1, ax2], [start_data, end_data], [start_year, end_year]):
            countries = world[world['CONTINENT'] == continent_name]
            merged = countries.merge(
                year_data[['Country/Territory', 'Density_scaled']],
                left_on='NAME', right_on='Country/Territory', how='left'
            )
            merged['DensityBin'] = pd.cut(
                merged['Density_scaled'].fillna(0),
                bins=density_bins, labels=density_labels, include_lowest=True
            )
            merged.plot(column='DensityBin', ax=ax, cmap='viridis', legend=True)
            ax.set_title(f"{continent_name} Country-wise Density in {year}")
            ax.axis('off')

    elif level == 'world-continent-wise':
        for ax, year_data, year in zip([ax1, ax2], [start_data, end_data], [start_year, end_year]):
            cont_density = year_data.groupby('Continent').agg({'Population': 'sum', 'Area (km²)': 'sum'}).reset_index()
            cont_density['Density'] = cont_density['Population'] / cont_density['Area (km²)']
            cont_density['Density_scaled'] = global_scaler.transform(cont_density[['Density']].fillna(0))
            continents = world.dissolve(by='CONTINENT', as_index=False)
            merged = continents.merge(
                cont_density[['Continent', 'Density_scaled']],
                left_on='CONTINENT', right_on='Continent', how='left'
            )
            merged['DensityBin'] = pd.cut(
                merged['Density_scaled'].fillna(0),
                bins=density_bins, labels=density_labels, include_lowest=True
            )
            merged.plot(column='DensityBin', ax=ax, cmap='viridis', legend=True)
            ax.set_title(f"World Continent-wise Density in {year}")
            ax.axis('off')

    elif level == 'world-country-wise':
        for ax, year_data, year in zip([ax1, ax2], [start_data, end_data], [start_year, end_year]):
            merged = world.merge(
                year_data[['Country/Territory', 'Density_scaled']],
                left_on='NAME', right_on='Country/Territory', how='left'
            )
            merged['DensityBin'] = pd.cut(
                merged['Density_scaled'].fillna(0),
                bins=density_bins, labels=density_labels, include_lowest=True
            )
            merged.plot(column='DensityBin', ax=ax, cmap='viridis', legend=True)
            ax.set_title(f"World Country-wise Density in {year}")
            ax.axis('off')
    elif level == 'country':
        country_name = start_data['Country/Territory'].iloc[0]
        country_shape = world[world['NAME'] == country_name]
        
        # Calculate shared color scale
        vmin = min(start_data['Density'].iloc[0], end_data['Density'].iloc[0])
        vmax = max(start_data['Density'].iloc[0], end_data['Density'].iloc[0])
        
        # Plot start year
        dens = start_data['Density'].iloc[0]
        country_shape['Density'] = dens
        country_shape.plot(column='Density', ax=ax1, cmap='viridis', 
                          legend=True, vmin=vmin, vmax=vmax)
        ax1.set_title(f"{country_name} Density in {start_year}")
        ax1.axis('off')
        
        # Plot end year
        dens = end_data['Density'].iloc[0]
        country_shape['Density'] = dens
        country_shape.plot(column='Density', ax=ax2, cmap='viridis', 
                          legend=True, vmin=vmin, vmax=vmax)
        ax2.set_title(f"{country_name} Density in {end_year}")
        ax2.axis('off')
    elif level == 'continent':
        # Density maps
        continent_name = start_data['Continent'].iloc[0]
        continent_shape = world[world['CONTINENT'] == continent_name].dissolve(by='CONTINENT', as_index=False)
        # Calculate total population and area for start and end years
        pop_start = start_data['Population'].sum()
        area_start = start_data['Area (km²)'].sum()
        dens_start = pop_start / area_start if area_start > 0 else 0
        pop_end = end_data['Population'].sum()
        area_end = end_data['Area (km²)'].sum()
        dens_end = pop_end / area_end if area_end > 0 else 0
        vmin = min(dens_start, dens_end)
        vmax = max(dens_start, dens_end)
        # Plot start year
        continent_shape['Density'] = dens_start
        continent_shape.plot(column='Density', ax=ax1, cmap='viridis', legend=True, vmin=vmin, vmax=vmax)
        ax1.set_title(f"{continent_name} Density in {start_year}")
        ax1.axis('off')
        # Plot end year
        continent_shape['Density'] = dens_end
        continent_shape.plot(column='Density', ax=ax2, cmap='viridis', legend=True, vmin=vmin, vmax=vmax)
        ax2.set_title(f"{continent_name} Density in {end_year}")
        ax2.axis('off')
    elif level == 'world':
        # Density maps
        world_shape = world.dissolve().reset_index(drop=True)
        pop_start = start_data['Population'].sum()
        area_start = start_data['Area (km²)'].sum()
        dens_start = pop_start / area_start if area_start > 0 else 0
        pop_end = end_data['Population'].sum()
        area_end = end_data['Area (km²)'].sum()
        dens_end = pop_end / area_end if area_end > 0 else 0
        vmin = min(dens_start, dens_end)
        vmax = max(dens_start, dens_end)
        # Plot start year
        world_shape['Density'] = dens_start
        world_shape.plot(column='Density', ax=ax1, cmap='viridis', legend=True, vmin=vmin, vmax=vmax)
        ax1.set_title(f"World Density in {start_year}")
        ax1.axis('off')
        # Plot end year
        world_shape['Density'] = dens_end
        world_shape.plot(column='Density', ax=ax2, cmap='viridis', legend=True, vmin=vmin, vmax=vmax)
        ax2.set_title(f"World Density in {end_year}")
        ax2.axis('off')
    
    plt.tight_layout()
    return fig

def create_growth_graph(data, title, level='country'):
    """Create growth line graph for country, continent, or world"""
    fig, ax = plt.subplots(figsize=(12, 6))
    if level == 'country':
        hist_data = data[data['Year'] <= PIVOT_YEAR]
        ax.plot(hist_data['Year'], hist_data['Growth'], label='Historical')
        forecast_data = data[data['Year'] > PIVOT_YEAR]
        ax.plot(forecast_data['Year'], forecast_data['Growth'], '--', label='Forecast')
    elif level == 'continent':
        grouped = data.groupby('Year', as_index=False)['Population'].sum().sort_values('Year')
        grouped['Growth'] = grouped['Population'].pct_change().bfill()
        hist_data = grouped[grouped['Year'] <= PIVOT_YEAR]
        ax.plot(hist_data['Year'], hist_data['Growth'], label='Historical')
        forecast_data = grouped[grouped['Year'] > PIVOT_YEAR]
        ax.plot(forecast_data['Year'], forecast_data['Growth'], '--', label='Forecast')
    elif level == 'world':
        grouped = data.groupby('Year', as_index=False)['Population'].sum().sort_values('Year')
        grouped['Growth'] = grouped['Population'].pct_change().bfill()
        hist_data = grouped[grouped['Year'] <= PIVOT_YEAR]
        ax.plot(hist_data['Year'], hist_data['Growth'], label='Historical')
        forecast_data = grouped[grouped['Year'] > PIVOT_YEAR]
        ax.plot(forecast_data['Year'], forecast_data['Growth'], '--', label='Forecast')
    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel("Growth Rate")
    ax.legend()
    ax.grid(True)
    return fig


def create_growth_maps(data, start_year, end_year, level='country'):
    start_data = data[data['Year'] == start_year]
    end_data = data[data['Year'] == end_year]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    
    growth_bins = [-0.1, -0.05, -0.01, 0, 0.01, 0.02, 0.05, 0.1, 0.2, 1]
    growth_labels = [
        '<-5%', '-5% to -1%', '-1% to 0%', '0% to 1%', '1% to 2%',
        '2% to 5%', '5% to 10%', '10% to 20%', '>20%'
    ]
    
    if level == 'continent-country-wise':
        continent_name = start_data['Continent'].iloc[0]
        for ax, year_data, year in zip([ax1, ax2], [start_data, end_data], [start_year, end_year]):
            countries = world[world['CONTINENT'] == continent_name]
            merged = countries.merge(
                year_data[['Country/Territory', 'Growth']],
                left_on='NAME', right_on='Country/Territory', how='left'
            )
            merged['GrowthBin'] = pd.cut(
                merged['Growth'].fillna(0),
                bins=growth_bins, labels=growth_labels, include_lowest=True
            )
            merged.plot(column='GrowthBin', ax=ax, cmap='RdYlGn', legend=True)
            ax.set_title(f"{continent_name} Country-wise Growth in {year}")
            ax.axis('off')

    elif level == 'world-continent-wise':
        growths = []
        for continent in data['Continent'].unique():
            cont_data = data[data['Continent'] == continent].groupby('Year', as_index=False)['Population'].sum().sort_values('Year')
            cont_data['Growth'] = cont_data['Population'].pct_change().bfill()
            for year in [start_year, end_year]:
                row = cont_data[cont_data['Year'] == year]
                if not row.empty:
                    growths.append({'Continent': continent, 'Year': year, 'Growth': row['Growth'].values[0]})
        growths_df = pd.DataFrame(growths)
        continents = world.dissolve(by='CONTINENT', as_index=False)
        for ax, year, label in zip([ax1, ax2], [start_year, end_year], [f"World Continent-wise Growth in {start_year}", f"World Continent-wise Growth in {end_year}"]):
            year_growth = growths_df[growths_df['Year'] == year][['Continent', 'Growth']]
            merged = continents.merge(
                year_growth, left_on='CONTINENT', right_on='Continent', how='left'
            )
            merged['GrowthBin'] = pd.cut(
                merged['Growth'].fillna(0),
                bins=growth_bins, labels=growth_labels, include_lowest=True
            )
            merged.plot(column='GrowthBin', ax=ax, cmap='RdYlGn', legend=True)
            ax.set_title(label)
            ax.axis('off')

    elif level == 'world-country-wise':
        for ax, year_data, year in zip([ax1, ax2], [start_data, end_data], [start_year, end_year]):
            merged = world.merge(
                year_data[['Country/Territory', 'Growth']],
                left_on='NAME', right_on='Country/Territory', how='left'
            )
            merged['GrowthBin'] = pd.cut(
                merged['Growth'].fillna(0),
                bins=growth_bins, labels=growth_labels, include_lowest=True
            )
            merged.plot(column='GrowthBin', ax=ax, cmap='RdYlGn', legend=True)
            ax.set_title(f"World Country-wise Growth in {year}")
            ax.axis('off')

    elif level == 'country':
        country_name = start_data['Country/Territory'].iloc[0]
        country_shape = world[world['NAME'] == country_name]
        
        # Calculate shared color scale
        vmin = min(start_data['Growth'].iloc[0], end_data['Growth'].iloc[0])
        vmax = max(start_data['Growth'].iloc[0], end_data['Growth'].iloc[0])
        
        # Plot start year
        growth = start_data['Growth'].iloc[0]
        country_shape['Growth'] = growth
        country_shape.plot(column='Growth', ax=ax1, cmap='RdYlGn', 
                          legend=True, vmin=vmin, vmax=vmax)
        ax1.set_title(f"{country_name} Growth in {start_year}")
        ax1.axis('off')
        
        # Plot end year
        growth = end_data['Growth'].iloc[0]
        country_shape['Growth'] = growth
        country_shape.plot(column='Growth', ax=ax2, cmap='RdYlGn', 
                          legend=True, vmin=vmin, vmax=vmax)
        ax2.set_title(f"{country_name} Growth in {end_year}")
        ax2.axis('off')
    elif level == 'continent':
        continent_name = start_data['Continent'].iloc[0]
        # Calculate growth as in the graph: sum population by year, then pct_change().bfill()
        grouped = data.groupby('Year', as_index=False)['Population'].sum().sort_values('Year')
        grouped['Growth'] = grouped['Population'].pct_change().bfill()
        growth_start = grouped[grouped['Year'] == start_year]['Growth'].values[0]
        growth_end = grouped[grouped['Year'] == end_year]['Growth'].values[0]
        vmin = min(growth_start, growth_end)
        vmax = max(growth_start, growth_end)
        continent_shape = world[world['CONTINENT'] == continent_name].dissolve(by='CONTINENT', as_index=False)
        # Plot start year
        continent_shape['Growth'] = growth_start
        continent_shape.plot(column='Growth', ax=ax1, cmap='RdYlGn', legend=True, vmin=vmin, vmax=vmax)
        ax1.set_title(f"{continent_name} Growth in {start_year}")
        ax1.axis('off')
        # Plot end year
        continent_shape['Growth'] = growth_end
        continent_shape.plot(column='Growth', ax=ax2, cmap='RdYlGn', legend=True, vmin=vmin, vmax=vmax)
        ax2.set_title(f"{continent_name} Growth in {end_year}")
        ax2.axis('off')
    elif level == 'world':
        # Calculate growth as in the graph: sum population by year, then pct_change().bfill()
        grouped = data.groupby('Year', as_index=False)['Population'].sum().sort_values('Year')
        grouped['Growth'] = grouped['Population'].pct_change().bfill()
        growth_start = grouped[grouped['Year'] == start_year]['Growth'].values[0]
        growth_end = grouped[grouped['Year'] == end_year]['Growth'].values[0]
        vmin = min(growth_start, growth_end)
        vmax = max(growth_start, growth_end)
        world_shape = world.dissolve().reset_index(drop=True)
        # Plot start year
        world_shape['Growth'] = growth_start
        world_shape.plot(column='Growth', ax=ax1, cmap='RdYlGn', legend=True, vmin=vmin, vmax=vmax)
        ax1.set_title(f"World Growth in {start_year}")
        ax1.axis('off')
        # Plot end year
        world_shape['Growth'] = growth_end
        world_shape.plot(column='Growth', ax=ax2, cmap='RdYlGn', legend=True, vmin=vmin, vmax=vmax)
        ax2.set_title(f"World Growth in {end_year}")
        ax2.axis('off')
    
    plt.tight_layout()
    return fig

def create_population_pie_charts(data, start_year, end_year, level='country', name=None):
    """Create population pie charts for start and end years"""
    # Get data for both years
    start_data = data[data['Year'] == start_year]
    end_data = data[data['Year'] == end_year]
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
    
    if level == 'country':
        # Calculate total world population
        world_pop_start = df[df['Year'] == start_year]['Population'].sum()
        world_pop_end = df[df['Year'] == end_year]['Population'].sum()
        
        # Get country population
        country_pop_start = start_data['Population'].sum()
        country_pop_end = end_data['Population'].sum()
        
        # Create pie charts
        ax1.pie([country_pop_start, world_pop_start - country_pop_start],
                labels=[name, 'Rest of World'],
                autopct='%1.1f%%',
                startangle=90)
        ax1.set_title(f"Population Share in {start_year}")
        
        ax2.pie([country_pop_end, world_pop_end - country_pop_end],
                labels=[name, 'Rest of World'],
                autopct='%1.1f%%',
                startangle=90)
        ax2.set_title(f"Population Share in {end_year}")
    
    elif level == 'continent':
        # Calculate total world population
        world_pop_start = df[df['Year'] == start_year]['Population'].sum()
        world_pop_end = df[df['Year'] == end_year]['Population'].sum()
        
        # Get continent population
        continent_pop_start = start_data['Population'].sum()
        continent_pop_end = end_data['Population'].sum()
        
        # Create pie charts
        ax1.pie([continent_pop_start, world_pop_start - continent_pop_start],
                labels=[name, 'Rest of World'],
                autopct='%1.1f%%',
                startangle=90)
        ax1.set_title(f"Population Share in {start_year}")
        
        ax2.pie([continent_pop_end, world_pop_end - continent_pop_end],
                labels=[name, 'Rest of World'],
                autopct='%1.1f%%',
                startangle=90)
        ax2.set_title(f"Population Share in {end_year}")
    
    return fig

@app.route('/get_visualizations', methods=['POST'])
def get_visualizations():
    """Route to get visualizations based on user selections"""
    try:
        debug_print("Processing visualization request...")
        data = request.get_json()
        
        # Get selection type and values
        selection_types = data.get('selection_types', [])
        continent = data.get('continent')
        country = data.get('country')
        start_year = int(data.get('start_year', 1970))
        end_year = int(data.get('end_year', 2032))
        
        visualizations = {}
        
        for selection_type in selection_types:
            if selection_type == 'country' and country:
                # Country level visualizations
                country_data = df[df['Country/Territory'] == country]
                
                # Create figures
                location_map = create_country_location_map(country)
                population_graph = create_population_graph(country_data, f"Population Forecast for {country}", 'country')
                population_maps = create_population_maps(country_data, start_year, end_year, 'country')
                density_graph = create_density_graph(country_data, f"Density Forecast for {country}", 'country')
                density_maps = create_density_maps(country_data, start_year, end_year, 'country')
                growth_graph = create_growth_graph(country_data, f"Growth Rate Forecast for {country}", 'country')
                growth_maps = create_growth_maps(country_data, start_year, end_year, 'country')
                population_pie_charts = create_population_pie_charts(country_data, start_year, end_year, 'country', country)
                
                # Convert figures to base64 strings
                visualizations['country'] = {
                    'location_map': fig_to_base64(location_map),
                    'population_graph': fig_to_base64(population_graph),
                    'population_maps': fig_to_base64(population_maps),
                    'density_graph': fig_to_base64(density_graph),
                    'density_maps': fig_to_base64(density_maps),
                    'growth_graph': fig_to_base64(growth_graph),
                    'growth_maps': fig_to_base64(growth_maps),
                    'population_pie_charts': fig_to_base64(population_pie_charts)
                }
                
                # Close figures to free memory
                plt.close('all')
            
            elif selection_type == 'continent' and continent:
                # Continent level visualizations
                continent_data = df[df['Continent'] == continent]
                
                # Create figures
                location_map = create_continent_location_map(continent)
                population_graph = create_population_graph(continent_data, f"Population Forecast for {continent}", 'continent')
                population_maps = create_population_maps(continent_data, start_year, end_year, 'continent')
                density_graph = create_density_graph(continent_data, f"Density Forecast for {continent}", 'continent')
                density_maps = create_density_maps(continent_data, start_year, end_year, 'continent')
                growth_graph = create_growth_graph(continent_data, f"Growth Rate Forecast for {continent}", 'continent')
                growth_maps = create_growth_maps(continent_data, start_year, end_year, 'continent')
                population_pie_charts = create_population_pie_charts(continent_data, start_year, end_year, 'continent', continent)
                # New: Country-wise maps for continent
                population_maps_country_wise = create_population_maps(continent_data, start_year, end_year, 'continent-country-wise')
                density_maps_country_wise = create_density_maps(continent_data, start_year, end_year, 'continent-country-wise')
                growth_maps_country_wise = create_growth_maps(continent_data, start_year, end_year, 'continent-country-wise')
                
                # Convert figures to base64 strings
                visualizations['continent'] = {
                    'location_map': fig_to_base64(location_map),
                    'population_graph': fig_to_base64(population_graph),
                    'population_maps': fig_to_base64(population_maps),
                    'density_graph': fig_to_base64(density_graph),
                    'density_maps': fig_to_base64(density_maps),
                    'growth_graph': fig_to_base64(growth_graph),
                    'growth_maps': fig_to_base64(growth_maps),
                    'population_pie_charts': fig_to_base64(population_pie_charts),
                    'population_maps_country_wise': fig_to_base64(population_maps_country_wise),
                    'density_maps_country_wise': fig_to_base64(density_maps_country_wise),
                    'growth_maps_country_wise': fig_to_base64(growth_maps_country_wise)
                }
                
                # Close figures to free memory
                plt.close('all')
            
            elif selection_type == 'world':
                # World level visualizations
                world_data = df.copy()
                
                # Create figures
                population_graph = create_population_graph(world_data, "World Population Forecast", 'world')
                population_maps = create_population_maps(world_data, start_year, end_year, 'world')
                density_graph = create_density_graph(world_data, "World Density Forecast", 'world')
                density_maps = create_density_maps(world_data, start_year, end_year, 'world')
                growth_graph = create_growth_graph(world_data, "World Growth Rate Forecast", 'world')
                growth_maps = create_growth_maps(world_data, start_year, end_year, 'world')
                # New: Continent-wise and country-wise maps for world
                population_maps_continent_wise = create_population_maps(world_data, start_year, end_year, 'world-continent-wise')
                population_maps_country_wise = create_population_maps(world_data, start_year, end_year, 'world-country-wise')
                density_maps_continent_wise = create_density_maps(world_data, start_year, end_year, 'world-continent-wise')
                density_maps_country_wise = create_density_maps(world_data, start_year, end_year, 'world-country-wise')
                growth_maps_continent_wise = create_growth_maps(world_data, start_year, end_year, 'world-continent-wise')
                growth_maps_country_wise = create_growth_maps(world_data, start_year, end_year, 'world-country-wise')
                
                # Convert figures to base64 strings
                visualizations['world'] = {
                    'population_graph': fig_to_base64(population_graph),
                    'population_maps': fig_to_base64(population_maps),
                    'density_graph': fig_to_base64(density_graph),
                    'density_maps': fig_to_base64(density_maps),
                    'growth_graph': fig_to_base64(growth_graph),
                    'growth_maps': fig_to_base64(growth_maps),
                    'population_maps_continent_wise': fig_to_base64(population_maps_continent_wise),
                    'population_maps_country_wise': fig_to_base64(population_maps_country_wise),
                    'density_maps_continent_wise': fig_to_base64(density_maps_continent_wise),
                    'density_maps_country_wise': fig_to_base64(density_maps_country_wise),
                    'growth_maps_continent_wise': fig_to_base64(growth_maps_continent_wise),
                    'growth_maps_country_wise': fig_to_base64(growth_maps_country_wise)
                }
                
                # Close figures to free memory
                plt.close('all')
        
        return jsonify({
            'status': 'success',
            'visualizations': visualizations
        })
        
    except Exception as e:
        debug_print(f"Error in get_visualizations: {str(e)}")
        debug_print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def fig_to_base64(fig):
    """Convert matplotlib figure to base64 string"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    return img_str

@app.route('/visualization')
def visualization():
    """Route to render the visualization page"""
    return render_template('visualization.html')

@app.route('/get_plot/<plot_id>')
def get_plot(plot_id):
    """Fetch a specific plot from MongoDB"""
    try:
        plot = plots_collection.find_one({'_id': ObjectId(plot_id)})
        if plot:
            return send_file(
                io.BytesIO(plot['image_data']),
                mimetype='image/png'
            )
        return jsonify({'status': 'error', 'message': 'Plot not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False) 