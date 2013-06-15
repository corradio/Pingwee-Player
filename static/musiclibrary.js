var ws;
var DEBUG = true;
var queue;
var taglist;
var edittags_selected_track_index = 0;

function edittags_tag_onClick(event) {
  var tag = event.data.Tag;
  var checked = $(this).is(':checked');
  if (checked) {
    // Add the tag
    ws.send(JSON.stringify(
      {
        message: 'tag_track',
        data: {
          tag: tag,
          track: queue.Tracks[edittags_selected_track_index]
        }
      }
    ));
  } else {
    // Remove the tag
    ws.send(JSON.stringify(
      {
        message: 'untag_track',
        data: {
          tag: tag,
          track: queue.Tracks[edittags_selected_track_index]
        }
      }
    ));
  }
}

function request_taglist() {
  ws.send(JSON.stringify(
    {
      message: 'list_tags',
      data: ''
    }
  ));
}

function request_queue() {
  ws.send(JSON.stringify(
    {
      message: 'list_queue',
      data: ''
    }
  ));
}

function next_onClick(event){
  ws.send(JSON.stringify(
    {
      message: 'next'
    }
  ));
  return false;
}

function stop_onClick(event){
  ws.send(JSON.stringify(
    {
      message: 'stop',
      data: {track: track}
    }
  ));
  return false;
}

function tag_onClick(event){
  tag = event.data.Tag;
  ws.send(JSON.stringify(
    {
      message: 'list_tracks',
      data: {tag: tag}
    }
  ));
  return false;
}

function tag_onClickPlay(event){
  tag = event.data.Tag;
  ws.send(JSON.stringify(
    {
      message: 'play_tag',
      data: {tag: tag}
    }
  ));
  return false;
}

function taglist_onChanged(data){
  taglist = data.Tags;

  $('#tags').text('');
  $('#tracks').text('');
  for (var i in taglist) {
    $('#tags').append("<a href='#'>" + taglist[i] + "</a>");
    $('#tags a:last').click( {Tag:taglist[i]}, tag_onClick );
    $('#tags').append("&nbsp;<a href='#'>Play</a>");
    $('#tags a:last').click( {Tag:taglist[i]}, tag_onClickPlay );
    $('#tags').append("<br>");
  }

  $('#edittags').text('');
  $('#edittags').append("Track:&nbsp;<span id='trackname'></span><br>");
  for (var i in taglist) {
    tag = taglist[i];
    if (tag[0] != '!') {
      $('#edittags').append("<input type='checkbox' name='" + tag + "'>" + tag + "</input><br>");
      $('#edittags input:last').click( {Tag:tag}, edittags_tag_onClick );
    }
  }
  $('#edittags').append("<br>");
  $('#edittags').append("<input type='text' name='newtag'></input>&nbsp;<input type='button' value='Add'>");
  $("#edittags input[type='button']").click( function () {
    newtag = $("#edittags input[name='newtag']").val();
    ws.send(JSON.stringify(
      {
        message: 'tag_track',
        data: {
          tag: newtag,
          track: queue.Tracks[edittags_selected_track_index]
        }
      }
    ));
  });
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

function track_onClickPlay(event){
  var track = event.data.Track;
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

function player_onChanged(event){
  return;
}

function queue_onChanged(data){
  queue = data;
  $('#playlist').text('');
  for (var i in queue.Tracks) {
    $('#playlist').append("<div></div>");
    $('#playlist div:last').append("<a href='#'>" + queue.TrackInfos[i].artist + " - " + queue.TrackInfos[i].title + "</a>");
    $('#playlist div:last a:last').click( {Track:queue.Tracks[i], queue_position:i}, queue_track_onClick );
  }
  if (queue.Tracks.length > 0) {
    queue_track_onClick({data: {Track:queue.Tracks[edittags_selected_track_index], queue_position:edittags_selected_track_index} });
  }

  return false;
}

function queue_track_onClick(event) {
  queue_position = event.data.queue_position;
  checkboxes = $("#edittags input[type='checkbox']");
  checkboxes.prop('checked', false);

  for (var i in queue.TrackInfos[queue_position].tags) {
    tag = queue.TrackInfos[queue_position].tags[i];
    $("#edittags input[type='checkbox'][name='" + tag + "']").prop('checked', true);
  }

  $("#edittags #trackname").text(queue.TrackInfos[queue_position].artist + ' - ' + queue.TrackInfos[queue_position].title);

  edittags_selected_track_index = queue_position;

  return false;
}

function init_connection() {
  if (ws != undefined) {
    ws.onopen = function() {alert('wtf it reopened!');};
    ws.onclose = function() {alert('wtf it reclosed!');};
  }
  ws = new WebSocket("ws://" + document.domain + ":8088/websocket");
  ws.onclose = function() {
    console.log('Connection lost');
    setTimeout(init_connection, 5000);
  };

  ws.onopen = function() {
    // This is where we first are fully operational, or back from offline mode
    request_taglist();
    request_queue();
    return;
  };

  ws.onmessage = function (event) {
    if (DEBUG) {
      console.log('Received raw message: ' + event.data);
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

  return ws;
}

$(window).bind("load", function() {
  // After page has loaded

  // Start the websocket
  ws = init_connection();

  // Do button bindings
  $('#stop').click(stop_onClick);
  $('#next').click(next_onClick);

});
