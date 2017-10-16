(function($) {
  $('input[name=which_dinner]').change(showMenuForm);

  function showMenuForm() {
    var which = $('form')[0].elements.which_dinner.value;

    if (which == 'contributors') {
      $('#contributors-dinner-form').show();
      $('#contributors-dinner-form select').prop('disabled', false);

      $('#conference-dinner-form').hide();
      $('#conference-dinner-form select').prop('disabled', true);

      $('#dinner-submit').show();
    } else if (which == 'conference' ) {
      $('#contributors-dinner-form').hide();
      $('#contributors-dinner-form select').prop('disabled', true);

      $('#conference-dinner-form').show();
      $('#conference-dinner-form select').prop('disabled', false);

      $('#dinner-submit').show();
    } else {
      $('#contributors-dinner-form').hide();
      $('#contributors-dinner-form select').prop('disabled', true);

      $('#conference-dinner-form').hide();
      $('#conference-dinner-form select').prop('disabled', true);

      $('#dinner-submit').hide();
    };
  }
})(jQuery);

