$(function() {
  
  /* Create new expense -form */
  if($('#expenses').length) {

    if($('.delete-expenseline').length > 1) {
      $('.delete-expenseline').css('background-color','#253764');
    }

    if($('.delete-expenseline').length <= 2) {
      $('.delete-expenseline').css('background-color','grey');
  }

  /* Prevent removing the last expenseline. 1 button is hidden for copying -> length ==2 */
    // if($('.delete-expenseline').length == 2) {
    //   $('.delete-expenseline button').first().prop('hidden')
    //   $('.delete-expenseline').first().prop('disabled', true)
    // }

    $(this).find(".datepicker").each(function() {
      $(this).datepicker({
        dateFormat: "dd.mm.yy",
        firstDay: 1
      })
    })
    
    var fixIndexes = function() {
      $('#expenses .expenseline').each(function(i) {
        // Labels
        $(this).find('label').each(function() {
          $(this).attr('for', $(this).attr('for').replace(/EXPENSELINES-.*-/, "EXPENSELINES-" + i + "-"));
        });
        
        // Inputs & Selects
        $(this).find('input, select').each(function() {
          $(this).attr('id', $(this).attr('id').replace(/EXPENSELINES-.*-/, "EXPENSELINES-" + i + "-"));
          $(this).attr('name', $(this).attr('name').replace(/EXPENSELINES-.*-/, "EXPENSELINES-" + i + "-"));
        });
      });
    }
    
    /* Add new expenseline*/
    $('#add-new-expenseline').on('click', function(e) {
      e.preventDefault();
      console.log($('.delete-expenseline').length)
      if($('.delete-expenseline').length > 1) {
        $('.delete-expenseline').css('background-color','#253764');
      }
      var clone = $('#empty-expenseline-form .expenseline')
        .clone();

      // Add the cloned empty form to the form
      clone.appendTo('#expenses');
      
      // Fix indexes (to make the validation and s bind correctly)
      fixIndexes();

      // Add datetimepickers to the new form
      clone.find(".datepicker").each(function() {
        $(this).removeClass('hasDatepicker').datepicker({
          dateFormat: "dd.mm.yy",
          firstDay: 1
        })
      })
          
      // Add validation to the new form
      var form = $('#expense-form');
      form.parsley()
      clone.find("input, select").not(":disabled, input[type=hidden], input[type=file]")
        .each(function() {
          form.parsley( 'addItem', $(this));
        });
    });

    findExpensetypeData2 =function findExpensetypeData2(seekFor) {
      var correct;
      $.each(expensetype_data, function(i, el) {
        if (el.name == seekFor) {
          correct = el;
          return false;
        }
      });
      return correct;
    }
    
    /* Delete single expenselines without removing all of them*/
    $('#expenses').on('click', '.delete-expenseline', function(e) {
      e.preventDefault();
      var line = $(this).closest('.expenseline');

      if($('.delete-expenseline').length <= 2) {
        return;
      }

      // Remove validations
      var form = $('#expense-form');
      line.find("input, select").not(":disabled, input[type=hidden], input[type=file]")
        .each(function() {
          form.parsley( 'removeItem', $(this));
        });
      
      // Remove the actual element

      line.remove();

      if($('.delete-expenseline').length <= 2) {
          $('.delete-expenseline').css('background-color','grey');
      }
    });
    
    /* Calculate single row total */
    // Find this once
    var expensetype_data = JSON.parse($('[id$="expensetype_data"]').first().val());
    $.each(expensetype_data, function() {
      this.multiplier = parseFloat(this.multiplier);
    });
    
    var findExpensetypeData = function findExpensetypeData(seekFor) {
      var correct;
      $.each(expensetype_data, function(i, el) {
        if (el.name == seekFor) {
          correct = el;
          return false;
        }
      });
      return correct;
    }, updateRow = function updateRow($row) {
      if(!$row.find('.subtotal').length) {
        $row.find('input[id$=basis]').after($('<span class="subtotal"/>'));
      }
      
      var $type = $row.find('[id$="expensetype"] :selected'),
          $subtotal = $row.find('.subtotal'),
          row_sum = 0;
          
      if($type.val() != '') {
        var $type_data = findExpensetypeData($type.text()),
            $basis = $row.find('input[id$=basis]'),
            subtotal_text = '';
        if($type_data) {
          subtotal_text = ' ' + $type_data.unit + ' × ' + $type_data.multiplier.toString().replace('.', ',') + ' = ';

          if($type_data.requires_endtime) {
            $row.find(".ended_at_date").parent().addClass('required');
            $row.find(".ended_at_date").parent().removeClass('visuallyhidden')
            $row.find(".ended_at_date").prop("disabled", false)
    
            $row.find(".ended_at_time").parent().addClass('required');
            $row.find(".ended_at_time").parent().removeClass('visuallyhidden')
            $row.find(".ended_at_time").prop("disabled", false)
          } else {
            $row.find(".ended_at_date").parent().addClass('required');
            $row.find(".ended_at_date").parent().addClass('visuallyhidden')
            $row.find(".ended_at_time").prop("disabled", true)
    
            $row.find(".ended_at_time").parent().removeClass('required');
            $row.find(".ended_at_time").parent().addClass('visuallyhidden')
            $row.find(".ended_at_time").prop("disabled", true)
          }
    
          if($type_data.requires_start_time) {
            $row.find(".begin_at_time").parent().addClass('required');
            $row.find(".begin_at_time").parent().removeClass('visuallyhidden')
            $row.find(".begin_at_time").prop("disabled", false)
          } else {
            $row.find(".begin_at_time").parent().removeClass('required');
            $row.find(".begin_at_time").parent().addClass('visuallyhidden')
            $row.find(".begin_at_time").prop("disabled", true)
          }
          
         if($basis.val() != '') {
            var basis = parseFloat($basis.val().replace(',', '.'));
            if (basis > 0) {
              var sum = basis * $type_data.multiplier;
              row_sum = sum.toFixed(2)
              subtotal_text += row_sum.replace('.', ',') + ' €';
            }
          }
        }
        
        $subtotal.text(subtotal_text);
        
      } else {
        $subtotal.text('');
      }
      
      $row.data('subtotal', row_sum);
      updateTotal();
      
    }, updateTotal = function UpdateTotal() {
      var $total = $('#expense-total span'),
          sum = 0.0;
      $('#expenses .expenseline').each(function() {
        sum += parseFloat($(this).data('subtotal'));
      });
      
      $total.text(sum.toFixed(2).replace('.', ',') + ' €');
    }
    
    $('#expenses').on('change keyup', '[id$="expensetype"], [id$="basis"]', function() {
      updateRow($(this).closest('.expenseline'));
    });
        
    /* Calculate whole form total */
    
    /* Delegate clicks to calendar icon to the actual input element */
    // $('#expenses').on('click', 'i.icon-calendar', function() {
    //   $(this)
    //     .parent()
    //     .find('input')
    //     .focus();
    // });
    
    /* Fix indexes and management form on form submit */
    $('#expense-form').on('submit', function() {
      
      fixIndexes();
      
      // Fix management form
      $('#id_expenseform_EXPENSELINES-TOTAL_FORMS').val($('#expenses .expenseline').length);
      
      // Let the form to be submitted
      return true;
    });
    
    /* Make enter to submit the form instead of adding more rows */
    $(window).keydown(function(event){
      if(event.keyCode == 13) {
        event.preventDefault();
        $('#expense-form').submit();
      }
    });
    
    /* Validation */
    $('#expense-form').parsley({
      excluded: 'input[type=hidden], input[type=file], :disabled, #empty-expenseline-form input, #empty-expenseline-form select',
      successClass: 'success',
      errorClass: 'error',
      errors: {
        classHandler: function ( elem, isRadioOrCheckbox ) {
          return $(elem).parent();
        },
        container: function ( elem, isRadioOrCheckbox ) {
          return $(elem).closest('.pure-control-group');
        },
        errorsWrapper: '<ul class="errorlist"></ul>'
      }
    });

    /* Open a preview of the POST data before actually saving */
    var $expense_form = $('#expense-form');
    $expense_form.on('submit.open_preview', function(event) {
      var is_valid = $expense_form.parsley('validate');
      if (is_valid) {
        $('body').append($('#preview-wrapper'));
        $('#preview-wrapper').fadeIn().find('#preview-background').css('opacity', '.75');
        $expense_form.attr('target', 'preview-frame');
        return true;
      } else {
        return false;
      }
    });
  }

  /* Expense preview */
  if($('#expense-preview-buttons').length) {
    $('#close-preview-button').click(function() {
      window.top.$('#preview-wrapper').fadeOut();
    });
    window.top.$('#expense-form').on('submit.save_form', function() {
      $("#confirm-expense-button-wrapper").addClass("loading");
    });
    $('#confirm-expense-button').click(function() {
      window.top.$('#expense-form').find('#id_preview').val(0);
      window.top.$('#expense-form').off('submit.open_preview').attr('target', '').submit();
    });
  }
  
  /* Expensetypes */
  if($('#organisation-form').length) {
        
    var fixIndexes = function() {
      $('#expensetypes .expensetype').each(function(i) {

        console.log('fixing index ' + i);

        // Labels
        $(this).find('label').each(function() {
          $(this).attr('for', $(this).attr('for').replace(/EXPENSETYPES-.*-/, "EXPENSETYPES-" + i + "-"));
        });
        
        // Inputs & Selects
        $(this).find('input, select').each(function() {
          $(this).attr('id', $(this).attr('id').replace(/EXPENSETYPES-.*-/, "EXPENSETYPES-" + i + "-"));
          $(this).attr('name', $(this).attr('name').replace(/EXPENSETYPES-.*-/, "EXPENSETYPES-" + i + "-"));
        });
      });

      // Fix management form
      $('#id_organisationform_EXPENSETYPES-TOTAL_FORMS').val($('#expensetypes .expensetype').length);
    }
    
    /* Add new expensetype*/
    $('#add-new-expensetype').on('click', function(e) {
      e.preventDefault();
      var clone = $('#empty-expensetype-form .expensetype')
        .clone()
        .appendTo('#expensetypes');
        fixIndexes();
    });
    
    /* Fix indexes and management form on form submit */
    $('#expense-form').on('submit', function() {
      
      fixIndexes();
      
      // Let the form to be submitted
      return true;
    });
    
    /* Make enter to submit the form instead of adding more rows */
    $(window).keydown(function(event){
      if(event.keyCode == 13) {
        event.preventDefault();
        $('#organisation-form').submit();
      }
    });

  }

  /* Make all form submit buttons loadable */
  $('.submit-button-wrapper').each(function () {
    var $this = $(this);
    var $form = $this.closest('form');
    $form.on('submit', function() {
      $this.addClass("loading");
    });
  });

});
