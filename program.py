import downloader
import os
import bs4
import random
import time
import sys
import progressbar


def get_absolute_filename(folderpath, name):
    filename = os.path.abspath(os.path.join(folderpath, name + '.html'))
    return filename


def parse_instapaper_html(folderpath, name: str):
    link_list = []
    fullpath = get_absolute_filename(folderpath, name)
    soup = bs4.BeautifulSoup(open(fullpath), 'html.parser')
    for item in soup.findAll('a', href=True):
        # print(item.get('href'))
        link_list.append(item.get('href'))
    return link_list


def filter_non_relevant_addresses(link_list):
    new_list = []
    discarded_list = []
    for entry in link_list:
        entry_string = str(entry)
        # if entry_string.contains('https://www.literotica.com/s/'):
        if ('imagefap.com/photo' in entry_string):
            new_list.append(entry)
        else:
            discarded_list.append(entry)

    return new_list


def main():
    folderpath = ''
    if sys.platform == 'linux':
        folderpath = '/mnt/ELEMENTS/completed'
    elif sys.platform == 'darwin':
        folderpath = '/Volumes/completed/'
    else:
        print('Unable to determine OS. Quitting.')
        return
    link_list = parse_instapaper_html(folderpath, 'tor')
    parsed_list = filter_non_relevant_addresses(link_list)
    parsed_list = sorted(parsed_list)
    parsed_list = list(set(parsed_list))
    total = parsed_list.__len__()
    #pbar = progressbar.ProgressBar(widgets=[progressbar.Percentage(), progressbar.Bar()], maxval=total + 1).start()
    i = 0
    for url in parsed_list[i:]:
        print('downloading gallery {} of {} = ({})'.format(i, total, url))
        retvalue = downloader.downloader_main(folderpath, url)
        if retvalue == 0:
            r = random.randrange(5, 15)
            print('done, sleeping ({})...'.format(r))
            time_delay = r
            time.sleep(time_delay)
        else:
            print('skipped, moving on...')
        i = i + 1
        #pbar.update(i)
    #pbar.finish()


if __name__ == '__main__':
    main()
