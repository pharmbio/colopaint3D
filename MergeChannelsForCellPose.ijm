dir1 = getDirectory("Source");
dir2 = getDirectory("Destination");

list = getFileList(dir1);
Array.sort(list);
setBatchMode(true);

// Create the arrays first
blue = newArray(0);
gray = newArray(0);

// Get the blue and gray channel names
for (i = 0; i < list.length; i++) {
   file = list[i];
   if (startsWith(file, "Well-")) {
      if (endsWith(file, "HOECHST.ome.tiff")) {
         blue = Array.concat(blue, file); 
      } else if (endsWith(file, "WGA.ome.tiff")) { 
         gray = Array.concat(gray, file); 
      }
   } 
}

// A safeguard. If one channel image is missing, we would fail somewhere
if (blue.length != gray.length) {
   exit("Unequal number of blue and gray channels found");
}

// Loop over the images
for (i = 0; i < blue.length; i++) {
   blueChannel = blue[i];
   grayChannel = gray[i];
   print(blueChannel);
   //open(dir1+blueChannel);
   run("Bio-Formats Importer", "open=" + dir1 + File.separator + blueChannel +" color_mode=Default rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT");	
   enhanceHOECHST(getImageID());
   //open(dir1+grayChannel);
   run("Bio-Formats Importer", "open=" + dir1 + File.separator + grayChannel +" color_mode=Default rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT");	
   enhanceWGA(getImageID());
   // Using the "&" string expansion option within command arguments
   run("Merge Channels...", "c3=&blueChannel c1=&grayChannel create");
   run("8-bit");
   fileName = substring(blueChannel, 0, lastIndexOf(blueChannel, "-HOECHST.ome.tiff"))+"_Composite";
   saveAs("tiff", dir2 + fileName);
   close();
}

// All common image processing tasks in here
function enhanceHOECHST(imageID) {
	//selectImage(imageID);
	//run("Subtract Background...", "rolling=40");
	//run("Enhance Contrast...", "saturated=0.35 normalize");
	//run("Gaussian Blur...", "sigma=1");
}

function enhanceWGA(imageID) {
	//selectImage(imageID);
	//run("Top Hat...", "radius=50");
	//run("Gaussian Blur...", "sigma=2");
	
	//run("Subtract Background...", "rolling=400 sliding");
	//run("Gaussian Blur...", "sigma=1");

}


setBatchMode(false);
print("Done");