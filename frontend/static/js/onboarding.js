// onboarding.js – client‑side validation & HTMX helpers
// Uses Alpine.js for reactive state. HTMX handles form submission.
// Place this file at /frontend/static/js/onboarding.js and reference it in the template.

window.onboardingForm = function () {
  return {
    // Reactive fields
    fields: {
      company_name: '',
      contact_person: '',
      email: '',
      phone: '',
      address: '',
      terms: false,
    },
    // Track touched fields for UI feedback
    touched: {},
    // Validation errors per field
    errors: {},
    // Submission state
    isSubmitting: false,

    // Mark a field as touched
    touch(field) {
      this.touched[field] = true;
      this.validateField(field);
    },

    // Validate a single field
    validateField(field) {
      const val = this.fields[field];
      switch (field) {
        case 'company_name':
        case 'contact_person':
          this.errors[field] = val.trim() ? '' : 'Required';
          break;
        case 'email':
          const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
          this.errors[field] = emailRegex.test(val) ? '' : 'Invalid email';
          break;
        case 'terms':
          this.errors[field] = this.fields.terms ? '' : 'You must accept the terms';
          break;
        default:
          this.errors[field] = '';
      }
    },

    // Full form validation before HTMX submit
    validateAll() {
      const fields = Object.keys(this.fields);
      fields.forEach(f => this.validateField(f));
      // Return true if no errors
      return Object.values(this.errors).every(e => e === '');
    },

    // Called by @submit.prevent on the form
    async validateAndSubmit(formEl) {
      // Run validation
      if (!this.validateAll()) {
        // Focus first error field
        const firstError = Object.keys(this.errors).find(k => this.errors[k]);
        this.$nextTick(() => {
          const el = formEl.querySelector(`[name="${firstError}"]`);
          if (el) el.focus();
        });
        return false;
      }
      // No client‑side errors – let HTMX submit
      // HTMX automatically sends the request because we prevented default.
      // Force re‑trigger of submit (HTMX respects the form's hx‑* attributes)
      this.isSubmitting = true;
      // Dispatch a native submit event that HTMX will catch
      const submitEvent = new Event('submit', { cancelable: true, bubbles: true });
      formEl.dispatchEvent(submitEvent);
      // Reset submitting state after HTMX request finishes – HTMX adds hx‑request class
      const cleanup = () => {
        this.isSubmitting = false;
        formEl.removeEventListener('htmx:afterOnLoad', cleanup);
      };
      formEl.addEventListener('htmx:afterOnLoad', cleanup);
    },

    // Helper for styling input based on validation state
    fieldClass(field) {
      if (!this.touched[field]) return '';
      return this.errors[field] ? 'field-error' : 'field-success';
    },
  };
};
