// =============================================
// MediCare HMS — Global JavaScript
// =============================================

document.addEventListener('DOMContentLoaded', function () {

  // ── 1. AUTO-DISMISS FLASH ALERTS ──────────
  // Flash messages disappear after 4 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-8px)';
      setTimeout(function () {
        if (alert.parentNode) alert.parentNode.removeChild(alert);
      }, 500);
    }, 4000);
  });

  // ── 2. RESTRICT PAST DATES FOR APPOINTMENTS ──
  // Sets today as the minimum selectable date
  const dateInput = document.querySelector('input[name="appointment_date"]');
  if (dateInput) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);
  }

  // ── 3. HIGHLIGHT ACTIVE NAV LINK ──────────
  // Marks the current page link as active
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(function (link) {
    // Compare path only (ignore query string)
    if (link.pathname === window.location.pathname) {
      link.classList.add('active');
    }
  });

  // ── 4. CONFIRM BEFORE DELETE ──────────────
  // Intercept delete buttons that don't already have onclick
  const deleteBtns = document.querySelectorAll('a.btn-danger');
  deleteBtns.forEach(function (btn) {
    if (!btn.getAttribute('onclick')) {
      btn.addEventListener('click', function (e) {
        if (!confirm('Are you sure you want to delete this record? This cannot be undone.')) {
          e.preventDefault();
        }
      });
    }
  });

  // ── 5. TABLE ROW SEARCH FILTER ────────────
  // If a search input exists above a .data-table, filter rows live
  const searchInput = document.getElementById('table-search');
  if (searchInput) {
    searchInput.addEventListener('input', function () {
      const query = this.value.toLowerCase();
      const rows  = document.querySelectorAll('.data-table tbody tr');
      rows.forEach(function (row) {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
      });
    });
  }

  // ── 6. CHECKBOX VISUAL FEEDBACK ──────────
  // Highlight checkbox-labels when checked
  const checkboxLabels = document.querySelectorAll('.checkbox-label');
  checkboxLabels.forEach(function (label) {
    const cb = label.querySelector('input[type="checkbox"]');
    if (!cb) return;

    // Apply initial state
    if (cb.checked) label.style.borderColor = 'var(--primary)';

    cb.addEventListener('change', function () {
      label.style.borderColor  = cb.checked ? 'var(--primary)' : '';
      label.style.color        = cb.checked ? 'var(--primary)' : '';
      label.style.background   = cb.checked ? '#eff6ff'        : '';
    });
  });

  // ── 7. FORM SUBMIT LOADING STATE ─────────
  // Disable submit button on click to prevent double-submissions
  const forms = document.querySelectorAll('form');
  forms.forEach(function (form) {
    form.addEventListener('submit', function () {
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Saving…';
      }
    });
  });

});