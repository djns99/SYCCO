const aspect_ratio = 2

function resize_canvas(ctx)
{
    // Set css tp fill width of screen
    ctx.style.width ='100%';
    ctx.style.height="";

    // Set internal sizes
    ctx.width  = ctx.offsetWidth;
    ctx.offsetHeight = ctx.width / aspect_ratio;
    ctx.height = ctx.width / aspect_ratio;
}

function update_graph(run_ids, data_points, ctx)
{
    var myChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: run_ids,
          datasets: [{
            data: data_points,
            lineTension: 0,
            backgroundColor: 'transparent',
            borderColor: '#007bff',
            borderWidth: 4,
            pointBackgroundColor: '#007bff'
          }]
        },
        options: {
          scales: {
            yAxes: [{
              ticks: {
                beginAtZero: true
              }
            }]
          },
          legend: {
            display: false,
          }
        }
    });
}