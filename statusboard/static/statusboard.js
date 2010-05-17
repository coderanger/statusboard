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
            $('#widget_'+k).trigger('statusboard-reload', [false]);
          });
        }
      });
      changed = [];
    }
    optionsMode = !optionsMode;
  });
  
  $('#menu-login').click(function() {
    return false;
  });
  
  $('.library-inner').children().not('.library-title').wrap('<div class="library-wrapper" style="width: 200px; height: 200px;" />');
  //$('#library .box2').parents('.library-wrapper').width(400);
  $('.library-wrapper').sortable({
    connectWith: '.row',
    helper: 'clone',
    placeholder: 'widget box placeholder',
    tolerance: 'pointer',
    start: function(evt, ui) {
        $(ui.placeholder).width($(ui.helper).width());
        if($('.row').last().find('.widget').length != 0) {
          var newid = $('.row').length;
          $('.row').last().after('<div id="row'+newid+'" class="row empty"><div class="clear"></div></div>');
          setup_sortable('#row'+newid);
          $('.library-wrapper').sortable('refresh');
        }
      },
    beforeStop: function(evt, ui) {
      if($(ui.placeholder).parents('#library').length > 0) {
        return;
      }
      var add_before = $(ui.placeholder).next();
      var new_creating = creating;
      creating += 1;
      var spinner = '<div id="creating'+new_creating+'" class="box loading"><img src="/static/spinner.gif" /></div>';
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
          new_widget.trigger('statusboard-reload', [true]).find('.front').hide().end().find('.back').show();
        }
      })
    },
    stop: function(evt, ui) {
      $(this).sortable('cancel');
    }
  });
  function setup_sortable(x) {
    $(x).sortable({
      connectWith: '.row',
      placeholder: 'widget box placeholder',
      tolerance: 'pointer',
      start: function(evt, ui) {
        $(ui.placeholder).width($(ui.helper).width());
        $('#trash').show(); 
        if($('.row').last().find('.widget').length != 0) {
          var newid = $('.row').length;
          $('.row').last().after('<div id="row'+newid+'" class="row empty"><div class="clear"></div></div>');
          setup_sortable('#row'+newid);
          $('.row').sortable('refresh');
        }
      },
      change: function(evt, ui) {
        $('.row').each(function() {
          if($(this).find('.widget').length == 0) {
            console.log('Adding empty');
            $(this).addClass('empty');
          } else {
            console.log('Remove empty');
            $(this).removeClass('empty');
          }
        });
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
  }
  setup_sortable('.row');
  $('#trash').droppable({
    hoverClass: 'hover',
    tolerance: 'touch',
    drop: function(evt, ui) {
      ui.draggable.remove();
    }
  });
  
  // Setup change tracking for widget options
  $('.widget .back input, .widget .back select').live('change', function() {
    var widget = $(this).parents('.widget').attr('id');
    changed.push(widget);
  });
  
  // Setup auto-reload for needed widgets
  var reload_interval = 30;
  $('.row div[data-reload]').each(function() {
    var time = parseInt($(this).attr('data-reload'), 10)
    $(this).data('reload', time).data('reload-orig', time);
  });
  function run_reload() {
    setTimeout(run_reload, reload_interval*1000);
    if(optionsMode)
      return;
    var to_reload = [];
    $('.row div[data-reload]').each(function() {
      var time_left = $(this).data('reload');
      time_left -= reload_interval;
      if(time_left <= 0) {
        time_left = $(this).data('reload-orig');
        var widget = $(this).attr('id').substring(7);
        to_reload.push(widget);
      }
      $(this).data('reload', time_left);
    });
    if(to_reload.length) {
      $.ajax({
        url: '/ajax/reload',
        dataType: 'json',
        data: {widgets:to_reload},
        cache: false,
        type: 'POST',
        success: function(data) {
          if(!data) {
            return;
          }
          $.each(data.output, function(k, v) {
            $('#widget_'+k).after(v).remove();
            $('#widget_'+k).trigger('statusboard-reload', [false]);
          });
        }
      });
    }
  }
  setTimeout(run_reload, reload_interval*1000);
});