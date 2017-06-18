(function($) {
  $('input[name=accessibility_reqs_yn]').change(toggleAccessibilityField);
  $('input[name=childcare_reqs_yn]').change(toggleChildcareField);
  $('input[name=dietary_reqs_yn]').change(toggleDietaryField);

  function toggleAccessibilityField() {
    if ($('input[name=accessibility_reqs_yn]:checked').val() == '3') {
      $('#requirements-accessibility .form-group').hide();
    } else {
      $('#requirements-accessibility .form-group').show();
    }
  }

  function toggleChildcareField() {
    if ($('input[name=childcare_reqs_yn]:checked').val() == '3') {
      $('#requirements-childcare .form-group').hide();
    } else {
      $('#requirements-childcare .form-group').show();
    }
  }

  function toggleDietaryField() {
    if ($('input[name=dietary_reqs_yn]:checked').val() == '3') {
      $('#requirements-dietary .form-group').hide();
    } else {
      $('#requirements-dietary .form-group').show();
    }
  }

  toggleAccessibilityField();
  toggleChildcareField();
  toggleDietaryField();
})(jQuery);
