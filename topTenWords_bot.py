from bs4 import BeautifulSoup
from functools import *
from itertools import *

import collections
import matplotlib.pyplot as plt
import numpy as np
import os
import praw
import pyimgur
import requests
import re
import time

class TenWordsBot():

	def __init__(self, current_thread):
		self.r = praw.Reddit('this is u/swingtheorys user comment scraper!')
		self.r.login('', '')
		self.submission = self.r.get_submission(submission_id=current_thread)
		self.responded_to = set()
		self.ignore = self.get_ignore_list()

	def moniter_thread(self):
		while True:
			for comment, redditor in zip(*self.get_commenters()):
				if redditor.name not in self.responded_to and not self.already_replied(comment):
					if comment.body[:15] == 'get_top_ten(me)':	
					#if redditor.name != 'tenwords_bot':
						self.usr_comments = self.get_user_comments(redditor)
						self.top_ten = self.get_top_ten()
						self.unique_word_count = len(self.collect_word_data())

						output_graph = self.plot_results(redditor.name)
						save_dir = os.getcwd() + '/tenwords_bot_output/'
						file_name = redditor.name + '.png'
						self.save_locally(output_graph, save_dir, file_name)

						file_path = save_dir + redditor.name + '.png'
						self.img_link = self.upload_to_imgur(file_path, redditor.name)

						self.reply_results(comment)
						self.responded_to.add(redditor.name)
						print 'successfully responded to ' + redditor.name + '...'

			time.sleep(30)

	def get_commenters(self):
		comment_list = list(praw.helpers.flatten_tree(self.submission.comments))
		# .... To make it only moniter root comments:
		commenters_list = reduce(lambda y, x: y + [x] if x.is_root else y, sub_comment_list, [])
		redditor_list = reduce(lambda y, x: y + [x.author] if x.is_root else y, sub_comment_list, [])
		#redditor_list = list(reduce(lambda y, x: y +[x.author] if x.author else y, comment_list, []))
		return (comment_list, redditor_list)

	def get_user_comments(self, redditor):
		user_comments = redditor.get_comments(limit=None)
		comment_ids = set()
		comment_list = []
		for comment in user_comments:
			if comment.id not in comment_ids:
				comment_ids.add(comment.id)
				comment_list.append(comment.body)

		return comment_list

	# uses regex to filter out "words", only counts words 4 letters and over
	def collect_word_data(self):
		words_dict = {}
		# iterates through a list of a list of comments from each page
		for comment in self.usr_comments:
			for word in re.findall(r"[\w']+", comment):
				word = self.filter_word(word)
				if word != None:
					if word not in words_dict.keys():
						words_dict[word] = 1
					else:
						words_dict[word] += 1
				
		# returns the list of words in descending from most->least usage
		return collections.OrderedDict(sorted(words_dict.items(), key=lambda x: x[1], reverse=True))

	def get_top_ten(self):
		word_list = self.collect_word_data()	
		# returns tuple, number of unique words, top ten words
		return (collections.Counter(word_list)).most_common(10)

	# loads words to be ignored from file
	def get_ignore_list(self):
		mcw_list = []
		with open(os.getcwd() + '/ignore_list.txt', "r") as mcwords:
			for line in mcwords.readlines():
				mcw_list.append(line.strip())

		return mcw_list

	def plot_results(self, r_username):
		words = [word[0] for word in self.top_ten]
		times_used = [word[1] for word in self.top_ten]

		y_axis = np.arange(10) + 0.5
		bar_height = 0.7
		opacity = 0.8

		output_graph = plt.barh(y_axis, times_used, bar_height,
				                alpha=opacity,
				                align='center',
				                color='g',
				                yerr=0)

		x_max = max(times_used) + 10
		plt.xlim([0, x_max])
		#labeling the graph
		plt.xlabel('Usage Count')
		plt.ylabel('Word')
		plt.title('Word Occurrences in First 1000 Comments: ' + r_username)
		plt.yticks(y_axis, words)

		max_usage = times_used[0]
		# labels the bars with respective word usage counts
		self.label_graph(output_graph, x_max)
		# makes errything pretty
		plt.tight_layout()
		# saves figure to 
		 # If the directory does not exist, create it
		return output_graph

	def label_graph(self, rects, max):
		for rect in rects:
			width = rect.get_width()
			xloc = width + .05*max
			yloc = rect.get_y() + rect.get_height()/2.0
			clr = 'white'
			align = 'right'

			plt.text(xloc, yloc, str(width), ha=align, va='center')

	def save_locally(self, output_graph, save_dir, file_name):

		if not os.path.exists(save_dir):
			os.makedirs(save_dir)
		 
		# The final path to save to
		savepath = os.path.join(save_dir, file_name)

		print("Saving figure to '%s'..." % savepath),	 
		# save the figure
		plt.savefig(savepath)
		# close it
		plt.close()

		print("... Done")

	def upload_to_imgur(self, file_path, username):
		CLIENT_ID = "cb4311169fa3a6b"
		CLIENT_SECRET = "a9ca3c24b949e374e3966dd0be65417114b6f7d3"

		im = pyimgur.Imgur(CLIENT_ID)
		uploaded_image = im.upload_image(file_path, title=username+' top ten words data:')

		print 'uploaded:' + uploaded_image.title
		print uploaded_image.link

		return uploaded_image.link

	# edit this function
	def reply_results(self, comment):
		comment.reply("Out of " + str(self.unique_word_count) + " words used, here are your top ten:\n" + self.img_link)

	def filter_word(self, word):
		if word in self.ignore:
			return None
		if word.isdigit():
			return None
		if len(word) < 4:
			return None

		return word.lower()

	def already_replied(self, comment):
		for cmnt in comment.replies:
			if cmnt.author.name == 'tenwords_bot':
				return True

		return False

if __name__ == '__main__':
	bot = TenWordsBot('') # your thread id goes here
	bot.moniter_thread()

