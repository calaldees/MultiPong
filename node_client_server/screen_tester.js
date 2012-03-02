var net = require('net');

var c = net.createConnection(4000, function () {
  c.setEncoding('utf8');
  var state = 'handshaking';
  function process_data(data) {
    console.log('data', data);
    switch (state) {
      case 'handshaking':
        if (data !== 'MultiPong NODE') return c.end();
        console.log('handshaking -> waiting');
        c.write(JSON.stringify('MultiPong SCREEN') + '\n');
        state = 'waiting';
        break;
      case 'waiting':
        if (data !== 'MultiPong OK') return c.end();
        console.log('waiting -> active');
        state = 'active';
        break;
      default:
        console.log('active');
    }
  }
  var buffer = ''
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
})
