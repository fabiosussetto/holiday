var BasePopupView = Backbone.View.extend({
    initialize: function(options) {
        this.parent = options.parent;
    },
    place: function(selection, viewport, show) {
        show = show || true;
        var scroll_offset = viewport.scrollLeft();
        var first_pos = selection.first.position();
        var last_pos = selection.last.position();
        var first_x = first_pos.left + scroll_offset;
        var last_x = last_pos.left + scroll_offset;
        
        var left = first_x + (last_x - first_x - this.$el.outerWidth() + selection.first.outerWidth()) / 2;
        this.$el.css({
            top: first_pos.top + 28,
            left: left
        });
        if (show) {
            this.show();
        }
    },
    show: function () {
        this.$el.show();
    },
    hide: function () {
        this.$el.hide();
    }
});


var InfoPopupView = BasePopupView.extend({
    template: _.template($('#template-popover').html()),
    events: {
        'click .show-details': function(e) {
            e.preventDefault();
            var self = this;
            modal = new Modal($('#myModal'), {
                backdrop: true,
                ajax: {
                    url: app_urls.request_details,
                    data: {
                        pk: this.requested_data.pk
                    }
                },
            });
            modal.$element.on('click', '.submit', function(e) {
                e.preventDefault();
                var form = modal.$element.find('form');
                var button = $(e.target);
                modal.$element.find('#id_status').val(button.data('status'));
                modal.load({
                    ajax: {
                        url: form.attr('action'),
                        type: 'POST',
                        data: form.serialize(),
                        success: function() {
                            modal.hide();
                            get_page(modal.$element.data('page-url'));
                        }
                    }
                });
            });
            modal.show();
            this.hide();
        }
    },
    render: function(requested_data) {
        this.requested_data = requested_data;
        this.$el.html(this.template(this.requested_data));
        return this;
    }
});


var SelectionPopupView = BasePopupView.extend({
    events: {
        'click .new-request': function(e) {
            e.preventDefault();
            var self = this;
            modal = new Modal($('#myModal'), {
                backdrop: true,
                ajax: {
                    url: this.$el.data('url'),
                    data: {
                        start_date: this.parent.selection.first.data('date'),
                        end_date: this.parent.selection.last.data('date')
                    }
                },
            });
            modal.$element.on('hide', function() {
                self.parent.clear_selection();
            });
            modal.$element.on('click', '.submit', function(e) {
                e.preventDefault();
                var form = modal.$element.find('form');
                modal.load({
                    ajax: {
                        url: form.attr('action'),
                        type: 'POST',
                        data: form.serialize()
                    }
                });
            }).on('click', '.cancel', function(e) {
                modal.hide();
            });
            modal.$element.on('click', '.done', function(e) {
                e.preventDefault();
                modal.hide();
                get_page(modal.$element.data('page-url'));
            });
            modal.show();
            this.hide();
        },
        'click .cancel': function(e) {
            e.preventDefault();
            this.trigger('cancel_selection');
            this.hide();
        }
    }
});

var CalendarView  = Backbone.View.extend({
    selection_active: false,
    selection: {first: null, last: null},
    viewport: $('.table-scroll'),
    initialize: function(options) {
        this.popup_view = new SelectionPopupView({el: $('#submit'), parent: this});
        this.popup_view.on('cancel_selection', this.clear_selection);
        
        this.info_popup_view = new InfoPopupView({el: $('#request-data'), parent: this});
    },
    events: {
        'click #current-user-row td': function(e) {
            var curr_td = $(e.currentTarget);
            if (curr_td.is('.request, .past')) {
                return;
            }
            if (!this.selection_active && curr_td.hasClass("highlighted")) {
                return;
            }
            if (!this.selection_active) {
                this.clear_selection();
                this.popup_view.hide();
                // first click, selection starts
                this.selection.first = this.selection.last = curr_td;
                this.selection.first.addClass('highlighted selection-first selection-last');
                this.selection_active = true;
                return;
            }
            // second click, selection finishes
            if (curr_td.index() < this.selection.first.index()) {
                // negative selection, do nothing
                return;
            }
            
            this.selection_active = false;
            this.selection.last = curr_td;
            var selected_tds = $('#current-user-row .highlighted');
            if (!selected_tds.length) {
                return;
            }
            this.popup_view.place(this.selection, this.viewport);
        },
        'mouseenter #current-user-row td': function(e) {
            if (!this.selection_active) {
                return;
            }
            var curr_td = $(e.currentTarget);
            if (curr_td.index() < this.selection.first.index() || curr_td.hasClass('request')) {
                // negative selection, do nothing
                return;
            }
            is_selected = curr_td.hasClass("highlighted");
            this.selection.last.removeClass('selection-last');
            if (is_selected) {
                curr_td.addClass('selection-last');
                this.selection.last = curr_td;
                this.selection.last.nextAll('.highlighted').removeClass('highlighted selection-last');
            } else {
                curr_td.addClass('highlighted selection-last');
                this.selection.last = curr_td;
                this.selection.first.nextUntil('.selection-last').removeClass('selection-last').addClass('highlighted');
            }
        },
        'click .request': function(e) {
            var selection = this.find_selection($(e.currentTarget));
            var request_obj = $(selection[0]).data('request');
            var selection = {first: $(selection[0]), last: $(selection[selection.length - 1])}
            this.info_popup_view.render(request_obj).place(selection, this.viewport);
        }
    },
    clear_selection: function() {
        $('#current-user-row .highlighted').removeClass("highlighted selection-first selection-last");
        this.selection = {first: null, last: null}
    },
    find_selection: function(td) {
        // TODO: use native js to improve performances
        if (td.hasClass('first')) {
            var selection = td.nextUntil('.last +').add(td);
        } else {
            var first = td.prevUntil('.first');
            if (first.length) {
                var selection = first.prev().add(td.nextUntil('.last +')).add(td);
            } else {
                var selection = td.prev().add(td.nextUntil('.last +')).add(td);
            }
        }
        return selection;
    },
    render: function() {
        return this;
    }
});

var UserRowsView = Backbone.View.extend({
    events: {
        'click .user-row .check': function(e) {
            var el = $(e.target);
            el.parent().toggleClass('selected');
        },
        'click .team-row': function(e) {
            e.preventDefault();
            var target = $(e.target);
            if (!target.hasClass('loaded')) {
                $.get(target.attr('href'), function(resp) {
                    var data = $('<div />').html(resp);
                    $('#team-row-' + target.data('target')).after(data.find('#data-users').html());
                    $('#days-group-' + target.data('target')).empty().html(data.find('#data-requests').html());
                    target.addClass('loaded');
                });
                return;
            }
            target.toggleClass('collapsed');
            target.find('i').toggleClass('icon-chevron-down').toggleClass('icon-chevron-right');
            var group_id = target.data('target');
            $('#users-group-' + group_id).toggle();
            $('#days-group-' + group_id).toggle();
        },
        'click .user-details': function(e) {
            var target = $(e.currentTarget);
            e.preventDefault();
            modal = new Modal($('#user-detail-modal'), {
                backdrop: true,
                ajax: {
                    url: target.attr('href'),
                }
            });
            modal.show();
        }
    }
});
