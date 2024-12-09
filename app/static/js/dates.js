function setDateRange(range) {
    const today = new Date();
    let startDate = new Date(today);  // Clone today
    
    switch(range) {
        case 'today':
            startDate = today;
            break;
        case 'last-7':
            startDate.setDate(today.getDate() - 6);
            break;
        case 'this-month':
            startDate.setDate(1);
            break;
        case 'last-30':
            startDate.setDate(today.getDate() - 29);
            break;
    }
    
    document.getElementById('custom-dates').style.display = 'none';
    document.querySelectorAll('.date-shortcut').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    document.getElementById('start_date').value = formatDate(startDate);
    document.getElementById('end_date').value = formatDate(today);
    
    document.querySelector('.filters-form').submit();
}

function toggleCustomDates() {
    const customDates = document.getElementById('custom-dates');
    customDates.style.display = 'flex';
    
    document.querySelectorAll('.date-shortcut').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

function formatDate(date) {
    return date.toISOString().split('T')[0];
} 