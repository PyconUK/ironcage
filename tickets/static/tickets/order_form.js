var RATES = {
  // These numbers are plucked out of the air
  // TODO don't hardcode these here
  individual: {
    ticketPrice: 18,
    dayPrice: 24,
  },
  corporate: {
    ticketPrice: 36,
    dayPrice: 48,
  },
};

(function($) {
  $('input[name=who]').change(maybeShowRestOfForm);
  $('input[name=rate]').change(maybeShowRestOfForm);
  $('input[type=checkbox]').change(recalculateTotal);

  $('#formset').formset({
    animateForms: true
  });
  $('#formset').on('formAdded', function(e) {
    $('input[type=checkbox]').change(recalculateTotal);
  });

  function maybeShowRestOfForm() {
    var who = $('#order-form')[0].elements.who.value;
    var rate = $('#order-form')[0].elements.rate.value;

    if (who == '' || rate == '') {
      return
    }

    $('#form-panel-self').hide();
    $('#form-panel-others').hide();

    if (who.match('self')) {
      $('#form-panel-self').show();
    }

    if (who.match('others')) {
      $('#form-panel-others').show();
    }

    $('#form-panel-submit').show();

    recalculateTotal();
  };

  function recalculateTotal() {
    var who = $('#order-form')[0].elements.who.value;
    var rate = $('#order-form')[0].elements.rate.value;

    var numTickets = 0;
    var numDays = 0;

    if (who.match('self')) {
      numTickets += 1;
      numDays += $('input[name=days]:checked').length;
    }

    if (who.match('others')) {
      $('[data-formset-form]').filter(':not([data-formset-form-deleted])').each(function(ix, form) {
        var numDaysForForm = $(form).find('input:checked').length;
        if (numDaysForForm > 0) {
          numTickets += 1;
          numDays += numDaysForForm;
        };
      });
    }

    var totalCost = numTickets * RATES[rate]['ticketPrice'] + numDays * RATES[rate]['dayPrice']

    $('#num-tickets').text(numTickets);
    $('#num-days').text(numDays);
    $('#total-cost').text(totalCost);
  };

  maybeShowRestOfForm();
})(jQuery);
