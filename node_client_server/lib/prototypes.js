var events = require('events');

Screen = module.exports.Screen = function Screen (c, screens) {
  var self = this;
  console.log('New Screen');
  this.c = c;
  this.state = 'handshaking';
  this.write({action: 'hello', value: 'node'});
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
      value: object.ipAddress
    });
  });
  this.on('right', function(object) {
    this.write({
      action: 'right',
      value: object.ipAddress
    });
  });

  // Process connection data
  function process_data(data) {
    console.log('data', self.state, data);
    switch (self.state) {
      case 'handshaking':
        if (data.action === 'hello' && data.value === 'screen') {
          self.ipAddress = c.remoteAddress;
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
Screen.prototype.delta = function (client, delta) {
  this.write({
    action: 'delta',
    client: client,
    value: delta
  });
}
Screen.prototype.clientEnd = function (client) {
  this.write({
    action: 'clientEnd',
    value: client
  });
}

