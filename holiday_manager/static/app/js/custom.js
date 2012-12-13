$(document).ready(function(){
    var $loader = $('#content-overlay');
    
    window.get_page = function(url) {
        $loader.show();
        $.get(url, function(template) {
            window.history.replaceState({}, document.title, url);
            $('#content').html(template);
            $loader.hide();
        });
    }
    
    var submit_form = function($form) {
        $loader.show();
        $.post($form.attr('action'), $form.serialize(), function(template) {
            $('#content').html(template);
            $loader.hide();
        });
    }
    
    $('#topnav > li a').not('.dropdown-toggle').click(function(e) {
        e.preventDefault();
        var $link = $(this);
        $('#topnav li.active').removeClass('active');
        $link.closest('li').addClass('active');
        get_page($link.attr('href'));
    });
    
    $('body').on('click', 'a.ajax', function(e) {
        e.preventDefault();
        var $link = $(this);
        get_page($link.attr('href'));
    });
    
    $('body').on('submit', 'form.ajax', function(e) {
        e.preventDefault();
        var $form = $(this);
        submit_form($form);
    });
    
    $('body').on('click', '.pagination a', function(e) {
        e.preventDefault();
        var $link = $(this);
        $('.pagination .active').removeClass('active');
        $link.closest('li').addClass('active');
        get_page($link.attr('href'));
    });
    
    $('body').on('click', '.nav-tabs a, .tab-link', function(e) {
        e.preventDefault();
        var $link = $(this);
        
        if ($link.siblings('.active').length) {
            $link.siblings('.active').removeClass('active');
            $link.addClass('active');
        } else {
            $link.closest('.nav-tabs').find('li.active').removeClass('active');
            $link.closest('li').addClass('active');
        }
        
        var $loader = $('#tab-overlay');
        var url = $link.attr('href');
        $loader.show();
        $.get(url, {src: 'tab'}, function(template) {
            window.history.replaceState({}, document.title, url);
            $('.tab-content').html(template);
            $loader.hide();
        });
    });
    
});