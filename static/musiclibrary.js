function list_tags() {
  $.getJSON('list_tags', null, function(data){
    for (var i in data.Tags) {
      $('#tags').append("<a href='#'>" + data.Tags[i] + "</a>");
      $('#tags a:last').click( {Tag:data.Tags[i]}, tag_onClick );
      $('#tags').append("<br>");
    }
  });
}

function tag_onClick(event){
  tag = event.data.Tag;
  $('#tracks').text('');
  $.getJSON('list_tracks', {tag:tag}, function(data){
    for (var i in data.Tracks) {
      $('#tracks').append("<a href='#'>" + data.Tracks[i] + "</a>");
      $('#tracks a:last').click( {Track:data.Tracks[i]}, track_onClick );
      $('#tracks').append("<br>");
    }
  });
}

function track_onClick(event){
  track = event.data.Track;
  $.getJSON('play', {track:track}, function(data){});
}

function stop_onClick(event){
  $.getJSON('stop', null, function(data){});
}

$(window).bind("load", function() {
   // After page has loaded

   // Do button bindings
   $('#stop').click(stop_onClick);

   // Populate data
   list_tags();
});
