;
if (window.simple_indicator_bar_chart) {
  $(function () {
          $('#simple_indicator_bar_chart').highcharts({
              chart: {
                  type: 'column'
              },
              title: {
                  text: window.simple_indicator_bar_chart['title-text']
              },
              xAxis: {
                  categories: window.simple_indicator_bar_chart['xAxis-categories']
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
              series: window.simple_indicator_bar_chart['series']
          });
      });
};