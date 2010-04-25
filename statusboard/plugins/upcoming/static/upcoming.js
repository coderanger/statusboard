$(function() {
  $('.upcoming .title').wrapInner('<div class="title-inner"><span></span></div>').live('mouseenter', function() {
    var self = $(this).find('.title-inner');
    function scroll() {
      var new_margin = self.data('title-scroll-margin') + 1;
      if(new_margin >= self.find('span').width()) {
        new_margin = 0;
      }
      self.css('margin-left', '-'+new_margin+'px');
      self.data('title-scroll-margin', new_margin);
      self.data('title-scroll', setTimeout(scroll, 30));
    }
    self.data('title-scroll', setTimeout(scroll, 30)).data('title-scroll-margin', 0);
  }).live('mouseleave', function() {
    var inner = $(this).find('.title-inner').css('margin-left', '0');
    clearTimeout(inner.data('title-scroll'));
    inner.removeData('title-scroll').removeData('title-scroll-margin');
  });
});