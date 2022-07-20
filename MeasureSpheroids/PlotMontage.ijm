#@File(label="Input directory", description="Select the directory with input images", style="directory") inputDir

run("Close All");
run("Image Sequence...", "select=[" + inputDir + "] dir=[" + inputDir + "] sort");
run("Make Montage...", "columns=16 rows=8 scale=0.25 label");
run("Rotate 90 Degrees Left")

run("Copy to System");