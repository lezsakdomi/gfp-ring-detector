// ask for a file to be imported
fileName = File.openDialog("Select the file to import");
allText = File.openAsString(fileName);

// parse text by lines
text = split(allText, "\n");

// define array for points
var xpoints = newArray;
var ypoints = newArray;

// loading and parsing each line
for (i = 0; i < (text.length); i++){
   line = split(text[i]);
   setOption("ExpandableArrays", true);
   xpoints[i] = parseInt(line[0]);
   ypoints[i] = parseInt(line[1]);
}

// show the points in the image
makeSelection("point", xpoints, ypoints);
