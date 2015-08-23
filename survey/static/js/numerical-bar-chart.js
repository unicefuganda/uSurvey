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
                        text: window.bar_chart_data['yAxis-text'],
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
                series: window.bar_chart_data['series']
            });
        });

    $('#bar-chart').css('height', window.bar_chart_data['length'] * 50)
};
