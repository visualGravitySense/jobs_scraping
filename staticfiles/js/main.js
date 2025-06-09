// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Add active class to current nav item
    const currentLocation = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentLocation) {
            link.classList.add('active');
        }
    });

    // Handle form submissions with confirmation
    const forms = document.querySelectorAll('form[data-confirm]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.add('fade');
            setTimeout(() => alert.remove(), 150);
        }, 5000);
    });

    // Handle dynamic form fields
    const addFormField = document.querySelector('.add-form-field');
    if (addFormField) {
        addFormField.addEventListener('click', function(e) {
            e.preventDefault();
            const template = this.dataset.template;
            const container = document.querySelector(this.dataset.container);
            const newField = template.replace(/__prefix__/g, container.children.length);
            container.insertAdjacentHTML('beforeend', newField);
        });
    }

    // Handle search form submission
    const searchForm = document.querySelector('#search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = this.querySelector('input[name="search"]');
            if (!searchInput.value.trim()) {
                e.preventDefault();
            }
        });
    }

    // Handle filter form changes
    const filterForm = document.querySelector('#filter-form');
    if (filterForm) {
        const filterInputs = filterForm.querySelectorAll('select, input[type="checkbox"]');
        filterInputs.forEach(input => {
            input.addEventListener('change', () => filterForm.submit());
        });
    }
}); 