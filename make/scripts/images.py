import csv
import shutil
import time
from urllib import request
from pathlib import Path
from itertools import islice
import subprocess

dir_root = "./make"
dir_csv  = f"{dir_root}/CSV"

def get_image(id):
    url1 = f"https://drive.usercontent.google.com/u/1/uc?id={id}&export=download"
    url2 = f"https://drive.usercontent.google.com/download?id={id}&export=download"
    try:
        return request.urlopen(url1)
    except Exception as ex:
        return request.urlopen(url2)

with open(f"{dir_csv}/images.csv", "r", encoding="utf-8") as read_obj:
    for row in islice(csv.reader(read_obj), 1, None):
        url,name = row
        try:
            if "unsplash" in url:
                id = url.split("-")[-1]

                if not Path(f"./src/images/{name}").exists():
                    with open(f"./src/images/{name}", mode='wb+') as f:

                        subprocess.run(["curl","-L", f"https://unsplash.com/photos/{id}/download"], stdout=f)

            elif "box.com" in url:
                id = url.split("/")[4]
                app = "virginia.app.box.com" in url
                if not Path(f"./src/images/{name}").exists():
                    with open(f"./src/images/{name}", mode='wb+') as f:
                        subprocess.run(["curl","-L",f"https://virginia{".app" if app else ""}.box.com/shared/static/{id}"], stdout=f)

            else:
                if "/view" in url:
                    #e.g., https://drive.google.com/file/d/1agACToHkWhDmNIHThNfXgoaZQzoBzUw1/view?usp=drive_link
                    start_index = url.index("/d/") + 3
                    end_index = url.index("/view")
                else:
                    #e.g., https://drive.google.com/file/d/1agACToHkWhDmNIHThNfXgoaZQzoBzUw1/view?usp=drive_link
                    start_index = url.index("id=") + 3
                    end_index = url.index("&usp")

                image_id = url[start_index:end_index]

                if not Path(f"./src/images/{name}").exists():

                    with get_image(image_id) as r:
                        with open(f"./src/images/{name}", mode="wb+") as f:
                            shutil.copyfileobj(r,f)
            # time.sleep(0.5)
        
        except (KeyboardInterrupt,FileNotFoundError):
            raise
        except Exception as e:
            print("-----------------------------------")
            print(str(e))
            print(name)
            print(url)
