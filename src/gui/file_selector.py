from tkinter import ttk
from tkinter import filedialog
from tkinter import StringVar

class FileSelector(ttk.Frame):
    def open_dialog(self):
        name = filedialog.askopenfilename(
            title="Select Products CSV",
            filetypes=[("CSV Files", "*.csv")]
        )
        self.file_path.set(name)

    def update_entry(self, *args):
        self.entry.config(state='normal')
        self.entry.delete(0, 'end')
        split_name = self.file_path.get().split("/")
        self.entry.insert(0, split_name[-1])
        self.entry.config(state='readonly')

    def __init__(self, parent, label):
        ttk.Frame.__init__(self, parent)

        self.file_path = StringVar()

        self.label = ttk.Label(self, text=label)

        # Confgure file name display entry
        self.entry = ttk.Entry(
            self, 
            textvariable=self.file_path.get(),
            state='readonly'
        )
        self.file_path.trace_add("write", self.update_entry)
        
        self.button = ttk.Button(self, text="Choose...", command=self.open_dialog)

        # Pack layout
        self.label.pack(side="top", fill="x")
        self.entry.pack(side="left", fill="x")
        self.button.pack(side="left", fill="both")

    def get_file(self):
        return self.file_path.get()

        
