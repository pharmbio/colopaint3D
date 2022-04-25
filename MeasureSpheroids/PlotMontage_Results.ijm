#@File(label="Input directory", description="Select the directory with input images", style="directory") inputDir

run("Close All");
run("Image Sequence...", "select=[" + inputDir + "] dir=[" + inputDir + "] sort");
run("Make Montage...", "columns=12 rows=16 scale=0.25 label");
run("Copy to System");