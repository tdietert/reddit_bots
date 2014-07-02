from bs4 import BeautifulSoup
from functools import *

import collections
import operator
import os
import praw
import requests
import re
import time

class TenWordsBot():

	def __init__(self, redditor, comment):

		self.redditor = redditor
		self.ignore = self.get_ignore_list()
		self.top_ten_words = self.get_top_ten()
		self.comment = comment

	def get_top_ten(self):
		usr_comments = self.get_user_comments()
		word_list = self.collect_word_data(usr_comments)
		word_dict = self.get_ordered_word_dict(word_list)
		return (collections.Counter(word_dict)).most_common(10)

	def get_user_comments(self):
		
		user_comments = self.redditor.get_comments(limit=None)

		comment_ids = set()
		comment_list = []
		for comment in user_comments:
			if comment.id not in comment_ids:
				comment_ids.add(comment.id)
				comment_list.append(comment.body)

		return comment_list

	def get_ignore_list(self):
		mcw_list = []
		with open('C:/Users/Tommy/pythonFiles/most_common_words.txt', "r") as mcwords:
			for line in mcwords.readlines():
				mcw_list.append(((line.split(' '))[-1]).strip())

		return mcw_list
		
	# uses regex to filter out "words", only counts words 4 letters and over
	def collect_word_data(self, usr_comments):
		words_dict = {}
		# iterates through a list of a list of comments from each page
		for comment in usr_comments:
			for word in re.findall(r"[\w]+", comment):
				word = self.filter_word(word)
				if word != None and word not in words_dict.keys():
					words_dict[word] = 1
				elif word != None:
					words_dict[word] += 1

		return words_dict

	def filter_word(self, word):
		if word in self.ignore:
			return None
		if word.isdigit():
			return None
		if len(word) < 4:
			return None
		return word.lower()

	def get_ordered_word_dict(self, words):
		# returns the list of words in descending from most->least usage
		return collections.OrderedDict(sorted(words.items(), key=lambda x: x[1], reverse=True))

	def reply_results(self):
		message = '\n\n'.join((wordcount[0] + ' : ' + str(wordcount[1]) for wordcount in self.top_ten_words))
		message = 'Your top ten words used:\n\n[ word : frequency ]\n\n' + message
		self.comment.reply(message)

def check_replied(comment):
	if comment.author.name == 'tenwords_bot':
		return True
	for comment in comment.replies:
		if comment.author.name == 'tenwords_bot':
			return True
	return False


if __name__ == '__main__':

	r = praw.Reddit('this is u/swingtheorys user comment scraper!')
	r.login('tenwords_bot', 'ilikepotatoesjug')

	already_commented = set()
	users_replied_to = set()

	while True:

		submission = r.get_submission(submission_id='29nmpq')
		sub_comment_list = praw.helpers.flatten_tree(submission.comments)

		for comment in sub_comment_list:
			if not check_replied(comment):
				if comment.author and comment.id not in already_commented and comment.author.name not in users_replied_to:
					author = comment.author
					reddit_bot = TenWordsBot(author, comment)
					reddit_bot.reply_results()
					already_commented.add(comment.id)
					users_replied_to.add(comment.author.name)
					time.sleep(600)



