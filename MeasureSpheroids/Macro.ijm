open("/Volumes/CHRISTA/spheroids/HT29_220322_4x_spheroid_za_0005_TRANS.tiff");	
selectWindow("HT29_220322_4x_spheroid_za_0005_TRANS.tiff");
run("Duplicate...", " ");
run("Gaussian Blur...", "sigma=220");
run("Calculator Plus", "i1=HT29_220322_4x_spheroid_za_0005_TRANS.tiff i2=HT29_220322_4x_spheroid_za_0005_TRANS-1.tiff operation=[Divide: i2 = (i1/i2) x k1 + k2] k1=182 k2=0 create");
run("Gaussian Blur...", "sigma=6");
setAutoThreshold("MaxEntropy");
setThreshold(70, 149);
run("Convert to Mask");
run("Fill Holes");

// Measure the size of the spheroid
Stack.setXUnit("µm");
run("Properties...", "channels=1 slices=1 frames=1 pixel_width=1.52 pixel_height=1.52 voxel_depth=1.52");

run("Analyze Particles...", "size=10000-Infinity circularity=0.60-1.00 show=Outlines display exclude clear add");

roiManager("Select", 0);



// Display the Ferret Diameter 
	// From https://imagej.nih.gov/ij/docs/menus/analyze.html
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