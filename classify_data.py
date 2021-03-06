from PIL import ImageTk, Image
import tkinter as tk
import numpy as np
import h5py
import windowTools as wt
import argparse
import os.path

class Classifier:
    def __init__(self, master, hfile):
        self.master = master
        master.title("Image Data Annotations")
        self.hfile = hfile
        self.canvas = tk.Canvas(master, width=600, height=400)
        self.canvas.pack()
        self.x = 0
        self.y = 0
        self.x_offset = 20  # image offset in canvas
        self.y_offset = 20
        self.grid_x = 15
        self.grid_y = 10
        self.data = np.zeros((self.grid_y, self.grid_x, 5))

        self._display_im()

        self.button_save = tk.Button(
            master, text='Save', command=self.save_data)
        self.button_save.pack()

        self.button_next = tk.Button(master, text="next", command=self._display_im)
        self.button_next.pack()

        self.button_delete = tk.Button(master, text="delete last", command=self.delete_data)
        self.button_delete.pack()

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.rect = None

        self.start_x = None
        self.start_y = None

        self.rectangles = []

    def _display_im(self):
        self.canvas.delete("all")
        self.data = np.zeros((self.grid_y, self.grid_x, 5))
        self.ar_im = wt.get_array((30, 2, 510, 340))
        self.img = ImageTk.PhotoImage(Image.fromarray(self.ar_im))
        self.im_w = self.ar_im.shape[1]
        self.im_h = self.ar_im.shape[0]

        self.canvas.create_image(
            self.x_offset, self.y_offset, anchor=tk.NW, image=self.img)

    def on_button_press(self, event):
        # save mouse drag start position
        self.start_x = event.x
        self.start_y = event.y

        # create rectangle if not yet exist
        #if not self.rect:
        self.rect = self.canvas.create_rectangle(self.x, self.y, 1, 1, fill="", outline="red")

    def on_move_press(self, event):
        curX, curY = (event.x, event.y)
        # expand rectangle as you drag the mouse
        self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)


    def on_button_release(self, event):
        coords = (self.start_x-self.x_offset, self.start_y-self.y_offset,
                  event.x-self.x_offset, event.y-self.y_offset)
        # add to data
        #calc midpoint
        midx = (coords[0] + coords[2])/2
        midy = (coords[1] + coords[3])/2

        cell_x = int(midx/self.im_w * self.grid_x)
        cell_y = int(midy/self.im_h * self.grid_y)
     
        bx = (midx - cell_x*34)/34
        by = (midy - cell_y*34)/34

        #calc width and height
        w = np.abs(coords[0] - coords[2])/34
        h = np.abs(coords[1] - coords[3])/34

        # append
        self.data[cell_y, cell_x] = np.array([1, bx, by, w, h])

    def save_data(self):
        """Save the simulation data into an existing h5 file.
        Args:
            i (int): iteration step
            F (np.array): merit function
            phi (np.array): level set function
            vn (np.array): velocity field
            Q (np.array): optimisation factor
        Returns:
            None.
        """
        if not os.path.isfile(self.hfile):
            with h5py.File(self.hfile, 'w') as f:
                g = f.create_group("Data")
                X_data = g.create_dataset("X_data", shape=(1, 340, 510, 3), maxshape=(None, 340, 510, 3))
                Y_data = g.create_dataset("Y_data", shape=(1, 10, 15, 5), maxshape=(None, 10, 15, 5))
                X_data[0] = self.ar_im[:, :, :3]
                Y_data[0] = self.data
                f.close()
            print("Data saved in new file {:}".format(self.hfile))
        else:
            with h5py.File(self.hfile, 'a') as f:
                g = f['Data']
                X_data = g['X_data']
                Y_data = g['Y_data']
                n = X_data.shape[0]
                Y_data.resize((n+1, *self.data.shape))
                X_data.resize((n+1, *self.ar_im[:, :, :3].shape))
                Y_data[n] = self.data
                X_data[n] = self.ar_im[:, :, :3]
                f.close()

            print("Data saved in file {:} !".format(self.hfile))


    def delete_data(self):
        """Delete last entry from file"""
        with h5py.File(self.hfile, 'a') as f:
            g = f['Data']
            X_data = g['X_data']
            Y_data = g['Y_data']
            n = X_data.shape[0]
            Y_data.resize((n-1, *self.data.shape))
            X_data.resize((n-1, *self.ar_im[:, :, :3].shape))
            f.close()

        print("Last entry deleted in file {:} !".format(self.hfile))

running = False

def close(*ignore):
    global running
    running = False
    root.destroy()


parser = argparse.ArgumentParser(description="Data Augmentation")
parser.add_argument('-f', '--file')

args = parser.parse_args()
    
root = tk.Tk()
window = Classifier(root, args.file)
root.bind('<Escape>', close)
root.protocol("WM_DELETE_WINDOW", close)
#root.after(500, window.run)
root.mainloop()
