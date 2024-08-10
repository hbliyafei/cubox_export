import json
import logging
import os
import os.path
import re
import sys
import time

import requests


def setup_logging(log_level=logging.DEBUG):
    """
    Configure logging settings.

    :param log_level: The logging level (default is DEBUG).
    :return: Configured logger instance.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        current_dir = os.path.dirname(sys.executable)

    log_path = os.path.join(current_dir, 'logs')
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    rq = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    log_name = os.path.join(log_path, f'{rq}.log')

    logger = logging.getLogger('main')
    logger.setLevel(log_level)

    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create file handler
    file_handler = logging.FileHandler(log_name, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_content_before_last_dash(string):
    last_dash_index = string.rfind("-")  # 获取最后一个"-"的索引
    if last_dash_index == -1:
        # 如果没有找到"-"，返回原字符串
        return string
    else:
        # 获取最后一个"-"之前的内容
        return string[:last_dash_index]


def remove_invalid_filename_chars(filename):
    # 定义要移除的非法字符
    invalid_chars = r'[<>:"/\\|?*]'
    # 使用正则表达式替换非法字符为空字符串
    cleaned_filename = re.sub(invalid_chars, '-', filename)
    return cleaned_filename


def show_process(process_num):
    if process_num == 100:
        process = "\r[%3s%%]: |%-50s|\n" % (int(process_num), '#' * (int(process_num / 2)))
    else:
        process = "\r[%3s%%]: |%-50s|" % (int(process_num), '#' * (int(process_num / 2)))
    print(process, end='', flush=True)


class Cubox:
    def __init__(self, logger, token, save_directory, export_type='md', delete_original=False):
        self.logger = logger
        self.token = token
        self.save_directory = save_directory
        self.export_type = export_type
        self.delete_original = delete_original

        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Authorization': f'{token}',
            'Connection': 'keep-alive',
            'Cookie': f'token={token}',
            'DNT': '1',
            'Referer': 'https://cubox.pro/my/inbox',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
            'sec-ch-ua': '"Microsoft Edge";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }

        self.logger.info(f'Start export cubox inbox save directory: {self.save_directory} export type: {self.export_type} delete_original: {self.delete_original}')

    def start(self):
        self.get_list()

    def get_list(self):
        flag = True
        page = 1
        lists = []
        downloaded_count = 0

        while flag:
            url = f"https://cubox.pro/c/api/v2/search_engine/inbox?page={page}"
            response = requests.request("GET", url, headers=self.headers, data={})
            rsp = json.loads(response.text)
            if rsp['code'] == 200:

                # list
                list = rsp['data']
                for item in list:
                    userSearchEngineID = item['userSearchEngineID']
                    title = item['title']

                    lists.append({
                        'id': userSearchEngineID,
                        'title': title
                    })

                page = page + 1
                if page > rsp['pageCount']:
                    break
            else:
                print('出错了')
                print(rsp['message'])
                break

        if len(lists) == 0:
            self.logger.info(f'Cubox inbox is empty.')

        for item in lists:
            self.export(item['id'], item['title'])
            downloaded_count += 1
            show_process(downloaded_count / len(lists) * 100)

    def export(self, id, title):
        url = "https://cubox.pro/c/api/search_engines/export"
        payload = f'engineIds={id}&type={self.export_type}&snap=false&compressed=false'

        headers = self.headers
        headers['Referer'] = f'https://cubox.pro/my/card?id={id}&query=true'
        response = requests.request("POST", url, headers=headers, data=payload)

        try:
            title = remove_invalid_filename_chars(title)
            title = get_content_before_last_dash(title)

            with open(os.path.join(directory, title + '.' + self.export_type), 'w', encoding='utf-8') as file:
                file.write(response.text)

            if self.delete_original:
                self.delete(id)

            # self.logger.info(f'Exported {title} successfully.')
        except Exception as e:
            self.logger.error(f'Error exporting {title} : {e}')

    def delete(self, id):
        url = f"https://cubox.pro/c/api/search_engine/delete/{id}"
        headers = self.headers
        headers['Referer'] = f'https://cubox.pro/my/card?id={id}'
        response = requests.request("POST", url, headers=headers, data={})
        self.logger.info(response.text)


if __name__ == '__main__':
    directory = './docs'
    token = ''
    # export markdown:md, text:text: pdf:pdf: html:html
    cubox = Cubox(setup_logging(), token, directory, 'md', False)
    cubox.start()
