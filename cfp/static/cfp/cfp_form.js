(function($) {
  $('select[name=session_type]').change(maybeShowRestrictedFields);

  function maybeShowRestrictedFields() {
    if ($('select[name=session_type]').val() == 'talk') {
      $('input[name=would_like_longer_slot]').closest('.form-group').show();
    } else {
      $('input[name=would_like_longer_slot]').closest('.form-group').hide();
    };
  };

  maybeShowRestrictedFields();
})(jQuery);
