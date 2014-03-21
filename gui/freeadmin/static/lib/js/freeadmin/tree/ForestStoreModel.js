define(["dijit/tree/ForestStoreModel", "dojo/_base/declare", "dojo/_base/lang"], function(ForestStoreModel, declare, lang) {
    var MyForestStoreModel = declare("freeadmin.tree.ForestStoreModel", [ForestStoreModel], {
        getChildren: function(parentItem, callback, onError){
            if(parentItem === this.root){
                if(this.root.children){
                    // already loaded, just return
                    callback(this.root.children);
                }else{
                    this.store.fetch({
                        query: this.query,
                        queryOptions: {cache:false},
                        onComplete: lang.hitch(this, function(items){
                            this.root.children = items;
                            callback(items);
                        }),
                        onError: onError
                    });
                }
            }else{

                /*
                 * This is the piece were we overwrite over the super class
                 * We do this to overwrite the deferred item load,
                 * {re}loading the node everytime
                 */
                var store = this.store;
                store.loadItem({
                    item: parentItem,
                    onItem: function(parItem){
                        callback(parItem.children);
                    },
                    onError: onError
                });
            }
        }
    });

    return MyForestStoreModel;

});
