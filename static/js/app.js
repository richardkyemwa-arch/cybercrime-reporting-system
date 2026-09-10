// Cyber Crime Reporting System - Client Side App Script
document.addEventListener('DOMContentLoaded', () => {

  // 1. PWA Service Worker Registration & Installation Prompt Handling
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
      .then(reg => console.log('ServiceWorker registered:', reg.scope))
      .catch(err => console.error('ServiceWorker registration failed:', err));
  }

  let deferredPrompt;
  const pwaBanner = document.getElementById('pwa-install-banner');
  const installBtn = document.getElementById('btn-install-app');

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (pwaBanner) pwaBanner.style.display = 'flex';
  });

  if (installBtn) {
    installBtn.addEventListener('click', () => {
      if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
          if (choiceResult.outcome === 'accepted') {
            console.log('User accepted PWA install prompt');
          }
          deferredPrompt = null;
          if (pwaBanner) pwaBanner.style.display = 'none';
        });
      }
    });
  }

  // 2. Multi-Step Form Wizard Navigation
  const wizardForm = document.getElementById('report-wizard-form');
  if (wizardForm) {
    let currentStep = 1;
    const totalSteps = 5;

    const btnNext = document.getElementById('btn-next-step');
    const btnPrev = document.getElementById('btn-prev-step');
    const btnSubmit = document.getElementById('btn-submit-report');

    function updateStepUI() {
      // Toggle step visibility
      document.querySelectorAll('.step-content').forEach(content => {
        content.classList.remove('active');
      });
      const currentContent = document.getElementById(`step-${currentStep}`);
      if (currentContent) currentContent.classList.add('active');

      // Update indicator dots
      for (let i = 1; i <= totalSteps; i++) {
        const item = document.getElementById(`step-item-${i}`);
        if (!item) continue;
        item.classList.remove('active', 'completed');
        if (i === currentStep) {
          item.classList.add('active');
        } else if (i < currentStep) {
          item.classList.add('completed');
        }
      }

      // Update buttons
      if (btnPrev) btnPrev.style.display = currentStep > 1 ? 'inline-flex' : 'none';
      if (btnNext) btnNext.style.display = currentStep < totalSteps ? 'inline-flex' : 'none';
      if (btnSubmit) btnSubmit.style.display = currentStep === totalSteps ? 'inline-flex' : 'none';
    }

    if (btnNext) {
      btnNext.addEventListener('click', () => {
        if (validateStep(currentStep)) {
          if (currentStep < totalSteps) {
            currentStep++;
            if (currentStep === 5) renderReviewSummary();
            updateStepUI();
          }
        }
      });
    }

    if (btnPrev) {
      btnPrev.addEventListener('click', () => {
        if (currentStep > 1) {
          currentStep--;
          updateStepUI();
        }
      });
    }

    // Step Validation
    function validateStep(step) {
      if (step === 1) {
        const catSelected = document.querySelector('input[name="category_id"]:checked');
        if (!catSelected) {
          alert('Please select a Cyber Crime Category.');
          return false;
        }
      } else if (step === 2) {
        const title = document.getElementById('title').value.trim();
        const desc = document.getElementById('description').value.trim();
        if (!title || !desc) {
          alert('Please fill out the Incident Title and Detailed Description.');
          return false;
        }
      }
      return true;
    }

    // Category Select Option Styling
    document.querySelectorAll('.category-option').forEach(option => {
      option.addEventListener('click', () => {
        document.querySelectorAll('.category-option').forEach(o => o.classList.remove('selected'));
        option.classList.add('selected');
        const radio = option.querySelector('input[type="radio"]');
        if (radio) radio.checked = true;
      });
    });

    // Anonymity Toggle Logic
    const anonCheck = document.getElementById('is_anonymous');
    const authInfoBox = document.getElementById('auth-info');
    const anonFieldsBox = document.getElementById('anonymous-fields');
    if (anonCheck && authInfoBox && anonFieldsBox) {
      anonCheck.addEventListener('change', () => {
        const anon = anonCheck.checked;
        authInfoBox.style.display = anon ? 'none' : 'block';
        anonFieldsBox.style.display = anon ? 'block' : 'none';
      });
    }

    // HTML5 Geolocation API
    const btnGetLocation = document.getElementById('btn-get-location');
    const locationStatus = document.getElementById('location-status');
    if (btnGetLocation) {
      btnGetLocation.addEventListener('click', () => {
        if (!navigator.geolocation) {
          if (locationStatus) locationStatus.textContent = 'Geolocation is not supported by your device.';
          return;
        }
        if (locationStatus) locationStatus.textContent = 'Acquiring GPS location...';
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            const lat = pos.coords.latitude.toFixed(6);
            const lng = pos.coords.longitude.toFixed(6);
            document.getElementById('latitude').value = lat;
            document.getElementById('longitude').value = lng;
            if (locationStatus) locationStatus.textContent = `GPS Captured: Lat ${lat}, Lng ${lng}`;
          },
          (err) => {
            if (locationStatus) locationStatus.textContent = 'Unable to retrieve location: ' + err.message;
          }
        );
      });
    }

    // Evidence File Preview
    const fileInput = document.getElementById('evidence_files');
    const previewList = document.getElementById('file-preview-list');
    if (fileInput && previewList) {
      fileInput.addEventListener('change', () => {
        previewList.innerHTML = '';
        Array.from(fileInput.files).forEach(file => {
          const div = document.createElement('div');
          div.className = 'file-preview-item';
          div.style.fontSize = '0.8rem';
          div.style.color = '#94a3b8';
          div.style.marginTop = '4px';
          div.innerHTML = `<i class="fas fa-paperclip"></i> ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
          previewList.appendChild(div);
        });
      });
    }

    // Review Step 5 Summary
    function renderReviewSummary() {
      const summaryBox = document.getElementById('review-summary-box');
      if (!summaryBox) return;

      const catText = document.querySelector('input[name="category_id"]:checked')?.parentElement?.innerText || 'N/A';
      const title = document.getElementById('title').value;
      const desc = document.getElementById('description').value;
      const loss = document.getElementById('financial_loss').value || '0.00';
      const isAnon = document.getElementById('is_anonymous')?.checked;

      summaryBox.innerHTML = `
        <div style="background:#090d16; padding:14px; border-radius:8px; border:1px solid #334155;">
          <p><strong>Category:</strong> ${catText.trim()}</p>
          <p><strong>Title:</strong> ${title}</p>
          <p><strong>Financial Loss:</strong> $${loss}</p>
          <p><strong>Reporter:</strong> ${isAnon ? '<span style="color:#f59e0b">Anonymous Victim</span>' : 'Provided Contact Info'}</p>
          <p style="margin-top:8px;"><strong>Description Snippet:</strong> ${desc.substring(0, 150)}...</p>
        </div>
      `;
    }

    // Form Submission via AJAX
    wizardForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const formData = new FormData(wizardForm);
      const submitBtn = document.getElementById('btn-submit-report');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
      }

      fetch('/report', {
        method: 'POST',
        body: formData
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          const successBox = document.getElementById('report-success-box');
          const wizardBox = document.getElementById('report-wizard-container');
          if (wizardBox) wizardBox.style.display = 'none';
          if (successBox) {
            successBox.style.display = 'block';
            document.getElementById('created-ref-no').textContent = data.reference_no;
          }
        } else {
          alert('Submission failed: ' + (data.error || 'Unknown error'));
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-check-circle"></i> Submit Official Report';
          }
        }
      })
      .catch(err => {
        alert('Network or server error: ' + err);
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<i class="fas fa-check-circle"></i> Submit Official Report';
        }
      });
    });
  }

});
