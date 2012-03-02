
/**
 * Module dependencies.
 */

var express = require('express')
  , routes = require('./routes')
  , net = require('net')
  , protos = require('./lib/prototypes');

var app = module.exports = express.createServer()
  , io = require('socket.io').listen(app);

// Configuration
var screens = [];

var tcp_server = net.createServer(function (c) {
  c.setEncoding('utf8');
  var screen = new protos.Screen(c, screens);
});

app.configure(function(){
  app.set('views', __dirname + '/views');
  app.set('view engine', 'ejs');
  app.use(express.bodyParser());
  app.use(express.methodOverride());
  app.use(app.router);
  app.use(express.static(__dirname + '/public'));
});

app.configure('development', function(){
  app.use(express.errorHandler({ dumpExceptions: true, showStack: true }));
});

app.configure('production', function(){
  app.use(express.errorHandler());
});

// Routes

app.get('/', function (req, res) {
  if (screens.length === 0) return res.render('no_screens');
  for (var i in screens) {
    if (screens[i].state != 'active') return res.render('waiting');
  }
  res.render('index', {screens: screens});
});

app.listen(3000);
tcp_server.listen(4000);
console.log("Express server listening on port %d in %s mode", app.address().port, app.settings.env);
