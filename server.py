#!/usr/bin/python

from mako.template import Template
from mako.lookup import TemplateLookup
from pyjade.ext.mako import preprocessor as mako_preprocessor

from http.server import BaseHTTPRequestHandler,HTTPServer
import http.server

import socket
import socketserver
from socketserver import ThreadingMixIn

import os
import subprocess
import json
import re

PORT = 9080
BASEDIR = "/tmp"
TEMPLATE_LOOKUP = TemplateLookup(directories=['/'], preprocessor=mako_preprocessor)

# The following class helps development as TCP socket
# is not closed for a long time (about a minute) after server is stopped.
class HTTPServer(socketserver.TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

class ThreadingServer(ThreadingMixIn, HTTPServer):
    pass

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


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == '/':
                status_dict = get_status()
                respond_html(self,
                    Template(filename=BASEDIR + '/templates/index.jade',
                        lookup=TEMPLATE_LOOKUP, preprocessor=mako_preprocessor,
                        module_directory="/tmp/mako_modules").render(status=status_dict))
            elif self.path == '/control':
                respond_html(self,
                    Template(filename=BASEDIR + '/templates/control.jade',
                        lookup=TEMPLATE_LOOKUP, preprocessor=mako_preprocessor,
                        module_directory="/tmp/mako_modules").render())
            elif self.path == '/control/update':
                output = subprocess.run(["/opt/insight-toolkit/update.sh"])
                if output != 0:
                    respond_error(self)
                else:
                    respond_html(self, "")
            elif self.path == '/control/update/progress':
                with subprocess.Popen(["tail","-1","/var/log/insight-services/progress.log"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL) as proc:
                    respond_json(self, {'line': proc.stdout.read().decode()})
            else:
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
                    self.end_headers()
        except socket.error:
            pass
        self.rfile.close()

def respond_error(req):
    req.send_response(500)
    req.end_headers()

def respond_html(req, content):
    req.send_response(200)
    req.send_header('Content-type', 'text/html')
    req.end_headers()
    req.wfile.write(str.encode(content))

def respond_json(req, data):
    json_data = json.dumps(data)
    req.send_response(200)
    req.send_header('Content-type', 'application/json')
    req.end_headers()
    req.wfile.write(str.encode(json_data))

try:
    BASEDIR = os.path.dirname(os.path.abspath(__file__))
    httpd = ThreadingServer(("", PORT), RequestHandler)

    print("serving at port", PORT)
    httpd.serve_forever()

except KeyboardInterrupt:
    print('^C received, shutting down the web server')
    httpd.socket.close()
