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

function populateStopsDropdown(route) {
    var stopDropdown = document.getElementById('stop');
    stopDropdown.innerHTML = '<option value="" disabled selected>Select Stop</option>';
    var stops = routeStops[route].stops;
    var totalFare = routeStops[route].fare;

    stops.forEach(function(stop, index) {
        var option = document.createElement('option');
        option.value = stop;
        option.textContent = stop;
        stopDropdown.appendChild(option);
    });
}

function calculateFare(route, stop) {
    var stops = routeStops[route].stops;
    var totalFare = routeStops[route].fare;
    var stopIndex = stops.indexOf(stop);
    var fare = totalFare * ((stopIndex + 1) / stops.length);
    return fare.toFixed(2); // Round to 2 decimal places
}

document.addEventListener('DOMContentLoaded', function() {
    var routeDropdown = document.getElementById('route');
    var stopDropdown = document.getElementById('stop');
    var fareInput = document.getElementById('fare');

    routeDropdown.addEventListener('change', function() {
        var selectedRoute = routeDropdown.value;
        populateStopsDropdown(selectedRoute);
        fareInput.value = ''; // Clear fare input when route changes
    });

    stopDropdown.addEventListener('change', function() {
        var selectedRoute = routeDropdown.value;
        var selectedStop = stopDropdown.value;
        var fare = calculateFare(selectedRoute, selectedStop);
        fareInput.value = fare;
    });

    document.getElementById('bookingForm').addEventListener('submit', function(event) {
        event.preventDefault();
        var selectedRoute = routeDropdown.value;
        var selectedStop = stopDropdown.value;
        var fare = fareInput.value;

        if (selectedRoute && selectedStop && fare) {
            localStorage.setItem('fare', fare);
            window.location.href = '/payment?fare=' + fare;
        } else {
            alert('Please select a route and stop.');
        }
    });
});
