#!/usr/bin/python

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import SimpleHTTPServer
import SocketServer
import os
import socket
import subprocess

PORT = 9080

# ==================== Monkey Patching ====================

# from http://pydoc.net/Python/pep8radius/0.9.0/pep8radius.shell/
# monkey-patch subprocess for python 2.6 to give feature parity with later versions.
try:
    from subprocess import STDOUT, check_output, CalledProcessError
except ImportError:  # pragma: no cover
    # python 2.6 doesn't include check_output
    # monkey patch it in!
    import subprocess
    STDOUT = subprocess.STDOUT

    def check_output(*popenargs, **kwargs):
        if 'stdout' in kwargs:  # pragma: no cover
            raise ValueError('stdout argument not allowed, '
                             'it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE,
                                   *popenargs, **kwargs)
        output, _ = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd,
                                                output=output)
        return output
    subprocess.check_output = check_output

    # overwrite CalledProcessError due to `output`
    # keyword not being available (in 2.6)
    class CalledProcessError(Exception):

        def __init__(self, returncode, cmd, output=None):
            self.returncode = returncode
            self.cmd = cmd
            self.output = output

        def __str__(self):
            return "Command '%s' returned non-zero exit status %d" % (
                self.cmd, self.returncode)
    subprocess.CalledProcessError = CalledProcessError

# ==================== Helpers ====================

def page(filename, content_type="text/html"):
    """ Creates an HTTP handler function that responds with the contents of a
    file (path is relative to this script) """
    base_path = os.path.dirname(os.path.abspath(__file__))
    data = ""
    with open(os.path.join(base_path, filename), 'r') as f:
        data=f.read()

    def render(req):
        req.send_response(200)
        req.send_header('Content-type',content_type)
        req.end_headers()
        req.wfile.write(data)

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
        return subprocess.check_output(command_with_args, stderr=subprocess.STDOUT)

    return handler_fn(handler)


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        sendReply = False

        if self.path not in HANDLER_MAP:
            self.send_response(404)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write("Cannot find path: '{0}'".format(self.path))
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
        '/': page('index.html'),
        '/start': command_handler(["sudo", "/usr/local/bin/insight-services", "start"]),
        '/stop' : command_handler(["sudo", "/usr/local/bin/insight-services", "stop"]),
        '/status' : command_handler(["sudo", "/usr/local/bin/insight-services", "status"]),
        }

# HANDLER_MAP = {
        # '/': page('index.html'),
        # '/start': command_handler(["ls", "-la", "/tmp"]),
        # '/stop' : command_handler(["ls", "-la", "/etc"]),
        # '/status' : command_handler(["ls", "-la", "/proc"]),
        # }

# ==================== Handlers ====================



try:
    httpd = HTTPServer(("", PORT), RequestHandler)

    print "serving at port", PORT
    httpd.serve_forever()

except KeyboardInterrupt:
    print '^C received, shutting down the web server'
    httpd.socket.close()
