odoo.define("web_set_single_page_hidden.Pager", function(require) {
    "use strict";

    var Pager = require("web.Pager");

    Pager.include({
        _setSinglePageHidden: function(value) {
            if (!_.isUndefined(this.options)) {
                this.options.single_page_hidden = value;
                this._render();
            }
        },
    });
});
