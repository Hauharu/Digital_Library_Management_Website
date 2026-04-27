function calculateFine() {
    const ratioSelect = document.getElementById('damageRatio');
    const fineInput = document.getElementById('fineAmount');

    const bookPrice = parseFloat(ratioSelect.getAttribute('data-book-price')) || 0;
    
    if (ratioSelect.value === 'custom') {
        fineInput.readOnly = false;
        fineInput.focus();
        fineInput.classList.add('border-primary');
    } else {
        fineInput.readOnly = true;
        fineInput.classList.remove('border-primary');
        const ratio = parseFloat(ratioSelect.value);
        const calculatedFine = Math.round(bookPrice * ratio);
        fineInput.value = calculatedFine;
    }
}

document.addEventListener('DOMContentLoaded', calculateFine);