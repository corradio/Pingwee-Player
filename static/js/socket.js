app.factory('socket', function ($rootScope) {

var handlers = {};
var onclose;
var onopen;
var socket;

  return {
    init: function() {
      socket = new WebSocket("ws://" + document.domain + ":8088/websocket");
      socket.onclose = function() {
        if (onclose !== undefined) {
          $rootScope.$apply(onclose());
        }
      };
      socket.onopen = function() {
        console.log('Connected');
        if (onopen !== undefined) {
          $rootScope.$apply(onopen());
        }
      };
      socket.onmessage = function (message) {
        var messageObj = JSON.parse(message.data);
        console.log("Received message: ", messageObj.message);
        handler = handlers[messageObj.message];
        if (handler === undefined) {
          console.log("Undefined handler for message " + messageObj.message);
        } else {
          // Let's run the handler inside the $rootScope.$apply wrapper so it notices changes
          $rootScope.$apply(handlers[messageObj.message](messageObj.data));
        }
      };
    },
    send: function(message, data) {
      console.log("Sending message: ", message);
      socket.send(JSON.stringify(
        {
          message: message,
          data: data
        }
      ));
    },
    on: function(message, callback) {
      handlers[message] = callback;
    },
    onclose: function(callback) {
      onclose = callback;
    },
    onopen: function(callback) {
      onopen = callback;
    }
  };
});