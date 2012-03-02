var events = require('events');

Screen = module.exports.Screen = function Screen (c, screens) {
  var self = this;
  console.log('New Screen');
  this.c = c;
  this.state = 'handshaking';
  c.write('"MultiPong NODE"\n');
  setTimeout(function () {
    if (self.state !== 'handshaking') return;
    console.log('handshake timeout');
    self.c.end();
  }, 500);
  var buffer = '';

  this.on('left', function (object) {
    c.write(JSON.stringify({
      action: 'left',
      ip: object.ipAddress
    }) + '\n');
  });
  this.on('right', function(object) {
    c.write(JSON.stringify({
      action: 'right',
      ip: object.ipAddress
    }) + '\n');
  });

  function process_data(data) {
    console.log('data', self.state, data);
    switch (self.state) {
      case 'handshaking':
        if (data === 'MultiPong SCREEN') {
          c.write('"MultiPong OK"\n');
          self.ipAddress = c.remoteAddress;
          self.index = screens.length;
          screens[self.index] = self;
          if (self.index > 0) {
            self.emit('left', screens[self.index-1]);
            screens[self.index-1].emit('right', self);
          } 
          self.state = 'active';
        } else {
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
  c.on('data', function (data) {
    buffer += data;
    var index = buffer.indexOf('\n');
    if (index > -1) {
      var json = buffer.slice(0, index);
        try {
          process_data(JSON.parse(json));
        } catch (e) {
          console.log('JSON Error');
        }
      buffer = buffer.slice(index + 1);
      if (buffer.indexOf('\n') > -1) setTimeout(function () {
        c.emit('data', '');
      }, 100);
    }
  });
  c.on('end', function () {
    self.emit('end');
    console.log('End Screen');
  });
}
Screen.prototype = new events.EventEmitter();

