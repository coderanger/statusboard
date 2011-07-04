$(function() {
  $('.jenkins').live('statusboard-reload', function() {
    $(this).find('.progress').cluetip({
      cluetipClass: 'jtip', 
      attribute: 'data-timing-url',
      width: 450,
      showTitle: false,
      ajaxCache: false,
    });
  }).trigger('statusboard-reload');
});
