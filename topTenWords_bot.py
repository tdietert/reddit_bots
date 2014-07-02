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

	def get_most_common(self):
		mcw_list = []
		with open('C:/Users/Tommy/pythonFiles/most_common_words.txt', "r") as mcwords:
			for line in mcwords.readlines():
				mcw_list.append(((line.split(' '))[-1]).strip())

		return mcw_list
		
	# uses regex to filter out "words", only counts words 4 letters and over
	def collect_word_data(self, usr_comments):
		words_dict = {}
		# gets the most commonly used words in english, and doesn't count them
		mcw_list = self.get_most_common()
		# iterates through a list of a list of comments from each page
		for comment in usr_comments:
			# ignores words with apostrophes because of contractions
			for word in re.findall(r"[\w]+", comment):
				if len(word) > 3 and word not in mcw_list:
					if not word.isdigit():
						word = word.lower()
					if word in words_dict.keys():
						words_dict[word] += 1
					else:
						words_dict[word] = 1
		return words_dict

	def get_ordered_word_dict(self, words):
		# returns the list of words in descending from most->least usage
		return collections.OrderedDict(sorted(words.items(), key=lambda x: x[1], reverse=True))

	def reply_results(self):
		message = '\n\n'.join((wordcount[0] + ' : ' + str(wordcount[1]) for wordcount in self.top_ten_words))
		message = 'Your top ten words used:\n\n[ word : frequency ]\n\n' + message
		self.comment.reply(message)

if __name__ == '__main__':

	r = praw.Reddit('this is u/swingtheorys user comment scraper!')
	r.login('', '')
	submission = r.get_submission(submission_id='29lkrz')
	sub_comment_list = praw.helpers.flatten_tree(submission.comments)

	already_commented = []
	users_replied_to = []
	
	while True:
		for comment in sub_comment_list:
			if comment.author and comment.id not in already_commented and comment.author not in users_replied_to:
				author = comment.author
				reddit_bot = TenWordsBot(author, comment)
				reddit_bot.reply_results()
				already_responded.append(comment.id)
				users_replied_to.append(comment.author)
				time.sleep(600)

