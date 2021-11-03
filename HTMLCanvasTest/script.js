var canvas = document.getElementById("myCanvas");
fitToContainer(canvas);

var ctx = canvas.getContext("2d");
var background = new Image();
background.src = "image.jpg";
console.log(background)
background.onload = function(){
    ctx.drawImage(background,0,0, canvas.width, canvas.height);
}


function fitToContainer(canvas){
  // Make it visually fill the positioned parent
  canvas.style.width ='100%';
  canvas.style.height='100%';
  // ...then set the internal size to match
  canvas.width  = canvas.offsetWidth;
  canvas.height = canvas.offsetHeight;
}

// X1 Y1 W H
var boxes = [];

function sort_coords(box) {
  x1 = Math.min(box[0], box[2])
  x2 = Math.max(box[0], box[2])
  y1 = Math.min(box[1], box[3])
  y2 = Math.max(box[1], box[3])
  return [x1, y1, x2, y2]
}

function redraw()
{
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(background,0,0, canvas.width, canvas.height);
  console.log(boxes)
  for(var box in boxes)
  {
    box = boxes[box]
    if(box.length != 4)
    {
      continue
    }
    console.log(box)
    x1 = box[0]
    y1 = box[1]
    x2 = box[2]
    y2 = box[3]
    ctx.beginPath();
    ctx.lineWidth="4";
    ctx.strokeStyle="lime";
    ctx.rect(x1, y1, x2 - x1, y2 - y1)
    ctx.stroke();
  }
}

canvas.onmousedown = function(mouseEvent){

  var obj = canvas
  var obj_left = 0;
  var obj_top = 0;
  var xpos;
  var ypos;
  while (obj.offsetParent)
  {
    obj_left += obj.offsetLeft;
    obj_top += obj.offsetTop;
    obj = obj.offsetParent;
  }
  if (mouseEvent)
  {
    //FireFox
    xpos = mouseEvent.pageX;
    ypos = mouseEvent.pageY;
  }
  else
  {
    //IE
    xpos = window.event.x + document.body.scrollLeft - 2;
    ypos = window.event.y + document.body.scrollTop - 2;
  }
  xpos -= obj_left;
  ypos -= obj_top;
  console.log(xpos + " " + ypos);

  if(boxes.length > 0 && boxes[boxes.length - 1].length == 2)
  {
    boxes[boxes.length - 1] = sort_coords(boxes[boxes.length - 1].concat(xpos, ypos))
  }
  else {
    boxes.push([xpos, ypos])
  }


  redraw()
}

document.onkeydown = function ()
{
  var evtobj = window.event? event : e
  if (evtobj.keyCode == 90 && evtobj.ctrlKey)
  {
    boxes.pop()
    redraw();
  }
}
