// "OpenSeriesUsingFilter.txt"
// Opens an image series as a stack using a customizable
// file name filter. To customize the filter, edit the
// filter() method.

macro "Open Series Using Filter" {
    requires("1.34e"); 
    //dir = getDirectory("Choose a Directory ");
    dir = "/Volumes/mikro_pharmbio/ColoPaint/colo44-v1-FA-P017365-CACO2-48h-P1-L1/2022-05-26/1043/";
    print(dir);
    list = getFileList(dir);
    //s = getString("Enter a string:", "str");
    //list_im = split(s, ",");
    list_im = split("B05_,B23_,C07_,C13_,D15_,E08_,F14_,F20_,G03_,G09_,H06_,H17_,I02_,I12_,J10_,J18_,K22_,L09_,M19_,M23_,N04_,N21_,O11_,O16", ",");
    stack = 0;
    setBatchMode(true); 
    for (i=0; i<list.length; i++) {
        showProgress(i, list.length);
        for (ii=0; ii<list_im.length; ii++) {
	        if (filter(i, list[i],list_im[ii])) {
	            open(dir+list[i]);
	            run("Copy");
	            if (stack==0) {
	                type = "" +bitDepth;
	                if (type=="24") type = "RGB";
	                w=getWidth(); h=getHeight();
	                close();
	                newImage("stack",type,w,h,1);
	                stack = getImageID();
	            } else {
	                close();
	                selectImage(stack);
	                run("Add Slice");
	            }
	            run("Paste");
	        }
        }
    }
    if (stack!=0) setSlice(1);
    setBatchMode(false);   
   
	waitForUser;

	 // Size of the stack divided by 3.
	getDimensions(ImageWidth, ImageHeight, ImageChannels, ImageSlices, ImageFrames); 
	run("Stack to Hyperstack...", "order=xyczt(default) channels=3 slices=1 frames=" + ImageSlices/3 + " display=Color");
	
	run("Split Channels");
	run("Merge Channels...", "c1=C2-stack c2=C3-stack c3=C1-stack create");
	run("Make Montage...", "columns=18 rows=12 scale=0.25");
	run("Stack to RGB");        	                
	         	                	         	                	         	                
}

function filter(i, name, im_rex) {
	//str = "_thumb";
	
    // is tiff?
	//if (indexOf(name,"_thumb")==50) return false;    // ignore text files
	if (indexOf(name,"_thumb")!=-1) return false;
    // if (endsWith(name,".txt")) return false;
    // does name contain both "Series002" and "ch01"
    // 
    //if (matches(name,".*w5.*")) return false;
    if (matches(name,".*w2.*")) return false;
    if (matches(name,".*w3.*")) return false;
    //if (!matches(name,".*A02_.*")) return false;

    if (!matches(name,".*" + im_rex + ".*")) return false;

    // open only first 10 images
    // if (i>=10) return false;

    return true;
}
 
