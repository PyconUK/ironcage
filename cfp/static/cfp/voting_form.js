(function($) {
  console.log('loaded');
  $('input[name=is_interested]').change(function() {
    console.log('submitting');
    $('form#voting-form').submit()
  });
})(jQuery);
