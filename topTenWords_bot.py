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
		self.current_thread_id = current_thread
		self.responded_to = set()
		self.ignore = self.get_ignore_list()

	def moniter_thread(self):
		while True:
			# reloads submission every loop, 
			submission = self.r.get_submission(submission_id=self.current_thread_id)
			submission.replace_more_comments(limit=None, threshold=0)
			for comment, redditor in zip(*self.get_commenters(submission)):
				if redditor.name not in self.responded_to and redditor != None:
					if not self.already_replied(comment):
						if comment.body[:15] == 'get_top_ten(me)'.lower(): #capitalization doesn't matter	

							# collects word data and finds top ten
							usr_comments = self.get_user_comments(redditor)
							word_data = self.collect_word_data(usr_comments)
							top_ten_words = self.get_top_ten(word_data)
							unique_word_count = self.count_unique_words(usr_comments)

							# graphs the data and saves it locally
							output_graph = self.plot_results(redditor.name, top_ten_words)
							save_dir = os.getcwd() + '/tenwords_bot_output/'
							file_name = redditor.name + '.png'
							self.save_locally(output_graph, save_dir, file_name)

							# uploads to imgur and retrieves the image link
							file_path = save_dir + redditor.name + '.png'
							img_link = self.upload_to_imgur(file_path, redditor.name)

							# replies to current comment
							self.reply_results(comment, img_link, unique_word_count)
							self.responded_to.add(redditor.name)
							print 'successfully responded to ' + redditor.name + '...\n'

							time.sleep(15)
			time.sleep(60)

	def get_commenters(self, submission):
		comment_list = self.submission.comments #This will get the root level comments only
		
		redditor_list = []
		for x in comment_list:
			redditor_list.append(x.author)
		#redditor_list = list(reduce(lambda y, x: y +[x.author] if x.author else y, comment_list, []))
		return (root_comment_list, redditor_list)

	def get_user_comments(self, redditor):
		user_comments = redditor.get_comments(limit=None)
		comment_ids = set()
		comment_list = []
		for comment in user_comments:
			if comment.id not in comment_ids:
				comment_ids.add(comment.id)
				comment_list.append(comment.body)

		return comment_list

	# collect word data filters some words based on length and frequency used in the English language
	# this function counts the actual number of unique words in the user's comment history
	def count_unique_words(self, usr_comments):
		words_counter = collections.Counter()
		for comment in usr_comments:
			for word in re.findall(r"[\w']+", comment):
				if not word.isdigit():
					words_counter[word.lower()] += 1

		return len(words_counter)

	# uses regex to filter out "words", only counts words 4 letters and over
	def collect_word_data(self, usr_comments):
		words_counter = collections.Counter()
		# iterates through a list of a list of comments from each page
		for comment in usr_comments:
			for word in re.findall(r"[\w']+", comment):
				filtered_word = self.filter_word(word)
				if filtered_word != None:
					words_counter[filtered_word] += 1
				
		# returns the list of words in descending from most->least usage
		return words_counter

	def get_top_ten(self, words_counter):	
		# returns top 10 most common words
		return words_counter.most_common(10)

	# loads words to be ignored from file
	def get_ignore_list(self):
		mcw_list = []
		with open(os.getcwd() + '/ignore_list.txt', "r") as mcwords:
			for line in mcwords.readlines():
				if line.strip() not in mcw_list:
					mcw_list.append(line.strip())

		return mcw_list

	def plot_results(self, r_username, top_ten):
		words = [word[0] for word in top_ten]
		times_used = [word[1] for word in top_ten]

		y_axis = np.arange(10) + 0.5
		bar_height = 0.7
		opacity = 0.8

		output_graph = plt.barh(y_axis, times_used, bar_height,
				                alpha=opacity,
				                align='center',
				                color='g',
				                yerr=0)

		x_max = max(times_used) + 0.1*max(times_used)
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

		return output_graph

	def label_graph(self, rects, x_max):
		for rect in rects:
			width = rect.get_width()
			xloc = width + float(.05*x_max)
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

	def upload_to_imgur(self, file_path, username):
		with open(os.getcwd() + '/tenwords_bot_config.txt', 'r') as id_and_secret:
			client_id, client_secret = ((id_and_secret.readlines())[0]).split(',')

			CLIENT_ID = client_id
			CLIENT_SECRET = client_secret

			im = pyimgur.Imgur(CLIENT_ID)
			uploaded_image = im.upload_image(file_path, title=username+' top ten words data:')

			print 'uploaded:' + uploaded_image.title
			print uploaded_image.link

			return uploaded_image.link

	def reply_results(self, comment, img_link, word_count):
		comment.reply("Out of " + str(word_count) + " words used, here are your top ten:\n" + img_link)

	# checks to see if string is a word to count
	def filter_word(self, word):
		if word.isdigit():
			return None
		if len(word) < 4:
			return None
		if word in self.ignore:
			return None	

		return word.lower()

	def already_replied(self, comment):
		for cmnt in comment.replies:
			# checks if comment is deleted before checking if it has name
			if cmnt.author:
				if cmnt.author.name == 'tenwords_bot':
					return True
			else:
				return True

		return False

if __name__ == '__main__':
	bot = TenWordsBot('2a8yyo') # your thread id goes here
	bot.moniter_thread()
