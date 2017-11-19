//  Theme Custom jquery file, 



"use strict";




// Prealoder
 function prealoader () {
   if ($('#loader').length) {
     $('#loader').fadeOut(); // will first fade out the loading animation
     $('#loader-wrapper').delay(350).fadeOut('slow'); // will fade out the white DIV that covers the website.
     $('body').delay(350).css({'overflow':'visible'});
  };
 }


// placeholder remove
function removePlaceholder () {
  if ($("input,textarea").length) {
    $("input,textarea").each(
            function(){
                $(this).data('holder',$(this).attr('placeholder'));
                $(this).on('focusin', function() {
                    $(this).attr('placeholder','');
                });
                $(this).on('focusout', function() {
                    $(this).attr('placeholder',$(this).data('holder'));
                });
                
        });
  }
}

// Time Picker
function timeSelect () {
  if ($(".timepicker").length) {
    $(".timepicker").timepicker();
  }
}

// Theme-banner slider 
function BannerSlider () {
  var banner = $("#theme-main-banner");
  if (banner.length) {
    banner.revolution({
      sliderType:"standard",
      sliderLayout:"auto",
      loops:true,
      delay:7000,
      navigation: {
         bullets: {
                  enable: true,
                  hide_onmobile: false,
                  style: "uranus",
                  hide_onleave: false,
                  direction: "vertical",
                  h_align: "center",
                  v_align: "bottom",
                  h_offset: 0,
                  v_offset: 135,
                  space: 8,
                  tmp: '<span class="tp-bullet-inner"></span>'
              }

      },
      responsiveLevels:[2220,1183,975,751],
                gridwidth:[1170,970,770,318],
                gridheight:[800,800,800,650],
                shadow:0,
                spinner:"off",
                autoHeight:"off",
                disableProgressBar:"on",
                hideThumbsOnMobile:"off",
                hideSliderAtLimit:0,
                hideCaptionAtLimit:0,
                hideAllCaptionAtLilmit:0,
                debugMode:false,
                fallbacks: {
                  simplifyAll:"off",
                  disableFocusListener:false,
                },
    });
  };
}

// Theme-banner slider Two
function BannerSliderTwo () {
  var banner = $("#theme-main-banner-two");
  if (banner.length) {
    banner.revolution({
      sliderType:"standard",
      sliderLayout:"auto",
      loops:true,
      delay:7000,
      navigation: {
         bullets: {
                  enable: true,
                  hide_onmobile: false,
                  style: "uranus",
                  hide_onleave: false,
                  direction: "vertical",
                  h_align: "center",
                  v_align: "bottom",
                  h_offset: 0,
                  v_offset: 135,
                  space: 8,
                  tmp: '<span class="tp-bullet-inner"></span>'
              }

      },
      responsiveLevels:[2220,1183,975,751],
                gridwidth:[1170,970,770,320],
                gridheight:[960,960,800,600],
                shadow:0,
                spinner:"off",
                autoHeight:"off",
                disableProgressBar:"on",
                hideThumbsOnMobile:"off",
                hideSliderAtLimit:0,
                hideCaptionAtLimit:0,
                hideAllCaptionAtLilmit:0,
                debugMode:false,
                fallbacks: {
                  simplifyAll:"off",
                  disableFocusListener:false,
                },
    });
  };
}


// Main Menu Function 
function themeMenu () {
  var menu= $("#mega-menu-holder");
  if(menu.length) {
    menu.menuzord({
      animation:"zoom-out"
    });
  }
}


// Fancybox 
function FancypopUp () {
  var popBox = $(".fancybox");
  if (popBox.length) {
      popBox.fancybox({
      openEffect  : 'elastic',
        closeEffect : 'elastic',
         helpers : {
            overlay : {
                css : {
                    'background' : 'rgba(0, 0, 0, 0.6)'
                }
            }
        }
    });
  };
}


// Service Slider 
function serviceSlider () {
  var sSlider = $ (".service-sldier");
  if(sSlider.length) {
    sSlider.owlCarousel({
        loop:true,
        nav:true,
        navText: ["",""],
        dots:false,
        lazyLoad:true,
        navSpeed:700,
        dragEndSpeed:1000,
        responsive:{
            0:{
                items:1
            },
            650:{
                items:2
            },
            992:{
                items:3
            }
        }
    })
  }
}


// Project Slider 
function projectSlider () {
  var pSlider = $ (".project-slider");
  if(pSlider.length) {
    pSlider.owlCarousel({
        loop:true,
        nav:true,
        navText: ["",""],
        dots:false,
        lazyLoad:true,
        navSpeed:700,
        dragEndSpeed:1000,
        responsive:{
            0:{
                items:1
            },
            600:{
                items:2
            },
            992:{
                items:3
            }
        }
    })
  }
}



