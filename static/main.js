// Main JS for World Population Analysis Dashboard
document.addEventListener('DOMContentLoaded', function () {
    // Toggle continent dropdown
    const continentCheck = document.getElementById('continent_check');
    const continentDropdown = document.getElementById('continent_dropdown_container');

    const countryCheck = document.getElementById('country_check');
    const countryDropdown = document.getElementById('country_dropdown_container');

    // Enable/disable dropdowns based on checkboxes
    if (continentCheck) {
        continentCheck.addEventListener('change', () => {
            continentDropdown.style.display = continentCheck.checked ? 'block' : 'none';
        });
    }

    if (countryCheck) {
        countryCheck.addEventListener('change', () => {
            countryDropdown.style.display = countryCheck.checked ? 'block' : 'none';
        });
    }

    // Initialize noUiSlider for year range selection
    const slider = document.getElementById('slider-range');
    if (slider) {
        noUiSlider.create(slider, {
            start: [1970, 2032],
            connect: true,
            step: 1,
            range: {
                'min': 1970,
                'max': 2032
            },
            tooltips: [true, true],
            format: {
                to: val => parseInt(val),
                from: val => parseInt(val)
            }
        });

        // Update hidden form fields when slider values change
        slider.noUiSlider.on('update', function (values) {
            document.getElementById('start_year').value = values[0];
            document.getElementById('end_year').value = values[1];
            
            // Also update display values if display elements exist
            const startYearDisplay = document.getElementById('start_year_display');
            const endYearDisplay = document.getElementById('end_year_display');
            
            if (startYearDisplay) startYearDisplay.textContent = values[0];
            if (endYearDisplay) endYearDisplay.textContent = values[1];
        });
    }

    // Form validation and submission
    const generateBtn = document.getElementById('generate_btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get selected analysis types
            const worldChecked = document.getElementById('world_check')?.checked || false;
            const continentChecked = document.getElementById('continent_check')?.checked || false;
            const countryChecked = document.getElementById('country_check')?.checked || false;
            
            // Validate that at least one option is selected
            if (!worldChecked && !continentChecked && !countryChecked) {
                alert('Please select at least one analysis type (World, Continent, or Country)');
                return;
            }
            
            // Validate continent selection if checked
            if (continentChecked && !document.getElementById('continent_dropdown').value) {
                alert('Please select a continent');
                return;
            }
            
            // Validate country selection if checked
            if (countryChecked && !document.getElementById('country_dropdown').value) {
                alert('Please select a country');
                return;
            }
            
            // Get form values
            const data = {
                selection_types: [],
                start_year: document.getElementById('start_year').value,
                end_year: document.getElementById('end_year').value
            };
            
            if (worldChecked) data.selection_types.push('world');
            if (continentChecked) {
                data.selection_types.push('continent');
                data.continent = document.getElementById('continent_dropdown').value;
            }
            if (countryChecked) {
                data.selection_types.push('country');
                data.country = document.getElementById('country_dropdown').value;
            }
            
            // Show loading indicator
            const loadingEl = document.getElementById('loading');
            if (loadingEl) loadingEl.style.display = 'block';
            
            // Hide results container
            const resultsEl = document.getElementById('results_container');
            if (resultsEl) resultsEl.style.display = 'none';
            
            console.log("Sending visualization request:", data);
            
            // Send data to server
            fetch('/get_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                // Hide loading indicator
                if (loadingEl) loadingEl.style.display = 'none';
                
                if (data.status === 'error') {
                    console.error("Server returned error:", data.message);
                    alert(data.message);
                    return;
                }
                
                // Show results container
                if (resultsEl) resultsEl.style.display = 'block';
                
                // Update visualizations (will be implemented later)
                console.log("Received data:", data);
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error generating visualizations');
                if (loadingEl) loadingEl.style.display = 'none';
            });
        });
    }
});
