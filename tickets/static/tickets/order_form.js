(function($) {
  $('form#order-form').submit(maybeSubmitform);
  $('input[name=who]').change(maybeShowRestOfForm);
  $('input[name=rate]').change(maybeShowRestOfForm);
  $('input[type=checkbox]').change(recalculateTotal);

  $('#formset').formset({
    animateForms: true
  });
  $('#formset').on('formAdded', function(e) {
    $('input[type=checkbox]').change(recalculateTotal);
  });

  function maybeSubmitform(e) {
    var who = $('#order-form')[0].elements.who.value;
    var valid = true;

    if (who.match('self')) {
      var numDaysForSelf = $('input[name=days]:checked').length;

      if (numDaysForSelf == 0) {
        valid = false;
        $('input[name=days]').closest('.btn-group').addClass('error');
      };
    };

    if (who.match('others')) {
      var numValidForms = 0;

      $('[data-formset-form]').filter(':not([data-formset-form-deleted])').each(function(ix, form) {
        var numDaysForForm = $(form).find('input:checked').length;
        var emailAddr = $(form).find('input[type=email]')[0].value;

        if (emailAddr != '' && numDaysForForm == 0) {
          valid = false;
          $(form).find('.btn-group').addClass('error');
        };

        if (emailAddr != '' && numDaysForForm != 0) {
          numValidForms += 1;
        };
      });

      if (numValidForms == 0) {
        valid = false;

        if ($('[data-formset-form]').filter(':not([data-formset-form-deleted])').length == 0) {
          $('[data-formset-add]').click()
        };

        $($('[data-formset-form]').filter(':not([data-formset-form-deleted])')[0]).find('.btn-group').addClass('error');
      };
    };

    if (!valid) {
      e.preventDefault();
    };
  };

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
    };

    if (who.match('others')) {
      $('#form-panel-others').show();
    } else {
      $('input[type=email]').removeAttr('required');
    };

    if (rate == 'corporate') {
      $('#form-panel-company-details').show();
      $('input[name=company_name]').attr('required', '');
      $('textarea[name=company_addr]').attr('required', '');
    } else {
      $('#form-panel-company-details').hide();
      $('input[name=company_name]').removeAttr('required');
      $('textarea[name=company_addr]').removeAttr('required');
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
      var numDaysForSelf = $('input[name=days]:checked').length;
      numDays += numDaysForSelf;
      numTickets += 1;

      if (numDaysForSelf != 0) {
        $('input[name=days]').closest('.btn-group').removeClass('error')
      };
    }

    if (who.match('others')) {
      $('[data-formset-form]').filter(':not([data-formset-form-deleted])').each(function(ix, form) {
        var numDaysForForm = $(form).find('input:checked').length;
        if (numDaysForForm > 0) {
          numTickets += 1;
          numDays += numDaysForForm;
          $(form).find('input[type=email]').attr('required', '');
          $(form).find('.btn-group').removeClass('error');
        } else {
          $(form).find('input[type=email]').removeAttr('required');
        };
      });
    }

    var totalCost = numTickets * rates[rate]['ticket_price'] + numDays * rates[rate]['day_price']

    $('#num-tickets').text(numTickets);
    $('#num-days').text(numDays);
    $('#total-cost').text(totalCost);
  };

  maybeShowRestOfForm();
})(jQuery);
