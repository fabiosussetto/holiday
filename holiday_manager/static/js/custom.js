/*
	Template: Leopard
	Author: Adrian Lampart
	URL: http://themeforest.net/user/yeroo
	JQUERY CUSTOM
*/


/* FLEXSLIDER */
$(window).load(function() {
    $('.flexslider').flexslider({
   					animation: "slide",              //String: Select your animation type, "fade" or "slide"
					pauseOnAction: true,            //Boolean: Pause the slideshow when interacting with control elements, highly recommended.
					pauseOnHover: false,            //Boolean: Pause the slideshow when hovering over slider, then resume when no longer hovering
					touch: true,                    //{NEW} Boolean: Allow touch swipe navigation of the slider on touch-enabled devices
					controlNav: true,               //Boolean: Create navigation for paging control of each clide? Note: Leave true for manualControls usage
					directionNav: true,             //Boolean: Create navigation for previous/next navigation? (true/false)
					slideshowSpeed: 7000,           //Integer: Set the speed of the slideshow cycling, in milliseconds
					animationSpeed: 600,            //Integer: Set the speed of animations, in milliseconds
	
	});
});


/* NIVO SLIDER */
$(window).load(function() {
	$('#nivo').nivoSlider({
				directionNav: true,
				controlNav: false,
				effect: 'sliceDownRight',
				effect: 'random',
				slices: 15,
				boxCols: 8,
				boxRows: 4,
				animSpeed: 500,
				pauseTime: 3000,
				startSlide: 0,
				pauseOnHover: true,
				randomStart: false,
			});
}); 


/* NAV */
$(document).ready(function(){
	$('nav ul').superfish({
			speed: 300,
			delay: 150,
			autoArrows: false,		
		});
});


/* NAV ELEMENTS */
$(document).ready(function() {
	var arrowDown = '<i class="icon-chevron-down"></i>',
		arrowRight = '<i class="icon-chevron-right"></i>'
    //$('li:has(ul)').children('a').append(arrowDown);
	$('ul ul li i').remove();
	//$('ul ul li:has(ul)').children('a').append(arrowRight);
	
	var span = '<span class="respList">&#8212;</span>'
	$('li ul li').children('a').prepend(span,' ');
	$('ul ul ul li span').remove();
	$('li ul ul li').children('a').prepend(span,span,'');
	$('ul ul ul ul li span').remove();
	$('li ul ul ul li').children('a').prepend(span,span,span,'');
});

$(document).ready(function(){
    var $loader = $('#content-overlay');
    
    var get_page = function(url) {
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
    
});


