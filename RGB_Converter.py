import tkinter as tk
from tkinter import filedialog
import astroalign as aa
import numpy as np
import glob
from astropy.io import fits
import tifffile
import glob

def process_images(reference_image_paths, images_folders, output_path, normalize_after_stacking):
    channels = ['red', 'green', 'blue']
    aligned_images_rgb = []

    for channel_index, (ref_image_path, images_folder) in enumerate(zip(reference_image_paths, images_folders)):
        image_paths = glob.glob(f"{images_folder}/*.fits")

        aligned_images = []
        reference_img_data = fits.getdata(ref_image_path)

        for img_path in image_paths:
            img_data = fits.getdata(img_path)

            try:
                aligned_img, _ = aa.register(img_data, reference_img_data)
                aligned_images.append(aligned_img)
            except aa.MaxIterError:
                print(f"Could not align {img_path} in {channels[channel_index]} channel. Skipping.")
                continue

        stacked_image = np.zeros_like(aligned_images[0], dtype=np.float64)

        for image in aligned_images:
            stacked_image += image

        stacked_image /= len(aligned_images)
        if normalize_after_stacking:
            stacked_image /= np.max(stacked_image)
        aligned_images_rgb.append(stacked_image)

    reference_stacked_image = aligned_images_rgb[0]
    for idx, stacked_image in enumerate(aligned_images_rgb[1:], 1):
        try:
            aligned_stacked_image, _ = aa.register(stacked_image, reference_stacked_image)
            aligned_images_rgb[idx] = aligned_stacked_image
        except aa.MaxIterError:
            print(f"Could not align the stacked image of {channels[idx]} channel. Skipping alignment.")
            continue

    height, width = aligned_images_rgb[0].shape
    merged_tiff = np.zeros((height, width, 3), dtype=np.float64)

    for channel_index, stacked_image in enumerate(aligned_images_rgb):
        merged_tiff[..., channel_index] = stacked_image

    merged_tiff = (merged_tiff / np.max(merged_tiff) * 255).astype(np.uint8)
    tifffile.imwrite(output_path, merged_tiff)
    print(f"Merged TIFF saved as {output_path}.")

def browse_reference_image(channel):
    file_path = filedialog.askopenfilename(filetypes=[("FITS files", "*.fits")])
    reference_image_paths[channel].set(file_path)

def browse_images_folder(channel):
    folder_path = filedialog.askdirectory()
    images_folders[channel].set(folder_path)

def browse_output_folder():
    file_path = filedialog.asksaveasfilename(defaultextension=".tiff", filetypes=[("TIFF files", "*.tiff")])
    output_path.set(file_path)

def run_alignment_and_stacking():
    process_images(
        [reference_image_paths[0].get(), reference_image_paths[1].get(), reference_image_paths[2].get()],
        [images_folders[0].get(), images_folders[1].get(), images_folders[2].get()],
        output_path.get(),
        normalize_var.get()
    )
    status_label.config(text="Processing complete")

root = tk.Tk()
root.title("RGB Image Alignment and Stacking")

channels = ['Red', 'Green', 'Blue']
reference_image_paths = [tk.StringVar() for _ in channels]
images_folders = [tk.StringVar() for _ in channels]
normalize_var = tk.IntVar()

for idx, channel in enumerate(channels):
    row_offset = idx * 2
    tk.Label(root, text=f"{channel} Reference Image:").grid(row=row_offset, column=0, sticky=tk.W)
    tk.Entry(root, textvariable=reference_image_paths[idx], width=50).grid(row=row_offset, column=1)
    tk.Button(root, text="Browse", command=lambda ch=idx: browse_reference_image(ch)).grid(row=row_offset, column=2)

    tk.Label(root, text=f"{channel} Images Folder:").grid(row=row_offset + 1, column=0, sticky=tk.W)
    tk.Entry(root, textvariable=images_folders[idx], width=50).grid(row=row_offset + 1, column=1)
    tk.Button(root, text="Browse", command=lambda ch=idx: browse_images_folder(ch)).grid(row=row_offset + 1, column=2)

output_path = tk.StringVar()
tk.Label(root, text="Output Image:").grid(row=6, column=0, sticky=tk.W)
tk.Entry(root, textvariable=output_path, width=50).grid(row=6, column=1)
tk.Button(root, text="Browse", command=browse_output_folder).grid(row=6, column=2)

# Normalize option
tk.Checkbutton(root, text="Normalize After Stacking", variable=normalize_var).grid(row=7, columnspan=3, pady=10)

tk.Button(root, text="Run Alignment and Stacking", command=run_alignment_and_stacking).grid(row=8, columnspan=3,
                                                                                            pady=10)

status_label = tk.Label(root, text="")
status_label.grid(row=9, columnspan=3)

root.mainloop()
