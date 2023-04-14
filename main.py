import tkinter as tk
from tkinter import filedialog
import astroalign as aa
import numpy as np
import glob
from astropy.io import fits

def process_images(reference_image_path, images_folder, output_path):
    image_paths = glob.glob(f"{images_folder}/*.fits")

    aligned_images = []
    reference_img_data = fits.getdata(reference_image_path)

    for img_path in image_paths:
        img_data = fits.getdata(img_path)

        try:
            aligned_img, _ = aa.register(img_data, reference_img_data)
            aligned_images.append(aligned_img)
        except aa.MaxIterError:
            print(f"Could not align {img_path}. Skipping.")
            continue

    stacked_image = np.zeros_like(aligned_images[0], dtype=np.float64)

    for image in aligned_images:
        stacked_image += image

    stacked_image /= len(aligned_images)
    hdu = fits.PrimaryHDU(stacked_image)
    hdu.writeto(output_path, overwrite=True)
    print(f"Stacked image saved as {output_path}.")

# GUI functions

def browse_reference_image():
    file_path = filedialog.askopenfilename(filetypes=[("FITS files", "*.fits")])
    reference_image_path.set(file_path)

def browse_images_folder():
    folder_path = filedialog.askdirectory()
    images_folder.set(folder_path)

def browse_output_folder():
    file_path = filedialog.asksaveasfilename(defaultextension=".fits", filetypes=[("FITS files", "*.fits")])
    output_path.set(file_path)

def run_alignment_and_stacking():
    process_images(reference_image_path.get(), images_folder.get(), output_path.get())
    status_label.config(text="Processing complete")

# GUI setup

root = tk.Tk()
root.title("Image Alignment and Stacking")

# Reference image selection
reference_image_path = tk.StringVar()
tk.Label(root, text="Reference Image:").grid(row=0, column=0, sticky=tk.W)
tk.Entry(root, textvariable=reference_image_path, width=50).grid(row=0, column=1)
tk.Button(root, text="Browse", command=browse_reference_image).grid(row=0, column=2)

# Images folder selection
images_folder = tk.StringVar()
tk.Label(root, text="Images Folder:").grid(row=1, column=0, sticky=tk.W)
tk.Entry(root, textvariable=images_folder, width=50).grid(row=1, column=1)
tk.Button(root, text="Browse", command=browse_images_folder).grid(row=1, column=2)

# Output folder selection
output_path = tk.StringVar()
tk.Label(root, text="Output Image:").grid(row=2, column=0, sticky=tk.W)
tk.Entry(root, textvariable=output_path, width=50).grid(row=2, column=1)
tk.Button(root, text="Browse", command=browse_output_folder).grid(row=2, column=2)

# Run button
tk.Button(root, text="Run Alignment and Stacking", command=run_alignment_and_stacking).grid(row=3, columnspan=3, pady=10)

# Status label
status_label = tk.Label(root, text="")
status_label.grid(row=4, columnspan=3)

root.mainloop()
