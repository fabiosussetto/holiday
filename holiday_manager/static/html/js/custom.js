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

/* PORTFOLIO ITEM SLIDER */
$(window).load(function() {
	$('#itemSlider').nivoSlider({
				directionNav: true,
				pauseTime: 4000,
				effect: 'fade',	
	});
}); 

/* TWITTER WIDGET */
$(document).ready(function() { 
$(".tweet").tweet({
            username: "envato",
            join_text: null,
            avatar_size: null,
            count: 2,
			template: "{text}<br>{time}",
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
    $('li:has(ul)').children('a').append(arrowDown);
	$('ul ul li i').remove();
	$('ul ul li:has(ul)').children('a').append(arrowRight);
	
	var span = '<span class="respList">&#8212;</span>'
	$('li ul li').children('a').prepend(span,' ');
	$('ul ul ul li span').remove();
	$('li ul ul li').children('a').prepend(span,span,'');
	$('ul ul ul ul li span').remove();
	$('li ul ul ul li').children('a').prepend(span,span,span,'');
});

/* PORTFOLIO FILTER */
$(document).ready(function() {
  var $filterType = $('#filterOptions li.active a').attr('class');
  var $holder = $('ul.portfolioHolder');
  var $data = $holder.clone();
  $('#filterOptions li a').click(function(e) {
    $('#filterOptions li').removeClass('active');
    var $filterType = $(this).attr('class');
    $(this).parent().addClass('active');
    if ($filterType == 'all') {
      var $filteredData = $data.find('li');
    }
    else {
      var $filteredData = $data.find('li[data-type~=' + $filterType + ']');
    }
    $holder.quicksand($filteredData, {
      duration: 0,
    });
    return false;
  });
});


/* FORM VALIDATION JAVASCRIPT */
$(document).ready(function() {
	$('form#contact-form').submit(function() {
		$('form#contact-form .alert').remove();
		var hasError = false;
		$('.requiredField').each(function() {
			if(jQuery.trim($(this).val()) == '') {
            	var labelText = $(this).prev('span').text();
            	$(this).parent().append('<div class="alert alert-error">This field is required!</div>');
            	$(this).addClass('inputError');
            	hasError = true;
            } else if($(this).hasClass('email')) {
            	var emailReg = /^([\w-\.]+@([\w-]+\.)+[\w-]{2,4})?$/;
            	if(!emailReg.test(jQuery.trim($(this).val()))) {
            		var labelText = $(this).prev('span').text();
            		$(this).parent().append('<div class="alert alert-error">You entered an invalid email address!</div>');
            		$(this).addClass('inputError');
            		hasError = true;
            	}
            }
		});
		if(!hasError) {
			$('form#contact-form button#send').fadeOut('normal', function() {
				$(this).parent().append('');
			});
			var formInput = $(this).serialize();
			$.post($(this).attr('action'),formInput, function(data){
				$('form#contact-form').slideUp("fast", function() {
					$(this).before('<div class="alert alert-success">Your email was successfully sent!</div>');
				});
			});
		}

		return false;

	});
});