// Testimonial Slider
function testimonialSlider () {
  var testimonial = $(".testimonial-slider");
  if(testimonial.length) {
    testimonial.owlCarousel({
        animateOut: 'fadeOutDown',
        loop:true,
        nav:false,
        navText:false,
        dots:true,
        autoplay:true,
        autoplayTimeout:15000,
        autoplaySpeed:900,
        lazyLoad:true,
        dotsSpeed:1000,
        dragEndSpeed:1000,
        smartSpeed:1000,
        items:1,
    })
  }
}


// Team SLider
function teamSlider () {
  var tSlider = $(".team-slider");
  if(tSlider.length) {
    tSlider.owlCarousel({
        loop:true,
        nav:false,
        dots:true,
        lazyLoad:true,
        autoplay:true,
        autoplayTimeout:8000,
        autoplaySpeed:900,
        dragEndSpeed:1000,
        responsive:{
            0:{
                items:1
            },
            600:{
                items:2
            }
        }
    })
  }
}


// Blog SLider
function blogSlider () {
  var blogcarousel = $(".blog-slider");
  if(blogcarousel.length) {
    blogcarousel.owlCarousel({
        loop:true,
        nav:true,
        navText: ["",""],
        dots:false,
        lazyLoad:true,
        navSpeed:700,
        autoplay:true,
        autoplayTimeout:15000,
        autoplaySpeed:900,
        dragEndSpeed:1000,
        responsive:{
            0:{
                items:1
            },
            768:{
                items:2
            }
        }
    })
  }
}

// Mixitup gallery
function mixitupGallery () {
  if ($("#mixitUp-item").length) {
    $("#mixitUp-item").mixItUp()
  };
}


// Scroll to top
function scrollToTop () {
  var scrollTop = $ (".scroll-top")
  if (scrollTop.length) {

    //Check to see if the window is top if not then display button
    $(window).on('scroll', function (){
      if ($(this).scrollTop() > 200) {
        scrollTop.fadeIn();
      } else {
        scrollTop.fadeOut();
      }
    });
    
    //Click event to scroll to top
      scrollTop.on('click', function() {
      $('html, body').animate({scrollTop : 0},1500);
      return false;
    });
  }
}



//Contact Form Validation
function contactFormValidation () {
  if($('.form-validation').length){
    $('.form-validation').validate({ // initialize the plugin
      rules: {
        name: {
          required: true
        },
        email: {
          required: true,
          email: true
        },
        sub: {
          required: true
        },
        category: {
          required: true
        },
        time: {
          required: true
        },
        message: {
          required: true
        }
      },
      submitHandler: function(form) {
                $(form).ajaxSubmit({
                    success: function() {
                        $('.form-validation :input').attr('disabled', 'disabled');
                        $('.form-validation').fadeTo( "slow", 1, function() {
                            $(this).find(':input').attr('disabled', 'disabled');
                            $(this).find('label').css('cursor','default');
                            $('#alert-success').fadeIn();
                        });
                    },
                    error: function() {
                        $('.form-validation').fadeTo( "slow", 1, function() {
                            $('#alert-error').fadeIn();
                        });
                    }
                });
            }
        });
  }
}

// Close suddess Alret
function closeSuccessAlert () {
  var closeButton = $ (".closeAlert");
  if(closeButton.length) {
      closeButton.on('click', function(){
        $(".alert-wrapper").fadeOut();
      });
      closeButton.on('click', function(){
        $(".alert-wrapper").fadeOut();
      })
  }
}


// Sticky header
function stickyHeader () {
  var sticky = $('.theme-main-menu'),
      scroll = $(window).scrollTop();

  if (sticky.length) {
    if (scroll >= 190) sticky.addClass('fixed');
    else sticky.removeClass('fixed');
    
  };
}



// Accordion panel
function themeAccrodion () {
  if ($('.theme-accordion > .panel').length) {
    $('.theme-accordion > .panel').on('show.bs.collapse', function (e) {
          var heading = $(this).find('.panel-heading');
          heading.addClass("active-panel");
          
    });
    
    $('.theme-accordion > .panel').on('hidden.bs.collapse', function (e) {
        var heading = $(this).find('.panel-heading');
          heading.removeClass("active-panel");
          //setProgressBar(heading.get(0).id);
    });

    $('.panel-heading a').on('click',function(e){
        if($(this).parents('.panel').children('.panel-collapse').hasClass('in')){
            e.stopPropagation();
        }
    });

  };
}


// DOM ready function
jQuery(document).on('ready', function() {
	(function ($) {
	   removePlaceholder ();
     timeSelect ();
     BannerSlider ();
     BannerSliderTwo ();
     themeMenu ();
     FancypopUp ();
     serviceSlider ();
     projectSlider ();
     testimonialSlider ();
     teamSlider ();
     blogSlider ();
     mixitupGallery ();
     scrollToTop ();
     contactFormValidation ();
     closeSuccessAlert ();
     themeAccrodion ();
  })(jQuery);
});


// Window load function
jQuery(window).on('load', function () {
   (function ($) {
		  prealoader ();
  })(jQuery);
 });


// Window scroll function
jQuery(window).on('scroll', function () {
  (function ($) {
    stickyHeader ();
  })(jQuery);
});
