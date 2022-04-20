import asyncio
import webbrowser

from server import serve


if __name__ == '__main__':
    from tkinter import Tk
    from tkinter.filedialog import askdirectory

    import list_targets
    Tk().withdraw()
    list_targets.default_dataset = askdirectory(initialdir=list_targets.default_dataset, mustexist=True,
                                                title="Select dataset")

    webbrowser.open("http://localhost:8080/")
    asyncio.run(serve())
