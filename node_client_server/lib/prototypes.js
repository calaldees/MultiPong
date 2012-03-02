var events = require('events');

Screen = module.exports.Screen = function Screen (c, screens) {
  var self = this;
  console.log('New Screen');
  this.c = c;
  this.state = 'handshaking';
  this.write({action: 'hello', value: 'node'});
  this.clients = [];
  setTimeout(function () {
    if (self.state !== 'handshaking') return;
    console.log('handshake timeout');
    self.c.end();
  }, 500);
  var buffer = '';

  // Our events
  this.on('left', function (object) {
    this.write({
      action: 'left',
      value: object.ipAddress,
      port: object.port
    });
  });
  this.on('right', function(object) {
    this.write({
      action: 'right',
      value: object.ipAddress,
      port: object.port
    });
  });

  // Process connection data
  function process_data(data) {
    console.log('data', self.state, data);
    switch (self.state) {
      case 'handshaking':
        if (data.action === 'hello' && data.value === 'screen') {
          self.ipAddress = c.remoteAddress;
          self.port = data.port || 5000;
          self.index = screens.length;
          self.write({action: 'ok', screen: self.index});
          screens[self.index] = self;
          if (self.index > 0) {
            self.emit('left', screens[self.index-1]);
            screens[self.index-1].emit('right', self);
          } 
          self.state = 'active';
        } else {
          console.log('invalid handshake', data);
          c.end();
        }
        break;
      case 'active':
        self.emit(data.action);
        break;
      default:
        console.log('unknown state');
    }
  }

  // Connection events
  c.on('data', function (data) {
    buffer += data;
    var index = buffer.indexOf('\n');
    if (index > -1) {
      var json = buffer.slice(0, index);
        try {
          json = JSON.parse(json);
        } catch (e) {
          console.log('JSON Error', json);
        }
        process_data(json);
      buffer = buffer.slice(index + 1);
/*      if (buffer.indexOf('\n') > -1) setTimeout(function () {
        c.emit('data', '');
      }, 100);
*/
    }
  });
  c.on('end', function () {
    self.state = 'disconnected';
    self.emit('end');
    console.log('End Screen');
  });
}
Screen.prototype = new events.EventEmitter();

Screen.prototype.write = function (object) {
  if (this.state !== 'disconnected' && this.c)
    this.c.write(
      JSON.stringify(object) + '\n'
    );
}
Screen.prototype.clientBegin = function (client) {
  this.write({
    action: 'clientBegin',
    value: client
  });
}
Screen.prototype.deltaX = function (client, delta) {
  this.write({
    action: 'deltaX',
    client: client,
    value: delta
  });
}
Screen.prototype.deltaY = function (client, delta) {
  this.write({
    action: 'deltaY',
    client: client,
    value: delta
  });
}
Screen.prototype.color = function (client, color) {
  this.write({
    action: 'color',
    value: color
  });
}
Screen.prototype.clientEnd = function (client) {
  this.write({
    action: 'clientEnd',
    value: client
  });
}

module.exports.Client = function Client (socket, screens) {
  var self = this;
  this.socket = socket;
  this.id = socket.id;
  this.state = 'handshake';
  socket.emit('hello');
  socket.on('screen', function (id) {
    if (self.state !== 'handshake') return socket.emit('error');
    var id = id * 1;
    if ((!screens[id]) || screens[id].state !== 'active') return socket.emit('error');
    self.screen = screens[id];
    self.screen.clients.push(self);
    self.state = 'active';
    self.screen.clientBegin(socket.id);
    socket.emit('begin');
  });
  socket.on('deltaX', function (delta) {
    console.log('deltaX', delta);
    if (self.state !== 'active') return socket.emit('error');
    self.screen.deltaX(socket.id, delta);
  });
  socket.on('deltaY', function (delta) {
    console.log('deltaY', delta);
    if (self.state !== 'active') return socket.emit('error');
    self.screen.deltaY(socket.id, delta);
  });
  socket.on('color', function (color) {
    console.log('color', color);
    if (self.state !== 'active') return socket.emit('error');
    self.screen.color(socket.id, color);
  });
  socket.on('disconnect', function () {
    if (self.screen) {
      self.screen.clientEnd(socket.id);
      var index = self.screen.clients.indexOf(self);
      if (index > -1)
        self.screen.clients.splice(index,1);
    }
  });
}
