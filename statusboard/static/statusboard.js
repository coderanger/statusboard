$(function() {
  var creating = 0;
  var changed = [];
  var optionsMode = false;
  
  $('#menu').mouseenter(function() {
    $('#menu-inner').show();
  }).mouseleave(function() {
    $('#menu-inner').hide();
  });
  $('#menu-inner').hide();
  $('#menu-edit').click(function() {
    $('#library, .row .front, .row .back').toggle();
    if(optionsMode && changed.length > 0)
    {
      var curChanged = changed;
      var args = {widgets: curChanged};
      $.each(curChanged, function(i, v) {
        $('#'+v).find(':input').each(function() {
          var elm = $(this);
          args[elm.attr('id')] = elm.val();
        }).end().addClass('loading').html('<img src="/static/spinner.gif" />');
      });
      $.ajax({
        url: '/ajax/config',
        dataType: 'json',
        data: args,
        cache: false,
        type: 'POST',
        success: function(data) {
          $.each(data.output, function(k, v) {
            $('#widget_'+k).after(v).remove();
          });
        }
      });
      changed = [];
    }
    optionsMode = !optionsMode;
  });
  $('#library').children().wrap('<div class="library-wrapper" />');
  $('.library-wrapper').sortable({
    connectWith: '.row',
    helper: 'clone',
    beforeStop: function(evt, ui) {
      var add_before = $(ui.placeholder).next();
      var new_creating = creating;
      creating += 1;
      var spinner = '<div id="creating'+new_creating+'"class="box loading"><img src="/static/spinner.gif" /></div>';
      if(add_before.length) {
        add_before.before(spinner);
      } else {
        $(ui.placeholder).before(spinner);
      }
      $.ajax({
        url: '/ajax/add',
        dataType: 'json',
        data: {before: ((add_before.attr('id')||'').substring(7))||'end', 
               row: $(ui.placeholder).parents('.row').attr('id').substring(3), 
               type: $(ui.item).attr('id').substring(15)},
        cache: false,
        type: 'POST',
        success: function(data) {
          var tmp = $('#creating'+new_creating);
          var new_widget = tmp.after(data.output).next();
          tmp.remove();
          new_widget.find('.front').hide().end().find('.back').show();
        }
      })
    },
    stop: function(evt, ui) {
      $(this).sortable('cancel');
    }
  });
  $('.row').sortable({
    connectWith: '.row',
    placeholder: 'box placeholder',
    start: function(evt, ui) {
      $('#trash').show();
    },
    stop: function(evt, ui) {
      $('#trash').hide();
      
      var serialized = '';
      var max_i = 0;
      $('.row').each(function(i) {
        serialized += '&'+$(this).sortable('serialize', {key:'row'+i});
        max_i = i;
      });
      $.ajax({
        url: '/ajax/layout',
        dataType: 'json',
        data: 'rows='+(max_i+1)+serialized,
        cache: false,
        type: 'POST',
        success: function(data) {
          
        }
      });
    }
  });
  $('#trash').droppable({
    hoverClass: 'hover',
    tolerance: 'touch',
    drop: function(evt, ui) {
      ui.draggable.remove();
    }
  });
  
  // Setup change tracking for widget options
  $('.box .back input').live('change', function() {
    var widget = $(this).parents('.box').attr('id');
    changed.push(widget);
  });
});