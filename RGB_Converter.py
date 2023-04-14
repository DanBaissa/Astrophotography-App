import cv2
import numpy as np
from astropy.io import fits
import tkinter as tk
from tkinter import filedialog

class FITSAlignerGUI:
    def __init__(self, master):
        self.master = master
        master.title("FITS Aligner")

        self.label = tk.Label(master, text="Select FITS files (R, G, B) and output image path")
        self.label.pack()

        self.select_red_button = tk.Button(master, text="Select Red FITS", command=self.select_red_fits)
        self.select_red_button.pack()

        self.select_green_button = tk.Button(master, text="Select Green FITS", command=self.select_green_fits)
        self.select_green_button.pack()

        self.select_blue_button = tk.Button(master, text="Select Blue FITS", command=self.select_blue_fits)
        self.select_blue_button.pack()

        self.select_output_button = tk.Button(master, text="Select Output Image", command=self.select_output_image)
        self.select_output_button.pack()

        self.align_button = tk.Button(master, text="Align and Save", command=self.align_and_save, state=tk.DISABLED)
        self.align_button.pack()

        self.red_fits_file = None
        self.green_fits_file = None
        self.blue_fits_file = None
        self.output_image_path = None

    def read_fits_image(self, file_path):
        with fits.open(file_path) as hdulist:
            data = hdulist[0].data
        return data

    def normalize_image(self, image_data):
        normalized_image = image_data.copy()
        normalized_image = cv2.normalize(image_data.astype(np.float32), None, 0.0, 1.0, cv2.NORM_MINMAX)
        return normalized_image

    def align_channels(self, channels):
        aligned_channels = []

        # Preprocess the channels by applying Gaussian blur to reduce noise
        channels_blurred = [cv2.GaussianBlur(channel, (5, 5), 0) for channel in channels]

        # Select the reference channel (the one with the highest mean)
        reference_channel_index = np.argmax([np.mean(channel) for channel in channels_blurred])
        reference_channel = channels_blurred[reference_channel_index]

        for i, channel in enumerate(channels_blurred):
            if i == reference_channel_index:
                aligned_channels.append(channels[i])  # No alignment needed for the reference channel
                continue

            # Register the channel to the reference channel
            warp_mode = cv2.MOTION_HOMOGRAPHY
            warp_matrix = np.eye(3, 3, dtype=np.float32)
            criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 5000, 1e-10)
            _, warp_matrix = cv2.findTransformECC(reference_channel, channel, warp_matrix, warp_mode, criteria)

            # Apply the transformation to the original channel
            aligned_channel = cv2.warpPerspective(channels[i], warp_matrix, (channels[i].shape[1], channels[i].shape[0]), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
            aligned_channels.append(aligned_channel)

        return aligned_channels

    def save_as_color_image(self, red, green, blue, output_path):
        color_image = cv2.merge((blue, green, red))
        cv2.imwrite(output_path, (color_image * 255).astype(np.uint8))

    def select_red_fits(self):
        self.red_fits_file = filedialog.askopenfilename(filetypes=[        ("FITS files", "*.fits")])
        self.check_files()

    def select_green_fits(self):
        self.green_fits_file = filedialog.askopenfilename(filetypes=[("FITS files", "*.fits")])
        self.check_files()

    def select_blue_fits(self):
        self.blue_fits_file = filedialog.askopenfilename(filetypes=[("FITS files", "*.fits")])
        self.check_files()

    def select_output_image(self):
        self.output_image_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        self.check_files()

    def check_files(self):
        if self.red_fits_file and self.green_fits_file and self.blue_fits_file and self.output_image_path:
            self.align_button.config(state=tk.NORMAL)

    def align_and_save(self):
        red_data = self.read_fits_image(self.red_fits_file)
        green_data = self.read_fits_image(self.green_fits_file)
        blue_data = self.read_fits_image(self.blue_fits_file)

        red_norm = self.normalize_image(red_data)
        green_norm = self.normalize_image(green_data)
        blue_norm = self.normalize_image(blue_data)

        aligned_channels = self.align_channels([red_norm, green_norm, blue_norm])

        self.save_as_color_image(*aligned_channels, self.output_image_path)

if __name__ == "__main__":
    root = tk.Tk()
    gui = FITSAlignerGUI(root)
    root.mainloop()

