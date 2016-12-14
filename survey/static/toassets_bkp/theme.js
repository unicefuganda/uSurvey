/*
Theme usurvey
 */
(function ($) {
    'use strict';
    
//========================
// Pretty Photo
//========================
    if ($(".popgals").length > 0) {
        $('.popgals').magnificPopup({
            type:'image',
            gallery:{
                enabled:true
            }
        });
    }
//=======================================================
// Gallery Mixing
//=======================================================
    if ($('#mixer').length > 0)
    {
        $('#mixer').themeWar();
    }
//=======================================================
// Circle Bar
//=======================================================
    if ($('.singleSkill').length > 0) {
        $('.singleSkill').appear(function () {
            $(".cmskill").each(function () {
                var pint = $(this).attr('data-skills');
                var decs = pint * 100;
                var grs = $(this).attr('data-gradientstart');
                var gre = $(this).attr('data-gradientend');

                $(this).circleProgress({
                    value: pint,
                    startAngle: -Math.PI / 4 * 2,
                    fill: {gradient: [[grs, 1], [gre, .2]], gradientAngle: Math.PI / 4 * 2},
                    lineCap: 'round',
                    thickness: 22,
                    animation: {duration: 1800},
                    size: 270
                }).on('circle-animation-progress', function (event, progress) {
                    $(this).find('strong').html(parseInt(decs * progress) + '<span>%</span>');
                });
            });
        });
    }
    //=======================================================
    // Portfolio Hover
    //=======================================================
    if ($('.folioImg').length > 0) {
        $(' .folioImg').each(function () {
            $(this).hoverdir({
                hoverDelay: 90
            });
        });
    }
    //=======================================================
    // Contact Map
    //=======================================================
    if ($("#map").length > 0)
    {
        var lat = $("#map").attr('data-latitude');
        var lang = $("#map").attr('data-longitude');
        var marker = $("#map").attr('data-marker');
        var map;
        map = new GMaps({
            el: '#map',
            lat: lat,
            lng: lang,
            scrollwheel: false,
            zoom: 18,
            zoomControl: false,
            panControl: false,
            streetViewControl: false,
            mapTypeControl: false,
            overviewMapControl: false,
            clickable: false
        });
        
        var image = '';
        map.addMarker({
            lat: lat,
            lng: lang,
            icon: marker,
            animation: google.maps.Animation.DROP,
            verticalAlign: 'center',
            horizontalAlign: 'center'
        });
    }
    
    //=======================================================
    // Mobile Menu
    //=======================================================
    $(".menuButton").on('click', function () {
        $(".mainMenu > ul").slideToggle('slow');
        $(this).toggleClass('active');
    });
    if ($(window).width() <= 991)
    {
        $("ul li.hasChild > a").on('click', function (e) {
            e.preventDefault();
            $(this).next('.dropSub').slideToggle('slow');
            $(this).next('.dropMenu').slideToggle('slow');
        });
    }
    $(".menuButton").on('click', function () {
        $(".innerMenu > ul").slideToggle('slow');
        $(this).toggleClass('active');
    });
    //=======================================================
    // Color Preset
    //=======================================================
    if ($(".presetArea").length > 0)
    {
        var switchs = true;
        $("#switches").on('click', function (e) {
            e.preventDefault();
            if (switchs)
            {
                $(this).addClass('active');
                $(".presetArea").animate({'left': '0px'}, 400);
                switchs = false;
            }
            else
            {
                $(this).removeClass('active');
                $(".presetArea").animate({'left': '-290px'}, 400);
                switchs = true;
            }
        });

        $(".patterns a").on('click', function (e) {
            e.preventDefault();
            var bg = $(this).attr('href');

            if ($("#boxLayout").hasClass('active'))
            {
                //alert(bg);
                $('.patterns a').removeClass('active');
                $(this).addClass('active');
                $('body').removeClass('bgOne bgTwo bgThree bgFour bgFive');
                $('body').addClass(bg);
            }
            else
            {
                alert('Please, active box layout First.');
            }

        });

        $(".accentColor a").click(function (e) {
            e.preventDefault();
            var color = $(this).attr('href');
            $(".accentColor a").removeClass('active');
            $(this).addClass('active');
            $("#topbiz-colors-css").attr('href', css_url+'/colorpreset/' + color + '.css');
        });
    }
    //=======================================================
    // Fixed Header 
    //=======================================================
    if ($(".headerArea").length > 0)
    {
        $(window).on('scroll', function () {
            if ($(window).scrollTop() > 500)
            {
                $(".headerArea").addClass('headerFix animated fadeInUp1');
            }
            else
            {
                $(".headerArea").removeClass('headerFix animated fadeInUp1');
            }
        });
    }
    else
    {
        $(window).on('scroll', function () {
            if ($(window).scrollTop() > 170)
            {
                $(".headerArea").addClass('headerFix animated fadeInUp1');
            }
            else
            {
                $(".headerArea").removeClass('headerFix animated fadeInUp1');
            }
        });
    }
    //========================================================
    // Fun Fact
    //========================================================
    $('.singleFacts').appear(function () {
        $('.mycounter').each(function () {
            var $this = $(this);
            jQuery({Counter: 0}).animate({Counter: $this.attr('data-counter')}, {
                duration: 6000,
                easing: 'swing',
                step: function () {
                    var num = Math.ceil(this.Counter).toString();
                    if (Number(num) > 999) {
                        while (/(\d+)(\d{3})/.test(num)) {
                            num = num.replace(/(\d+)(\d{3})/, '<span>' + '$1' + '</span>' + '$2');
                        }
                    }
                    $this.html(num);
                }
            });
        });
    });
    //========================
    // Back To Top
    //========================
    if ($("#backto").length > 0)
    {
        $("#backto").on('click', function (e) {
            e.preventDefault();
            $('html, body').animate({scrollTop: 0}, 1000);
        });
    }
    //========================
    // WOW INIT
    //========================
    if ($(window).width() > 767)
    {
        var wow = new WOW({
            mobile: false
        });
        wow.init();
    }
    //========================
    // Image Carousel
    //========================
    if ($(".caroselArea").length > 0)
    {
        // home page slider 
        $('.imageCaros').slick({
            centerMode: true,
            centerPadding: '80px',
            slidesToShow: 3,
            autoplay: true,
            autoplaySpeed: 5000,
            responsive: [
                {
                    breakpoint: 1024,
                    settings: {
                        slidesToShow: 3,
                        slidesToScroll: 3,
                        infinite: true
                    }
                },
                {
                    breakpoint: 600,
                    settings: {
                        slidesToShow: 2,
                        slidesToScroll: 2
                    }
                },
                {
                    breakpoint: 480,
                    settings: {
                        slidesToShow: 1,
                        slidesToScroll: 1
                    }
                }
            ]
        });
    }
    
    //========================
    // Loader
    //========================
    $(window).load(function () {
        if ($(".loaderWrap").length > 0)
        {
            $(".loaderWrap").delay(500).fadeOut("slow");
        }
    });
    
})(jQuery);
