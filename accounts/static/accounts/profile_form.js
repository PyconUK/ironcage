(function($) {
  $('input[name=nationality]').data('provide', 'typeahead')
  $('input[name=nationality]').attr('autocomplete', 'off')

  $('input[name=nationality]').typeahead({
    source: countries
  });

  $('input[name=country_of_residence]').data('provide', 'typeahead')
  $('input[name=country_of_residence]').attr('autocomplete', 'off')

  $('input[name=country_of_residence]').typeahead({
    source: countries
  });

  $('input[name=accessibility_reqs_yn]').change(toggleAccessibilityField);
  $('input[name=childcare_reqs_yn]').change(toggleChildcareField);
  $('input[name=dietary_reqs_yn]').change(toggleDietaryField);

  $('input[name=dont_ask_demographics]').change(toggleDemographicsFields);

  function toggleAccessibilityField() {
    var formGroup = $('input[name=accessibility_reqs_yn]').closest('td').find('.form-group');
    if ($('input[name=accessibility_reqs_yn]:checked').val() == '2') {
      $(formGroup).show();
    } else {
      $(formGroup).hide();
    };
  }

  function toggleChildcareField() {
    var formGroup = $('input[name=childcare_reqs_yn]').closest('td').find('.form-group');
    if ($('input[name=childcare_reqs_yn]:checked').val() == '2') {
      $(formGroup).show();
    } else {
      $(formGroup).hide();
    };
  }

  function toggleDietaryField() {
    var formGroup = $('input[name=dietary_reqs_yn]').closest('td').find('.form-group');
    if ($('input[name=dietary_reqs_yn]:checked').val() == '2') {
      $(formGroup).show();
    } else {
      $(formGroup).hide();
    };
  }

  function toggleDemographicsFields() {
    console.log($('input[name=dont_ask_demographics]:checked').val());
    if ($('input[name=dont_ask_demographics]:checked').val() == 'on') {
      $('.demographics-field').hide();
    } else {
      $('.demographics-field').show();
    };
  }

  toggleAccessibilityField();
  toggleChildcareField();
  toggleDietaryField();
  toggleDemographicsFields();
})(jQuery);
