(function($) {
    "use strict";
    function main() {
        mobilecheck();
        mdselect();
        Learning();
        scrollStyle();

        $(".feature-slider").owlCarousel({
            autoPlay: 10000,
            items: 4,
            itemsDesktop : [1199,4],
            itemsDesktopSmall : [979,3],
            itemsTablet: [768,2],
            itemsTabletSmall: [600,1],
            slideSpeed: 300,
            navigation: true,
            pagination: false,
            navigationText: ["<i class='fa fa-angle-left'></i>", "<i class='fa fa-angle-right'></i>"]
        });

        $('.view-grid').on('click', function() {
            $('.categories-content .content').attr('class', 'content grid');
            $('.grid').addClass('fade-1');
            $('.list').removeClass('fade-2');
            $(this).addClass('active');
            $('.view-list').removeClass('active');
        });
        $('.view-list').on('click', function() {
            $('.categories-content .content').attr('class', 'content list');
            $('.list').addClass('fade-2');
            $('.grid').removeClass('fade-1');
            $(this).addClass('active');
            $('.view-grid').removeClass('active');
        });


        /*==============================
            Account info
        ==============================*/

        var $toggleList = $('.list-account-info .list-item .toggle-list');
        $('html').on('click', function() {
            $toggleList.stop().removeClass('toggle-message-add');
            $('.list-account-info .item-click').stop().removeClass('active-ac');
        });
        $('.list-account-info .list-item').on('click', function(event) {
            event.stopPropagation();
        });
        $('.list-account-info .item-click').on('click', function(event) {
            if ($(this).hasClass('active-ac') == false) {
                $('.list-account-info .item-click').removeClass('active-ac');
                $toggleList.stop().removeClass('toggle-message-add');
            }
            $(this).toggleClass('active-ac');
            $(this).siblings('.toggle-list')
                .stop()
                .toggleClass('toggle-message-add');
            
        });

        $.each($('.content-bar'), function() {
            var widthList = $(this).find('li').outerWidth(),
                totalList = $(this).find('li').length;
            $(this).find('ul').width(widthList * totalList + 20);
        });
        

        /*==============================
            PROGRESS BAR
        ==============================*/
        $('.current-progress').appear(function () {
            $('.current-progress .progress-run').addClass('progress-run-add');
            var percent = $('.current-progress .count').text();
            $('.progress-run-add').width(percent);
        });


        /*==============================
            PERCENT LEARN
        ==============================*/
        $('.percent-learn').appear(function () {
            $(this)
                .siblings('.percent-learn-bar')
                    .find('.percent-learn-run')
                        .addClass('percent-learn-run-add');
            var percentLearn = $(this).text();
            var context = $(this).siblings('.percent-learn-bar').find('.percent-learn-run-add');
            context.width(percentLearn);
        });


        /*==============================
            CHECKOUT
        ==============================*/
        var current_fs, next_fs, previous_fs;
        var left, opacity, scale;
        var animating;
        $(".form-checkout .next").on('click', function() {
            if(animating) return false;
            animating = true;
            
            current_fs = $(this).closest('fieldset');
            next_fs = $(this).closest('fieldset').next();
            
            $(".form-checkout #bar li").eq($("fieldset").index(next_fs)).addClass("active");
            
            //show the next fieldset
            next_fs.show();
            //hide the current fieldset with style
            current_fs.animate({opacity: 0}, {
                step: function(now, mx) {
                    left = (now * 50)+"%";
                    opacity = 1 - now;
                    current_fs.css({'opacity': '0'});
                    next_fs.css({'left': left, 'opacity': opacity});
                }, 
                duration: 800, 
                complete: function(){
                    current_fs.hide();
                    animating = false;
                }, 
                //this comes from the custom easing plugin
                easing: 'easeInOutBack'
            });
        });

        $(".submit").on('click', function() {
            return false;
        });
        formCheckoutCal();

        $('#page-wrap').append('<div class="overlayForm"></div>');
        $('.take-this-course').on('click', function() {
            $('.form-checkout, .overlayForm').fadeIn(400);
            return false;
        });
        
        $('.closeForm').on('click', function() {
            $('.form-checkout, .overlayForm').fadeOut(400);
        });
        $('.closeForm').click();

        /*==============================
            TABS STYLE LINE
        ==============================*/
        if ($('.nav-tabs').length) {
            $.each($('.nav-tabs'), function() {
                var tabsItem = $(this).find('a'),
                    tabs = $(this),
                    leftActive = tabs.find('.active').children('a').position().left,
                    widthActive = tabs.find('.active').children('a').width();
                tabs.append('<li class="tabs-hr"></li>');
                $('.tabs-hr').css({
                    left: leftActive,
                    width: widthActive
                });
                tabsItem.on('click', function() {
                    var left = $(this).position().left,
                        width = $(this).width();
                    $('.tabs-hr').animate({
                        left: left,
                        width: width
                    }, 500, 'easeInOutExpo');
                });
            });
        }

        /*==============================
            FOOTER STYLE 2
        ==============================*/
        var $footerStyle2 = $('footer#footer.footer-style-2'),
            heightFooter =  $footerStyle2.height();
        $footerStyle2.appendTo('body');
        $footerStyle2.siblings('#page-wrap').css('marginBottom', heightFooter);


        $('.question-sidebar ul, .list-message, .list-notification').wrap('<div class="list-wrap"></div>');
    }
    /*==============================
        Mobile check
    ==============================*/
    function mobilecheck() {
        if( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ) {
            return false;
        }
        return true;
    }

    function formCheckoutCal() {
        var heightWindow = $(window).height(),
            heightForm = $('.form-checkout .container').height(),
            formMiddle = (heightWindow - heightForm) / 2;
        $('.form-checkout').css('top', formMiddle);
        $('.form-checkout .form-body').height($(".form-checkout fieldset").height());
    }

    /*==============================
        MC SELECT
    ==============================*/
    function mdselect() {
        $('.mc-select').find('select.select').each(function() {
            var selected = $(this).find('option:selected').text();
            $(this)
                .css({'z-index':10,'opacity':0,'-khtml-appearance':'none'})
                .after('<span class="select">' + selected + '</span>' + '<i class="fa fa-angle-down"></i>')
                .change(function(){
                    var val = $('option:selected',this).text();
                    $(this).next().text(val);
                });
        });
    }

    /*==============================
        Learning
    ==============================*/
    function Learning() {
        var $navListBody = $('.top-nav-list').find('.list-item-body');
        var width = $navListBody.closest('.top-nav-list').width() - 1;
        $navListBody.width(width);
        if ($('.top-nav-list').children('li').hasClass('active')) {
            $('.learning-section')
                .toggleClass('learning-section-fly')
                .css('paddingRight', width);
        }
        $('.top-nav-list').find('.outline-learn, .discussion-learn, .note-learn').on('click', '> a', function(e) {
            e.preventDefault();
            if ($(this).parent().hasClass('active') == false) {
                $('.top-nav-list').children('li').removeClass('active');
            }
            $(this).parent().toggleClass('active');
            if ($(this).parent().hasClass('active')) {
                $('.learning-section')
                    .toggleClass('learning-section-fly')
                    .css('paddingRight', width);
            } else {
                $('.learning-section')
                    .removeClass('learning-section-fly')
                    .css('paddingRight', '0');
            }
        });
        $('html').on('click', function() {
            $navListBody.removeClass('item-fly');
            $navListBody.parent('li').removeClass('active');
            $('.learning-section')
                .removeClass('learning-section-fly')
                .css('paddingRight', '0');
        });
        $('.top-nav-list, .list-item-body').on('click', function(event) {
            event.stopPropagation();
        });
    }
    function setHeightRespon() {
        var windowHeight = $(window).height(),
            w = window.innerWidth;
        $('.learn-section').css('min-height', windowHeight);

        if (w < 992) {
            $('.question-content-wrap').find('.question-sidebar').height('auto');
            $('.question-content-wrap').find('.score-sb').find('.list-wrap').height('auto').css('max-height', '300px');
        } else if (w >= 992) {
            var height = $('.question-content-wrap').find('.question-content').height() + 30;
            var heightUl = height - 90;
            $('.question-content-wrap').find('.score-sb').find('.list-wrap').height(heightUl).css('max-height', 'none');
            $('.question-content-wrap').find('.question-sidebar').height(height);
        }
    }

    /*==============================
        SET HEIGHT MESSAGE SB
    ==============================*/
    function setHeightMessagesb() {
        if ($('.list-item-body').length) {
            var heightlist = $(window).height() - $('.list-item-body').css('margin-top').split('px')[0];
            $('.list-item-body').height(heightlist);
        }
    }

    /*==============================
        SCROLL STYLE
    ==============================*/
    function scrollbar() {
        var $scrollbar = $('.question-sidebar .list-wrap, .messages .list-wrap, .message-sb .list-wrap, .notification .list-wrap, .list-item-body, .table-wrap .tbody');
        $scrollbar.perfectScrollbar({
            maxScrollbarLength: 150,
        });
        $scrollbar.perfectScrollbar('update');

        $('.content-bar').perfectScrollbar({
            maxScrollbarLength: 150,
            suppressScrollY: true,
            useBothWheelAxes: true,
        });
        $('.content-bar').perfectScrollbar('update');
    }
    function scrollStyle() {
        scrollbar();
        $(window).on('load', function() {
            if ($('.content-bar').length > 0) {
                var  currentPosition =$('.content-bar').find('.current').position().left;
                var  prevCurrentWidth =$('.content-bar').find('.current').prev().width();
                setTimeout(function() {
                    $('.content-bar').animate({
                        scrollLeft: currentPosition - prevCurrentWidth
                    }, 400);
                }, 100);
            }
        });
    }

    function uploadFile() {
        $('.up-file').delegate('a', 'click', function(e) {
            e.preventDefault();
            $(this).siblings('input[type="file"]').trigger('click');
        });
        $('.up-file').delegate('input[type="file"]', 'change', function() {
            var nameFile = $(this).val().replace(/\\/g, '/').replace(/.*\//, '');
            $(this).siblings('input[type="hidden"]').val(nameFile);
            readURL(this);
        });
        function readURL(input) {
            if (input.files && input.files[0]) {
                var reader = new FileReader();
                reader.onload = function (e) {
                    $('.changes-avatar')
                        .find('img')
                            .attr('src', e.target.result)
                            .width(140);
                };
                reader.readAsDataURL(input.files[0]);
            }
        }
    }

    /*==========  Slider Home ==========*/
    function SliderHome(){
        if($('#slide-home').length){
            $('#slide-home').owlCarousel({
                autoPlay: 10000,
                navigation: false,
                pagination: true,
                singleItem: true,
                mouseDrag:false,
                addClassActive:true,
                transitionStyle:'fade'
            });
        }
    }

    /*==========  Resize Slider Home ==========*/
    function ResizeSliderHome() {
        if($('#slide-home')) {
            var parentWidth = $('.slide-cn').innerWidth(),
              imgWidth = $('.item-inner').width(),
              imgHeight = $('.item-inner').height(),
              scale = parentWidth/imgWidth,
              ratio = imgWidth/imgHeight,
              heightItem = parentWidth/ratio;

          $('.slide-item').css({'height': heightItem});

          if ($(window).width() <= 1200) {

            $('.item-inner').css({
              '-webkit-transform': 'scale(' + scale + ')',
              '-moz-transform': 'scale(' + scale + ')',
              '-ms-transform': 'scale(' + scale + ')',
              'transform': 'scale(' + scale + ')'
            });

          } else {

            $('.item-inner').css({
                '-webkit-transform': 'scale(1)',
                '-moz-transform': 'scale(1)',
                '-ms-transform': 'scale(1)',
                'transform': 'scale(1)'
            });

          }
      }
    }
         

    $(document).ready(function() {
        main();
        setHeightRespon();
        uploadFile();
        setHeightMessagesb();
        scrollbar();
        $('.nav-tabs').wrap('<div class="nav-tabs-wrap"></div>');

        if (window.innerWidth < 1200) {
            $('.menu-item-has-children').on('click', '> a', function(evt) {
                evt.preventDefault();
                $(this).next().slideToggle(300);
                $(this).toggleClass('mobile-active');
            });
            $('.open-menu').on('click', function() {
                $(this).toggleClass('toggle-active');
                $('.navigation .menu, .search-box').slideToggle(300);
            });
            $('html').on('click', function() {
                $('.open-menu').removeClass('toggle-active');
                $('.navigation .menu, .search-box').slideUp(300);
            });
            $('.navigation .menu, .open-menu, .search-box').on('click', function(evt) {
                evt.stopPropagation();
            });
        }
    });
    $(window).load(function() {
        ResizeSliderHome();
    });

    $(window).on('resize', function() {
        setHeightRespon();
        setHeightMessagesb();
        scrollbar();
        SliderHome();
        formCheckoutCal();
        ResizeSliderHome();
    }).trigger('resize');;
    

})(jQuery);