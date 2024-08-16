document.addEventListener('DOMContentLoaded', function() {
    const creditCardOption = document.getElementById('creditCardOption');
    const debitCardOption = document.getElementById('debitCardOption');
    const mobileMoneyOption = document.getElementById('mobileMoneyOption');

    const mobileMoneyDetails = document.getElementById('mobileMoneyDetails');
    const creditCardDetails = document.getElementById('creditCardDetails');
    const debitCardDetails = document.getElementById('debitCardDetails');

    // Event listeners for payment option images
    creditCardOption.addEventListener('click', function() {
        showPaymentDetails('creditCard');
    });

    debitCardOption.addEventListener('click', function() {
        showPaymentDetails('debitCard');
    });

    mobileMoneyOption.addEventListener('click', function() {
        showPaymentDetails('mobileMoney');
    });

    // Function to show payment details based on the selected option
    function showPaymentDetails(option) {
        mobileMoneyDetails.style.display = 'none';
        creditCardDetails.style.display = 'none';
        debitCardDetails.style.display = 'none';

        if (option === 'mobileMoney') {
            mobileMoneyDetails.style.display = 'block';
        } else if (option === 'creditCard') {
            creditCardDetails.style.display = 'block';
        } else if (option === 'debitCard') {
            debitCardDetails.style.display = 'block';
        }
    }

    // Handle form submission for Mobile Money
    document.getElementById('mobileMoneyForm').addEventListener('submit', function(event) {
        event.preventDefault();
        const mobileNumber = document.getElementById('mobileNumber').value;
        const fare = document.getElementById('fare').value;
        const bookingId = document.getElementById('bookingId').value;

        if (!validateMobileNumber(mobileNumber)) {
            alert('Please enter a valid mobile number starting with 07 or 01 and containing exactly 10 digits.');
            return;
        }

        sendMobileMoneyPayment(mobileNumber, fare, bookingId);
    });

    // Add similar form submission handlers for credit and debit card forms here

    function validateMobileNumber(number) {
        // Validate mobile number format (10 digits starting with 07 or 01)
        return /^\b(07|01)\d{8}\b$/.test(number);
    }

    function sendMobileMoneyPayment(number, fare, bookingId) {
        // Send request to the server to initiate M-Pesa payment
        fetch('/api/payment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ mobileNumber: number, fare: fare, bookingId: bookingId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = '/report/' + bookingId;
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
