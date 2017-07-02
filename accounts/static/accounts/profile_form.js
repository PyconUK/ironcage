(function($) {
  $('input[name=accessibility_reqs_yn]').change(toggleAccessibilityField);
  $('input[name=childcare_reqs_yn]').change(toggleChildcareField);
  $('input[name=dietary_reqs_yn]').change(toggleDietaryField);

  $('input[name=dont_ask_demographics]').change(toggleDemographicsFields);

  $('#id_gender').change(maybeShowGenderFreeText);
  $('#id_nationality').change(maybeShowNationalityFreeText);
  $('#id_country_of_residence').change(maybeShowCountryOfResidenceFreeText);
  $('#id_ethnicity').change(maybeShowEthnicityFreeText);

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
    if ($('input[name=dont_ask_demographics]:checked').val() == 'on') {
      $('.demographics-field').hide();
    } else {
      $('.demographics-field').show();
    };
  }

  function maybeShowGenderFreeText() {
    if ($('#id_gender').val() == 'other') {
      $('#id_gender_free_text').show();
      $('#id_gender').attr('name', null)
      $('#id_gender_free_text').attr('name', 'gender')
      $('#id_gender_free_text').attr('required', true)
    } else {
      $('#id_gender_free_text').hide();
      $('#id_gender').attr('name', 'gender')
      $('#id_gender_free_text').attr('name', null)
      $('#id_gender_free_text').attr('required', false)
    }
  };

  function maybeShowNationalityFreeText() {
    if ($('#id_nationality').val() == 'other') {
      $('#id_nationality_free_text').show();
      $('#id_nationality').attr('name', null)
      $('#id_nationality_free_text').attr('name', 'nationality')
      $('#id_nationality_free_text').attr('required', true)
    } else {
      $('#id_nationality_free_text').hide();
      $('#id_nationality').attr('name', 'nationality')
      $('#id_nationality_free_text').attr('name', null)
      $('#id_nationality_free_text').attr('required', false)
    }
  };

  function maybeShowCountryOfResidenceFreeText() {
    if ($('#id_country_of_residence').val() == 'other') {
      $('#id_country_of_residence_free_text').show();
      $('#id_country_of_residence').attr('name', null)
      $('#id_country_of_residence_free_text').attr('name', 'country_of_residence')
      $('#id_country_of_residence_free_text').attr('required', true)
    } else {
      $('#id_country_of_residence_free_text').hide();
      $('#id_country_of_residence').attr('name', 'country_of_residence')
      $('#id_country_of_residence_free_text').attr('name', null)
      $('#id_country_of_residence_free_text').attr('required', false)
    }
  };

  function maybeShowEthnicityFreeText() {
    if ($('#id_ethnicity').val().match('please describe')) {
      $('#id_ethnicity_free_text').show();
    } else {
      $('#id_ethnicity_free_text').hide();
    }
  };

  toggleAccessibilityField();
  toggleChildcareField();
  toggleDietaryField();
  toggleDemographicsFields();

  maybeShowGenderFreeText();
  maybeShowNationalityFreeText();
  maybeShowCountryOfResidenceFreeText();
  maybeShowEthnicityFreeText();
})(jQuery);
