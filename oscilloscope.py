#!C:\env\Scripts\python
#coding: utf8

import wave
import cv2
import numpy as np
import time
import struct
import pyaudio
import threading
import sys

def audio(file_path):
	CHUNK = 1024
	wf = wave.open(file_path, 'rb')
	p = pyaudio.PyAudio()
	stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
	                channels=wf.getnchannels(),
	                rate=wf.getframerate(),
	                output=True)
	data = wf.readframes(CHUNK)
	while data != '':
	    stream.write(data)
	    data = wf.readframes(CHUNK)
	stream.stop_stream()
	stream.close()
	p.terminate()

def stereo_to_points(raw, byte_size):
	points = []

	size = range(0, len(raw), byte_size*2)
	if byte_size == 2:
		for i in size:
			points.append([
				struct.unpack('h', raw[i:i+2])[0],
				struct.unpack('h', raw[i+2:i+4])[0]
				])
	elif byte_size == 3:
		for i in size:
			points.append([
				(struct.unpack('l', b'\0' + raw[i:i+3])[0]) >> 8,
				(struct.unpack('l', b'\0' + raw[i+3:i+6])[0]) >> 8
				])
	elif byte_size == 4:
		for i in size:
			points.append([
				struct.unpack('f', raw[i:i+4])[0],
				struct.unpack('f', raw[i+4:i+8])[0]
				])
	return points

def stereo_to_image(raw, byte_size, size_screen):
	points = stereo_to_points(raw, byte_size)
	value_max = (1 << (byte_size * 8)) >> 1
	size_05 = int(size_screen / 2)

	tmp_calc = size_05 / value_max
	last_x, last_y = size_05, size_05

	img_line = np.zeros((size_screen, size_screen, 1), np.uint8)
	img_point = np.zeros((size_screen, size_screen, 1), np.uint8)

	size = range(len(points))
	for i in size:
		left, right = points[i]
		x = int(left * tmp_calc + size_05)
		y = int(-right * tmp_calc + size_05)
		cv2.line(img_line, (x, y), (last_x, last_y), 255, 2)
		cv2.circle(img_point, (x, y), 1, 255, -1)
		last_x, last_y = x, y

	alpha = 0.9
	img = cv2.addWeighted(img_point, alpha, img_line, 1 - alpha, 0, img_line)
	o = np.zeros((size_screen, size_screen, 1), np.uint8)			
	img = cv2.merge((o, img, o))
	return img


def video(file_path):
	with wave.open(file_path, 'rb') as wf:

		size_sc = 800
		byte_size = wf.getsampwidth()
		size_05 = int(size_sc/2)
		framerate = wf.getframerate()
		persistence = 1/25

		TRACE = int(framerate * persistence)

		cv2.namedWindow('Oscilloscope')

		p = 0
		start = time.time()
		length = wf.getnframes()
		while p < length:
			start_t = time.time()

			wf.setpos(max(p, p - TRACE))
			raw = wf.readframes(TRACE)
			img = stereo_to_image(raw, byte_size, size_sc)
			cv2.imshow('Oscilloscope', img)

			if cv2.waitKey(1) & 0xFF == 27:
				break

			end_t = time.time()
			step = int((end_t - start) * framerate - p)
			p += step
			fps_current = 1 / (end_t - start_t)
			new_trace = TRACE * fps_current / 30
			# print('fps',
			# 	round(p / (end_t - start), 2),
			# 	round(fps_current, 2),
			# 	step,
			# 	new_trace,
			# 	TRACE)
			TRACE = int(min((framerate * persistence), new_trace))

		cv2.destroyAllWindows()


def main(file_path):
	with open(file_path, 'rb') as file:
		head = struct.unpack('4sL4s4sLHHLLHH4sL', file.read(44))
		print(head)

	th_audio = threading.Thread(target=lambda: audio(file_path), daemon=True)
	th_video = threading.Thread(target=lambda: video(file_path), daemon=True)

	th_audio.start()
	th_video.start()

	th_video.join()

def in_out():
	FORMAT = pyaudio.paInt24
	CHUNK = 1024
	CHANNELS = 2
	RATE = 96000
	 
	p = pyaudio.PyAudio()
	 
	stream = p.open(format=FORMAT,
	                channels=CHANNELS,
	                rate=RATE,
	                input=True,
	                frames_per_buffer=CHUNK)
	 
	cv2.namedWindow('Oscilloscope')
	 
	while True:
		try:
			data = stream.read(CHUNK)
			img = stereo_to_image(data, 3, 800)
			cv2.imshow('Oscilloscope', img)

			if cv2.waitKey(1) & 0xFF == 27:
				break
		except:
			break
	 
	cv2.destroyAllWindows()
	stream.stop_stream()
	stream.close()
	p.terminate()
	 

if __name__ == '__main__':
	if len(sys.argv) == 2:
		main(sys.argv[1])
	else:
		# main("Downforce.wav")
		in_out()