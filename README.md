[![Build Status](https://travis-ci.org/palette-software/insight-website.svg?branch=master)](https://travis-ci.org/palette-software/insight-website)

# Palette Insight Architecture

![Palette Insight Architecture](https://github.com/palette-software/palette-insight/blob/master/insight-system-diagram.png?raw=true)

# Palette Insight Website
[Insight Server]: https://github.com/palette-software/insight-server

## What is Palette Insight Website?

WebUI microservice for providing status and start/stop features for Palette [Insight Server].

In this project you will find:

- the [supervisord](http://supervisord.org/) configuration [file](supervisor.conf)
 which starts the website as a service
- an [nginx](https://nginx.org) configuration [file](nginx.site.conf)
- a [sample.txt](sample.txt) for testing purposes

The Palette Insight Website serves multiple functions:

  - Shows status information on Palette Insight components.
  - Enables download option for Palette Insight Agent on `/control`
  - Allows user to stop and start Palette Insight server side services on `/control`
  - Allows updating Palette Insight on `/control`
  - Allows remote editing of Palette Insight Agent config files. `/config`

## How do I set up Palette Insight Website?

### Prerequisites

- Palette Insight Website is compatible with Python 3.5

### Packaging

To build the package you may use the [create_rpm.sh](create_rpm.sh):

```bash
export PACKAGEVERSION=123
export VERSION=v1.0.$PACKAGEVERSION
./create_rpm.sh
```

### Installation

The most convenient is to build the RPM package and install it using either yum or rpm.
It does require and install the other necessary components and services.

The following process is executed by the installer:

- installation of the required python packages (`pip install -r requirements.txt`)
- enabling the http/s services on the firewall
- disabling the default nginx site configuration
- startup of the palette-insight-website service

## How can I test-drive Palette Insight Website?

To start the server execute:

```bash
python server.py
```

To test the website without the other components been installed start it in test mode:

```bash
DEBUG=1 python server.py
```

The website is available under <http://localhost:9080>

### Unit tests

To run the unit tests execute:

```bash
python -m unittest test_agent_installer.py
```

## Is Palette Insight Website supported?

Palette Insight Website is licensed under the GNU GPL v3 license. For professional support please contact developers@palette-software.com

Any bugs discovered should be filed in the [Palette Insight Website Git issue tracker](https://github.com/palette-software/insight-website/issues) or contribution is more than welcome.
