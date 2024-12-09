function toggleDetails(row, detailsId) {
    const detailsContainer = document.getElementById(detailsId);
    const expandIcon = row.querySelector('.expand-icon');
    
    if (detailsContainer.style.display === 'none') {
        detailsContainer.style.display = 'block';
        expandIcon.classList.add('expanded');
    } else {
        detailsContainer.style.display = 'none';
        expandIcon.classList.remove('expanded');
    }
} 