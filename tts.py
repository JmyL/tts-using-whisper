import os
import sys
import argparse

from openai import OpenAI

from mutagen.mp4 import MP4
from pydub import AudioSegment
from pydub.silence import detect_silence

def get_audio_duration(file_path):
    audio = MP4(file_path)
    duration = audio.info.length  # duration in seconds
    return duration

def calculate_cost(duration):
    price_per_minute = 0.006
    total_minutes = duration / 60
    cost = total_minutes * price_per_minute
    return cost

def split_audio(file_path, max_size_mb=25):
    print("Reading audio file ... ")
    audio = AudioSegment.from_file(file_path, format="m4a")
    print("Finished.")
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    num_parts = int(file_size_mb // max_size_mb) + 1
    part_duration = len(audio) // num_parts

    output_files = []

    start_time = 0
    print(f"Splitting into {num_parts} parts:")
    for i in range(num_parts):
        print(f"- Processing part {i + 1}")
        end_time = start_time + part_duration
        if end_time > len(audio):
            end_time = len(audio)

        time_window_start = end_time - 20000
        print("\t - Finding silence ranges ... ")
        silence_ranges = detect_silence(audio[time_window_start:end_time], min_silence_len=1000, silence_thresh=-20)
        print("\t - Finished.")
        if not silence_ranges:
            raise ValueError("Adjust silence threshold!")

        end_time = time_window_start + silence_ranges[-1][0]

        print("\t - Exporting audio file ... ")
        part = audio[start_time:end_time]
        output_file_path = f"{file_path.rsplit('.', 1)[0]}_part{i + 1}.m4a"
        part.export(output_file_path, format="mp4")
        # output_file_path = f"{file_path.rsplit('.', 1)[0]}_part{i + 1}.mp3"
        # part.export(output_file_path, format="mp3", bitrate="192k")  # Use 'mp3' format with a reasonable bitrate
        print("\t - Finished.")
        output_files.append(output_file_path)

        start_time = time_window_start + silence_ranges[-1][1]

    return output_files

def perform_sst(file_path):
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            # response_format="text"

            # TODO: Add language option according to [ISO-639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)


            # TODO: Add prompt, maximum 224 tokens, should match the audio language
            # prompt="ZyntriQix, Digique Plus, CynapseFive, VortiQore V8, EchoNix Array, OrbitalLink Seven, DigiFractal Matrix, PULSE, RAPT, B.R.I.C.K., Q.U.A.R.T.Z., F.L.I.N.T."
        )
    return transcription.text
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process an M4A file.")
    parser.add_argument("file_path", type=str, help="Path to the M4A file")
    parser.add_argument("--simulate", action="store_true", help="Simulate and print the duration of the M4A file")

    args = parser.parse_args()

    if not os.path.isfile(args.file_path):
        print(f"File not found: {args.file_path}")
        sys.exit(1)

    duration = get_audio_duration(args.file_path)
    minutes = duration // 60
    seconds = duration % 60
    print(f"{int(minutes)} minutes and {int(seconds)} seconds")
    cost = calculate_cost(duration)
    print(f"Estimated cost: {cost:.2f} USD")


    output_files = split_audio(args.file_path)

    if not args.simulate:
        text = ""
        for output_file in output_files:
            text += perform_sst(output_file)

        output_file_path = f"{args.file_path}.txt"
        with open(output_file_path, "w") as output_file:
            output_file.write(text)
