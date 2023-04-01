# media_converter
A simple media converter application made with python.

You can either open it as a project via VSCode or launch run.bat.
Using run.bat will only work if you have Python 3 installed on your system.

The general purpose of the program is to convert all video files within "media_converter\MediaConverterVenv\Input" directory and convert them to the selected format.

First step of the process is to convert the initial file codec to FFV1, keep in mind that this will change the file size substantially. For example, a 12MB file could go up to around 700MB during the intermediate file creation.
Second step is to convert the intermediate file to the final format with its fitting codecs.

Make sure that the input files do not have the same file name, as all outputs will be the same format.

If this program is launched with run.bat, once the process is finished, the terminal will close and the Output directory will be opened automatically.

If you see the intermediate file within the MediaConverterVenv directory after the terminal has closed, the process was not done correctly.