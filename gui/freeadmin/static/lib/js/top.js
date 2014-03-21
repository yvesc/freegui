/*-
 * Copyright (c) 2011 iXsystems, Inc.
 * All rights reserved.
 *
 * Written by:  Xin LI
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *
 */

require([
    "dojox/timing",
    "dojo/dom",
    "dijit/registry",
    "dojo/request/xhr"], function(
    timing,
    dom,
    registry,
    xhr) {

    ttop = new timing.Timer(2500);

    ttop.onTick = function() {
        loadtop();
    }
    ttop.onStart = function() {
        loadtop();
    }

    var _topstarted = false;

    loadtop = function() {

        if(_topstarted == true)
            return;
        _topstarted = true;
        xhr('/system/top/', {
            handleAs: "xml"
            }).then(function(data) {

                _topstarted = false;
                var topOutput = data.getElementsByTagName('top')[0].childNodes[0].nodeValue;
                var pageElement = dom.byId('top_output');

                var top_dialog = registry.byId("top_dialog");
                if(!top_dialog.open) {
                    ttop.stop();
                }

                if ('innerText' in pageElement) {
                    pageElement.innerText = topOutput;
                } else {
                    pageElement.innerHTML = topOutput;
                }

            });
    }

});
