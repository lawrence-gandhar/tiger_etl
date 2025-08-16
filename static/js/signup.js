/**
 * Signup Form Validation for Tiger ETL
 * This file contains client-side validation for the signup form
 */

class SignupValidator {
    constructor() {
        this.emailField = document.getElementById('email');
        this.passwordField = document.getElementById('password');
        this.confirmPasswordField = document.getElementById('confirm_passwd');
        this.submitButton = document.querySelector('.login-btn');
        this.form = document.querySelector('.login-form');
        
        // Only initialize if all required elements exist (this is the signup form)
        if (this.emailField && this.passwordField && this.confirmPasswordField && this.form) {
            this.initializeValidation();
        }
    }

    /**
     * Initialize all validation event listeners
     */
    initializeValidation() {
        if (this.emailField) {
            this.emailField.addEventListener('input', () => this.validateEmail());
            this.emailField.addEventListener('blur', () => this.validateEmail());
        }

        if (this.passwordField) {
            this.passwordField.addEventListener('input', () => this.validatePassword());
            this.passwordField.addEventListener('blur', () => this.validatePassword());
        }

        if (this.confirmPasswordField) {
            this.confirmPasswordField.addEventListener('input', () => this.validatePasswordConfirmation());
            this.confirmPasswordField.addEventListener('blur', () => this.validatePasswordConfirmation());
        }

        // Only attach validation to the specific signup form submission
        if (this.form && this.form.getAttribute('action') === '/signup') {
            this.form.addEventListener('submit', (e) => this.validateForm(e));
        }
    }

    /**
     * Validate email format
     */
    validateEmail() {
        const email = this.emailField.value.trim();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        if (!email) {
            this.setFieldError(this.emailField, 'Email address is required');
            return false;
        } else if (!emailRegex.test(email)) {
            this.setFieldError(this.emailField, 'Please enter a valid email address');
            return false;
        } else {
            this.setFieldSuccess(this.emailField);
            return true;
        }
    }

