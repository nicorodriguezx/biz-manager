document.addEventListener('DOMContentLoaded', function() {
    // Format all prices on load
    document.querySelectorAll('[data-price]').forEach(el => {
        el.textContent = formatMoney(el.dataset.price);
    });

    // Handle form submission
    const form = document.getElementById('expense-form');
    form.addEventListener('submit', submitExpense);
});

function formatMoney(amount) {
    return `$ ${parseFloat(amount).toLocaleString('es-AR')}`;
}

function submitExpense(event) {
    event.preventDefault();
    
    const data = {
        date: event.target.querySelector('.date-input').value,
        amount: parseFloat(event.target.querySelector('.amount-input').value),
        description: event.target.querySelector('.description-input').value
    };

    fetch('/admin/expenses', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert(data.error || 'Error al registrar el gasto');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al procesar la solicitud');
    });
} 