$(function() {
  function update() {
    var today = new Date();
    var h = today.getHours();
    if(h > 12) { h -= 12; }
    else if(h == 0) { h = 12; }
    var m = today.getMinutes();
    if(m < 10) { m = '0' + m; }
    $('.clock .time').html(h + ':' + m);
    setTimeout(update, 5000);
  }
  update();
});