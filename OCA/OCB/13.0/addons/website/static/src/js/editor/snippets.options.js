odoo.define('website.editor.snippets.options', function (require) {
'use strict';

var core = require('web.core');
var Dialog = require('web.Dialog');
var weWidgets = require('wysiwyg.widgets');
var options = require('web_editor.snippets.options');

var _t = core._t;
var qweb = core.qweb;

options.Class.include({

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Refreshes all public widgets related to the given element.
     *
     * @private
     * @param {jQuery} [$el=this.$target]
     */
    _refreshPublicWidgets: function ($el) {
        this.trigger_up('widgets_start_request', {
            editableMode: true,
            $target: $el || this.$target,
        });
    },
});

options.registry.background.include({

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _getEditableMedia: function () {
        if (!this._hasBgvideo()) {
            return this._super(...arguments);
        }
        return this.$('.o_bg_video_iframe')[0];
    },
    /**
     * @override
     */
    _getMediaDialogOptions: function () {
        return _.extend(this._super(...arguments), {
            // For now, disable the possibility to have a parallax video bg
            noVideos: this.$target.is('.parallax, .s_parallax_bg'),
            isForBgVideo: true,
        });
    },
    /**
     * @override
     */
    _setActive: function () {
        this._super(...arguments);
        if (this._hasBgvideo()) {
            this.$el.find('[data-choose-image]').addClass('active');
        }
    },
    /**
     * Updates the background video used by the snippet.
     *
     * @private
     * @see this.selectClass for parameters
     */
    _setBgVideo: function (previewMode, value) {
        this.$('> .o_bg_video_container').toggleClass('d-none', previewMode === true);

        if (previewMode !== false) {
            return;
        }

        var target = this.$target[0];
        target.classList.toggle('o_background_video', !!(value && value.length));
        if (value && value.length) {
            target.dataset.bgVideoSrc = value;
        } else {
            delete target.dataset.bgVideoSrc;
        }
        this._refreshPublicWidgets();
        this._setActive();
    },
    /**
     * Returns whether the current target has a background video or not.
     *
     * @private
     * @returns {boolean}
     */
    _hasBgvideo: function () {
        return this.$target[0].classList.contains('o_background_video');
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @override
     */
     _onBackgroundColorUpdate: function (ev, previewMode) {
        var ret = this._super(...arguments);
        if (ret) {
            this._setBgVideo(previewMode);
        }
        return ret;
    },
    /**
     * @override
     */
    _onSaveMediaDialog: function (data) {
        if (!data.bgVideoSrc) {
            this._setBgVideo(false);
            this._super(...arguments);
            return;
        }
        // if the user chose a video, only add the video without removing the
        // background
        this._setBgVideo(false, data.bgVideoSrc);
    },
});

options.registry.menu_data = options.Class.extend({
    xmlDependencies: ['/website/static/src/xml/website.editor.xml'],

    /**
     * When the users selects a menu, a dialog is opened to ask him if he wants
     * to follow the link (and leave editor), edit the menu or do nothing.
     *
     * @override
     */
    onFocus: function () {
        var self = this;
        (new Dialog(this, {
            title: _t("Confirmation"),
            $content: $(core.qweb.render('website.leaving_current_page_edition')),
            buttons: [
                {text: _t("Go to Link"), classes: 'btn-primary', click: function () {
                    self.trigger_up('request_save', {
                        reload: false,
                        onSuccess: function () {
                            window.location.href = self.$target.attr('href');
                        },
                    });
                }},
                {text: _t("Edit the menu"), classes: 'btn-primary', click: function () {
                    this.trigger_up('action_demand', {
                        actionName: 'edit_menu',
                        params: [
                            function () {
                                var prom = new Promise(function (resolve, reject) {
                                    self.trigger_up('request_save', {
                                        onSuccess: resolve,
                                        onFailure: reject,
                                    });
                                });
                                return prom;
                            },
                        ],
                    });
                }},
                {text: _t("Stay on this page"), close: true}
            ]
        })).open();
    },
});

options.registry.company_data = options.Class.extend({
    /**
     * Fetches data to determine the URL where the user can edit its company
     * data. Saves the info in the prototype to do this only once.
     *
     * @override
     */
    start: function () {
        var proto = options.registry.company_data.prototype;
        var prom;
        var self = this;
        if (proto.__link === undefined) {
            prom = this._rpc({route: '/web/session/get_session_info'}).then(function (session) {
                return self._rpc({
                    model: 'res.users',
                    method: 'read',
                    args: [session.uid, ['company_id']],
                });
            }).then(function (res) {
                proto.__link = '/web#action=base.action_res_company_form&view_type=form&id=' + (res && res[0] && res[0].company_id[0] || 1);
            });
        }
        return Promise.all([this._super.apply(this, arguments), prom]);
    },
    /**
     * When the users selects company data, opens a dialog to ask him if he
     * wants to be redirected to the company form view to edit it.
     *
     * @override
     */
    onFocus: function () {
        var self = this;
        var proto = options.registry.company_data.prototype;

        Dialog.confirm(this, _t("Do you want to edit the company data ?"), {
            confirm_callback: function () {
                self.trigger_up('request_save', {
                    reload: false,
                    onSuccess: function () {
                        window.location.href = proto.__link;
                    },
                });
            },
        });
    },
});

/**
 * @todo should be refactored / reviewed
 */
options.registry.carousel = options.Class.extend({
    /**
     * @override
     */
    start: function () {
        var self = this;

        this.$target.carousel({interval: false});
        this.id = this.$target.attr('id');
        this.$inner = this.$target.find('.carousel-inner');
        this.$indicators = this.$target.find('.carousel-indicators');
        this.$target.carousel('pause');
        this._rebindEvents();

        var def = this._super.apply(this, arguments);

        // set background and prepare to clean for save
        this.$target.on('slid.bs.carousel', function () {
            self.$target.carousel('pause');
            self.trigger_up('option_update', {
                optionNames: ['background', 'background_position', 'colorpicker', 'sizing_y'],
                name: 'target',
                data: self.$target.find('.carousel-item.active'),
            });
        });

        return def;
    },
    /**
     * Associates unique ID on slider elements.
     *
     * @override
     */
    onBuilt: function () {
        this.id = 'myCarousel' + new Date().getTime();
        this.$target.attr('id', this.id);
        this.$target.find('[data-target]').attr('data-target', '#' + this.id);
        this._rebindEvents();
    },
    /**
     * @override
     */
    onFocus: function () {
        // Needs to be done on focus, not on start, as all other options are
        // maybe not all initialized in start
        this.$target.trigger('slid.bs.carousel');
    },
    /**
     * Associates unique ID on cloned slider elements.
     *
     * @override
     */
    onClone: function () {
        var id = 'myCarousel' + new Date().getTime();
        this.$target.attr('id', id);
        _.each(this.$target.find('[data-slide], [data-slide-to]'), function (el) {
            var $el = $(el);
            if ($el.attr('data-target')) {
                $el.attr('data-target', '#' + id);
            } else if ($el.attr('href')) {
                $el.attr('href', '#' + id);
            }
        });
    },
    /**
     * @override
     */
    cleanForSave: function () {
        this._super.apply(this, arguments);
        this.$target.find('.carousel-item').removeClass('next prev left right active')
            .first().addClass('active');
        this.$target.find('.carousel-indicators').find('li').removeClass('active').html('')
            .first().addClass('active');
        this.$target.removeClass('oe_img_bg ' + this._class).css('background-image', '');
    },

    //--------------------------------------------------------------------------
    // Options
    //--------------------------------------------------------------------------

    /**
     * Adds a slide.
     *
     * @see this.selectClass for parameters
     */
    addSlide: function (previewMode) {
        var self = this;
        var cycle = this.$inner.find('.carousel-item').length;
        var $active = this.$inner.find('.carousel-item.active, .carousel-item.prev, .carousel-item.next').first();
        var index = $active.index();
        this.$('.carousel-control-prev, .carousel-control-next, .carousel-indicators').removeClass('d-none');
        // we added a space after the <li> in the line below to keep the same space between the indicators
        this.$indicators.append('<li data-target="#' + this.id + '" data-slide-to="' + cycle + '"></li> ');
        // Need to remove editor data from the clone so it gets its own.
        $active.clone(false)
            .removeClass('active')
            .insertAfter($active);
        _.defer(function () {
            self.$target.carousel().carousel(++index);
            self._rebindEvents();
        });
    },
    /**
     * Removes the current slide.
     *
     * @see this.selectClass for parameters.
     */
    removeSlide: function (previewMode) {
        if (this.remove_process) {
            return;
        }

        var self = this;

        var $items = this.$inner.find('.carousel-item');
        var cycle = $items.length - 1;
        var $active = $items.filter('.active');
        var index = $active.index();

        if (cycle > 0) {
            this.remove_process = true;
            this.$target.on('slid.bs.carousel.slide_removal', function (event) {
                $active.remove();
                self.$indicators.find('li:last').remove();
                self.$target.off('slid.bs.carousel.slide_removal');
                self._rebindEvents();
                self.remove_process = false;
                if (cycle === 1) {
                    self.$target.find('.carousel-control-prev, .carousel-control-next, .carousel-indicators').addClass('d-none');
                }
            });
            _.defer(function () {
                self._refreshPublicWidgets();
                self.$target.carousel(index > 0 ? --index : cycle);
            });
        }
    },
    /**
     * Changes the interval for autoplay.
     *
     * @see this.selectClass for parameters
     */
    interval: function (previewMode, value) {
        this.$target.attr('data-interval', value);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _setActive: function () {
        this._super.apply(this, arguments);
        this.$el.find('[data-interval]').removeClass('active')
            .filter('[data-interval=' + this.$target.attr('data-interval') + ']').addClass('active');
    },
    /**
     * Rebinds carousel events on indicators.
     *
     * @private
     */
    _rebindEvents: function () {
        var self = this;
        this.$target.find('.carousel-control-prev, .carousel-control-next').off('click').on('click', function () {
            self.$target.carousel($(this).data('slide'));
        });
        this.$target.find('.carousel-indicators [data-slide-to]').off('click').on('click', function () {
            self.$target.carousel(+$(this).data('slide-to'));
        });

        /* Fix: backward compatibility saas-3 */
        this.$target.find('.item.text_image, .item.image_text, .item.text_only').find('.container > .carousel-caption > div, .container > img.carousel-image').attr('contentEditable', 'true');
    },
});

options.registry.navTabs = options.Class.extend({
    /**
     * @override
     */
    start: function () {
        this._findLinksAndPanes();
        return this._super.apply(this, arguments);
    },
    /**
     * @override
     */
    onBuilt: function () {
        this._generateUniqueIDs();
    },
    /**
     * @override
     */
    onClone: function () {
        this._generateUniqueIDs();
    },

    //--------------------------------------------------------------------------
    // Options
    //--------------------------------------------------------------------------

    /**
     * Creates a new tab and tab-pane.
     *
     * @see this.selectClass for parameters
     */
    addTab: function (previewMode, value, $opt) {
        var $activeItem = this.$navLinks.filter('.active').parent();
        var $activePane = this.$tabPanes.filter('.active');

        var $navItem = $activeItem.clone();
        var $navLink = $navItem.find('.nav-link').removeClass('active show');
        var $tabPane = $activePane.clone().removeClass('active show');
        $navItem.insertAfter($activeItem);
        $tabPane.insertAfter($activePane);
        this._findLinksAndPanes();
        this._generateUniqueIDs();

        $navLink.tab('show');
    },
    /**
     * Removes the current active tab and its content.
     *
     * @see this.selectClass for parameters
     */
    removeTab: function (previewMode, value, $opt) {
        var self = this;

        var $activeLink = this.$navLinks.filter('.active');
        var $activePane = this.$tabPanes.filter('.active');

        var $next = this.$navLinks.eq((this.$navLinks.index($activeLink) + 1) % this.$navLinks.length);
        $next.one('shown.bs.tab', function () {
            $activeLink.parent().remove();
            $activePane.remove();
            self._findLinksAndPanes();
            self._setActive(); // TODO forced to do this because we do not return deferred for options
        });
        $next.tab('show');
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _findLinksAndPanes: function () {
        this.$navLinks = this.$target.find('.nav-link');
        var $el = this.$target;
        do {
            $el = $el.parent();
            this.$tabPanes = $el.find('.tab-pane');
        } while (this.$tabPanes.length === 0 && !$el.is('body'));
    },
    /**
     * @private
     */
    _generateUniqueIDs: function () {
        for (var i = 0 ; i < this.$navLinks.length ; i++) {
            var id = _.now() + '_' + _.uniqueId();
            var idLink = 'nav_tabs_link_' + id;
            var idContent = 'nav_tabs_content_' + id;
            this.$navLinks.eq(i).attr({
                'id': idLink,
                'href': '#' + idContent,
                'aria-controls': idContent,
            });
            this.$tabPanes.eq(i).attr({
                'id': idContent,
                'aria-labelledby': idLink,
            });
        }
    },
    /**
     * @private
     * @override
     */
    _setActive: function () {
        this._super.apply(this, arguments);
        this.$el.filter('[data-remove-tab]').toggleClass('d-none', this.$tabPanes.length <= 2);
    },
});

options.registry.sizing_x = options.registry.sizing.extend({
    /**
     * @override
     */
    onClone: function (options) {
        this._super.apply(this, arguments);
        // Below condition is added to remove offset of target element only
        // and not its children to avoid design alteration of a container/block.
        if (options.isCurrent) {
            var _class = this.$target.attr('class').replace(/\s*(offset-xl-|offset-lg-)([0-9-]+)/g, '');
            this.$target.attr('class', _class);
        }
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _getSize: function () {
        var width = this.$target.closest('.row').width();
        var gridE = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
        var gridW = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
        this.grid = {
            e: [_.map(gridE, function (v) { return 'col-lg-' + v; }), _.map(gridE, function (v) { return width/12*v; }), 'width'],
            w: [_.map(gridW, function (v) { return 'offset-lg-' + v; }), _.map(gridW, function (v) { return width/12*v; }), 'margin-left'],
        };
        return this.grid;
    },
    /**
     * @override
     */
    _onResize: function (compass, beginClass, current) {
        if (compass === 'w') {
            // don't change the right border position when we change the offset (replace col size)
            var beginCol = Number(beginClass.match(/col-lg-([0-9]+)|$/)[1] || 0);
            var beginOffset = Number(beginClass.match(/offset-lg-([0-9-]+)|$/)[1] || beginClass.match(/offset-xl-([0-9-]+)|$/)[1] || 0);
            var offset = Number(this.grid.w[0][current].match(/offset-lg-([0-9-]+)|$/)[1] || 0);
            if (offset < 0) {
                offset = 0;
            }
            var colSize = beginCol - (offset - beginOffset);
            if (colSize <= 0) {
                colSize = 1;
                offset = beginOffset + beginCol - 1;
            }
            this.$target.attr('class',this.$target.attr('class').replace(/\s*(offset-xl-|offset-lg-|col-lg-)([0-9-]+)/g, ''));

            this.$target.addClass('col-lg-' + (colSize > 12 ? 12 : colSize));
            if (offset > 0) {
                this.$target.addClass('offset-lg-' + offset);
            }
        }
        this._super.apply(this, arguments);
    },
});

options.registry.layout_column = options.Class.extend({

    //--------------------------------------------------------------------------
    // Options
    //--------------------------------------------------------------------------

    /**
     * Changes the number of columns.
     *
     * @see this.selectClass for parameters
     */
    selectCount: function (previewMode, value, $opt) {
        this._updateColumnCount(value - this.$target.children().length);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Adds new columns which are clones of the last column or removes the
     * last x columns.
     *
     * @private
     * @param {integer} count - positif to add, negative to remove
     */
    _updateColumnCount: function (count) {
        if (!count) {
            return;
        }

        this.trigger_up('request_history_undo_record', {$target: this.$target});

        var colsLength = this.$target.children().length + count;
        if (count > 0) {
            var $lastColumn = this.$target.children().last();
            for (var i = 0; i < count; i++) {
                this.trigger_up('clone_snippet', {$snippet: $lastColumn});
            }
        } else {
            var self = this;
            _.each(this.$target.children().slice(count), function (el) {
                self.trigger_up('remove_snippet', {$snippet: $(el)});
            });
        }

        this._resizeColumns(colsLength);
        this.trigger_up('cover_update');
    },
    /**
     * Resizes the columns so that they are kept on one row.
     *
     * @private
     * @param {number} [colsLength] (default to the actual number of columns)
     */
    _resizeColumns: function (colsLength) {
        var $columns = this.$target.children();
        colsLength = colsLength || $columns.length;
        var colSize = Math.floor(12 / colsLength) || 1;
        var colOffset = Math.floor((12 - colSize * colsLength) / 2);
        var colClass = 'col-lg-' + colSize;
        _.each($columns, function (column) {
            var $column = $(column);
            $column.attr('class', $column.attr('class').replace(/\b(col|offset)-lg(-\d+)?\b/g, ''));
            $column.addClass(colClass);
        });
        if (colOffset) {
            $columns.first().addClass('offset-lg-' + colOffset);
        }
        // TODO: remove in master. This is used to keep the UI in sync, but
        // won't be needed once option methods are properly asynchronous.
        this.colsLength = colsLength;
    },
    /**
     * @override
     */
    _setActive: function () {
        this._super.apply(this, arguments);
        this.$el.find('[data-select-count]').removeClass('active')
            .filter('[data-select-count=' + (this.colsLength || this.$target.children().length) + ']').addClass('active');
    },
});

options.registry.parallax = options.Class.extend({
    /**
     * @override
     */
    start: function () {
        var self = this;
        this.$target.on('snippet-option-change snippet-option-preview', function () {
            self._refreshPublicWidgets();
        });
        return this._super.apply(this, arguments);
    },
    /**
     * @override
     */
    onFocus: function () {
        this.trigger_up('option_update', {
            optionNames: ['background', 'background_position'],
            name: 'target',
            data: this.$target.find('> .s_parallax_bg'),
        });
        // Refresh the parallax animation on focus; at least useful because
        // there may have been changes in the page that influenced the parallax
        // rendering (new snippets, ...).
        // TODO make this automatic.
        this._refreshPublicWidgets();
    },
    /**
     * @override
     */
    onMove: function () {
        this._refreshPublicWidgets();
    },

    //--------------------------------------------------------------------------
    // Options
    //--------------------------------------------------------------------------

    /**
     * Changes the scrolling speed of the parallax effect.
     *
     * @see this.selectClass for parameters
     */
    scroll: function (previewMode, value) {
        this.$target.attr('data-scroll-background-ratio', value);
        this._refreshPublicWidgets();
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _setActive: function () {
        this._super.apply(this, arguments);
        this.$el.find('[data-scroll]').removeClass('active')
            .filter('[data-scroll="' + (this.$target.attr('data-scroll-background-ratio') || 0) + '"]').addClass('active');
    },
});

var FacebookPageDialog = weWidgets.Dialog.extend({
    xmlDependencies: weWidgets.Dialog.prototype.xmlDependencies.concat(
        ['/website/static/src/xml/website.facebook_page.xml']
    ),
    template: 'website.facebook_page_dialog',
    events: _.extend({}, weWidgets.Dialog.prototype.events || {}, {
        'change': '_onOptionChange',
    }),

    /**
     * @constructor
     */
    init: function (parent, fbData, options) {
        this._super(parent, _.extend({
            title: _t("Facebook Page"),
        }, options || {}));

        this.fbData = $.extend(true, {}, fbData);
        this.final_data = this.fbData;
    },
    /**
     * @override
     */
    start: function () {
        this.$previewPage = this.$('.o_facebook_page');
        this.opened().then(this._renderPreview.bind(this));
        return this._super.apply(this, arguments);
    },

    //------------------------------------------------------------------
    // Private
    //------------------------------------------------------------------

    /**
     * Manages Facebook page preview. Also verifies if the page exists on
     * Facebook or not.
     *
     * @private
     */
    _renderPreview: function () {
        var self = this;
        var match = this.fbData.href.match(/^(?:https?:\/\/)?(?:www\.)?(?:fb|facebook)\.com\/(?:([\w.]+)|[^/?#]+-([0-9]{15,16}))(?:$|[\/?# ])/);
        if (match) {
            // Check if the page exists on Facebook or not
            $.ajax({
                url: 'https://graph.facebook.com/' + (match[2] || match[1]) + '/picture',
                statusCode: {
                    200: function () {
                        self._toggleWarning(true);

                        // Managing height based on options
                        if (self.fbData.tabs) {
                            self.fbData.height = self.fbData.tabs === 'events' ? 300 : 500;
                        } else if (self.fbData.small_header) {
                            self.fbData.height = self.fbData.show_facepile ? 165 : 70;
                        } else if (!self.fbData.small_header) {
                            self.fbData.height = self.fbData.show_facepile ? 225 : 150;
                        }
                        options.registry.facebookPage.prototype.markFbElement(self.getParent(), self.$previewPage, self.fbData);
                    },
                    404: function () {
                        self._toggleWarning(false);
                    },
                },
            });
        } else {
            this._toggleWarning(false);
        }
    },
    /**
     * Toggles the warning message and save button and destroy iframe preview.
     *
     * @private
     * @param {boolean} toggle
     */
    _toggleWarning: function (toggle) {
        this.trigger_up('widgets_stop_request', {
            $target: this.$previewPage,
        });
        this.$('.facebook_page_warning').toggleClass('d-none', toggle);
        this.$footer.find('.btn-primary').prop('disabled', !toggle);
    },

    //------------------------------------------------------------------
    // Handlers
    //------------------------------------------------------------------

    /**
     * Called when a facebook option is changed -> adapt the preview and saved
     * data.
     *
     * @private
     */
    _onOptionChange: function () {
        var self = this;
        // Update values in fbData
        this.fbData.tabs = _.map(this.$('.o_facebook_tabs input:checked'), function (tab) { return tab.name; }).join(',');
        this.fbData.href = this.$('.o_facebook_page_url').val();
        _.each(this.$('.o_facebook_options input'), function (el) {
            self.fbData[el.name] = $(el).prop('checked');
        });
        this._renderPreview();
    },
});
options.registry.facebookPage = options.Class.extend({
    /**
     * Initializes the required facebook page data to create the iframe.
     *
     * @override
     */
    willStart: function () {
        var defs = [this._super.apply(this, arguments)];

        var defaults = {
            href: false,
            height: 215,
            width: 350,
            tabs: '',
            small_header: false,
            hide_cover: false,
            show_facepile: false,
        };
        this.fbData = _.defaults(_.pick(this.$target.data(), _.keys(defaults)), defaults);

        if (!this.fbData.href) {
            // Fetches the default url for facebook page from website config
            var self = this;
            defs.push(this._rpc({
                model: 'website',
                method: 'search_read',
                args: [[], ['social_facebook']],
                limit: 1,
            }).then(function (res) {
                if (res) {
                    self.fbData.href = res[0].social_facebook || 'https://www.facebook.com/Odoo';
                }
            }));
        }

        return Promise.all(defs);
    },
    /**
     * @override
     */
    start: function () {
        var self = this;
        this.$target.on('click.facebook_page_option', '.o_add_facebook_page', function (ev) {
            ev.preventDefault();
            self.fbPageOptions();
        });
        return this._super.apply(this, arguments);
    },
    /**
     * @override
     */
    destroy: function () {
        this._super.apply(this, arguments);
        this.$target.off('.facebook_page_option');
    },

    //--------------------------------------------------------------------------
    // Options
    //--------------------------------------------------------------------------

    /**
     * Opens a dialog to configure the facebook page options.
     *
     * @see this.selectClass for parameters
     */
    fbPageOptions: function () {
        var dialog = new FacebookPageDialog(this, this.fbData).open();
        dialog.on('save', this, function (fbData) {
            this.$target.empty();
            this.fbData = fbData;
            options.registry.facebookPage.prototype.markFbElement(this, this.$target, this.fbData);
        });
    },

    //--------------------------------------------------------------------------
    // Static
    //--------------------------------------------------------------------------

    /**
     * @static
     */
    markFbElement: function (self, $el, fbData) {
        _.each(fbData, function (value, key) {
            $el.attr('data-' + key, value);
            $el.data(key, value);
        });
        self._refreshPublicWidgets($el);
    },
});

options.registry.ul = options.Class.extend({
    /**
     * @override
     */
    start: function () {
        var self = this;
        this.$target.on('mouseup', '.o_ul_toggle_self, .o_ul_toggle_next', function () {
            self.trigger_up('cover_update');
        });
        return this._super.apply(this, arguments);
    },
    /**
     * @override
     */
    cleanForSave: function () {
        this._super();
        if (!this.$target.hasClass('o_ul_folded')) {
            this.$target.find('.o_close').removeClass('o_close');
            this.$target.find('li').css('list-style', '');
        }
    },

    //--------------------------------------------------------------------------
    // Options
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    toggleClass: function () {
        this._super.apply(this, arguments);

        this.trigger_up('widgets_stop_request', {
            $target: this.$target,
        });

        this.$target.find('.o_ul_toggle_self, .o_ul_toggle_next').remove();
        this.$target.find('li:has(>ul,>ol)').map(function () {
            // get if the li contain a text label
            var texts = _.filter(_.toArray(this.childNodes), function (a) { return a.nodeType === 3;});
            if (!texts.length || !texts.reduce(function (a,b) { return a.textContent + b.textContent;}).match(/\S/)) {
                return;
            }
            $(this).children('ul,ol').addClass('o_close');
            return $(this).children(':not(ul,ol)')[0] || this;
        })
        .prepend('<a href="#" class="o_ul_toggle_self fa" />');
        var $li = this.$target.find('li:has(+li:not(>.o_ul_toggle_self)>ul, +li:not(>.o_ul_toggle_self)>ol)');
        $li.css('list-style', this.$target.hasClass('o_ul_folded') ? 'none' : '');
        $li.map(function () { return $(this).children()[0] || this; })
            .prepend('<a href="#" class="o_ul_toggle_next fa" />');
        $li.removeClass('o_open').next().addClass('o_close');
        this.$target.find('li').removeClass('o_open');
        this._refreshPublicWidgets();
    },
});

options.registry.collapse = options.Class.extend({
    /**
     * @override
     */
    start: function () {
        var self = this;
        this.$target.on('shown.bs.collapse hidden.bs.collapse', '[role="tabpanel"]', function () {
            self.trigger_up('cover_update');
            self.$target.trigger('content_changed');
        });
        return this._super.apply(this, arguments);
    },
    /**
     * @override
     */
    onBuilt: function () {
        this._createIDs();
    },
    /**
     * @override
     */
    onClone: function () {
        this._createIDs();
    },
    /**
     * @override
     */
    onMove: function () {
        this._createIDs();
        var $panel = this.$target.find('.collapse').removeData('bs.collapse');
        if ($panel.attr('aria-expanded') === 'true') {
            $panel.closest('.accordion').find('.collapse[aria-expanded="true"]')
                .filter(function () {return this !== $panel[0];})
                .collapse('hide')
                .one('hidden.bs.collapse', function () {
                    $panel.trigger('shown.bs.collapse');
                });
        }
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Associates unique ids on collapse elements.
     *
     * @private
     */
    _createIDs: function () {
        let time = new Date().getTime();
        const $tablist = this.$target.closest('[role="tablist"]');
        const $tab = this.$target.find('[role="tab"]');
        const $panel = this.$target.find('[role="tabpanel"]');

        const setUniqueId = ($elem, label) => {
            let elemId = $elem.attr('id');
            if (!elemId || $('[id="' + elemId + '"]').length > 1) {
                do {
                    time++;
                    elemId = label + time;
                } while ($('#' + elemId).length);
                $elem.attr('id', elemId);
            }
            return elemId;
        };

        const tablistId = setUniqueId($tablist, 'myCollapse');
        $panel.attr('data-parent', '#' + tablistId);
        $panel.data('parent', '#' + tablistId);

        const panelId = setUniqueId($panel, 'myCollapseTab');
        $tab.attr('data-target', '#' + panelId);
        $tab.data('target', '#' + panelId);
    },
});

options.registry.gallery = options.Class.extend({
    xmlDependencies: ['/website/static/src/xml/website.gallery.xml'],

    /**
     * @override
     */
    start: function () {
        var self = this;

        // The snippet should not be editable
        this.$target.addClass('o_fake_not_editable').attr('contentEditable', false);

        // Make sure image previews are updated if images are changed
        this.$target.on('save.gallery', 'img', function (ev) {
            var $img = $(ev.currentTarget);
            var index = self.$target.find('.carousel-item.active').index();
            self.$('.carousel:first li[data-target]:eq(' + index + ')')
                .css('background-image', 'url(' + $img.attr('src') + ')');
        });

        // When the snippet is empty, an edition button is the default content
        // TODO find a nicer way to do that to have editor style
        this.$target.on('click.gallery', '.o_add_images', function (e) {
            e.stopImmediatePropagation();
            self.addImages(false);
        });

        this.$target.on('dropped.gallery', 'img', function (ev) {
            self.mode(null, self.getMode());
            if (!ev.target.height) {
                $(ev.target).one('load', function () {
                    setTimeout(function () {
                        self.trigger_up('cover_update');
                    });
                });
            }
        });

        if (this.$('.container:first > *:not(div)').length) {
            self.mode(null, self.getMode());
        }

        return this._super.apply(this, arguments);
    },
    /**
     * @override
     */
    onBuilt: function () {
        this._adaptNavigationIDs();
    },
    /**
     * @override
     */
    onClone: function () {
        this._adaptNavigationIDs();
    },
    /**
     * @override
     */
    cleanForSave: function () {
        if (this.$target.hasClass('slideshow')) {
            this.$target.removeAttr('style');
        }
    },
    /**
     * @override
     */
    destroy() {
        this._super(...arguments);
        this.$target.off('.gallery');
    },

    //--------------------------------------------------------------------------
    // Options
    //--------------------------------------------------------------------------

    /**
     * Allows to select images to add as part of the snippet.
     *
     * @see this.selectClass for parameters
     */
    addImages: function (previewMode) {
        var self = this;
        var $container = this.$('.container:first');
        var dialog = new weWidgets.MediaDialog(this, {multiImages: true, onlyImages: true, mediaWidth: 1920});
        var lastImage = _.last(this._getImages());
        var index = lastImage ? this._getIndex(lastImage) : -1;
        dialog.on('save', this, function (attachments) {
            for (var i = 0 ; i < attachments.length; i++) {
                $('<img/>', {
                    class: 'img img-fluid',
                    src: attachments[i].image_src,
                    'data-index': ++index,
                }).appendTo($container);
            }
            self._reset();
            self.trigger_up('cover_update');
            this._setActive();
        });
        dialog.open();
    },
    /**
     * Allows to change the number of columns when displaying images with a
     * grid-like layout.
     *
     * @see this.selectClass for parameters
     */
    columns: function (previewMode, value) {
        this.$target.attr('data-columns', value);

        var $activeMode = this.$el.find('.active[data-mode]');
        this.mode(null, $activeMode.data('mode'), $activeMode);
    },
    /**
     * Get the image target's layout mode (slideshow, masonry, grid or nomode).
     *
     * @returns {String('slideshow'|'masonry'|'grid'|'nomode')}
     */
    getMode: function () {
        var mode = 'slideshow';
        if (this.$target.hasClass('o_masonry')) {
            mode = 'masonry';
        }
        if (this.$target.hasClass('o_grid')) {
            mode = 'grid';
        }
        if (this.$target.hasClass('o_nomode')) {
            mode = 'nomode';
        }
        return mode;
    },
    /**
     * Displays the images with the "grid" layout.
     */
    grid: function () {
        var imgs = this._getImages();
        var $row = $('<div/>', {class: 'row'});
        var columns = this._getColumns();
        var colClass = 'col-lg-' + (12 / columns);
        var $container = this._replaceContent($row);

        _.each(imgs, function (img, index) {
            var $img = $(img);
            var $col = $('<div/>', {class: colClass});
            $col.append($img).appendTo($row);
            if ((index + 1) % columns === 0) {
                $row = $('<div/>', {class: 'row'});
                $row.appendTo($container);
            }
        });
        this.$target.css('height', '');
    },
    /**
     * Allows to changes the interval of automatic slideshow (not active in
     * edit mode).
     */
    interval: function (previewMode, value) {
        this.$target.find('.carousel:first').attr('data-interval', value);
    },
    /**
     * Displays the images with the "masonry" layout.
     */
    masonry: function () {
        var self = this;
        var imgs = this._getImages();
        var columns = this._getColumns();
        var colClass = 'col-lg-' + (12 / columns);
        var cols = [];

        var $row = $('<div/>', {class: 'row'});
        this._replaceContent($row);

        // Create columns
        for (var c = 0; c < columns; c++) {
            var $col = $('<div/>', {class: 'col o_snippet_not_selectable ' + colClass});
            $row.append($col);
            cols.push($col[0]);
        }

        // Dispatch images in columns by always putting the next one in the
        // smallest-height column
        while (imgs.length) {
            var min = Infinity;
            var $lowest;
            _.each(cols, function (col) {
                var $col = $(col);
                var height = $col.is(':empty') ? 0 : $col.find('img').last().offset().top + $col.find('img').last().height() - self.$target.offset().top;
                if (height < min) {
                    min = height;
                    $lowest = $col;
                }
            });
            $lowest.append(imgs.pop());
        }
    },
    /**
     * Allows to change the images layout. @see grid, masonry, nomode, slideshow
     *
     * @see this.selectClass for parameters
     */
    mode: function (previewMode, value, $opt) {
        this.$target.css('height', '');
        this.$target
            .removeClass('o_nomode o_masonry o_grid o_slideshow')
            .addClass('o_' + value);
        this[value]();
        this.trigger_up('cover_update');
    },
    /**
     * Displays the images with the standard layout: floating images.
     */
    nomode: function () {
        var $row = $('<div/>', {class: 'row'});
        var imgs = this._getImages();

        this._replaceContent($row);

        _.each(imgs, function (img) {
            var wrapClass = 'col-lg-3';
            if (img.width >= img.height * 2 || img.width > 600) {
                wrapClass = 'col-lg-6';
            }
            var $wrap = $('<div/>', {class: wrapClass}).append(img);
            $row.append($wrap);
        });
    },
    /**
     * Allows to remove all images. Restores the snippet to the way it was when
     * it was added in the page.
     *
     * @see this.selectClass for parameters
     */
    removeAllImages: function (previewMode) {
        var $addImg = $('<div>', {
            class: 'alert alert-info css_non_editable_mode_hidden text-center',
        });
        var $text = $('<span>', {
            class: 'o_add_images',
            style: 'cursor: pointer;',
            text: _t(" Add Images"),
        });
        var $icon = $('<i>', {
            class: ' fa fa-plus-circle',
        });
        this._replaceContent($addImg.append($icon).append($text));
    },
    /**
     * Displays the images with a "slideshow" layout.
     */
    slideshow: function () {
        var imgStyle = this.$el.find('.active[data-styling]').data('styling') || '';
        var urls = _.map(this._getImages(), function (img) {
            return $(img).attr('src');
        });
        var currentInterval = this.$target.find('.carousel:first').attr('data-interval');
        var params = {
            srcs : urls,
            index: 0,
            title: "",
            interval : currentInterval || this.$target.data('interval') || 0,
            id: 'slideshow_' + new Date().getTime(),
            userStyle: imgStyle,
        },
        $slideshow = $(qweb.render('website.gallery.slideshow', params));
        this._replaceContent($slideshow);
        _.each(this.$('img'), function (img, index) {
            $(img).attr({contenteditable: true, 'data-index': index});
        });
        this.$target.css('height', Math.round(window.innerHeight * 0.7));

        // Apply layout animation
        this.$target.off('slide.bs.carousel').off('slid.bs.carousel');
        this.$('li.fa').off('click');
        this._refreshPublicWidgets();
    },
    /**
     * Allows to change the style of the individual images.
     *
     * @see this.selectClass for parameters
     */
    styling: function (previewMode, value) {
        var classes = _.map(this.$el.find('[data-styling]'), function (el) {
            return $(el).data('styling');
        }).join(' ');
        this.$('img').removeClass(classes).addClass(value);
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Handles image removals and image index updates.
     *
     * @override
     */
    notify: function (name, data) {
        this._super.apply(this, arguments);
        if (name === 'image_removed') {
            data.$image.remove(); // Force the removal of the image before reset
            this._reset();
        } else if (name === 'image_index_request') {
            var imgs = this._getImages();
            var position = _.indexOf(imgs, data.$image[0]);
            imgs.splice(position, 1);
            switch (data.position) {
                case 'first':
                    imgs.unshift(data.$image[0]);
                    break;
                case 'prev':
                    imgs.splice(position - 1, 0, data.$image[0]);
                    break;
                case 'next':
                    imgs.splice(position + 1, 0, data.$image[0]);
                    break;
                case 'last':
                    imgs.push(data.$image[0]);
                    break;
            }
            _.each(imgs, function (img, index) {
                // Note: there might be more efficient ways to do that but it is
                // more simple this way and allows compatibility with 10.0 where
                // indexes were not the same as positions.
                $(img).attr('data-index', index);
            });
            this._reset();
        }
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _adaptNavigationIDs: function () {
        var uuid = new Date().getTime();
        this.$target.find('.carousel').attr('id', 'slideshow_' + uuid);
        _.each(this.$target.find('[data-slide], [data-slide-to]'), function (el) {
            var $el = $(el);
            if ($el.attr('data-target')) {
                $el.attr('data-target', '#slideshow_' + uuid);
            } else if ($el.attr('href')) {
                $el.attr('href', '#slideshow_' + uuid);
            }
        });
    },
    /**
     * Returns the images, sorted by index.
     *
     * @private
     * @returns {DOMElement[]}
     */
    _getImages: function () {
        var imgs = this.$('img').get();
        var self = this;
        imgs.sort(function (a, b) {
            return self._getIndex(a) - self._getIndex(b);
        });
        return imgs;
    },
    /**
     * Returns the index associated to a given image.
     *
     * @private
     * @param {DOMElement} img
     * @returns {integer}
     */
    _getIndex: function (img) {
        return img.dataset.index || 0;
    },
    /**
     * Returns the currently selected column option.
     *
     * @private
     * @returns {integer}
     */
    _getColumns: function () {
        return parseInt(this.$target.attr('data-columns')) || 3;
    },
    /**
     * Empties the container, adds the given content and returns the container.
     *
     * @private
     * @param {jQuery} $content
     * @returns {jQuery} the main container of the snippet
     */
    _replaceContent: function ($content) {
        var $container = this.$('.container:first');
        $container.empty().append($content);
        return $container;
    },
    /**
     * @override
     */
    _setActive: function () {
        this._super(...arguments);

        var activeModeSelectors = [];
        for (const className of this.$target[0].classList) {
            if (className.startsWith('o_')) {
                activeModeSelectors.push('[data-mode="' + className.substring(2) + '"]');
            }
        }
        var activeMode = this.$el.find('[data-mode]')
            .removeClass('active')
            .filter(activeModeSelectors.join(', '))
            .addClass('active')
            .data('mode');

        var carousel = this.$target[0].querySelector('.carousel');
        var activeInterval = carousel ? (carousel.dataset.interval || 0) : undefined;
        var $intervalOptions = this.$el.find('[data-interval]');
        $intervalOptions.removeClass('active')
            .filter('[data-interval="' + activeInterval + '"]')
            .addClass('active');
        $intervalOptions.closest('we-collapse-area')[0]
            .classList.toggle('d-none', activeMode !== 'slideshow');

        var columns = this._getColumns();
        var $columnOptions = this.$el.find('[data-columns]');
        $columnOptions.removeClass('active')
            .filter('[data-columns="' + columns + '"]')
            .addClass('active');
        $columnOptions.closest('we-collapse-area')[0]
            .classList.toggle('d-none', !(activeMode === 'grid' || activeMode === 'masonry'));

        this.el.querySelector('.o_w_image_spacing_option')
            .classList.toggle('d-none', activeMode === 'slideshow');

        var $stylingOptions = this.$el.find('[data-styling]');
        $stylingOptions.removeClass('active');
        var img = this.$target[0].querySelector('img');
        var activeStyleSelectors = [];
        if (img) {
            for (const className of img.classList) {
                activeStyleSelectors.push('[data-styling="' + className + '"]');
            }
        }
        var $toEnable = activeStyleSelectors.length
            ? $stylingOptions.filter(activeStyleSelectors.join(', '))
            : null;
        if (!$toEnable || !$toEnable.length) {
            $toEnable = $stylingOptions.first();
        }
        $toEnable.addClass('active');
    },
});

options.registry.gallery_img = options.Class.extend({
    /**
     * Rebuilds the whole gallery when one image is removed.
     *
     * @override
     */
    onRemove: function () {
        this.trigger_up('option_update', {
            optionName: 'gallery',
            name: 'image_removed',
            data: {
                $image: this.$target,
            },
        });
    },

    //--------------------------------------------------------------------------
    // Options
    //--------------------------------------------------------------------------

    /**
     * Allows to change the position of an image (its order in the image set).
     *
     * @see this.selectClass for parameters
     */
    position: function (previewMode, value) {
        this.trigger_up('deactivate_snippet');
        this.trigger_up('option_update', {
            optionName: 'gallery',
            name: 'image_index_request',
            data: {
                $image: this.$target,
                position: value,
            },
        });
    },
});

options.registry.topMenuTransparency = options.Class.extend({

    //--------------------------------------------------------------------------
    // Options
    //--------------------------------------------------------------------------

    /**
     * Handles the toggling between normal and overlay positions of the header.
     *
     * @see this.selectClass for params
     */
    transparent: function (previewMode, value, $opt) {
        var self = this;
        this.trigger_up('action_demand', {
            actionName: 'toggle_page_option',
            params: [{name: 'header_overlay'}],
            onSuccess: function () {
                self.trigger_up('action_demand', {
                    actionName: 'toggle_page_option',
                    params: [{name: 'header_color', value: ''}],
                });
            },
        });
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _setActive: function () {
        this._super.apply(this, arguments);

        this.trigger_up('action_demand', {
            actionName: 'get_page_option',
            params: ['header_overlay'],
            onSuccess: value => {
                this.$el.find('[data-transparent]').toggleClass('active', !!value);
            },
        });
    },
});

options.registry.topMenuColor = options.registry.colorpicker.extend({
    /**
     * @override
     */
    start: function () {
        var self = this;
        var def = this._super.apply(this, arguments);
        this.$target.on('snippet-option-change', function () {
            self.onFocus();
        });
        return def;
    },
    /**
     * @override
     */
    onFocus: function () {
        this.trigger_up('action_demand', {
            actionName: 'get_page_option',
            params: ['header_overlay'],
            onSuccess: value => {
                this.$el.toggleClass('d-none', !value);
                if (!value) {
                    this.$el.find('button.selected').removeClass('selected');
                }
            },
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _onColorButtonClick: function () {
        this._super.apply(this, arguments);
        var bgs = this.$target.attr('class').match(/bg-(\w|-)+/g);
        var allowedBgs = this.classes.split(' ');
        var color = _.intersection(bgs, allowedBgs).join(' ');
        this.trigger_up('action_demand', {
            actionName: 'toggle_page_option',
            params: [{name: 'header_color', value: color}],
        });
    },
    /**
     * @override
     */
    _onColorResetButtonClick: function () {
        this._super.apply(this, arguments);
        this.trigger_up('action_demand', {
            actionName: 'toggle_page_option',
            params: [{name: 'header_color', value: ''}],
        });
    },
});

/**
 * Handles the edition of snippet's anchor name.
 */
options.registry.anchorName = options.Class.extend({
    xmlDependencies: ['/website/static/src/xml/website.editor.xml'],

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    onClone: function () {
        this.$target.removeAttr('data-anchor');
        this.$target.filter(':not(.carousel)').removeAttr('id');
    },

    //--------------------------------------------------------------------------
    // Options
    //--------------------------------------------------------------------------

    /**
     * @see this.selectClass for parameters
     */
    openAnchorDialog: function (previewMode, value, $opt) {
        var self = this;
        var buttons = [{
            text: _t("Save"),
            classes: 'btn-primary',
            click: function () {
                var $input = this.$('.o_input_anchor_name');
                var anchorName = $input.val().trim().replace(/\s/g, '_');
                if (self.$target[0].id === anchorName) {
                    // If the chosen anchor name is already the one used by the
                    // element, close the dialog and do nothing else
                    this.close();
                    return;
                }

                var isValid = /^[\w-]+$/.test(anchorName);
                var alreadyExists = isValid && $('#' + anchorName).length > 0;
                var anchorOK = isValid && !alreadyExists;
                this.$('.o_anchor_not_valid').toggleClass('d-none', isValid);
                this.$('.o_anchor_already_exists').toggleClass('d-none', !alreadyExists);
                $input.toggleClass('is-invalid', !anchorOK);
                if (anchorOK) {
                    self._setAnchorName(anchorName);
                    this.close();
                }
            },
        }, {
            text: _t("Discard"),
            close: true,
        }];
        if (this.$target.attr('id')) {
            buttons.push({
                text: _t("Remove"),
                classes: 'btn-link ml-auto',
                icon: 'fa-trash',
                close: true,
                click: function () {
                    self._setAnchorName();
                },
            });
        }
        new Dialog(this, {
            title: _t("Link Anchor"),
            $content: $(qweb.render('website.dialog.anchorName', {
                currentAnchor: this.$target.attr('id'),
            })),
            buttons: buttons,
        }).open();
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {String} value
     */
    _setAnchorName: function (value) {
        if (value) {
            this.$target.attr({
                'id': value,
                'data-anchor': true,
            });
        } else {
            this.$target.removeAttr('id data-anchor');
        }
        this.$target.trigger('content_changed');
    },
});

/**
 * Allows edition of 'cover_properties' in website models which have such
 * fields (blogs, posts, events, ...).
 */
options.registry.CoverProperties = options.Class.extend({
    /**
     * @constructor
     */
    init: function () {
        this._super.apply(this, arguments);

        this.$image = this.$target.find('.o_record_cover_image');
        this.$filter = this.$target.find('.o_record_cover_filter');
    },
    /**
     * @override
     */
    start: function () {
        this.$filterValueOpts = this.$el.find('[data-filter-value]');
        this.$filterColorOpts = this.$el.find('[data-filter-color]');
        this.filterColorClasses = this.$filterColorOpts.map(function () {
            return $(this).data('filterColor');
        }).get().join(' ');

        return this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Options
    //--------------------------------------------------------------------------

    /**
     * @see this.selectClass for parameters
     */
    clear: function (previewMode, value, $opt) {
        this.selectClass(previewMode, '', $());
        this.$image.css('background-image', '');
    },
    /**
     * @see this.selectClass for parameters
     */
    change: function (previewMode, value, $opt) {
        var $image = $('<img/>');
        var background = this.$image.css('background-image');
        if (background && background !== 'none') {
            $image.attr('src', background.match(/^url\(["']?(.+?)["']?\)$/)[1]);
        }

        var editor = new weWidgets.MediaDialog(this, {
            mediaWidth: 1920,
            onlyImages: true,
        }, $image[0]).open();
        editor.on('save', this, function (image) {
            var src = image.src;
            this.$image.css('background-image', src ? ('url(' + src + ')') : '');
            if (!this.$target.hasClass('o_record_has_cover')) {
                var $opt = this.$el.find('.o_record_cover_opt_size_default[data-select-class]');
                this.selectClass(previewMode, $opt.data('selectClass'), $opt);
            }
            this._setActive();
        });
    },
    /**
     * @see this.selectClass for parameters
     */
    filterValue: function (previewMode, value, $opt) {
        this.$filter.css('opacity', value);
    },
    /**
     * @see this.selectClass for parameters
     */
    filterColor: function (previewMode, value, $opt) {
        this.$filter.removeClass(this.filterColorClasses);
        if (value) {
            this.$filter.addClass(value);
        }

        var $firstVisibleFilterOpt = this.$filterValueOpts.eq(1);
        if (parseFloat(this.$filter.css('opacity')) < parseFloat($firstVisibleFilterOpt.data('filterValue'))) {
            this.filterValue(previewMode, $firstVisibleFilterOpt.data('filterValue'), $firstVisibleFilterOpt);
        }
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     * @override
     */
    _setActive: function () {
        this._super.apply(this, arguments);

        _.each(this.$el.children(), el => {
            var $el = $(el);

            if (!$el.is('[data-change]')) {
                $el.removeClass('d-none');

                ['size', 'filters', 'text_size', 'text_align'].forEach(optName => {
                    var $opts = $el.find('[data-cover-opt="' + optName + '"]');
                    var notAllowed = (this.$target.data('use_' + optName) !== 'True');

                    if ($opts.length && (!this.$target.hasClass('o_record_has_cover') || notAllowed)) {
                        $el.addClass('d-none');
                    }
                });
            }
        });

        this.$el.find('[data-clear]').toggleClass('d-none', !this.$target.hasClass('o_record_has_cover'));

        this.$filterValueOpts.removeClass('active');
        this.$filterColorOpts.removeClass('active');

        var activeFilterValue = this.$filterValueOpts
            .filter((i, el) => {
                return (parseFloat($(el).data('filterValue')).toFixed(1) === parseFloat(this.$filter.css('opacity')).toFixed(1));
            }).addClass('active').data('filterValue');

        var activeFilterColor = this.$filterColorOpts
            .filter((i, el) => {
                return this.$filter.hasClass($(el).data('filterColor'));
            }).addClass('active').data('filterColor');

        this.$target[0].dataset.coverClass = this.$el.find('.active[data-cover-opt="size"]').data('selectClass') || '';
        this.$target[0].dataset.textSizeClass = this.$el.find('.active[data-cover-opt="text_size"]').data('selectClass') || '';
        this.$target[0].dataset.textAlignClass = this.$el.find('.active[data-cover-opt="text_align"]').data('selectClass') || '';
        this.$target[0].dataset.filterValue = activeFilterValue || 0.0;
        this.$target[0].dataset.filterColor = activeFilterColor || '';
    },
});
});
