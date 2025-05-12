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
function displayVisualizations(plotIds) {
    console.log("DEBUG: Full plot IDs object:", plotIds);

    // Helper function to set image source
    const setImage = async (id, plotId) => {
        const element = document.getElementById(id);
        console.log(`[DEBUG] setImage called for id='${id}', plotId='${plotId}'`);
        if (!element) {
            console.warn(`[DEBUG] No element found in DOM for id='${id}'`);
            return;
        }
        if (!plotId) {
            console.warn(`[DEBUG] No plotId provided for id='${id}'`);
            element.style.display = 'none';
            element.alt = 'No data available';
            return;
        }
        try {
            // Show loading state
            element.style.display = 'block';
            element.src = '';
            element.alt = 'Loading...';
            console.log(`[DEBUG] Fetching /get_plot/${plotId} for id='${id}'`);
            const response = await fetch(`/get_plot/${plotId}`);
            if (response.ok) {
                const blob = await response.blob();
                element.src = URL.createObjectURL(blob);
                element.alt = '';
                console.log(`[DEBUG] Successfully loaded image for id='${id}'`);
            } else {
                console.error(`[DEBUG] Failed to load plot for id='${id}', plotId='${plotId}', status=${response.status}`);
                element.style.display = 'none';
                element.alt = 'Failed to load image';
            }
        } catch (error) {
            console.error(`[DEBUG] Error loading plot for id='${id}', plotId='${plotId}':`, error);
            element.style.display = 'none';
            element.alt = 'Error loading image';
        }
    };

    // Display country visualizations
    if (plotIds.country) {
        Object.entries(plotIds.country).forEach(([type, id]) => {
            setImage(`country-${type}`, id);
        });
    }

    // Display continent visualizations
    if (plotIds.continent) {
        Object.entries(plotIds.continent).forEach(([type, id]) => {
            setImage(`continent-${type}`, id);
        });
    }

    // Display world visualizations
    if (plotIds.world) {
        Object.entries(plotIds.world).forEach(([type, id]) => {
            setImage(`world-${type}`, id);
        });
    }
}

// Helper to show only the selected map type for continent
function showContinentMapView(view) {
    // Hide all
    const ids = [
        'continent-population_maps',
        'continent-density_maps',
        'continent-growth_maps',
        'continent-population_maps_country_wise',
        'continent-density_maps_country_wise',
        'continent-growth_maps_country_wise'
    ];
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (!el) {
            console.warn(`Element '${id}' not found!`);
        } else {
            el.style.display = 'none';
        }
    });
    if (view === 'whole') {
        ['continent-population_maps', 'continent-density_maps', 'continent-growth_maps'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = '';
        });
    } else if (view === 'country-wise') {
        ['continent-population_maps_country_wise', 'continent-density_maps_country_wise', 'continent-growth_maps_country_wise'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = '';
        });
    }
}

// Helper to show only the selected map type for world
function showWorldMapView(view) {
    const ids = [
        'world-population_maps',
        'world-density_maps',
        'world-growth_maps',
        'world-population_maps_continent_wise',
        'world-population_maps_country_wise',
        'world-density_maps_continent_wise',
        'world-density_maps_country_wise',
        'world-growth_maps_continent_wise',
        'world-growth_maps_country_wise'
    ];
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (!el) {
            console.warn(`Element '${id}' not found!`);
        } else {
            el.style.display = 'none';
        }
    });
    if (view === 'whole') {
        ['world-population_maps', 'world-density_maps', 'world-growth_maps'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = '';
        });
    } else if (view === 'continent-wise') {
        ['world-population_maps_continent_wise', 'world-density_maps_continent_wise', 'world-growth_maps_continent_wise'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = '';
        });
    } else if (view === 'country-wise') {
        ['world-population_maps_country_wise', 'world-density_maps_country_wise', 'world-growth_maps_country_wise'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = '';
        });
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
                    plot_ids: result.plot_ids
                }));
                // Remove the pending data
                sessionStorage.removeItem('pendingVisualizationData');
                // Hide loading spinner
                if (loadingEl) loadingEl.style.display = 'none';
                // Display the visualizations
                const { plot_ids } = result;
                updateVisibleSections(formData.selection_types);
                updateSectionTitles(formData);
                displayVisualizations(plot_ids);
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
        const { formData, plot_ids } = JSON.parse(storedData);
        console.log("visualization.js: Displaying plots after redirect", plot_ids);
        updateVisibleSections(formData.selection_types);
        updateSectionTitles(formData);
        displayVisualizations(plot_ids);
        sessionStorage.removeItem('visualizationData');
        if (loadingEl) loadingEl.style.display = 'none';
    } else {
        window.location.href = '/';
    }
}); 