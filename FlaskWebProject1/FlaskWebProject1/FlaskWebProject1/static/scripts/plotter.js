
$(document).ready(function () {
    var j = "{{item}}"
    console.log(j)
    $('#chart_ID').highcharts({
        chart: chart,
        title: title,
        xAxis: xAxis,
        yAxis: yAxis,
        series: series
    });
});