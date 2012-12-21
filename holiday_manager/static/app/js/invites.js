var BaseModalView = Backbone.View.extend({
    reload_parent: false,
    specific_events: {},
    base_events: {
        'click .nav-tabs a': function (e) {
            e.preventDefault();
            var target = $(e.target);
            target.tab('show');
        },
        'click .modal-body': function (e) {
            e.stopPropagation();
        },
        'hidden': function(e) {
            router.navigate(router.root);
            if (this.reload_parent) {
                get_page(this.$el.data('reload-url'));
            }
        },
        'click [data-action="close"]': function(e) {
            e.preventDefault();
            this.close();
        }
    },
    events: function() {
        var events = _.extend(this.base_events, this.specific_events);
        return events;
    },
    initialize: function() {
        this.loader = this.$('.modal-loader');  
    },
    render: function(url, callback) {
        var self = this;
        this.modal = new Modal(self.$el, {
            backdrop: true,
            ajax: {
                url: url
            },
            after_loaded: function(modal, data) {
                self.after_loaded();
                if (callback) {
                    _.bind(callback, self)();
                }
            }
        });
        return this;
    },
    after_loaded: function () {
        this.position();
    },
    position: function() {
        this.$el.css({
            top: ($(window).height() - this.$el.outerHeight()) / 2 + 200
        });  
    },
    show: function () {
        this.modal.show();
        return this;
    },
    close: function() {
        this.modal.hide();
        this.undelegateEvents();
        return this;
    }
});

var UserDetailModalView = BaseModalView.extend({
    specific_events: {
        'click [data-action="edit"]': function (e) {
            var self = this;
            e.preventDefault();
            var target = $(e.target);
            this.close();
            var modal = new AddMemberModalView({el: $('#invite-user-modal')}).render(target.attr('href')).show();
        },
    }
});


var AddMemberModalView = BaseModalView.extend({
    specific_events: {
        'click .send-invite': function (e) {
            var self = this;
            e.preventDefault();
            var target = $(e.target);
            var form = target.closest('form');
            self.loader.show();
            $.post(form.attr('action'), form.serialize(), function(resp) {
                self.loader.hide();
                self.modal.injectContent(resp);
                self.reload_parent = true;
            }).error(function() {
                self.loader.hide();
                alert("Unexpected error, please retry.");
            });    
        },
        'click .import-contacts': function (e) {
            var self = this;
            e.preventDefault();
            var target = $(e.target);
            var form = target.closest('form');
            self.loader.show();
            $.post(form.attr('action'), form.serialize(), function(resp) {
                //self.modal.injectContent(resp);
                self.loader.hide();
                self.$('#tab-gmail').html(resp);
                self.reload_parent = true;
            }).error(function() {
                self.loader.hide();
                alert("Unexpected error, please retry.");
            });    
        },
        'click a[href="#tab-gmail"]': function(e) {
            var target = $(e.target);
            var self = this;
            self.load_contacts(target);
            router.navigate(target.attr('href'));
        }
    },
    load_contacts: function(target) {
        var self = this;
        if (target.data('ajax-loaded')) {
            return;
        }
        $.get(target.data('ajax'), function(resp) {
            $(target.attr('href')).html(resp);
            target.data('ajax-loaded', true);
        });
    }
});

