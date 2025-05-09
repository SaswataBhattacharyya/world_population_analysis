// Function to show/hide sections based on selection
function updateVisibleSections(selections) {
    const sections = {
        'world': document.getElementById('world-section'),
        'continent': document.getElementById('continent-section'),
        'country': document.getElementById('country-section')
    };

    // Hide all sections first
    Object.values(sections).forEach(section => {
        if (section) section.style.display = 'none';
    });

    // Show selected sections
    selections.forEach(selection => {
        if (sections[selection]) {
            sections[selection].style.display = 'block';
        }
    });
}

// Function to update section titles
function updateSectionTitles(data) {
    if (data.country) {
        const countryTitle = document.getElementById('country-title');
        if (countryTitle) {
            countryTitle.textContent = `${data.country} - Prediction`;
        }
    }

    if (data.continent) {
        const continentTitle = document.getElementById('continent-title');
        if (continentTitle) {
            continentTitle.textContent = `${data.continent} - Prediction`;
        }
    }
}

// Function to update map view based on radio selection
function updateMapView(type, view) {
    // Simply call the appropriate show/hide function based on type
    if (type === 'continent') {
        showContinentMapView(view);
    } else if (type === 'world') {
        showWorldMapView(view);
    }
}

// Add request tracking
let currentRequest = null;

// Function to fetch and display visualizations
function fetchVisualizations(data) {
    // Cancel any ongoing request
    if (currentRequest) {
        currentRequest.abort();
    }

    // Create new AbortController for this request
    const controller = new AbortController();
    currentRequest = controller;

    fetch('/get_visualizations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
        signal: controller.signal
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            displayVisualizations(result.visualizations);
        } else {
            console.error('Error:', result.message);
            alert('Error loading visualizations: ' + result.message);
        }
    })
    .catch(error => {
        // Don't show error if request was aborted
        if (error.name === 'AbortError') {
            console.log('Request was cancelled');
            return;
        }
        console.error('Error:', error);
        alert('Error loading visualizations');
    })
    .finally(() => {
        // Clear current request if this was the last one
        if (currentRequest === controller) {
            currentRequest = null;
        }
    });
}

// Function to display visualizations
function displayVisualizations(visualizations) {
    console.log("DEBUG: Full visualizations object:", visualizations);
    console.log("DEBUG: World visualizations:", visualizations.world);
    console.log("DEBUG: World country-wise maps:", {
        population: visualizations.world?.population_maps_country_wise,
        density: visualizations.world?.density_maps_country_wise,
        growth: visualizations.world?.growth_maps_country_wise
    });

    // Helper function to set image source
    const setImage = (id, base64Data) => {
        const element = document.getElementById(id);
        if (element && base64Data) {
            element.src = `data:image/png;base64,${base64Data}`;
        } else {
            console.log(`DEBUG: Missing data for ${id}:`, base64Data);
        }
    };

    // Display country visualizations
    if (visualizations.country) {
        setImage('country-location-map', visualizations.country.location_map);
        setImage('country-population-graph', visualizations.country.population_graph);
        setImage('country-population-maps', visualizations.country.population_maps);
        setImage('country-density-graph', visualizations.country.density_graph);
        setImage('country-density-maps', visualizations.country.density_maps);
        setImage('country-growth-graph', visualizations.country.growth_graph);
        setImage('country-growth-maps', visualizations.country.growth_maps);
        setImage('country-population-pie-charts', visualizations.country.population_pie_charts);
    }

    // Display continent visualizations
    if (visualizations.continent) {
        setImage('continent-location-map', visualizations.continent.location_map);
        setImage('continent-population-graph', visualizations.continent.population_graph);
        setImage('continent-population-maps', visualizations.continent.population_maps);
        setImage('continent-density-graph', visualizations.continent.density_graph);
        setImage('continent-density-maps', visualizations.continent.density_maps);
        setImage('continent-growth-graph', visualizations.continent.growth_graph);
        setImage('continent-growth-maps', visualizations.continent.growth_maps);
        setImage('continent-population-pie-charts', visualizations.continent.population_pie_charts);
        // New country-wise maps for continent
        setImage('continent-population-maps-country-wise', visualizations.continent.population_maps_country_wise);
        setImage('continent-density-maps-country-wise', visualizations.continent.density_maps_country_wise);
        setImage('continent-growth-maps-country-wise', visualizations.continent.growth_maps_country_wise);
    }

    // Display world visualizations
    if (visualizations.world) {
        setImage('world-population-graph', visualizations.world.population_graph);
        setImage('world-population-maps', visualizations.world.population_maps);
        setImage('world-density-graph', visualizations.world.density_graph);
        setImage('world-density-maps', visualizations.world.density_maps);
        setImage('world-growth-graph', visualizations.world.growth_graph);
        setImage('world-growth-maps', visualizations.world.growth_maps);
        // New continent-wise and country-wise maps for world
        setImage('world-population-maps-continent-wise', visualizations.world.population_maps_continent_wise);
        setImage('world-population-maps-country-wise', visualizations.world.population_maps_country_wise);
        setImage('world-density-maps-continent-wise', visualizations.world.density_maps_continent_wise);
        setImage('world-density-maps-country-wise', visualizations.world.density_maps_country_wise);
        setImage('world-growth-maps-continent-wise', visualizations.world.growth_maps_continent_wise);
        setImage('world-growth-maps-country-wise', visualizations.world.growth_maps_country_wise);
    }
}

