document.addEventListener('DOMContentLoaded', function() {
    const paymentOption = document.getElementById('paymentOption');
    const mobileMoneyDetails = document.getElementById('mobileMoneyDetails');

    // Show mobile money details when Mobile Money is selected
    paymentOption.addEventListener('change', function() {
        if (paymentOption.value === 'mobileMoney') {
            mobileMoneyDetails.style.display = 'block';
        } else {
            mobileMoneyDetails.style.display = 'none';
        }
    });

    // Handle form submission
    document.getElementById('paymentForm').addEventListener('submit', function(event) {
        event.preventDefault();
        const selectedPaymentMethod = paymentOption.value;
        const mobileNumber = document.getElementById('mobileNumber').value;

        if (selectedPaymentMethod === 'mobileMoney' && !validateMobileNumber(mobileNumber)) {
            alert('Please enter a valid mobile number starting with 07 or 01 and containing exactly 10 digits.');
            return;
        }

        // Process payment based on selected method
        if (selectedPaymentMethod === 'mobileMoney') {
            sendMobileMoneyPayment(mobileNumber);
        } else {
            alert('Payment processing for selected method is not implemented yet.');
        }
    });

    function validateMobileNumber(number) {
        // Validate mobile number format (10 digits starting with 07 or 01)
        return /^\b(07|01)\d{8}\b$/.test(number);
    }

    function sendMobileMoneyPayment(number) {
        // Send request to the server to initiate M-Pesa payment
        fetch('/api/payment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ mobileNumber: number })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Payment request sent successfully. Check your mobile for further instructions.');
            } else {
                alert('Failed to send payment request. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while processing your payment. Please try again.');
        });
    }
});
