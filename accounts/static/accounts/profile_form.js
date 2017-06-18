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
})(jQuery);
