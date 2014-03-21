#+
# Copyright 2012 iXsystems, Inc.
# All rights reserved
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted providing that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
#####################################################################
import logging
import os

from django.http import HttpResponse
from django.shortcuts import render

from freenasUI.reporting import rrd

RRD_BASE_PATH = "/var/db/collectd/rrd/localhost"

log = logging.getLogger('reporting.views')


def plugin2graphs(name):

    graphs = []
    if name in rrd.name2plugin:
        ins = rrd.name2plugin[name](RRD_BASE_PATH)
        ids = ins.get_identifiers()
        if ids is not None:
            if len(ids) > 0:
                for ident in ids:
                    graphs.append({
                        'plugin': ins.plugin,
                        'identifier': ident,
                    })
        else:
           graphs.append({
               'plugin': ins.plugin,
           })

    return graphs


def index(request):
    return render(request, "reporting/index.html")


def generic_graphs(request, names=None):

    if names is None:
        names = []

    graphs = []
    for name in names:
        graphs.extend(plugin2graphs(name))

    return render(request, 'reporting/graphs.html', {
        'graphs': graphs,
    })


def generate(request):

    try:
        plugin = request.GET.get("plugin")
        plugin = rrd.name2plugin.get(plugin)
        unit = request.GET.get("unit", "hourly")
        step = request.GET.get("step", "0")
        identifier = request.GET.get("identifier")

        plugin = plugin(
            base_path=RRD_BASE_PATH,
            unit=unit,
            step=step,
            identifier=identifier
            )
        fd, path = plugin.generate()
        with open(path, 'rb') as f:
            data = f.read()

        try:
            os.unlink(path)
            os.close(fd)
        except OSError, e:
            log.warn("Failed to remove reporting temp file: %s", e)

        response = HttpResponse(data)
        response['Content-type'] = 'image/png'
        return response
    except Exception, e:
        log.debug("Failed to generate rrd graph: %s", e)
