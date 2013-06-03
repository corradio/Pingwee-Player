function request_taglist() {
  ws.send(JSON.stringify(
    {
      message: 'list_tags',
      data: ''
    }
  ));
}

function tag_onClick(event){
  tag = event.data.Tag;
  ws.send(JSON.stringify(
    {
      message: 'list_tracks',
      data: {tag: tag}
    }
  ));
}

function track_onClickPlay(event){
  track = event.data.Track;
  ws.send(JSON.stringify(
    {
      message: 'play',
      data: {track: track}
    }
  ));
  return false;
}

function track_onClickEnqueue(event){
  track = event.data.Track;
  ws.send(JSON.stringify(
    {
      message: 'enqueue',
      data: {track: track}
    }
  ));
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

function player_onChanged(event){
  return;
}

function queue_onChanged(data){
  $('#playlist').text('');
  for (var i in data.Tracks) {
    $('#playlist').append("<div></div>");
    $('#playlist div:last').append(data.TrackInfos[i].artist + " - " + data.TrackInfos[i].title);
  }

  return false;
}

function taglist_onChanged(data){
  $('#tags').text('');
  for (var i in data.Tags) {
    $('#tags').append("<a href='#'>" + data.Tags[i] + "</a>");
    $('#tags a:last').click( {Tag:data.Tags[i]}, tag_onClick );
    $('#tags').append("<br>");
  }
}

function tracklist_onChanged(data){
  $('#tracks').text('');
  for (var i in data.Tracks) {
    $('#tracks').append("<div></div>");

    $('#tracks div:last').append("<a href='#'>Play</a> ");
    $('#tracks div:last a:last').click( {Track:data.Tracks[i]}, track_onClickPlay );

    $('#tracks div:last').append("<a href='#'>Enqueue</a> ");
    $('#tracks div:last a:last').click( {Track:data.Tracks[i]}, track_onClickEnqueue );

    $('#tracks div:last').append(data.TrackInfos[i].artist + " - " + data.TrackInfos[i].title);
  }
}

var ws;
var DEBUG = false;
$(window).bind("load", function() {
  // After page has loaded

  // Start the websocket
  ws = new WebSocket("ws://127.0.0.1:8080/websocket");
  ws.onopen = function() {
    // This is where we first truly are operational
    request_taglist();
    return;
  };
  ws.onclose = function() {
    console.log('ws closed!')
  }
  ws.onmessage = function (event) {
    if (DEBUG) {
      console.log('Raw message: ' + event.data);
    }
    obj = JSON.parse(event.data);
    message = obj.message;
    data = obj.data;

    if (message == "list_tags") {
      taglist_onChanged(data);

    } else if (message == "list_tracks") {
      tracklist_onChanged(data);

    } else if (message == "player_changed") {
      player_onChanged();

    } else if (message == "queue_changed") {
      queue_onChanged(data);
    }
  };

  // Do button bindings
  $('#stop').click(stop_onClick);
  $('#next').click(next_onClick);

});
