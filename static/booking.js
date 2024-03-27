// Define a dictionary mapping routes to stops and fares
var routeStops = {
    'Nairobi-Embakasi village': {
        stops: ['Makadara', 'Donholm', 'Pipeline'],
        fare: 100
    },
    'Nairobi-Syokimau': {
        stops: ['Makadara', 'Imara Daima', 'Nairobi terminus'],
        fare: 120
    },
    'Nairobi-Ruiru': {
        stops: ['Makadara', 'Dandora', 'Mwiki', 'Githurai', 'Kahawa west'],
        fare: 130
    },
    'Nairobi-Limuru': {
        stops: ['Kibera', 'Dagoreti', 'Kikuyu'],
        fare: 140
    },
    'Nairobi-Lukenya': {
        stops: ['Makadara', 'Imara Daima', 'Embakasi', 'Mlolongo', 'Arthi river', 'Kitengela'],
        fare: 150
    }
};

// Function to populate stops dropdown with fare information
function populateStopsDropdown(route) {
    var stopDropdown = document.getElementById('stop');
    // Clear previous options
    stopDropdown.innerHTML = '<option value="" disabled selected>Select Stop</option>';
    // Get the stops array and fare for the selected route
    var stops = routeStops[route].stops;
    var totalFare = routeStops[route].fare;
    // Calculate fare per stop
    var totalStops = stops.length;
    var baseFare = totalFare / totalStops; // Base fare for each stop
    // Populate with new options
    stops.forEach(function(stop, index) {
        // Calculate fare for current stop
        var stopFare = baseFare * (index + 1); // Fare decreases as stop moves further from origin
        // Append fare to stop name
        var optionText = `${stop} (Ksh ${stopFare.toFixed(2)})`; // Include fare in the option text
        var option = document.createElement('option');
        option.value = stop;
        option.textContent = optionText;
        stopDropdown.appendChild(option);
    });
    // Display route fare
    document.getElementById('routeFare').textContent = `Route Fare: Ksh ${totalFare.toFixed(2)}`;
}

// Function to book ticket
function bookTicket() {
    // Retrieve selected route and stop
    var route = document.getElementById('route').value;
    var stop = document.getElementById('stop').value;
    // Retrieve fare for selected stop
    var fare = parseFloat(document.getElementById('stop').selectedOptions[0].text.match(/\d+\.\d+/)[0]); // Extract fare from option text
    // Display booking information
    var bookingInfo = `You have booked a ticket for ${route} with stop at ${stop}. The fare for this stop is Ksh ${fare.toFixed(2)}.`;
    alert(bookingInfo);
}