var EditUserModalView = Backbone.View.extend({
    reload_parent: false,
    events: {
        'click .save': function (e) {
            var self = this;
            e.preventDefault();
            console.log('Send invite');
            var target = $(e.target);
            var form = target.closest('form');
            self.loader.show();
            $.post(form.attr('action'), form.serialize(), function(resp) {
                self.modal.injectContent(resp);
                self.loader.hide();
            });    
        },
        'click .nav-tabs a': function (e) {
            e.preventDefault();
            $(e.target).tab('show');
        },
        'click .modal-body': function (e) {
            e.stopPropagation();
        },
        'click .form-actions [type="submit"]': function(e) {
            e.preventDefault();
            var self = this;
            var target = $(e.target);
            var form = target.closest('form');
            self.loader.show();
            $.post(form.attr('action'), form.serialize(), function(resp) {
                self.modal.injectContent(resp);
                self.loader.hide();
                self.reload_parent = true;
            });
        },
        'hidden': function(e) {
            if (this.reload_parent) {
                get_page(this.$el.data('reload-url'));    
            }
        }
    },
    initialize: function() {
        this.loader = this.$('.modal-loader');  
    },
    render: function(url) {
        var self = this;
        this.modal = new Modal(self.$el, {
            backdrop: true,
            ajax: {
                url: url
            },
            after_loaded: function(modal, data) {
                self.after_loaded();
                //$(':input').focus(function(e) {
                //    $help = $(this).siblings('.help-icon');
                //    if ($help.length) {
                //        $help.clickover('clickery');
                //    } else {
                //        $('[data-clickover-open=1]').each(function() { 
                //            $(this).data('clickover') && $(this).data('clickover').clickery();
                //        });
                //    }
                //});
                //$('.help-icon').clickover({
                //    template: '<div class="popover"><div class="arrow"></div><div class="popover-inner"><div class="popover-content"><p></p></div></div></div>'
                //});
            }
        });
        return this;
    },
    after_loaded: function () {
        this.position();
    },
    position: function() {
        this.$el.css({
            top: ($(window).height() - this.$el.outerHeight()) / 2 + 200
        });  
    },
    show: function () {
        this.modal.show();
    },
    close: function() {
        this.modal.hide();
    }
});

var GroupModalView = BaseModalView.extend({
    specific_events: {
        'click .form-actions [type="submit"]': function (e) {
            var self = this;
            e.preventDefault();
            var target = $(e.target);
            var form = this.$('.modal-body form');
            self.loader.show();
            $.post(form.attr('action'), form.serialize(), function(resp) {
                self.loader.hide();
                //self.close();
                //get_page(this.$el.data('reload-url'));
                self.modal.injectContent(resp);
                self.reload_parent = true;
            }).error(function() {
                self.loader.hide();
                alert("Unexpected error, please retry.");
            });    
        },
        'click .delete-group': function(e) {
            e.preventDefault();
            var target = $(e.target);
            var self = this;
            self.loader.show();
            $.post(target.attr('href'), function() {
                self.close();
                get_page(self.$el.data('reload-url'));
            }).error(function() {
                alert("Unexpected error");
                self.loader.hide();
            });
        },
        'click .modal-body': function (e) {
            e.stopPropagation();
        },
        'click .nav-tabs a': function (e) {
            e.preventDefault();
            var target = $(e.target);
            target.tab('show');
        },
        'hidden': function(e) {
            router.navigate(router.root);
            if (this.reload_parent) {
                get_page(this.$el.data('reload-url'));
            }
        }
    },
    after_loaded: function () {
        this.position();
        this.$(".sortable-formset .select2").select2();
        this.$('.sortable-formset > li').formset({
            prefix: app_vars.formset_prefix,
            formTemplate: $('#empty-form-template'),
            fieldsetContainer: '.sortable-formset',
            beforeRender: function(row, form_count) {
                $(".select2", row).select2();
                $(".position", row).text(form_count + 1);
                return row;
            }
        });
    }
});

var Router = Backbone.Router.extend({
    routes: {
        "invite": "invite",
        "tab-gmail": "gmail_contacts",
    },
    invite: function() {
        var modal = new AddMemberModalView({el: $('#invite-user-modal')}).render(app_urls.invite).show();        
    },
    gmail_contacts: function() {
        var modal = new AddMemberModalView({el: $('#invite-user-modal')}).render(app_urls.invite, function() {
            this.load_contacts(this.$('[href="#tab-gmail"]'));
            //this.$('[href="#tab-gmail"]').tab('show');
        }).show();
    }
});

var router = new Router();
Backbone.history.start({pushState: false, root: app_urls.root});


$('.invite-user').click(function(e) {
    e.preventDefault();
    var target = $(e.target);
    var modal = new AddMemberModalView({el: $('#invite-user-modal')}).render(target.attr('href')).show();
    router.navigate('invite');
});

$('.create-group').click(function(e) {
    e.preventDefault();
    var target = $(e.target);
    var modal = new GroupModalView({el: $('#create-group-modal')}).render(target.attr('href')).show();
    router.navigate('creategroup');
});

$('.user-details').click(function(e) {
    e.preventDefault();
    var target = $(e.currentTarget);
    var modal = new UserDetailModalView({el: $('#user-detail-modal')}).render(target.attr('href')).show();
});
