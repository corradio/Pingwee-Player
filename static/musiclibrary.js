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
      $('#tracks').append("<div></div>");

      $('#tracks div:last').append("<a href='#'>Play</a> ");
      $('#tracks div:last a:last').click( {Track:data.Tracks[i]}, track_onClickPlay );

      $('#tracks div:last').append("<a href='#'>Enqueue</a> ");
      $('#tracks div:last a:last').click( {Track:data.Tracks[i]}, track_onClickEnqueue );

      $('#tracks div:last').append(data.TrackInfos[i].artist + " - " + data.TrackInfos[i].title);
    }
  });

  return false;
}

function track_onClickPlay(event){
  track = event.data.Track;
  $.getJSON('play', {track:track}, function(data){});
  return false;
}

function track_onClickEnqueue(event){
  track = event.data.Track;
  $.getJSON('enqueue', {track:track}, function(data){});
  return false;
}

function stop_onClick(event){
  $.getJSON('stop', null, function(data){});
  return false;
}

function next_onClick(event){
  $.getJSON('next', null, function(data){});
  return false;
}

function queue_onChanged(event){
  $.getJSON('list_queue', null, function(data){
    for (var i in data.Tracks) {
      $('#queue').append("<div></div>");

      //$('#queue div:last').append("<a href='#'>Play</a> ");
      //$('#queue div:last a:last').click( {Track:data.Tracks[i]}, track_onClickPlay );

      $('#queue div:last').append(data.TrackInfos[i].artist + " - " + data.TrackInfos[i].title);
    }
  });
  return false;
}

var ws;
$(window).bind("load", function() {
  // After page has loaded

  // Listen for events
  ws = new WebSocket("ws://127.0.0.1:8080/websocket");
  ws.onopen = function() {
     ws.send("idle");
  };
  ws.onmessage = function (event) {
    message = event.data;
    console.log(message);
    console.log('bring this abstraction on the server. Here we should just call queue_changed event')
    if (message == "playlist") {
      playlist_onChanged();
    }
  };

  // Do button bindings
  $('#stop').click(stop_onClick);
  $('#next').click(next_onClick);

   // Populate data
   list_tags();
});
