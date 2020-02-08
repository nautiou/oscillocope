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

def video(file_path):
	with wave.open(file_path, 'rb') as wf:

		size_sc = 800
		byte_size = wf.getsampwidth()
		size_05 = int(size_sc/2)
		size_max = (1 << (8 * byte_size)) - 1
		framerate = wf.getframerate()
		
		TRACE = byte_size * 1000

		cv2.namedWindow('Oscilloscope')

		def frames(begin, n):
			wf.setpos(begin)
			a = wf.readframes(n)

			len_a = len(a)
			b = []
			c = []
			size = range(0, len_a, byte_size*2)

			if byte_size == 2:
				for i in size:
					b.append(struct.unpack('h', a[i:i+2])[0])
					c.append(struct.unpack('h', a[i+2:i+4])[0])
			elif byte_size == 3:
				for i in size:
					b.append((struct.unpack('l', b'\0' + a[i:i+3])[0]) >> 8)
					c.append((struct.unpack('l', b'\0' + a[i+3:i+6])[0]) >> 8)
			return a, b, c, len_a

		p = 0
		start = time.time()
		length = wf.getnframes()
		while p < length:
			start_t = time.time()
			raw, left, right, nb = frames(p, TRACE)

			size = range(int(nb/(byte_size * 2)))
			tmp_calc = size_sc / size_max
			last_x, last_y = size_05, size_05

			img = np.zeros((size_sc, size_sc, 1), np.uint8)

			for i in size:
				x = int(left[i] * tmp_calc + size_05)
				y = int(-right[i] * tmp_calc + size_05)
				cv2.line(img, (x, y), (last_x, last_y), 255, 1)
				last_x, last_y = x, y

			o = np.zeros((size_sc, size_sc, 1), np.uint8)			
			img = cv2.merge((o, img, o))
			cv2.imshow('Oscilloscope', img)

			if cv2.waitKey(1) & 0xFF == 27:
				break

			end_t = time.time()
			step = int((end_t - start_t) * framerate)
			p += step
			# print('fps', round(p / (end_t - start), 2),
			# 	round(1 / (end_t - start_t), 2), step)

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

if __name__ == '__main__':
	if len(sys.argv) == 2:
		main(sys.argv[1])