// LTFPQRR Custom JavaScript

// Track if form is being submitted to avoid opacity change on form submission
let isFormSubmitting = false;

// Show loading spinner on page transitions (but not form submissions)
window.addEventListener('beforeunload', function() {
    if (!isFormSubmitting) {
        document.body.style.opacity = '0.7';
    }
});

document.addEventListener('DOMContentLoaded', function() {
    // Reset page state when page loads
    resetPageState();
    
    // Add ARIA labels for accessibility
    document.querySelectorAll('.btn').forEach(btn => {
        if (!btn.getAttribute('aria-label') && btn.textContent.trim()) {
            btn.setAttribute('aria-label', btn.textContent.trim());
        }
    });

    // Reset page state function
    function resetPageState() {
        // Reset form submission flag
        isFormSubmitting = false;
        
        // Reset page opacity
        document.body.style.opacity = '1';
        
        // Reset all submit buttons
        document.querySelectorAll('button[type="submit"]').forEach(btn => {
            btn.disabled = false;
            // Restore original button text if it was stored
            const originalText = btn.getAttribute('data-original-text');
            if (originalText && (btn.innerHTML.includes('Processing...') || btn.innerHTML.includes('fa-spinner'))) {
                btn.innerHTML = originalText;
            }
        });
    }

    // Handle page show events (including back button navigation)
    window.addEventListener('pageshow', function(event) {
        // Reset state when page is shown (including from cache)
        resetPageState();
    });

    // Error handling for images
    document.querySelectorAll('img').forEach(img => {
        img.addEventListener('error', function() {
            this.style.display = 'none';
            const fallback = document.createElement('div');
            fallback.className = 'image-placeholder d-flex align-items-center justify-content-center bg-light text-muted';
            fallback.style.height = this.height || '200px';
            fallback.innerHTML = '<i class="fas fa-image fa-2x"></i>';
            this.parentNode.insertBefore(fallback, this);
        });
    });

    // Form validation feedback
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            isFormSubmitting = true;
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                // Store original text before changing
                if (!submitBtn.getAttribute('data-original-text')) {
                    submitBtn.setAttribute('data-original-text', submitBtn.innerHTML);
                }
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                submitBtn.disabled = true;
            }
        });
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Fade in animations on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate__animated', 'animate__fadeInUp');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe all cards and stats
    document.querySelectorAll('.feature-card, .stats-card, .process-step').forEach(el => {
        observer.observe(el);
    });

    // Counter animation for stats
    function animateCounter(element, target) {
        let current = 0;
        const increment = target / 100;
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            
            if (target.toString().includes('%')) {
                element.textContent = Math.floor(current) + '%';
            } else if (target.toString().includes('+')) {
                element.textContent = Math.floor(current).toLocaleString() + '+';
            } else if (target.toString().includes('/')) {
                element.textContent = target;
            } else {
                element.textContent = Math.floor(current).toLocaleString();
            }
        }, 20);
    }

    // Animate stats when they come into view
    const statsObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const statsNumber = entry.target.querySelector('.stats-number');
                if (statsNumber && !statsNumber.classList.contains('animated')) {
                    statsNumber.classList.add('animated');
                    const text = statsNumber.textContent;
                    
                    if (text.includes('5,000+')) {
                        animateCounter(statsNumber, '5,000+');
                    } else if (text.includes('98%')) {
                        animateCounter(statsNumber, '98%');
                    } else if (text.includes('24/7')) {
                        statsNumber.textContent = '24/7';
                    }
                }
                statsObserver.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.stats-card').forEach(el => {
        statsObserver.observe(el);
    });

    // Form validation and UX improvements
    const searchForm = document.querySelector('form[action=""]');
    if (searchForm) {
        const tagInput = searchForm.querySelector('input[name="tag_id"]');
        const submitBtn = searchForm.querySelector('button[type="submit"]');
        
        if (tagInput && submitBtn) {
            // Format tag input as user types
            tagInput.addEventListener('input', function(e) {
                let value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
                
                // Add formatting for readability
                if (value.length > 3) {
                    value = value.slice(0, 3) + value.slice(3, 6) + value.slice(6, 8);
                }
                
                e.target.value = value;
                
                // Enable/disable submit button
                submitBtn.disabled = value.length < 6;
                if (value.length >= 6) {
                    submitBtn.classList.remove('btn-secondary');
                    submitBtn.classList.add('btn-primary');
                } else {
                    submitBtn.classList.remove('btn-primary');
                    submitBtn.classList.add('btn-secondary');
                }
            });

            // Loading state on form submit
            searchForm.addEventListener('submit', function(e) {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
                submitBtn.disabled = true;
            });
        }
    }

    // Add hover effects to cards
    document.querySelectorAll('.feature-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Add ripple effect to buttons
    document.querySelectorAll('.btn').forEach(button => {
        button.addEventListener('click', function(e) {
            if (this.classList.contains('btn-primary') || this.classList.contains('btn-success')) {
                const ripple = document.createElement('span');
                const rect = this.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                const x = e.clientX - rect.left - size / 2;
                const y = e.clientY - rect.top - size / 2;
                
                ripple.style.width = ripple.style.height = size + 'px';
                ripple.style.left = x + 'px';
                ripple.style.top = y + 'px';
                ripple.classList.add('ripple');
                
                this.appendChild(ripple);
                
                setTimeout(() => {
                    ripple.remove();
                }, 600);
            }
        });
    });

    // Mobile menu improvements
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        // Close mobile menu when clicking on a link
        navbarCollapse.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth < 992) {
                    navbarToggler.click();
                }
            });
        });
    }

    // Add loading states for dashboard links
    document.querySelectorAll('a[href*="dashboard"], a[href*="register"], a[href*="login"]').forEach(link => {
        link.addEventListener('click', function(e) {
            if (!this.hasAttribute('target')) {
                const icon = this.querySelector('i');
                if (icon && !icon.classList.contains('fa-spin')) {
                    icon.classList.add('fa-spin');
                    setTimeout(() => {
                        if (icon) icon.classList.remove('fa-spin');
                    }, 2000);
                }
            }
        });
    });

    // Enhanced form validation for all forms
    document.querySelectorAll('form').forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            // Real-time validation feedback
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateField(this);
                }
            });
        });
        
        form.addEventListener('submit', function(e) {
            let isValid = true;
            
            inputs.forEach(input => {
                if (!validateField(input)) {
                    isValid = false;
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                const firstInvalid = form.querySelector('.is-invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    });

    function validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let message = '';

        // Remove existing validation classes
        field.classList.remove('is-valid', 'is-invalid');
        
        // Skip validation for optional fields
        if (!field.hasAttribute('required') && !value) {
            return true;
        }

        // Required field validation
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            message = 'This field is required';
        }

        // Email validation
        if (field.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                message = 'Please enter a valid email address';
            }
        }

        // Password validation
        if (field.type === 'password' && value) {
            if (value.length < 6) {
                isValid = false;
                message = 'Password must be at least 6 characters';
            }
        }

        // Tag ID validation
        if (field.name === 'tag_id' && value) {
            if (value.length < 6 || !/^[A-Za-z0-9]+$/.test(value)) {
                isValid = false;
                message = 'Tag ID must be at least 6 characters (letters and numbers only)';
            }
        }

        // Add validation classes
        field.classList.add(isValid ? 'is-valid' : 'is-invalid');
        
        // Show/hide validation message
        let feedback = field.parentElement.querySelector('.invalid-feedback');
        if (!isValid) {
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                field.parentElement.appendChild(feedback);
            }
            feedback.textContent = message;
        } else if (feedback) {
            feedback.remove();
        }

        return isValid;
    }

    // Add smooth transitions to all elements
    document.querySelectorAll('*').forEach(el => {
        if (!el.style.transition && !el.classList.contains('btn')) {
            el.style.transition = 'all 0.3s ease';
        }
    });
});

// Add CSS for ripple effect
const style = document.createElement('style');
style.textContent = `
    .btn {
        position: relative;
        overflow: hidden;
    }
    
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.6);
        transform: scale(0);
        animation: ripple-animation 0.6s linear;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .fade-in {
        opacity: 0;
        transform: translateY(30px);
        transition: all 0.8s ease;
    }
    
    .fade-in.animate__animated {
        opacity: 1;
        transform: translateY(0);
    }
    
    .navbar-brand img {
        transition: transform 0.3s ease;
    }
    
    .navbar-brand:hover img {
        transform: scale(1.1);
    }
    
    .btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }
    
    .is-invalid {
        border-color: #dc3545 !important;
        box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25) !important;
    }
    
    .is-valid {
        border-color: #28a745 !important;
        box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25) !important;
    }
    
    .invalid-feedback {
        display: block;
        width: 100%;
        margin-top: 0.25rem;
        font-size: 0.875rem;
        color: #dc3545;
    }
`;
document.head.appendChild(style);
