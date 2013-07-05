var app = angular.module('musikApp', []);

function MainController($scope, socket, keyboardManager) {

  // Default values
  $scope.player_state = 'stop';
  $scope.selected_track_index = 0;
  $scope.tracks = [];

  // Socket handlers
  socket.onclose(function() {
    console.log('Connection lost.. will retry in 5seconds');
    setTimeout(
      function() {
        console.log('Retrying');
        $scope.$apply(socket.init);
      },
      5000);
  });
  socket.onopen(function() {
    socket.send('list_tags', '');
    socket.send('list_queue', '');
    socket.send('list_queue', '');
  });

  // Declare key bindings
  keyboardManager.bind('space', function() {
    socket.send('play_pause_toogle', '');
  });
  keyboardManager.bind('up', function() {
    $scope.selected_track_index = Math.max($scope.selected_track_index - 1, 0);
    queue_track_onSelected($scope.selected_track_index);
  });
  keyboardManager.bind('down', function() {
    $scope.selected_track_index = Math.min($scope.selected_track_index + 1, $scope.tracks.length - 1);
    queue_track_onSelected($scope.selected_track_index);
  });
  keyboardManager.bind('enter', function() {
    socket.send('play', {'QueueIndex': $scope.selected_track_index});
  });
  keyboardManager.bind('backspace', function() {
    socket.send('remove_from_queue', {'QueueIndex': $scope.selected_track_index});
  });
  keyboardManager.bind('shift+backspace', function() {
    socket.send('delete', {'QueueIndex': $scope.selected_track_index});
  });
  keyboardManager.bind('ctrl+L', function() {
    $scope.selected_track_index = $scope.currently_playing;
    queue_track_onSelected($scope.selected_track_index);
  });

  // Events
  socket.on('get_coverart', function(data) {
    $scope.coverdata = "data:image/png;base64," + data.data;
  });
  socket.on('queue_changed', function(data) {
    $scope.tracks = data.TrackInfos;
    $scope.trackIDs = data.Tracks;
    queue_track_onSelected($scope.selected_track_index);
  });
  socket.on('player_changed', function(data) {
    if (data.State !== undefined) {
      $scope.player_state = data.State;
    }
    if (data.QueueIndexOfCurrentlyPlaying !== undefined) {
      $scope.currently_playing = data.QueueIndexOfCurrentlyPlaying;
    }
  });
  socket.on('list_tags', function(data) {
    $scope.tags = data.Tags;

    $scope.selectedtrack_taglist = [];
    for (var i=0; i<$scope.tags.length; i++) {
      // The double binding can be watched through $watch('var', fun, true)
      // but it does not tell which one of the items was changed
      // unless we watch() all of them?
      $scope.selectedtrack_taglist[i] = {
        'name': $scope.tags[i],
        'checked': false,
        'is_special': $scope.tags[i][0] == '!',
        'onClick': function(event, index) {
          var tag = $scope.selectedtrack_taglist[index];
          socket.send(tag.checked ? 'tag_track':'untag_track',
            {
              tag: tag.name,
              track: $scope.trackIDs[$scope.selected_track_index]
            }
          );
        }
      };
    }

    queue_track_onSelected($scope.selected_track_index);
  });

  // Update events
  function queue_track_onSelected(index) {
    // Use a HashMap here to be able to reference quickly...
    if ($scope.tags === undefined || $scope.tracks.length == 0) { return; }
    var found = false;
    for (var i=0; i<$scope.tags.length; i++) {
      found = false;
      if ($scope.tracks[index].tags === undefined) {
        // No tags defined
        found = false;
      } else {
        for (var j=0; j<$scope.tracks[index].tags.length; j++) {
          if ($scope.tracks[index].tags[j] == $scope.tags[i]) {
            found = true;
          }
        }
      }
      $scope.selectedtrack_taglist[i].checked = found;
    }

    // Update cover
    socket.send('get_coverart',
      {
        'QueueIndex': $scope.selected_track_index
      }
    );

    // Update raw data
    $scope.trackrawdata = $scope.tracks[$scope.selected_track_index];
    $scope.trackrawdata['ID'] = $scope.trackIDs[$scope.selected_track_index];
  }

  $scope.tag_onAdd = function() {
    socket.send('tag_track',
      {
        tag: $scope.newtag,
        track: $scope.trackIDs[$scope.selected_track_index]
      }
    );
    $scope.newtag = '';
  }

  /*$scope.$watch('selectedtrack_taglist', function(newval, oldval) {
    for (var i=0; i<$newval.length; i++) {
      if (newval.checked != oldval.checked) {
        // Item was checked or unchecked
      }
    }
    //console.log(newval.selected);
    console.log('changed');
    console.log(newval);
  }, true);*/

  // Start the sockets!
  socket.init();
}

app.directive('backImg', function(){
    return function(scope, element, attrs){
        attrs.$observe('backImg', function(value) {
            element.css({
                'background-image': 'url(' + value +')'
            });
        });
    };
});