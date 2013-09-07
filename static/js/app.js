var app = angular.module('musikApp', []);

function MainController($scope, socket, keyboardManager) {

  // Default values
  $scope.player_state = 'stop';
  $scope.selected_track_index = 0;
  $scope.tracks = [];
  $scope.scan_state = "";

  // Model definition with default values
  $scope.currentlyplaying = {}
  $scope.currentlyplaying['cover'] = undefined
  $scope.currentlyplaying['index'] = undefined

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
    if ($scope.selected_track_index > 0) {
      $scope.selected_track_index -= 1;
      queue_track_onSelected($scope.selected_track_index);
    }
  });
  keyboardManager.bind('down', function() {
    if ($scope.selected_track_index + 1 < $scope.tracks.length) {
      $scope.selected_track_index += 1;
      queue_track_onSelected($scope.selected_track_index);
    }
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
    $scope.selected_track_index = $scope.currentlyplaying.index;
    queue_track_onSelected($scope.currentlyplaying.index);
  });

  // Add sway.fm/api support for media keys
  var unity = UnityMusicShim();
  unity.setSupports({
    playpause: true,
    next: true,
    previous: true,
    favorite: false
  });

  unity.setCallbackObject({
    pause: function() {
      console.log("Received playpause command");
      //yourPlayer.pause();
      socket.send('play_pause_toogle', '');
    },
    next: function() {
      console.log("Received next command")
      //yourPlayer.skip();
      socket.send('next', '');
    },
    previous:function() {
      console.log("Received previous command");
      //yourPlayer.previous();
      socket.send('previous', '');
    }
  });

  var playerState = {
    playing: true,
    title: "Song Title",
    artist: "Artist Name",
    albumArt: "http://yoursite.com/path/to/public/image.png",
  }
  unity.sendState(playerState);
  /*var playerState = {
    playing: false
  }
  unity.sendState(playerState);*/

  // Ideas for the API
  $scope.player = {}
  $scope.player['play'] = function() {console.log('called');};
  $scope.player.play();

  $scope.player['play_tag'] = function(index) {
    socket.send('play_tag',
      {
        'tag': $scope.tags[index],
        'shuffle': 1
      }
    );
  };

  $scope.player['scan_library'] = function() {
    socket.send('scan_library', '');
  };
  $scope.player['burn_cd'] = function() {
    socket.send('burn_cd', '');
  };
  // This can be put in a Player() constructor


  // Events
  socket.on('describe_player_state', function(data) {
    $scope.player_state = data.state;
  });
  socket.on('get_coverart', function(data) {
    if ($scope.trackIDs[$scope.currentlyplaying.index] == data.Track) {
      $scope.currentlyplaying.cover = data.data
    }
    if ($scope.trackIDs[$scope.selected_track_index] == data.Track) {
      $scope.coverdata = data.data;
    }
  });
  socket.on('queue_changed', function(data) {
    $scope.tracks = data.TrackInfos;
    $scope.trackIDs = data.Tracks;
    $scope.currentlyplaying.index = data.QueueIndexOfCurrentlyPlaying;
    queue_track_onSelected($scope.selected_track_index);
  });
  socket.on('player_changed', function(data) {
    if (data.State !== undefined) {
      $scope.player_state = data.State;
    }
    if (data.QueueIndexOfCurrentlyPlaying !== undefined && $scope.currentlyplaying.index != data.QueueIndexOfCurrentlyPlaying) {
      $scope.currentlyplaying.index = data.QueueIndexOfCurrentlyPlaying;
      socket.send('get_coverart',
      {
        'QueueIndex': $scope.currentlyplaying.index
      }
    );
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
  socket.on('scan_library_started', function(data) {
    $scope.scan_state = ' (scanning)';
  })
  socket.on('scan_library_finished', function(data) {
    $scope.scan_state = '';
  })

  // Update events
  function queue_track_onSelected(index) {
    // Use a HashMap here to be able to reference quickly...
    if ($scope.tags === undefined || $scope.tracks.length == 0 || $scope.tracks[index] === undefined) { return; }
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

  // Add UI event listeners
  var cov = document.getElementById('cover');

  cov.addEventListener('dragenter', function(e) {
      cov.classList.add('over');
      e.stopPropagation();
      e.preventDefault();
    },
    false
  );
  cov.addEventListener('dragleave', function(e) {
      cov.classList.remove('over');
      e.stopPropagation();
      e.preventDefault();
    },
    false
  );
  cov.addEventListener('dragover', function(e) {
      e.stopPropagation();
      e.preventDefault();
    },
    false
  );
  cov.addEventListener('drop', function(e) {
      //console.log(e.dataTransfer.files);
      data = e.dataTransfer.items[0];
      if (data.type == "text/uri-list") {
        console.log('Setting cover to dropped URL');
        data.getAsString( function(url){
          socket.send('set_track_coverart',
            {
              track: $scope.trackIDs[$scope.selected_track_index],
              url: url
            }
          );
        });
      } else {
        console.log('Type ' + data.type + ' is not supported');
      }

      cov.classList.remove('over');
      e.stopPropagation();
      e.preventDefault();
    },
    false
  );

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