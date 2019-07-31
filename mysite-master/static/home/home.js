        // 图表配置
        var options = {
            chart: { type: 'line' },  // 指定图表的类型，默认是折线图（line）
            title: { text: null },  // 标题
            xAxis: {
                categories: {{ dates|safe }},  // x 轴分类
                tickmarkPlacement: 'on',  // 以点来标出坐标
                title: { text: '前7日阅读量变化' },
            },
            yAxis: {
                title: { text: null },
                labels:{ enabled: false },
                gridLineDashStyle: 'Dash',  // 虚线
            },
            series: [{     // 数据列
                name: '阅读量',                        // 数据列名
                data:  {{ read_nums }}                  // 数据
            }],
            // 在线上显示数量
            plotOptions: {
                line: {
                    dataLabels: {
                        enabled: true
                    }
                }
            },
            legend: { enabled: false },
            credits: { enabled: false },  // 去掉版权信息
        };
        // 图表初始化函数
        var chart = Highcharts.chart('container', options);
