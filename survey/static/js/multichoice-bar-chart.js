;
if (window.multi_choice_bar_chart_data) {
  $(function () {
          $('#multichoice-bar-chart').highcharts({
              chart: {
                  type: 'column'
              },
              title: {
                  text: window.multi_choice_bar_chart_data['title-text']
              },
              xAxis: {
                  categories: window.multi_choice_bar_chart_data['xAxis-categories']
              },
              yAxis: {
                  min: 0,
                  title: {
                      text: 'Percentage'
                  },
                  labels: {
                      overflow: 'justify'
                  }
              },
              tooltip: {
                  headerFormat: '<span style="font-size:10px">{point.key}</span><table>',
                  pointFormat: '<tr><td style="color:{series.color};padding:0">{series.name}: </td>' +
                      '<td style="padding:0"><b>{point.y:.1f} mm</b></td></tr>',
                  footerFormat: '</table>',
                  shared: true,
                  useHTML: true
              },
              plotOptions: {
                  column: {
                      pointPadding: 0.2,
                      borderWidth: 0
                  },
                  column: {
                      dataLabels: {
                          enabled: true
                      }
                  }
              },
              series: window.multi_choice_bar_chart_data['series']
          });
      });
};