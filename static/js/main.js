// Main JavaScript file for TU SANG Family Tree

// Global variables
let currentUser = null;
let familyMembers = [];
let relationships = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            // Only prevent default and scroll if href is not just "#"
            if (href && href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
}

// Form validation helpers
function validateForm(formId) {
    const form = document.getElementById(formId);
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;

    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });

    return isValid;
}

// Date validation
function validateDates(birthDate, deathDate) {
    if (birthDate && deathDate) {
        const birth = new Date(birthDate);
        const death = new Date(deathDate);
        return death > birth;
    }
    return true;
}

// Show loading state for buttons
function showLoadingState(button, text = 'Loading...') {
    const originalText = button.innerHTML;
    button.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${text}`;
    button.disabled = true;
    return originalText;
}

// Hide loading state for buttons
function hideLoadingState(button, originalText) {
    button.innerHTML = originalText;
    button.disabled = false;
}

// Show success message
function showSuccessMessage(message, containerId = 'successMessage') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
        container.style.display = 'block';
        container.classList.remove('alert-danger');
        container.classList.add('alert-success');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            container.style.display = 'none';
        }, 5000);
    }
}

// Show error message
function showErrorMessage(message, containerId = 'errorMessage') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${message}`;
        container.style.display = 'block';
        container.classList.remove('alert-success');
        container.classList.add('alert-danger');
        
        // Auto-hide after 7 seconds
        setTimeout(() => {
            container.style.display = 'none';
        }, 7000);
    }
}

// Format date for display
function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Calculate age
function calculateAge(birthDate, deathDate = null) {
    if (!birthDate) return 'Unknown';
    
    const birth = new Date(birthDate);
    const end = deathDate ? new Date(deathDate) : new Date();
    const age = end.getFullYear() - birth.getFullYear();
    const monthDiff = end.getMonth() - birth.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && end.getDate() < birth.getDate())) {
        return age - 1;
    }
    
    return age;
}

// Export data functions
function exportToCSV(data, filename) {
    const csv = convertToCSV(data);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

function convertToCSV(data) {
    if (!data.length) return '';
    
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => {
            const value = row[header];
            return typeof value === 'string' && value.includes(',') ? `"${value}"` : value;
        }).join(','))
    ].join('\n');
    
    return csvContent;
}

// Print functionality
function printPage() {
    window.print();
}

// Search functionality
function searchFamilyMembers(query) {
    if (!query.trim()) return familyMembers;
    
    const searchTerm = query.toLowerCase();
    return familyMembers.filter(member => 
        member.full_name.toLowerCase().includes(searchTerm) ||
        (member.chinese_name && member.chinese_name.toLowerCase().includes(searchTerm)) ||
        (member.nickname && member.nickname.toLowerCase().includes(searchTerm)) ||
        (member.birth_place && member.birth_place.toLowerCase().includes(searchTerm)) ||
        (member.notes && member.notes.toLowerCase().includes(searchTerm))
    );
}

// Local storage helpers
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        return true;
    } catch (error) {
        console.error('Error saving to localStorage:', error);
        return false;
    }
}

function loadFromLocalStorage(key) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : null;
    } catch (error) {
        console.error('Error loading from localStorage:', error);
        return null;
    }
}

// API helper functions
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Error handling
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showErrorMessage('An unexpected error occurred. Please try again.');
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    showErrorMessage('An unexpected error occurred. Please try again.');
});

// Export functions for global use
window.FamilyTreeApp = {
    validateForm,
    validateDates,
    showLoadingState,
    hideLoadingState,
    showSuccessMessage,
    showErrorMessage,
    formatDate,
    calculateAge,
    exportToCSV,
    printPage,
    searchFamilyMembers,
    saveToLocalStorage,
    loadFromLocalStorage,
    apiCall,
    debounce,
    throttle
};
