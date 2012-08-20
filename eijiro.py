# coding=utf-8

import sublime, sublime_plugin
import urllib
import urllib2
import thread
import re

class EijiroCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        point = self.view.sel()[0].begin()
        self.word = self.view.substr(self.view.word(point))

        if not self.word or self.word == "":
            sublime.status_message("No word found.")
            return
        else:
            self.consult_dictionary(self.word)

    def consult_dictionary(self, word):
        encoded_word = urllib.quote(word)
        self.url = "http://eow.alc.co.jp/{0}/UTF-8/".format(encoded_word)
        thread.start_new_thread(self.fetch_remote_dictionary, ())

    def fetch_remote_dictionary(self):
        try:
            request = urllib2.Request(self.url, headers={"User-Agent":
                    "Sublime Eijiro"})
            return self.handle_response(urllib2.urlopen(request, timeout=10))

        except urllib2.HTTPError as e:
            self.handle_error("HTTP", e)

        except urllib2.URLError as e:
            self.handle_error("URL", e)

    def handle_response(self, response):
        self.content = response.read()
        sublime.set_timeout(self.show_output_view, 0)

    def show_output_view(self):
        output_view = self.view.window().get_output_panel("eijiro." + self.word)

        output_view.set_scratch(True)
        output_view.set_name("Eijiro Result")

        edit = output_view.begin_edit()
        raw_content = self.extract_content(self.content)
        output_view.replace(edit, sublime.Region(0, 0), raw_content.decode("utf-8")[:])
        output_view.end_edit(edit)

        output_view.set_read_only(True)
        self.view.window().run_command("show_panel", {"panel": "output.eijiro." + self.word})

    def extract_content(self, content):
        pattern = r"<!-- ▼ 検索結果本体 ▼ -->\s*(.+)\s*<!-- ▲ 検索結果本体 ▲ -->"
        matched = re.search(pattern, content, re.M | re.S)
        if matched:
            raw_content = matched.group(1)
            raw_content = re.sub(r"</li>", "\n", raw_content)
            raw_content = re.sub(r"<[^>]+>", "",   raw_content)
            return raw_content.strip()

    def handle_error(self, type, error):
        self.message = '{0}: {1} error {2} downloading {3}.'.format(__name__, type, error.message, str(error.code), self.url)
        sublime.set_timeout(self.show_status_message, 0)

    def show_status_message(self):
        sublime.status_message(self.message)
