from tkinter import *
from tkinter import ttk, filedialog, messagebox
import base64
import json
from pathlib import Path
from bs4 import BeautifulSoup
import requests

config = {}
_status_msg = None  # Initialize _status_msg as a global variable


def fetch_url():
    url = _url.get()
    config["images"] = []
    _images.set(())
    try:
        page = requests.get(url)
    except requests.RequestException as err:
        sb(str(err))
    else:
        soup = BeautifulSoup(page.content, "html.parser")
        images = fetch_images(soup, url)
        if images:
            _images.set(tuple(img["name"] for img in images))
            sb("Images found: {}".format(len(images)))
        else:
            sb("No images found")
        config["images"] = images


def fetch_images(soup, base_url):
    images = []
    for img in soup.findAll("img"):
        src = img.get("src")
        img_url = f"{base_url}/{src}"
        name = img_url.split("/")[-1]
        images.append(dict(name=name, url=img_url))
    return images


def fetch_title():
    url = _url.get()
    try:
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        title = soup.title.string if soup.title else "No title found"
        sb(f"Title: {title}")
    except requests.RequestException as err:
        sb(f"Error fetching title: {err}")


def fetch_links():
    url = _url.get()
    base_url = url.split("//")[-1].split("/")[0]
    try:
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        external_links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith("http") and base_url not in href:
                external_links.append(href)
        if external_links:
            _images.set(tuple(external_links))
            sb(f"External links found: {len(external_links)}")
        else:
            sb("No external links found")
    except requests.RequestException as err:
        sb(f"Error fetching links: {err}")


def save():
    if not config.get("images"):
        alert("No images to save")
        return
    if _save_method.get() == "img":
        dirname = filedialog.askdirectory(mustexist=True)
        save_images(dirname)
    else:
        filename = filedialog.asksaveasfilename(
            initialfile="images.json", filetypes=[("JSON", ".json")]
        )
        save_json(filename)


def save_images(dirname):
    if dirname and config.get("images"):
        for img in config["images"]:
            img_data = requests.get(img["url"]).content
            filename = Path(dirname).joinpath(img["name"])
            with open(filename, "wb") as f:
                f.write(img_data)
        alert("Done")


def save_json(filename):
    if filename and config.get("images"):
        data = {}
        for img in config["images"]:
            img_data = requests.get(img["url"]).content
            b64_img_data = base64.b64encode(img_data)
            str_img_data = b64_img_data.decode("utf-8")
            data[img["name"]] = str_img_data
        with open(filename, "w") as ijson:
            ijson.write(json.dumps(data))
        alert("Done")


def sb(msg):
    global _status_msg
    _status_msg.set(msg)


def alert(msg):
    messagebox.showinfo(message=msg)


if __name__ == "__main__":
    _root = Tk()
    _root.title("SEO Scraper Tool")
    _mainframe = ttk.Frame(_root, padding="5 5 5 5 ")
    _mainframe.grid(row=0, column=0, sticky=("E", "W", "N", "S"))

    _url_frame = ttk.LabelFrame(_mainframe, text="URL", padding="5 5 5 5")
    _url_frame.grid(row=0, column=0, sticky=("E", "W"))
    _url_frame.columnconfigure(0, weight=1)
    _url_frame.rowconfigure(0, weight=1)

    _url = StringVar()
    _url.set("http://localhost:8000")
    _url_entry = ttk.Entry(_url_frame, width=40, textvariable=_url)
    _url_entry.grid(row=0, column=0, sticky=(E, W, S, N), padx=5)

    _fetch_btn = ttk.Button(_url_frame, text="Fetch info", command=fetch_url)
    _fetch_btn.grid(row=0, column=1, sticky=W, padx=5)

    _img_frame = ttk.LabelFrame(_mainframe, text="Content", padding="9 0 0 0")
    _img_frame.grid(row=1, column=0, sticky=(N, S, E, W))

    _images = StringVar()
    _img_listbox = Listbox(_img_frame, listvariable=_images, height=6, width=25)
    _img_listbox.grid(row=0, column=0, sticky=(E, W), pady=5)
    _scrollbar = ttk.Scrollbar(_img_frame, orient=VERTICAL, command=_img_listbox.yview)
    _scrollbar.grid(row=0, column=1, sticky=(S, N), pady=6)
    _img_listbox.configure(yscrollcommand=_scrollbar.set)

    _radio_frame = ttk.Frame(_img_frame)
    _radio_frame.grid(row=0, column=2, sticky=(N, S, W, E))

    _choice_lbl = ttk.Label(_radio_frame, text="Choose how to save images")
    _choice_lbl.grid(row=0, column=0, padx=5, pady=5)
    _save_method = StringVar()
    _save_method.set("img")

    _img_only_radio = ttk.Radiobutton(
        _radio_frame, text="As Images", variable=_save_method, value="img"
    )
    _img_only_radio.grid(row=1, column=0, padx=5, pady=2, sticky="W")
    _img_only_radio.configure(state="normal")
    _json_radio = ttk.Radiobutton(
        _radio_frame, text="As JSON", variable=_save_method, value="json"
    )
    _json_radio.grid(row=2, column=0, padx=5, pady=2, sticky="W")

    _scrape_btn = ttk.Button(_mainframe, text="Scrape!", command=save)
    _scrape_btn.grid(row=2, column=0, sticky=E, pady=5)

    _status_frame = ttk.Frame(_root, relief="sunken", padding="2 2 2 2")
    _status_frame.grid(row=1, column=0, sticky=("E", "W", "S"))
    _status_msg = StringVar()  # Initialize _status_msg here
    _status_msg.set("Type a URL to start scraping...")
    _status = ttk.Label(_status_frame, textvariable=_status_msg, anchor=W)
    _status.grid(row=0, column=0, sticky=(E, W))

    _root.mainloop()
