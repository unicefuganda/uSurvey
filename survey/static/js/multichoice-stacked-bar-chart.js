;
if (window.multi_choice_stacked_bar_chart_data) {
  $(function () {
          $('#multichoice-stacked-bar-chart').highcharts({
              chart: {
                  type: 'bar'
              },
              title: {
                  text: window.multi_choice_stacked_bar_chart_data['title-text']
              },
              xAxis: {
                  categories: window.multi_choice_stacked_bar_chart_data['xAxis-categories'],
                  title: {
                    text: window.multi_choice_stacked_bar_chart_data['xAxis-text']
                  }
              },
              yAxis: {
                  min: 0,
                  title: {
                      text: window.multi_choice_stacked_bar_chart_data['yAxis-text']
                  }
              },
              legend: {
                  backgroundColor: '#FFFFFF',
                  reversed: true
              },
              plotOptions: {
                  series: {
                      stacking: 'normal'
                  }
              },
              series: window.multi_choice_stacked_bar_chart_data['series']
          });

          $('#multichoice-stacked-bar-chart').css('height', window.multi_choice_stacked_bar_chart_data['length'] * 50)
      });
};