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

    // --- AJAX Filtering for Search Results Page ---
    const filterForm = document.getElementById('advanced-filter-form');
    const resultsArea = document.getElementById('results-area');

    if (filterForm && resultsArea) {
        const updateResults = (url) => {
            // Show loading state
            resultsArea.style.opacity = '0.5';
            resultsArea.style.pointerEvents = 'none';

            fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.text())
            .then(html => {
                resultsArea.innerHTML = html;
                resultsArea.style.opacity = '1';
                resultsArea.style.pointerEvents = 'auto';
                
                // Re-bind pagination links
                bindPagination();
                
                // Update URL in browser without reload
                window.history.pushState({}, '', url);
            })
            .catch(err => {
                console.error('Lỗi tải kết quả:', err);
                resultsArea.style.opacity = '1';
                resultsArea.style.pointerEvents = 'auto';
            });
        };

        const bindPagination = () => {
            document.querySelectorAll('.ajax-page-link').forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const url = this.getAttribute('href');
                    if (url && url !== '#') {
                        updateResults(url);
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    }
                });
            });
        };

        // Handle select changes immediately
        filterForm.querySelectorAll('select').forEach(select => {
            select.addEventListener('change', function() {
                const catVal = filterForm.querySelector('select[name="category"]').value;
                const langVal = filterForm.querySelector('select[name="language"]').value;
                
                // SYNC Q FROM HEADER
                const headerSearchInput = document.querySelector('#header-search-form input[name="q"]');
                const sidebarQ = filterForm.querySelector('input[name="q"]');
                
                if (headerSearchInput && sidebarQ) {
                    // Logic: If both filters are "All", clear the keyword (User requirement)
                    if (catVal === "" && langVal === "") {
                        headerSearchInput.value = "";
                        sidebarQ.value = "";
                    } else {
                        sidebarQ.value = headerSearchInput.value;
                    }
                }

                const formData = new FormData(filterForm);
                const params = new URLSearchParams(formData);
                const url = `${filterForm.action}?${params.toString()}`;
                updateResults(url);
            });
        });

        // Handle form submit
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const catVal = filterForm.querySelector('select[name="category"]').value;
            const langVal = filterForm.querySelector('select[name="language"]').value;
            
            const headerSearchInput = document.querySelector('#header-search-form input[name="q"]');
            const sidebarQ = filterForm.querySelector('input[name="q"]');
            
            if (headerSearchInput && sidebarQ) {
                // Logic: If both filters are "All" when clicking Apply, clear keyword
                if (catVal === "" && langVal === "") {
                    headerSearchInput.value = "";
                    sidebarQ.value = "";
                } else {
                    sidebarQ.value = headerSearchInput.value;
                }
            }

            const formData = new FormData(filterForm);
            const params = new URLSearchParams(formData);
            const url = `${filterForm.action}?${params.toString()}`;
            updateResults(url);
        });

        // Handle header search form if on search page
        const headerSearchForm = document.getElementById('header-search-form');
        if (headerSearchForm) {
            headerSearchForm.addEventListener('submit', function(e) {
                if (window.location.pathname === '/search') {
                    e.preventDefault();
                    const q = headerSearchForm.querySelector('input[name="q"]').value;
                    const sidebarQ = filterForm.querySelector('input[name="q"]');
                    if (sidebarQ) sidebarQ.value = q;
                    
                    const formData = new FormData(filterForm);
                    const params = new URLSearchParams(formData);
                    const url = `${filterForm.action}?${params.toString()}`;
                    updateResults(url);
                    dropdown.classList.add('d-none');
                }
            });
        }

        // Handle clear filter (ONLY CLEAR FILTERS, KEEP KEYWORD)
        const clearFilterBtn = document.getElementById('btn-clear-filter');
        if (clearFilterBtn) {
            clearFilterBtn.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Reset only the select elements
                filterForm.querySelectorAll('select').forEach(select => {
                    select.selectedIndex = 0;
                });
                
                // Keep the current keyword from the header
                const headerSearchInput = document.querySelector('#header-search-form input[name="q"]');
                const sidebarQ = filterForm.querySelector('input[name="q"]');
                if (headerSearchInput && sidebarQ) {
                    sidebarQ.value = headerSearchInput.value;
                }
                
                const formData = new FormData(filterForm);
                const params = new URLSearchParams(formData);
                const url = `${filterForm.action}?${params.toString()}`;
                updateResults(url);
            });
        }

        bindPagination();
    }
});
