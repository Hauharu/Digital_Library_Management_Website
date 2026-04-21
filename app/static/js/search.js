/**
 * OU BOOK - Search Autocomplete
 */
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.querySelector('.header-search input[name="q"]');
    const searchContainer = document.querySelector('.header-search');
    
    if (!searchInput) return;

    // Create dropdown element
    const dropdown = document.createElement('div');
    dropdown.className = 'search-autocomplete-dropdown shadow-lg rounded-3 d-none';
    dropdown.style.position = 'absolute';
    dropdown.style.top = '100%';
    dropdown.style.left = '0';
    dropdown.style.width = '100%';
    dropdown.style.zIndex = '1000';
    dropdown.style.backgroundColor = '#fff';
    dropdown.style.marginTop = '8px';
    dropdown.style.maxHeight = '400px';
    dropdown.style.overflowY = 'auto';
    
    searchContainer.style.position = 'relative';
    searchContainer.appendChild(dropdown);

    let debounceTimer;

    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        
        clearTimeout(debounceTimer);
        
        if (query.length < 2) {
            dropdown.classList.add('d-none');
            return;
        }

        debounceTimer = setTimeout(() => {
            fetch(`/search/quick?q=${encodeURIComponent(query)}`)
                .then(response => response.text())
                .then(html => {
                    dropdown.innerHTML = html;
                    dropdown.classList.remove('d-none');
                })
                .catch(err => console.error('Lỗi tìm kiếm:', err));
        }, 300);
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchContainer.contains(e.target)) {
            dropdown.classList.add('d-none');
        }
    });

    // Handle "Advanced Filter" button in header
    const filterBtn = document.querySelector('.btn-filter');
    if (filterBtn) {
        filterBtn.addEventListener('click', function() {
            window.location.href = '/search';
        });
    }
});
