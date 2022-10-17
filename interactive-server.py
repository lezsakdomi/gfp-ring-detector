import asyncio
import webbrowser

from server import app


if __name__ == '__main__':
    from tkinter import Tk
    from tkinter.filedialog import askdirectory

    import list_targets
    while True:
        from os.path import exists, join

        Tk().withdraw()
        list_targets.default_dataset = askdirectory(initialdir=list_targets.default_dataset, mustexist=True,
                                                    title="Select dataset")
        if list_targets.default_dataset == "":
            from tkinter.messagebox import showerror
            showerror("No dataset selected", "Could not operate without selecting a dataset, closing")
            exit(1)

        toml_file = join(list_targets.default_dataset, 'dataset.toml')

        if not exists(toml_file):
            from tkinter.simpledialog import Dialog

            class DatasetTomlDialog(Dialog):
                DsRedChannelEntry = None
                GFPChannelEntry = None
                DAPIChannelEntry = None
                result = None

                def __init__(self):
                    Dialog.__init__(self, None, title="Dataset options")

                def body(self, master):
                    import tkinter as tk
                    from tkinter import ttk

                    master.columnconfigure(0, weight=1)
                    master.columnconfigure(1, weight=2)

                    label = tk.Label(master,
                                     text="Please provide information about the dataset.\n"
                                          "The options set below will be saved to the dataset.toml file.\n")
                    label.grid(row=0, rowspan=2, column=1, columnspan=2, sticky=tk.W + tk.E)

                    label = tk.Label(master, text="DsRed channel number", justify=tk.LEFT)
                    label.grid(row=3, column=1, padx=5, sticky=tk.W)
                    self.DsRedChannelEntry = tk.Entry(master, name="channels/DsRed")
                    self.DsRedChannelEntry.grid(row=3, column=2, padx=5, sticky=tk.W + tk.E)
                    self.DsRedChannelEntry.insert(0, "0")
                    # self.DsRedChannelEntry.select_range(0, tk.END)

                    label = tk.Label(master, text="GFP channel number", justify=tk.LEFT)
                    label.grid(row=4, column=1, padx=5, sticky=tk.W)
                    self.GFPChannelEntry = tk.Entry(master, name="channels/GFP")
                    self.GFPChannelEntry.grid(row=4, column=2, padx=5, sticky=tk.W + tk.E)
                    self.GFPChannelEntry.insert(0, "1")
                    # self.GFPChannelEntry.select_range(0, tk.END)

                    label = tk.Label(master, text="DAPI channel number", justify=tk.LEFT)
                    label.grid(row=5, column=1, padx=5, sticky=tk.W)
                    self.DAPIChannelEntry = tk.Entry(master, name="channels/DAPI")
                    self.DAPIChannelEntry.grid(row=5, column=2, padx=5, sticky=tk.W + tk.E)
                    self.DAPIChannelEntry.insert(0, "2")
                    # self.DAPIChannelEntry.select_range(0, tk.END)

                def get_dict(self):
                    return {
                        'channels': {
                            'DsRed': self.getint(self.DsRedChannelEntry.get()),
                            'GFP': self.getint(self.GFPChannelEntry.get()),
                            'DAPI': self.getint(self.DAPIChannelEntry.get()),
                        },
                    }

                def validate(self):
                    try:
                        self.result = self.get_dict()
                        return 1
                    except ValueError:
                        return 0

                def apply(self):
                    from toml import dump

                    dataset_options = self.result
                    with open(toml_file, 'w') as f:
                        dump(dataset_options, f)

            d = DatasetTomlDialog()
        if exists(toml_file):
            break
    webbrowser.open("http://localhost:8080/")
    app.run('localhost', 8080)
