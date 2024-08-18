document.addEventListener('DOMContentLoaded', function() {
    const reportContainer = document.getElementById('report-container');

    fetch('/api/report_data')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayReport(data.report);
            } else {
                reportContainer.innerHTML = '<p>Error fetching report data.</p>';
            }
        })
        .catch(error => {
            console.error('Error fetching report:', error);
            reportContainer.innerHTML = '<p>Error fetching report data.</p>';
        });

    function displayReport(report) {
        let html = `
            <h2>Booking Report</h2>
            <p>Name: ${report.name}</p>
            <p>Phone Number: ${report.phone_number}</p>
            <p>Stop: ${report.stop}</p>
            <p>Payment Status: ${report.payment_status}</p>
        `;
        reportContainer.innerHTML = html;
    }
});
