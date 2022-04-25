#@File(label="Input directory", description="Select the directory with input images", style="directory") inputDir
#@File(label="Output directory", description="Select the output directory", style="directory") outputDir
#@Float(label="Resolution", description="Pixel resolution", value="1.52") resolution
#@Float(label="minSize", description="Minimum Spheroid size", value="10000") minSize
#@Float(label="minCircularity", description="Minimum Spheroid circularity", value="0.55") minCircularity
#@ String(label = "Threshold method", value = "MaxEntropy") thresMeth
#@Float(label="minimum", description="minumum threshold value", value="0") min
#@Float(label="maximum", description="maximum threshold value", value="132") max

// clean up first
close("*"); // close all images
roiManager("reset"); // empty the ROI manager
run("Clear Results"); // empty the results table

list = getFileList(inputDir);
d = newArray(list.length);

for (i=0; i<list.length; i++) {
		 
 showProgress(i+1, list.length);
 name = list[i];
 if(name.contains("tiff")) {
		 open(inputDir+File.separator+name);
		 run("8-bit");
		 
		 // Preprocess the data - Threshold the data
		 setAutoThreshold(thresMeth);
		 setThreshold(min, max);
		 run("Convert to Mask");
		 run("Fill Holes");
		 run("Erode");run("Erode");run("Erode");
		 run("Dilate");run("Dilate");run("Dilate");

		 // Measure the size of the spheroid
		 Stack.setXUnit("µm");
		 run("Properties...", "channels=1 slices=1 frames=1 pixel_width=resolution pixel_height=resolution voxel_depth=1");
		 run("Analyze Particles...", "size=minSize-Infinity circularity=minCircularity-1.00 show=Outlines display exclude clear add");
		 
		 if (roiManager("count")>0) {
		 roiManager("Select", 0); // Assumes one spheroid per image
		 
		 // Save the results image 1
		 selectWindow(name);
		 saveAs(outputDir + File.separator + substring(name, 0, lastIndexOf(name, ".")) + "_1_Mask.jpeg");
		 selectWindow("Drawing of " + name);
		 
		 // Display the Ferret Diameter: from https://imagej.nih.gov/ij/docs/menus/analyze.html
		 List.setMeasurements;
		 x1 = List.getValue("FeretX");
		 y1 = List.getValue("FeretY");
		 length = List.getValue("Feret") / 1.52;
		 degrees = List.getValue("FeretAngle");
		 if (degrees>90)
		     degrees -= 180; 
		 angle = degrees*PI/180;
		 x2 = x1 + cos(angle)*length;
		 y2 = y1 - sin(angle)*length;
		 setColor("red");
		 Overlay.drawLine(x1, y1, x2, y2);
		 Overlay.show();
		 showStatus("angle="+degrees);

		 // Save the results image 2
		 saveAs(outputDir + File.separator + substring(name, 0, lastIndexOf(name, ".")) + "_2_Ferret.jpeg");

		 // Save the value for later 
		 d[i] = length; 
		 } else {print("error: Could not measure a Spheroid" + name);}
//		 waitForUser;
		 roiManager("reset");
		 close("*");
		 }
 }
 
 // Export 


run("Clear Results"); // empty the results table
for (i=0; i<list.length; i++)
if(list[i].contains("tiff")) {
    setResult("Diameter", i, d[i]);
    setResult("Image", i, list[i]);
    updateResults();
    }


saveAs("Results", outputDir + File.separator + "ResultsSpheroidTest.csv");
selectWindow("Log");
saveAs("Text", outputDir + File.separator + "LogSpheroidTest.txt");

// Save some metadata
file = File.open(outputDir + File.separator + "MetaDataSpheroidTest.csv"); // display file open dialog
      
print(file, "Input directory,\""+ inputDir +"\"\n");
print(file, "Output directory,\""+ outputDir +"\"\n");
print(file, "Resolution,"+ resolution +"\n");
print(file, "minSize,"+ minSize +"\n");
print(file, "minCircularity,"+ minCircularity +"\n");
print(file, "Threshold method,"+ thresMeth +"\n");
print(file, "minimum,"+ min +"\n");
print(file, "maximum,"+ max +"\n");