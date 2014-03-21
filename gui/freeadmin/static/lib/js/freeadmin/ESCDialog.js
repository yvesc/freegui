define([
    "dojo/_base/declare",
    "dojo/keys",
    "dijit/Dialog"
    ], function(
    declare,
    keys,
    Dialog
    ) {

    var MyDialog = declare("freeadmin.ESCDialog", [Dialog], {
        _onKey: function(evt) {
            if(evt.keyCode == keys.ESCAPE ||
               evt.keyCode == keys.BACKSPACE ||
               (dojo.isWebKit && (
                   evt.keyCode == keys.TAB
                   ))) {
                if(_webshell) {
                    _webshell.keypress(evt);
                }
                return;
            }
            this.inherited(arguments);
        },
    });
    return MyDialog;

});
