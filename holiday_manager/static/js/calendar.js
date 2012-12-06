/* Simple JavaScript Inheritance
 * By John Resig http://ejohn.org/
 * MIT Licensed.
 */
// Inspired by base2 and Prototype
(function(){
  var initializing = false, fnTest = /xyz/.test(function(){xyz;}) ? /\b_super\b/ : /.*/;
  // The base Class implementation (does nothing)
  this.Class = function(){};
  
  // Create a new Class that inherits from this class
  Class.extend = function(prop) {
    var _super = this.prototype;
    
    // Instantiate a base class (but only create the instance,
    // don't run the init constructor)
    initializing = true;
    var prototype = new this();
    initializing = false;
    
    // Copy the properties over onto the new prototype
    for (var name in prop) {
      // Check if we're overwriting an existing function
      prototype[name] = typeof prop[name] == "function" && 
        typeof _super[name] == "function" && fnTest.test(prop[name]) ?
        (function(name, fn){
          return function() {
            var tmp = this._super;
            
            // Add a new ._super() method that is the same method
            // but on the super-class
            this._super = _super[name];
            
            // The method only need to be bound temporarily, so we
            // remove it when we're done executing
            var ret = fn.apply(this, arguments);        
            this._super = tmp;
            
            return ret;
          };
        })(name, prop[name]) :
        prop[name];
    }
    
    // The dummy class constructor
    function Class() {
      // All construction is actually done in the init method
      if ( !initializing && this.init )
        this.init.apply(this, arguments);
    }
    
    // Populate our constructed prototype object
    Class.prototype = prototype;
    
    // Enforce the constructor to be what we expect
    Class.prototype.constructor = Class;

    // And make this class extendable
    Class.extend = arguments.callee;
    
    return Class;
  };
})();

var Selection = Class.extend({
    start_elem: null,
    end_elem: null,
    init: function(start, end){
        this.start_elem = start;
        this.end_elem = end;
    },
    start: function(elem) {
        this.start_elem = elem;
    },
    update: function() {
    
    }
});

var UserListView = Backbone.View.extend({
    events: {
    },
    render: function() {
    }
});

var SelectionPopupView = Backbone.View.extend({
    events: {
        'click .new-request': function(e) {
            e.preventDefault();
            $('#myModal').modal({
                remote: this.$el.data('url'),
                remote_data: {
                    start_date: this.parent.selection.first.data('date'),
                    end_date: this.parent.selection.last.data('date')
                }
            });
            //window.dialog2 = $('<div/>').dialog2({
            //    title: "Submit request", 
            //    content: this.$el.data('url'), 
            //    id: "server-notice",
            //    ajax: {
            //        data: {
            //            start_date: this.parent.selection.first.data('date'),
            //            end_date: this.parent.selection.last.data('date')
            //        }
            //    }
            //});
            this.hide();
        },
        'click .cancel': function(e) {
            e.preventDefault();
            this.trigger('cancel_selection');
            this.hide();
        }
    },
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
    },
});

var CalendarView  = Backbone.View.extend({
    selection_active: false,
    selection: {first: null, last: null},
    viewport: $('.table-scroll'),
    initialize: function(options) {
        this.popup_view = new SelectionPopupView({el: $('#submit'), parent: this})
        this.popup_view.on('cancel_selection', this.clear_selection);
    },
    events: {
        'click #current-user-row td': function(e) {
            var curr_td = $(e.currentTarget);
            if (!this.selection_active && curr_td.hasClass("highlighted")) {
                return;
            }
            if (!this.selection_active) {
                this.clear_selection();
                this.popup_view.hide();
                // first click, selection starts
                this.selection.first = this.selection.last = $(e.target);
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
            this.selection.last = $(e.target);
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
            if (curr_td.index() < this.selection.first.index()) {
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
        }
    },
    clear_selection: function() {
        $('#current-user-row .highlighted').removeClass("highlighted selection-first selection-last");
        this.selection = {first: null, last: null}
    },
    render: function() {
    }
});



