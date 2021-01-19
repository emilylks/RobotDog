# Note that the majority of this file, excluding command choosing and
# sending to to other pi, are from a google tutorial

# export GOOGLE_APPLICATION_CREDENTIALS="/home/pi/Documents/Sven-keys.json"

from __future__ import division

import socket

import re
import sys

from gpiozero import LED

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
import pyaudio
from six.moves import queue

# Audio recording parameters
RATE = 48000
CHUNK = int(RATE / 10)

# Pi communication parameters
UDP_IP = "137.82.226.210"
UDP_PORT = 5005
SOCK = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_DGRAM) # UDP

led = LED(14)

class MicrophoneStream(object):


    """Opens a recording stream as a generator yielding the audio chunks."""
    
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)


def listen_print_loop(responses):
    prev_cmd = ""
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response
    is provided by the server.

    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the
    response is an interim one, print a line feed at the end of it, to allow
    the next result to overwrite it, until the response is a final one. For the
    final one, print a newline to preserve the finalized transcription.
    """
    listening = 0
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue

        # Display the transcription of the top alternative.
        transcript = result.alternatives[0].transcript

        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = ' ' * (num_chars_printed - len(transcript))

        if not result.is_final:
            #sys.stdout.write(transcript + overwrite_chars + '\r')
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            # Turn on robot, and enable receptiveness to cmds (wake up word)
            if "treat" in (transcript + overwrite_chars):
                listening = 1
                cmd = "treat"
                print(cmd + " " + prev_cmd)
                prev_cmd = cmd
            # Turn robot off, and disable receptiveness to cmds (besides wake up word)
            elif "sleep" in (transcript + overwrite_chars):
                listening = 0
                cmd = "sleep"
                print(cmd + " " + prev_cmd)
                prev_cmd = cmd
            # If receptive to cmds,                                                                                                                                                                                                                                                                               change mode to follow
            elif listening and ("follow" in (transcript + overwrite_chars)):
                cmd = "follow"
                print(cmd + " " + prev_cmd)
                prev_cmd = cmd
            elif listening and ("walk" in (transcript + overwrite_chars)):
                cmd = "walk"
                print(cmd + " " + prev_cmd)
                prev_cmd = cmd
            # If not listening, resend previous cmd so that function chooser on the other 
            # pi chooses to continue executing the current function
            elif not listening:
                print("not listening")
                cmd = prev_cmd
            # Unrecognized word, cmd will do nothing so robot continues with current functionality
            else:
                print(cmd + " " + prev_cmd)
                cmd = prev_cmd



            
            SOCK.sendto(cmd.encode(), (UDP_IP, UDP_PORT)) # send cmd to robot

            num_chars_printed = 0

        if (listening):
            # turn on an LED to indicate the robot is listening to cmds
            led.on()
        else:
            led.off()


def main():
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    language_code = 'en-US'  # a BCP-47 language tag

    client = speech.SpeechClient()
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code)
    streaming_config = types.StreamingRecognitionConfig(
        config=config,
        interim_results=True)

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (types.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)

        responses = client.streaming_recognize(streaming_config, requests)

        # Now, put the transcription responses to use.
        listen_print_loop(responses)


if __name__ == '__main__':
    main()
