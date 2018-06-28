import os
import shutil
import requests
import bs4
import re
import progressbar


def remove_non_ascii(text):
    return ''.join([i if ((122 >= ord(i) >= 65) or (48 <= ord(i) <= 57)) else ' ' for i in text])


def check_or_create_folder(gallery_name):
    full_path = os.path.abspath(os.path.join('/Volumes/completed/Imagefap_Downloads', remove_non_ascii(gallery_name)))
    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        # print('Creating new directory {}'.format(full_path))
        os.mkdir(full_path)
    return full_path


def get_gallery_name(url):
    html = get_html(url)
    soup = bs4.BeautifulSoup(html, 'html.parser')
    try:
        html_title_tag = soup.findAll("font", {"itemprop": "name"})
        title = html_title_tag[0].contents[0]
    except IndexError as e:
        # No title in the image page, I need to go looking for it in the table under the image
        for tag in soup.find_all("td"):
            if tag.contents[0] == "Gallery:":
                title = tag.parent.contents[3].contents[0].contents[0]
    except Exception as e:
        title = url.split("/")[4]
    return remove_non_ascii(title)


def get_html(url):
    response = requests.get(url)
    # print(response.status_code)
    # print(response.text)
    if response.status_code != 200:
        return response.status_code
    else:
        return response.text


def get_data_from_url(url):
    response = requests.get(url, stream=True)
    return response.raw


def save_image(folder_full_path, url):
    data = get_data_from_url(url)
    name = url.split("/")[-1]
    file_name = os.path.join(folder_full_path, name)
    if not os.path.exists(file_name) and not os.path.isdir(file_name):
        with open(file_name, 'wb') as fout:
            shutil.copyfileobj(data, fout)


def download_gallery(url, folder_full_path):
    html = get_html(url)
    soup = bs4.BeautifulSoup(html, 'html.parser')
    navigation_ul = soup.findAll("ul", {"class": "thumbs"})
    for li_tag in navigation_ul[0].findAll('li'):
        # print(li_tag.contents[1].attrs['original'])
        # print()
        save_image(folder_full_path, li_tag.contents[1].attrs['original'])
        print()

    # for li_tag in bs4.BeautifulSoup(html, 'html.parser').find_all('ul', {'class':'thumbs'}):
    # print(li_tag)
    # li_tag.find_all('li')
    return


def get_gallery_home(url):
    html = get_html(url)
    soup = bs4.BeautifulSoup(html, 'html.parser')
    try:
        html_title_tag = soup.findAll("font", {"itemprop": "name"})
        home_url = html_title_tag[0].parent.attrs['href']
    except IndexError:
        for tag in soup.find_all("td"):
            if tag.contents[0] == "Gallery:":
                home_url = tag.parent.contents[3].contents[0].attrs['href']
    except:
        home_url = "Could not find gallery home"
    return home_url


def get_visible_gallery_pages(url):
    gallery_pages_list = list()
    html = get_html(url)
    soup = bs4.BeautifulSoup(html, 'html.parser')
    tags = soup.find_all("a", {"class": "link3"})
    if not tags:
        gallery_pages_list.append(url)
    else:
        for tag in tags:
            if str(tag.contents[0]) != ":: prev ::":
                gallery_pages_list.append("http://www.imagefap.com/gallery.php{}".format(tag.attrs['href']))
            if str(tag.contents[0]) == ":: next ::":
                # print()
                gallery_pages_list.extend(get_visible_gallery_pages(
                    "http://www.imagefap.com/gallery.php{}".format(tag.parent.contents[-4].attrs['href'])))

    return gallery_pages_list


def get_all_pages_from_gallery_home(gallery_home_url):
    gallery_pages_list = get_visible_gallery_pages(gallery_home_url)
    return sorted(set(gallery_pages_list))


def get_all_pictures_from_single_gallery_page(page_url):
    image_url_list = list()
    html = get_html(page_url)
    soup = bs4.BeautifulSoup(html, 'html.parser')
    for tag in soup.find_all("a", {"name": re.compile("^[0-9]+$")}):
        # print()
        photo_id = tag.attrs['name']
        url = "http://www.imagefap.com/photo/{}/".format(photo_id)
        image_url_list.append(url)
    return image_url_list


def get_all_pictures_from_sorted_page_list(sorted_gallery_pages_list):
    image_url_list = list()
    for page_url in sorted_gallery_pages_list:
        image_url_list.extend(get_all_pictures_from_single_gallery_page(page_url))
    return image_url_list


def download_image_from_single_page(image_page_url, folder_full_path):
    html = get_html(image_page_url)
    soup = bs4.BeautifulSoup(html, 'html.parser')
    for tag in soup.find_all("span", {"itemprop": "contentUrl"}):
        # print(tag.contents[0])
        save_image(folder_full_path, tag.contents[0])
        # print("saved image")
    return


def download_image_from_pages(image_url_list, folder_full_path):
    # pbar = progressbar.ProgressBar(widgets=[progressbar.Percentage(), progressbar.Bar()], maxval=image_url_list.__len__() + 1).start()
    # i = 1
    for image_page_url in image_url_list:
        download_image_from_single_page(image_page_url, folder_full_path)
    #    pbar.update(i + 1)
    # pbar.finish()
    return


def gallery_still_exists(url):
    html = get_html(url)
    # 404 - Not Found
    if type(html) == int:
        return False
    else:
        return True


def downloader_main(url):
    if not gallery_still_exists(url):
        print("gallery no longer exists, skipping")
        return -1
    gallery_name = get_gallery_name(url)
    print("Downloading gallery {} ...".format(gallery_name), end="  ")
    if "There seems to be an issue with the gallery, skipping" in gallery_name:
        print(gallery_name)
        return -1
    folder_full_path = check_or_create_folder(gallery_name)
    gallery_home_url = get_gallery_home(url)
    if "Could not find gallery home" in gallery_home_url:
        print(gallery_home_url)
        return -1
    sorted_gallery_pages_list = get_all_pages_from_gallery_home(gallery_home_url)
    image_url_list = get_all_pictures_from_sorted_page_list(sorted_gallery_pages_list)
    download_image_from_pages(image_url_list, folder_full_path)
    return 0


if __name__ == '__main__':
    # downloader_main("http://www.imagefap.com/photo/1115754502/#23")
    downloader_main("http://www.imagefap.com/photo/373465752/")  # 404
    # downloader_main("http://www.imagefap.com/photo/374323761/?pgid=&gid=6265052&page=0&idx=0")  # no title, check in the table below the image
