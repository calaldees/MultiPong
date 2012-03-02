$(function () {
  var color_values = ['red', 'green', 'blue', 'orange'];
  var status = $('#status');
  var debug = $('#debug');
  var area = $('#area');
  var colors = $('#colors');
  var socket = io.connect();
  var joystick = new VirtualJoystick({
    container: $('#control')[0],
    mouseSupport: true,
    range: 10
  });
  var interval = null;
  var prevY = 0;
  var prevX = 0;
  var maxD = 100;

  function applyMax(delta) {
    var sign = delta < 0 ? -1 : 1;
    var abs = Math.abs(delta);
    return (sign * (abs > maxD ? maxD : abs));
  }

  function updateInterval() {
    var deltaY = applyMax(joystick.deltaY());
    var deltaX = applyMax(joystick.deltaX());
    
    var dText = 'X: ' + deltaX;
    if (prevX !== deltaX) {
      socket.emit('deltaX', deltaX);
      dText += ' changed';
    }

    dText += '<br />Y: ' + deltaY;
    if (prevY !== deltaY) {
      socket.emit('deltaY', deltaY);
      dText += 'changed';
    }
    debug.html(dText);
    prevX = deltaX;
    prevY = deltaY;
  }

  socket.on('hello', function () {
    socket.emit('screen', status.data('screen'));
    status.text('Connected, please wait...');
  });

  socket.on('begin', function () {
    status.text('Go!');
    interval = setInterval(updateInterval, 100);
  });

  socket.on('end', function () {
    status.text('Game Over');
    clearInterval(interval);
    interval = null;
  });
  
  for (var i in color_values) {
    var color_value = color_values[i];
    var color = $('<td />').append('&nbsp;').css('background-color', color_value);
    colors.append(color);
  }
  colors.on('click', 'td', function () {
    var color = $(this).css('background-color');
    area.css('background-color', color);
    socket.emit('color', color);
  });
});
