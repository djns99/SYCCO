// X1 Y1 X2 Y2 in percentages
var boxes = [];

// List of colours for boxes
const colour_palette = ["lime", "magenta", "red", "yellow", "green", "aqua", "orange"]

//List of labels and corresponding colours
var option_mappings = {}
const label_selection = document.getElementById("labelSelection");
for(var i = 0; i < label_selection.options.length; i++)
{
    option = label_selection.options[i].value
    option_mappings[option] = colour_palette[i % colour_palette.length]
}

// Get canvas
const canvas = document.getElementById("drawingCanvas");
// Fit to correct size
fitToContainer(canvas);

// Canvas context
var ctx = undefined;
// Background image object
var background = new Image();
// Canvas aspect ratio
var aspect_ratio = undefined;
// Name of the file being labelled
var filename = undefined


// Reset canvas on resize to new image
function reset_canvas(url)
{
  filename = url.split('/').pop()
  // Get updated context
  ctx = canvas.getContext("2d");
  // Set background image
  background.src = url;
  // Scale canvas once image is loaded
  background.onload = function(){
    aspect_ratio = background.width / background.height;
    fitToContainer(canvas)
    ctx.drawImage(background, 0,0, canvas.width, canvas.height);
  }
  // Reset bounding boxes
  boxes = []
}

function send_labels(json)
{

    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if(this.readyState == 4)
        {
            if(this.status < 200 || this.status >= 300)
            {
                alert("Internal error occurred. Failed to save labels.")
                return
            }
            
            location.reload(true)
        }
    };
    xhttp.open("POST", "/submit_labels", true)
    xhttp.setRequestHeader("Content-type", "application/json")
    xhttp.send(json)

}

function save_labels()
{
    // Check image is selected
    if(!ctx)
    {
        alert("Please select image")
        return;
    }

    if(boxes[boxes.length - 1].length !== 5)
    {
        boxes.pop();
    }

    if(boxes.length == 0)
    {
        var res = confirm("You have not labelled anything. Do you wish to continue?");
        if(!res)
        {
            return;
        }
    }

    var output = [filename, boxes]
    var json = JSON.stringify(output)

    send_labels(json)

    boxes = []
    redraw();
}

function create_label()
{
    textbox = document.getElementById("label_name")
    new_name = textbox.value
    if(new_name in label_selection.options)
    {
        alert("Label name already exists")
    }

    for(var option_idx in label_selection.options)
    {
        if(new_name === label_selection.options[option_idx].value)
        {
            alert("Label name already exists")
            return
        }
    }


    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if(this.readyState == 4)
        {
            if(this.status < 200 || this.status >= 300)
            {
                alert("Internal error occurred. Failed to save labels.")
                return
            }

            var option = document.createElement("option");
            option.text = new_name;
            label_selection.add(option);

            option_mappings[new_name] = colour_palette[(label_selection.options.length - 1) % colour_palette.length]
            textbox.value = ""
        }
    };
    xhttp.open("POST", "/create_label", true)
    xhttp.setRequestHeader("Content-type", "text/plain")
    xhttp.send(new_name)
}

// Fit the canvas to width with correct aspect ratio
function fitToContainer(canvas){
  // Set css tp fill width of screen
  canvas.style.width ='100%';
  if(aspect_ratio === undefined)
  {
    canvas.style.height='100%';
  }
  else
  {
    canvas.style.height="";
  }
  // Set internal sizes
  canvas.width  = canvas.offsetWidth;
  if(aspect_ratio === undefined)
  {
    canvas.height = canvas.offsetHeight;
  }
  else
  {
    canvas.offsetHeight = canvas.width / aspect_ratio;
    canvas.height = canvas.width / aspect_ratio;
  }
}

// Ensure coordinate are top-left, bottom-right
function sort_coords(box) {
  // Left
  x1 = Math.min(box[0], box[2])
  // Right
  x2 = Math.max(box[0], box[2])
  // Top
  y1 = Math.min(box[1], box[3])
  // Bottom
  y2 = Math.max(box[1], box[3])
  return [x1, y1, x2, y2]
}

// Update the canvas
function redraw()
{
  // Clear canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  // Redraw background
  ctx.drawImage(background,0,0, canvas.width, canvas.height);
  // Loop over all bounding boxes
  for(var box_idx in boxes)
  {
    box = boxes[box_idx]
    // Check box is finished
    if(box.length != 5)
    {
      continue
    }
    // Convert from percentage to absolute coords
    x1 = box[0] * canvas.width
    y1 = box[1] * canvas.height
    x2 = box[2] * canvas.width
    y2 = box[3] * canvas.height
    // Get label
    label = box[4]

    // Draw box
    ctx.beginPath();
    ctx.lineWidth="2";
    ctx.strokeStyle=option_mappings[label];
    ctx.fillStyle=option_mappings[label];
    ctx.rect(x1, y1 -8, x2 - x1, 8);
    ctx.fill();
    ctx.rect(x1, y1, x2 - x1, y2 - y1);
    ctx.stroke();

    // Print label
    ctx.fillStyle="black";
    ctx.fillText(label, x1, y1);
  }
}

// Get mouse click
canvas.onmousedown = function(mouseEvent){
  // Check image is selected
  if(!ctx)
  {
    alert("Please select image")
    return
  }
  
  if(label_selection.options.length == 0)
  {
    alert("Please select a label");
    return
  }

  // Some copy paste code to find mouse position in canvas space
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

  // Convert coordinate to percentage of width
  xpercent = xpos / canvas.offsetWidth;
  ypercent = ypos / canvas.offsetHeight;
  // Add to boxes array
  if(boxes.length > 0 && boxes[boxes.length - 1].length == 2)
  {
    // Last two coords
    boxes[boxes.length - 1] = sort_coords(boxes[boxes.length - 1].concat(xpercent, ypercent));
    boxes[boxes.length - 1].push(label_selection.options[label_selection.selectedIndex].value)
  }
  else {
    // Start new box
    boxes.push([xpercent, ypercent])
  }

  // Draw the new box
  redraw()
}

// Adjust canvas dimensions on screen resize
canvas.onresize = fitToContainer(canvas)

// Undo drawing last box
function undo()
{
    if(boxes.length > 0)
    {
      boxes.pop()
      redraw();
    }
}

// Get ctrl+z for undo
document.onkeydown = function ()
{
  var evtobj = window.event? event : e
  if (evtobj.keyCode == 90 && evtobj.ctrlKey)
  {
    undo();
  }
}
