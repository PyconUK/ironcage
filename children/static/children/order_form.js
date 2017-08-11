(function($) {
  $('#formset').formset({
    animateForms: true
  });

  $('#formset').on('formAdded formDeleted', recalculateTotal);
  $('#formset').on('formAdded formDeleted', setRequired);

  function recalculateTotal() {
    var numTickets = $('[data-formset-form]').filter(':not([data-formset-form-deleted])').length;

    $('#num-tickets').text(numTickets);
    $('#total-cost').text(numTickets * 5);
  };

  function setRequired() {
    $('[data-formset-form]').each(function(ix, form) {
      if (typeof $(form).data('formset-form-deleted') != 'undefined') {
        $(form).find('input').first().removeAttr('required');
      } else {
        $(form).find('input').first().attr('required', '');
      };
    });
  };
})(jQuery);