    /**
     * Validate password strength
     */
    validatePassword() {
        const password = this.passwordField.value;
        const requirements = {
            minLength: password.length >= 8,
            hasUpper: /[A-Z]/.test(password),
            hasLower: /[a-z]/.test(password),
            hasNumber: /\d/.test(password),
            hasSpecial: /[!@#$%^&*(),.?":{}|<>]/.test(password)
        };

        const errors = [];
        
        if (!requirements.minLength) {
            errors.push('At least 8 characters');
        }
        if (!requirements.hasUpper) {
            errors.push('At least one uppercase letter');
        }
        if (!requirements.hasLower) {
            errors.push('At least one lowercase letter');
        }
        if (!requirements.hasNumber) {
            errors.push('At least one number');
        }

        if (errors.length > 0) {
            this.setFieldError(this.passwordField, 'Password must contain: ' + errors.join(', '));
            return false;
        } else {
            this.setFieldSuccess(this.passwordField);
            // Revalidate confirm password if it has a value
            if (this.confirmPasswordField.value) {
                this.validatePasswordConfirmation();
            }
            return true;
        }
    }

    /**
     * Validate password confirmation
     */
    validatePasswordConfirmation() {
        const password = this.passwordField.value;
        const confirmPassword = this.confirmPasswordField.value;

        if (!confirmPassword) {
            this.setFieldError(this.confirmPasswordField, 'Please confirm your password');
            return false;
        } else if (password !== confirmPassword) {
            this.setFieldError(this.confirmPasswordField, 'Passwords do not match');
            return false;
        } else {
            this.setFieldSuccess(this.confirmPasswordField);
            return true;
        }
    }

    /**
     * Set field error state and message
     */
    setFieldError(field, message) {
        field.setCustomValidity(message);
        field.style.borderColor = '#dc3545';
        field.style.boxShadow = '0 0 0 3px rgba(220, 53, 69, 0.1)';
        
        // Remove any existing error message
        this.removeErrorMessage(field);
        
        // Add error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.cssText = `
            color: #dc3545;
            font-size: 0.875rem;
            margin-top: 0.25rem;
            padding: 0.25rem 0;
        `;
        errorDiv.textContent = message;
        
        field.parentNode.appendChild(errorDiv);
    }

    /**
     * Set field success state
     */
    setFieldSuccess(field) {
        field.setCustomValidity('');
        field.style.borderColor = '#28a745';
        field.style.boxShadow = '0 0 0 3px rgba(40, 167, 69, 0.1)';
        
        // Remove any existing error message
        this.removeErrorMessage(field);
    }

    /**
     * Remove error message from field
     */
    removeErrorMessage(field) {
        const existingError = field.parentNode.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }
    }

    /**
     * Validate entire form before submission
     */
    validateForm(event) {
        const isEmailValid = this.validateEmail();
        const isPasswordValid = this.validatePassword();
        const isConfirmPasswordValid = this.validatePasswordConfirmation();

        const isFormValid = isEmailValid && isPasswordValid && isConfirmPasswordValid;

        if (!isFormValid) {
            event.preventDefault();
            
            // Focus on first invalid field
            if (!isEmailValid) {
                this.emailField.focus();
            } else if (!isPasswordValid) {
                this.passwordField.focus();
            } else if (!isConfirmPasswordValid) {
                this.confirmPasswordField.focus();
            }

            // Show general error message
            this.showGeneralError('Please fix the errors above before submitting');
        } else {
            // Remove general error message if form is valid
            this.removeGeneralError();
        }

        return isFormValid;
    }

    /**
     * Show general form error message
     */
    showGeneralError(message) {
        this.removeGeneralError();
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'general-error';
        errorDiv.style.cssText = `
            background: #f8d7da;
            color: #721c24;
            padding: 1rem;
            border-radius: 6px;
            margin-bottom: 1.5rem;
            border: 1px solid #f5c6cb;
            text-align: center;
        `;
        errorDiv.textContent = message;
        
        const form = document.querySelector('.login-form');
        const firstFormGroup = form.querySelector('.form-group');
        form.insertBefore(errorDiv, firstFormGroup);
    }

    /**
     * Remove general error message
     */
    removeGeneralError() {
        const existingError = document.querySelector('.general-error');
        if (existingError) {
            existingError.remove();
        }
    }

    /**
     * Reset all field styles to default
     */
    resetFieldStyles() {
        [this.emailField, this.passwordField, this.confirmPasswordField].forEach(field => {
            if (field) {
                field.style.borderColor = '';
                field.style.boxShadow = '';
                field.setCustomValidity('');
                this.removeErrorMessage(field);
            }
        });
        this.removeGeneralError();
    }
}

// Utility functions
const Utils = {
    /**
     * Show/hide password visibility
     */
    togglePasswordVisibility(fieldId, toggleButtonId) {
        const field = document.getElementById(fieldId);
        const toggleButton = document.getElementById(toggleButtonId);
        
        if (field && toggleButton) {
            toggleButton.addEventListener('click', () => {
                const type = field.getAttribute('type') === 'password' ? 'text' : 'password';
                field.setAttribute('type', type);
                toggleButton.textContent = type === 'password' ? '👁️' : '🙈';
            });
        }
    },

    /**
     * Add real-time password strength indicator
     */
    addPasswordStrengthIndicator(passwordFieldId, containerId) {
        const passwordField = document.getElementById(passwordFieldId);
        const container = document.getElementById(containerId);
        
        if (passwordField && container) {
            passwordField.addEventListener('input', () => {
                const password = passwordField.value;
                const strength = this.calculatePasswordStrength(password);
                this.updateStrengthIndicator(container, strength);
            });
        }
    },

    /**
     * Calculate password strength score
     */
    calculatePasswordStrength(password) {
        let score = 0;
        let feedback = [];

        // Length check
        if (password.length >= 8) score += 1;
        else feedback.push('Use at least 8 characters');

        // Character variety checks
        if (/[a-z]/.test(password)) score += 1;
        else feedback.push('Include lowercase letters');

        if (/[A-Z]/.test(password)) score += 1;
        else feedback.push('Include uppercase letters');

        if (/\d/.test(password)) score += 1;
        else feedback.push('Include numbers');

        if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score += 1;
        feedback.push('Consider adding special characters');

        return { score, feedback };
    },

    /**
     * Update password strength visual indicator
     */
    updateStrengthIndicator(container, strength) {
        const colors = ['#dc3545', '#fd7e14', '#ffc107', '#28a745', '#20c997'];
        const labels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
        
        container.innerHTML = `
            <div style="margin-top: 0.5rem;">
                <div style="display: flex; height: 4px; background: #e9ecef; border-radius: 2px; overflow: hidden;">
                    ${Array.from({length: 5}, (_, i) => 
                        `<div style="flex: 1; background: ${i < strength.score ? colors[strength.score - 1] : 'transparent'};"></div>`
                    ).join('')}
                </div>
                <small style="color: ${colors[strength.score - 1] || '#6c757d'}; margin-top: 0.25rem; display: block;">
                    ${strength.score > 0 ? labels[strength.score - 1] : 'Enter a password'}
                </small>
            </div>
        `;
    }
};

// Initialize validation when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're specifically on the signup page
    const signupForm = document.querySelector('form[action="/signup"]');
    const confirmPasswordField = document.getElementById('confirm_passwd');
    
    // Only initialize if we're on the signup page with the signup form
    if (signupForm && confirmPasswordField) {
        new SignupValidator();
    }
});

// Export for potential use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SignupValidator, Utils };
}
