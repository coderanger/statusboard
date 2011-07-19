$(function() {
  $(document).delegate('.jenkins', 'statusboard-reload', function() {
    $(this).find('.progress').cluetip({
      cluetipClass: 'jtip', 
      attribute: 'data-timing-url',
      width: 450,
      showTitle: false,
      ajaxCache: false,
    });
  }).delegate('.jenkins select[id$=_server_url]', 'change', function() {
    var server_url_elm = $(this);
    var job_elm = server_url_elm.siblings('select[id$=_job]');
    console.log(server_url_elm.val());
    if(!server_url_elm.val()) return;
    $.ajax({
      'url': job_elm.data('jobs-url'),
      'data': {'server_url': server_url_elm.val()},
      'dataType': 'json',
      'type': 'GET',
      'success': function(data) {
        var options = ['<option value="">'+data.label+'</option>'];
        $.each(data.jobs, function(i, job) {
          options.push('<option value="'+job.id+'">'+job.name+'</option>');
        });
        job_elm.html(options.join('')).val('');
      }
    });
  });
});
