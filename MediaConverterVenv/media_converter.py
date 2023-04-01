import os
import sys
import platform
import subprocess
import imageio_ffmpeg as ff


# Check if all requirements are installed, if not, install them.

def check_and_install_requirements(requirements_file):
    # Check if the current Python version is 3.x, raise an error if not.
    if sys.version_info[0] < 3:
        raise RuntimeError("This script requires Python 3.x.")

    # Try to import pkg_resources, if not available, install setuptools and import it.
    try:
        import pkg_resources
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "setuptools"])
        import pkg_resources

    # Read the requirements file and store the package requirements as a list.
    with open(requirements_file, "r") as f:
        requirements = [line.strip() for line in f.readlines() if line.strip()]

    # Get a dictionary of installed packages and their versions.
    installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
    # Find any packages in the requirements that are not installed.
    missing_packages = [pkg for pkg in requirements if pkg.split("==")[0].lower() not in installed_packages]

    # Install any missing packages.
    if missing_packages:
        print("Installing missing packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
    else:
        print("All required packages are installed.")


# Make sure Input folder contains something, otherwise open Input folder.

def get_input_files(input_folder):
    # Return a list of all files within the input_folder.
    input_files = [os.path.join(input_folder, f)
                   for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))]
    return input_files


# The commented codecs at the end are for different results.
# First one is the best lossless codec.
# Second one is high quality and reasonable compression.
# Third is balanced quality and compression.

def get_video_codec(output_format):
    # Dictionary of video codecs and quality flags for supported output formats.
    codec_map = {
        # Format: (video_codec, quality_flag)
        "webm": ("libvpx-vp9", "-lossless 1"),  # libvpx-vp9, libvpx, libvorbis
        "mkv": ("ffv1", ""),  # ffv1, libx264, libx265
        "flv": ("flv", "-q:v 0"),  # flv, libx264, libx265
        "vob": ("mpeg2video", "-q:v 0"),  # mpeg2video, libx264, libx265
        "avi": ("ffv1", ""),  # ffv1, mpeg4, msmpeg4v2
        "mov": ("prores_ks", "-profile:v hq"),  # prores_ks, libx264, libx265
        "wmv": ("wmv2", "-q:v 0"),  # wmv2, wmv1, vc1
        "mp4": ("libx265", "-crf 0"),  # libx265, libx264, mpeg4
        "mpg": ("mpeg2video", "-q:v 0"),  # mpeg2video, libx264, libx265
        "mpeg": ("mpeg2video", "-q:v 0"),  # mpeg2video, libx264, libx265
        "3gp": ("libx264", "-crf 0")  # libx264, libx265, mpeg4
    }
    # Raise an error if the output format is unsupported.
    if output_format.lower() not in codec_map:
        raise ValueError(f"Unsupported output format: {output_format}")
    # Return the video codec and quality flag for the specified output format.
    return codec_map.get(output_format.lower(), ("libx264", "-crf 0"))


# List of audio codecs for each supported format.

def get_audio_codec(output_format):
    # Dictionary of audio codecs for supported output formats.
    codec_map = {
        # Format: audio_codec
        "webm": "libopus",
        "mkv": "aac",
        "flv": "libmp3lame",
        "vob": "ac3",
        "avi": "libmp3lame",
        "mov": "aac",
        "wmv": "wmav2",
        "mp4": "aac",
        "mpg": "mp2",
        "mpeg": "mp2",
        "3gp": "aac"
    }
    # Raise an error if the audio output format is unsupported.
    if output_format.lower() not in codec_map:
        raise ValueError(f"Unsupported audio output format: {output_format}")
    # Return the audio codec for the specified output format.
    return codec_map.get(output_format.lower(), "aac")


# Check if input and output directories exist.

def ensure_directory_exists(directory):
    # Check if the given directory exists.
    if not os.path.exists(directory):
        # If the directory does not exist, create it.
        os.makedirs(directory)


# Convert video codec to FFV1 as intermediate precautionary step. Then convert intermediate_file to final format.

def convert_media(input_file, output_file):
    # Get the input file's name without the path.
    input_filename = os.path.basename(input_file)
    # Get the output file's format (extension) from the output_file parameter.
    output_format = output_file.split('.')[-1]
    # Get the appropriate video and audio codecs for the specified output format.
    video_codec, quality_flag = get_video_codec(output_format)
    audio_codec = get_audio_codec(output_format)

    # Create the intermediate file's name with the FFV1 codec.
    intermediate_file = f"intermediate_{input_filename}.mkv"

    # Get the path to the FFmpeg executable.
    ffmpeg_path = ff.get_ffmpeg_exe()

    # Define the FFmpeg command for converting the input file to an intermediate file with the FFV1 codec.
    cmd_ffv1 = f'"{ffmpeg_path}" -i "{input_file}" -c:v ffv1 -async 1 -level 3 -coder 1 -context 1 -g 1' \
               f' -slices 24 -slicecrc 1 -b:v 0 -c:a copy -row-mt 1 "{intermediate_file}"'
    try:
        # Run the FFmpeg command for the FFV1 conversion and capture its output.
        subprocess.check_output(cmd_ffv1, shell=True, stderr=subprocess.STDOUT)
        print(f"Successfully re-encoded {input_file} using FFV1 codec to {intermediate_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while re-encoding {input_file} using FFV1 codec: {e}")

    # Define the FFmpeg command for converting the intermediate file to the final output format.
    cmd_convert = f'"{ffmpeg_path}" -i "{intermediate_file}" -c:v {video_codec} {quality_flag} -async 1  -b:v 0' \
                  f' -c:a {audio_codec} -map 0 -map_metadata 0 -row-mt 1 "{output_file}"'
    try:
        # Run the FFmpeg command for the final conversion and capture its output.
        subprocess.check_output(cmd_convert, shell=True, stderr=subprocess.STDOUT)
        print(f"Successfully converted {intermediate_file} to {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while converting {intermediate_file} to {output_file}: {e}")
    finally:
        # Delete the intermediate file.
        os.remove(intermediate_file)


if __name__ == "__main__":
    # Check and install required packages from the requirements.txt file.
    requirements_file = "requirements.txt"
    check_and_install_requirements(requirements_file)

    # Define the names of the input and output folders.
    input_folder = "Input"
    output_folder = "Output"

    # Ask the user for the desired output format for the converted media files.
    output_format = input("Enter output format (webm, mkv, flv, vob, avi, mov, wmv, mp4, mpg, mpeg, 3gp): ")

    # Ensure the input and output folders exist, creating them if necessary.
    ensure_directory_exists(input_folder)
    ensure_directory_exists(output_folder)

    # Get a list of input files from the input folder.
    input_files = get_input_files(input_folder)

    # Check if the input folder is empty.
    if not input_files:
        print("The Input folder is empty.")
        # Open the input folder in the file explorer.
        if platform.system() == "Windows":
            os.startfile(input_folder)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", input_folder])
        else:
            subprocess.Popen(["xdg-open", input_folder])
    else:
        # Iterate over all files in the input folder.
        for input_file in input_files:
            # Get the file name without the path.
            input_filename = os.path.basename(input_file)
            # Create the output file path with the desired output format.
            output_file = os.path.join(output_folder, f"{os.path.splitext(input_filename)[0]}.{output_format}")
            # Print a message about the current conversion process.
            print(f"Converting {input_file} to {output_file}...")
            # Call the convert_media function to convert the input file.
            convert_media(input_file, output_file)