// Helper to show only the selected map type for continent
function showContinentMapView(view) {
    // Hide all
    document.getElementById('continent-population-maps').style.display = 'none';
    document.getElementById('continent-density-maps').style.display = 'none';
    document.getElementById('continent-growth-maps').style.display = 'none';
    document.getElementById('continent-population-maps-country-wise').style.display = 'none';
    document.getElementById('continent-density-maps-country-wise').style.display = 'none';
    document.getElementById('continent-growth-maps-country-wise').style.display = 'none';
    if (view === 'whole') {
        document.getElementById('continent-population-maps').style.display = '';
        document.getElementById('continent-density-maps').style.display = '';
        document.getElementById('continent-growth-maps').style.display = '';
    } else if (view === 'country-wise') {
        document.getElementById('continent-population-maps-country-wise').style.display = '';
        document.getElementById('continent-density-maps-country-wise').style.display = '';
        document.getElementById('continent-growth-maps-country-wise').style.display = '';
    }
}

// Helper to show only the selected map type for world
function showWorldMapView(view) {
    // Hide all
    document.getElementById('world-population-maps').style.display = 'none';
    document.getElementById('world-density-maps').style.display = 'none';
    document.getElementById('world-growth-maps').style.display = 'none';
    document.getElementById('world-population-maps-continent-wise').style.display = 'none';
    document.getElementById('world-population-maps-country-wise').style.display = 'none';
    document.getElementById('world-density-maps-continent-wise').style.display = 'none';
    document.getElementById('world-density-maps-country-wise').style.display = 'none';
    document.getElementById('world-growth-maps-continent-wise').style.display = 'none';
    document.getElementById('world-growth-maps-country-wise').style.display = 'none';
    if (view === 'whole') {
        document.getElementById('world-population-maps-country-wise').style.display = '';
        document.getElementById('world-density-maps').style.display = '';
        document.getElementById('world-growth-maps').style.display = '';
    } else if (view === 'continent-wise') {
        document.getElementById('world-population-maps-continent-wise').style.display = '';
        document.getElementById('world-density-maps-continent-wise').style.display = '';
        document.getElementById('world-growth-maps-continent-wise').style.display = '';
    } else if (view === 'country-wise') {
        document.getElementById('world-population-maps').style.display = '';
        document.getElementById('world-density-maps-country-wise').style.display = '';
        document.getElementById('world-growth-maps-country-wise').style.display = '';
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Show loading spinner on page load
    const loadingEl = document.getElementById('loading');
    if (loadingEl) loadingEl.style.display = 'block';

    // Add event listeners for map view toggles FIRST
    const continentMapToggles = document.querySelectorAll('input[name="continent-map-view"]');
    console.log("Found continent map toggles:", continentMapToggles.length);
    continentMapToggles.forEach(toggle => {
        toggle.addEventListener('change', (e) => {
            console.log("Radio button clicked for continent map view:", e.target.value);
            updateMapView('continent', e.target.value);
        });
    });
    // Set initial view
    const checkedContinent = document.querySelector('input[name="continent-map-view"]:checked');
    if (checkedContinent) {
        console.log("Setting initial continent map view:", checkedContinent.value);
        showContinentMapView(checkedContinent.value);
    }

    const worldMapToggles = document.querySelectorAll('input[name="world-map-view"]');
    console.log("Found world map toggles:", worldMapToggles.length);
    worldMapToggles.forEach(toggle => {
        toggle.addEventListener('change', (e) => {
            console.log("Radio button clicked for world map view:", e.target.value);
            updateMapView('world', e.target.value);
        });
    });
    // Set initial view
    const checkedWorld = document.querySelector('input[name="world-map-view"]:checked');
    if (checkedWorld) {
        console.log("Setting initial world map view:", checkedWorld.value);
        showWorldMapView(checkedWorld.value);
    }

    // Check if we are in the handshake phase (not redirected yet)
    const pendingData = sessionStorage.getItem('pendingVisualizationData');
    if (pendingData) {
        // Parse the form data
        const formData = JSON.parse(pendingData);
        console.log("visualization.js: Loaded pendingVisualizationData from sessionStorage", formData);
        // Send POST to /get_data
        console.log("visualization.js: Sending POST to /get_data with", formData);
        fetch('/get_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(result => {
            console.log("visualization.js: Received plots from app.py", result);
            if (result.status === 'success') {
                // Store the plots and form data for later display
                sessionStorage.setItem('visualizationData', JSON.stringify({
                    formData: formData,
                    plots: result.plots
                }));
                // Remove the pending data
                sessionStorage.removeItem('pendingVisualizationData');
                // Hide loading spinner
                if (loadingEl) loadingEl.style.display = 'none';
                // Display the visualizations
                const { plots } = result;
                updateVisibleSections(formData.selection_types);
                updateSectionTitles(formData);
                displayVisualizations(plots);
            } else {
                alert('Error: ' + result.message);
                if (loadingEl) loadingEl.style.display = 'none';
            }
        })
        .catch(error => {
            alert('Error processing request');
            if (loadingEl) loadingEl.style.display = 'none';
        });
        // Do NOT display anything yet; wait for fetch
        return;
    }

    // If redirected, display the visualizations as before
    const storedData = sessionStorage.getItem('visualizationData');
    if (storedData) {
        const { formData, plots } = JSON.parse(storedData);
        console.log("visualization.js: Displaying plots after redirect", plots);
        updateVisibleSections(formData.selection_types);
        updateSectionTitles(formData);
        displayVisualizations(plots);
        sessionStorage.removeItem('visualizationData');
        if (loadingEl) loadingEl.style.display = 'none';
    } else {
        window.location.href = '/';
    }
}); 