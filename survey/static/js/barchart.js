;
if (window.bar_chart_data) {
    $(function () {
            $('#bar-chart').highcharts({
                chart: {
                    type: 'bar'
                },
                title: {
                    text: window.bar_chart_data['title-text']
                },
                xAxis: {
                    categories: window.bar_chart_data['xAxis-categories'],
                    title: {
                        text: window.bar_chart_data['xAxis-text']
                    }
                },
                yAxis: {
                    min: 0,
                    title: {
                        text: 'Percentage',
                        align: 'high'
                    },
                    labels: {
                        overflow: 'justify'
                    }
                },
                tooltip: {
                    valueSuffix: ' %'
                },
                plotOptions: {
                    bar: {
                        dataLabels: {
                            enabled: true
                        }
                    }
                },
                legend: {
                    layout: 'vertical',
                    align: 'right',
                    verticalAlign: 'top',
                    x: -40,
                    y: 100,
                    floating: true,
                    borderWidth: 1,
                    backgroundColor: '#FFFFFF',
                    shadow: true
                },
                credits: {
                    enabled: false
                },
                series: [{
                    name: window.bar_chart_data['series-name'],
                    data: window.bar_chart_data['series-data']
                }]
            });
        });

    $('#bar-chart').css('height', window.bar_chart_data['series-data'].length * 50)
};
