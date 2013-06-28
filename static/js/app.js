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
    socket.send('play', {'index': $scope.selected_track_index});
  });
  keyboardManager.bind('backspace', function() {
    socket.send('remove_from_queue', {'index': $scope.selected_track_index});
  });

  // Events
  socket.on('queue_changed', function(data) {
    $scope.tracks = data.TrackInfos;
    $scope.currently_playing = data.CurrentlyPlaying;
  });
  socket.on('player_changed', function(data) {
    $scope.player_state = data.State;
    $scope.currently_playing = data.CurrentlyPlaying;
  });
  socket.on('list_tags', function(data) {
    $scope.tags = data.Tags;

    $scope.tracktags = [];
    for (var i=0; i<$scope.tags.length; i++) {
      $scope.tracktags[i] = {'name': $scope.tags[i], 'checked': 0};
    }
  });

  // Update events
  function queue_track_onSelected(index) {
    // Use a HashMap here to be able to reference quickly...
    // Also check for double bindings here
    for (var i=0; i<$scope.tags.length; i++) {
      $scope.tracktags[i].checked = 0;
    }

  }

  // Start the sockets!
  socket.init();
}