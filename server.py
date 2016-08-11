#!/usr/bin/python

from mako.template import Template
from mako.lookup import TemplateLookup
from pyjade.ext.mako import preprocessor as mako_preprocessor

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import SimpleHTTPServer
import SocketServer
import os
import socket
import subprocess

PORT = 9080

def page(filename, content_type="text/html"):
    """ Creates an HTTP handler function that responds with the contents of a
    file (path is relative to this script) """
    mylookup = TemplateLookup(directories=['templates/', '.'], preprocessor=mako_preprocessor)

    def render(req):
        req.wfile.write(Template(filename='templates/' + filename, lookup=mylookup, preprocessor=mako_preprocessor).render())

    return render


def handler_fn(handler_fn, content_type="text/plain"):
    """ Creates an HTTP handler that responds with the return value of a
    function """

    def render(req):
        response = handler_fn(req)

        req.send_response(200)
        req.send_header('Content-type', content_type)
        req.end_headers()
        req.wfile.write(response)

    return render


def command_handler(command_with_args):
    """ Creates a handler that responds with the output of running the command
    throught POPEN """
    def handler(req):
        output = subprocess.check_output(command_with_args, stderr=subprocess.STDOUT)
        return output

    return handler_fn(handler)


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        sendReply = False

        if self.path not in HANDLER_MAP:
            filename = "static/" + self.path
            data = ""
            try:
                with open(filename, 'r') as f:
                    data=f.read()
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(data)
            except IOError:
                self.send_response(404)
            return


        # call the actual handler
        output_data = HANDLER_MAP[self.path](self)
        return

# Absolutely essential!  This ensures that socket resuse is setup BEFORE
# it is bound.  Will avoid the TIME_WAIT issue

class HTTPServer(SocketServer.TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


# ==================== Handlers ====================

HANDLER_MAP = {
        '/': page('index.jade'),
        '/control': page('control.jade'),
        '/start': command_handler(["sudo", "/usr/local/bin/insight-services", "start"]),
        '/stop' : command_handler(["sudo", "/usr/local/bin/insight-services", "stop"]),
        '/status' : command_handler(["sudo", "/usr/local/bin/insight-services", "status"]),
        # '/status' : command_handler(["sudo", "ls", "-ltr"]),
        }
# ==================== Handlers ====================

try:
    httpd = HTTPServer(("", PORT), RequestHandler)

    print "serving at port", PORT
    httpd.serve_forever()

except KeyboardInterrupt:
    print '^C received, shutting down the web server'
    httpd.socket.close()
