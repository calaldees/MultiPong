
/**
 * Module dependencies.
 */

var express = require('express')
  , routes = require('./routes')
  , net = require('net')
  , protos = require('./lib/prototypes')
  , repl = require('repl');

var app = module.exports = express.createServer()
  , io = require('socket.io').listen(app);

io.set('log level', 1)

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

app.get('/screen/:id', function (req, res) {
  var id = req.params.id * 1;
  if ((!screens[id]) || screens[id].state !== 'active') return res.render('no_screen');
  res.render('screen', {screen: screens[id]});
});


io.sockets.on('connection', function (socket) {
  var client = new protos.Client(socket, screens);
});

app.listen(3000);
tcp_server.listen(4000);
console.log("Express server listening on port %d in %s mode", app.address().port, app.settings.env);

var c = repl.start().context

c.app = app;
c.screens = screens
