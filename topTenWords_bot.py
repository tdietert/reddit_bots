
from bs4 import BeautifulSoup
from functools import *
from itertools import *

import collections
import operator
import os
import praw
import requests
from bs4 import BeautifulSoup
from functools import *
from itertools import *

import collections
import operator
import os
import praw
import requests
import re
import time

class TenWordsBot():

	def __init__(self, current_thread):
		self.r = praw.Reddit('this is u/swingtheorys user comment scraper!')
		self.r.login('tenwords_bot', 'ilikepotatoesjug')
		self.submission = self.r.get_submission(submission_id=current_thread)

		self.responded_to = set()
		self.ignore = self.get_ignore_list()

	def moniter_thread(self):
		while True:
			for comment, redditor in zip(*self.get_commenters()):
				if redditor.name not in self.responded_to and not self.already_replied(comment):
					if comment.body[:15] == 'get_top_ten(me)':	
						top_ten_words = self.get_top_ten(redditor)
						self.reply_results(top_ten_words, comment)
						self.responded_to.add(redditor.name)

			time.sleep(30)

	def get_commenters(self):
		sub_comment_list = praw.helpers.flatten_tree(self.submission.comments)
		commenters_list = reduce(lambda y, x: y + [x] if x.is_root else y, sub_comment_list, [])
		redditor_list = reduce(lambda y, x: y + [x.author] if x.is_root else y, sub_comment_list, [])

		return (commenters_list, redditor_list)

	def get_top_ten(self, redditor):
		usr_comments = self.get_user_comments(redditor)
		word_list = self.collect_word_data(usr_comments)
		word_dict = self.get_ordered_word_dict(word_list)
		
		return (collections.Counter(word_dict)).most_common(10)

	def get_user_comments(self, redditor):
		user_comments = redditor.get_comments(limit=None)
		comment_ids = set()
		comment_list = []
		for comment in user_comments:
			if comment.id not in comment_ids:
				comment_ids.add(comment.id)
				comment_list.append(comment.body)

		return comment_list

	def get_ignore_list(self):
		mcw_list = []
		with open('C:/Users/Thomas/Documents/python_files/ignore_list.txt', "r") as mcwords:
			for line in mcwords.readlines():
				mcw_list.append(((line.split(' '))[-1]).strip())

		return mcw_list

	# uses regex to filter out "words", only counts words 4 letters and over
	def collect_word_data(self, usr_comments):
		words_dict = {}
		# iterates through a list of a list of comments from each page
		for comment in usr_comments:
			for word in re.findall(r"[\w']+", comment):
				word = self.filter_word(word)
				if word != None:
					if word not in words_dict.keys():
						words_dict[word] = 1
					else:
						words_dict[word] += 1

		return words_dict

	def get_ordered_word_dict(self, words):
		# returns the list of words in descending from most->least usage
		return collections.OrderedDict(sorted(words.items(), key=lambda x: x[1], reverse=True))

	def reply_results(self, top_ten, comment):
		message = '\n\n'.join((word[0] + ' : ' + str(word[1]) for word in top_ten))
		message = 'Your top ten words used:\n\n[ word : frequency ]\n\n' + message
		comment.reply(message)

	def filter_word(self, word):
		if word in self.ignore:
			return None
		if word.isdigit():
			return None
		if len(word) < 4:
			return None

		return word.lower()

	def already_replied(self, comment):
		for comment in comment.replies:
			if comment.author.name == 'tenwords_bot':
				return True

		return False

if __name__ == '__main__':
	bot = TenWordsBot('29ur58')
	bot.moniter_thread()
