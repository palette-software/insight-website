#!/usr/bin/python

from mako.template import Template
from mako.lookup import TemplateLookup
from pyjade.ext.mako import preprocessor as mako_preprocessor

from http.server import BaseHTTPRequestHandler,HTTPServer
import http.server
import socketserver
import os
import socket
import subprocess
import json
import re

PORT = 9080
BASEDIR = "/tmp"

def page(filename, content_type="text/html"):
    """ Creates an HTTP handler function that responds with the contents of a
    file (path is relative to this script) """
    mylookup = TemplateLookup(directories=['/'], preprocessor=mako_preprocessor)

    def render(req):
        status_dict = get_status()
        req.wfile.write(str.encode(Template(filename=BASEDIR + '/templates/' + filename, lookup=mylookup, preprocessor=mako_preprocessor).render(status=status_dict)))

    return render


def handler_fn(handler_fn, content_type="text/plain"):
    """ Creates an HTTP handler that responds with the return value of a
    function """

    def render(req):
        response = handler_fn(req)

        req.send_response(200)
        req.send_header('Content-type', content_type)
        req.end_headers()
        if response:
            req.wfile.write(response)

    return render

def get_dummy_subprocess_output():
    with open('sample.txt', 'r') as myfile:
        data = myfile.read()
        return data


def get_status():
    if 'DEBUG' not in os.environ:
        try:
            status = subprocess.check_output(["sudo", "/usr/local/bin/insight-services", "status"], stderr=subprocess.STDOUT)
            status = status.decode()
        except Exception:
            status = "{}"
    else:
        status = get_dummy_subprocess_output()
    status_json = parse_status(status)
    return status_json


def status_handler():
    """ Creates a handler that responds with the output of running the command
    throught POPEN """
    def handler(req):
        get_status()

    return handler_fn(handler)

def service_status(service_name, raw_status_message):
    match = re.search(service_name + "\s+(\w+)\s+pid\s(\d+), uptime.+?(\d+:\d+:\d+)", raw_status_message)
    status = {}
    if match:
        status['active'] = match.group(1) == 'RUNNING'
        status['pid'] = match.group(2)
        status['uptime'] = match.group(3)
    else:
        status['active'] = False
    status["show_detail"] = True
    return status

def parse_status(status):
    data = {}
    data["greenplum"] = {}
    data['greenplum']['show_detail'] = True
    data['greenplum']['display_name'] = "Palette Insight Repository"
    match = re.search("local Greenplum Version: 'postgres \(Greenplum Database\) (.+?)'", status)
    if match:
        data['greenplum']['local-greenplum-version'] = match.group(1)

    match = re.search("master Greenplum Version: '(.+?\s.+?) .*'", status)
    if match:
        data['greenplum']['master-greenplum-version'] = match.group(1)

    match = re.search("Master instance\s+=\s(.+)", status)
    if match:
        data['greenplum']['active'] = match.group(1) == 'Active'
    else:
        data['greenplum']['active'] = False

    match = re.search("Total segment instance count from metadata.*(\d+)", status)
    if match:
        data['greenplum']['segments-from-metadata'] = match.group(1)

    match = re.search("Total primary segments.*(\d+)", status)
    if match:
        data['greenplum']['total-primary-segments'] = match.group(1)

    match = re.search("Total primary segment valid \(at master\).*(\d+)", status)
    if match:
        data['greenplum']['valid-primary-segments'] = match.group(1)

    match = re.search("Total primary segment failures \(at master\).*(\d+)", status)
    if match:
        data['greenplum']['primary-segment-failures'] = match.group(1)

    data['gpfdist'] = service_status("insight-gpfdist", status)
    data['gpfdist']['display_name'] = "Palette Insight Load"
    data['status-page'] = service_status("insight-services-webui", status)
    data['status-page']['display_name'] = "Palette Insight Website"
    data['palette-insight-server'] = {}
    data['palette-insight-server'] = service_status("palette-insight-server", status)
    data['palette-insight-server']['display_name'] = "Palette Insight Web Service"

    match = re.search("palette-insight-server-(\d+\.\d+\.\d+).*", status)
    if match:
        data['palette-insight-server']['version'] = match.group(1)


    data['datamodel'] = {}
    data['datamodel']['show_detail'] = False
    data['datamodel']['load_tables'] = {}
    data['datamodel']['reporting'] = {}
    # We are matching on an optional # for commenting out the jobs
    #   and after a cron timing definition (for example 5-55/5 * * * * )
    #   and afterwards the name of the job
    match = re.search("(.*?([^\s]+\s){5}/opt/palette-insight-talend/load_tables.sh)", status)
    if match:
        # Search for the # in the beginning
        data['datamodel']['load_tables']['active'] = match and not re.search("\#", match.group(1))
    else:
        data['datamodel']['load_tables']['active'] = False

    match = re.search("palette-insight-loadtables-(\d+\.\d+\.\d+).*", status)
    if match:
        data['datamodel']['load_tables']['version'] = match.group(1)

    match = re.search("(.*?([^\s]+\s){5}/home/insight/loadctrl.sh)", status)
    if match:
        data['datamodel']['reporting']['active'] = match and not re.search("\#", match.group(1))
    else:
        data['datamodel']['reporting']['active'] = False

    match = re.search("palette-insight-reporting-(\d+\.\d+\.\d+).*", status)
    if match:
        data['datamodel']['reporting']['version'] = match.group(1)

    return data


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
            filename = BASEDIR + "/static/" + self.path
            data = ""
            try:
                with open(filename, 'rb') as f:
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

class HTTPServer(socketserver.TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


# ==================== Handlers ====================

HANDLER_MAP = {
        '/': page('index.jade'),
        '/control': page('control.jade'),
        '/status' : status_handler(),
        }
# ==================== Handlers ====================

try:
    BASEDIR = os.path.dirname(os.path.abspath(__file__))
    httpd = HTTPServer(("", PORT), RequestHandler)

    print("serving at port", PORT)
    httpd.serve_forever()

except KeyboardInterrupt:
    print('^C received, shutting down the web server')
    httpd.socket.close()
