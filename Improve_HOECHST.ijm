// Make the nuclei more visible

run("Subtract Background...", "rolling=40");
run("Enhance Contrast...", "saturated=0.35 normalize");
run("Gaussian Blur...", "sigma=1");
