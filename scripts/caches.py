
import os
import shutil
import base64
from browser import Browser
import tempfile
import email
from PIL import Image

import pickle
from browser import Browser
from utils import deduplicate_filename, wget, wait
import time

class Cache:
    base_filename=("cached-", ".data")
    index_filename=("data-", ".pickled")
    @classmethod
    def _get_filename_pattern(cls):
        return cls.base_filename[0] + "(\d+)" + cls.base_filename[1]
    @classmethod
    def _get_number_from_filename(cls, filename):
        match = re.match(
            cls._get_filename_pattern(),
            cls.filename
        )
        if not match:
            return -1
        else:
            return int(match[1])
    @classmethod
    def _get_highest_filename_number(cls):
        return max(
            os.listdir(cls.folder),
            cls._get_number_from_filename
        )
    @classmethod
    def _make_filename(cls, filename_number, base_filename=None):
        if base_filename is None:
            base_filename = cls.base_filename
        return base_filename[0] \
               + str(filename_number) \
               + base_filename[1]
    @classmethod
    def _get_filename(cls):
        return cls._make_filename(time.time())
    @classmethod
    def load(cls):
        path = os.path.join(cls.folder, "".join(cls.index_filename))
        if os.path.exists(path):
            with open(path, "rb") as handle:
                cls.data = pickle.load(handle)
        else:
            cls.data = {}
            if not os.path.exists(cls.folder):
                os.mkdir(cls.folder)
    @classmethod
    def save(cls):
        path = os.path.join(cls.folder, "".join(cls.index_filename))
        backup_path = os.path.join(
            cls.folder,
            cls._make_filename(
                 time.time(),
                 cls.index_filename
            )
        )
        with open(path, "wb") as handle:
            pickle.dump(cls.data, handle)
        with open(backup_path, "wb") as handle:
            pickle.dump(cls.data, handle)
    @classmethod
    def post(cls, asset):
        return asset
    @classmethod
    def get(cls, id):
        if not id in cls.data:
            cls.add(id, cls.source(id))
        return cls.post(cls.data[id])
    @classmethod
    def add(cls, id, val, replace=False):
        if replace or (id not in cls.data):
            cls.data[id] = val
            cls.save()
    @classmethod
    def add_from_path(cls, id, path, replace=False):
        new_filename = cls._get_filename()
        new_path = os.path.join(
            cls.folder,
            new_filename
        )
        shutil.copyfile(
            path,
            new_path
        )
        cls.add(id, new_filename, replace=replace)

class ResourceCache(Cache):
    folder="rad_resource_cache"
    @classmethod
    def post(cls, resource):
        return os.path.join(cls.folder, resource)
    @classmethod
    def source(cls, resource):
        "Fall back on downloading with wget."
        filename = cls._get_filename()
        wget(
            resource,
            os.path.join(
                cls.folder,
                filename,
            )
        )
        wait(10)
        return filename

class MHTMLCache(Cache):
    folder="rad_mhtml_cache"
    base_filename=("saved-", ".mhtml")
    @classmethod
    def post(cls, filename):
        return os.path.join(cls.folder, filename)
    @classmethod
    def add_from_browser(cls, id, browser):
        print("adding from browser")
        filename = cls._get_filename()
        browser.save_mhtml(os.path.join(cls.folder,
                                        filename))
        super().add(id, filename)
        with open(cls.get(id)) as handle:
            message = email.message_from_file(handle)
            for idx, item in enumerate(message.walk()):
                if idx > 0: #First is just the whole mhtml
                    attrs = dict(item.items())
                    location = attrs.get("Content-Location") or attrs.get("Snapshot-Content-Location")
                    with tempfile.NamedTemporaryFile() as temp:
                        filename=temp.name
                        content_t = item.get_content_type()
                        if content_t.startswith("image") and not content_t.endswith("svg"):
                            with open(filename,"wb") as handle:
                                handle.write(base64.b64decode(item.get_payload()))
                        else:
                            with open(filename,"w") as handle:
                                handle.write(item.get_payload())
                        ResourceCache.add_from_path(
                            location,
                            filename
                        )


class SimpleMHTMLCache(MHTMLCache):
    @classmethod
    def source(cls, url):
        with tempfile.TemporaryDirectory() as tmp:
            browser = Browser(tmp)
            browser.get(url)
            cls.add_from_browser(url, browser)
            browser.close()

class MetadataCache(Cache):
    @classmethod
    def source(cls, url):
        print("Getting metadata from source")
        browser = Browser(os.path.join(os.path.abspath(os.path.dirname(__file__)),"random_downloads"))
        browser.get(url)
        print("URL gotten")
        metadata = cls.metadata_from_result_page(browser)
        MHTMLCache.add_from_browser(url, browser)
        browser.close()
        return metadata

class Scraper:
    def __init__(self, mhtml_folder, resource_folder):
        pass
    def get_mhtml_filename(self):
        return deduplicate_filename("saved.mhtml", self.folder)
    def retrieve(self, url):
        path=os.path.join(os.path.abspath(os.path.dirname(__file__)),"random_downloads")
        #print(path)
        browser = Browser(path) #architectural flaw
        browser.get_local(SimpleMHTMLCache.get(url))
        metadata = self.metadata_from_result_page(browser)
        mhtml = browser.save_mhtml(
            "mhtml_path",
             os.path.join(self.folder,
                     self.get_mhtml_filename())
        )
        MHTMLCache.add(mhtml)
        return mhtml, metadata
    def extract(self, url):
        if not url in self.data:
            mhtml, metadata = self.retrieve(url)
            self.data[url] = {
                "mhtml":mhtml,
                "metadata":metadata
            }
            self.save()
        return self.data[url]
